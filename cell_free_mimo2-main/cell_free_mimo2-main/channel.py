# channel.py
"""
Cell-Free MIMO Channel Model.
Generates the wireless channels between APs and users.

Key concept: h_{m,k} is a complex vector telling us how the signal
changes between AP m and user k. Bigger |h| = better connection.
"""

import numpy as np
import config


def generate_positions(seed=None):
    """
    Place APs and users randomly in a 1×1 square area.
    
    Returns:
        ap_pos:   (N_AP, 2) array - x,y positions of APs
        user_pos: (N_USER, 2) array - x,y positions of users
    """
    if seed is not None:
        np.random.seed(seed)
    
    ap_pos = np.random.uniform(0, 1, size=(config.N_AP, 2))
    user_pos = np.random.uniform(0, 1, size=(config.N_USER, 2))
    
    return ap_pos, user_pos


def compute_distances(ap_pos, user_pos):
    """
    Compute distance between every AP-user pair.
    
    Returns:
        distances: (N_AP, N_USER) matrix
                   distances[m, k] = distance between AP m and user k
                   Normalized to [0, 1] range
    """
    N_AP = len(ap_pos)
    N_USER = len(user_pos)
    distances = np.zeros((N_AP, N_USER))
    
    for m in range(N_AP):
        for k in range(N_USER):
            # Euclidean distance
            diff = ap_pos[m] - user_pos[k]
            distances[m, k] = np.sqrt(diff[0]**2 + diff[1]**2)
    
    # Normalize so max distance = 1
    max_dist = np.max(distances)
    if max_dist > 0:
        distances = distances / max_dist
    
    # Avoid zero distance (would cause division by zero)
    distances = np.maximum(distances, 0.01)
    
    return distances


def generate_channel(distances):
    """
    Generate random channel vectors for all AP-user pairs.
    
    For each AP m and user k:
        h_{m,k} is a complex vector of size N_TX
    
    Closer AP-user pairs get stronger channels (bigger |h|).
    
    The formula (simplified from Eq. 3):
        h_{m,k}[j] = (1/sqrt(N_PATH)) * sum of random_complex * distance_factor
    
    Returns:
        H: dict where H[(m, k)] = complex numpy array of shape (N_TX,)
    """
    H = {}
    
    for m in range(config.N_AP):
        for k in range(config.N_USER):
            # Distance-based signal strength
            # Farther away = weaker signal (this is "pathloss")
            channel_strength = distances[m, k] ** (-config.KAPPA)
            
            # Generate the channel vector (one element per antenna)
            h_mk = np.zeros(config.N_TX, dtype=complex)
            
            for j in range(config.N_TX):
                # Sum over multiple signal paths (reflections off walls, etc.)
                for n in range(config.N_PATH):
                    # Random complex number (Rayleigh fading)
                    # This models the random nature of wireless
                    random_gain = (np.random.randn() + 1j * np.random.randn()) / np.sqrt(2)
                    
                    # Scale by distance-based strength
                    random_gain *= np.sqrt(channel_strength)
                    
                    # Random phase from antenna array
                    angle = np.random.uniform(0, 2 * np.pi)
                    z = j - 0.5 * (config.N_TX - 1)
                    steering = np.exp(-1j * 2 * np.pi * angle * z)
                    
                    h_mk[j] += random_gain * steering
                
                # Average over paths
                h_mk[j] /= np.sqrt(config.N_PATH)
            
            H[(m, k)] = h_mk
    
    return H


def channel_to_features(H):
    """
    Convert complex channel dict into a real-valued matrix
    that can be fed into a QNN.
    
    Complex numbers have real and imaginary parts:
        h = a + bj  →  we store [a, b]
    
    Returns:
        features: (N_AP, N_USER * 2 * N_TX) real-valued matrix
    """
    rows = []
    for m in range(config.N_AP):
        row = []
        for k in range(config.N_USER):
            h = H[(m, k)]
            # Split complex into real and imaginary parts
            row.extend(np.real(h).tolist())
            row.extend(np.imag(h).tolist())
        rows.append(row)
    
    return np.array(rows)


# =====================================================================
# V2X one-ring channel (non-WSSUS, from SOP.m.txt)
#
# APs are static road-side units, users are vehicles. Each vehicle
# carries a ring of L_SCAT scatterers (radius RING_R). Every ray has a
# Doppler shift from the vehicle speed and a linear Doppler chirp from
# its acceleration, so the channel changes with time t.
# =====================================================================

