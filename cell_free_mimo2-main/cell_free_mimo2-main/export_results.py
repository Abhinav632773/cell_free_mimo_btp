# export_results.py
"""
Reads the already-completed bench_results.csv and SUMMARY.md and exports
ALL results into editable formats:
  - results/editable_results.xlsx  (Excel with multiple sheets)
  - results/Table1_E0_bugfix.csv
  - results/Table2_E1_channels.csv
  - results/Table3_E2_ageing_qnn_mr.csv
  - results/Table3_E2_ageing_search.csv
  - results/Table3_E2_ageing_qnn.csv
  - results/Table4_E3_generalisation.csv
  - results/Table5_E4_channel_structure.csv
  - results/Table6_channel_validation.csv
  - results/Table7_training_history.csv  (placeholder)

Run: python export_results.py
"""

import csv
import json
import os
import numpy as np

RESULTS = "results"
CSV_PATH = os.path.join(RESULTS, "bench_results.csv")

METHOD_NAMES = {
    "qnn":          "QNN (cloud + edge)",
    "qnn_assign_mr":"QNN assignment + MR",
    "search":       "Search-based + MR",
    "strongest":    "Strongest channel + MR",
    "random":       "Random + MR",
    "channel":      "Channel structure",
}

DELAYS_MS  = [0.0, 0.25, 0.5, 1.0, 2.0, 5.0]
SPEEDS_KMH = [20.0, 40.0, 80.0, 120.0]
METHODS    = ["qnn", "qnn_assign_mr", "search", "strongest", "random"]


# ── helpers ──────────────────────────────────────────────────────────────────

def load_rows():
    with open(CSV_PATH, newline="") as f:
        return list(csv.DictReader(f))

def flt(s):
    try: return float(s)
    except: return None

def match(row, **kw):
    for k, v in kw.items():
        rv = row.get(k, "")
        # cast to same type for comparison
        if isinstance(v, bool):
            rv = rv.lower() in ("true", "1", "yes")
        elif isinstance(v, float):
            try: rv = float(rv)
            except: rv = None
        if rv != v:
            return False
    return True

def mean_std(rows, key, **filt):
    vals = [flt(r[key]) for r in rows if match(r, **filt) and flt(r[key]) is not None]
    if not vals:
        return float("nan"), float("nan")
    return float(np.mean(vals)), float(np.std(vals))

def fmt(m, s):
    if np.isnan(m): return "N/A"
    return f"{m:.3f} ± {s:.3f}"


# ── write helpers ─────────────────────────────────────────────────────────────

def write_csv(path, headers, rows_data):
    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows_data)
        print(f"  Saved: {path}")
    except PermissionError:
        print(f"  [LOCKED] Cannot overwrite {path} (it is open in another program, e.g. Excel). Close it to overwrite.")


# ── Table 1: E0 Bug Fix ───────────────────────────────────────────────────────

def make_table1(rows):
    headers = ["Method", "Legacy Code (mean ± std)", "Fixed Code (mean ± std)", "Change (%)"]
    data = []
    for meth in METHODS:
        leg = mean_std(rows, "min_rate", exp="E0", legacy="True",  method=meth, metric="correct")
        fix = mean_std(rows, "min_rate", exp="E0", legacy="False", method=meth, metric="correct")
        if not np.isnan(leg[0]) and leg[0] != 0:
            chg = (fix[0] - leg[0]) / abs(leg[0]) * 100
            chg_str = f"{chg:+.1f}%"
        else:
            chg_str = "N/A"
        data.append([METHOD_NAMES[meth], fmt(*leg), fmt(*fix), chg_str])
    write_csv(os.path.join(RESULTS, "Table1_E0_bugfix.csv"), headers, data)
    return headers, data


# ── Table 2: E1 Channel Comparison ──────────────────────────────────────────

def make_table2(rows):
    headers = ["Method", "Min Rate i.i.d.", "Min Rate V2X",
               "Sum Rate i.i.d.", "Sum Rate V2X", "Jain Index V2X", "Decision Time ms V2X"]
    data = []
    for meth in METHODS:
        mi  = mean_std(rows, "min_rate",  exp="E1", train_model="iid", test_model="iid", method=meth, metric="correct")
        mv  = mean_std(rows, "min_rate",  exp="E1", train_model="v2x", test_model="v2x", method=meth, metric="correct")
        si  = mean_std(rows, "sum_rate",  exp="E1", train_model="iid", test_model="iid", method=meth, metric="correct")
        sv  = mean_std(rows, "sum_rate",  exp="E1", train_model="v2x", test_model="v2x", method=meth, metric="correct")
        jv  = mean_std(rows, "jain",      exp="E1", train_model="v2x", test_model="v2x", method=meth, metric="correct")
        tv  = mean_std(rows, "time_ms",   exp="E1", train_model="v2x", test_model="v2x", method=meth, metric="correct")
        data.append([METHOD_NAMES[meth], fmt(*mi), fmt(*mv), fmt(*si), fmt(*sv),
                     f"{jv[0]:.3f}" if not np.isnan(jv[0]) else "N/A",
                     f"{tv[0]:.2f}" if not np.isnan(tv[0]) else "N/A"])
    write_csv(os.path.join(RESULTS, "Table2_E1_channels.csv"), headers, data)
    return headers, data


