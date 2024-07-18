"""This script converts old .npy files to .h5 files, in the convention
established in the merge of the enforce_hdf5 branch.
"""

import os
from os.path import join, isfile
import numpy as np
from omegaconf import OmegaConf
import argparse

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--suite', type=str)
parser.add_argument('--lhid', type=int)
parser.add_argument('--del_old', action='store_true')
args = parser.parse_args()
# '/automnt/data80/mattho/cmass-ili/sz_shivam/borgpm/L3000-N384'
suitepath = args.suite
lhid = args.lhid
lhid = str(lhid)
simpath = join(suitepath, lhid)
del_old = args.del_old

print(suitepath, lhid, del_old)

# load config
cfg = OmegaConf.load(join(simpath, 'config.yaml'))
print(OmegaConf.to_yaml(cfg))


# convert nbody
def convert_nbody():
    from cmass.nbody.tools import save_nbody, save_transfer

    rho = np.load(join(simpath, 'rho.npy'))
    fvel = np.load(join(simpath, 'fvel.npy'))
    if isfile(join(simpath, 'ppos.npy')):
        ppos = np.load(join(simpath, 'ppos.npy'))
        pvel = np.load(join(simpath, 'pvel.npy'))
    else:
        ppos, pvel = None, None
    save_nbody(simpath, cfg.nbody.af, rho, fvel, ppos, pvel)

    if del_old:
        print('Deleting old nbody')
        os.remove(join(simpath, 'rho.npy'))
        os.remove(join(simpath, 'fvel.npy'))
        if isfile(join(simpath, 'ppos.npy')):
            os.remove(join(simpath, 'ppos.npy'))
            os.remove(join(simpath, 'pvel.npy'))

    if isfile(join(simpath, 'rho_transfer.npy')):
        filename = join(simpath, 'rho_transfer.npy')
    elif isfile(join(simpath, 'rho_z50.npy')):
        filename = join(simpath, 'rho_z50.npy')
    else:
        return

    rho_transfer = np.load(filename)
    save_transfer(simpath, rho_transfer)

    if del_old:
        print('Deleting old transfer')
        os.remove(filename)


if not isfile(join(simpath, 'nbody.h5')):
    print('Converting nbody')
    convert_nbody()


# convert halos
def convert_halos():
    from cmass.bias.rho_to_halo import save_snapshot

    hpos = np.load(join(simpath, 'halo_pos.npy'))
    hvel = np.load(join(simpath, 'halo_vel.npy'))
    hmass = np.load(join(simpath, 'halo_mass.npy'))

    save_snapshot(simpath, cfg.nbody.af, hpos, hvel, hmass)

    if del_old:
        print('Deleting old halos')
        os.remove(join(simpath, 'halo_pos.npy'))
        os.remove(join(simpath, 'halo_vel.npy'))
        os.remove(join(simpath, 'halo_mass.npy'))
        if isfile(join(simpath, 'halo_cuboid_pos.npy')):
            os.remove(join(simpath, 'halo_cuboid_pos.npy'))
            os.remove(join(simpath, 'halo_cuboid_vel.npy'))


if not isfile(join(simpath, 'halos.h5')):
    print('Converting halos')
    convert_halos()


# convert galaxies
def convert_galaxies(i):
    from cmass.bias.apply_hod import save_snapshot
    if isfile(join(simpath, 'hod', f'hod{i}_pos.npy')):
        hpos = np.load(join(simpath, 'hod', f'hod{i}_pos.npy'))
        hvel = np.load(join(simpath, 'hod', f'hod{i}_vel.npy'))
        hmeta = np.load(
            join(simpath, 'hod', f'hod{i}_meta.npz'), allow_pickle=True)

        os.makedirs(join(simpath, 'galaxies'), exist_ok=True)
        savepath = join(simpath, 'galaxies', f'hod{i:03}.h5')
        save_snapshot(savepath, cfg.nbody.af, hpos, hvel, **hmeta)

        if del_old:
            print(f'Deleting old galaxies {i}')
            os.remove(join(simpath, 'hod', f'hod{i}_pos.npy'))
            os.remove(join(simpath, 'hod', f'hod{i}_vel.npy'))
            os.remove(join(simpath, 'hod', f'hod{i}_meta.npz'))


for i in range(5):
    print(f'Converting galaxies {i}')
    convert_galaxies(i)
if del_old and os.path.isdir(join(simpath, 'hod')):
    os.rmdir(join(simpath, 'hod'))


# convert lightcone
def convert_lightcone(i):
    from cmass.survey.tools import save_lightcone
    if isfile(join(simpath, 'obs', f'rdz{i}.npy')):
        rdz = np.load(join(simpath, 'obs', f'rdz{i}.npy'))
        os.makedirs(join(simpath, 'lightcone'), exist_ok=True)
        save_lightcone(
            join(simpath, 'lightcone'),
            ra=rdz[:, 0], dec=rdz[:, 1], z=rdz[:, 2], hod_seed=i)

        if del_old:
            print(f'Deleting old lightcone {i}')
            os.remove(join(simpath, 'obs', f'rdz{i}.npy'))


for i in range(5):
    print(f'Converting lightcone {i}')
    convert_lightcone(i)
if del_old and os.path.isdir(join(simpath, 'obs')):
    os.rmdir(join(simpath, 'obs'))