def generate_scenario(seed=None):
    """
    Place APs and vehicles in an AREA_M × AREA_M square (metres).
    Vehicles are kept at least D_MIN from every AP.

    Returns:
        scn: dict with
            ap_pos, user_pos: positions [m]
            dist:   (N_AP, N_USER) distances [m]
            beta:   (N_AP, N_USER) large-scale gain = rho × pathloss
            gammaR: (N_USER,) direction of motion [rad]
            betaR:  (N_USER,) direction of acceleration [rad]
    """
    rng = np.random.default_rng(seed)
    ap_pos = rng.uniform(0, config.AREA_M, size=(config.N_AP, 2))

    user_pos = np.zeros((config.N_USER, 2))
    for k in range(config.N_USER):
        while True:
            p = rng.uniform(0, config.AREA_M, size=2)
            if np.min(np.linalg.norm(ap_pos - p, axis=1)) >= config.D_MIN:
                user_pos[k] = p
                break

    dist = np.linalg.norm(ap_pos[:, None, :] - user_pos[None, :, :], axis=2)

    return {
        'ap_pos': ap_pos,
        'user_pos': user_pos,
        'dist': dist,
        'beta': large_scale_gain(dist),
        'gammaR': rng.uniform(-np.pi, np.pi, size=config.N_USER),
        'betaR': rng.uniform(-np.pi, np.pi, size=config.N_USER),
    }


def large_scale_gain(dist_m):
    """
    beta = SNR at D_REF × (d / D_REF)^(-KAPPA)

    The noise power is 1 in rates.py, so beta already contains the
    SNR: a link at D_REF has an average SNR of SNR_REF_DB per antenna.
    """
    return 10 ** (config.SNR_REF_DB / 10) * (dist_m / config.D_REF) ** (-config.KAPPA)


def generate_scatterers(rng=None):
    """
    Draw one ring of scatterers per vehicle (shared by all APs).

    Returns:
        scat: dict of (N_USER, L_SCAT) arrays
            phi:   scatterer angle on the ring
            g:     positive path gains, normalized so sum(g²) = 1
            theta: random path phases
    """
    rng = np.random.default_rng() if rng is None else rng
    shape = (config.N_USER, config.L_SCAT)

    g = np.sqrt(rng.standard_normal(shape) ** 2 + rng.standard_normal(shape) ** 2)
    g = g / np.sqrt(np.sum(g ** 2, axis=1, keepdims=True))

    return {
        'phi': rng.uniform(-np.pi, np.pi, size=shape),
        'g': g,
        'theta': rng.uniform(-np.pi, np.pi, size=shape),
    }


def v2x_link_params(scn, scat, m, k, speed_kmh=None, accel=None):
    """
    Per-ray geometry of the link AP m → vehicle k (SOP.m, steps 14-19).

    Returns:
        tau0: (L,) initial delays [s]
        fS:   (L,) velocity Doppler [Hz]
        A:    (L,) acceleration Doppler rate [Hz/s]
        aod:  (L,) angle of departure at the AP [rad]
    """
    speed_kmh = config.V_USER_KMH if speed_kmh is None else speed_kmh
    accel = config.A_USER if accel is None else accel
    lam = config.C_LIGHT / config.FC

    phi = scat['phi'][k]
    xS = scn['user_pos'][k, 0] + config.RING_R * np.cos(phi)
    yS = scn['user_pos'][k, 1] + config.RING_R * np.sin(phi)

    dx = xS - scn['ap_pos'][m, 0]
    dy = yS - scn['ap_pos'][m, 1]
    dT = np.sqrt(dx ** 2 + dy ** 2)
    aod = np.arctan2(dy, dx)

    tau0 = (dT + config.RING_R) / config.C_LIGHT

    # Static AP: only the vehicle (receiver) terms of SOP.m remain.
    # The ray arrives from the scatterer direction phi.
    fS = (speed_kmh / 3.6) / lam * np.cos(phi - scn['gammaR'][k])
    A = accel / lam * np.cos(phi - scn['betaR'][k])

    return tau0, fS, A, aod


def steering_vector(aod):
    """
    Half-wavelength ULA steering, one column per ray.
    a_j(phi) = exp(-1j π z_j sin(phi)),  z_j = j - (N_TX-1)/2

    Returns: (N_TX, L) complex array
    """
    z = np.arange(config.N_TX) - 0.5 * (config.N_TX - 1)
    return np.exp(-1j * np.pi * np.outer(z, np.sin(aod)))


