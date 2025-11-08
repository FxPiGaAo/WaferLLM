#!/usr/bin/env python3
"""
Generate parameter sets for parallel MeshGEMM simulations or WSE executions.

This script generates a grid of parameters P, M, K, N based on specified ranges and rules.

MeshGEMM computes [M,N] = [M,K] @ [K,N] on a P×P PE grid.

Simulator mode:
- P: Start value, end value, step size (user-defined)
- M, K, N: User-defined ranges with step sizes
- No parameter limits (user has full control)

WSE mode:
- P: User-defined range with step size
- M, K, N: User-defined ranges with step sizes
- No parameter limits (user has full control)

Usage:
    python generate_params.py --simulator [output_file] [P_start] [P_end] [P_step] [M_start] [M_end] [M_step] [K_start] [K_end] [K_step] [N_start] [N_end] [N_step]
    python generate_params.py --wse [output_file] [P_start] [P_end] [P_step] [M_start] [M_end] [M_step] [K_start] [K_end] [K_step] [N_start] [N_end] [N_step]

    --simulator: Generate parameters for simulator
    --wse: Generate parameters for WSE

    Default output_file: simulator_in_out/input/input_temp.txt (simulator) or wse_in_out/input/input_temp.txt (wse)
    Default P_start: 16, P_end: 128, P_step: 16
    Default M_start: 1024, M_end: 1024, M_step: 1024
    Default K_start: 1024, K_end: 1024, K_step: 1024
    Default N_start: 1024, N_end: 1024, N_step: 1024

Examples:
    # Generate with all defaults (P: 16-128 step 16, M=K=N=1024)
    python generate_params.py --simulator

    # Custom P range, default M,K,N
    python generate_params.py --simulator params.txt 32 256 32

    # Custom P and M ranges
    python generate_params.py --simulator params.txt 16 64 16 512 2048 512

    # Full custom specification
    python generate_params.py --simulator params.txt 16 64 16 512 2048 512 1024 4096 1024 512 2048 512
"""

import sys
from pathlib import Path


def generate_parameters(P_start, P_end, P_step, M_start, M_end, M_step, K_start, K_end, K_step, N_start, N_end, N_step):
    """
    Generate parameter combinations based on the ranges.

    Args:
        P_start, P_end, P_step: Range for P (PE grid dimension)
        M_start, M_end, M_step: Range for M (rows in first matrix)
        K_start, K_end, K_step: Range for K (shared dimension)
        N_start, N_end, N_step: Range for N (columns in second matrix)

    Returns:
        List of tuples (P, M, K, N)
    """
    params = []

    # Generate all combinations
    P = P_start
    while P <= P_end:
        M = M_start
        while M <= M_end:
            K = K_start
            while K <= K_end:
                N = N_start
                while N <= N_end:
                    params.append((P, M, K, N))
                    N += N_step
                K += K_step
            M += M_step
        P += P_step

    return params


def generate_wse_parameters(P_start, P_end, P_step):
    """
    Generate WSE parameter combinations with M, K, N as multiples of P.

    For each P value, M, K, N iterate through: P, 2P, 3P, 8P

    Args:
        P_start: Starting value for P
        P_end: Ending value for P (inclusive)
        P_step: Step size for P

    Returns:
        List of tuples (P, M, K, N)
    """
    params = []
    multipliers = [1, 2, 3, 8]  # P, 2P, 3P, 8P

    P = P_start
    while P <= P_end:
        for m_mult in multipliers:
            for k_mult in multipliers:
                for n_mult in multipliers:
                    M = P * m_mult
                    K = P * k_mult
                    N = P * n_mult
                    params.append((P, M, K, N))
        P += P_step

    return params


