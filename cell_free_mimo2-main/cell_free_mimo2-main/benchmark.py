# benchmark.py
"""
Benchmarks for the bug fixes and the V2X channel.
    E1  Channel comparison  i.i.d. Rayleigh vs V2X, same layout and pathloss
    E2  CSI ageing          decide on H(0), evaluate on H(Δ), several speeds (V2X)
    E3  Generalisation      train on i.i.d., test on V2X  vs  train on V2X
    E4  Channel structure   fading depth and beam leakage, i.i.d. vs V2X

Every number is averaged over seeds (one network layout per seed).
All rates are computed with the corrected gain |h^T v|², so legacy and
fixed code are judged by the same metric.

Outputs: results/bench_*.csv, results/bench_*.png, results/SUMMARY.md

Run:  python benchmark.py            (full: 5 seeds, 50 epochs)
      python benchmark.py --quick    (smoke test: 1 seed, 2 epochs)
"""

import os
import sys
import csv
import json
import time
import argparse
import multiprocessing as mp
import numpy as onp

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

os.environ.setdefault("OMP_NUM_THREADS", "1")

import config

RESULTS = "results"
METHODS = ["qnn", "qnn_assign_mr", "search", "strongest", "random"]
METHOD_NAMES = {
    "qnn": "QNN (cloud + edge)",
    "qnn_assign_mr": "QNN assignment + MR",
    "search": "Search-based + MR",
    "strongest": "Strongest channel + MR",
    "random": "Random + MR",
}
DELAYS_MS = [0.0, 0.25, 0.5, 1.0, 2.0, 5.0]
SPEEDS_KMH = [20.0, 40.0, 80.0, 120.0]


# =====================================================================
# Decisions and evaluation
# =====================================================================

def mr_for_assignment(H, gamma):
    from rates import build_precoding_from_assignment
    return build_precoding_from_assignment(H, gamma)


def strongest_assignment(H, cloud):
    """Each AP serves its strongest user; coverage fixed as in the cloud QNN."""
    gamma = onp.zeros((config.N_AP, config.N_USER))
    for m in range(config.N_AP):
        gamma[m, onp.argmax([onp.linalg.norm(H[(m, k)]) for k in range(config.N_USER)])] = 1
    return cloud._enforce_coverage(gamma)


def decide(method, H, features, cloud, edges):
    """Assignment gamma and precoding V from the channel the method sees."""
    from baselines import search_based_assignment, random_assignment

    if method in ("qnn", "qnn_assign_mr"):
        t = time.perf_counter()
        gamma = cloud.decode_assignment(cloud.forward(cloud.prepare_features(features)))
        if method == "qnn_assign_mr":
            return gamma, mr_for_assignment(H, gamma), time.perf_counter() - t
        V = {}
        for m in range(config.N_AP):
            if onp.any(gamma[m] == 1):
                V[m] = edges[m].decode_precoding(edges[m].forward(edges[m].prepare_features(H)))
            else:
                V[m] = onp.zeros(config.N_TX, dtype=complex)
        return gamma, V, time.perf_counter() - t

    t = time.perf_counter()
    if method == "search":
        gamma = search_based_assignment(H)
    elif method == "strongest":
        gamma = strongest_assignment(H, cloud)
    else:
        gamma = random_assignment(H)
    return gamma, mr_for_assignment(H, gamma), time.perf_counter() - t


def evaluate(dataset, cloud, edges, H_eval=None, legacy_gain=False, methods=METHODS):
    """
    Average metrics per method.

    H_eval: optional list of channels to measure rates on (CSI ageing);
            decisions are always made on sample['H'].
    """
    from rates import compute_user_rates

    out = {}
    for method in methods:
        mins, sums, fair, times = [], [], [], []
        for i, sample in enumerate(dataset):
            gamma, V, dt = decide(method, sample['H'], sample['features'], cloud, edges)
            H_rate = sample['H'] if H_eval is None else H_eval[i]
            r = compute_user_rates(H_rate, gamma, V, legacy=legacy_gain)
            mins.append(onp.min(r))
            sums.append(onp.sum(r))
            fair.append(onp.sum(r) ** 2 / (len(r) * onp.sum(r ** 2) + 1e-30))
            times.append(dt)
        out[method] = {
            'min_rate': float(onp.mean(mins)),
            'sum_rate': float(onp.mean(sums)),
            'jain': float(onp.mean(fair)),
            'time_ms': float(onp.mean(times) * 1e3),
        }
    return out


