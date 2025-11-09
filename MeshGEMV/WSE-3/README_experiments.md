# MeshGEMV Parallel Experiment Runner

This directory contains scripts to run multiple MeshGEMV experiments in parallel, either on the simulator or WSE-3 hardware.

## Overview

MeshGEMV computes general matrix-vector multiplication: `[1,N] = [1,M] @ [M,N]` on a `P×P` PE grid with `group_num` groups.

The experiment scripts allow you to:
- Generate parameter sets for experiments
- Run multiple experiments in parallel on the simulator
- Run multiple experiments in parallel on WSE-3 hardware
- Collect and aggregate results into JSON format

## Quick Start

### Simulator Mode

```bash
# Step 1: Generate parameter sets (using defaults: P=16-128 step 16, M=N=1024, group_num=8)
python generate_params.py --simulator

# Step 2: Run parallel simulations (using 4 processes)
python parallel_sim.py

# Step 3: Collect results into JSON
python collect_results.py --mode simulator
```

### WSE Mode

```bash
# Step 1: Generate parameter sets
python generate_params.py --wse

# Step 2: Run parallel WSE executions (using 1 process for testing)
python parallel_wse.py

# Step 3: Collect results into JSON
python collect_results.py --mode wse
```

---

## Parameter Generation

The `generate_params.py` script creates input files with parameter combinations for experiments.

### Usage

```bash
# Simulator mode: Full control over all parameter ranges
python generate_params.py --simulator [output_file] [P_start] [P_end] [P_step] [M_start] [M_end] [M_step] [N_start] [N_end] [N_step] [group_num_start] [group_num_end] [group_num_step]

# WSE mode: M, N automatically generated as multiples of P
python generate_params.py --wse [output_file] [P_start] [P_end] [P_step]
```

### Arguments

**Simulator Mode:**
All arguments are optional with sensible defaults:

- `--simulator`: Required mode flag
- `output_file`: Path where parameter file will be saved (default: `simulator_in_out/input/input_temp.txt`)
- `P_start`, `P_end`, `P_step`: Range for P (PE grid dimension) - Default: 16, 128, 16
- `M_start`, `M_end`, `M_step`: Range for M (input vector length) - Default: 1024, 1024, 1024
- `N_start`, `N_end`, `N_step`: Range for N (output vector length) - Default: 1024, 1024, 1024
- `group_num_start`, `group_num_end`, `group_num_step`: Range for group_num - Default: 8, 8, 8

**WSE Mode:**
Automatically generates M, N as multiples of P:

- `--wse`: Required mode flag
- `output_file`: Path where parameter file will be saved (default: `wse_in_out/input/input_temp.txt`)
- `P_start`, `P_end`, `P_step`: Range for P (PE grid dimension) - Default: 16, 730, 64
- **M, N**: For each P value, automatically iterate through **2P, 3P, 8P**
- **group_num**: Automatically iterate through **1, 2, 4, 8**
  - This generates 3×3×4 = 36 parameter combinations per P value

### Examples

**Simulator Mode Examples:**

```bash
# Generate with all defaults (P: 16-128 step 16, M=N=1024, group_num=8)
python generate_params.py --simulator

# Custom P range, default M,N,group_num
python generate_params.py --simulator params.txt 32 256 32

# Custom P and M ranges
python generate_params.py --simulator params.txt 16 64 16 512 2048 512

# Full custom specification
python generate_params.py --simulator params.txt 16 64 16 512 2048 512 1024 4096 1024 4 32 4
```

**WSE Mode Examples:**

```bash
# Generate with defaults (P: 16-730 step 64, M/N = 2P,3P,8P, group_num=1,2,4,8)
# This generates 12 P values × 36 combinations = 432 parameter sets
python generate_params.py --wse

# Custom P range (P: 16-256 step 64)
# This generates 4 P values × 36 combinations = 144 parameter sets
python generate_params.py --wse wse_params.txt 16 256 64

# Smaller range for testing (P: 64-128 step 64)
# This generates 2 P values × 36 combinations = 72 parameter sets
python generate_params.py --wse test_params.txt 64 128 64
```

### Output Format

**Simulator Mode Output:**
```
# Auto-generated parameter sets (Simulator mode)
# P range: 16 to 128 (step: 16)
# M range: 1024 to 1024 (step: 1024)
# N range: 1024 to 1024 (step: 1024)
# group_num range: 8 to 8 (step: 8)
# Format: P M N group_num
# MeshGEMV computes [1,N] = [1,M] @ [M,N] on P×P PE grid with group_num groups
#
16 1024 1024 8
32 1024 1024 8
48 1024 1024 8
...
```

