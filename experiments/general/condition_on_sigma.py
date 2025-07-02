import os
from tools import load_posterior
import numpy as np
import torch
import zuko
from tqdm import tqdm
from torch.utils.data import DataLoader, TensorDataset
import csv
from copy import deepcopy
import argparse
import time
import yaml
import logging

from tools import torch_device
device = torch_device()

from cmass.infer.loaders import (
    preprocess_Pk, preprocess_Bk, _construct_hod_prior,
    _load_single_simulation_summaries, _get_log10nbar)
from cmass.infer.preprocess import aggregate #load_summaries

def load_summaries(suitepath, tracer, simpaths, a=None,
                   include_hod=False, include_noise=False):
    if tracer not in ['halo', 'galaxy', 'ngc_lightcone', 'sgc_lightcone',
                      'mtng_lightcone', 'simbig_lightcone']:
        raise ValueError(f'Unknown tracer: {tracer}')

    logging.info(f'Looking for {tracer} summaries at {suitepath}')

    # load summaries
    summlist, paramlist, idlist = [], [], []
    for lhid in tqdm(simpaths):
        sourcepath = os.path.join(suitepath, lhid)
        summs, params = _load_single_simulation_summaries(
            sourcepath, tracer, a=a,
            include_hod=include_hod, include_noise=include_noise)
        summlist += summs
        paramlist += params
        idlist += [lhid] * len(summs)

    # get parameter names
    hodprior = None
    if (tracer != 'halo') & include_hod:  # add HOD params
        example_config_file = os.path.join(suitepath, simpaths[0], 'config.yaml')
        hodprior = _construct_hod_prior(example_config_file)

    # aggregate summaries (merges all summaries into a single dict)
    summaries, parameters, ids = aggregate(summlist, paramlist, idlist)
    for key in summaries:
        logging.info(
            f'Successfully loaded {len(summaries[key])} {key} summaries')
    return summaries, parameters, ids, hodprior


def find_all_summaries(nbody='quijotelike', sim='fastpm_varnoise', tracer='simbig_lightcone'):
    
    wdir = '/anvil/scratch/x-mho1/cmass-ili'
    save_dir = os.path.join(wdir, nbody, sim, 'models', tracer)
    summaries = os.listdir(save_dir)
    summaries.sort()
    
    return summaries


def get_posterior_runner(ind, savepath, nbody='quijotelike', sim='fastpm_varnoise', tracer='simbig_lightcone', 
                         summary='nbar+Pk0+Pk2+Pk4+Qk0', kmin=0.0, kmax=0.4, 
                         test_nbody='quijotelike', test_sim='fastpm_varnoise'):
    
    wdir = '/anvil/scratch/x-mho1/cmass-ili'

    cosmonames = [r'$\Omega_m$', r'$\Omega_b$', r'$h$', r'$n_s$', r'$\sigma_8$']
    noisenames = [r'$\sigma_{\rm radial}$', r'$\sigma_{\rm tangential}$',]
    names = cosmonames + noisenames

    # Specify model configuration
    save_dir = os.path.join(wdir, nbody, sim, 'models')

    # Specify data dtype
    tracer = 'simbig_lightcone'
    modelpath = os.path.join(save_dir, tracer, summary, f'kmin-{kmin}_kmax-{kmax}')
    print(
        f'Loading model: nbody={nbody}, sim={sim}, tracer={tracer}, \n\tsummary={summary}, kmin={kmin}, kmax={kmax}')

    posterior = load_posterior(modelpath)

    # Find indices to test at
    itest = np.load(os.path.join(modelpath, 'ids_test.npy'))
    if test_nbody != nbody or test_sim != sim:
        # Load the test indices from the test modelpath
        test_modelpath = os.path.join(wdir, test_nbody, test_sim, 'models', tracer, summary, f'kmin-{kmin}_kmax-{kmax}')
    else:
        test_modelpath = modelpath

    if os.path.isfile(os.path.join(test_modelpath, 'ids_test.npy')):
        itest_test = np.load(os.path.join(test_modelpath, 'ids_test.npy'))
        # Check if the test indices are the same for the modelpath
        assert np.array_equal(itest, itest_test), "Test indices do not match between model and test paths."
        xtest = np.load(os.path.join(test_modelpath, 'x_test.npy'))
        ytest = np.load(os.path.join(test_modelpath, 'theta_test.npy'))
        x0 = torch.Tensor(xtest[ind]).to(device)
        y0 = ytest[ind]
    else:
        test_modelpath = os.path.join(wdir, test_nbody, test_sim)
        dirs = os.listdir(test_modelpath)
        # See which of dirs are in format L{L}-N{N} then extract L and N
        dirs = [d for d in dirs if d.startswith('L') and 'N' in d]
        L, N = [], []
        for d in dirs:
            L.append(int(d.split('-')[0][1:]))
            N.append(int(d.split('-')[1][1:]))
        assert len(L) == 1 and len(N) == 1, "There should be only one L and N in the directories."
        L, N = L[0], N[0]
        suite_path = os.path.join(test_modelpath, f'L{L}-N{N}')

        # Find information
        isim = itest[ind]
        conf_name = os.path.join(suite_path, str(isim), 'config.yaml')
        with open(conf_name, 'r') as f:
            cfg = yaml.safe_load(f)

        # Find out what this should be
        correct_shot = True

        suite_path = os.path.join(wdir, test_nbody, test_sim, f'L{L}-N{N}')

        summaries, parameters, ids, hodprior = load_summaries(
            suite_path, tracer, [itest[ind]], a=cfg['nbody']['af'],
            include_hod=True,
            include_noise=True)

        exp_summary = summary.split('+')
        xs = []

        for summ in exp_summary:
            # Handle all the different summaries
            if summ == 'nbar':
                continue  # we handle this separately
            eq_bool = "Eq" in summ
            summ = summ.replace("Eq", "") if eq_bool else summ
            x, theta, id = summaries[summ], parameters[summ], ids[summ]
            # Preprocess the summaries
            if 'Pk0' in summ:
                k = np.unique(x[0]['k'])
                m = (k <= kmax) & (k >= kmin)
                x = preprocess_Pk(x, kmax, monopole=True, kmin=kmin,
                                    correct_shot=correct_shot)
            elif 'Pk' in summ:
                norm_key = summ[:-1] + '0'  # monopole (Pk0 or zPk0)
                if norm_key in summaries:
                    x = preprocess_Pk(
                        x, kmax, monopole=False, norm=summaries[norm_key],
                        kmin=kmin)
                else:
                    raise ValueError(
                        f'Need monopole for normalization of {summ}')
            elif 'Bk' in summ:
                x = preprocess_Bk(x, kmax, log=True,
                                    equilateral_only=eq_bool, kmin=kmin,
                                    correct_shot=correct_shot)
            elif 'Qk' in summ:
                x = preprocess_Bk(x, kmax, log=False,
                                    equilateral_only=eq_bool, kmin=kmin,
                                    correct_shot=correct_shot)
            else:
                raise NotImplementedError  # TODO: implement other summaries
            xs.append(x)
        if 'nbar' in exp_summary:  # add nbar
            xs.append(_get_log10nbar(summaries['Pk0']))

        if not np.all([len(x) == len(xs[0]) for x in xs]):
            raise ValueError(
                f'Inconsistent lengths of summaries. Check that all '
                'summaries have been computed for the same simulations.')
        x = np.concatenate(xs, axis=-1)

        # Get test samples only
        id = ids[summ]
        x, theta = map(np.array, [x, theta])
        test_mask = np.isin(id, itest)
        xtest = x[test_mask]
        ytest = theta[test_mask]

        nrep = int(len(itest) / len(set(itest)))
        i = ind % nrep
        x0 = torch.Tensor(xtest[i]).to(device)
        y0 = ytest[i]

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
    
    parts = os.path.normpath(modelpath).split(os.sep)
    outpath = os.path.join(savepath, parts[-2], parts[-1])
    if not os.path.isdir(outpath):
        os.makedirs(outpath)
    
    return modelpath, outpath, posterior, x0, y0, par_names


