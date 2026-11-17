# config.py
"""
All system parameters from Table III of the paper.
One place to change everything.
"""

import numpy as np


# --- System Model (the wireless network) ---
N_AP = 4            # Number of Access Points (routers)
N_USER = 3          # Number of users (phones)
N_TX = 2            # Number of antennas per AP
N_PATH = 3          # Number of signal paths (reflections)
KAPPA = 2.3         # How fast signal weakens with distance
SIGMA2 = 1.0        # Background noise power
P_T = 1.0           # Transmit power per AP
RHO = P_T / SIGMA2  # Signal-to-noise ratio
MU_NK = 0.1         # Interference factor between APs

# --- Training ---
N_DATA = 100        # Training samples
N_EPOCH = 100       # Training epochs
LR = 0.01           # Learning rate
R_PENALTY = -10     # Penalty when a user gets no AP

# --- QNN Architecture ---
N_LAYER_CLOUD = 3   # Layers in cloud QNN
N_LAYER_EDGE = 3    # Layers in edge QNN

# --- Reproducibility ---
SEED = 42
# --- Bug-fix toggle ---
# True reproduces the original (pre-fix) behaviour, only for benchmark E0:
#   RZ-before-H encoding (input ignored), cloud sees AP 0 only, gain = |conj(h)·v|².
LEGACY_MODE = False

# --- ISAC (Integrated Sensing and Communication) Extension ---
# False = standard APs (communication only); True = ISAC nodes (comms + radar sensing)
useISACnodes = True
N_TARGET = 1            # Number of radar sensing targets
RADAR_POWER_RATIO = 0.2 # Fraction of node transmit power allocated to radar beamforming (eta)
ISAC_ALPHA = 0.5        # Pareto weight: alpha * Comm_Rate + (1 - alpha) * Radar_Sensing
RADAR_RCS = 1.0         # Target Radar Cross Section (RCS) [m^2]
MU_RADAR = 0.1          # Interference factor from radar probing to comm users

# --- Channel model ---
CHANNEL_MODEL = "v2x"  # "rayleigh" (original, unit square) | "iid" | "v2x"

# --- V2X one-ring channel (SOP.m.txt) ---
C_LIGHT = 299792458.0       # Speed of light [m/s]
FC = 5.9e9                  # Carrier frequency [Hz]
BW = 10e6                   # Bandwidth [Hz]
N_SC = 64                   # Number of OFDM subcarriers
RING_R = 30.0               # Scatterer ring radius around each vehicle [m]
L_SCAT = 100                # Scatterers (rays) per vehicle
AREA_M = 500.0              # Side of the square deployment area [m]
D_MIN = 40.0                # Minimum AP-vehicle distance [m] (> RING_R)
V_USER_KMH = 40.0           # Vehicle speed [km/h]
A_USER = 10.0               # Vehicle acceleration [m/s^2]
T0 = 10e-3                  # Observation interval [s]
D_REF = 100.0               # Reference distance for large-scale gain [m]
SNR_REF_DB = 25.0           # Per-antenna SNR at D_REF (sets beta = rho * pathloss)
