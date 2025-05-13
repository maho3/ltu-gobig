#!/bin/bash
#SBATCH --job-name=process_quijote  # Job name
#SBATCH --array=0-499  # Array range
#SBATCH --nodes=1               # Number of nodes
#SBATCH --ntasks=4            # Number of tasks
#SBATCH --time=4:00:00         # Time limit
#SBATCH --partition=shared  # Partition name
#SBATCH --account=phy240043  # Account name
#SBATCH --output=/anvil/scratch/x-mho1/jobout/%x_%A_%a.out  # Output file for each array task
#SBATCH --error=/anvil/scratch/x-mho1/jobout/%x_%A_%a.out   # Error file for each array task


# SLURM_ARRAY_TASK_ID=499


# Environment
echo cd-ing...

cd /home/x-mho1/git/ltu-gobig/scripts/preprocess_existing_sims

echo activating environment...
module restore cmass
conda activate cmass


# Kill job if there are any errors
set -e

# Run script
echo running script...
echo "arrayind is ${SLURM_ARRAY_TASK_ID}"

# FOR LOOPING AUGMENTATION
for i in $(seq 0 500 1500); do
    lhid=$(($i + $SLURM_ARRAY_TASK_ID))
    echo "lhid is $lhid"

    cd /home/x-mho1/git/ltu-gobig/scripts/preprocess_existing_sims
    # python quijote_rockstar.py --lhid $lhid
    python quijote_fof.py --lhid $lhid

done

exit 0