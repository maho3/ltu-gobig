import os
from tools import load_posterior
import numpy as np
import torch
import zuko
from tqdm import tqdm
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader, TensorDataset
import csv
from copy import deepcopy

from tools import torch_device
device = torch_device()


def get_posterior_runner(nbody='quijotelike', sim='fastpm_varnoise', tracer='simbig_lightcone', summaries=['nbar', 'Pk0', 'Pk2', 'Pk4'],
                kmin=0.0, kmax=0.4):
    
    wdir = '/anvil/scratch/x-mho1/cmass-ili'

    cosmonames = [r'$\Omega_m$', r'$\Omega_b$', r'$h$', r'$n_s$', r'$\sigma_8$']
    noisenames = [r'$\sigma_{\rm radial}$', r'$\sigma_{\rm tangential}$',]
    names = cosmonames + noisenames

    # Specify model configuration
    save_dir = os.path.join(wdir, nbody, sim, 'models')

    # Specify data dtype
    tracer = 'simbig_lightcone'
    summary = '+'.join(summaries)
    modelpath = os.path.join(save_dir, tracer, summary, f'kmin-{kmin}_kmax-{kmax}')
    print(
        f'Loading model: nbody={nbody}, sim={sim}, tracer={tracer}, \n\tsummary={summary}, kmin={kmin}, kmax={kmax}')
    print(modelpath)

    posterior = load_posterior(modelpath)

    xtest = np.load(os.path.join(modelpath, 'x_test.npy'))
    ytest = np.load(os.path.join(modelpath, 'theta_test.npy'))

    name_dict = {
        r'$\Omega_m$':'Omega_m', 
        r'$\Omega_b$':'Omega_b', 
        r'$h$':'h', 
        r'$n_s$':'n_s', 
        r'$\sigma_8$':'sigma_8',
        r'$\alpha$':'alpha', 
        r'$\log M_0$':'logM0', 
        r'$\log M_1$':'logM1', 
        r'$\log M_{\min}$':'logMmin', 
        r'$\sigma_{\log M}$':'sigma_logM',
        r'$\sigma_{\rm radial}$':'sigma_radial', 
        r'$\sigma_{\rm tangential}$':'sigma_tangential',
    }
    par_names = [name_dict[n] for n in names]
    
    return modelpath, posterior, xtest, ytest, par_names


def load_prior(modelpath):

    # Store uniform parameter details
    uniform_priors = {
        'Omega_m': [0.1, 0.5],
        'Omega_b': [0.03, 0.07],
        'h': [0.5, 0.9],
        'n_s': [0.8, 1.2],
        'sigma_8': [0.6, 1.0]
    }

    with open(os.path.join(modelpath,'hodprior.csv'), newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[1].strip() == 'uniform':
                name = row[0].strip()
                min_val = float(row[2])
                max_val = float(row[3])
                uniform_priors[name] = [min_val, max_val]
    
    return uniform_priors


def get_posterior_samples(posterior, uniform_priors, x0, par_names, nsamp=2000):
    
    samp0 = posterior.sample(x=x0, shape=(nsamp,))

    # Check uniform priors
    for n, v in uniform_priors.items():
        if n in par_names:
            i = par_names.index(n)
            prior_mask = (samp0[:,i] >= v[0]) & (samp0[:,i] <= v[1])
            samp0 = samp0[prior_mask]
    print('Number of remaining samples:', samp0.shape[0])
    
    return samp0


def approximate_posterior(samp0, par_names, transforms=3, hidden_features=(64, 64), train_frac=0.8, lr=1e-3, nepoch=500,
                         patience=50, min_delta=1e-4, scheduler_patience=20, scheduler_factor=0.5, min_lr=1e-6):
    
    best_val_loss = float('inf')
    best_model_state = None
    epochs_no_improve = 0

    # Neural spline flow (NSF)
    con_flow = zuko.flows.NSF(samp0.shape[1] - 2, 2, transforms=transforms, hidden_features=hidden_features)

    # Train to maximize the log-likelihood
    optimizer = torch.optim.Adam(con_flow.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=scheduler_patience, factor=scheduler_factor,min_lr=min_lr,)

    m = np.array([p in ['sigma_radial', 'sigma_tangential'] for p in par_names], dtype=bool)
    X_train = samp0[:int(train_frac * samp0.shape[0]), ~m]
    C_train = samp0[:int(train_frac * samp0.shape[0]), m]
    X_val = samp0[int(train_frac * samp0.shape[0]):, ~m]
    C_val = samp0[int(train_frac * samp0.shape[0]):, m]

    # Build datasets
    train_dataset = TensorDataset(X_train, C_train)
    val_dataset = TensorDataset(X_val, C_val)

    # DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=256, shuffle=False)
    val_loader = DataLoader(val_dataset, batch_size=1024)

    all_train_loss = []
    all_val_loss = []

    for epoch in tqdm(range(nepoch)):
        con_flow.train()
        for x, c in train_loader:
            loss = -con_flow(c).log_prob(x.unsqueeze(0)).mean()
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
        all_train_loss.append(loss.detach().numpy())

        # Validation evaluation
        con_flow.eval()
        with torch.no_grad():
            val_loss = 0.0
            count = 0
            for x, c in val_loader:
                val_loss += -con_flow(c).log_prob(x.unsqueeze(0)).sum().item()
                count += x.size(0)
            val_loss /= count
        all_val_loss.append(val_loss)

        scheduler.step(val_loss)

        # Early stopping check
        if best_val_loss - val_loss > min_delta:
            best_val_loss = val_loss
            best_model_state = deepcopy(con_flow.state_dict())
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping at epoch {epoch}")
                break

    # Load best model
    if best_model_state is not None:
        print('Loading state')
        con_flow.load_state_dict(best_model_state)

    plt.plot(all_train_loss, label='Training')
    plt.plot(all_val_loss, label='Validation')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.tight_layout()
    plt.savefig('train_loss.png')
    plt.clf()
    plt.close(plt.gcf())
    
    return con_flow


def save_samples(ind, savepath, modelpath, con_flow, x0, y0, par_names, nsamp=5000):
    
    m = np.array([p in ['sigma_radial', 'sigma_tangential'] for p in par_names], dtype=bool)
    c = torch.Tensor(y0[m])
    samp = con_flow(c).sample((nsamp,))
    
    parts = os.path.normpath(modelpath).split(os.sep)
    outname = os.path.join(savepath, parts[-2], parts[-1])
    if not os.path.isdir(outname):
        os.makedirs(outname)
    outname = os.path.join(outname, f'samples_{ind}.npy')
    np.save(outname, samp)
    
    return


def main():
    
    ind = 0
    
    savepath = '.'
    modelpath, posterior, xtest, ytest, par_names = get_posterior_runner()
    x0 = torch.Tensor(xtest[ind]).to(device)
    y0 = ytest[ind]
    uniform_priors = load_prior(modelpath)
    samp0 = get_posterior_samples(posterior, uniform_priors, x0, par_names, nsamp=2000)
    con_flow = approximate_posterior(samp0, par_names)
    save_samples(ind, savepath, modelpath, con_flow, x0, y0, par_names)
                          
    return


if __name__ == "__main__":
    main()
    