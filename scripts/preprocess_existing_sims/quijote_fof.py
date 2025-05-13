import numpy as np
import readfof
import os
from os.path import join as pjoin
from cmass.bias.rho_to_halo import save_snapshot
import argparse


def load_halos(source_dir, simnum, redshift):
    """
    Load the halo data from a given Quijote simulation at a given redshift

    Args:
        :source_dir (str): Directory containing all simulations
        :simnum (int): The number of the simulation to use
        :redshift (float): The redshift to use. For Quijote this must be in [0.0, 0.5, 1.0, 2.0, 3.0]

    Returns:
        :pos_h (np.ndarry): Halo positions in Mpc/h. Shape = (nhalos, 3).
        :pos_v (np.ndarry): Halo peculiar velocities in km/s. Shape = (nhalos, 3).
        :mass (np.ndarry): Halo masses in Msun/h. Shape = (nhalos,).

    """
    # Parameters
    min_logM = np.log10(5e12)

    z_dict = {0.0: 4, 0.5: 3, 1.0: 2, 2.0: 1, 3.0: 0}
    snapnum = z_dict[redshift]
    snapdir = pjoin(source_dir, str(simnum))

    # read the halo catalogue
    FoF = readfof.FoF_catalog(snapdir, snapnum, long_ids=False,
                              swap=False, SFR=False, read_IDs=False)

    # get the properties of the halos
    hpos = FoF.GroupPos/1e3                 # Halo positions in Mpc/h
    hvel = FoF.GroupVel * (1.0 + redshift)  # Halo peculiar velocities in km/s
    hmass = np.log10(FoF.GroupMass*1e10)      # Halo masses in log10(Msun/h)

    # Remove halos with mass < min_logM
    mask = hmass > min_logM
    hpos = hpos[mask]
    hvel = hvel[mask]
    hmass = hmass[mask]
    del mask

    # typecast to float32
    hpos = hpos.astype(np.float32)
    hvel = hvel.astype(np.float32)
    hmass = hmass.astype(np.float32)

    return hpos, hvel, hmass


def main():

    source_dir = '/anvil/scratch/x-mho1/quijote/Halos/FoF/latin_hypercube_HR/'
    out_dir = '/anvil/scratch/x-mho1/cmass-ili/quijote/nbody_fof/L1000-N128'
    redshift = 0.5
    a = 1/(1+redshift)

    # Parse the lhid
    parser = argparse.ArgumentParser()
    parser.add_argument('--lhid', type=int)
    args = parser.parse_args()
    lhid = args.lhid

    out_path = pjoin(out_dir, str(lhid))
    os.makedirs(out_path, exist_ok=True)
    outfile = pjoin(out_path, 'halos.h5')
    if os.path.isfile(outfile):
        # # Delete the existing file
        # os.remove(outfile)
        print(f'Skipping lhid={lhid} as file already exists')
        return
    print(
        f'Processing snapshot from {source_dir} for '
        f'lhid={lhid} to save at {out_path}')

    hpos, hvel, hmass = load_halos(source_dir, lhid, redshift)

    save_snapshot(out_path, a, hpos=hpos, hvel=hvel, hmass=hmass)


if __name__ == "__main__":
    main()
