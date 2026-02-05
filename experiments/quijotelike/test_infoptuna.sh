#!/bin/bash

SLURM_ARRAY_TASK_ID=0

module restore cmass_env
conda activate cmass

exp_index=0
net_index=$SLURM_ARRAY_TASK_ID

sleep $net_index  # to stagger the start of each job

# Command to run for each lhid
cd /home/x-dbartlett/ltu-cmass

nbody=quijote
sim=nbody_nonoise_appended
infer=append_noise

halo=False
galaxy=True
ngc=False
sgc=False
mtng=False
simbig=False

extras="nbody.zf=0.5" # 
device="cpu"

export TQDM_DISABLE=0
extras="$extras hydra/job_logging=disabled"

suffix="nbody=$nbody sim=$sim infer=$infer infer.exp_index=$exp_index infer.net_index=$net_index"
suffix="$suffix infer.halo=$halo infer.galaxy=$galaxy"
suffix="$suffix infer.ngc_lightcone=$ngc infer.sgc_lightcone=$sgc infer.mtng_lightcone=$mtng infer.simbig_lightcone=$simbig"
suffix="$suffix infer.device=$device $extras"
# suffix="$suffix infer.val_frac=0 infer.test_frac=1"
suffix="$suffix infer.include_noise=False infer.include_hod=False"

echo "Running inference pipeline with $suffix"

# python -m cmass.infer.train $suffix net=nsfonly
python -m cmass.infer.optuna $suffix # net=nsfonly
