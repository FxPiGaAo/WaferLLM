#!/usr/bin/env python3
"""
Parallel simulation runner script for MeshGEMM.
Reads input parameters from a file and runs run_sim.sh in parallel.

Usage:
    python parallel_sim.py [options]

Arguments (all optional):
    input_file       Path to input file (default: simulator_in_out/input/input.txt)
    output_folder    Output directory (default: simulator_in_out/outputs)
    num_processes    Number of parallel processes (default: 4)

    OR use flags:
    -n, --num-processes NUM   Number of parallel processes
    -i, --input FILE          Input file path
    -o, --output DIR          Output directory
    --runonedp                Run only the first input parameter (always run, no skip)

Input file format (each line):
    P M K N
    # MeshGEMM computes [M,N] = [M,K] @ [K,N] on P×P PE grid

Examples:
    python parallel_sim.py                        # Use all defaults
    python parallel_sim.py -n 8                   # Only specify process count
    python parallel_sim.py --num-processes 16     # Same as above
    python parallel_sim.py params.txt             # Custom input, default output and processes
    python parallel_sim.py params.txt simulator_in_out/outputs 8   # Custom input, output, and processes
    python parallel_sim.py -i params.txt -n 8     # Using flags
    python parallel_sim.py --runonedp             # Run only first param, always run
"""

import sys
import os
import subprocess
from multiprocessing import Pool
from pathlib import Path
import time
import argparse


def run_simulation(args):
    """Run a single simulation with given parameters."""
    params, output_folder, script_path, skip_existing = args
    p, m, k, n = params.strip().split()

    # Create output filename based on parameters
    output_file = os.path.join(output_folder, f"output_P{p}_M{m}_K{k}_N{n}.txt")

    # Check if output file already exists (only if skip_existing is True)
    if skip_existing and os.path.exists(output_file):
        print(f"⊘ Skipped: P={p} M={m} K={k} N={n} (already ran - output file exists)")
        return (params, 0, 0.0)  # Return success code and zero runtime since simulation was skipped

    # Construct command
    cmd = [script_path, p, m, k, n]

    print(f"Running: {' '.join(cmd)} -> {output_file}")

    try:
        # Measure runtime
        start_time = time.time()

        # Run the simulation and capture output
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )

        end_time = time.time()
        runtime = end_time - start_time

        # Write output to file
        with open(output_file, 'w') as f:
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write(f"Exit code: {result.returncode}\n")
            f.write(f"Runtime: {runtime:.2f} seconds\n")
            f.write("-" * 80 + "\n")
            f.write(result.stdout)

        if result.returncode == 0:
            print(f"✓ Completed: P={p} M={m} K={k} N={n} (Runtime: {runtime:.2f}s)")
        else:
            print(f"✗ Failed (exit {result.returncode}): P={p} M={m} K={k} N={n} (Runtime: {runtime:.2f}s)")

        return (params, result.returncode, runtime)

    except Exception as e:
        error_msg = f"Error running simulation: {e}"
        print(f"✗ Error: P={p} M={m} K={k} N={n} - {e}")

        # Write error to output file
        with open(output_file, 'w') as f:
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write(f"Error: {error_msg}\n")

        return (params, -1, 0.0)


def main():
    # Default values
    default_input_file = "simulator_in_out/input/input.txt"
    default_output_folder = "simulator_in_out/outputs"
    default_num_processes = 4

    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Run MeshGEMM simulations in parallel with different parameter sets.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parallel_sim.py                        # Use all defaults
  python parallel_sim.py -n 8                   # Only specify process count
  python parallel_sim.py --num-processes 16     # Same as above
  python parallel_sim.py params.txt             # Custom input, default output and processes
  python parallel_sim.py params.txt simulator_in_out/outputs 8   # Positional: input, output, processes
  python parallel_sim.py -i params.txt -n 8     # Using flags
  python parallel_sim.py -i params.txt -o results -n 16  # All flags
  python parallel_sim.py --runonedp             # Run only first param, always run
        """
    )

    parser.add_argument('input_file', nargs='?', default=None,
                        help=f'Input file with parameters (default: {default_input_file})')
    parser.add_argument('output_folder', nargs='?', default=None,
                        help=f'Output directory (default: {default_output_folder})')
    parser.add_argument('num_processes', nargs='?', type=int, default=None,
                        help=f'Number of parallel processes (default: {default_num_processes})')

    parser.add_argument('-i', '--input', dest='input_flag',
                        help='Input file (alternative to positional argument)')
    parser.add_argument('-o', '--output', dest='output_flag',
                        help='Output directory (alternative to positional argument)')
    parser.add_argument('-n', '--num-processes', dest='num_processes_flag', type=int,
                        help='Number of parallel processes (alternative to positional argument)')
    parser.add_argument('--runonedp', action='store_true',
                        help='Run only the first input parameter (always run, never skip)')

    args = parser.parse_args()

    # Check SINGULARITYENV_SIMFABRIC_DEBUG environment variable
    simfabric_debug = os.environ.get('SINGULARITYENV_SIMFABRIC_DEBUG')
    if simfabric_debug is None:
        print("fast simulation!!!")
    else:
        print(f"SINGULARITYENV_SIMFABRIC_DEBUG={simfabric_debug}")
    print()

    # Determine final values (flags take precedence over positional arguments)
    input_file = args.input_flag or args.input_file or default_input_file
    output_folder = args.output_flag or args.output_folder or default_output_folder
    num_processes = args.num_processes_flag or args.num_processes or default_num_processes

    # Get absolute path to run_sim.sh
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "run_sim.sh")

    # Validate inputs
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)

    if not os.path.exists(script_path):
        print(f"Error: run_sim.sh not found at '{script_path}'")
        sys.exit(1)

    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # Read input parameters
    with open(input_file, 'r') as f:
        param_lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    if not param_lines:
        print("Error: No valid parameter lines found in input file")
        sys.exit(1)

    # If runonedp flag is set, only use the first parameter
    if args.runonedp:
        param_lines = [param_lines[0]]
        print("Running in runonedp mode: only first parameter will be processed")

    print(f"Found {len(param_lines)} simulation(s) to run")
    print(f"Using {num_processes} parallel processes")
    print(f"Output folder: {output_folder}")
    print("-" * 80)

    # Prepare arguments for each simulation
    # skip_existing is False when runonedp is enabled, True otherwise
    skip_existing = not args.runonedp
    args_list = [(params, output_folder, script_path, skip_existing) for params in param_lines]

    # Run simulations in parallel
    with Pool(processes=num_processes) as pool:
        results = pool.map(run_simulation, args_list)

    # Summary
    print("-" * 80)
    print("Summary:")
    successful = sum(1 for _, code, _ in results if code == 0)
    failed = len(results) - successful
    total_runtime = sum(runtime for _, _, runtime in results)
    print(f"Total: {len(results)} simulations")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total runtime: {total_runtime:.2f} seconds ({total_runtime/60:.2f} minutes)")

    # Show individual runtimes for completed simulations
    completed_with_runtime = [(params, runtime) for params, code, runtime in results if code == 0 and runtime > 0]
    if completed_with_runtime:
        print("\nRuntimes:")
        for params, runtime in completed_with_runtime:
            p, m, k, n = params.strip().split()
            print(f"  P={p} M={m} K={k} N={n}: {runtime:.2f}s")

    if failed > 0:
        print("\nFailed simulations:")
        for params, code, _ in results:
            if code != 0:
                print(f"  {params} (exit code: {code})")
        sys.exit(1)


if __name__ == "__main__":
    main()
