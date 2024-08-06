import numpy as np
import os
from os.path import join as pjoin
from tqdm import tqdm
from cmass.bias.rho_to_halo import save_snapshot


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
    mass_type = 'rockstar_200c'
    min_logM = 13.0

    z_dict = {0.0: 4, 0.5: 3, 1.0: 2, 2.0: 1, 3.0: 0}
    snapnum = z_dict[redshift]
    snapdir = pjoin(source_dir, str(simnum))
    rockstar = np.loadtxt(snapdir + '/out_' + str(snapnum) + '_pid.list')

    with open(snapdir + '/out_' + str(snapnum) + '_pid.list', 'r') as f:
        lines = f.readlines()
    header = lines[0].split()

    hpos = rockstar[:, header.index('X'):header.index('Z')+1]
    hvel = rockstar[:, header.index('VX'):header.index('VZ')+1]

    if mass_type == 'rockstar_vir':
        index_M = header.index('Mvir')
        hmass = rockstar[:, index_M]  # Halo masses in Msun/h
    if mass_type == 'rockstar_200c':
        index_M = header.index('M200c')
        hmass = rockstar[:, index_M]  # Halo masses in Msun/h

    # Remove halos with mass < min_logM
    mask = hmass > 10**min_logM
    hpos = hpos[mask]
    hvel = hvel[mask]
    hmass = hmass[mask]
    del mask

    # Convert to physical units
    hmass = np.log10(hmass)  # Halo masses in log10(Msun/h)
    hvel *= (1.0 + redshift)  # Halo peculiar velocities in km/s

    return hpos, hvel, hmass


def main():

    source_dir = '/globus/mattho/Quijote_simulations/Halos/Rockstar/latin_hypercube_HR'
    out_dir = '/data80/mattho/data/cmass-ili/quijote/nbody/L1000-N128'
    redshift = 0.5
    a = 1/(1+redshift)

    all_simnum = os.listdir(source_dir)
    all_simnum = [a for a in all_simnum if a.isnumeric()]

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    for i in tqdm(range(len(all_simnum))):
        out_path = pjoin(out_dir, str(all_simnum[i]))
        os.makedirs(out_path, exist_ok=True)

        hpos, hvel, hmass = load_halos(source_dir, all_simnum[i], redshift)
        save_snapshot(out_path, a, hpos=hpos, hvel=hvel, hmass=hmass)


if __name__ == "__main__":
    main()
