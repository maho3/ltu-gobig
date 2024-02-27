import numpy as np
import readfof
import os
from os.path import join as pjoin
from tqdm import tqdm


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
    z_dict = {0.0:4, 0.5:3, 1.0:2, 2.0:1, 3.0:0}
    snapnum = z_dict[redshift]
    snapdir = pjoin(source_dir, str(simnum))
    
    # read the halo catalogue
    FoF = readfof.FoF_catalog(snapdir, snapnum, long_ids=False,
                              swap=False, SFR=False, read_IDs=False)

    # get the properties of the halos
    pos_h = FoF.GroupPos/1e3             #Halo positions in Mpc/h
    mass  = np.log10(FoF.GroupMass*1e10) #Halo masses in Msun/h
    vel_h = FoF.GroupVel  #Halo peculiar velocities in km/s. Note Pylians usually adds (1.0+redshift) here
    
    return pos_h, vel_h, mass


def main():
    
    source_dir = '/home/mattho/data/quijote/Halos/latin_hypercube_HR/'
    out_dir = '/data101/bartlett/quijote/Halos/latin_hypercube_HR/'
    redshift = 0.5
    
    all_simnum = os.listdir(source_dir)
    all_simnum = [a for a in all_simnum if a.isnumeric()]
    
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    
    for i in tqdm(range(len(all_simnum))):
        out_path = pjoin(out_dir, str(all_simnum[i]))
        if not os.path.isdir(out_path):
            os.mkdir(out_path)
        hpos, hvel, hmass = load_halos(source_dir, all_simnum[i], redshift)
        np.save(pjoin(out_path, 'halo_pos.npy'), hpos)  # halo positions [Mpc/h]
        np.save(pjoin(out_path, 'halo_vel.npy'), hvel)  # halo velocities [km/s]
        np.save(pjoin(out_path, 'halo_mass.npy'), hmass)  # halo masses [Msun/h]
    
if __name__ == "__main__":
    main()
