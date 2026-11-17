# train.py
"""
Training Engine for the Multi-Stage QNN Protocol (Algorithm 1).

FIXED VERSION: Uses proper differentiable cost functions
that actually guide the QNNs toward better solutions.
"""

import time
import pennylane as qml
from pennylane import numpy as np
import config
import numpy as onp
from channel import (generate_positions, compute_distances, generate_sample,
                     generate_scenario, generate_scatterers,
                     generate_channel_v2x, channel_to_features)
from rates import (compute_mr_precoding, compute_user_rates,
                   build_precoding_from_assignment)
from cloud_qnn import CloudQNN
from edge_qnn import EdgeQNN


def generate_dataset(N_samples, layout, seed=None, model=None):
    """
    Generate multiple channel samples for training.
    
    Args:
        layout: distances (model "rayleigh") or scenario dict ("iid", "v2x")
        model:  default config.CHANNEL_MODEL
    
    For "v2x" each sample is a new scatterer ring per vehicle at t = 0;
    the rings are kept in sample['scat'] so the same channel can be
    evaluated later in time (CSI ageing).
    """
    model = config.CHANNEL_MODEL if model is None else model
    if seed is not None:
        np.random.seed(seed)
    rng = onp.random.default_rng(seed)
    
    dataset = []
    for i in range(N_samples):
        if model == "v2x":
            scat = generate_scatterers(rng)
            H = generate_channel_v2x(layout, scat)
            dataset.append({'H': H, 'features': channel_to_features(H), 'scat': scat})
        else:
            H, features = generate_sample(layout, model, rng)
            dataset.append({'H': H, 'features': features})
    
    return dataset


def make_layout(model=None, seed=None):
    """
    Network layout for a channel model.
    
    Returns:
        layout: distances (unit square) for "rayleigh", scenario dict otherwise
        ap_pos, user_pos
    """
    model = config.CHANNEL_MODEL if model is None else model
    seed = config.SEED if seed is None else seed
    if model == "rayleigh":
        ap_pos, user_pos = generate_positions(seed=seed)
        return compute_distances(ap_pos, user_pos), ap_pos, user_pos
    scn = generate_scenario(seed)
    return scn, scn['ap_pos'], scn['user_pos']


def compute_ideal_assignment(H):
    """
    Compute the "best" assignment using channel strengths.
    
    This gives us a TARGET for the cloud QNN to learn.
    For each AP, which user has the strongest channel?
    
    Returns target_probs: for each AP, the probability of being |1⟩
    that would correspond to the best user assignment.
    """
    # For each AP, find the best user (strongest channel)
    best_users = []
    for m in range(config.N_AP):
        strengths = [np.linalg.norm(H[(m, k)]) for k in range(config.N_USER)]
        best_user = np.argmax(strengths)
        best_users.append(best_user)
    
    # Convert to target probabilities
    # If AP m should serve user k, target prob = (k + 0.5) / N_USER
    # This maps user index to a probability in [0, 1]
    target_probs = np.array([
        (best_users[m] + 0.5) / config.N_USER 
        for m in range(config.N_AP)
    ])
    
    return target_probs, best_users


def compute_marginal_probs(full_probs, n_qubits):
    """
    From the joint probability distribution,
    compute marginal probability of each qubit being |1⟩.
    
    This is differentiable since it's just summing probabilities!
    """
    marginals = []
    n_states = len(full_probs)
    
    for m in range(n_qubits):
        # Sum probabilities of all states where qubit m is |1⟩
        prob_one = 0.0
        for state_idx in range(n_states):
            if (state_idx >> (n_qubits - 1 - m)) & 1:
                prob_one = prob_one + full_probs[state_idx]
        marginals.append(prob_one)
    
    return marginals


