"""
plot_training_overview.py

Fetches data from: results/training_history.csv
Generates: 2x2 Training Overview (Cloud Loss, Edge Loss, Min Rate, Sum Rate)
Matches the Training Overview plot in the chat screenshot.

Run in VS Code Terminal:
    python plot_training_overview.py
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

# =========================================================================
# 1. EDITABLE PARAMETERS (CUSTOMIZE AXES, LABELS, COLORS, FONTS HERE)
# =========================================================================

# --- File Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_candidate_paths = [
    os.path.join(SCRIPT_DIR, "results", "training_history.csv"),
    os.path.join("results", "training_history.csv"),
    os.path.join(os.path.dirname(SCRIPT_DIR), "final_res", "training_history.csv"),
]
CSV_FILE_PATH   = next((p for p in _candidate_paths if os.path.exists(p)), _candidate_paths[0])
OUTPUT_FIG_PATH = os.path.join(SCRIPT_DIR, "results", "python_training_overview.png")

# --- Figure Window Properties ---
FIG_SIZE   = (12, 8)          # (width, height) in inches
DPI        = 300              # Resolution for saved figure
FONT_FAMILY = "sans-serif"
TITLE_FONT_SIZE = 12
LABEL_FONT_SIZE = 11
TICK_FONT_SIZE  = 10
SUPTITLE_FONT_SIZE = 15

# --- Subplot 1: Cloud QNN Loss (Top-Left) ---
SUB1_COLOR      = "#E63946"   # Vivid Red / Coral
SUB1_LINE_WIDTH = 2.0
SUB1_TITLE      = "Cloud QNN Loss (↓ better)"
SUB1_XLABEL     = "Epoch"
SUB1_YLABEL     = "Cloud Loss (L_assign)"
SUB1_XLIM       = (0, 100)    # Set to None for auto-scale, or (min, max)
SUB1_YLIM       = (0.18, 0.30)# Set to None for auto-scale

# --- Subplot 2: Edge QNN Loss (Top-Right) ---
SUB2_COLOR      = "#2A9D8F"   # Green / Teal
SUB2_LINE_WIDTH = 2.0
SUB2_TITLE      = "Edge QNN Loss (↓ better)"
SUB2_XLABEL     = "Epoch"
SUB2_YLABEL     = "Edge Loss (L_precode)"
SUB2_XLIM       = (0, 100)
SUB2_YLIM       = (0.65, 1.25)

# --- Subplot 3: Minimum User Rate (Bottom-Left) ---
SUB3_COLOR      = "#1D3557"   # Navy Blue
SUB3_LINE_WIDTH = 2.0
SUB3_TITLE      = "Minimum User Rate (↑ better)"
SUB3_XLABEL     = "Epoch"
SUB3_YLABEL     = "Min Rate [bits/s/Hz]"
SUB3_XLIM       = (0, 100)
SUB3_YLIM       = (0.90, 1.35)

# --- Subplot 4: Sum Rate (Bottom-Right) ---
SUB4_COLOR      = "#9D4EDD"   # Purple / Magenta
SUB4_LINE_WIDTH = 2.0
SUB4_TITLE      = "Sum Rate (↑ better)"
SUB4_XLABEL     = "Epoch"
SUB4_YLABEL     = "Sum Rate [bits/s/Hz]"
SUB4_XLIM       = (0, 100)
SUB4_YLIM       = (8.50, 10.20)

# --- Grid Settings ---
ENABLE_GRID      = True
GRID_LINE_STYLE  = ":"        # ':', '--', '-'
GRID_ALPHA       = 0.6


# =========================================================================
# 2. DATA IMPORT & VERIFICATION
# =========================================================================

def main():
    if not os.path.exists(CSV_FILE_PATH):
        searched = "\n  - ".join(_candidate_paths)
        raise FileNotFoundError(
            f"Could not find data file 'training_history.csv'. Searched locations:\n  - {searched}\n"
            "Please ensure the data file exists or run the training/export script first."
        )

    # Read CSV
    df = pd.read_csv(CSV_FILE_PATH)
    
    # Extract columns by position (guarantees compatibility with headers)
    epochs     = df.iloc[:, 0]
    cloud_loss = df.iloc[:, 1]
    edge_loss  = df.iloc[:, 2]
    min_rate   = df.iloc[:, 3]
    sum_rate   = df.iloc[:, 4]

    # =====================================================================
    # 3. PLOTTING (2x2 GRID)
    # =====================================================================
    fig, axes = plt.subplots(2, 2, figsize=FIG_SIZE, dpi=100)
    plt.rcParams["font.family"] = FONT_FAMILY

    # --- Subplot 1: Cloud Loss ---
    ax1 = axes[0, 0]
    ax1.plot(epochs, cloud_loss, color=SUB1_COLOR, linewidth=SUB1_LINE_WIDTH)
    ax1.set_title(SUB1_TITLE, fontsize=TITLE_FONT_SIZE, fontweight="bold")
    ax1.set_xlabel(SUB1_XLABEL, fontsize=LABEL_FONT_SIZE)
    ax1.set_ylabel(SUB1_YLABEL, fontsize=LABEL_FONT_SIZE)
    ax1.tick_params(labelsize=TICK_FONT_SIZE)
    if SUB1_XLIM: ax1.set_xlim(SUB1_XLIM)
    if SUB1_YLIM: ax1.set_ylim(SUB1_YLIM)
    if ENABLE_GRID: ax1.grid(True, linestyle=GRID_LINE_STYLE, alpha=GRID_ALPHA)

    # --- Subplot 2: Edge Loss ---
    ax2 = axes[0, 1]
    ax2.plot(epochs, edge_loss, color=SUB2_COLOR, linewidth=SUB2_LINE_WIDTH)
    ax2.set_title(SUB2_TITLE, fontsize=TITLE_FONT_SIZE, fontweight="bold")
    ax2.set_xlabel(SUB2_XLABEL, fontsize=LABEL_FONT_SIZE)
    ax2.set_ylabel(SUB2_YLABEL, fontsize=LABEL_FONT_SIZE)
    ax2.tick_params(labelsize=TICK_FONT_SIZE)
    if SUB2_XLIM: ax2.set_xlim(SUB2_XLIM)
    if SUB2_YLIM: ax2.set_ylim(SUB2_YLIM)
    if ENABLE_GRID: ax2.grid(True, linestyle=GRID_LINE_STYLE, alpha=GRID_ALPHA)

    # --- Subplot 3: Minimum User Rate ---
    ax3 = axes[1, 0]
    ax3.plot(epochs, min_rate, color=SUB3_COLOR, linewidth=SUB3_LINE_WIDTH)
    ax3.set_title(SUB3_TITLE, fontsize=TITLE_FONT_SIZE, fontweight="bold")
    ax3.set_xlabel(SUB3_XLABEL, fontsize=LABEL_FONT_SIZE)
    ax3.set_ylabel(SUB3_YLABEL, fontsize=LABEL_FONT_SIZE)
    ax3.tick_params(labelsize=TICK_FONT_SIZE)
    if SUB3_XLIM: ax3.set_xlim(SUB3_XLIM)
    if SUB3_YLIM: ax3.set_ylim(SUB3_YLIM)
    if ENABLE_GRID: ax3.grid(True, linestyle=GRID_LINE_STYLE, alpha=GRID_ALPHA)

    # --- Subplot 4: Sum Rate ---
    ax4 = axes[1, 1]
    ax4.plot(epochs, sum_rate, color=SUB4_COLOR, linewidth=SUB4_LINE_WIDTH)
    ax4.set_title(SUB4_TITLE, fontsize=TITLE_FONT_SIZE, fontweight="bold")
    ax4.set_xlabel(SUB4_XLABEL, fontsize=LABEL_FONT_SIZE)
    ax4.set_ylabel(SUB4_YLABEL, fontsize=LABEL_FONT_SIZE)
    ax4.tick_params(labelsize=TICK_FONT_SIZE)
    if SUB4_XLIM: ax4.set_xlim(SUB4_XLIM)
    if SUB4_YLIM: ax4.set_ylim(SUB4_YLIM)
    if ENABLE_GRID: ax4.grid(True, linestyle=GRID_LINE_STYLE, alpha=GRID_ALPHA)

    # Main Super Title
    fig.suptitle("Training Overview", fontsize=SUPTITLE_FONT_SIZE, fontweight="bold")
    plt.tight_layout()

    # =====================================================================
    # 4. EXPORT HIGH-RES IMAGE
    # =====================================================================
    os.makedirs(os.path.dirname(OUTPUT_FIG_PATH), exist_ok=True)
    plt.savefig(OUTPUT_FIG_PATH, dpi=DPI, bbox_inches="tight")
    print(f"[OK] Training Overview saved to: {OUTPUT_FIG_PATH}")
    # plt.show()  # Uncomment if running interactively to pop up window
    plt.close()

if __name__ == "__main__":
    main()
