import json
import logging
import os
import datetime
from typing import Dict, Any
from dateutil import parser

from my_proof.models.proof_response import ProofResponse


class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.input_dir = config.get('input_dir', '/input')
        self.output_dir = config.get('output_dir', '/output')
        self.proof_response = ProofResponse(dlp_id=config.get('dlp_id', 12345))
        
    def _load_json(self, file_path):
        """Helper method to load JSON files"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading {file_path}: {e}")
            return None
        
    def verify_ownership(self, account_data, posts_data):
        """
        Verify ownership of the social media data
        Returns ownership score between 0 and 1 and attributes dict
        """
        if not account_data or not posts_data:
            logging.error("Cannot verify ownership: data not loaded")
            return 0.0, {}
        
        # Extract verification data
        account_email = account_data.get('email', '')
        account_username = account_data.get('username', '')
        account_user_id = account_data.get('user_id', '')
        
        # Compare with config email (if provided)
        config_email = self.config.get('user_email', '')
        email_match = (config_email == account_email) if config_email else True
        
        # Check posts ownership
        user_id_matches = 0
        url_consistency = 0
        total_posts = len(posts_data)
        
        for post in posts_data:
            # Check if user_id in post matches account user_id
            if post.get('user_id') == account_user_id:
                user_id_matches += 1
                
            # Check if username appears in post_url
            post_url = post.get('post_url', '')
            if account_username in post_url:
                url_consistency += 1
        
        # Calculate ownership score components (0-1 range)
        user_id_score = user_id_matches / total_posts if total_posts > 0 else 0
        url_score = url_consistency / total_posts if total_posts > 0 else 0
        
        # Final ownership score (weighted average)
        ownership_score = (
            0.4 * (1.0 if email_match else 0.0) +  # Email match: 40% weight
            0.3 * user_id_score +                  # User ID match: 30% weight
            0.3 * url_score                        # URL consistency: 30% weight
        )
        
        # Additional attributes for transparency
        attributes = {
            'email_verified': email_match,
            'user_id_match_percentage': user_id_score * 100,
            'url_consistency_percentage': url_score * 100
        }
        
        logging.info(f"Ownership verification: {ownership_score:.2f}")
        return ownership_score, attributes
    
    def assess_quality(self, posts_data):
        """
        Assess the quality of social media data
        Returns quality score between 0 and 1 and attributes dict
        """
        if not posts_data:
            logging.error("Cannot assess quality: posts data not loaded")
            return 0.0, {}
        
        total_posts = len(posts_data)
        if total_posts == 0:
            return 0.0, {}
        
        # Calculate quality metrics
        engagement_scores = []
        content_length_scores = []
        media_scores = []
        
        # Min/max values for normalization
        min_content_length = 10  # Minimum content length to consider
        ideal_content_length = 280  # Ideal content length (Twitter standard)
        
        for post in posts_data:
            # 1. Engagement Score (likes, comments, shares, views)
            engagement = post.get('engagement', {})
            total_engagement = (
                engagement.get('likes', 0) + 
                engagement.get('comments', 0) + 
                engagement.get('shares', 0) + 
                engagement.get('retweets', 0)  # include retweets for X platform
            )
            
            # Calculate engagement rate (engagement / views)
            views = engagement.get('views', 0)
            engagement_rate = total_engagement / views if views > 0 else 0
            # Normalize engagement rate (0-5% is considered good)
            engagement_score = min(engagement_rate * 20, 1.0)
            engagement_scores.append(engagement_score)
            
            # 2. Content Length Score
            content = post.get('content', '')
            content_length = len(content)
            # Score based on content length (prefer neither too short nor too long)
            if content_length < min_content_length:
                content_score = content_length / min_content_length
            else:
                # Optimal range around ideal_content_length
                content_score = min(1.0, content_length / ideal_content_length)
                # Penalize if too long
                if content_length > ideal_content_length * 1.5:
                    content_score = max(0.7, 1.0 - (content_length - ideal_content_length * 1.5) / 1000)
            
            content_length_scores.append(content_score)
            
            # 3. Media Score (presence and variety)
            media = post.get('media', [])
            if len(media) > 0:
                # Bonus for multiple media
                media_score = min(1.0, 0.8 + 0.1 * len(media))
            else:
                media_score = 0.5  # Base score for text-only posts
            
            media_scores.append(media_score)
        
        # Calculate average scores
        avg_engagement_score = sum(engagement_scores) / total_posts
        avg_content_score = sum(content_length_scores) / total_posts
        avg_media_score = sum(media_scores) / total_posts
        
        # Overall quality score (weighted average)
        quality_score = (
            0.5 * avg_engagement_score +  # Engagement: 50% weight
            0.3 * avg_content_score +     # Content quality: 30% weight
            0.2 * avg_media_score         # Media presence: 20% weight
        )
        
        # Additional attributes for transparency
        attributes = {
            'engagement_score': avg_engagement_score * 100,
            'content_score': avg_content_score * 100,
            'media_score': avg_media_score * 100
        }
        
        logging.info(f"Quality assessment: {quality_score:.2f}")
        return quality_score, attributes
    
    def verify_authenticity(self, account_data, posts_data):
        """
        Verify the authenticity of posts based on URL structures and platform consistency
        Returns an authenticity score between 0 and 1 and attributes dict
        """
        # Initialize metrics
        total_posts = len(posts_data)
        valid_urls = 0
        
        # Define platform-specific URL patterns
        url_patterns = {
            "X": ["https://x.com/", "https://twitter.com/"],
            "Instagram": ["https://www.instagram.com/", "https://instagram.com/"],
            "LinkedIn": ["https://www.linkedin.com/"],
            "Facebook": ["https://www.facebook.com/", "https://facebook.com/"]
        }
        
        # Check each post
        for post in posts_data:
            platform = post.get("platform")
            post_url = post.get("post_url", "")
            
            # Skip if platform or URL is missing
            if not platform or not post_url:
                continue
            
            # Check if URL is consistent with the claimed platform
            valid_url = False
            if platform in url_patterns:
                for pattern in url_patterns[platform]:
                    if post_url.startswith(pattern):
                        valid_url = True
                        break
            
            if valid_url:
                valid_urls += 1
        
        # Calculate authenticity score
        authenticity_score = valid_urls / total_posts if total_posts > 0 else 0
        
        # Add attributes to track
        attributes = {
            "valid_urls_percentage": (valid_urls / total_posts * 100) if total_posts > 0 else 0,
        }
        
        return authenticity_score, attributes

    def verify_time_consistency(self, posts_data):
        """
        Verify the time consistency of posts based on chronological order,
        future dates, and posting frequency
        Returns a time consistency score between 0 and 1 and attributes dict
        """
        # Initialize metrics
        total_posts = len(posts_data)
        if total_posts <= 1:
            return 1.0, {"time_consistency_issues": 0}
        
        # Sort posts by date (oldest to newest)
        try:
            sorted_posts = sorted(posts_data, key=lambda x: parser.parse(x.get("posted_at", "2000-01-01T00:00:00Z")))
        except Exception as e:
            logging.error(f"Error parsing dates: {e}")
            return 0.0, {"time_consistency_issues": 100}
        
        # Get current time for future date check
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Initialize counters for issues
        future_dates = 0
        unusual_frequency = 0
        
        # Check for future dates and unusual posting frequency
        prev_date = None
        min_reasonable_interval = datetime.timedelta(seconds=10)  # Minimum reasonable time between posts
        
        for post in sorted_posts:
            try:
                post_date = parser.parse(post.get("posted_at"))
                
                # Check for future dates
                if post_date > current_time:
                    future_dates += 1
                
                # Check posting frequency (not applicable for first post)
                if prev_date is not None:
                    interval = post_date - prev_date
                    if interval < min_reasonable_interval:
                        unusual_frequency += 1
                
                prev_date = post_date
                
            except Exception as e:
                logging.error(f"Error processing date for post {post.get('post_id')}: {e}")
                continue
        
        # Calculate percentage of posts with time consistency issues
        total_issues = future_dates + unusual_frequency
        issue_percentage = (total_issues / total_posts) * 100
        
        # Calculate time consistency score (inverse of issue percentage)
        time_score = 1.0 - (total_issues / total_posts)
        time_score = max(0.0, min(1.0, time_score))  # Clamp between 0 and 1
        
        # Create attributes
        attributes = {
            "time_consistency_issues": issue_percentage,
            "future_dates": future_dates,
            "unusual_posting_frequency": unusual_frequency
        }
        
        return time_score, attributes

    def generate(self) -> ProofResponse:
        """Generate proof and return it"""
        logging.info("Starting proof generation")
        
        try:
            # Load data
            account_data = self._load_json(os.path.join(self.input_dir, "account.json"))
            posts_data = self._load_json(os.path.join(self.input_dir, "posts.json"))
            metadata = self._load_json(os.path.join(self.input_dir, "metadata.json"))
            
            if not account_data or not posts_data:
                logging.error("Failed to load required data files")
                return self.proof_response
            
            # Verify ownership
            ownership_score, ownership_attrs = self.verify_ownership(account_data, posts_data)
            
            # Assess quality
            quality_score, quality_attrs = self.assess_quality(posts_data)
            
            # Verify authenticity
            authenticity_score, authenticity_attrs = self.verify_authenticity(account_data, posts_data)
            
            # Verify time consistency
            time_score, time_attrs = self.verify_time_consistency(posts_data)
            
            # Combine attributes
            attributes = {**ownership_attrs, **quality_attrs, **authenticity_attrs, **time_attrs}
            self.proof_response.attributes = attributes
            
            # Calculate overall score (weighted average)
            self.proof_response.ownership = ownership_score
            self.proof_response.quality = quality_score
            
            # Authenticity now includes time consistency as part of its score
            self.proof_response.authenticity = (authenticity_score + time_score) / 2  
            
            # Overall weighted score: 40% ownership, 30% quality, 30% combined authenticity
            self.proof_response.score = (0.4 * ownership_score) + (0.3 * quality_score) + (0.3 * self.proof_response.authenticity)
            
            # Determine if proof is valid (minimum thresholds)
            self.proof_response.valid = (
                ownership_score >= 0.7 and
                quality_score >= 0.5 and
                authenticity_score >= 0.9 and  # Strict threshold for URL authenticity
                time_score >= 0.8  # Strict threshold for time consistency
            )
            
            # Set metadata
            dlp_id = metadata.get('dlp_id', self.config.get('dlp_id', 12345)) if metadata else self.config.get('dlp_id', 12345)
            self.proof_response.metadata = {
                'dlp_id': dlp_id,
                'timestamp': datetime.datetime.now().isoformat(),
            }
                
        except Exception as e:
            logging.error(f"Error generating proof: {e}")
            self.proof_response.valid = False
            self.proof_response.score = 0
        
        return self.proof_response 