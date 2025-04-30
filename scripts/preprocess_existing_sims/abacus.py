import numpy as np
import os
import sys
from tqdm import tqdm
from os.path import join
import abacusnbody.data.asdf
from abacusnbody.data.compaso_halo_catalog import CompaSOHaloCatalog
from cmass.bias.rho_to_halo import save_snapshot


def halos_to_cmass(rootdir, z, m_min, m_max, all_at_once=True):
    '''
    doc
    '''
    z_dict = {0.5: "z0.500"}

    # snapdir should have a subfolder such that we have the structure "...snapdir/halo_info/halo_info*.asdf"
    snapdir = join(rootdir, 'halos', z_dict[z], 'halo_info')

    if all_at_once:
        raise NotImplementedError
        cat = CompaSOHaloCatalog(snapdir, cleaned=True, fields=[
                                 "N", "x_com", "v_com"])
        MHsun = cat.header["ParticleMassHMsun"]
        print(MHsun)
        N_min = int(m_min/MHsun)
        print(N_min)
        N_max = int(m_max/MHsun)
        print(N_max)
        cat = cat.halos[(cat.halos["N"] >= N_min) & (cat.halos["N"] <= N_max)]

        masses = cat["N"].data * MHsun
        pos = cat["x_com"].data
        vel = cat["v_com"].data
    else:
        slabs = sorted(os.listdir(snapdir))
        masses, pos, vel = [], [], []

        # slab is eg halo_info_003.asdf
        for i, slab in enumerate(slabs):
            if 'checksums' in slab:
                continue
            filename = join(snapdir, slab)
            print(f"Processing slab {i+1}/{len(slabs)}: {filename}")

            cat = CompaSOHaloCatalog(
                filename, cleaned=True,
                fields=["N", "x_com", "v_com"])
            MHsun = cat.header["ParticleMassHMsun"]
            # print(MHsun)
            N_min = int(m_min/MHsun)
            N_max = int(m_max/MHsun)
            cat = cat.halos[(cat.halos["N"] >= N_min) &
                            (cat.halos["N"] <= N_max)]

            masses.append(cat["N"].data * MHsun)
            pos.append(cat["x_com"].data)
            vel.append(cat["v_com"].data)

        masses = np.concatenate(masses, axis=0)
        pos = np.concatenate(pos, axis=0)
        vel = np.concatenate(vel, axis=0)

        pos += 1000   # to avoid negative positions
        pos %= 2000  # periodicity
        #     masses = np.concatenate((masses, cat["N"].data * MHsun), axis=0)
        #     pos = np.concatenate((pos, cat["x_com"].data), axis=0)
        #     vel = np.concatenate((vel, cat["v_com"].data), axis=0)

    # assert z == cat.header["Redshift"]
    return np.log10(masses), pos, vel  # *(1.0 + z)


if __name__ == "__main__":

    print(sys.argv)

    # Number of threads for abacus API
    Nth = int(sys.argv[1])
    abacusnbody.data.asdf.set_nthreads(Nth)

    m_min = 5e12  # Charm minimum mass threshold
    m_max = 1e17

    in_dir = sys.argv[2]
    my_z = float(sys.argv[3])
    out_dir = sys.argv[4]
    allslabs = int(sys.argv[5])

    massh, posh, velh = halos_to_cmass(
        in_dir, my_z, m_min, m_max, all_at_once=allslabs)

    a = 1.0/(1.0 + my_z)
    if os.path.isfile(join(out_dir, 'halos.h5')):
        os.remove(join(out_dir, 'halos.h5'))
    save_snapshot(out_dir, a, posh, velh, massh)
    # np.save(os.path.join(out_dir, 'halo_pos.npy'),
    #         posh)  # halo comoving positions [Mpc/h]
    # np.save(os.path.join(out_dir, 'halo_vel.npy'),
    #         velh)  # halo physical velocities [km/s]
    # np.save(os.path.join(out_dir, 'halo_mass.npy'),
    #         massh)  # halo masses [Msun/h]
