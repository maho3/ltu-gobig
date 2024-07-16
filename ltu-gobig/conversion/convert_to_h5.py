"""This script converts old .npy files to .h5 files, in the convention
established in the merge of the enforce_hdf5 branch.
"""

import os
from os.path import join
import numpy as np
import h5py
from omegaconf import OmegaConf

suitepath = '/automnt/data80/mattho/cmass-ili/sz_shivam/borgpm/L3000-N384'
lhid = 6
lhid = str(lhid)
simpath = join(suitepath, lhid)
del_old = False

# load config
cfg = OmegaConf.load(join(simpath, 'config.yaml'))

# convert nbody


def convert_nbody():
    from cmass.nbody.tools import save_nbody

    rho = np.load(join(simpath, 'rho.npy'))
    fvel = np.load(join(simpath, 'fvel.npy'))
    if os.path.isfile(join(simpath, 'ppos.npy')):
        ppos = np.load(join(simpath, 'ppos.npy'))
        pvel = np.load(join(simpath, 'pvel.npy'))
    else:
        ppos, pvel = None, None
    save_nbody(simpath, rho, fvel, ppos, pvel)


if os.path.

# convert halos

# convert galaxies

# convert lightcone
