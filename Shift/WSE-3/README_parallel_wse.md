# Parallel WSE Runner

A Python script to run multiple WSE executions in parallel using `run_wse3.sh`.

## Overview

`parallel_wse.py` allows you to execute multiple WSE runs with different parameter sets in parallel, utilizing multiple CPU cores to speed up the process. Each WSE execution's output is saved to a separate file.

**Cloud-Based Compilation**: Unlike the simulator which stores compiled artifacts locally, WSE uses the Cerebras SDK's remote compilation service (`SdkCompiler`). Compiled artifacts are stored remotely and referenced by unique `artifact_id` values. This enables parallel execution without needing parameter-specific local folders, as each compilation gets its own unique identifier managed by the Cerebras infrastructure.

**Smart Skip Feature**: The script automatically skips WSE executions that have already been run by checking for existing output files in the output folder (default: `wse_in_out/outputs/`). If a file named `output_P<p>_L<l>_M<m>_N<n>.txt` exists, that execution will be skipped. This allows you to safely re-run the script to resume interrupted batch jobs or add new parameter sets without wasting time on already-completed executions.

## Quick Start

The repository includes a pre-configured `wse_in_out/input/input.txt` file with sample parameters. To run WSE executions immediately:

```bash
# Run WSE executions with defaults (1 process for testing)
python parallel_wse.py

# Run with more parallel processes
python parallel_wse.py -n 4
```

This will read parameters from `wse_in_out/input/input.txt`, run WSE executions in parallel (using 1 process by default), and save outputs to `wse_in_out/outputs/`.

## Usage

```bash
python parallel_wse.py [options]
```

### Arguments

You can use either positional arguments or flags (or mix them):