def main():
    # Default values
    default_simulator_output_file = "simulator_in_out/input/input_temp.txt"
    default_wse_output_file = "wse_in_out/input/input_temp.txt"

    # Simulator defaults
    default_sim_P_start, default_sim_P_end, default_sim_P_step = 16, 128, 16
    default_M_start, default_M_end, default_M_step = 1024, 1024, 1024
    default_K_start, default_K_end, default_K_step = 1024, 1024, 1024
    default_N_start, default_N_end, default_N_step = 1024, 1024, 1024

    # WSE defaults: P from 16 to 730 step 64, M/K/N = P, 2P, 3P, 8P
    default_wse_P_start, default_wse_P_end, default_wse_P_step = 16, 730, 64

    # Parse arguments
    args = sys.argv[1:]
    wse_mode = None

    # Check for --wse or --simulator flag
    if "--wse" in args:
        wse_mode = True
        args.remove("--wse")
    elif "--simulator" in args:
        wse_mode = False
        args.remove("--simulator")

    # If no mode specified, show error and exit
    if wse_mode is None:
        print("Error: You must specify a mode using --simulator or --wse")
        print("\nUsage:")
        print("  python generate_params.py --simulator [output_file] [P_start] [P_end] [P_step] [M_start] [M_end] [M_step] [K_start] [K_end] [K_step] [N_start] [N_end] [N_step]")
        print("  python generate_params.py --wse [output_file] [P_start] [P_end] [P_step] [M_start] [M_end] [M_step] [K_start] [K_end] [K_step] [N_start] [N_end] [N_step]")
        print("\nExamples:")
        print("  python generate_params.py --simulator")
        print("  python generate_params.py --wse")
        print("  python generate_params.py --simulator params.txt 16 64 16")
        print("  python generate_params.py --wse params.txt 16 128 16 1024 4096 1024")
        sys.exit(1)

    # Set defaults based on mode
    default_output_file = default_wse_output_file if wse_mode else default_simulator_output_file

    # For WSE mode, we only need P parameters (M/K/N are derived)
    # For Simulator mode, we need all parameters
    max_args = 4 if wse_mode else 13  # output_file + P_start + P_end + P_step for WSE

    # Show help if too many positional arguments
    if len(args) > max_args:
        print("Error: Too many arguments")
        print("\nUsage:")
        print("  python generate_params.py --simulator [output_file] [P_start] [P_end] [P_step] [M_start] [M_end] [M_step] [K_start] [K_end] [K_step] [N_start] [N_end] [N_step]")
        print("  python generate_params.py --wse [output_file] [P_start] [P_end] [P_step]")
        print("\nDefaults:")
        if wse_mode:
            print(f"  output_file: {default_output_file}")
            print(f"  P: {default_wse_P_start} to {default_wse_P_end} step {default_wse_P_step}")
            print(f"  M, K, N: For each P, iterate through P, 2P, 3P, 8P")
        else:
            print(f"  output_file: {default_output_file}")
            print(f"  P: {default_sim_P_start} to {default_sim_P_end} step {default_sim_P_step}")
            print(f"  M: {default_M_start} to {default_M_end} step {default_M_step}")
            print(f"  K: {default_K_start} to {default_K_end} step {default_K_step}")
            print(f"  N: {default_N_start} to {default_N_end} step {default_N_step}")
        sys.exit(1)

    # Parse positional arguments with defaults
    output_file = args[0] if len(args) > 0 else default_output_file

    if wse_mode:
        # WSE mode: only P parameters needed
        P_start = int(args[1]) if len(args) > 1 else default_wse_P_start
        P_end = int(args[2]) if len(args) > 2 else default_wse_P_end
        P_step = int(args[3]) if len(args) > 3 else default_wse_P_step
        # M, K, N not used in WSE mode (generated from P)
        M_start = M_end = M_step = None
        K_start = K_end = K_step = None
        N_start = N_end = N_step = None
    else:
        # Simulator mode: all parameters
        P_start = int(args[1]) if len(args) > 1 else default_sim_P_start
        P_end = int(args[2]) if len(args) > 2 else default_sim_P_end
        P_step = int(args[3]) if len(args) > 3 else default_sim_P_step
        M_start = int(args[4]) if len(args) > 4 else default_M_start
        M_end = int(args[5]) if len(args) > 5 else default_M_end
        M_step = int(args[6]) if len(args) > 6 else default_M_step
        K_start = int(args[7]) if len(args) > 7 else default_K_start
        K_end = int(args[8]) if len(args) > 8 else default_K_end
        K_step = int(args[9]) if len(args) > 9 else default_K_step
        N_start = int(args[10]) if len(args) > 10 else default_N_start
        N_end = int(args[11]) if len(args) > 11 else default_N_end
        N_step = int(args[12]) if len(args) > 12 else default_N_step

    # Validate inputs
    if P_start <= 0 or P_end <= 0 or P_step <= 0:
        print("Error: P parameters must be positive integers")
        sys.exit(1)
    if P_start > P_end:
        print("Error: P_start must be less than or equal to P_end")
        sys.exit(1)

    # Additional validation for simulator mode
    if not wse_mode:
        if M_start <= 0 or M_end <= 0 or M_step <= 0:
            print("Error: M parameters must be positive integers")
            sys.exit(1)
        if K_start <= 0 or K_end <= 0 or K_step <= 0:
            print("Error: K parameters must be positive integers")
            sys.exit(1)
        if N_start <= 0 or N_end <= 0 or N_step <= 0:
            print("Error: N parameters must be positive integers")
            sys.exit(1)
        if M_start > M_end:
            print("Error: M_start must be less than or equal to M_end")
            sys.exit(1)
        if K_start > K_end:
            print("Error: K_start must be less than or equal to K_end")
            sys.exit(1)
        if N_start > N_end:
            print("Error: N_start must be less than or equal to N_end")
            sys.exit(1)

    # Print configuration
    mode_str = "WSE" if wse_mode else "Simulator"
    print(f"Parameter Generation Configuration ({mode_str} mode):")
    print("=" * 60)
    print(f"Output file: {output_file}")
    print(f"P range: {P_start} to {P_end} (step: {P_step})")
    if wse_mode:
        print(f"M, K, N: For each P, iterate through P, 2P, 3P, 8P")
    else:
        print(f"M range: {M_start} to {M_end} (step: {M_step})")
        print(f"K range: {K_start} to {K_end} (step: {K_step})")
        print(f"N range: {N_start} to {N_end} (step: {N_step})")
    print("=" * 60)
    print()

    # Generate parameters
    if wse_mode:
        params = generate_wse_parameters(P_start, P_end, P_step)
    else:
        params = generate_parameters(P_start, P_end, P_step, M_start, M_end, M_step, K_start, K_end, K_step, N_start, N_end, N_step)

    # Print preview
    print(f"Generated {len(params)} parameter sets:")
    print("-" * 60)
    print("P    M    K    N")
    print("-" * 60)
    for p, m, k, n in params[:20]:  # Show first 20
        print(f"{p:<4} {m:<4} {k:<4} {n}")
    if len(params) > 20:
        print("...")
        print(f"(showing first 20 of {len(params)} total)")
    print("-" * 60)
    print()

    # Write to file
    with open(output_file, 'w') as f:
        f.write(f"# Auto-generated parameter sets ({mode_str} mode)\n")
        f.write(f"# P range: {P_start} to {P_end} (step: {P_step})\n")
        if wse_mode:
            f.write(f"# M, K, N: For each P, iterate through P, 2P, 3P, 8P\n")
        else:
            f.write(f"# M range: {M_start} to {M_end} (step: {M_step})\n")
            f.write(f"# K range: {K_start} to {K_end} (step: {K_step})\n")
            f.write(f"# N range: {N_start} to {N_end} (step: {N_step})\n")
        f.write("# Format: P M K N\n")
        f.write("# MeshGEMM computes [M,N] = [M,K] @ [K,N] on P×P PE grid\n")
        f.write("#\n")
        for p, m, k, n in params:
            f.write(f"{p} {m} {k} {n}\n")

    print(f"✓ Successfully wrote {len(params)} parameter sets to '{output_file}'")
    if wse_mode:
        print(f"\nYou can now run WSE executions with:")
        print(f"  python parallel_wse.py {output_file}")
    else:
        print(f"\nYou can now run simulations with:")
        print(f"  python parallel_sim.py {output_file}")


if __name__ == "__main__":
    main()
