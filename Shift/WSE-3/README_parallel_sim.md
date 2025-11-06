# Parallel Simulation Runner

A Python script to run multiple simulations in parallel using `run_sim.sh`.

## Overview

`parallel_sim.py` allows you to execute multiple simulation runs with different parameter sets in parallel, utilizing multiple CPU cores to speed up the process. Each simulation's output is saved to a separate file.

The system now fully supports parallel execution with no conflicts. Each simulation run uses parameter-specific output directories (e.g., `out_P4_L2_M32_N64/`) to store compiled artifacts, preventing any folder conflicts between concurrent simulations.

**Smart Skip Feature**: The script automatically skips simulations that have already been run by checking for existing output files. This allows you to safely re-run the script to resume interrupted batch jobs or add new parameter sets without wasting time on already-completed simulations.

## Quick Start

The repository includes a pre-configured `simulator_in_out/input/input.txt` file with sample parameters. To run simulations immediately:

```bash
# Run simulations with defaults
python parallel_sim.py

# Collect results into JSON
python collect_results.py
```

This will read parameters from `simulator_in_out/input/input.txt`, run simulations in parallel (using 4 processes), save outputs to `simulator_in_out/outputs/`, and collect results into `results.json`.

## Usage

```bash
python parallel_sim.py [options]
```

### Arguments

You can use either positional arguments or flags (or mix them):

