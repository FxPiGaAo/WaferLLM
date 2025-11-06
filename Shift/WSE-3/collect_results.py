#!/usr/bin/env python3
"""
Collect simulation/WSE results from output folder into JSON format.

Usage:
    python collect_results.py --mode {simulator|wse} [output_folder] [json_output_file]

Required:
    --mode {simulator|wse}  Choose data source: 'simulator' or 'wse'

Optional:
    output_folder           Path to output folder (default depends on mode)
    json_output_file        Path to output JSON file (default depends on mode)

Defaults by mode:
    --mode simulator: simulator_in_out/outputs -> simulator_result.json
    --mode wse:       wse_in_out/outputs -> wse_result.json

Examples:
    python collect_results.py --mode simulator         # Uses simulator defaults
    python collect_results.py --mode wse               # Uses WSE defaults
    python collect_results.py --mode simulator custom_outputs results.json
"""

import os
import sys
import json
import re
import argparse
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
    parser = argparse.ArgumentParser(
        description='Collect simulation/WSE results from output folder into JSON format.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python collect_results.py --mode simulator                        # Uses simulator defaults
  python collect_results.py --mode wse                              # Uses WSE defaults
  python collect_results.py --mode simulator custom_outputs         # Custom folder
  python collect_results.py --mode wse custom_outputs results.json  # Custom folder and file

Defaults by mode:
  --mode simulator: simulator_in_out/outputs -> simulator_result.json
  --mode wse:       wse_in_out/outputs -> wse_result.json
        """
    )

    parser.add_argument(
        '--mode',
        choices=['simulator', 'wse'],
        required=True,
        help='Choose data source: "simulator" or "wse"'
    )
    parser.add_argument(
        'output_folder',
        nargs='?',
        help='Path to output folder (default depends on mode)'
    )
    parser.add_argument(
        'json_output_file',
        nargs='?',
        help='Path to output JSON file (default depends on mode)'
    )

    args = parser.parse_args()

    # Set default output folder based on mode
    if args.output_folder is None:
        if args.mode == 'simulator':
            args.output_folder = 'simulator_in_out/outputs'
        else:  # wse
            args.output_folder = 'wse_in_out/outputs'

    # Set default JSON output file based on mode
    if args.json_output_file is None:
        if args.mode == 'simulator':
            args.json_output_file = 'simulator_result.json'
        else:  # wse
            args.json_output_file = 'wse_result.json'

    print(f"Mode: {args.mode}")
    print(f"Reading from: {args.output_folder}")
    print(f"Writing to: {args.json_output_file}")
    print()

    collect_results(args.output_folder, args.json_output_file)


if __name__ == '__main__':
    main()
