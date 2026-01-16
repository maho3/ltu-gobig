#!/bin/bash

module purge
module restore cmass_env
conda activate cmass

echo $(which python)

# Stop if error raised
set -e

# Command to run for each lhid
cd /home/x-dbartlett/ltu-cmass

nbody=quijote
sim=nbody_nonoise
infer=simple

halo=False
galaxy=True
ngc=False
sgc=False
mtng=False

exp_index=2
net_index=0

extras="nbody.zf=0.500015"
device=cpu

suffix="nbody=$nbody sim=$sim infer=$infer infer.exp_index=$exp_index infer.net_index=$net_index"
suffix="$suffix infer.halo=$halo infer.galaxy=$galaxy"
suffix="$suffix infer.ngc_lightcone=$ngc infer.sgc_lightcone=$sgc infer.mtng_lightcone=$mtng"
suffix="$suffix infer.device=$device $extras"

echo "Running inference with $suffix"
# python3 -m cmass.infer.preprocess $suffix
python -m cmass.infer.train $suffix net=tuning
# python -m cmass.infer.validate $suffix