**Positional arguments** (all optional):
- `input_file`: Path to a text file containing parameter sets (one per line) (default: `simulator_in_out/input/input.txt`)
- `output_folder`: Directory where output files will be saved (created if it doesn't exist) (default: `simulator_in_out/outputs`)
- `num_processes`: Number of parallel processes to use (e.g., 4, 8, 16) (default: `4`)

**Flags** (alternative to positional arguments):
- `-i, --input FILE`: Input file path
- `-o, --output DIR`: Output directory
- `-n, --num-processes NUM`: Number of parallel processes

Flags take precedence over positional arguments if both are specified.

## Generating Parameter Sets

The `generate_params.py` script automates the generation of parameter sets following specific rules, making it easy to create comprehensive parameter grids for simulations and WSE executions.

### Overview

This script supports two modes:

**Simulator mode** (use `--simulator` flag):
- **P**: User-defined range with custom step size
- **L**: Starts at 1, doubles until reaching 3×P
- **M and N**: Always equal, start at P, double until reaching 8×P

**WSE mode** (use `--wse` flag):
- **P**: Specific sequence from 16 to 650
  - First 5 steps: 16, 32, 48, 64, 80 (increment by 16)
  - Next 5 steps: 112, 144, 176, 208, 240 (increment by 32)
  - Remaining steps: 304, 368, 432, ... 624 (increment by 64)
- **L**: Starts at 1, doubles until reaching 3×P (with constraint L+P < 740)
- **M and N**: Always equal, start at P, double until reaching 8×P
- **Note**: WSE mode does not support `--max-product` flag

### Usage

```bash
# Simulator mode (supports --max-product)
python generate_params.py --simulator [output_file] [P_start] [P_end] [P_step] [--max-product MAX]

# WSE mode (uses only L+P < 740 constraint)
python generate_params.py --wse [output_file]
```

**Note**: You must specify either `--simulator` or `--wse` mode. The script will show an error if no mode is specified.

### Arguments for Simulator Mode

- `--simulator`: Required flag to enable simulator mode
- `output_file`: Path where parameter file will be saved (default: `simulator_in_out/input/input_temp.txt`)
- `P_start`: Starting value for P (default: `16`)
- `P_end`: Ending value for P, inclusive (default: `128`)
- `P_step`: Step increment for P (default: `16`)
- `--max-product MAX`: Optional constraint limiting P×P×L×M×N (default when enabled: `33554432`)

### Examples

```bash
# Use all defaults: P from 16 to 128 (step 16), no product limit
python generate_params.py --simulator

# Generate with custom P range
python generate_params.py --simulator params.txt 32 256 32

# Enable max product constraint with default value (33554432)
python generate_params.py --simulator params.txt 16 128 16 --max-product

# Use custom max product constraint
python generate_params.py --simulator params.txt 16 128 16 --max-product 500000

# Only specify max product, use other defaults
python generate_params.py --simulator --max-product
```

### The `--max-product` Option

When enabled, this option filters out parameter sets where P×P×L×M×N exceeds the specified maximum. This is useful for:
- Limiting memory requirements
- Constraining computational complexity
- Focusing on parameter sets within hardware constraints

**Default value**: 33554432 (2²⁵) when the flag is used without a value

**Example**: With `--max-product 500000` and P range 16-32:
- Generates 52 parameter sets without constraint
- Filters to 21 parameter sets with constraint
- Automatically reports how many sets were filtered out

### Parameter Generation Rules

For each value of P in the range [P_start, P_end] with increment P_step:
1. L starts at 1 and doubles: 1, 2, 4, 8, ... until L ≤ 3×P
2. For each L, M starts at P and doubles: P, 2P, 4P, 8P, ... until M ≤ 8×P
3. N always equals M
4. If `--max-product` is enabled, only include sets where P×P×L×M×N ≤ MAX

### Output Format

The generated file contains:
- Header comments documenting the generation rules
- One parameter set per line in format: `P L M N`
- Parameter sets are ready to use with `parallel_sim.py`

**Example output file**:
```
# Auto-generated parameter sets
# P range: 16 to 32 (step: 16)
# L: Start at 1, double until 3*P
# M=N: Start at P, double until 8*P
# Max product (P*P*L*M*N): 33554432
# Format: P L M N
#
16 1 16 16
16 1 32 32
16 1 64 64
16 2 16 16
16 2 32 32
...
```

### Complete Workflow with Parameter Generation

```bash
# Step 1: Generate parameter sets with constraints
python generate_params.py --simulator simulator_in_out/input/my_params.txt 16 128 16 --max-product

# Step 2: Run parallel simulations with generated parameters
python parallel_sim.py simulator_in_out/input/my_params.txt simulator_in_out/outputs 8

# Step 3: Collect results
python collect_results.py
```

## Input File Format

Each line in the input file should contain four space-separated parameters:

```
P L M N
```

- **P**: First parameter
- **L**: Second parameter
- **M**: Third parameter
- **N**: Fourth parameter

Lines starting with `#` are treated as comments and ignored.

### Example Input File (`params.txt`)

```
# Simulation parameter sets
# Format: P L M N
4 2 32 64
8 4 64 128
16 8 128 256
32 16 256 512
```

## Output

Each simulation produces an output file in the specified output folder with the naming pattern:

```
output_P<p>_L<l>_M<m>_N<n>.txt
```

For example, a simulation with parameters `P=4 L=2 M=32 N=64` will create:

```
output_P4_L2_M32_N64.txt
```

Each output file contains:
- The command that was executed
- The exit code
- The runtime in seconds
- The complete stdout/stderr output from the simulation

## Examples

### Example 1: Run with all defaults (recommended for quick start)

```bash
# Uses simulator_in_out/input/input.txt as input, outputs to simulator_in_out/outputs folder, 4 parallel processes
python parallel_sim.py
```

### Example 2: Only specify number of processes

```bash
# Use default input and output, but run with 8 processes
python parallel_sim.py -n 8

# Or use the long form
python parallel_sim.py --num-processes 16
```

### Example 3: Custom input file, default output and processes

```bash
# Using positional argument
python parallel_sim.py params.txt

# Using flag
python parallel_sim.py -i params.txt
```

### Example 4: Custom input and output, default processes

```bash
# Using positional arguments
python parallel_sim.py params.txt custom_outputs

# Using flags
python parallel_sim.py -i params.txt -o custom_outputs
```

### Example 5: Specify all parameters

```bash
# Using positional arguments
python parallel_sim.py my_parameters.txt simulation_results 8

# Using flags
python parallel_sim.py -i my_parameters.txt -o simulation_results -n 8

# Mix positional and flags
python parallel_sim.py my_parameters.txt -o simulation_results -n 8
```

### Example 6: Create and run a simple test

```bash
# Create input file
cat > test_params.txt << EOF
4 2 32 64
8 4 64 128
EOF

# Run simulations with 2 parallel processes
python parallel_sim.py test_params.txt test_outputs 2

# Or using flags
python parallel_sim.py -i test_params.txt -o test_outputs -n 2
```

## Output Example

When running, you'll see progress messages:

```
Found 4 simulation(s) to run
Using 4 parallel processes
Output folder: simulator_in_out/outputs
--------------------------------------------------------------------------------
Running: ./run_sim.sh 4 2 32 64 -> simulator_in_out/outputs/output_P4_L2_M32_N64.txt
⊘ Skipped: P=8 L=4 M=64 N=128 (already ran - output file exists)
✓ Completed: P=4 L=2 M=32 N=64 (Runtime: 45.23s)
Running: ./run_sim.sh 16 8 128 256 -> simulator_in_out/outputs/output_P16_L8_M128_N256.txt
✓ Completed: P=16 L=8 M=128 N=256 (Runtime: 67.89s)
--------------------------------------------------------------------------------
Summary:
Total: 4 simulations
Successful: 4
Failed: 0
Total runtime: 113.12 seconds (1.89 minutes)

Runtimes:
  P=4 L=2 M=32 N=64: 45.23s
  P=16 L=8 M=128 N=256: 67.89s
```

**Note**: Simulations that have already been run (output file exists) will be automatically skipped with a "⊘ Skipped" message. Runtime measurements are displayed for each completed simulation and in the summary.

## Tips

- **Choosing num_processes**: Set this to the number of CPU cores available on your system for optimal performance. You can check available cores with `nproc` command.

- **Resuming interrupted runs**: If a batch simulation is interrupted, simply re-run the same command. The script will automatically skip already-completed simulations and only run the remaining ones.

- **Adding new parameter sets**: You can add new parameter sets to your input file and re-run the script. Only the new simulations will be executed; existing results will be preserved.

- **Re-running specific simulations**: To force a re-run of specific simulations, delete their corresponding output files before running the script.

- **Monitoring**: While simulations run, you can check the output folder to see intermediate results:
  ```bash
  ls -lh simulator_in_out/outputs/
  tail -f simulator_in_out/outputs/output_P4_L2_M32_N64.txt
  ```

- **Error handling**: If any simulation fails, the script will continue running others and report failures in the summary.

- **Cleaning up compilation artifacts**: After collecting results, you can free up disk space by removing the compilation directory:
  ```bash
  rm -rf out_params/
  ```

## How Parallel Execution Works

The parallel simulation system has been designed to avoid conflicts between concurrent runs:

1. **Parameter-Specific Compilation Directories**: When `run_sim.sh` is invoked with parameters `P L M N`, it creates a unique output directory named `out_params/out_P<p>_L<l>_M<m>_N<n>/` where the compiled CSL artifacts are stored.

2. **Independent Execution**: Each simulation run operates in its own compilation directory, using `launch_sim.py` with the `--out-dir` argument to load artifacts from the correct location.

3. **No Conflicts**: Multiple simulations can now compile and run simultaneously without interfering with each other's artifacts or intermediate files.

Example directory structure after running parallel simulations:
```
WSE-3/
├── out_params/                    # Parent folder for all compilation artifacts
│   ├── out_P4_L2_M32_N64/        # Compilation artifacts for first parameter set
│   └── out_P8_L4_M64_N128/       # Compilation artifacts for second parameter set
├── simulator_in_out/
│   └── outputs/                   # Simulation results
│       ├── output_P4_L2_M32_N64.txt  # Results for first parameter set
│       └── output_P8_L4_M64_N128.txt # Results for second parameter set
...
```

**Note**: You may want to periodically clean up the `out_params/` directory to free up disk space, especially after collecting results.

## Requirements

- Python 3.6 or higher
- `run_sim.sh` must be in the same directory as `parallel_sim.py`
- Sufficient disk space for output files and compilation artifacts

## Troubleshooting

**Error: Input file not found**
- Check that the path to your input file is correct

**Error: run_sim.sh not found**
- Ensure `run_sim.sh` exists in the same directory as `parallel_sim.py`

**Simulations failing**
- Check individual output files in the output folder for error messages
- Verify that your parameters are valid for `run_sim.sh`

---

## Collecting Results

After running simulations, use `collect_results.py` to automatically extract and aggregate results from all output files into a JSON format.

### Usage

```bash
python collect_results.py [output_folder] [json_output_file]
```

### Arguments

Both arguments are optional with defaults:

- `output_folder`: Directory containing the simulation output files (default: `simulator_in_out/outputs`)
- `json_output_file`: Path to the output JSON file where results will be saved (default: `results.json`)

### What It Collects

For each simulation output file, the script extracts:
- **P**: First parameter
- **L**: Second parameter
- **M**: Third parameter
- **N**: Fourth parameter
- **mean_cycle_count**: The average cycle count from the simulation

### Examples

```bash
# Use defaults: collect from "simulator_in_out/outputs" folder to "results.json"
python collect_results.py

# Use custom output folder, default JSON file
python collect_results.py test_outputs

# Use custom output folder and JSON file
python collect_results.py test_outputs my_results.json
```

### Output Format

The JSON file contains:

```json
{
  "total_experiments": 2,
  "results": [
    {
      "P": 10,
      "L": 10,
      "M": 10,
      "N": 10,
      "mean_cycle_count": 887.4
    },
    {
      "P": 12,
      "L": 12,
      "M": 12,
      "N": 12,
      "mean_cycle_count": 886.2833333333334
    }
  ]
}
```

### Complete Workflow Example

#### Quick Start (using all defaults)

```bash
# The simulator_in_out/input/input.txt file already contains sample parameters
# Just run with defaults:
python parallel_sim.py

# Collect results
python collect_results.py
```

#### Custom Workflow

```bash
# Step 1: Create parameter file
cat > params.txt << EOF
10 10 10 10
12 12 12 12
EOF

# Step 2: Run parallel simulations (outputs to "simulator_in_out/outputs" folder)
python parallel_sim.py params.txt simulator_in_out/outputs 2

# Step 3: Collect results into JSON (uses defaults)
python collect_results.py
```

### Features

- Automatically finds all output files matching the pattern `output_P*_L*_M*_N*.txt`
- Extracts parameters from filenames
- Parses mean cycle count from output files
- Handles errors gracefully with informative messages
- Outputs well-formatted JSON for easy data analysis
