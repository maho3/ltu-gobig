#PBS -N process_quijote
#PBS -q batch
#PBS -l walltime=4:00:00
#PBS -l nodes=1:ppn=4,mem=16gb
#PBS -t 0-499
#PBS -j oe
#PBS -m a
#PBS -o ${HOME}/data/jobout/${PBS_JOBNAME}.${PBS_JOBID}.log

# Environment
echo cd-ing...

cd /home/mattho/git/ltu-gobig/scripts/preprocess_existing_sims

echo activating environment...
module restore cmass
source /data80/mattho/anaconda3/bin/activate
conda activate cmass


# Kill job if there are any errors
set -e


# Run script
echo running script...
echo "arrayind is ${PBS_ARRAYID}"

# FOR LOOPING AUGMENTATION
for i in $(seq 0 500 1500); do
    lhid=$(($i + $PBS_ARRAYID))
    echo "lhid is $lhid"
    python quijote_rockstar.py --lhid $lhid
done

exit 0