# ── Table 3: E2 CSI Ageing ───────────────────────────────────────────────────

def make_table3(rows, meth):
    delay_headers = [f"{d:g} ms" for d in DELAYS_MS]
    headers = ["Speed (km/h)"] + delay_headers + ["Lifetime (>=90%)"]
    data = []
    for sp in SPEEDS_KMH:
        vals = [mean_std(rows, "min_rate", exp="E1", metric="ageing", method=meth,
                         speed_kmh=sp, delay_ms=d)[0]
                for d in DELAYS_MS]
        # compute lifetime
        life = 0.0
        base = vals[0] if vals else 1.0
        for d, v in zip(DELAYS_MS, vals):
            if not np.isnan(v) and base > 0 and v >= 0.9 * base:
                life = d
            else:
                break
        life_str = f"{life:g} ms" if life > 0 else f"< {DELAYS_MS[1]:g} ms"
        data.append([f"{sp:g}"] + [f"{v:.3f}" if not np.isnan(v) else "N/A" for v in vals] + [life_str])

    slug = meth.replace("_", "")
    path = os.path.join(RESULTS, f"Table3_E2_ageing_{slug}.csv")
    write_csv(path, headers, data)
    return headers, data, path


# ── Table 4: E3 Generalisation ───────────────────────────────────────────────

def make_table4(rows):
    headers = ["Method", "Trained on i.i.d. (V2X test)", "Trained on V2X (V2X test)", "Change (%)"]
    data = []
    for meth in ["qnn", "qnn_assign_mr"]:
        a = mean_std(rows, "min_rate", exp="E1", train_model="iid", test_model="v2x", method=meth, metric="correct")
        b = mean_std(rows, "min_rate", exp="E1", train_model="v2x", test_model="v2x", method=meth, metric="correct")
        chg = (b[0] - a[0]) / abs(a[0]) * 100 if not np.isnan(a[0]) and a[0] != 0 else float("nan")
        data.append([METHOD_NAMES[meth], fmt(*a), fmt(*b),
                     f"{chg:+.1f}%" if not np.isnan(chg) else "N/A"])
    write_csv(os.path.join(RESULTS, "Table4_E3_generalisation.csv"), headers, data)
    return headers, data


# ── Table 5: E4 Channel Structure ────────────────────────────────────────────

def make_table5(rows):
    headers = ["Metric", "i.i.d. Rayleigh", "V2X One-Ring"]
    metrics = [
        ("fade_mean", "Mean ||h||² / (β·N_TX)"),
        ("fade_p10",  "10th percentile (deep fades)"),
        ("leakage",   "Beam leakage to other users"),
    ]
    data = []
    for key, name in metrics:
        ai = mean_std(rows, key, exp="E1", train_model="iid", method="channel", metric="structure")
        av = mean_std(rows, key, exp="E1", train_model="v2x", method="channel", metric="structure")
        data.append([name,
                     f"{ai[0]:.3f}" if not np.isnan(ai[0]) else "N/A",
                     f"{av[0]:.3f}" if not np.isnan(av[0]) else "N/A"])
    write_csv(os.path.join(RESULTS, "Table5_E4_channel_structure.csv"), headers, data)
    return headers, data


# ── Table 6: Channel Validation ──────────────────────────────────────────────

def make_table6():
    val_path = os.path.join(RESULTS, "channel_validation.json")
    if not os.path.exists(val_path):
        print(f"  SKIP Table6: {val_path} not found.")
        return
    with open(val_path) as f:
        v = json.load(f)
    headers = ["Property", "Measured Value", "Status"]
    data = [
        ["Power ratio mean",            f"{v.get('power_ratio_mean', 'N/A'):.4f}", "OK" if v.get("power_ratio_ok") else "FAIL"],
        ["Antenna correlation (V2X)",   f"{v.get('antenna_corr_v2x', 'N/A'):.4f}", "—"],
        ["Antenna correlation (i.i.d)", f"{v.get('antenna_corr_iid', 'N/A'):.4f}", "—"],
        ["Max Doppler [Hz]",            f"{v.get('f_max_hz', 'N/A'):.2f}",          "OK" if v.get("doppler_ok") else "FAIL"],
        ["Coherence time [ms]",         f"{v.get('coherence_time_ms', 'N/A'):.3f}", "—"],
        ["Delay spread max [ns]",       f"{v.get('delay_spread_max_ns', 'N/A'):.1f}","OK" if v.get("delay_ok") else "FAIL"],
        ["Median link SNR [dB]",        f"{v.get('median_link_snr_db', 'N/A'):.2f}", "—"],
    ]
    write_csv(os.path.join(RESULTS, "Table6_channel_validation.csv"), headers, data)


