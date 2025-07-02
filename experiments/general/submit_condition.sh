#!/bin/bash
#SBATCH --job-name=condition_on_sigma # Job name
#SBATCH --array=2-199        # 200 jobs in total
#SBATCH --nodes=1               # Number of nodes
#SBATCH --ntasks=8            # Number of tasks
#SBATCH --time=1:00:00         # Time limit
#SBATCH --partition=shared  # Partition name
#SBATCH --account=phy240043  # Account name
#SBATCH --output=/anvil/scratch/x-dbartlett/jobout/%x_%A_%a.out  # Output file for each array task
#SBATCH --error=/anvil/scratch/x-dbartlett/jobout/%x_%A_%a.out   # Error file for each array task

set -e 

module purge
module restore cmass_env
conda activate cmass

cd /home/x-dbartlett/ltu-gobig/experiments/general

# Calculate the starting index for this array task
start=$((SLURM_ARRAY_TASK_ID * 5))
end=$((start + 4))

# Loop over 5 iterations
for ((i=start; i<=end; i++)); do
    echo "Running iteration $i on SLURM_ARRAY_TASK_ID=$SLURM_ARRAY_TASK_ID"
    # python3 condition_on_sigma.py ind=$i nbody=quijotelike sim=fastpm_varnoise
    python3 condition_on_sigma.py --ind $i --test_nbody quijote --test_sim varnoise --sim fastpm_recnoise
done
