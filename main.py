#!/usr/bin/env python3
"""
Helper script to run the Vana Social Media Proof of Contribution code directly.
"""
import os
import sys
from my_proof.__main__ import run

if __name__ == "__main__":
    # Ensure we can import my_proof module
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Run the proof generation
    run() 