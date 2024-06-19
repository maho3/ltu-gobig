"""
This script makes CIC fields from the quijote Snapshots using pylians' readgadget functions.

It follows the quijote convention of making the corner cell centered at (0,0,0). As a result, the density mesh is offset by half a voxel length over the periodic boundary.

Author: Simon Ding (@AsianTaco)
"""

import readgadget
from jax import numpy as jnp

from jax.config import config

config.update("jax_enable_x64", True)

def cic(coords, boxsize, Ngrid, ndim):
    # Create a new grid which will contain the densities
    grid = jnp.zeros(Ngrid ** ndim, dtype=jnp.float32)

    # Bin coords into their cells and find distance to cell centre.
    x_c = jnp.floor(coords[:, 0] * Ngrid / boxsize).astype(int)
    y_c = jnp.floor(coords[:, 1] * Ngrid / boxsize).astype(int)
    z_c = jnp.floor(coords[:, 2] * Ngrid / boxsize).astype(int)

    # Distance to center of cell
    d_x = coords[:, 0] * Ngrid / boxsize - (x_c + 0.5)
    d_y = coords[:, 1] * Ngrid / boxsize - (y_c + 0.5)
    d_z = coords[:, 2] * Ngrid / boxsize - (z_c + 0.5)

    # Which side of the center is this particle on
    inc_x = jnp.where(d_x < 0, -1, 1)
    inc_y = jnp.where(d_y < 0, -1, 1)
    inc_z = jnp.where(d_z < 0, -1, 1)

    # Work with absolute values.
    d_x = jnp.abs(d_x).astype(jnp.float64)
    d_y = jnp.abs(d_y).astype(jnp.float64)
    d_z = jnp.abs(d_z).astype(jnp.float64)

    t_x = 1. - d_x
    t_y = 1. - d_y
    t_z = 1. - d_z

    assert t_x.dtype == 'float64'
    assert t_y.dtype == 'float64'
    assert t_z.dtype == 'float64'

    # Add contributions to 8 cells
    idx = get_index(x_c, y_c, z_c, Ngrid)
    grid += jnp.bincount(idx, minlength=Ngrid ** ndim, weights=t_x * t_y * t_z)

    idx = get_index(x_c + inc_x, y_c, z_c, Ngrid)
    grid += jnp.bincount(idx, minlength=Ngrid ** ndim, weights=d_x * t_y * t_z)

    idx = get_index(x_c, y_c + inc_y, z_c, Ngrid)
    grid += jnp.bincount(idx, minlength=Ngrid ** ndim, weights=t_x * d_y * t_z)

    idx = get_index(x_c, y_c, z_c + inc_z, Ngrid)
    grid += jnp.bincount(idx, minlength=Ngrid ** ndim, weights=t_x * t_y * d_z)

    idx = get_index(x_c + inc_x, y_c + inc_y, z_c, Ngrid)
    grid += jnp.bincount(idx, minlength=Ngrid ** ndim, weights=d_x * d_y * t_z)

    idx = get_index(x_c, y_c + inc_y, z_c + inc_z, Ngrid)
    grid += jnp.bincount(idx, minlength=Ngrid ** ndim, weights=t_x * d_y * d_z)

    idx = get_index(x_c + inc_x, y_c, z_c + inc_z, Ngrid)
    grid += jnp.bincount(idx, minlength=Ngrid ** ndim, weights=d_x * t_y * d_z)

    idx = get_index(x_c + inc_x, y_c + inc_y, z_c + inc_z, Ngrid)
    grid += jnp.bincount(idx, minlength=Ngrid ** ndim, weights=d_x * d_y * d_z)
    return grid.reshape(Ngrid, Ngrid, Ngrid, order='F')

box_size = 1000
mesh_sizes = [64, 128]
base_path = '/data80/sding/quijote'
for seed_i in range(100):
    print(f'processing seed {seed_i}')
    snapshot = f'{base_path}/{seed_i}/snapdir_004/snap_004'
    pos = readgadget.read_block(snapshot, "POS ", ptype=[1])/1e3 #position in Mpc/h
    for mesh_size in mesh_sizes:
         rho = cic(pos, boxsize=box_size, Ngrid=mesh_size, ndim=3)
         overdensity = rho / rho.mean() - 1
         jnp.save(f"{base_path}/{seed_i}/cic_{mesh_size}", overdensity)
 