# ── Excel export (openpyxl if available) ─────────────────────────────────────

def try_excel(all_tables):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("\n  [INFO] openpyxl not installed — skipping Excel export.")
        print("         Install with:  pip install openpyxl")
        print("         Then re-run:   python export_results.py")
        return

    wb = openpyxl.Workbook()
    wb.remove(wb.active)   # remove default blank sheet

    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(bold=True, color="FFFFFF")
    alt_fill    = PatternFill("solid", fgColor="D6E4F0")

    for sheet_name, headers, rows_data in all_tables:
        ws = wb.create_sheet(title=sheet_name[:31])  # Excel sheet name limit
        # Header row
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font  = header_font
            cell.fill  = header_fill
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
        # Data rows
        for ri, row in enumerate(rows_data, 2):
            fill = alt_fill if ri % 2 == 0 else None
            for col, val in enumerate(row, 1):
                cell = ws.cell(row=ri, column=col, value=val)
                cell.alignment = Alignment(horizontal="center")
                if fill:
                    cell.fill = fill
        # Auto column width
        for col in ws.columns:
            max_len = max((len(str(c.value or "")) for c in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    path = os.path.join(RESULTS, "editable_results.xlsx")
    try:
        wb.save(path)
        print(f"\n  [OK] Excel saved: {path}")
        print("     Open in Excel / LibreOffice Calc / Google Sheets (File -> Import)")
    except PermissionError:
        alt_path = os.path.join(RESULTS, "editable_results_new.xlsx")
        wb.save(alt_path)
        print(f"\n  [NOTICE] editable_results.xlsx is locked in Excel, saved copy as: {alt_path}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("EXPORTING RESULTS TO EDITABLE FORMATS")
    print("=" * 55)

    if not os.path.exists(CSV_PATH):
        print(f"\n  ERROR: {CSV_PATH} not found.")
        print("  Run  python benchmark.py  first to generate it.")
        return

    rows = load_rows()
    print(f"  Loaded {len(rows)} rows from bench_results.csv\n")

    os.makedirs(RESULTS, exist_ok=True)

    # ── CSVs ──
    print("[ CSVs ]")
    h1, d1 = make_table1(rows)
    h2, d2 = make_table2(rows)
    _, d3a, _ = make_table3(rows, "qnn_assign_mr")
    h3, d3b, _ = make_table3(rows, "search")
    _, d3c, _ = make_table3(rows, "qnn")
    h4, d4 = make_table4(rows)
    h5, d5 = make_table5(rows)
    make_table6()

    # ── Excel ──
    print("\n[ Excel ]")
    ageing_headers = ["Speed (km/h)"] + [f"{d:g} ms" for d in DELAYS_MS] + ["Lifetime (>=90%)"]
    all_tables = [
        ("E0 Bug Fix",             h1,             d1),
        ("E1 Channel Comparison",  h2,             d2),
        ("E2 Ageing - QNN+MR",    ageing_headers,  d3a),
        ("E2 Ageing - Search+MR", ageing_headers,  d3b),
        ("E2 Ageing - QNN",       ageing_headers,  d3c),
        ("E3 Generalisation",      h4,             d4),
        ("E4 Channel Structure",   h5,             d5),
    ]

    # Include ISAC and training history if available
    for fname, sheet_title in [
        ("isac_summary.csv", "ISAC Summary"),
        ("isac_pareto.csv", "ISAC Pareto Front"),
        ("training_history.csv", "Training History"),
    ]:
        p = os.path.join(RESULTS, fname)
        if os.path.exists(p):
            with open(p, newline='', encoding='utf-8-sig') as f:
                rdr = list(csv.reader(f))
                if rdr:
                    all_tables.append((sheet_title, rdr[0], rdr[1:]))

    try_excel(all_tables)

    print("\n" + "=" * 55)
    print("FILES SAVED IN:  results/")
    print("=" * 55)
    print("  Table1_E0_bugfix.csv")
    print("  Table2_E1_channels.csv")
    print("  Table3_E2_ageing_qnnassignmr.csv")
    print("  Table3_E2_ageing_search.csv")
    print("  Table3_E2_ageing_qnn.csv")
    print("  Table4_E3_generalisation.csv")
    print("  Table5_E4_channel_structure.csv")
    print("  Table6_channel_validation.csv")
    print("  editable_results.xlsx  (if openpyxl installed)")


if __name__ == "__main__":
    main()
