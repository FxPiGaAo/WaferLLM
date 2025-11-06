#!/usr/bin/env python3
"""
Generate parameter sets for parallel simulations or WSE executions.

This script generates a grid of parameters P, L, M, N based on specified ranges and rules:

Simulator mode:
- P: Start value, end value, step size (user-defined)
- L: Starts at 1, doubles each time until it reaches 3*P
- M and N: Always equal, start at P, double each time until reaching 8*P
- Max product constraint (P*P*L*M*N <= 33554432) is ENABLED by default

WSE mode:
- P: Starts at 16, ends at 650
  - First 5 steps increment by 16: 16, 32, 48, 64, 80
  - Next 5 steps increment by 32: 112, 144, 176, 208, 240
  - Remaining steps increment by 64: 304, 368, 432, 496, 560, 624, ...
- L: Starts at 1, doubles each time until it reaches 3*P
  - Constraint: L + P < 740 (hardware fabric limit)
- M and N: Always equal, start at P, double each time until reaching 8*P

Usage:
    python generate_params.py --simulator [output_file] [P_start] [P_end] [P_step] [--max-product MAX]
    python generate_params.py --wse [output_file]

    --simulator: Generate parameters for simulator (supports --max-product)
    --wse: Generate parameters for WSE (uses only L+P < 740 constraint, ignores P_start/P_end/P_step)

    Default output_file: simulator_in_out/input/input_temp.txt (simulator) or wse_in_out/input/input_temp.txt (wse)
    Default P_start: 16 (simulator only)
    Default P_end: 128 (simulator only)
    Default P_step: 16 (simulator only)
    Default max_product: 33554432 (simulator only)

    --max-product MAX: (Simulator mode only) Maximum product constraint (P*P*L*M*N <= MAX)
                       Default value: 33554432
"""

import sys
from pathlib import Path


def generate_wse_p_values():
    """
    Generate P values for WSE mode.

    First 5 steps: increment by 16 (16, 32, 48, 64, 80)
    Next 5 steps: increment by 32 (112, 144, 176, 208, 240)
    Remaining steps: increment by 64 until 650

    Returns:
        List of P values
    """
    p_values = []

    # First 5 steps: increment by 16
    for i in range(5):
        p_values.append(16 * (i + 1))

    # Next 5 steps: increment by 32 starting from 112
    for i in range(5):
        p_values.append(112 + 32 * i)

    # Remaining steps: increment by 64 starting from 304
    p = 304
    while p <= 650:
        p_values.append(p)
        p += 64

    return p_values


def generate_parameters(P_start, P_end, P_step, max_product=None, wse_mode=False):
    """
    Generate parameter combinations based on the rules.

    Args:
        P_start: Starting value for P (ignored in WSE mode)
        P_end: Ending value for P (inclusive) (ignored in WSE mode)
        P_step: Step size for P (ignored in WSE mode)
        max_product: Maximum value for P*P*L*M*N (None to disable)
        wse_mode: If True, use WSE-specific P generation and constraints

    Returns:
        List of tuples (P, L, M, N)
    """
    params = []
    filtered_count = 0
    lp_filtered_count = 0

    # Generate P values based on mode
    if wse_mode:
        p_values = generate_wse_p_values()
    else:
        # Simulator mode: use traditional range
        p_values = []
        P = P_start
        while P <= P_end:
            p_values.append(P)
            P += P_step

    # Iterate through P values
    for P in p_values:
        # L starts at 1 and doubles until it reaches 3*P
        L = 1
        while L <= 3 * P:
            # WSE mode constraint: L + P < 740
            if wse_mode and L + P >= 740:
                lp_filtered_count += 1
                L *= 2
                continue

            # M and N are equal, start at P and double until reaching 8*P
            M = P
            while M <= 8 * P:
                N = M  # M always equals N

                # Check max product constraint if enabled
                if max_product is not None:
                    product = P * P * L * M * N
                    if product <= max_product:
                        params.append((P, L, M, N))
                    else:
                        filtered_count += 1
                else:
                    params.append((P, L, M, N))

                M *= 2  # Double M (and N)

            L *= 2  # Double L

    if wse_mode and lp_filtered_count > 0:
        print(f"Note: Filtered out {lp_filtered_count} parameter sets due to L+P >= 740 constraint")

    if max_product is not None and filtered_count > 0:
        print(f"Note: Filtered out {filtered_count} parameter sets exceeding max product {max_product}")

    if (wse_mode and lp_filtered_count > 0) or (max_product is not None and filtered_count > 0):
        print()

    return params


