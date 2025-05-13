#!/bin/bash
#SBATCH --job-name=abacus  # Job name
#SBATCH --array=6-118  # Array range
#SBATCH --nodes=1               # Number of nodes
#SBATCH --ntasks=16            # Number of tasks
#SBATCH --time=4:00:00         # Time limit
#SBATCH --partition=shared  # Partition name
#SBATCH --account=phy240043  # Account name
#SBATCH --output=/anvil/scratch/x-mho1/jobout/%x_%A_%a.out  # Output file for each array task
#SBATCH --error=/anvil/scratch/x-mho1/jobout/%x_%A_%a.out   # Error file for each array task


# SLURM_ARRAY_TASK_ID=110

# module purge
module restore cmass
conda activate cmass
echo "Modules loaded successfully"

basePath="/anvil/scratch/x-mho1/abacus/base"
destPath="/anvil/scratch/x-mho1/cmass-ili/abacus/custom/L2000-N256"
z=0.5
threads=8

cd /home/x-mho1/git/ltu-gobig/scripts/preprocess_existing_sims
#cd /home/chartier/Documents/LTU_ILI/iliData/abacus_test/ltu-gobig/ltu-gobig/preprocessing/

lhid=$SLURM_ARRAY_TASK_ID
echo $lhid
echo $destPath/$lhid
mkdir -p $destPath/$lhid
python abacus.py $threads $lhid $z "$destPath/$lhid" 0