def generate_channel_v2x(scn, scat, t=0.0, f=0.0, speed_kmh=None, accel=None):
    """
    V2X channel at time t [s] and subcarrier offset f [Hz].

    h_mk[j] = sqrt(beta_mk) Σ_l g_l exp(-j(θ_l + 2π τ_l(t)(FC+f))) a_j(φ_l)
    τ_l(t)  = τ_l(0) - (t/FC)(fS_l + A_l t/2)

    Returns:
        H: dict where H[(m, k)] = complex numpy array of shape (N_TX,)
    """
    H = {}
    for m in range(config.N_AP):
        for k in range(config.N_USER):
            tau0, fS, A, aod = v2x_link_params(scn, scat, m, k, speed_kmh, accel)
            tau = tau0 - (t / config.FC) * (fS + A * t / 2)
            ray = scat['g'][k] * np.exp(
                -1j * (scat['theta'][k] + 2 * np.pi * tau * (config.FC + f)))
            H[(m, k)] = np.sqrt(scn['beta'][m, k]) * (steering_vector(aod) @ ray)
    return H


def generate_channel_v2x_grid(scn, scat, m, k, t, f, speed_kmh=None, accel=None):
    """
    Full time-frequency response of one link, for validation plots.

    Args:
        t: (N_T,) time instants [s]
        f: (N_F,) subcarrier offsets [Hz]

    Returns: (N_TX, N_F, N_T) complex array
    """
    tau0, fS, A, aod = v2x_link_params(scn, scat, m, k, speed_kmh, accel)
    tau = tau0[:, None] - (t[None, :] / config.FC) * (fS[:, None] + A[:, None] * t[None, :] / 2)
    phase = scat['theta'][k][:, None, None] + \
        2 * np.pi * tau[:, None, :] * (config.FC + f[None, :, None])
    ray = scat['g'][k][:, None, None] * np.exp(-1j * phase)        # (L, N_F, N_T)
    return np.sqrt(scn['beta'][m, k]) * np.einsum('jl,lft->jft', steering_vector(aod), ray)


def generate_channel_iid(scn, rng=None):
    """
    i.i.d. Rayleigh with the same large-scale gain as the V2X scenario:
    h_mk ~ CN(0, beta_mk I). Used to compare small-scale fading only.
    """
    rng = np.random.default_rng() if rng is None else rng
    H = {}
    for m in range(config.N_AP):
        for k in range(config.N_USER):
            w = (rng.standard_normal(config.N_TX) + 1j * rng.standard_normal(config.N_TX)) / np.sqrt(2)
            H[(m, k)] = np.sqrt(scn['beta'][m, k]) * w
    return H


def generate_sample(layout, model=None, rng=None):
    """
    Generate one complete channel sample.

    Args:
        layout: distances matrix (model "rayleigh") or scenario dict
                from generate_scenario (models "iid" and "v2x")
        model:  "rayleigh" | "iid" | "v2x" (default: config.CHANNEL_MODEL)

    Returns:
        H: channel dict
        features: real-valued feature matrix for QNN input
    """
    model = config.CHANNEL_MODEL if model is None else model

    if model == "rayleigh":
        H = generate_channel(layout)
    elif model == "iid":
        H = generate_channel_iid(layout, rng)
    elif model == "v2x":
        H = generate_channel_v2x(layout, generate_scatterers(rng))
    else:
        raise ValueError(f"Unknown channel model: {model}")

    features = channel_to_features(H)
    return H, features


# ---- Quick test ----
if __name__ == "__main__":
    # Generate positions
    ap_pos, user_pos = generate_positions(seed=42)
    print("AP positions:")
    print(ap_pos)
    print("\nUser positions:")
    print(user_pos)
    
    # Compute distances
    dist = compute_distances(ap_pos, user_pos)
    print("\nDistances (AP x User):")
    print(np.round(dist, 3))
    
    # Generate channel
    H, features = generate_sample(dist)
    
    print("\nChannel h_(AP0, User0):", H[(0, 0)])
    print("  Strength |h|:", np.round(np.abs(H[(0, 0)]), 3))
    
    print("\nChannel h_(AP0, User1):", H[(0, 1)])
    print("  Strength |h|:", np.round(np.abs(H[(0, 1)]), 3))
    
    print(f"\nFeature matrix shape: {features.shape}")
    print(f"  ({config.N_AP} APs × {config.N_USER * 2 * config.N_TX} features per AP)")