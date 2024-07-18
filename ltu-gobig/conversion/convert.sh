
#!/bin/sh
#PBS -S /bin/sh
#PBS -N convert
#PBS -l nodes=1:ppn=8,mem=16gb
#PBS -l walltime=2:00:00
#PBS -j oe
#PBS -o ${HOME}/data/jobout/${PBS_JOBNAME}.${PBS_JOBID}.log
#PBS -t 0-99

module restore cmass
source /data80/mattho/anaconda3/bin/activate
conda activate cmass

cd /home/mattho/git/ltu-gobig/ltu-gobig/conversion

SIMDIR=/automnt/data80/mattho/cmass-ili/2gpch_0704/borgpm/L2000-N256

for i in $(seq 0 100 900); do
    lhid=$(($i + $PBS_ARRAYID))
    python convert_to_h5.py --suite=$SIMDIR --lhid=$lhid --del_old
done