def channel_structure(dataset, layout):
    """
    E4: fading depth and beam leakage, normalized by beta.
        fade_p10:  10th percentile of ||h||²/(beta N_TX)  (deep fades)
        leakage:   mean |h_k^T v_k'|² / (beta N_TX), v_k' = MR beam of another user
    """
    gains, leak = [], []
    for s in dataset:
        H = s['H']
        for m in range(config.N_AP):
            for k in range(config.N_USER):
                b = layout['beta'][m, k] * config.N_TX
                gains.append(onp.linalg.norm(H[(m, k)]) ** 2 / b)
                for k2 in range(config.N_USER):
                    if k2 != k:
                        v = onp.conj(H[(m, k2)]) / onp.linalg.norm(H[(m, k2)])
                        leak.append(onp.abs(onp.dot(H[(m, k)], v)) ** 2 / b)
    return {
        'fade_p10': float(onp.percentile(gains, 10)),
        'fade_mean': float(onp.mean(gains)),
        'leakage': float(onp.mean(leak)),
    }


# =====================================================================
# One training job (runs in a worker process)
# =====================================================================

def run_job(job):
    """
    job: dict(exp, model, legacy, seed, epochs, n_data, n_test)
    Returns a list of result rows.
    """
    config.LEGACY_MODE = job['legacy']
    from train import train, generate_dataset, make_layout
    from channel import generate_channel_v2x

    seed, model = job['seed'], job['model']
    layout, _, _ = make_layout(model, seed)
    train_set = generate_dataset(job['n_data'], layout, seed=seed, model=model)

    t = time.time()
    cloud, edges, history, *_ = train(train_set, layout, n_epoch=job['epochs'],
                                      model=model, verbose=False)
    train_s = time.time() - t
    test = generate_dataset(job['n_test'], layout, seed=seed + 999, model=model)

    rows = []
    base = {'exp': job['exp'], 'seed': seed, 'train_model': model,
            'legacy': job['legacy'], 'train_s': round(train_s, 1),
            'final_cloud_loss': float(history['cloud_loss'][-1])}

    def add(res, **extra):
        for method, metrics in res.items():
            rows.append({**base, **extra, 'method': method, **metrics})

    # Correct metric for everyone
    add(evaluate(test, cloud, edges), test_model=model, metric="correct")

    if job['exp'] == "E0" and job['legacy']:
        # What the old code itself would have printed
        add(evaluate(test, cloud, edges, legacy_gain=True), test_model=model, metric="as_reported")

    if job['exp'] == "E1":
        add({'channel': channel_structure(test, layout)}, test_model=model, metric="structure")

        if model == "iid":
            # E3: same layout, test on V2X
            v2x_test = generate_dataset(job['n_test'], layout, seed=seed + 999, model="v2x")
            add(evaluate(v2x_test, cloud, edges), test_model="v2x", metric="correct")

        if model == "v2x":
            # E2: decide on H(0), evaluate on H(Δ)
            for speed in SPEEDS_KMH:
                for d_ms in DELAYS_MS:
                    H_eval = [generate_channel_v2x(layout, s['scat'], t=d_ms * 1e-3, speed_kmh=speed)
                              for s in test]
                    add(evaluate(test, cloud, edges, H_eval=H_eval,
                                 methods=["qnn", "qnn_assign_mr", "search", "strongest"]),
                        test_model="v2x", metric="ageing", speed_kmh=speed, delay_ms=d_ms)
    return rows


# =====================================================================
# Analysis
# =====================================================================

def stats(rows, **filt):
    """mean, std, values over seeds for rows matching filt (one per seed)."""
    vals = {}
    for r in rows:
        if all(r.get(k) == v for k, v in filt.items()):
            vals[r['seed']] = r
    return vals


def mean_std(rows, key, **filt):
    v = [r[key] for r in stats(rows, **filt).values()]
    return (float(onp.mean(v)), float(onp.std(v)), v) if v else (onp.nan, onp.nan, [])


def paired_test(a, b):
    """Paired t-test p-value (two-sided); nan if fewer than 2 seeds."""
    if len(a) < 2:
        return onp.nan
    from scipy.stats import ttest_rel
    d = onp.array(b) - onp.array(a)
    if onp.allclose(d, d[0]):
        return 0.0 if d[0] != 0 else 1.0
    return float(ttest_rel(b, a).pvalue)


