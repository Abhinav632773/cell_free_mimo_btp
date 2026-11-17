"""
load_fig.py

Helper script to interactively view and inspect any .fig file saved by the Python plotting scripts.

Usage:
    python load_fig.py                              # opens python_training_overview.fig or python_isac_pareto.fig
    python load_fig.py python_isac_pareto.fig        # opens specified .fig file
    python load_fig.py python_training_overview.fig
"""

import os
import sys
import pickle
import matplotlib.pyplot as plt

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        # Default options to try
        candidates = [
            os.path.join(script_dir, "python_training_overview.fig"),
            os.path.join(script_dir, "python_isac_pareto.fig"),
            "python_training_overview.fig",
            "python_isac_pareto.fig",
        ]
        target = next((c for c in candidates if os.path.exists(c)), None)

    if not target or not os.path.exists(target):
        print("Usage: python load_fig.py <filename.fig>")
        print("Available .fig files in current folder:")
        fig_files = [f for f in os.listdir(script_dir) if f.endswith(".fig")]
        if fig_files:
            for f in fig_files:
                print(f"  - {f}")
        else:
            print("  (No .fig files found yet. Run plot_training_overview.py or plot_isac_pareto.py first!)")
        return

    print(f"[...] Loading figure from: {target}")
    with open(target, "rb") as f:
        fig = pickle.load(f)

    print("[OK] Figure loaded successfully. Displaying interactive window...")
    print("     (You can pan, zoom, resize, or inspect values in this window)")
    plt.show()

if __name__ == "__main__":
    main()