**WSE Mode Output:**
```
# Auto-generated parameter sets (WSE mode)
# P range: 16 to 730 (step: 64)
# M, N: For each P, iterate through 2P, 3P, 8P
# group_num: 1, 2, 4, 8
# Format: P M N group_num
# MeshGEMV computes [1,N] = [1,M] @ [M,N] on P×P PE grid with group_num groups
#
16 32 32 1
16 32 32 2
16 32 32 4
16 32 32 8
16 32 48 1
16 32 48 2
...
720 5760 5760 8
```

---

## Parallel Simulator Execution

The `parallel_sim.py` script runs multiple simulations in parallel using the Cerebras simulator.

### Usage

```bash
python parallel_sim.py [options]
```

### Arguments

Positional arguments (all optional):
- `input_file`: Path to input file (default: `simulator_in_out/input/input.txt`)
- `output_folder`: Output directory (default: `simulator_in_out/outputs`)
- `num_processes`: Number of parallel processes (default: 4)

Flags (alternative to positional arguments):
- `-i, --input FILE`: Input file path
- `-o, --output DIR`: Output directory
- `-n, --num-processes NUM`: Number of parallel processes
- `--runonedp`: Run only the first input parameter (always run, never skip)

### Smart Skip Feature

The script automatically skips simulations that have already been run by checking for existing output files. This allows you to:
- Resume interrupted batch jobs
- Add new parameter sets without re-running completed ones
- Force re-run by deleting output files

### Examples

```bash
# Use all defaults
python parallel_sim.py

# Custom process count
python parallel_sim.py -n 8

# Custom input file
python parallel_sim.py -i my_params.txt

# Full specification using flags
python parallel_sim.py -i params.txt -o results -n 16

# Run only first parameter for testing
python parallel_sim.py --runonedp
```

### Output

Each simulation creates an output file named `output_P{p}_M{m}_N{n}_G{g}.txt` containing:
- The command executed
- Exit code
- Runtime in seconds
- Complete stdout/stderr output

Example output during execution:
```
Found 8 simulation(s) to run
Using 4 parallel processes
Output folder: simulator_in_out/outputs
--------------------------------------------------------------------------------
Running: ./run_sim.sh 16 1024 1024 8 -> simulator_in_out/outputs/output_P16_M1024_N1024_G8.txt
✓ Completed: P=16 M=1024 N=1024 group_num=8 (Runtime: 45.23s)
⊘ Skipped: P=32 M=1024 N=1024 group_num=8 (already ran - output file exists)
Running: ./run_sim.sh 48 1024 1024 8 -> simulator_in_out/outputs/output_P48_M1024_N1024_G8.txt
✓ Completed: P=48 M=1024 N=1024 group_num=8 (Runtime: 52.18s)
--------------------------------------------------------------------------------
Summary:
Total: 8 simulations
Successful: 8
Failed: 0
Total runtime: 325.67 seconds (5.43 minutes)

Runtimes:
  P=16 M=1024 N=1024 group_num=8: 45.23s
  P=48 M=1024 N=1024 group_num=8: 52.18s
```

---

## Parallel WSE Execution

The `parallel_wse.py` script runs multiple executions in parallel on WSE-3 hardware.

### Usage

```bash
python parallel_wse.py [options]
```

### Arguments

Positional arguments (all optional):
- `input_file`: Path to input file (default: `wse_in_out/input/input.txt`)
- `output_folder`: Output directory (default: `wse_in_out/outputs`)
- `num_processes`: Number of parallel processes (default: 1)

Flags (alternative to positional arguments):
- `-i, --input FILE`: Input file path
- `-o, --output DIR`: Output directory
- `-n, --num-processes NUM`: Number of parallel processes
- `--max-params NUM`: Maximum number of input parameters to execute (default: 2000)
- `--skip-check`: Skip the executed check and run all parameters (default: False, which means already executed parameters will be skipped)
- `--runonedp`: Run only the first input parameter (for testing)

### Smart Skip Feature

By default, the script automatically skips executions with existing output files. This allows you to:
- Resume interrupted batch jobs
- Add new parameter sets without re-running completed ones
- Use `--skip-check` flag to force re-run all parameters, ignoring existing output files

