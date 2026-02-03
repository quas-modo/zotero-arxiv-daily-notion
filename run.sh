#!/bin/bash

# Helper script to run Python with the daily_reading_paper conda environment

CONDA_BASE="/mnt/shared-storage-user/chenxinyi1/env/miniconda3"
ENV_NAME="daily_reading_paper"
PYTHON_BIN="$CONDA_BASE/envs/$ENV_NAME/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "Error: Python not found in conda environment"
    echo "Please make sure the environment is set up correctly"
    exit 1
fi

exec "$PYTHON_BIN" "$@"
