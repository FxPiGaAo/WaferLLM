#!/usr/bin/env python3
"""
Collect simulation results from output folder into JSON format.

Usage:
    python collect_results.py [output_folder] [json_output_file]

    Default output_folder: outputs
    Default json_output_file: results.json

Examples:
    python collect_results.py                          # Uses defaults: outputs -> results.json
    python collect_results.py test_outputs             # Custom folder, default file
    python collect_results.py test_outputs results.json # Custom folder and file
"""

import os
import sys
import json
import re
from pathlib import Path


def parse_output_file(filepath):
    """
    Parse a single output file to extract P, L, M, N and mean cycle count.

    Args:
        filepath: Path to the output file

    Returns:
        dict with keys: P, L, M, N, mean_cycle_count
        None if parsing fails
    """
    # Extract parameters from filename (e.g., output_P10_L10_M10_N10.txt)
    filename = os.path.basename(filepath)
    match = re.match(r'output_P(\d+)_L(\d+)_M(\d+)_N(\d+)\.txt', filename)

    if not match:
        print(f"Warning: Cannot parse filename {filename}")
        return None

    P, L, M, N = map(int, match.groups())

    # Read file and find mean cycle count
    mean_cycle_count = None
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('Mean cycle count:'):
                    # Extract the number after "Mean cycle count: "
                    parts = line.split(':')
                    if len(parts) >= 2:
                        mean_cycle_count = float(parts[1].strip())
                        break
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

    if mean_cycle_count is None:
        print(f"Warning: Could not find mean cycle count in {filename}")
        return None

    return {
        'P': P,
        'L': L,
        'M': M,
        'N': N,
        'mean_cycle_count': mean_cycle_count
    }


def collect_results(output_folder, json_output_file):
    """
    Collect all results from output folder and save to JSON.

    Args:
        output_folder: Path to folder containing output files
        json_output_file: Path to output JSON file
    """
    output_folder = Path(output_folder)

    if not output_folder.exists():
        print(f"Error: Output folder {output_folder} does not exist")
        sys.exit(1)

    # Find all output files
    output_files = list(output_folder.glob('output_P*_L*_M*_N*.txt'))

    if not output_files:
        print(f"Warning: No output files found in {output_folder}")
        results = []
    else:
        print(f"Found {len(output_files)} output file(s)")

        # Parse each file
        results = []
        for filepath in sorted(output_files):
            print(f"Processing {filepath.name}...")
            result = parse_output_file(filepath)
            if result:
                results.append(result)

        print(f"\nSuccessfully parsed {len(results)} result(s)")

    # Save to JSON
    output_data = {
        'total_experiments': len(results),
        'results': results
    }

    with open(json_output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Results saved to {json_output_file}")


def main():
    # Default values
    default_output_folder = "simulator_in_out/outputs"
    default_json_file = "results.json"

    if len(sys.argv) > 3:
        print("Usage: python collect_results.py [output_folder] [json_output_file]")
        print("\nDefaults:")
        print(f"  output_folder: {default_output_folder}")
        print(f"  json_output_file: {default_json_file}")
        print("\nExamples:")
        print("  python collect_results.py                          # Use all defaults")
        print("  python collect_results.py test_outputs             # Custom folder, default file")
        print("  python collect_results.py test_outputs results.json # Custom folder and file")
        sys.exit(1)

    # Parse arguments with defaults
    output_folder = sys.argv[1] if len(sys.argv) > 1 else default_output_folder
    json_output_file = sys.argv[2] if len(sys.argv) > 2 else default_json_file

    collect_results(output_folder, json_output_file)


if __name__ == '__main__':
    main()
