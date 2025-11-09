#!/usr/bin/env python3
"""
Parallel MeshGEMV Simulator Runner

This script runs multiple MeshGEMV simulations in parallel using a pool of worker processes.
It reads parameter sets from an input file and executes run_sim.sh for each set.

Features:
  - Parallel execution using multiprocessing
  - Smart skip: automatically skips already-completed simulations
  - Progress tracking with detailed output
  - Error handling and logging
"""

import subprocess
import sys
import os
import time
from multiprocessing import Pool
import argparse


def run_simulation(params):
    """
    Run a single simulation with the given parameters.

    Args:
        params: tuple of (P, M, N, group_num, output_folder, preview_mode)

    Returns:
        tuple: (success, P, M, N, group_num, runtime, error_msg)
    """
    P, M, N, group_num, output_folder, preview_mode = params

    output_file = os.path.join(output_folder, f"output_P{P}_M{M}_N{N}_G{group_num}.txt")

    # Check if output already exists and contains valid results (skip feature)
    from datetime import datetime
    skip_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if os.path.exists(output_file):
        # Check if the file contains "Mean" which indicates successful data collection
        try:
            with open(output_file, 'r') as f:
                content = f.read()
                if "Mean" in content:
                    print(f"[{skip_timestamp}] ⊘ Skipped: P={P} M={M} N={N} group_num={group_num} (already ran - output file contains valid results)")
                    return (True, P, M, N, group_num, 0, "skipped")
                else:
                    # File exists but no valid results - need to re-run
                    if preview_mode:
                        print(f"[{skip_timestamp}] ▶ Will run: P={P} M={M} N={N} group_num={group_num} (previous run failed - no valid results found)")
                        return (False, P, M, N, group_num, 0, "will_run")
                    else:
                        print(f"[{skip_timestamp}] ⚠ Re-running: P={P} M={M} N={N} group_num={group_num} (previous run failed - no valid results found)")
                        # Continue to run the simulation below
        except Exception as e:
            # Could not read file - need to re-run
            if preview_mode:
                print(f"[{skip_timestamp}] ▶ Will run: P={P} M={M} N={N} group_num={group_num} (could not read output file: {e})")
                return (False, P, M, N, group_num, 0, "will_run")
            else:
                print(f"[{skip_timestamp}] ⚠ Re-running: P={P} M={M} N={N} group_num={group_num} (could not read output file: {e})")
                # Continue to run the simulation below
    else:
        # File doesn't exist - need to run
        if preview_mode:
            print(f"[{skip_timestamp}] ▶ Will run: P={P} M={M} N={N} group_num={group_num} (no output file found)")
            return (False, P, M, N, group_num, 0, "will_run")
        # If not preview mode, continue to run the simulation below

    # If in preview mode, we should have already returned by now
    if preview_mode:
        return (True, P, M, N, group_num, 0, "preview_done")

    # Run the simulation
    cmd = f"./run_sim.sh {P} {M} {N} {group_num}"

    # Print start time
    from datetime import datetime
    start_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{start_timestamp}] Running: {cmd} -> {output_file}")

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        runtime = time.time() - start_time

        # Write output to file
        with open(output_file, 'w') as f:
            f.write(f"Command: {cmd}\n")
            f.write(f"Exit code: {result.returncode}\n")
            f.write(f"Runtime: {runtime:.2f} seconds\n")
            f.write(f"\n{'='*80}\n")
            f.write(f"STDOUT:\n")
            f.write(f"{'='*80}\n")
            f.write(result.stdout)
            f.write(f"\n{'='*80}\n")
            f.write(f"STDERR:\n")
            f.write(f"{'='*80}\n")
            f.write(result.stderr)

        if result.returncode == 0:
            end_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{end_timestamp}] ✓ Completed: P={P} M={M} N={N} group_num={group_num} (Runtime: {runtime:.2f}s)")
            return (True, P, M, N, group_num, runtime, None)
        else:
            end_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{end_timestamp}] ✗ Failed: P={P} M={M} N={N} group_num={group_num} (Exit code: {result.returncode})")
            return (False, P, M, N, group_num, runtime, f"Exit code: {result.returncode}")

    except subprocess.TimeoutExpired:
        runtime = time.time() - start_time
        error_msg = "Timeout (>1 hour)"
        end_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{end_timestamp}] ✗ Failed: P={P} M={M} N={N} group_num={group_num} ({error_msg})")

        # Write timeout info to file
        with open(output_file, 'w') as f:
            f.write(f"Command: {cmd}\n")
            f.write(f"Error: {error_msg}\n")
            f.write(f"Runtime: {runtime:.2f} seconds\n")

        return (False, P, M, N, group_num, runtime, error_msg)

    except Exception as e:
        runtime = time.time() - start_time
        error_msg = str(e)
        end_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{end_timestamp}] ✗ Failed: P={P} M={M} N={N} group_num={group_num} (Error: {error_msg})")

        # Write error info to file
        with open(output_file, 'w') as f:
            f.write(f"Command: {cmd}\n")
            f.write(f"Error: {error_msg}\n")
            f.write(f"Runtime: {runtime:.2f} seconds\n")

        return (False, P, M, N, group_num, runtime, error_msg)


