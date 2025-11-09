#!/usr/bin/env python3
"""
MeshGEMV Results Collector

This script collects results from MeshGEMV experiment output files and aggregates them into JSON format.
It extracts mean cycle counts and organizes results by parameters.

Supports both simulator and WSE-3 output files.
"""

import os
import sys
import json
import re
import argparse


def extract_mean_cycle_count(output_file):
    """
    Extract mean cycle count from an output file.

    Args:
        output_file: Path to the output file

    Returns:
        float or None: The mean cycle count, or None if not found
    """
    try:
        with open(output_file, 'r') as f:
            content = f.read()

            # Look for patterns like "mean cycle count = 123.45" or "mean_cycle_count: 123.45"
            patterns = [
                r'mean[_ ]cycle[_ ]count[:\s=]+([0-9.]+)',
                r'Mean[_ ]Cycle[_ ]Count[:\s=]+([0-9.]+)',
                r'cycle[_ ]count[:\s=]+([0-9.]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return float(match.group(1))

            return None

    except Exception as e:
        print(f"Warning: Failed to read {output_file}: {e}")
        return None


def collect_results(output_folder, json_output_file):
    """
    Collect all results from output files and save to JSON.

    Args:
        output_folder: Path to folder containing output files
        json_output_file: Path to output JSON file
    """
    if not os.path.exists(output_folder):
        print(f"Error: Output folder '{output_folder}' not found")
        sys.exit(1)

    results = []

    # Find all output files
    output_files = [f for f in os.listdir(output_folder) if f.startswith('output_') and f.endswith('.txt')]

    if not output_files:
        print(f"Warning: No output files found in '{output_folder}'")
        print("Make sure you have run simulations/executions first.")
        sys.exit(1)

    print(f"Found {len(output_files)} output files")
    print("Extracting results...")

    # Parse each file
    for output_file in sorted(output_files):
        # Extract parameters from filename: output_P{p}_M{m}_N{n}_G{g}.txt
        match = re.match(r'output_P(\d+)_M(\d+)_N(\d+)_G(\d+)\.txt', output_file)
        if not match:
            print(f"Warning: Skipping file with unexpected name: {output_file}")
            continue

        P, M, N, group_num = map(int, match.groups())

        # Extract mean cycle count
        full_path = os.path.join(output_folder, output_file)
        mean_cycle_count = extract_mean_cycle_count(full_path)

        if mean_cycle_count is None:
            print(f"Warning: Could not extract cycle count from {output_file}")
            continue

        results.append({
            "P": P,
            "M": M,
            "N": N,
            "group_num": group_num,
            "mean_cycle_count": mean_cycle_count
        })

        print(f"  P={P} M={M} N={N} group_num={group_num}: {mean_cycle_count}")

    # Sort results by P, M, N, group_num
    results.sort(key=lambda x: (x["P"], x["M"], x["N"], x["group_num"]))

    # Create output data structure
    output_data = {
        "total_experiments": len(results),
        "results": results
    }

    # Write to JSON file
    with open(json_output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSuccessfully collected {len(results)} results")
    print(f"Output saved to: {json_output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Collect MeshGEMV experiment results into JSON format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect simulator results (uses defaults)
  python collect_results.py --mode simulator

  # Collect WSE results (uses defaults)
  python collect_results.py --mode wse

  # Custom output folder
  python collect_results.py --mode simulator custom_outputs

  # Custom output folder and JSON file
  python collect_results.py --mode wse custom_outputs my_results.json
        """
    )

    parser.add_argument('--mode', required=True, choices=['simulator', 'wse'],
                        help='Mode: simulator or wse')
    parser.add_argument('output_folder', nargs='?',
                        help='Output folder containing result files (uses mode defaults if not specified)')
    parser.add_argument('json_output_file', nargs='?',
                        help='Output JSON file path (uses mode defaults if not specified)')

    args = parser.parse_args()

    # Set defaults based on mode
    if args.mode == 'simulator':
        default_output_folder = 'simulator_in_out/outputs'
        default_json_file = 'simulator_result.json'
    else:  # wse
        default_output_folder = 'wse_in_out/outputs'
        default_json_file = 'wse_result.json'

    output_folder = args.output_folder if args.output_folder else default_output_folder
    json_output_file = args.json_output_file if args.json_output_file else default_json_file

    print(f"Mode: {args.mode}")
    print(f"Output folder: {output_folder}")
    print(f"JSON output: {json_output_file}")
    print("-" * 80)

    collect_results(output_folder, json_output_file)


if __name__ == "__main__":
    main()
