# Vana Social Media Data Validator (Proof of Contribution)

This project provides a Proof of Contribution (PoC) mechanism for social media data and is designed to run on Vana's Satya network.

## Overview

This proof of contribution system validates the following properties of social media data:

1. **Ownership**: Verifies that the data genuinely belongs to the user.
2. **Quality**: Evaluates whether the data has high engagement, appropriate content length, and various media content.
3. **Authenticity**: Checks the authenticity of data through URL structures and time consistency.

## How It Works

The proof mechanism follows these steps:

1. Reads JSON files (account.json, posts.json, and metadata.json) from the `/input` directory.
2. Verifies ownership by validating email, user ID, and URL consistency.
3. Calculates quality score based on engagement rate, content length, and media presence.
4. Performs authenticity validation by checking URL patterns and time consistency.
5. Writes the validation results to `/output/results.json`.

## Data Format

The system expects the following input data:

### account.json

```json
{
  "user_id": "user123456",
  "username": "socialmedia_user",
  "email": "user@example.com",
  "profile_info": {
    "display_name": "Social Media User",
    "bio": "Digital content creator",
    "location": "Istanbul, Turkey"
  }
}
```

### posts.json

```json
[
  {
    "post_id": "post98765",
    "user_id": "user123456",
    "platform": "X",
    "post_url": "https://x.com/socialmedia_user/status/123456789",
    "content": "Sample post content",
    "posted_at": "2023-12-15T10:23:45Z",
    "media": [
      {
        "type": "image",
        "url": "https://example.com/media/image12345.jpg",
        "alt_text": "Alt text"
      }
    ],
    "engagement": {
      "likes": 87,
      "comments": 12,
      "shares": 5,
      "views": 1250
    }
  }
]
```

## Results

Results are written to `/output/results.json` in the following format:

```json
{
  "dlp_id": 12345,
  "valid": true,
  "score": 0.94,
  "authenticity": 1.0,
  "ownership": 1.0,
  "quality": 0.79,
  "uniqueness": 0.0,
  "attributes": {
    "email_verified": true,
    "user_id_match_percentage": 100.0,
    "url_consistency_percentage": 100.0,
    "engagement_score": 100.0,
    "content_score": 45.64,
    "media_score": 76.0,
    "valid_urls_percentage": 100.0,
    "time_consistency_issues": 0.0,
    "future_dates": 0,
    "unusual_posting_frequency": 0
  },
  "metadata": {
    "dlp_id": 12345,
    "timestamp": "2023-12-20T08:30:45.123456Z"
  }
}
```

## Local Development

To test the proof mechanism on your local machine with Docker:

```bash
docker build -t vana-social-media-poc .
docker run \
  --rm \
  --volume "$(pwd)/input:/input" \
  --volume "$(pwd)/output:/output" \
  --env USER_EMAIL=user@example.com \
  vana-social-media-poc
```

## Satya Network Integration

This proof mechanism is designed to run on Vana's Satya network with the security guarantees provided by Intel TDX (Trust Domain Extensions). By running in a Trusted Execution Environment (TEE), it provides secure validation while preserving data privacy.