def fmt(m, s):
    return f"{m:.3f} ± {s:.3f}"


def summarize(rows, validation, args):
    lines = ["# Benchmark summary", "",
             f"Seeds: {args.seeds}, epochs: {args.epochs}, training samples: {args.n_data}, "
             f"test samples: {args.n_test} per seed. Values are mean ± std over seeds. "
             f"All rates in bits/s/Hz with the corrected gain |hᵀv|².", ""]
    claims = []

    # ---------------- E0 ----------------
    lines += ["## E0 — Bug fixes (original Rayleigh channel)", "",
              "| Method | Legacy code | Fixed code |", "|---|---|---|"]
    for meth in METHODS:
        a = mean_std(rows, 'min_rate', exp="E0", legacy=True, method=meth, metric="correct")
        b = mean_std(rows, 'min_rate', exp="E0", legacy=False, method=meth, metric="correct")
        lines.append(f"| {METHOD_NAMES[meth]} (min rate) | {fmt(a[0], a[1])} | {fmt(b[0], b[1])} |")
    rep = mean_std(rows, 'min_rate', exp="E0", legacy=True, method="qnn", metric="as_reported")
    cor = mean_std(rows, 'min_rate', exp="E0", legacy=True, method="qnn", metric="correct")
    lines += ["", f"Old code's own printout of the QNN min rate (wrong gain formula): "
                  f"{fmt(rep[0], rep[1])}; with the correct formula: {fmt(cor[0], cor[1])}.", ""]

    for meth in ["qnn", "qnn_assign_mr"]:
        a = mean_std(rows, 'min_rate', exp="E0", legacy=True, method=meth, metric="correct")
        b = mean_std(rows, 'min_rate', exp="E0", legacy=False, method=meth, metric="correct")
        p = paired_test(a[2], b[2])
        change = (b[0] - a[0]) / abs(a[0]) * 100 if a[0] else onp.nan
        if change > 0 and p < 0.05:
            claims.append(f"**Bug fixes improved the {METHOD_NAMES[meth]} min rate by {change:.1f}%** "
                          f"({a[0]:.3f} → {b[0]:.3f} bits/s/Hz, paired t-test p = {p:.3g}).")
        else:
            claims.append(f"Bug fixes changed the {METHOD_NAMES[meth]} min rate by {change:+.1f}% "
                          f"({a[0]:.3f} → {b[0]:.3f}), p = {p:.3g}: **not a significant improvement**.")

    # ---------------- E1 ----------------
    lines += ["## E1 — i.i.d. Rayleigh vs V2X (same layout and pathloss, fixed code)", "",
              "| Method | Min rate i.i.d. | Min rate V2X | Sum rate i.i.d. | Sum rate V2X | Jain V2X | Decision time [ms] |",
              "|---|---|---|---|---|---|---|"]
    for meth in METHODS:
        mi = mean_std(rows, 'min_rate', exp="E1", train_model="iid", test_model="iid", method=meth, metric="correct")
        mv = mean_std(rows, 'min_rate', exp="E1", train_model="v2x", test_model="v2x", method=meth, metric="correct")
        si = mean_std(rows, 'sum_rate', exp="E1", train_model="iid", test_model="iid", method=meth, metric="correct")
        sv = mean_std(rows, 'sum_rate', exp="E1", train_model="v2x", test_model="v2x", method=meth, metric="correct")
        jv = mean_std(rows, 'jain', exp="E1", train_model="v2x", test_model="v2x", method=meth, metric="correct")
        tv = mean_std(rows, 'time_ms', exp="E1", train_model="v2x", test_model="v2x", method=meth, metric="correct")
        lines.append(f"| {METHOD_NAMES[meth]} | {fmt(*mi[:2])} | {fmt(*mv[:2])} | "
                     f"{fmt(*si[:2])} | {fmt(*sv[:2])} | {jv[0]:.3f} | {tv[0]:.2f} |")
    lines.append("")

    def ratio(train_model, test_model, meth):
        q = stats(rows, exp="E1", train_model=train_model, test_model=test_model, method=meth, metric="correct")
        s = stats(rows, exp="E1", train_model=train_model, test_model=test_model, method="search", metric="correct")
        return [q[k]['min_rate'] / s[k]['min_rate'] * 100 for k in q if k in s and s[k]['min_rate'] > 0]

    for meth in ["qnn", "qnn_assign_mr"]:
        ri, rv = ratio("iid", "iid", meth), ratio("v2x", "v2x", meth)
        if ri and rv:
            drop = onp.mean(ri) - onp.mean(rv)
            verdict = "robust" if drop < 5 else ("moderately affected" if drop <= 15 else "degrades")
            lines.append(f"- {METHOD_NAMES[meth]} reaches **{onp.mean(ri):.1f}%** of search-based min rate on "
                         f"i.i.d. and **{onp.mean(rv):.1f}%** on V2X.")
            claims.append(f"{METHOD_NAMES[meth]} reaches {onp.mean(ri):.1f}% (i.i.d.) vs {onp.mean(rv):.1f}% (V2X) "
                          f"of the search-based min rate → change of {-drop:+.1f} points: **{verdict}** "
                          f"on the realistic channel.")
    lines.append("")

    # ---------------- E2 ----------------
    lines += ["## E2 — CSI ageing on V2X (decision on H(0), rates on H(Δ))", "",
              "Min rate (mean over seeds):", ""]
    lifetimes = {}
    
    def life_str(d):
        return f"{d:g} ms" if d > 0 else f"< {DELAYS_MS[1]:g} ms"
    
    for meth in ["qnn_assign_mr", "search", "qnn"]:
        lines += [f"**{METHOD_NAMES[meth]}**", "",
                  "| Speed \\ Δ [ms] | " + " | ".join(f"{d:g}" for d in DELAYS_MS) + " | Lifetime (≥90%) |",
                  "|---|" + "---|" * (len(DELAYS_MS) + 1)]
        for sp in SPEEDS_KMH:
            vals = [mean_std(rows, 'min_rate', exp="E1", metric="ageing", method=meth,
                             speed_kmh=sp, delay_ms=d)[0] for d in DELAYS_MS]
            # largest Δ such that every Δ up to it keeps ≥ 90%
            life = 0.0
            for d, v in zip(DELAYS_MS, vals):
                if v >= 0.9 * vals[0]:
                    life = d
                else:
                    break
            lifetimes[(meth, sp)] = life
            lines.append(f"| {sp:g} km/h | " + " | ".join(f"{v:.3f}" for v in vals) + f" | {life_str(life)} |")
        lines.append("")
    for meth in ["qnn_assign_mr", "search"]:
        claims.append(f"{METHOD_NAMES[meth]}: a decision stays within 90% of its fresh min rate for "
                      + ", ".join(f"{life_str(lifetimes[(meth, sp)])} at {sp:g} km/h" for sp in SPEEDS_KMH)
                      + f" → at 40 km/h the cloud should re-decide every {life_str(lifetimes[(meth, 40.0)])} "
                        f"(grid resolution: {', '.join(f'{d:g}' for d in DELAYS_MS)} ms).")

    # ---------------- E3 ----------------
    lines += ["## E3 — Generalisation (tested on V2X)", "",
              "| Method | Trained on i.i.d. | Trained on V2X |", "|---|---|---|"]
    for meth in ["qnn", "qnn_assign_mr"]:
        a = mean_std(rows, 'min_rate', exp="E1", train_model="iid", test_model="v2x", method=meth, metric="correct")
        b = mean_std(rows, 'min_rate', exp="E1", train_model="v2x", test_model="v2x", method=meth, metric="correct")
        lines.append(f"| {METHOD_NAMES[meth]} | {fmt(*a[:2])} | {fmt(*b[:2])} |")
        g = (b[0] - a[0]) / abs(a[0]) * 100 if a[0] else onp.nan
        p = paired_test(a[2], b[2])
        sig = "significant" if p < 0.05 else "not significant"
        claims.append(f"Training {METHOD_NAMES[meth]} on V2X instead of i.i.d. data changes its V2X min rate by "
                      f"{g:+.1f}% (p = {p:.3g}, {sig}).")
    lines.append("")

    # ---------------- E4 + validation ----------------
    lines += ["## E4 — Channel structure (normalized by large-scale gain)", "",
              "| | i.i.d. | V2X |", "|---|---|---|"]
    for key, name in [('fade_mean', "Mean ‖h‖²/(β·N_TX)"), ('fade_p10', "10th percentile (deep fades)"),
                      ('leakage', "Beam leakage to other users")]:
        a = mean_std(rows, key, exp="E1", train_model="iid", method="channel", metric="structure")
        b = mean_std(rows, key, exp="E1", train_model="v2x", method="channel", metric="structure")
        lines.append(f"| {name} | {a[0]:.3f} | {b[0]:.3f} |")
    lines += ["", "## Channel validation (validate_channel.py)", "", "```",
              json.dumps(validation, indent=2), "```", ""]
    claims.append(f"The V2X channel reproduces the SOP.m physics: antenna correlation "
                  f"{validation['antenna_corr_v2x']:.2f} (i.i.d.: {validation['antenna_corr_iid']:.2f}), "
                  f"time correlation follows Clarke's J0 (coherence ≈ {validation['coherence_time_ms']:.1f} ms "
                  f"at {config.V_USER_KMH:g} km/h), delay spread {validation['delay_spread_max_ns']:.0f} ns.")

    lines = ["# Benchmark summary", "", "## Claims derived from the numbers", ""] + \
            [f"{i + 1}. {c}" for i, c in enumerate(claims)] + [""] + lines[2:]
    with open(os.path.join(RESULTS, "SUMMARY.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
    print("\n".join(lines[:len(claims) + 4]))


def plot(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # E1 bar chart
    fig, ax = plt.subplots(figsize=(8, 4))
    x = onp.arange(len(METHODS))
    for i, (tm, label) in enumerate([("iid", "i.i.d. Rayleigh"), ("v2x", "V2X one-ring")]):
        ms = [mean_std(rows, 'min_rate', exp="E1", train_model=tm, test_model=tm, method=m, metric="correct")
              for m in METHODS]
        ax.bar(x + (i - 0.5) * 0.38, [a[0] for a in ms], 0.38, yerr=[a[1] for a in ms], label=label, capsize=3)
    ax.set_xticks(x, [METHOD_NAMES[m] for m in METHODS], rotation=20, ha="right")
    ax.set_ylabel("Avg min rate [bits/s/Hz]")
    ax.set_title("E1: same layout, different small-scale channel")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "bench_E1_channels.png"), dpi=150)
    plt.close(fig)

    # E2 ageing
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, meth in zip(axes, ["qnn_assign_mr", "search"]):
        for sp in SPEEDS_KMH:
            vals = [mean_std(rows, 'min_rate', exp="E1", metric="ageing", method=meth,
                             speed_kmh=sp, delay_ms=d)[0] for d in DELAYS_MS]
            ax.plot(DELAYS_MS, vals, marker="o", label=f"{sp:g} km/h")
        ax.set(xlabel="Decision delay Δ [ms]", title=METHOD_NAMES[meth])
        ax.grid(True)
    axes[0].set_ylabel("Avg min rate [bits/s/Hz]")
    axes[0].legend()
    fig.suptitle("E2: CSI ageing on the V2X channel")
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS, "bench_E2_ageing.png"), dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--n-data", type=int, default=config.N_DATA)
    ap.add_argument("--n-test", type=int, default=50)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()
    if args.quick:
        args.seeds, args.epochs, args.n_data, args.n_test = 1, 2, 10, 5
    os.makedirs(RESULTS, exist_ok=True)

    import validate_channel
    print("Channel validation...")
    validation = validate_channel.main(RESULTS)

    common = {'epochs': args.epochs, 'n_data': args.n_data, 'n_test': args.n_test}
    jobs = []
    for seed in range(args.seeds):
        jobs += [{**common, 'exp': "E0", 'model': "rayleigh", 'legacy': lg, 'seed': seed} for lg in (True, False)]
        jobs += [{**common, 'exp': "E1", 'model': md, 'legacy': False, 'seed': seed} for md in ("iid", "v2x")]

    print(f"\nRunning {len(jobs)} training jobs on {args.workers} workers...")
    t = time.time()
    # "fork" is Linux/macOS only; use "spawn" on Windows
    ctx = "fork" if os.name != "nt" else "spawn"
    with mp.get_context(ctx).Pool(args.workers) as pool:
        rows = [r for res in pool.imap_unordered(run_job, jobs) for r in res]
    print(f"  done in {(time.time() - t) / 60:.1f} min")

    keys = sorted({k for r in rows for k in r})
    with open(os.path.join(RESULTS, "bench_results.csv"), "w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    plot(rows)
    summarize(rows, validation, args)


if __name__ == "__main__":
    mp.freeze_support()   # needed for Windows spawn + PyInstaller
    main()
