import numpy as np
import os
from os.path import join as pjoin
import h5py
from tqdm import tqdm

from cmass.bias.apply_hod import save_snapshot


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
        :gpos (np.ndarry): Halo positions in Mpc/h. Shape = (nhalos, 3).
        :gvel (np.ndarry): Halo peculiar velocities in km/s. Shape = (nhalos, 3).
        :res (dict): Dictionary of auxilary halo/galaxy properties

    Questions:
        * Do I need to apply redshift correction to velocity?
        
    """
    
    all_fname = os.listdir(source_dir)
    all_fname = [pjoin(source_dir, f) for f in all_fname]
    
    res = {k:None for k in ['Mag', 'MagDust', 'ObsMag', 'ObsMagDust', 'StellarMass', 'Ascale']}
    gpos = None
    gvel = None
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

            if gpos is None:
                gpos = fin['Galaxies/Pos'][:][m]
            else:
                gpos = np.concatenate([gpos, fin['Galaxies/Pos'][:][m]])

            if gvel is None:
                gvel = fin['Galaxies/Vel'][:][m]
            else:
                gvel = np.concatenate([gvel, fin['Galaxies/Vel'][:][m]])

    res['CentralMvir'] = all_mass

    return gpos, gvel, res


def main():
    
    #source_dir = '/home/mattho/data/mtng/GalaxyLightconeMTNG/galaxies_lightcone_01/'
    #out_dir = '/data101/bartlett/mtng/GalaxyLightconeMTNG/galaxies_lightcone_01/'

    source_dir = '/anvil/projects/x-phy240043/x-adelgado1/galaxies_214/' 
    out_dir = '/anvil/projects/x-phy240043/x-dbartlett/galaxies_214/'
    outname = pjoin(out_dir, 'gal_snap_214.hdf5') 

    Mmin = 12.8
    zmin = 0.4
    zmax = 0.7

    # What a to use as key when saving in hdf5 file
    asave = 0.5
    
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        
    gpos, gvel, res = load_halos(source_dir, Mmin, zmin, zmax)
    save_snapshot(outname, asave, gpos, gvel, **res)
    

if __name__ == "__main__":
    main()

