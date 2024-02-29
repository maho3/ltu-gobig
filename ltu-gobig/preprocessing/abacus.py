import numpy as np
import os
import sys
import abacusnbody.data.asdf
from abacusnbody.data.compaso_halo_catalog import CompaSOHaloCatalog


def halos_to_cmass(rootdir, z, m_min, m_max, all_at_once = True):

    '''
    doc
    '''
    z_dict = {0.5:"z0.500"}

    # snapdir should have a subfolder such that we have the structure "...snapdir/halo_info/halo_info*.asdf"
    snapdir = os.path.join(rootdir, z_dict[z])

    if all_at_once:

        cat = CompaSOHaloCatalog(snapdir, cleaned = False, fields = ["N", "x_com","v_com"])
        MHsun = cat.header["ParticleMassHMsun"]
        N_min = int(m_min/MHsun)
        N_max = int(m_max/MHsun)
        cat = cat.halos[(cat.halos["N"]>=N_min) & (cat.halos["N"]<=N_max)]

        masses = cat["N"].data * MHsun
        pos = cat["x_com"].data
        vel = cat["v_com"].data
    else:
        slabs = os.listdir(snapdir)
        masses = np.array([])
        pos    = np.array([])
        vel    = np.array([])

        # slab is eg halo_info_003.asdf
        for slab in slabs:
            cat = CompaSOHaloCatalog(snapdir+ "/" + slab, cleaned = False, fields = ["N", "x_com","v_com"])
            MHsun = cat.header["ParticleMassHMsun"]
            N_min = int(m_min/MHsun)
            N_max = int(m_max/MHsun)
            cat = cat.halos[(cat.halos["N"]>=N_min) & (cat.halos["N"]<=N_max)]

            masses = np.concatenate((masses,cat["N"].data * MHsun))
            pos = np.concatenate((pos,cat["x_com"].data))
            vel = np.concatenate((vel,cat["v_com"].data))

    #assert z == cat.header["Redshift"]
    return np.log10(masses*1e10), pos, vel*(1.0 + z)

if __name__ == "__main__":

    # Number of threads for abacus API
    Nth = int(sys.argv[1])
    abacusnbody.data.asdf.set_nthreads(Nth)

    m_min = 1e11
    m_max = 1e15
    
    in_dir = sys.argv[2]
    my_z = float(sys.argv[3])
    out_dir = sys.argv[4]
    allslabs = sys.argv[5]

    massh, posh, velh = halos_to_cmass(in_dir, my_z, m_min, m_max, all_at_once = allslabs)
    np.save(os.path.join(out_dir, 'halo_pos.npy'), posh)  # halo positions [Mpc/h]
    np.save(os.path.join(out_dir, 'halo_vel.npy'), velh)  # halo velocities [km/s]
    np.save(os.path.join(out_dir, 'halo_mass.npy'), massh)  # halo masses [Msun/h]