def main():
    parser = argparse.ArgumentParser(
        description='Run MeshGEMV simulations in parallel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use all defaults
  python parallel_sim.py

  # Custom number of processes
  python parallel_sim.py -n 8

  # Custom input file
  python parallel_sim.py -i my_params.txt

  # Limit to first 10 parameters
  python parallel_sim.py --max-params 10

  # Preview what will run or be skipped
  python parallel_sim.py --preview

  # Run only first parameter
  python parallel_sim.py --runonedp

  # Full specification
  python parallel_sim.py -i params.txt -o results -n 16 --max-params 100
        """
    )

    parser.add_argument('input_file', nargs='?', default='simulator_in_out/input/input.txt',
                        help='Input file with parameters (default: simulator_in_out/input/input.txt)')
    parser.add_argument('output_folder', nargs='?', default='simulator_in_out/outputs',
                        help='Output folder for results (default: simulator_in_out/outputs)')
    parser.add_argument('num_processes', nargs='?', type=int, default=4,
                        help='Number of parallel processes (default: 4)')
    parser.add_argument('-i', '--input', dest='input_file_flag',
                        help='Input file path (overrides positional argument)')
    parser.add_argument('-o', '--output', dest='output_folder_flag',
                        help='Output directory (overrides positional argument)')
    parser.add_argument('-n', '--num-processes', dest='num_processes_flag', type=int,
                        help='Number of parallel processes (overrides positional argument)')
    parser.add_argument('--max-params', type=int, default=None,
                        help='Maximum number of input parameters to execute (default: all)')
    parser.add_argument('--preview', action='store_true',
                        help='Preview mode: show what would be run or skipped without actually executing')
    parser.add_argument('--runonedp', action='store_true',
                        help='Run only the first parameter (for testing)')

    args = parser.parse_args()

    # Prioritize flag arguments over positional arguments
    input_file = args.input_file_flag if args.input_file_flag else args.input_file
    output_folder = args.output_folder_flag if args.output_folder_flag else args.output_folder
    num_processes = args.num_processes_flag if args.num_processes_flag else args.num_processes

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Read input file
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)

    params_list = []
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) == 4:
                    P, M, N, group_num = map(int, parts)
                    params_list.append((P, M, N, group_num, output_folder, args.preview))

    if not params_list:
        print(f"Error: No valid parameters found in '{input_file}'")
        sys.exit(1)

    # If --runonedp flag is set, run only the first parameter
    if args.runonedp:
        print("Running only the first parameter (--runonedp flag set)")
        params_list = params_list[:1]
    # If --max-params is set, limit the number of parameters
    elif args.max_params is not None:
        if args.max_params < len(params_list):
            print(f"Limiting to first {args.max_params} parameters (--max-params flag set)")
            params_list = params_list[:args.max_params]

    print(f"Found {len(params_list)} simulation(s) to {'preview' if args.preview else 'run'}")
    if args.preview:
        print(f"Preview mode enabled - no simulations will be executed")
    print(f"Using {num_processes} parallel processes")
    print(f"Output folder: {output_folder}")
    print("-" * 80)

    # Run simulations in parallel (or preview)
    start_time = time.time()

    # Track progress in real-time
    results = []
    completed = 0
    successful = 0
    skipped = 0
    failed = 0
    will_run = 0
    total = len(params_list)

    with Pool(processes=num_processes) as pool:
        # Use imap_unordered for real-time progress tracking
        for result in pool.imap_unordered(run_simulation, params_list):
            results.append(result)
            completed += 1

            # Update counters based on result
            success, P, M, N, group_num, runtime, error = result
            if success and error == "skipped":
                skipped += 1
            elif success:
                successful += 1
            elif error == "will_run":
                will_run += 1
            else:
                failed += 1

            # Show real-time progress
            from datetime import datetime
            remaining = total - completed
            progress_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if args.preview:
                print(f"[{progress_timestamp}] Progress: {completed}/{total} | Will run: {will_run} | Skipped: {skipped} | Remaining: {remaining}")
            else:
                print(f"[{progress_timestamp}] Progress: {completed}/{total} completed | Success: {successful} | Skipped: {skipped} | Failed: {failed} | Remaining: {remaining}")

    total_time = time.time() - start_time

    # Summary
    print("-" * 80)
    if args.preview:
        print("Preview Summary:")
        print(f"Total parameters: {total}")
        print(f"Will run: {will_run}")
        print(f"Will skip: {skipped}")
    else:
        print("Summary:")
        print(f"Total: {total} simulations")
        print(f"Successful: {successful}")
        print(f"Skipped: {skipped}")
        print(f"Failed: {failed}")
    print(f"Total runtime: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")

    # Print runtimes for successful runs
    if successful > 0:
        print("\nRuntimes:")
        for success, P, M, N, group_num, runtime, error in results:
            if success and error != "skipped":
                print(f"  P={P} M={M} N={N} group_num={group_num}: {runtime:.2f}s")

    # Print failed runs
    if failed > 0:
        print("\nFailed runs:")
        for success, P, M, N, group_num, runtime, error in results:
            if not success:
                print(f"  P={P} M={M} N={N} group_num={group_num}: {error}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
