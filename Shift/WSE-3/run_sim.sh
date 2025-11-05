#!/bin/bash
set -e
P=$1
L=$2
M=$3
N=$4
fabric_w=$(($1 + $2 + 7)) # P + L
fabric_h=$(($1 + 2)) # P

Mt=$(($3 / $1))
Nt=$(($4 / $1))

# Create parameter-specific output folder to support parallel runs
# All parameter-specific folders are organized under simulator_in_out/output_params/
mkdir -p simulator_in_out/output_params
OUT_DIR="simulator_in_out/output_params/out_P${P}_L${L}_M${M}_N${N}"

echo "P=$1, L=$2, M=$3, N=$4"
echo "Output directory: $OUT_DIR"

cslc --arch=wse3 ./src/layout.csl --fabric-dims="$fabric_w","$fabric_h" --fabric-offsets=4,1 \
    --params=P:"$P",L:"$L",Mt:"$Mt",Nt:"$Nt" \
    -o "$OUT_DIR" --memcpy --channels 1

cs_python ./launch_sim.py --P "$P" --L "$L" --M "$M" --N "$N" --out-dir "$OUT_DIR"