#!/bin/sh
#PBS -S /bin/sh
#PBS -N process_quijote_halos
#PBS -j oe
#PBS -m ae
#PBS -l nodes=h02:ppn=16,walltime=24:00:00

# Environment
source /home/bartlett/.bashrc
source /home/bartlett/anaconda3/etc/profile.d/conda.sh
conda deactivate
conda activate ili-sbi

# Kill job if there are any errors
set -e

cd
cd ili/ltu-gobig/ltu-gobig/preprocessing
python3 quijote.py

conda deactivate

exit 0