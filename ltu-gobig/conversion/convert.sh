
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
conda activate cmassrun

cd /home/mattho/git/ltu-gobig/ltu-gobig/conversion

suite=quijote
sim=nbody
L=1000
N=128
SIMDIR=/automnt/data80/mattho/cmass-ili/${suite}/${sim}/L${L}-N${N}

# # FOR INDIVIDUAL RUNS
# # lhid=$(($PBS_ARRAYID))
lhid=0
python convert_to_h5.py --suite=$SIMDIR --lhid=$lhid --del_old

# # FOR ONLY LOOPING
# for lhid in 1660 1652 1440 1443 1448 1541 1439 1545 1549; do
#     echo "Converting $lhid"
#     python convert_to_h5.py --suite=$SIMDIR --lhid=$lhid --del_old
# done

# FOR LOOPING AUGMENTATION
# PBS_ARRAYID=3
# for i in $(seq 0 100 1900); do
#     lhid=$(($i + $PBS_ARRAYID))
#     python convert_to_h5.py --suite=$SIMDIR --lhid=$lhid --del_old
# done
