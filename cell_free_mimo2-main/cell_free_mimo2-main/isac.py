# isac.py
"""
Integrated Sensing and Communication (ISAC) Extension for Cell-Free MIMO.

Transforms standard communication Access Points (APs) into Dual-Functional
Radar-Communication (DFRC) / ISAC nodes that simultaneously:
  1. Transmit communication data beams to mobile users (downlink communication).
  2. Transmit radar probing beams toward sensing targets (environmental sensing / tracking).

Activated when `config.useISACnodes = True`.
When `config.useISACnodes = False`, standard AP communication is preserved.
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import config
from rates import beam_gain, compute_mr_precoding


def steering_vector(aod, n_tx=None):
    """
    Uniform Linear Array (ULA) half-wavelength steering vector.
    
    Args:
        aod: Angle of departure in radians
        n_tx: Number of transmit antennas (default: config.N_TX)
        
    Returns:
        steer: Complex array of shape (n_tx,) normalized so ||steer||^2 = 1.
    """
    n_tx = config.N_TX if n_tx is None else n_tx
    z = np.arange(n_tx) - 0.5 * (n_tx - 1)
    # Normalized steering vector
    vec = np.exp(-1j * np.pi * z * np.sin(aod))
    return vec / np.sqrt(n_tx)


def generate_targets(ap_pos, user_pos, n_targets=None, seed=None):
    """
    Generate target locations and compute geometric angles/distances from ISAC nodes.
    
    Args:
        ap_pos: (N_AP, 2) positions of ISAC nodes
        user_pos: (N_USER, 2) positions of users
        n_targets: Number of radar targets (default: config.N_TARGET)
        seed: Random seed for target placement
        
    Returns:
        target_info: dict with:
            'pos': (n_targets, 2) target coordinates
            'distances': (N_AP, n_targets) distances from each node to target
            'aod': (N_AP, n_targets) angles of departure (radians)
            'steer': dict of (m, t) -> steering vector of shape (N_TX,)
    """
    n_targets = config.N_TARGET if n_targets is None else n_targets
    rng = np.random.default_rng(seed if seed is not None else config.SEED + 101)
    
    # Determine deployment boundaries
    max_bound = config.AREA_M if config.CHANNEL_MODEL in ("v2x", "iid") else 1.0
    
    # Place target(s) centrally or randomly within the deployment area
    target_pos = np.zeros((n_targets, 2))
    for t in range(n_targets):
        # Center region to ensure visibility from multiple ISAC nodes
        target_pos[t] = rng.uniform(0.2 * max_bound, 0.8 * max_bound, size=2)
    
    distances = np.zeros((config.N_AP, n_targets))
    aod = np.zeros((config.N_AP, n_targets))
    steer = {}
    
    for m in range(config.N_AP):
        for t in range(n_targets):
            dx = target_pos[t, 0] - ap_pos[m, 0]
            dy = target_pos[t, 1] - ap_pos[m, 1]
            dist = np.sqrt(dx**2 + dy**2)
            distances[m, t] = max(dist, 1.0)
            angle = np.arctan2(dy, dx)
            aod[m, t] = angle
            steer[(m, t)] = steering_vector(angle)
            
    return {
        'pos': target_pos,
        'distances': distances,
        'aod': aod,
        'steer': steer
    }


def compute_isac_precoding(H, gamma, target_info, eta=None):
    """
    Compute Dual-Functional Radar-Communication (DFRC) precoding vectors.
    
    Transmitted signal from ISAC node m:
        x_m = sqrt(1 - eta) * v_m * s_c + sqrt(eta) * w_m * s_r
        
    where:
        v_m: Communication precoding unit vector (pointing at assigned user)
        w_m: Radar probing unit vector (pointing at sensing target)
        eta: Radar power allocation ratio in [0, 1)
        
    Args:
        H: Channel dictionary H[(m, k)]
        gamma: (N_AP, N_USER) binary assignment matrix
        target_info: Geometry dict from generate_targets()
        eta: Radar power fraction (default: config.RADAR_POWER_RATIO)
        
    Returns:
        V_comm: dict of m -> communication precoding vector (with power sqrt(1 - eta))
        W_radar: dict of m -> radar precoding vector (with power sqrt(eta))
    """
    eta = config.RADAR_POWER_RATIO if eta is None else eta
    eta = np.clip(eta, 0.0, 0.99)
    p_comm = np.sqrt(1.0 - eta)
    p_radar = np.sqrt(eta)
    
    V_MR = compute_mr_precoding(H)
    V_comm = {}
    W_radar = {}
    
    for m in range(config.N_AP):
        assigned_users = np.where(gamma[m] == 1)[0]
        if len(assigned_users) > 0:
            k = assigned_users[0]
            V_comm[m] = p_comm * V_MR[(m, k)]
        else:
            V_comm[m] = np.zeros(config.N_TX, dtype=complex)
            
        # Point radar beam toward target 0 (or primary target)
        w_dir = target_info['steer'][(m, 0)]
        W_radar[m] = p_radar * w_dir
        
    return V_comm, W_radar


def compute_isac_rates_and_sensing(H, gamma, V_comm, W_radar, target_info):
    """
    Compute communication user rates AND radar sensing metrics under DFRC operation.
    
    1. Communication SINR:
       Signal: desired communication from serving ISAC nodes.
       Interference: non-serving comm beams + all radar probing beams.
       R_k = log2(1 + SINR_k)
       
    2. Radar Sensing Metric:
       Target illumination power:
         P_target = sum_m [ |a_m^H v_m|^2 + |a_m^H w_m|^2 ]
       Radar received echo SNR (radar range equation).
       Radar sensing rate / capacity R_sens = 0.5 * log2(1 + SNR_radar).
       
    Returns:
        results: dict containing:
            'rates': (N_USER,) communication rates in bits/s/Hz
            'min_rate': minimum communication rate (bits/s/Hz)
            'sum_rate': sum communication rate (bits/s/Hz)
            'radar_snr_db': target received echo SNR in dB
            'sensing_rate': radar sensing capacity (bits/s/Hz)
            'isac_utility': weighted joint score alpha * min_rate + (1 - alpha) * sensing_rate
            'target_power': total target illumination power
    """
    rates = np.zeros(config.N_USER)
    
    # --- 1. Downlink Communication Rates ---
    for k in range(config.N_USER):
        signal = 0.0
        comm_interference = 0.0
        radar_interference = 0.0
        
        for m in range(config.N_AP):
            h_mk = H[(m, k)]
            v_m = V_comm[m]
            w_m = W_radar[m]
            
            comm_gain = beam_gain(h_mk, v_m)
            radar_gain = beam_gain(h_mk, w_m)
            
            if gamma[m, k] == 1:
                signal += config.RHO * comm_gain
            else:
                comm_interference += config.MU_NK * config.RHO * comm_gain
                
            # Radar probing signals act as interference to user communication
            radar_interference += config.MU_RADAR * config.RHO * radar_gain
            
        sinr = signal / (comm_interference + radar_interference + 1.0)
        rates[k] = np.log2(1.0 + sinr)
        
    # --- 2. Radar Sensing Metrics ---
    # Primary target 0
    t = 0
    target_power = 0.0
    radar_echo_power = 0.0
    
    for m in range(config.N_AP):
        a_m = target_info['steer'][(m, t)]
        # Received power at target from node m
        p_comm_illumin = np.abs(np.dot(a_m.conj(), V_comm[m]))**2
        p_radar_illumin = np.abs(np.dot(a_m.conj(), W_radar[m]))**2
        node_power = p_comm_illumin + p_radar_illumin
        target_power += node_power
        
        # Pathloss for radar sensing link
        dist = target_info['distances'][m, t]
        if config.CHANNEL_MODEL in ("v2x", "iid"):
            # Large scale pathloss scaled with radar distance
            beta_rad = 10**(config.SNR_REF_DB / 10.0) * (dist / config.D_REF)**(-config.KAPPA)
        else:
            # Normalized distance model
            beta_rad = (max(dist, 0.05))**(-config.KAPPA)
            
        # Monostatic/cooperative echo power proportional to round-trip pathloss & RCS
        radar_echo_power += config.RHO * node_power * config.RADAR_RCS * (beta_rad ** 1.5)
        
    radar_snr = radar_echo_power / config.SIGMA2
    radar_snr_db = 10.0 * np.log10(max(radar_snr, 1e-12))
    sensing_rate = 0.5 * np.log2(1.0 + radar_snr)
    
    min_rate = float(np.min(rates))
    sum_rate = float(np.sum(rates))
    isac_utility = config.ISAC_ALPHA * min_rate + (1.0 - config.ISAC_ALPHA) * sensing_rate
    
    return {
        'rates': rates,
        'min_rate': min_rate,
        'sum_rate': sum_rate,
        'radar_snr': radar_snr,
        'radar_snr_db': radar_snr_db,
        'sensing_rate': sensing_rate,
        'isac_utility': isac_utility,
        'target_power': target_power,
    }


def evaluate_isac_dataset(dataset, cloud, edges, target_info, eta=None):
    """Evaluate QNN and classical baselines under ISAC operation over a dataset."""
    from baselines import search_based_assignment, random_assignment
    
    eta = config.RADAR_POWER_RATIO if eta is None else eta
    results = {
        'qnn': {'min_rates': [], 'sum_rates': [], 'radar_snr_db': [], 'sensing_rates': [], 'utility': []},
        'search': {'min_rates': [], 'sum_rates': [], 'radar_snr_db': [], 'sensing_rates': [], 'utility': []},
        'random': {'min_rates': [], 'sum_rates': [], 'radar_snr_db': [], 'sensing_rates': [], 'utility': []},
    }
    
    for sample in dataset:
        H = sample['H']
        features = sample['features']
        
        # --- 1. QNN Assignment ---
        cloud_in = cloud.prepare_features(features)
        gamma_qnn = cloud.decode_assignment(cloud.forward(cloud_in))
        V_qnn, W_qnn = compute_isac_precoding(H, gamma_qnn, target_info, eta=eta)
        res_qnn = compute_isac_rates_and_sensing(H, gamma_qnn, V_qnn, W_qnn, target_info)
        
        results['qnn']['min_rates'].append(res_qnn['min_rate'])
        results['qnn']['sum_rates'].append(res_qnn['sum_rate'])
        results['qnn']['radar_snr_db'].append(res_qnn['radar_snr_db'])
        results['qnn']['sensing_rates'].append(res_qnn['sensing_rate'])
        results['qnn']['utility'].append(res_qnn['isac_utility'])
        
        # --- 2. Search Assignment ---
        gamma_search = search_based_assignment(H)
        V_search, W_search = compute_isac_precoding(H, gamma_search, target_info, eta=eta)
        res_search = compute_isac_rates_and_sensing(H, gamma_search, V_search, W_search, target_info)
        
        results['search']['min_rates'].append(res_search['min_rate'])
        results['search']['sum_rates'].append(res_search['sum_rate'])
        results['search']['radar_snr_db'].append(res_search['radar_snr_db'])
        results['search']['sensing_rates'].append(res_search['sensing_rate'])
        results['search']['utility'].append(res_search['isac_utility'])
        
        # --- 3. Random Assignment ---
        gamma_rand = random_assignment(H)
        V_rand, W_rand = compute_isac_precoding(H, gamma_rand, target_info, eta=eta)
        res_rand = compute_isac_rates_and_sensing(H, gamma_rand, V_rand, W_rand, target_info)
        
        results['random']['min_rates'].append(res_rand['min_rate'])
        results['random']['sum_rates'].append(res_rand['sum_rate'])
        results['random']['radar_snr_db'].append(res_rand['radar_snr_db'])
        results['random']['sensing_rates'].append(res_rand['sensing_rate'])
        results['random']['utility'].append(res_rand['isac_utility'])
        
    summary = {}
    for method, d in results.items():
        summary[method] = {
            'avg_min_rate': np.mean(d['min_rates']),
            'avg_sum_rate': np.mean(d['sum_rates']),
            'avg_radar_snr_db': np.mean(d['radar_snr_db']),
            'avg_sensing_rate': np.mean(d['sensing_rates']),
            'avg_utility': np.mean(d['utility']),
        }
    return summary


def run_isac_pareto_analysis(dataset, cloud, edges, target_info,
                             eta_list=[0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.85]):
    """Sweep radar power fraction eta to obtain Pareto Trade-off Curve."""
    pareto_res = {'eta': eta_list, 'qnn': [], 'search': [], 'random': []}
    
    for eta in eta_list:
        res = evaluate_isac_dataset(dataset, cloud, edges, target_info, eta=eta)
        pareto_res['qnn'].append((res['qnn']['avg_min_rate'], res['qnn']['avg_sensing_rate'], res['qnn']['avg_radar_snr_db']))
        pareto_res['search'].append((res['search']['avg_min_rate'], res['search']['avg_sensing_rate'], res['search']['avg_radar_snr_db']))
        pareto_res['random'].append((res['random']['avg_min_rate'], res['random']['avg_sensing_rate'], res['random']['avg_radar_snr_db']))
        
    return pareto_res


def plot_isac_network(ap_pos, user_pos, target_info, gamma=None, save_path="results/isac_network.png"):
    """Plot network topology displaying ISAC nodes, communication users, and radar targets."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.figure(figsize=(7, 6))
    
    # Plot ISAC nodes (APs)
    plt.scatter(ap_pos[:, 0], ap_pos[:, 1], c='blue', marker='s', s=120, label='ISAC Nodes (DFRC)', zorder=5)
    for m in range(len(ap_pos)):
        plt.annotate(f"ISAC-{m}", (ap_pos[m, 0], ap_pos[m, 1] + 0.03 * np.max(ap_pos)),
                     ha='center', fontsize=9, fontweight='bold', color='blue')
        
    # Plot Users
    plt.scatter(user_pos[:, 0], user_pos[:, 1], c='green', marker='o', s=100, label='Comm Users', zorder=5)
    for k in range(len(user_pos)):
        plt.annotate(f"User-{k}", (user_pos[k, 0], user_pos[k, 1] - 0.04 * np.max(user_pos)),
                     ha='center', fontsize=9, color='green')
        
    # Plot Radar Target(s)
    targets = target_info['pos']
    plt.scatter(targets[:, 0], targets[:, 1], c='crimson', marker='*', s=250, label='Radar Sensing Target', zorder=6)
    for t in range(len(targets)):
        plt.annotate(f"Target-{t}", (targets[t, 0], targets[t, 1] + 0.03 * np.max(targets)),
                     ha='center', fontsize=10, fontweight='bold', color='crimson')
        
    # Draw communication links (assignment)
    if gamma is not None:
        for m in range(len(ap_pos)):
            for k in range(len(user_pos)):
                if gamma[m, k] == 1:
                    plt.plot([ap_pos[m, 0], user_pos[k, 0]], [ap_pos[m, 1], user_pos[k, 1]],
                             'g--', alpha=0.6, linewidth=1.5, label='Comm Link' if (m == 0 and k == 0) else "")
                    
    # Draw radar probing beams toward target 0
    for m in range(len(ap_pos)):
        plt.plot([ap_pos[m, 0], targets[0, 0]], [ap_pos[m, 1], targets[0, 1]],
                 'r:', alpha=0.5, linewidth=1.2, label='Radar Probing Beam' if m == 0 else "")
        
    plt.title("Cell-Free ISAC Network Topology (Communication + Radar Sensing)")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.legend(loc='upper right', framealpha=0.9)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()
    print(f"  ISAC topology saved to: {save_path}")


