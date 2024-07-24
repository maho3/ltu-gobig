"""This script converts old .npy files to .h5 files, in the convention
established in the merge of the enforce_hdf5 branch.
"""

import shutil
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


oldfile = join(simpath, 'rho.npy')
newfile = join(simpath, 'nbody.h5')
if (not isfile(newfile)) and isfile(oldfile):
    print('Converting nbody')
    convert_nbody()
else:
    print('nbody already converted')


# convert bias models
def convert_bias():
    from cmass.bias.fit_halo_bias import save_bias

    if isfile(join(simpath, 'halo_bias.npy')):
        medges = np.load(join(simpath, 'halo_medges.npy'))
        popt = np.load(join(simpath, 'halo_bias.npy'))
        save_bias(simpath, cfg.nbody.af, medges, popt)

        if del_old:
            print('Deleting old bias')
            os.remove(join(simpath, 'halo_medges.npy'))
            os.remove(join(simpath,  'halo_bias.npy'))


oldfile = join(simpath, 'halo_bias.npy')
newfile = join(simpath, 'bias.h5')
if (not isfile(newfile)) and isfile(oldfile):
    print('Converting bias')
    convert_bias()
else:
    print('bias already converted')


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


oldfile = join(simpath, 'halo_pos.npy')
newfile = join(simpath, 'halos.h5')
if (not isfile(newfile)) and isfile(oldfile):
    print('Converting halos')
    convert_halos()
else:
    print('halos already converted')


# convert galaxies
def convert_galaxies(i):
    from cmass.bias.apply_hod import save_snapshot
    if isfile(join(simpath, 'hod', f'hod{i}_pos.npy')):
        hpos = np.load(join(simpath, 'hod', f'hod{i}_pos.npy'))
        hvel = np.load(join(simpath, 'hod', f'hod{i}_vel.npy'))
        if isfile(join(simpath, 'hod', f'hod{i}_meta.npz')):
            hmeta = np.load(
                join(simpath, 'hod', f'hod{i}_meta.npz'), allow_pickle=True)
        else:
            hmeta = {}

        os.makedirs(join(simpath, 'galaxies'), exist_ok=True)
        savepath = join(simpath, 'galaxies', f'hod{i:03}.h5')
        save_snapshot(savepath, cfg.nbody.af, hpos, hvel, **hmeta)

        if del_old:
            print(f'Deleting old galaxies {i}')
            os.remove(join(simpath, 'hod', f'hod{i}_pos.npy'))
            os.remove(join(simpath, 'hod', f'hod{i}_vel.npy'))
            if isfile(join(simpath, 'hod', f'hod{i}_meta.npz')):
                os.remove(join(simpath, 'hod', f'hod{i}_meta.npz'))


for i in range(10):
    oldfile = join(simpath, 'hod', f'hod{i}_pos.npy')
    newfile = join(simpath, 'galaxies', f'hod{i:03}.h5')
    if (not isfile(newfile)) and isfile(oldfile):
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


for i in range(10):
    oldfile = join(simpath, 'obs', f'rdz{i}.npy')
    newfile = join(simpath, 'lightcone', f'hod{i:03}_aug{0:03}.h5')
    if (not isfile(newfile)) and isfile(oldfile):
        print(f'Converting lightcone {i}')
        convert_lightcone(i)

# remove filtered and all else
if del_old and os.path.isdir(join(simpath, 'obs')):
    print('Deleting old obs')
    os.rmdir(join(simpath, 'obs'))
    # shutil.rmtree(join(simpath, 'obs'))


# convert power spectrum
def convert_pk(i):
    from cmass.summary.tools import save_summary
    if isfile(join(simpath, 'Pk', f'Pk{i}.npz')):
        pk = np.load(join(simpath, 'Pk', f'Pk{i}.npz'))
        k_gal = pk['k_gal']
        p0k_gal = pk['p0k_gal']
        p2k_gal = pk['p2k_gal']
        p4k_gal = pk['p4k_gal']

        os.makedirs(join(simpath, 'summary'), exist_ok=True)
        outname = f'hod{i:03}_aug{0:03}.h5'
        outpath = join(simpath, 'summary', outname)
        save_summary(
            outpath, 'Pk',
            k=k_gal, p0k=p0k_gal,
            p2k=p2k_gal, p4k=p4k_gal)

        if del_old:
            print(f'Deleting old summary {i}')
            os.remove(join(simpath, 'Pk', f'Pk{i}.npz'))


for i in range(10):
    oldfile = join(simpath, 'Pk', f'Pk{i}.npz')
    newfile = join(simpath, 'summary', f'hod{i:03}_aug{0:03}.h5')
    if (not isfile(newfile)) and isfile(oldfile):
        print(f'Converting summary {i}')
        convert_pk(i)

if del_old and os.path.isdir(join(simpath, 'Pk')):
    print('Deleting old Pk')
    os.rmdir(join(simpath, 'Pk'))
    # shutil.rmtree(join(simpath, 'Pk'))
