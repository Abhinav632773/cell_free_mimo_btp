"""
plot_isac_pareto.py

Fetches data from: results/isac_pareto.csv
Generates: ISAC Pareto Trade-off Front (Comm Min Rate vs. Radar Sensing SNR)
Exactly matches the visual comparison in "cell_free_mimo2-mainimagr.jpeg".

Run in VS Code Terminal:
    python plot_isac_pareto.py
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

# =========================================================================
# 1. EDITABLE PARAMETERS (CUSTOMIZE AXES, LABELS, COLORS, ANNOTATIONS HERE)
# =========================================================================

# --- File Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_candidate_paths = [
    os.path.join(SCRIPT_DIR, "results", "isac_pareto.csv"),
    os.path.join("results", "isac_pareto.csv"),
    os.path.join(os.path.dirname(SCRIPT_DIR), "final_res", "isac_pareto.csv"),
]
CSV_FILE_PATH   = next((p for p in _candidate_paths if os.path.exists(p)), _candidate_paths[0])
OUTPUT_FIG_PATH = os.path.join(SCRIPT_DIR, "results", "python_isac_pareto.png")

# --- Figure Window Properties ---
FIG_SIZE   = (9.5, 6.2)       # (width, height) in inches
DPI        = 300              # Resolution for saved figure
FONT_FAMILY = "sans-serif"
TITLE_FONT_SIZE  = 13.5
LABEL_FONT_SIZE  = 12.0
TICK_FONT_SIZE   = 11.0
LEGEND_FONT_SIZE = 11.5
ANNOT_FONT_SIZE  = 10.0

# --- Main Titles & Axis Labels ---
PLOT_TITLE = "ISAC Pareto Trade-off Front: Comm Min Rate vs. Radar Sensing SNR"
X_LABEL    = "Target Radar Echo SNR [dB]"
Y_LABEL    = "Min User Communication Rate [bits/s/Hz]"

# --- Axis Limits & Tick Intervals (Set to None for auto-scale) ---
X_LIMITS = (40.5, 44.7)       # (min, max) for X-axis
Y_LIMITS = (0.4, 3.7)         # (min, max) for Y-axis
X_TICKS  = [40.5, 41.0, 41.5, 42.0, 42.5, 43.0, 43.5, 44.0, 44.5]
Y_TICKS  = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]

# --- Curve 1: Search-based + DFRC ---
C1_NAME        = "Search-based + DFRC"
C1_COLOR       = "#FF8C00"    # Dark Orange (HEX)
C1_MARKER      = "s"          # Square
C1_MARKER_SIZE = 7.5
C1_LINE_WIDTH  = 2.2

# --- Curve 2: QNN + DFRC (Proposed) ---
C2_NAME        = "QNN + DFRC"
C2_COLOR       = "#0000FF"    # Blue (HEX)
C2_MARKER      = "o"          # Circle
C2_MARKER_SIZE = 7.5
C2_LINE_WIDTH  = 2.2

# --- Curve 3: Random + DFRC ---
C3_NAME        = "Random + DFRC"
C3_COLOR       = "#777777"    # Grey (HEX)
C3_MARKER      = "^"          # Triangle Up
C3_MARKER_SIZE = 7.5
C3_LINE_WIDTH  = 2.2

# --- Annotations (eta = 0.0, 0.2, 0.5, 0.85) ---
SHOW_ANNOTATIONS = True
ANNOT_ETAS       = [0.0, 0.2, 0.5, 0.85]

# Custom (dx, dy) offsets for annotations to prevent overlapping
ANNOT_OFFSETS = {
    ("Search", 0.0):  (-0.06,  0.07),
    ("Search", 0.2):  ( 0.01,  0.07),
    ("Search", 0.5):  ( 0.01,  0.07),
    ("Search", 0.85): ( 0.01,  0.07),

    ("QNN", 0.0):     (-0.05,  0.07),
    ("QNN", 0.2):     ( 0.01,  0.07),
    ("QNN", 0.5):     ( 0.02,  0.07),
    ("QNN", 0.85):    ( 0.01,  0.07),

    ("Random", 0.0):  (-0.09,  0.07),
    ("Random", 0.2):  (-0.09,  0.07),
    ("Random", 0.5):  ( 0.01,  0.07),
    ("Random", 0.85): ( 0.01,  0.07),
}

# --- Grid & Legend Settings ---
ENABLE_GRID     = True
GRID_LINE_STYLE = "--"
GRID_ALPHA      = 0.55
LEGEND_LOC      = "upper right"


# =========================================================================
# 2. DATA IMPORT & EXTRACTION
# =========================================================================

def main():
    if not os.path.exists(CSV_FILE_PATH):
        searched = "\n  - ".join(_candidate_paths)
        raise FileNotFoundError(
            f"Could not find data file 'isac_pareto.csv'. Searched locations:\n  - {searched}\n"
            "Please ensure the data file exists or run the simulation/export script first."
        )

    df = pd.read_csv(CSV_FILE_PATH)

    # Columns:
    # 0: Radar Power Ratio (eta)
    # 1: Method
    # 2: Min Comm Rate [bits/s/Hz]
    # 3: Radar Echo SNR [dB]
    # 4: Sensing Rate [bits/s/Hz]

    # Split dataset per method
    df_search = df[df.iloc[:, 1].str.contains("Search", case=False)].copy()
    df_qnn    = df[df.iloc[:, 1].str.contains("QNN", case=False)].copy()
    df_rand   = df[df.iloc[:, 1].str.contains("Random", case=False)].copy()

    # =====================================================================
    # 3. PLOTTING
    # =====================================================================
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=100)
    plt.rcParams["font.family"] = FONT_FAMILY

    # Plot Lines
    line_search, = ax.plot(
        df_search.iloc[:, 3], df_search.iloc[:, 2],
        linestyle="-", color=C1_COLOR, linewidth=C1_LINE_WIDTH,
        marker=C1_MARKER, markersize=C1_MARKER_SIZE, markerfacecolor=C1_COLOR,
        label=C1_NAME, zorder=4
    )

    line_qnn, = ax.plot(
        df_qnn.iloc[:, 3], df_qnn.iloc[:, 2],
        linestyle="-", color=C2_COLOR, linewidth=C2_LINE_WIDTH,
        marker=C2_MARKER, markersize=C2_MARKER_SIZE, markerfacecolor=C2_COLOR,
        label=C2_NAME, zorder=5
    )

    line_rand, = ax.plot(
        df_rand.iloc[:, 3], df_rand.iloc[:, 2],
        linestyle="-", color=C3_COLOR, linewidth=C3_LINE_WIDTH,
        marker=C3_MARKER, markersize=C3_MARKER_SIZE, markerfacecolor=C3_COLOR,
        label=C3_NAME, zorder=3
    )

    # Add Annotations for specific eta values
    if SHOW_ANNOTATIONS:
        for method_key, sub_df, color in [
            ("Search", df_search, C1_COLOR),
            ("QNN", df_qnn, C2_COLOR),
            ("Random", df_rand, C3_COLOR),
        ]:
            for target_eta in ANNOT_ETAS:
                # Find matching row for eta
                matched = sub_df[sub_df.iloc[:, 0].round(2) == round(target_eta, 2)]
                if not matched.empty:
                    x_val = matched.iloc[0, 3]
                    y_val = matched.iloc[0, 2]
                    dx, dy = ANNOT_OFFSETS.get((method_key, target_eta), (0.01, 0.06))
                    ax.text(
                        x_val + dx, y_val + dy,
                        f"η={target_eta}",
                        color=color, fontsize=ANNOT_FONT_SIZE,
                        fontweight="bold", ha="left", va="bottom", zorder=6
                    )

    # Title & Labels
    ax.set_title(PLOT_TITLE, fontsize=TITLE_FONT_SIZE, fontweight="bold", pad=12)
    ax.set_xlabel(X_LABEL, fontsize=LABEL_FONT_SIZE)
    ax.set_ylabel(Y_LABEL, fontsize=LABEL_FONT_SIZE)

    # Axis Limits & Ticks
    if X_LIMITS: ax.set_xlim(X_LIMITS)
    if Y_LIMITS: ax.set_ylim(Y_LIMITS)
    if X_TICKS:  ax.set_xticks(X_TICKS)
    if Y_TICKS:  ax.set_yticks(Y_TICKS)

    ax.tick_params(labelsize=TICK_FONT_SIZE)

    # Grid
    if ENABLE_GRID:
        ax.grid(True, linestyle=GRID_LINE_STYLE, alpha=GRID_ALPHA)

    # Legend
    legend = ax.legend(loc=LEGEND_LOC, fontsize=LEGEND_FONT_SIZE, framealpha=0.92, edgecolor="#CCCCCC")
    legend.get_frame().set_linewidth(1.0)

    plt.tight_layout()

    # =====================================================================
    # 4. EXPORT HIGH-RES IMAGE
    # =====================================================================
    os.makedirs(os.path.dirname(OUTPUT_FIG_PATH), exist_ok=True)
    plt.savefig(OUTPUT_FIG_PATH, dpi=DPI, bbox_inches="tight")
    print(f"[OK] ISAC Pareto plot saved to: {OUTPUT_FIG_PATH}")
    # plt.show()  # Uncomment if running interactively to pop up window
    plt.close()

if __name__ == "__main__":
    main()