def plot_isac_pareto(pareto_res, save_path="results/isac_pareto.png"):
    """Plot the ISAC Pareto Trade-off Front: Communication Min Rate vs. Radar Sensing Quality."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.figure(figsize=(7.5, 5))
    
    etas = pareto_res['eta']
    for method, label, color, marker in [
        ('search', 'Search-based + DFRC', 'darkorange', 's'),
        ('qnn', 'QNN + DFRC', 'blue', 'o'),
        ('random', 'Random + DFRC', 'gray', '^'),
    ]:
        comm_rates = [pt[0] for pt in pareto_res[method]]
        sensing_snrs = [pt[2] for pt in pareto_res[method]]
        plt.plot(sensing_snrs, comm_rates, marker=marker, color=color, linewidth=2, label=label)
        for i, eta in enumerate(etas):
            if eta in (0.0, 0.2, 0.5, 0.85):
                plt.annotate(f"η={eta}", (sensing_snrs[i], comm_rates[i]),
                             textcoords="offset points", xytext=(-10, 7), fontsize=8, color=color)
                
    plt.title("ISAC Pareto Trade-off Front: Comm Min Rate vs. Radar Sensing SNR")
    plt.xlabel("Target Radar Echo SNR [dB]")
    plt.ylabel("Min User Communication Rate [bits/s/Hz]")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='best', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()
    print(f"  ISAC Pareto trade-off curve saved to: {save_path}")


def run_isac_main(quick=False):
    """Main execution pipeline for the ISAC nodes extension."""
    n_epochs = 2 if quick else config.N_EPOCH
    n_train = 10 if quick else config.N_DATA
    n_test = 10 if quick else 50
    
    print("=" * 65)
    print("CELL-FREE ISAC: INTEGRATED SENSING AND COMMUNICATION NODES")
    print("=" * 65)
    print(f"  Mode: ISAC Nodes (config.useISACnodes = True)")
    print(f"  Nodes: {config.N_AP} DFRC Transceivers")
    print(f"  Users: {config.N_USER} Communication Terminals")
    print(f"  Targets: {config.N_TARGET} Radar Sensing Target(s)")
    print(f"  Radar Power Ratio (eta): {config.RADAR_POWER_RATIO}")
    print(f"  Channel Model: {config.CHANNEL_MODEL}")
    if quick:
        print(f"  [QUICK MODE]: {n_train} samples, {n_epochs} epochs\n")
    else:
        print(f"  [FULL MODE]: {n_train} samples, {n_epochs} epochs\n")
    
    # 1. Setup layout & Train QNN
    from train import train, generate_dataset, make_layout
    layout, ap_pos, user_pos = make_layout()
    train_data = generate_dataset(n_train, layout, seed=config.SEED)
    
    print("[1/5] Training QNN under Cell-Free layout...")
    cloud, edges, history, _, _, _ = train(
        dataset=train_data, layout=layout, n_epoch=n_epochs
    )
    
    # 2. Setup Targets
    print("\n[2/5] Initializing Radar Sensing Target(s)...")
    target_info = generate_targets(ap_pos, user_pos, seed=config.SEED + 42)
    t_pos = target_info['pos'][0]
    print(f"  Target 0 position: [{t_pos[0]:.2f}, {t_pos[1]:.2f}]")
    
    # 3. Test dataset
    print("\n[3/5] Generating test dataset...")
    test_data = generate_dataset(n_test, layout, seed=config.SEED + 999)
    print(f"  Test samples: {len(test_data)}")
    
    # 4. Evaluate ISAC performance
    print("\n[4/5] Evaluating ISAC methods (Communication + Radar Sensing)...")
    summary = evaluate_isac_dataset(test_data, cloud, edges, target_info)
    
    print(f"\n  {'Method':<20} {'Min Rate [b/s/Hz]':>18} {'Radar SNR [dB]':>16} {'ISAC Utility':>14}")
    print(f"  {'-'*72}")
    for method, name in [('qnn', 'QNN + DFRC'), ('search', 'Search + DFRC'), ('random', 'Random + DFRC')]:
        m_res = summary[method]
        print(f"  {name:<20} {m_res['avg_min_rate']:>18.4f} {m_res['avg_radar_snr_db']:>16.2f} {m_res['avg_utility']:>14.4f}")
        
    # 5. Pareto Trade-off analysis & Plots
    print("\n[5/5] Generating ISAC Trade-off Front and Visualizations...")
    pareto_res = run_isac_pareto_analysis(test_data, cloud, edges, target_info)
    
    # Save editable ISAC results to CSV
    os.makedirs("results", exist_ok=True)
    import csv
    with open(os.path.join("results", "isac_summary.csv"), "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.writer(fp)
        w.writerow(["Method", "Min Rate [bits/s/Hz]", "Sum Rate [bits/s/Hz]", "Radar SNR [dB]", "Sensing Rate", "ISAC Utility"])
        for m_key, m_name in [('qnn', 'QNN + DFRC'), ('search', 'Search + DFRC'), ('random', 'Random + DFRC')]:
            r = summary[m_key]
            w.writerow([m_name, f"{r['avg_min_rate']:.4f}", f"{r['avg_sum_rate']:.4f}", f"{r['avg_radar_snr_db']:.2f}", f"{r['avg_sensing_rate']:.4f}", f"{r['avg_utility']:.4f}"])
    
    with open(os.path.join("results", "isac_pareto.csv"), "w", newline="", encoding="utf-8-sig") as fp:
        w = csv.writer(fp)
        w.writerow(["Radar Power Ratio (eta)", "Method", "Min Comm Rate [bits/s/Hz]", "Radar Echo SNR [dB]", "Sensing Rate [bits/s/Hz]"])
        etas = pareto_res['eta']
        for i, eta in enumerate(etas):
            for m_key, m_name in [('search', 'Search-based + DFRC'), ('qnn', 'QNN + DFRC'), ('random', 'Random + DFRC')]:
                pt = pareto_res[m_key][i]
                w.writerow([eta, m_name, f"{pt[0]:.4f}", f"{pt[2]:.2f}", f"{pt[1]:.4f}"])
    print("  Saved editable CSVs: results/isac_summary.csv, results/isac_pareto.csv")
    
    # Sample assignment for network visualization
    sample = test_data[0]
    cloud_in = cloud.prepare_features(sample['features'])
    gamma_sample = cloud.decode_assignment(cloud.forward(cloud_in))
    
    plot_isac_network(ap_pos, user_pos, target_info, gamma=gamma_sample)
    plot_isac_pareto(pareto_res)
    from plot import plot_training_curves
    plot_training_curves(history)
    
    print("\n" + "=" * 65)
    print("ISAC EXTENSION EXECUTION COMPLETED")
    print("=" * 65)
    print("  Results & Visualizations stored in results/")
    print("=" * 65)


if __name__ == "__main__":
    import sys
    quick_flag = "--quick" in sys.argv
    run_isac_main(quick=quick_flag)
