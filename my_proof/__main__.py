import json
import logging
import os
import sys
import traceback
import zipfile
from typing import Dict, Any

from my_proof.proof import Proof

# Development environment path detection
if os.path.exists('./input') and os.path.exists('./output'):
    INPUT_DIR, OUTPUT_DIR = './input', './output'
else:
    INPUT_DIR, OUTPUT_DIR = '/input', '/output'

logging.basicConfig(level=logging.INFO, format='%(message)s')


def load_config() -> Dict[str, Any]:
    """Load proof configuration from environment variables."""
    config = {
        'dlp_id': int(os.environ.get('DLP_ID', 12345)),
        'input_dir': INPUT_DIR,
        'output_dir': OUTPUT_DIR,
        'user_email': os.environ.get('USER_EMAIL', None),
    }
    logging.info(f"Using config: {json.dumps(config, indent=2)}")
    return config


def run() -> None:
    """Generate proofs for all input files."""
    config = load_config()
    input_files_exist = os.path.isdir(INPUT_DIR) and bool(os.listdir(INPUT_DIR))

    if not input_files_exist:
        raise FileNotFoundError(f"No input files found in {INPUT_DIR}")
    
    # Extract any zip files in input directory
    extract_input()

    # Run proof generation
    proof = Proof(config)
    proof_response = proof.generate()

    # Write results to output file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "results.json")
    with open(output_path, 'w') as f:
        json.dump(proof_response.model_dump(), f, indent=2)
    
    logging.info(f"Proof generation complete:")
    logging.info(f"  Valid: {proof_response.valid}")
    logging.info(f"  Score: {proof_response.score:.2f}")
    logging.info(f"  Ownership: {proof_response.ownership:.2f}")
    logging.info(f"  Quality: {proof_response.quality:.2f}")
    logging.info(f"  Authenticity: {proof_response.authenticity:.2f}")


def extract_input() -> None:
    """
    If the input directory contains any zip files, extract them
    """
    for input_filename in os.listdir(INPUT_DIR):
        input_file = os.path.join(INPUT_DIR, input_filename)

        if zipfile.is_zipfile(input_file):
            with zipfile.ZipFile(input_file, 'r') as zip_ref:
                zip_ref.extractall(INPUT_DIR)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Error during proof generation: {e}")
        traceback.print_exc()
        sys.exit(1) 