### Examples

```bash
# Use all defaults (1 process for testing)
python parallel_wse.py

# Custom process count
python parallel_wse.py -n 2

# Custom input file
python parallel_wse.py -i my_params.txt

# Limit to first 500 parameters
python parallel_wse.py --max-params 500

# Force re-run all parameters (ignore existing outputs)
python parallel_wse.py --skip-check

# Full specification using flags
python parallel_wse.py -i params.txt -o results -n 4 --max-params 1000 --skip-check

# Run only first parameter for testing
python parallel_wse.py --runonedp
```

### Output

Each WSE execution creates an output file named `output_P{p}_M{m}_N{n}_G{g}.txt` with the same format as simulator mode.

### Important Notes

- Default process count is 1 for testing/resource management
- Requires access to WSE-3 hardware
- Uses remote cloud-based compilation with Cerebras SDK
- Compilation artifacts are managed remotely by unique IDs

---

## Results Collection

The `collect_results.py` script aggregates results from output files into JSON format.

### Usage

```bash
python collect_results.py --mode {simulator|wse} [output_folder] [json_output_file]
```

### Arguments

Required:
- `--mode {simulator|wse}`: Choose data source

Optional:
- `output_folder`: Path to output folder (defaults based on mode)
- `json_output_file`: Path to output JSON file (defaults based on mode)

Defaults by mode:
- `--mode simulator`: `simulator_in_out/outputs` → `simulator_result.json`
- `--mode wse`: `wse_in_out/outputs` → `wse_result.json`

### Examples

```bash
# Collect simulator results (uses defaults)
python collect_results.py --mode simulator

# Collect WSE results (uses defaults)
python collect_results.py --mode wse

# Custom folder
python collect_results.py --mode simulator custom_outputs

# Custom folder and output file
python collect_results.py --mode wse custom_outputs my_results.json
```

### Output Format

The JSON file contains:
```json
{
  "total_experiments": 8,
  "results": [
    {
      "P": 16,
      "M": 1024,
      "N": 1024,
      "group_num": 8,
      "mean_cycle_count": 887.4
    },
    {
      "P": 32,
      "M": 1024,
      "N": 1024,
      "group_num": 8,
      "mean_cycle_count": 886.2
    }
  ]
}
```

---

## Complete Workflow Examples

### Example 1: Basic Simulator Workflow

```bash
# Generate parameters with defaults
python generate_params.py --simulator

# Run simulations with 8 parallel processes
python parallel_sim.py -n 8

# Collect results
python collect_results.py --mode simulator
```

### Example 2: Custom Parameter Ranges

```bash
# Generate parameters with custom ranges
# P: 16-64 step 16, M: 512-2048 step 512, N=1024, group_num=8
python generate_params.py --simulator my_params.txt 16 64 16 512 2048 512

# Run simulations using the custom parameters
python parallel_sim.py -i my_params.txt -n 8

# Collect results to custom file
python collect_results.py --mode simulator simulator_in_out/outputs my_results.json
```

### Example 3: WSE Workflow (Default)

```bash
# Generate WSE parameters with defaults (P: 16-730 step 64, M/N = 2P,3P,8P, group_num=1,2,4,8)
# This creates 432 parameter combinations
python generate_params.py --wse

# Run on WSE with 2 parallel processes (will limit to first 2000 by default)
python parallel_wse.py -n 2

# Collect results
python collect_results.py --mode wse
```

### Example 4: WSE Workflow (Custom P Range)

```bash
# Generate WSE parameters with custom P range (P: 16-256 step 64)
# This creates 144 parameter combinations (4 P values × 36 combinations)
python generate_params.py --wse wse_params.txt 16 256 64

# Run on WSE
python parallel_wse.py -i wse_params.txt -n 2

# Collect results
python collect_results.py --mode wse
```

### Example 5: Testing Before Full Run

```bash
# Generate full parameter set
python generate_params.py --simulator full_params.txt 16 256 16

# Test with just the first parameter
python parallel_sim.py -i full_params.txt --runonedp

# If successful, run the full set
python parallel_sim.py -i full_params.txt -n 16
```

---

## Tips and Best Practices

### Choosing Number of Processes

**Simulator:**
- Set to the number of CPU cores available
- Check with `nproc` command
- Default of 4 is conservative

