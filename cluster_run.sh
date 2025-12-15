#!/bin/bash
#$ -clear
#$ -S /bin/bash
#$ -N bubble_train       # Nombre del job
#$ -cwd                  # Usa el directorio actual como working dir
#$ -pe neworte 2         # Cantidad de cores por job (ajustá según tu entorno)
#$ -l mem=2G
##$ -l gpu=0
##$ -t 1-5                # Crea 5 tareas (array job)
#$ -o logs/$JOB_NAME_$JOB_ID_$TASK_ID.out
#$ -e logs/$JOB_NAME_$JOB_ID_$TASK_ID.err

# Cargá tu entorno o activá conda
module load miniconda
conda activate sb3

echo "env loaded"

# Cada tarea obtiene un ID distinto ($SGE_TASK_ID)
LOG_DIR="./Terrain/PPO_${SGE_TASK_ID}"
mkdir -p "$LOG_DIR"

echo "log_dir created"

# # send outputs to the log folder
# OUT_FILE="${LOG_DIR}/${JOB_NAME}.${SGE_TASK_ID}.out"
# ERR_FILE="${LOG_DIR}/${JOB_NAME}.${SGE_TASK_ID}.err"

# # --- Redirect all output ---
# exec > >(tee -a "$OUT_FILE") 2> >(tee -a "$ERR_FILE" >&2)

# Decide which Python script to run
PYTHON_SCRIPT="cluster_run.py"

# Check that the script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: Python file '$PYTHON_SCRIPT' not found!"
    exit 1
else
    echo "about to run ${PYTHON_SCRIPT}"
fi

echo "Starting training task $SGE_TASK_ID"
echo "  Python script:   $PYTHON_SCRIPT"
echo "  Job Folder:      $FOLDER"
echo "  Log directory:   $LOG_DIR"
echo "  Host:            $(hostname)"


python "$PYTHON_SCRIPT"