def train(dataset=None, layout=None, n_epoch=None, model=None, verbose=True):
    """
    Main training function implementing Algorithm 1.
    
    Args:
        dataset: training samples (default: N_DATA samples from layout)
        layout:  from make_layout (default: built from model and SEED)
        n_epoch: default n_epoch
        model:   channel model, default config.CHANNEL_MODEL
        verbose: print progress
    """
    log = print if verbose else (lambda *a, **kw: None)
    n_epoch = config.N_EPOCH if n_epoch is None else n_epoch
    
    log("=" * 60)
    log("SETTING UP")
    log("=" * 60)
    
    # Generate network
    if layout is None:
        layout, ap_pos, user_pos = make_layout(model)
    elif isinstance(layout, dict):
        ap_pos, user_pos = layout['ap_pos'], layout['user_pos']
    else:
        ap_pos = user_pos = None
    
    log(f"  Network: {config.N_AP} APs, {config.N_USER} users")
    if not isinstance(layout, dict):
        log(f"  Distances:\n{np.round(layout, 3)}")
    
    # Generate training data
    if dataset is None:
        dataset = generate_dataset(config.N_DATA, layout, seed=config.SEED, model=model)
    log(f"  Training samples: {len(dataset)}")
    log(f"  Epochs: {n_epoch}")
    
    # Initialize QNNs
    cloud = CloudQNN()
    edges = [EdgeQNN(m) for m in range(config.N_AP)]
    
    log(f"\n  Cloud QNN: {cloud.n_qubits} qubits, {cloud.params.size} params")
    log(f"  Edge QNNs: {edges[0].n_qubits} qubits, {edges[0].params.size} params each")
    
    # Pre-compute targets for all training data
    # This tells the QNN what the "correct" assignment should be
    log("\n  Computing training targets...")
    targets = []
    for sample in dataset:
        target_probs, best_users = compute_ideal_assignment(sample['H'])
        targets.append({
            'target_probs': target_probs,
            'best_users': best_users
        })
    
    # Training history
    history = {
        'cloud_loss': [],
        'edge_loss': [],
        'min_rate': [],
        'sum_rate': [],
    }
    
    # =============================================
    # TRAINING LOOP
    # =============================================
    log("\n" + "=" * 60)
    log("TRAINING STARTED")
    log("=" * 60)
    
    total_start = time.time()
    
    for epoch in range(n_epoch):
        epoch_start = time.time()
        
        # Descending learning rate
        lr = config.LR / np.sqrt(epoch + 1)
        
        # Accumulators
        epoch_cloud_loss = []
        epoch_edge_loss = []
        epoch_min_rate = []
        epoch_sum_rate = []
        
        for i_data in range(len(dataset)):
            sample = dataset[i_data]
            H = sample['H']
            H_matrix = sample['features']
            target = targets[i_data]
            target_probs = target['target_probs']
            
            # ========================================
            # PHASE 1: Cloud QNN — Assignment
            # ========================================
            
            cloud_features = cloud.prepare_features(H_matrix)
            
            # The DIFFERENTIABLE cost function
            # We minimize the distance between QNN's marginal probabilities
            # and the target probabilities (ideal assignment)
            def cloud_cost(params):
                """
                Differentiable cost: make QNN output match ideal assignment.
                
                target_probs[m] = ideal probability for AP m
                marginals[m] = QNN's predicted probability for AP m
                
                Cost = sum of (marginal - target)²
                This IS differentiable because marginals are just
                sums of circuit output probabilities!
                """
                full_probs = cloud.circuit(params, cloud_features)
                n_out = min(cloud.n_neurons, config.N_AP)
                
                cost = 0.0
                for m in range(n_out):
                    # Marginal probability of qubit m being |1⟩
                    marginal = 0.0
                    for state_idx in range(len(full_probs)):
                        if (state_idx >> (n_out - 1 - m)) & 1:
                            marginal = marginal + full_probs[state_idx]
                    
                    # Squared error from target
                    cost = cost + (marginal - target_probs[m]) ** 2
                
                return cost
            
            # Compute loss BEFORE update (for monitoring)
            current_loss = float(cloud_cost(cloud.params))
            epoch_cloud_loss.append(current_loss)
            
            # Gradient descent step
            opt_cloud = qml.GradientDescentOptimizer(stepsize=lr)
            cloud.params = opt_cloud.step(cloud_cost, cloud.params)
            
            # Decode assignment for use by edge QNNs
            cloud_output = cloud.forward(cloud_features)
            gamma = cloud.decode_assignment(cloud_output)
            
            # ========================================
            # PHASE 2: Edge QNNs — Precoding
            # ========================================
            
            V_MR = compute_mr_precoding(H)
            edge_losses = []
            V_qnn = {}
            
            for m in range(config.N_AP):
                edge = edges[m]
                edge_features = edge.prepare_features(H)
                
                # Find which user this AP should serve
                assigned = np.where(gamma[m] == 1)[0]
                if len(assigned) == 0:
                    V_qnn[m] = np.zeros(config.N_TX, dtype=complex)
                    continue
                
                k_assigned = assigned[0]
                h_mk = H[(m, k_assigned)]
                
                # Target: MR precoding direction
                # We want the edge QNN to learn to output something
                # close to the MR precoding (or better)
                mr_target = V_MR[(m, k_assigned)]
                
                # Target expectation values for the edge QNN
                # Map MR precoding to target outputs in [-1, 1]
                target_outputs = np.zeros(config.N_USER)
                for j in range(config.N_TX):
                    if 2*j < config.N_USER:
                        target_outputs[2*j] = np.real(mr_target[j])
                    if 2*j+1 < config.N_USER:
                        target_outputs[2*j+1] = np.imag(mr_target[j])
                
                # Differentiable edge cost
                def edge_cost(params, feat=edge_features, 
                            targets=target_outputs, eq=edge):
                    """
                    Make QNN output match MR precoding direction.
                    
                    PauliZ expectation values should match target_outputs.
                    """
                    outputs = eq.circuit(params, feat)
                    cost = 0.0
                    for j in range(len(outputs)):
                        cost = cost + (outputs[j] - targets[j]) ** 2
                    return cost
                
                # Compute loss before update
                e_loss = float(edge_cost(edge.params))
                edge_losses.append(e_loss)
                
                # Gradient descent step
                opt_edge = qml.GradientDescentOptimizer(stepsize=lr)
                edge.params = opt_edge.step(edge_cost, edge.params)
                
                # Get current precoding
                edge_output = edge.forward(edge_features)
                V_qnn[m] = edge.decode_precoding(edge_output)
            
            if edge_losses:
                epoch_edge_loss.append(np.mean(edge_losses))
            
            # ========================================
            # Compute achieved rates
            # ========================================
            V_final = {}
            for m in range(config.N_AP):
                assigned = np.where(gamma[m] == 1)[0]
                if len(assigned) > 0 and m in V_qnn:
                    V_final[m] = V_qnn[m]
                elif len(assigned) > 0:
                    V_final[m] = V_MR[(m, assigned[0])]
                else:
                    V_final[m] = np.zeros(config.N_TX, dtype=complex)
            
            rates = compute_user_rates(H, gamma, V_final)
            epoch_min_rate.append(float(np.min(rates)))
            epoch_sum_rate.append(float(np.sum(rates)))
        
        # ========================================
        # Record epoch statistics
        # ========================================
        avg_cloud = np.mean(epoch_cloud_loss)
        avg_edge = np.mean(epoch_edge_loss) if epoch_edge_loss else 0
        avg_min = np.mean(epoch_min_rate)
        avg_sum = np.mean(epoch_sum_rate)
        
        history['cloud_loss'].append(avg_cloud)
        history['edge_loss'].append(avg_edge)
        history['min_rate'].append(avg_min)
        history['sum_rate'].append(avg_sum)
        
        elapsed = time.time() - epoch_start
        
        if epoch == 0 or (epoch + 1) % max(1, n_epoch // 10) == 0:
            log(f"  Epoch {epoch+1:3d}/{n_epoch}: "
                  f"Cloud Loss={avg_cloud:8.4f}  "
                  f"Edge Loss={avg_edge:8.4f}  "
                  f"Min Rate={avg_min:6.3f}  "
                  f"Sum Rate={avg_sum:6.3f}  "
                  f"({elapsed:.1f}s)")
    
    total_time = time.time() - total_start
    
    log("\n" + "=" * 60)
    log("TRAINING COMPLETE")
    log("=" * 60)
    log(f"  Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    log(f"  Final min rate:   {history['min_rate'][-1]:.4f}")
    log(f"  Final sum rate:   {history['sum_rate'][-1]:.4f}")
    log(f"  Final cloud loss: {history['cloud_loss'][-1]:.4f}")
    log(f"  Final edge loss:  {history['edge_loss'][-1]:.4f}")
    
    return cloud, edges, history, layout, ap_pos, user_pos


if __name__ == "__main__":
    cloud, edges, history, distances, ap_pos, user_pos = train()