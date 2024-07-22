import numpy as np
import os
from os.path import join as pjoin
import h5py
from tqdm import tqdm


def load_halos(source_dir, Mmin, zmin, zmax):
    """
    Load the halo data from the MTNG simulation at a given redshift
    See https://lgalaxiespublicrelease.github.io/Documentation_databases_henriques2015a_galaxies.pdf
    for a description of the fields of the MTNG output
    
    Args:
        :source_dir (str): Directory containing the catalogues
        :Mmin (float):
        :zmin (float): The minimum redshift to consider
        :zmax (float): The maximum redshift to consider
        
    Returns:
        :pos_h (np.ndarry): Halo positions in Mpc/h. Shape = (nhalos, 3).
        :pos_v (np.ndarry): Halo peculiar velocities in km/s. Shape = (nhalos, 3).
        :mass (np.ndarry): Halo masses in Msun/h. Shape = (nhalos,).

    Questions:
        * Do I need to apply redshift correction to velocity?
        
    """
    
    all_fname = os.listdir(source_dir)
    all_fname = [pjoin(source_dir, f) for f in all_fname]
    
    res = {k:None for k in ['Pos', 'Vel', 'Mag', 'MagDust', 'ObsMag', 'ObsMagDust', 'StellarMass']}
    all_mass = None
    
    for i in tqdm(range(len(all_fname))):
    
        with h5py.File(all_fname[i], 'r') as fin:
            mass = fin['Galaxies/CentralMvir'][:]  # 1e10 Msun / h
            mass = np.log10(mass) + 10

            ascale = fin['Galaxies/Ascale'][:]
            redshift = 1 / ascale - 1

            # Mask based on mass and redshift
            m = (mass > Mmin) & (redshift >= zmin) & (redshift <= zmax)
            mass = mass[m]
            redshift = redshift[m]

            for k in res.keys():
                if res[k] is None:
                    res[k] = fin[f'Galaxies/{k}'][:][m]
                else:
                    res[k] = np.concatenate([res[k], fin[f'Galaxies/{k}'][:][m]])
                    
            if all_mass is None:
                all_mass = mass.copy()
            else:
                all_mass = np.concatenate([all_mass, mass])

    return res, all_mass


def main():
    
    source_dir = '/home/mattho/data/mtng/GalaxyLightconeMTNG/galaxies_lightcone_01/'
    out_dir = '/data101/bartlett/mtng/GalaxyLightconeMTNG/galaxies_lightcone_01/'
    Mmin = 12.8
    zmin = 0.4
    zmax = 0.7
    
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        
    res, mass = load_halos(source_dir, Mmin, zmin, zmax)
    np.save(pjoin(out_dir, 'halo_mass.npy'), mass)  # log10(halo masses [Msun/h])
    for k in res.keys():
        if k in ['Pos', 'Vel']:
            np.save(pjoin(out_dir, f'halo_{k.lower()}.npy'), res[k])
        else:
            np.save(pjoin(out_dir, f'galaxy_{k.lower()}.npy'), res[k])
    
if __name__ == "__main__":
    main()
