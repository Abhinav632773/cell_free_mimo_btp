# Standalone Cell-Free MIMO & ISAC MATLAB Plotting Suite

This standalone directory contains **complete MATLAB scripts and CSV datasets** for **every plot** in the repository.

Every script in this suite:
- Auto-resolves its directory paths (`fileparts(mfilename('fullpath'))`) so it can be run from **any location** in MATLAB without path errors.
- Automatically generates and saves **native MATLAB `.fig` files** (for interactive zooming, pan, and inspection) as well as publication-ready **300 DPI `.png` images**.
- Loads data directly from portable `.csv` files stored in this folder.

---

## 📁 Plot Scripts & Data Files

| MATLAB Script | Target Plot | CSV Data Source | Output Files Generated |
| :--- | :--- | :--- | :--- |
| **`run_all_plots.m`** | **Master Runner** | *Executes all scripts at once* | *Generates all `.fig` and `.png` below* |
| **`plot_isac_pareto.m`** | ISAC Pareto Trade-off Front | `isac_pareto.csv` | `matlab_isac_pareto.fig`<br>`matlab_isac_pareto.png` |
| **`plot_training_overview.m`** | 2x2 Training Loss & Rates | `training_history.csv` | `matlab_training_overview.fig`<br>`matlab_training_overview.png` |
| **`plot_v2x_acceleration.m`** | V2X Dynamics & Acceleration (2x2) | `v2x_acceleration_data.csv` | `matlab_v2x_acceleration.fig`<br>`matlab_v2x_acceleration.png` |
| **`plot_bench_channels.m`** | Benchmark E1: i.i.d. vs. V2X | `Table2_E1_channels.csv` | `matlab_bench_E1_channels.fig`<br>`matlab_bench_E1_channels.png` |
| **`plot_bench_ageing.m`** | Benchmark E2: CSI Ageing vs. Speed | `Table3_E2_ageing_qnnassignmr.csv`<br>`Table3_E2_ageing_search.csv` | `matlab_bench_E2_ageing.fig`<br>`matlab_bench_E2_ageing.png` |
| **`plot_isac_topology.m`** | ISAC Network Topology & Beams | `isac_topology.csv` | `matlab_isac_topology.fig`<br>`matlab_isac_topology.png` |
| **`SOP.m`** | Full Physics Non-WSSUS V2X Model | *Generates & exports CSV* | `matlab_sop_fig1.fig` to `fig4.fig`<br>`matlab_sop_fig1.png` to `fig4.png` |

---

## 🚀 How to Run in MATLAB

### Method 1: Run All Plots at Once
1. Open MATLAB.
2. In MATLAB's Current Folder panel, navigate to `standalone_plots`.
3. In the Command Window, type:
   ```matlab
   run_all_plots
   ```
   All 6 plots will be generated and saved as `.fig` and `.png` files in seconds.

### Method 2: Run Individual Plots
In the MATLAB Command Window, you can run any individual script:
```matlab
run('plot_v2x_acceleration.m')   % Non-WSSUS V2X acceleration & Doppler
run('plot_isac_pareto.m')        % ISAC Pareto front
run('plot_training_overview.m')  % 2x2 Training progress
run('plot_bench_channels.m')     % Benchmark E1: i.i.d. vs V2X
run('plot_bench_ageing.m')       % Benchmark E2: CSI ageing
run('plot_isac_topology.m')      % ISAC Network layout
```

### Method 3: Using the MATLAB Editor UI
1. Double-click any `.m` file in MATLAB to open it in the Editor.
2. Click the green **Run** button (or press `F5`).
3. If MATLAB asks whether to *"Change Folder"* or *"Add to Path"*, select either option — both will work seamlessly.

---

## 🔍 How to Open and Inspect `.fig` Files in MATLAB

To reopen and interactively explore any generated `.fig` file (e.g. zoom in, pan, click data points):
```matlab
openfig('matlab_v2x_acceleration.fig');
openfig('matlab_isac_pareto.fig');
openfig('matlab_training_overview.fig');
```
Or simply double-click the `.fig` file in MATLAB's file browser.
