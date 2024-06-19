"""
This script reads the quijote snapshot and produces DM density fields, using pylians.
"""

import numpy as np
import MAS_library as MASL

root_in = '/home/mattho/data/quijote/Snapshots/latin_hypercube_HR'
root_out = '/home/mattho/data/quijote/density_field/latin_hypercube_HR'
ptypes = [1]
grids = [256, 512]  # [128, 64, 32, 16, 8, 4]
BoxSize = 1000.0  # Mpc/h ; size of box
# snapnum, z = 3, 0.5  # for z=0.5
snapnum, z = 4, 0  # for z=0.0
sim_LH_nums = [0]  # , 1, 10, 100]

for grid in grids:
    for sim_LH_num in sim_LH_nums:
        snapshot = f'{root_in}/{sim_LH_num}/snapdir_{snapnum:03d}/snap_{snapnum:03d}'
        print(f'lhid: {sim_LH_num}, grid: {grid}, snapshot: {snapshot}')

        df_cic = MASL.density_field_gadget(snapshot, ptypes, grid, MAS='CIC',
                                           do_RSD=False, axis=0, verbose=False)
        df_pylians_cic = df_cic/np.mean(df_cic, dtype=np.float64)-1.0

        out_file = f'{root_out}/{sim_LH_num}/dfmatt_m_{grid}_z={z}.npy'
        np.save(out_file, df_pylians_cic)
