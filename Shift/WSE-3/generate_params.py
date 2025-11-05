#!/usr/bin/env python3
"""
Generate parameter sets for parallel simulations.

This script generates a grid of parameters P, L, M, N based on specified ranges and rules:
- P: Start value, end value, step size
- L: Starts at 1, doubles each time until it reaches 3*P
- M and N: Always equal, start at P, double each time until reaching 8*P

Usage:
    python generate_params.py [output_file] [P_start] [P_end] [P_step] [--max-product MAX]

    Default output_file: input_temp.txt
    Default P_start: 16
    Default P_end: 128
    Default P_step: 16
    Default MAX: None (disabled)

    --max-product MAX: Enable maximum product constraint (P*P*L*M*N <= MAX)
                       Default value when enabled: 33554432
"""

import sys
from pathlib import Path


def generate_parameters(P_start, P_end, P_step, max_product=None):
    """
    Generate parameter combinations based on the rules.

    Args:
        P_start: Starting value for P
        P_end: Ending value for P (inclusive)
        P_step: Step size for P
        max_product: Maximum value for P*P*L*M*N (None to disable)

    Returns:
        List of tuples (P, L, M, N)
    """
    params = []
    filtered_count = 0

    # Iterate through P values
    P = P_start
    while P <= P_end:
        # L starts at 1 and doubles until it reaches 3*P
        L = 1
        while L <= 3 * P:
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

        P += P_step  # Increment P by step

    if max_product is not None and filtered_count > 0:
        print(f"Note: Filtered out {filtered_count} parameter sets exceeding max product {max_product}")
        print()

    return params


def main():
    # Default values
    default_output_file = "input_temp.txt"
    default_P_start = 16
    default_P_end = 128
    default_P_step = 16
    default_max_product = 33554432

    # Parse arguments
    args = sys.argv[1:]
    max_product = None

    # Check for --max-product flag
    if "--max-product" in args:
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

    # Show help if too many positional arguments
    if len(args) > 4:
        print("Usage: python generate_params.py [output_file] [P_start] [P_end] [P_step] [--max-product MAX]")
        print("\nDefaults:")
        print(f"  output_file: {default_output_file}")
        print(f"  P_start: {default_P_start}")
        print(f"  P_end: {default_P_end}")
        print(f"  P_step: {default_P_step}")
        print(f"  max_product: None (disabled)")
        print("\nOptions:")
        print(f"  --max-product MAX: Limit P*P*L*M*N to MAX (default when enabled: {default_max_product})")
        print("\nParameter generation rules:")
        print("  - P: Ranges from P_start to P_end with P_step increment")
        print("  - L: Starts at 1, doubles until reaching 3*P")
        print("  - M and N: Always equal, start at P, double until reaching 8*P")
        sys.exit(1)

    # Parse positional arguments with defaults
    output_file = args[0] if len(args) > 0 else default_output_file
    P_start = int(args[1]) if len(args) > 1 else default_P_start
    P_end = int(args[2]) if len(args) > 2 else default_P_end
    P_step = int(args[3]) if len(args) > 3 else default_P_step

    # Validate inputs
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
    print("Parameter Generation Configuration:")
    print("=" * 60)
    print(f"Output file: {output_file}")
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
    params = generate_parameters(P_start, P_end, P_step, max_product)

    # Print preview
    print(f"Generated {len(params)} parameter sets:")
    print("-" * 60)
    print("P    L    M    N    P*P*L*M*N")
    print("-" * 60)
    for p, l, m, n in params:
        product = p * p * l * m * n
        print(f"{p:<4} {l:<4} {m:<4} {n:<4} {product}")
    print("-" * 60)
    print()

    # Write to file
    with open(output_file, 'w') as f:
        f.write("# Auto-generated parameter sets\n")
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
    print(f"\nYou can now run simulations with:")
    print(f"  python parallel_sim.py {output_file}")


if __name__ == "__main__":
    main()