def load_prior(modelpath):

    # Store uniform parameter details
    uniform_priors = {
        'Omega_m': [0.1, 0.5],
        'Omega_b': [0.03, 0.07],
        'h': [0.5, 0.9],
        'n_s': [0.8, 1.2],
        'sigma_8': [0.6, 1.0]
    }

    fname = os.path.join(modelpath,'hodprior.csv')
    if os.path.isfile(fname):
        with open(fname, newline='') as csvfile:
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


def approximate_posterior(ind, samp0, par_names, outpath, transforms=3, hidden_features=(64, 64), train_frac=0.8, lr=1e-3, nepoch=500,
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

    print('Approximating conditional posterior')
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
        con_flow.load_state_dict(best_model_state)
        
    # Save the samples
    np.savez(os.path.join(outpath, f'train_loss_{ind}.npz'), train=all_train_loss, val=all_val_loss)
    
    return con_flow


def save_samples(ind, outpath, con_flow, x0, y0, par_names, nsamp=5000):
    
    m = np.array([p in ['sigma_radial', 'sigma_tangential'] for p in par_names], dtype=bool)
    c = torch.Tensor(y0[m])
    samp = con_flow(c).sample((nsamp,))
    
    outname = os.path.join(outpath, f'samples_{ind}.npz')
    np.savez(outname, samples=samp, x0=x0, y0=y0)
    
    return


def main(ind, sim, test_nbody, test_sim):

    savepath = f'/anvil/scratch/x-dbartlett/cmass/{test_nbody}/{test_sim}/condition_on_sigma'
    summaries = find_all_summaries(sim=sim)

    start = time.time()
    for summ in summaries:
        print(f'\nRunning summaries: {summ}')
        modelpath, outpath, posterior, x0, y0, par_names = get_posterior_runner(ind, savepath, summary=summ, sim=sim, 
                                                                                      test_nbody=test_nbody, test_sim=test_sim)
        uniform_priors = load_prior(modelpath)
        samp0 = get_posterior_samples(posterior, uniform_priors, x0, par_names, nsamp=5_000)
        con_flow = approximate_posterior(ind, samp0, par_names, outpath, hidden_features=(64, 64))
        save_samples(ind, outpath, con_flow, x0, y0, par_names, nsamp=5000)
    end = time.time()
    print(f'\nTotal time to run all summaries: {int(end - start)}s')
                          
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Condition posterior for tests on sigma values")
    parser.add_argument("--ind", help="Index of test to use", type=int)
    parser.add_argument("--sim", help="Simulation name", type=str, default='fastpm_varnoise')
    parser.add_argument("--test_nbody", help="N-body simulation type to test on", type=str, default='quijotelike')
    parser.add_argument("--test_sim", help="Test Simulation name", type=str, default='fastpm_varnoise')
    args = parser.parse_args()
    main(args.ind, args.sim, args.test_nbody, args.test_sim)
