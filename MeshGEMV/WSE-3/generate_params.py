#!/usr/bin/env python3
"""
Parameter Set Generator for MeshGEMV Experiments

This script generates input parameter files for running MeshGEMV experiments
on either the Cerebras simulator or WSE-3 hardware.

MeshGEMV computes: [1,N] = [1,M] @ [M,N] on a P×P PE grid with group_num groups

Two modes:
  1. Simulator mode: Full control over all parameters (P, M, N, group_num)
  2. WSE mode: M, N automatically generated as multiples of P
"""

import sys
import os


def generate_simulator_params(
    output_file='simulator_in_out/input/input_temp.txt',
    P_start=16, P_end=128, P_step=16,
    M_start=1024, M_end=1024, M_step=1024,
    N_start=1024, N_end=1024, N_step=1024,
    group_num_start=8, group_num_end=8, group_num_step=8
):
    """Generate parameter sets for simulator mode with full control."""

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    params = []

    # Generate all combinations
    P = P_start
    while P <= P_end:
        M = M_start
        while M <= M_end:
            N = N_start
            while N <= N_end:
                group_num = group_num_start
                while group_num <= group_num_end:
                    params.append((P, M, N, group_num))
                    group_num += group_num_step
                N += N_step
            M += M_step
        P += P_step

    # Write to file
    with open(output_file, 'w') as f:
        f.write(f"# Auto-generated parameter sets (Simulator mode)\n")
        f.write(f"# P range: {P_start} to {P_end} (step: {P_step})\n")
        f.write(f"# M range: {M_start} to {M_end} (step: {M_step})\n")
        f.write(f"# N range: {N_start} to {N_end} (step: {N_step})\n")
        f.write(f"# group_num range: {group_num_start} to {group_num_end} (step: {group_num_step})\n")
        f.write(f"# Format: P M N group_num\n")
        f.write(f"# MeshGEMV computes [1,N] = [1,M] @ [M,N] on P×P PE grid with group_num groups\n")
        f.write(f"#\n")

        for p, m, n, g in params:
            f.write(f"{p} {m} {n} {g}\n")

    print(f"Generated {len(params)} parameter sets for simulator mode")
    print(f"Output: {output_file}")
    return len(params)


def generate_wse_params(
    output_file='wse_in_out/input/input_temp.txt',
    P_start=16, P_end=730, P_step=64,
    single_group_num=False
):
    """Generate parameter sets for WSE mode with M, N as multiples of P."""

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    params = []

    # For each P value, generate M, N as multiples of P
    # Using P, 2P, 3P, 8P for both M and N (starting from P)
    # group_num options: 2, 4, 8 (or just 8 if single_group_num is True)
    multipliers = [1, 2, 3, 8]
    group_nums = [8] if single_group_num else [2, 4, 8]

    P = P_start
    while P <= P_end:
        for m_mult in multipliers:
            M = P * m_mult
            for n_mult in multipliers:
                N = P * n_mult
                for group_num in group_nums:
                    params.append((P, M, N, group_num))
        P += P_step

    # Write to file
    with open(output_file, 'w') as f:
        f.write(f"# Auto-generated parameter sets (WSE mode)\n")
        f.write(f"# P range: {P_start} to {P_end} (step: {P_step})\n")
        f.write(f"# M, N: For each P, iterate through P, 2P, 3P, 8P\n")
        if single_group_num:
            f.write(f"# group_num: 8 (single value)\n")
        else:
            f.write(f"# group_num: 2, 4, 8\n")
        f.write(f"# Format: P M N group_num\n")
        f.write(f"# MeshGEMV computes [1,N] = [1,M] @ [M,N] on P×P PE grid with group_num groups\n")
        f.write(f"#\n")

        for p, m, n, g in params:
            f.write(f"{p} {m} {n} {g}\n")

    print(f"Generated {len(params)} parameter sets for WSE mode")
    print(f"Output: {output_file}")
    print(f"P values: {P_start} to {P_end} (step {P_step})")
    print(f"M, N multipliers: P, 2P, 3P, 8P")
    if single_group_num:
        print(f"group_num value: 8 (single value)")
    else:
        print(f"group_num values: 2, 4, 8")
    print(f"Each P generates {len(multipliers) * len(multipliers) * len(group_nums)} combinations")
    return len(params)


def print_usage():
    """Print usage information."""
    print("Usage:")
    print("  Simulator mode:")
    print("    python generate_params.py --simulator [output_file] [P_start] [P_end] [P_step] \\")
    print("                              [M_start] [M_end] [M_step] [N_start] [N_end] [N_step] \\")
    print("                              [group_num_start] [group_num_end] [group_num_step]")
    print()
    print("  WSE mode:")
    print("    python generate_params.py --wse [--single-group-num] [output_file] [P_start] [P_end] [P_step]")
    print()
    print("Flags:")
    print("  --single-group-num: Use only group_num=8 instead of iterating through 2,4,8 (WSE mode only)")
    print()
    print("Defaults:")
    print("  Simulator: P=16-128 step 16, M=1024, N=1024, group_num=8")
    print("  WSE: P=16-730 step 64, M/N=P,2P,3P,8P, group_num=2,4,8")
    print("  WSE with --single-group-num: P=16-730 step 64, M/N=P,2P,3P,8P, group_num=8")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ['--simulator', '--wse']:
        print("Error: Must specify mode (--simulator or --wse)")
        print()
        print_usage()
        sys.exit(1)

    mode = sys.argv[1]

    if mode == '--simulator':
        # Parse simulator mode arguments
        args = sys.argv[2:]

        # Default values
        output_file = 'simulator_in_out/input/input_temp.txt'
        P_start, P_end, P_step = 16, 128, 16
        M_start, M_end, M_step = 1024, 1024, 1024
        N_start, N_end, N_step = 1024, 1024, 1024
        group_num_start, group_num_end, group_num_step = 8, 8, 8

        # Parse provided arguments
        if len(args) >= 1:
            output_file = args[0]
        if len(args) >= 4:
            P_start, P_end, P_step = int(args[1]), int(args[2]), int(args[3])
        if len(args) >= 7:
            M_start, M_end, M_step = int(args[4]), int(args[5]), int(args[6])
        if len(args) >= 10:
            N_start, N_end, N_step = int(args[7]), int(args[8]), int(args[9])
        if len(args) >= 13:
            group_num_start, group_num_end, group_num_step = int(args[10]), int(args[11]), int(args[12])

        generate_simulator_params(
            output_file,
            P_start, P_end, P_step,
            M_start, M_end, M_step,
            N_start, N_end, N_step,
            group_num_start, group_num_end, group_num_step
        )

    elif mode == '--wse':
        # Parse WSE mode arguments
        args = sys.argv[2:]

        # Default values
        output_file = 'wse_in_out/input/input_temp.txt'
        P_start, P_end, P_step = 16, 730, 64
        single_group_num = False

        # Check for --single-group-num flag
        if '--single-group-num' in args:
            single_group_num = True
            args.remove('--single-group-num')

        # Parse provided arguments
        if len(args) >= 1:
            output_file = args[0]
        if len(args) >= 4:
            P_start, P_end, P_step = int(args[1]), int(args[2]), int(args[3])

        generate_wse_params(output_file, P_start, P_end, P_step, single_group_num)