**Positional arguments** (all optional):
- `input_file`: Path to a text file containing parameter sets (one per line) (default: `wse_in_out/input/input.txt`)
- `output_folder`: Directory where output files will be saved (created if it doesn't exist) (default: `wse_in_out/outputs`)
- `num_processes`: Number of parallel processes to use (e.g., 1, 2, 4) (default: `1`)

**Flags** (alternative to positional arguments):
- `-i, --input FILE`: Input file path
- `-o, --output DIR`: Output directory
- `-n, --num-processes NUM`: Number of parallel processes

Flags take precedence over positional arguments if both are specified.

## Generating Parameter Sets

The `generate_params.py` script can automatically generate parameter sets optimized for WSE hardware constraints.

### Overview

WSE mode generates parameter combinations (P, L, M, N) with specific rules:
- **P**: Specific sequence from 16 to 650
  - First 5 steps: 16, 32, 48, 64, 80 (increment by 16)
  - Next 5 steps: 112, 144, 176, 208, 240 (increment by 32)
  - Remaining steps: 304, 368, 432, 496, 560, 624 (increment by 64)
- **L**: Starts at 1, doubles until reaching 3×P
  - **WSE Constraint**: L + P < 740 (hardware fabric limit)
- **M and N**: Always equal, start at P, double until reaching 8×P

### Usage

```bash
python generate_params.py --wse [output_file]
```

### Arguments

- `--wse`: Required flag to enable WSE mode
- `output_file`: Path where parameter file will be saved (default: `wse_in_out/input/input_temp.txt`)

**Note**: WSE mode does not support the `--max-product` flag. It only uses the L+P < 740 constraint based on hardware fabric limits.

### Examples

```bash
# Use defaults: generates parameters to wse_in_out/input/input_temp.txt
python generate_params.py --wse

# Generate to custom output file
python generate_params.py --wse wse_in_out/input/my_params.txt
```

### Output

The script will:
- Generate 536 parameter sets (16 filtered due to L+P >= 740 constraint)
- Create a file with header comments documenting the generation rules
- List all parameter sets in format: `P L M N`

**Example generated file**:
```
# Auto-generated parameter sets (WSE mode)
# P: WSE-specific sequence (16-650)
# L: Start at 1, double until 3*P (constraint: L+P < 740)
# M=N: Start at P, double until 8*P
# Format: P L M N
#
16 1 16 16
16 1 32 32
16 1 64 64
16 1 128 128
16 2 16 16
...
```

### Complete Workflow with Parameter Generation

```bash
# Step 1: Generate WSE parameter sets
python generate_params.py --wse wse_in_out/input/my_params.txt

# Step 2: Run parallel WSE executions with generated parameters
python parallel_wse.py wse_in_out/input/my_params.txt wse_in_out/outputs 2

# Step 3: Monitor progress
ls -lh wse_in_out/outputs/
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
# WSE parameter sets
# Format: P L M N
8 8 8 8
10 10 10 10
12 12 12 12
16 16 16 16
```

## Output

Each WSE execution produces an output file in the specified output folder with the naming pattern:

```
output_P<p>_L<l>_M<m>_N<n>.txt
```

For example, a WSE execution with parameters `P=8 L=8 M=8 N=8` will create:

```
output_P8_L8_M8_N8.txt
```

Each output file contains:
- The command that was executed
- The exit code
- The runtime in seconds
- The complete stdout/stderr output from the WSE execution

## Examples

### Example 1: Run with all defaults (recommended for quick start)

```bash
# Uses wse_in_out/input/input.txt as input, outputs to wse_in_out/outputs folder, 1 parallel process
python parallel_wse.py
```

### Example 2: Only specify number of processes

```bash
# Use default input and output, but run with 2 processes
python parallel_wse.py -n 2

# Or use the long form
python parallel_wse.py --num-processes 4
```

### Example 3: Custom input file, default output and processes

```bash
# Using positional argument
python parallel_wse.py params.txt

# Using flag
python parallel_wse.py -i params.txt
```

### Example 4: Custom input and output, default processes

```bash
# Using positional arguments
python parallel_wse.py params.txt custom_outputs

# Using flags
python parallel_wse.py -i params.txt -o custom_outputs
```

### Example 5: Specify all parameters

```bash
# Using positional arguments
python parallel_wse.py my_parameters.txt wse_results 2

# Using flags
python parallel_wse.py -i my_parameters.txt -o wse_results -n 2

# Mix positional and flags
python parallel_wse.py my_parameters.txt -o wse_results -n 2
```

### Example 6: Run only first parameter for testing

```bash
# Run only the first parameter, always execute (no skip)
python parallel_wse.py --runonedp
```

## Output Example

When running, you'll see progress messages:

```
Found 4 WSE execution(s) to run
Using 1 parallel processes
Output folder: wse_in_out/outputs
--------------------------------------------------------------------------------
Running: ./run_wse3.sh 8 8 8 8 -> wse_in_out/outputs/output_P8_L8_M8_N8.txt
⊘ Skipped: P=10 L=10 M=10 N=10 (already ran - output file exists)
✓ Completed: P=8 L=8 M=8 N=8 (Runtime: 125.23s)
Running: ./run_wse3.sh 12 12 12 12 -> wse_in_out/outputs/output_P12_L12_M12_N12.txt
✓ Completed: P=12 L=12 M=12 N=12 (Runtime: 187.89s)
--------------------------------------------------------------------------------
Summary:
Total: 4 WSE executions
Successful: 4
Failed: 0
Total runtime: 313.12 seconds (5.22 minutes)

Runtimes:
  P=8 L=8 M=8 N=8: 125.23s
  P=12 L=12 M=12 N=12: 187.89s
```

**Note**: WSE executions that have already been run (output file exists) will be automatically skipped with a "⊘ Skipped" message. Runtime measurements are displayed for each completed execution and in the summary.

## Tips

- **Choosing num_processes**: Start with 1 for testing. For production runs, set this based on your WSE resource availability and system capacity.

- **Resuming interrupted runs**: If a batch WSE execution is interrupted, simply re-run the same command. The script will automatically skip already-completed executions and only run the remaining ones.

- **Adding new parameter sets**: You can add new parameter sets to your input file and re-run the script. Only the new WSE executions will be executed; existing results will be preserved.

- **Re-running specific executions**: To force a re-run of specific WSE executions, delete their corresponding output files before running the script.

- **Monitoring**: While WSE executions run, you can check the output folder to see intermediate results:
  ```bash
  ls -lh wse_in_out/outputs/
  tail -f wse_in_out/outputs/output_P8_L8_M8_N8.txt
  ```

- **Error handling**: If any WSE execution fails, the script will continue running others and report failures in the summary.

## Requirements

- Python 3.6 or higher
- `run_wse3.sh` must be in the same directory as `parallel_wse.py`
- Sufficient disk space for output files
- Access to WSE hardware resources

## Troubleshooting

**Error: Input file not found**
- Check that the path to your input file is correct

**Error: run_wse3.sh not found**
- Ensure `run_wse3.sh` exists in the same directory as `parallel_wse.py`

**WSE executions failing**
- Check individual output files in the output folder for error messages
- Verify that your parameters are valid for `run_wse3.sh`
- Ensure you have access to WSE hardware resources

## How WSE Artifact Storage Works

WSE uses a fundamentally different approach to compilation and artifact storage compared to the simulator:

1. **Remote Compilation**: The `compile.py` script uses `SdkCompiler` from Cerebras SDK, which is a cloud-based compilation service that runs on Cerebras infrastructure.

2. **Artifact IDs Instead of Local Files**: When compilation completes, it returns an `artifact_id` (a unique identifier). Only a small JSON file containing this ID is stored locally in `compile_out/artifact_<P>_<L>_<Mt>_<Nt>.json`.

3. **Remote Artifact Storage**: The actual compiled binary artifacts are stored remotely on Cerebras servers and fetched on-demand when `launch_wse3.py` runs using `SdkRuntime(artifact_id)`.

4. **No Local Artifact Conflicts**: Because artifacts are managed remotely by unique IDs, there's no need for parameter-specific local directories like the simulator uses. Multiple WSE compilations can run in parallel without conflicting.

Example directory structure after running parallel WSE executions:
```
WSE-3/
├── compile_out/                          # Local artifact ID references only
│   ├── artifact_16_1_1_1.json            # Contains artifact_id for remote artifact
│   ├── artifact_32_2_2_2.json            # Contains artifact_id for remote artifact
│   └── ...
├── wse_in_out/
│   └── outputs/                          # WSE execution results (checked for skip feature)
│       ├── output_P16_L1_M16_N16.txt     # Results for first parameter set
│       ├── output_P32_L2_M32_N32.txt     # Results for second parameter set
│       └── ...
...
```

**Note**: The `compile_out/` directory only contains small JSON files (~100 bytes each), not full compiled binaries. The actual compilation artifacts are stored remotely by Cerebras infrastructure.

## Differences from Simulator Parallel Execution

- Default number of processes is 1 (instead of 4) for testing and resource management
- Uses `run_wse3.sh` instead of `run_sim.sh`
- Default input/output directories are in `wse_in_out/` instead of `simulator_in_out/`
- Uses remote cloud-based compilation (`SdkCompiler`) instead of local compilation (`cslc`)
- Stores only artifact IDs locally instead of full compiled binaries
- WSE executions may require specific hardware access and permissions
- No need to clean up large compilation artifact directories
