#!/bin/bash

set -e 

# module purge
# module restore cmass_env
# conda activate cmass

lhid=665

cd /home/x-dbartlett/ltu-cmass/

all_sigma=(0.5)
all_uniform=(True False)

# Loop through each sigma value and run the command
for noise_uniform in "${all_uniform[@]}"; do
    for sigma in "${all_sigma[@]}"; do
        echo "Running with noise_uniform=$noise_uniform"
        echo "Running with sigma=$sigma"
        python -m cmass.diagnostics.summ \
            nbody=abacuslike \
            noise=fixed \
            nbody.lhid=$lhid \
            sim=fastpm \
            diag.halo=true \
            bias.hod.noise_uniform=True \
            noise.params.radial=$sigma \
            noise.params.transverse=$sigma \
            diag.summaries=['Pk'] \
            diag.focus_z=0.7 \
            diag.from_scratch=True

        # Extract directory name
        dir_name=/anvil/scratch/x-dbartlett/cmass/abacuslike/fastpm/L2000-N256/665/diag/

        # Rename the output file
        mv $dir_name/halos.h5 $dir_name/halos_sigma_${sigma}_noise_uniform_${noise_uniform}.h5
    done
done
