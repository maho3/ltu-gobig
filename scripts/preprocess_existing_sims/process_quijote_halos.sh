#!/bin/bash
#SBATCH --job-name=fix_quijote   # Job name
#SBATCH --array=0-499         # Job array range for lhid
#SBATCH --nodes=1               # Number of nodes
#SBATCH --ntasks=8            # Number of tasks
#SBATCH --time=03:00:00         # Time limit
#SBATCH --partition=shared      # Partition name
#SBATCH --account=phy240043   # Account name
#SBATCH --output=/anvil/scratch/x-mho1/jobout/%x_%A_%a.out  # Output file for each array task
#SBATCH --error=/anvil/scratch/x-mho1/jobout/%x_%A_%a.out   # Error file for each array task

module restore cmass
source /anvil/projects/x-phy240043/x-mho1/anaconda3/bin/activate
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
    python quijote_rockstar.py --lhid $lhid

    cd /home/x-mho1/git/ltu-cmass
    python -m cmass.diagnostics.summ nbody=quijote sim=nbody nbody.lhid=$lhid
done

exit 0