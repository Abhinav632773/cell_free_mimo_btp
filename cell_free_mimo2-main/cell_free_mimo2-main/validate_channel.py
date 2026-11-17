# validate_channel.py
"""
Check the V2X channel against the physics of SOP.m.txt and compare it
with the i.i.d. Rayleigh channel.

Checks (statistical, since the random numbers differ from MATLAB):
    1. Mean power per link ≈ beta_mk
    2. Doppler: ray Doppler shifts ≤ f_max = v / λ, and the time
       correlation of h(t) follows Clarke's J0(2π f_max Δ)
    3. Acceleration phase π·A·T0² is small (≤ ~0.12 rad)
    4. Delay spread ≈ 2·RING_R / c
    5. Antenna correlation: high for V2X, ≈ 0 for i.i.d.
Also saves the four figures of SOP.m for one link.

Run:  python validate_channel.py
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.special import j0
import config
from channel import (generate_scenario, generate_scatterers, generate_channel_v2x,
                     generate_channel_iid, generate_channel_v2x_grid, v2x_link_params)


def antenna_correlation(samples):
    """|E[h_0 h_1*]| / E[|h|²] averaged over links, for N_TX ≥ 2."""
    corr = []
    for (m, k) in samples[0]:
        h = np.array([H[(m, k)] for H in samples])
        corr.append(np.abs(np.mean(h[:, 0] * np.conj(h[:, 1]))) /
                    np.mean(np.abs(h) ** 2))
    return float(np.mean(corr))


def time_correlation(scn, rng, delays, n_draws=500):
    """Measured |E[h(0) h(Δ)*]| / E|h|² for AP 0 → vehicle 0, antenna 0."""
    t = np.asarray(delays)
    x = np.array([generate_channel_v2x_grid(scn, generate_scatterers(rng), 0, 0, t,
                                            np.array([0.0]))[0, 0] for _ in range(n_draws)])
    return np.abs(np.mean(x * np.conj(x[:, :1]), axis=0)) / np.mean(np.abs(x[:, 0]) ** 2)


def main(save_dir="results", n_draws=1000, seed=0):
    os.makedirs(save_dir, exist_ok=True)
    rng = np.random.default_rng(seed)
    scn = generate_scenario(seed)
    lam = config.C_LIGHT / config.FC
    f_max = config.V_USER_KMH / 3.6 / lam
    checks = {}

    # 1. Power and 5. antenna correlation
    v2x = [generate_channel_v2x(scn, generate_scatterers(rng)) for _ in range(n_draws)]
    iid = [generate_channel_iid(scn, rng) for _ in range(n_draws)]
    ratio = [np.mean([np.mean(np.abs(H[(m, k)]) ** 2) for H in v2x]) / scn['beta'][m, k]
             for m in range(config.N_AP) for k in range(config.N_USER)]
    checks['power_ratio_mean'] = float(np.mean(ratio))
    checks['power_ratio_ok'] = bool(abs(np.mean(ratio) - 1) < 0.05)
    checks['antenna_corr_v2x'] = antenna_correlation(v2x)
    checks['antenna_corr_iid'] = antenna_correlation(iid)

    # 2. Doppler: per-ray shifts, and time correlation vs Clarke's J0
    scat = generate_scatterers(rng)
    f_inst = []
    for k in range(config.N_USER):
        tau0, fS, A, aod = v2x_link_params(scn, scat, 0, k)
        f_inst.append(np.max(np.abs(fS) + np.abs(A) * config.T0))
    checks['f_max_hz'] = float(f_max)
    checks['ray_doppler_max_hz'] = float(np.max(f_inst))
    checks['doppler_ok'] = bool(np.max(f_inst) <= f_max + config.A_USER / lam * config.T0)
    delays = np.array([0, 0.25, 0.5, 1.0, 2.0, 5.0]) * 1e-3
    measured = time_correlation(scn, rng, delays)
    clarke = np.abs(j0(2 * np.pi * f_max * delays))
    checks['time_corr_delays_ms'] = (delays * 1e3).tolist()
    checks['time_corr_measured'] = np.round(measured, 3).tolist()
    checks['time_corr_clarke'] = np.round(clarke, 3).tolist()
    checks['time_corr_ok'] = bool(np.max(np.abs(measured - clarke)) < 0.1)
    # Clarke model: coherence time ≈ 0.423 / f_max
    checks['coherence_time_ms'] = float(0.423 / f_max * 1e3)
    
    # 3. Acceleration phase and 4. delay spread, over all links
    scat = generate_scatterers(rng)
    max_phase, delay_spread = 0.0, []
    for m in range(config.N_AP):
        for k in range(config.N_USER):
            tau0, fS, A, aod = v2x_link_params(scn, scat, m, k)
            max_phase = max(max_phase, float(np.max(np.abs(np.pi * A * config.T0 ** 2))))
            delay_spread.append(np.max(tau0) - np.min(tau0))
    checks['accel_phase_max_rad'] = max_phase
    checks['accel_phase_bound_rad'] = float(np.pi * config.A_USER / lam * config.T0 ** 2)
    checks['delay_spread_max_ns'] = float(np.max(delay_spread) * 1e9)
    checks['delay_spread_bound_ns'] = float(2 * config.RING_R / config.C_LIGHT * 1e9)
    checks['delay_ok'] = bool(np.max(delay_spread) <= 2 * config.RING_R / config.C_LIGHT + 1e-12)

    # Median link SNR (beta already includes rho)
    checks['median_link_snr_db'] = float(np.median(10 * np.log10(scn['beta'])))

    # ---- SOP.m figures 1-4, link AP 0 → vehicle 0 ----
    t = np.linspace(0, config.T0, 1280)
    f = (np.arange(config.N_SC) - config.N_SC // 2) * config.BW / config.N_SC
    grid = generate_channel_v2x_grid(scn, scat, 0, 0, t, f)
    tau0, fS, A, _ = v2x_link_params(scn, scat, 0, 0)
    tau_t = tau0[0] - (t / config.FC) * (fS[0] + A[0] * t / 2)

    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    ax[0, 0].plot(t * 1e3, np.abs(grid[0, config.N_SC // 2]))
    ax[0, 0].set(xlabel="Time (ms)", ylabel="|h(t)|", title="Channel magnitude, centre subcarrier")
    ax[0, 1].plot(t * 1e3, tau_t * 1e9)
    ax[0, 1].set(xlabel="Time (ms)", ylabel="τ(t) [ns]", title="Time-varying path delay (ray 0)")
    ax[1, 0].plot(t * 1e3, A[0] * t)
    ax[1, 0].set(xlabel="Time (ms)", ylabel="f_A(t) [Hz]", title="Acceleration Doppler (ray 0)")
    ax[1, 1].plot(t * 1e3, np.pi * A[0] * t ** 2)
    ax[1, 1].set(xlabel="Time (ms)", ylabel="π A t² [rad]", title="Acceleration phase (ray 0)")
    for a in ax.flat:
        a.grid(True)
    fig.tight_layout()
    fig.savefig(os.path.join(save_dir, "v2x_validation.png"), dpi=150)
    plt.close(fig)

    # Time-frequency map
    fig, a = plt.subplots(figsize=(7, 4))
    im = a.imshow(20 * np.log10(np.abs(grid[0]) + 1e-12), aspect="auto", origin="lower",
                  extent=[0, config.T0 * 1e3, f[0] / 1e6, f[-1] / 1e6])
    a.set(xlabel="Time (ms)", ylabel="Subcarrier offset (MHz)", title="|h(t, f)| [dB], AP 0 → vehicle 0")
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(os.path.join(save_dir, "v2x_time_frequency.png"), dpi=150)
    plt.close(fig)

    with open(os.path.join(save_dir, "channel_validation.json"), "w") as fp:
        json.dump(checks, fp, indent=2)

    for key, val in checks.items():
        print(f"  {key:<24} {val}")
    return checks


if __name__ == "__main__":
    main()