def main():
    # Default values for simulator mode
    default_simulator_output_file = "simulator_in_out/input/input_temp.txt"
    default_wse_output_file = "wse_in_out/input/input_temp.txt"
    default_P_start = 16
    default_P_end = 128
    default_P_step = 16
    default_max_product = 33554432

    # Parse arguments
    args = sys.argv[1:]
    max_product = None
    wse_mode = None  # Changed to None to detect if mode was specified
    max_product_explicitly_set = False  # Track if user explicitly set max_product

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
        print("  python generate_params.py --simulator [output_file] [P_start] [P_end] [P_step] [--max-product MAX]")
        print("  python generate_params.py --wse [output_file]")
        print("\nExamples:")
        print("  python generate_params.py --simulator")
        print("  python generate_params.py --wse")
        print("  python generate_params.py --simulator simulator_in_out/input/params.txt 16 64 16")
        print("  python generate_params.py --wse wse_in_out/input/params.txt")
        sys.exit(1)

    # Check for --max-product flag
    if "--max-product" in args:
        # max_product is only supported in simulator mode
        if wse_mode:
            print("Error: --max-product flag is not supported in WSE mode")
            print("WSE mode only uses the L+P < 740 constraint")
            sys.exit(1)

        max_product_explicitly_set = True
        idx = args.index("--max-product")
        if idx + 1 < len(args):
            try:
                max_product = int(args[idx + 1])
                # Remove the flag and its value from args
                args.pop(idx + 1)
                args.pop(idx)
            except ValueError:
                print("Error: --max-product value must be a positive integer")
                sys.exit(1)
        else:
            # Flag present but no value, use default
            max_product = default_max_product
            args.pop(idx)

    # Set max_product default based on mode if not explicitly set
    if not max_product_explicitly_set:
        if wse_mode:
            # WSE mode: no max_product constraint
            max_product = None
        else:
            # Simulator mode: enable max_product by default
            max_product = default_max_product

    # Set defaults based on mode
    default_output_file = default_wse_output_file if wse_mode else default_simulator_output_file

    # Show help if too many positional arguments
    if len(args) > 4:
        print("Usage:")
        print("  python generate_params.py --simulator [output_file] [P_start] [P_end] [P_step] [--max-product MAX]")
        print("  python generate_params.py --wse [output_file]")
        print("\nMode flags:")
        print("  --simulator: Generate parameters for simulator")
        print("  --wse: Generate parameters for WSE")
        print("\nDefaults (simulator mode):")
        print(f"  output_file: {default_simulator_output_file}")
        print(f"  P_start: {default_P_start}")
        print(f"  P_end: {default_P_end}")
        print(f"  P_step: {default_P_step}")
        print(f"  max_product: {default_max_product} (enabled by default)")
        print("\nDefaults (WSE mode):")
        print(f"  output_file: {default_wse_output_file}")
        print("  P values: 16, 32, 48, 64, 80, 112, 144, 176, 208, 240, 304, 368, ... 650")
        print("  (First 5: +16, Next 5: +32, Remaining: +64)")
        print("\nOptions (simulator mode only):")
        print(f"  --max-product MAX: Override max product constraint (default: {default_max_product})")
        print("\nParameter generation rules:")
        print("  Simulator mode:")
        print("    - P: Ranges from P_start to P_end with P_step increment")
        print("    - L: Starts at 1, doubles until reaching 3*P")
        print("    - M and N: Always equal, start at P, double until reaching 8*P")
        print("    - Max product (P*P*L*M*N) constraint enabled by default")
        print("  WSE mode:")
        print("    - P: 16, 32, 48, 64, 80, 112, 144, 176, 208, 240, 304, 368, ... 650")
        print("    - L: Starts at 1, doubles until reaching 3*P (constraint: L+P < 740)")
        print("    - M and N: Always equal, start at P, double until reaching 8*P")
        sys.exit(1)

    # Parse positional arguments with defaults
    output_file = args[0] if len(args) > 0 else default_output_file
    P_start = int(args[1]) if len(args) > 1 else default_P_start
    P_end = int(args[2]) if len(args) > 2 else default_P_end
    P_step = int(args[3]) if len(args) > 3 else default_P_step

    # Validate inputs (only for simulator mode)
    if not wse_mode:
        if P_start <= 0 or P_end <= 0 or P_step <= 0:
            print("Error: All parameters must be positive integers")
            sys.exit(1)

        if P_start > P_end:
            print("Error: P_start must be less than or equal to P_end")
            sys.exit(1)

    if max_product is not None and max_product <= 0:
        print("Error: max_product must be a positive integer")
        sys.exit(1)

    # Print configuration
    mode_str = "WSE" if wse_mode else "Simulator"
    print(f"Parameter Generation Configuration ({mode_str} mode):")
    print("=" * 60)
    print(f"Output file: {output_file}")
    if wse_mode:
        print(f"P values: WSE-specific sequence (16-650)")
        print(f"  First 5: 16, 32, 48, 64, 80 (increment by 16)")
        print(f"  Next 5: 112, 144, 176, 208, 240 (increment by 32)")
        print(f"  Remaining: 304, 368, ... 650 (increment by 64)")
        print(f"L rule: Start at 1, double until 3*P (constraint: L+P < 740)")
    else:
        print(f"P range: {P_start} to {P_end} (step: {P_step})")
        print(f"L rule: Start at 1, double until 3*P")
    print(f"M=N rule: Start at P, double until 8*P")
    if max_product is not None:
        print(f"Max product (P*P*L*M*N): {max_product}")
    else:
        print(f"Max product constraint: Disabled")
    print("=" * 60)
    print()

    # Generate parameters
    params = generate_parameters(P_start, P_end, P_step, max_product, wse_mode)

    # Print preview
    print(f"Generated {len(params)} parameter sets:")
    print("-" * 60)
    if wse_mode:
        # WSE mode: only show P L M N (no calculated columns)
        print("P    L    M    N")
        print("-" * 60)
        for p, l, m, n in params:
            print(f"{p:<4} {l:<4} {m:<4} {n}")
    else:
        # Simulator mode: show P*P*L*M*N column
        print("P    L    M    N    P*P*L*M*N")
        print("-" * 60)
        for p, l, m, n in params:
            product = p * p * l * m * n
            print(f"{p:<4} {l:<4} {m:<4} {n:<4} {product}")
    print("-" * 60)
    print()

    # Write to file
    with open(output_file, 'w') as f:
        f.write(f"# Auto-generated parameter sets ({mode_str} mode)\n")
        if wse_mode:
            f.write("# P: WSE-specific sequence (16-650)\n")
            f.write("# L: Start at 1, double until 3*P (constraint: L+P < 740)\n")
        else:
            f.write(f"# P range: {P_start} to {P_end} (step: {P_step})\n")
            f.write("# L: Start at 1, double until 3*P\n")
        f.write("# M=N: Start at P, double until 8*P\n")
        if max_product is not None:
            f.write(f"# Max product (P*P*L*M*N): {max_product}\n")
        f.write("# Format: P L M N\n")
        f.write("#\n")
        for p, l, m, n in params:
            f.write(f"{p} {l} {m} {n}\n")

    print(f"✓ Successfully wrote {len(params)} parameter sets to '{output_file}'")
    if wse_mode:
        print(f"\nYou can now run WSE executions with:")
        print(f"  python parallel_wse.py {output_file}")
    else:
        print(f"\nYou can now run simulations with:")
        print(f"  python parallel_sim.py {output_file}")


if __name__ == "__main__":
    main()
