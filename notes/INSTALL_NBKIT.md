### Installing nbodykit
We use the [`nbodykit`](https://github.com/bccp/nbodykit) package to apply survey masks and calculate some summary statistics. If you don't want to use these features, you can skip this section.

Installing `nbodykit` is quite tricky. It requires that you have a working C compiler and MPI backend which are compatible with `cython` and `mpi4py`. Below are example instructions for installing `nbodykit` on Infinity and Rusty. 

#### Infinity@IAP
On the Infinity cluster at IAP, you can install nbodykit and its dependencies as:
```bash
# load the C-compiler and MPI modules
module load gcc/13.2.0 openmpi/4.1.2-intel

# clone nbodykit
git clone https://github.com/bccp/nbodykit.git
cd nbodykit

# install nbodykit dependencies
pip install --no-cache-dir  numpy==1.24.4 cython==0.29.33 mpi4py
pip install -r requirements.txt
pip install -r requirements-extras.txt

# install nbodykit itself
pip install -e .

# return to the parent directory
cd ..
```

#### Rusty@Flatiron
On Flatiron/Rusty, the correct versions of nbodykit and mpi4py are already installed. You can load them as follows:
```bash
module load python
module load openmpi
module load python-mpi
module load gcc/13.2.0
python -m venv --system-site-packages $VENVDIR/venv-name  # make your virtual env, and it has nbodykit and mpi4
```

#### Narval@computecanada
On Narval, you can install nbodykit and its dependencies as:
```bash
module load gcc
module load openmpi
git clone https://github.com/bccp/nbodykit.git
cd nbodykit
pip install --no-cache-dir  numpy==1.24.4 cython==0.29.33
module load mpi4py
module load gsl
pip install -r requirements.txt
pip install -r requirements-extras.txt
pip install -e .
```

#### Other machines
Currently, there is not a known convenient installation of `nbodykit` on Mac machines. If you manage to install `nbodykit` on a different machine, please let us know so we can add instructions here.

