import numpy as np
import os

old_dir = '/anvil/scratch/x-mho1/cmass-ili/quijote/nbody_nonoise/models/galaxy'
new_dir = '/anvil/scratch/x-dbartlett/cmass/quijote/nbody_nonoise_appended/galaxy'
base_summary = 'nbar+zPk0'
seed = 12345

# Set random seed for reproducibility
np.random.seed(seed)

os.makedirs(new_dir, exist_ok=True)

# Find the available appended simulations
appended_sims = os.listdir(old_dir)
appended_sims = [sim for sim in appended_sims if sim.startswith(base_summary) and sim != base_summary]

# Sort these for reproducibility
appended_sims = sorted(appended_sims)

# Get the kmin-kmax dir
kmin_kmax_dir = os.listdir(os.path.join(old_dir, base_summary))
assert len(kmin_kmax_dir) == 1, "There should be exactly one kmin-kmax directory."
kmin_kmax_dir = kmin_kmax_dir[0]
print(f"Using kmin-kmax directory: {kmin_kmax_dir}")

# Get the original summaires from the base summary
dirname = os.path.join(old_dir, base_summary, kmin_kmax_dir)
x_train_orig = np.load(os.path.join(dirname, 'x_train.npy'))
x_val_orig = np.load(os.path.join(dirname, 'x_val.npy'))
x_test_orig = np.load(os.path.join(dirname, 'x_test.npy'))

copy_fnames = ['config.yaml', 'theta_train.npy', 'theta_val.npy', 'theta_test.npy', 'ids_train.npy', 'ids_val.npy', 'ids_test.npy']

# Loop over each appended simulation and create new datasets
for sim in appended_sims:
    print(f"Processing appended simulation: {sim}")
    dirname_appended = os.path.join(old_dir, sim, kmin_kmax_dir)
    
    x_train_shape = np.load(os.path.join(dirname_appended, 'x_train.npy')).shape
    x_val_shape = np.load(os.path.join(dirname_appended, 'x_val.npy')).shape
    x_test_shape = np.load(os.path.join(dirname_appended, 'x_test.npy')).shape
    
    # Create new datasets
    x_train_new = np.zeros(x_train_shape)
    x_val_new = np.zeros(x_val_shape)
    x_test_new = np.zeros(x_test_shape)

    # First enrties are the base summaries
    x_train_new[:, :x_train_orig.shape[1]] = x_train_orig
    x_val_new[:, :x_val_orig.shape[1]] = x_val_orig
    x_test_new[:, :x_test_orig.shape[1]] = x_test_orig

    # Remaining entries are noise
    x_train_new[:, x_train_orig.shape[1]:] = np.random.normal(0, 1, size=(x_train_shape[0], x_train_shape[1] - x_train_orig.shape[1]))
    x_val_new[:, x_val_orig.shape[1]:] = np.random.normal(0, 1, size=(x_val_shape[0], x_val_shape[1] - x_val_orig.shape[1]))
    x_test_new[:, x_test_orig.shape[1]:] = np.random.normal(0, 1, size=(x_test_shape[0], x_test_shape[1] - x_test_orig.shape[1]))

    # Save the new datasets
    new_sim_dir = os.path.join(new_dir, sim, kmin_kmax_dir)
    os.makedirs(new_sim_dir, exist_ok=True)
    np.save(os.path.join(new_sim_dir, 'x_train.npy'), x_train_new)
    np.save(os.path.join(new_sim_dir, 'x_val.npy'), x_val_new)
    np.save(os.path.join(new_sim_dir, 'x_test.npy'), x_test_new)

    # Copy over other relevant files
    for filename in copy_fnames:
        src_file = os.path.join(dirname_appended, filename)
        dst_file = os.path.join(new_sim_dir, filename)
        assert os.path.exists(src_file), f"File {src_file} does not exist."
        os.system(f'cp {src_file} {dst_file}')


# Copy over the base summary as well
print(f"Processing appended simulation: {base_summary}")
dirname_base = os.path.join(old_dir, base_summary, kmin_kmax_dir)
new_base_dir = os.path.join(new_dir, base_summary, kmin_kmax_dir)
copy_fnames += ['x_train.npy', 'x_val.npy', 'x_test.npy']
os.makedirs(new_base_dir, exist_ok=True)
for filename in copy_fnames:
    src_file = os.path.join(dirname_base, filename)
    dst_file = os.path.join(new_base_dir, filename)
    assert os.path.exists(src_file), f"File {src_file} does not exist."
    os.system(f'cp {src_file} {dst_file}')