**WSE:**
- Start with 1 for testing
- Increase based on WSE resource availability
- Default of 1 is recommended

### Resuming Interrupted Runs

If a batch run is interrupted:
1. Simply re-run the same command
2. The script automatically skips completed experiments
3. Only remaining experiments will be executed

### Adding New Parameter Sets

1. Add new parameter sets to your input file
2. Re-run the same command
3. New experiments will run; existing results preserved

### Force Re-running Specific Experiments

Delete the corresponding output files:
```bash
rm simulator_in_out/outputs/output_P16_M1024_N1024_G8.txt
```

### Monitoring Progress

While experiments run:
```bash
# List output files
ls -lh simulator_in_out/outputs/

# Watch a specific output file
tail -f simulator_in_out/outputs/output_P16_M1024_N1024_G8.txt

# Count completed experiments
ls simulator_in_out/outputs/output_*.txt | wc -l
```

---

## Directory Structure

After running experiments, your directory structure will look like:

```
WSE-3/
├── generate_params.py              # Parameter generation script
├── parallel_sim.py                 # Parallel simulator runner
├── parallel_wse.py                 # Parallel WSE runner
├── collect_results.py              # Results collection script
├── run_sim.sh                      # Single simulation runner
├── run_wse3.sh                     # Single WSE runner
├── simulator_in_out/               # Simulator experiment data
│   ├── input/
│   │   ├── input.txt               # Default input parameters
│   │   └── input_temp.txt          # Generated parameters
│   ├── outputs/                    # Simulation results
│   │   ├── output_P16_M1024_N1024_G8.txt
│   │   ├── output_P32_M1024_N1024_G8.txt
│   │   └── ...
│   └── output_params/              # Compilation artifacts (can be cleaned)
├── wse_in_out/                     # WSE experiment data
│   ├── input/
│   │   ├── input.txt
│   │   └── input_temp.txt
│   └── outputs/                    # WSE results
│       ├── output_P16_M1024_N1024_G8.txt
│       └── ...
├── simulator_result.json           # Collected simulator results
└── wse_result.json                 # Collected WSE results
```

---

## Differences from MeshGEMM Experiments

The MeshGEMV experiment scripts are adapted from the MeshGEMM experiment scripts with these key differences:

1. **Parameters**: Uses `P M N group_num` instead of `P M K N`
   - MeshGEMV: `[1,N] = [1,M] @ [M,N]` on `P×P` PE grid with `group_num` groups
   - MeshGEMM: `[M,N] = [M,K] @ [K,N]` on `P×P` PE grid

2. **Parameter Generation Modes**:
   - **Simulator Mode**: Full user control over all parameter ranges (P, M, N, group_num independent)
   - **WSE Mode**: M, N automatically generated as multiples of P (2P, 3P, 8P)
     - group_num automatically set to 1, 2, 4, 8
     - Default P range: 16-730 step 64 (generates 432 parameter combinations)
     - Each P value generates 3×3×4 = 36 combinations

3. **group_num Parameter**:
   - MeshGEMV: Has `group_num` parameter for PE grouping
   - MeshGEMM: No equivalent parameter

4. **File Naming**:
   - MeshGEMV: `output_P{p}_M{m}_N{n}_G{g}.txt`
   - MeshGEMM: `output_P{p}_M{m}_K{k}_N{n}.txt`

5. **Command Line Arguments**:
   - MeshGEMV Simulator: 13 arguments (includes group_num ranges)
   - MeshGEMV WSE: 3 arguments (P range only, M/N/group_num auto-generated)
   - MeshGEMM: Similar structure but with K instead of group_num

---

## Troubleshooting

### Input file not found
- Check that the path to your input file is correct
- Generate input file with `generate_params.py` first

### run_sim.sh or run_wse3.sh not found
- Ensure the scripts exist in the same directory as the parallel runners
- Check file permissions

### Simulations/Executions failing
- Check individual output files for error messages
- Verify parameters are valid for your hardware
- For WSE: Ensure you have access to WSE-3 resources

### Out of memory errors
- Reduce the number of parallel processes
- Reduce matrix dimensions (M, N)
- Check available system resources

---

## Requirements

- Python 3.6 or higher
- `run_sim.sh` for simulator mode
- `run_wse3.sh` for WSE mode
- Sufficient disk space for output files
- WSE-3 hardware access (for WSE mode)
- Cerebras SDK configured (for WSE mode)
