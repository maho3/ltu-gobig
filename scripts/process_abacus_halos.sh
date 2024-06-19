#!/bin/bash
#PBS -S /bin/sh
#PBS -N abacus_halos
#PBS -j oe
#PBS -l nodes=1:ppn=16,walltime=02:00:00

#module purge
source /home/chartier/myModules/abacus_halos/bin/activate
#source /home/chartier/Modules/abacus_env/bin/activate
echo "Modules loaded successfully"

export basePath="/home/mattho/data/abacus"
export destPath="/data74/chartier/abacus"
#export basePath="/home/chartier/Documents/LTU_ILI/iliData/abacus_test"
#export destPath="/home/chartier/Documents/LTU_ILI/iliData/abacus_test"
export z=0.5
export threads=8

cd /home/chartier/abacus_halos
#cd /home/chartier/Documents/LTU_ILI/iliData/abacus_test/ltu-gobig/ltu-gobig/preprocessing/

# LOOP THROUGH THE LIST OF SEEDS # eg 130 to 181
startSeed=130
endSeed=130

for k in $(seq $startSeed $endSeed)
do
    echo $k
    echo $destPath/$k
    mkdir -p $destPath/$k
    echo "$basePath/AbacusSummit_base_c$k""_ph000"
    python abacus.py $threads "$basePath/AbacusSummit_base_c$k""_ph000" $z "$destPath/$k" True

    
done

exit 0

