import os
import glob
from tqdm import tqdm


def rename_file(filepath, dryrun=True):
    # Extract the directory, base name, and extension
    dirpath, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)

    parts = name.split('_')
    prefix = [x[:3] for x in parts]
    nums = [int(x[3:]) for x in parts]
    parts = [f"{p}{n:05d}" for p, n in zip(prefix, nums)]
    parts = '_'.join(parts) + ext

    new_filepath = os.path.join(dirpath, parts)

    if dryrun:
        # Print what would happen
        print(f"Dry Run: Would rename {filepath} -> {new_filepath}")
    else:
        # Rename the file
        os.rename(filepath, new_filepath)


def rename_hod_files(root_dir, dryrun=True):
    # Use glob to find all the matching files recursively
    filepaths = glob.glob(os.path.join(
        root_dir, '**', 'hod*.h5'), recursive=True)

    # Use multiprocessing Pool to process files in parallel
    for filepath in filepaths:
        rename_file(filepath, dryrun=dryrun)


if __name__ == "__main__":
    suite = 'quijotelike'
    wdir = f'/automnt/data80/mattho/cmass-ili/{suite}'
    dryrun = False

    for sim in os.listdir(wdir):
        simdir = os.path.join(wdir, sim)
        cfgdir = os.path.join(simdir, os.listdir(simdir)[0])

        root_directory = cfgdir
        # Prompt user for confirmation
        user_input = input(f"Rename files in {root_directory}? (y/n): ")

        if user_input.lower() != "y":
            print("Skipping...")
            continue
        print(f"Renaming files in {root_directory}")
        for lhid in tqdm(os.listdir(root_directory)):
            root_dir = os.path.join(root_directory, str(lhid))
            # Set dryrun=True to only print the actions, False to actually rename
            rename_hod_files(root_dir, dryrun=dryrun)
