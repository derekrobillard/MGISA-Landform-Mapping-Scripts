# ------------------------------------------------------------------------
# Title: violinplots_segmentlevel_MEAN_byclass.py  (original: Plot_Violin_SegmentLevel_ByClass_MEAN_v9_99thPerc_SchemaD_legend.py)
# Author: Derek Robillard, with OpenAI assistance
# Purpose: Produce a grid of violin plots showing segment-level GV means by landform class (Schema D),
#          with a compact legend panel suitable for letter-layout figures.
# Notes: Snapshot of the script used for the MGISA final report (Schema D: no TERRACE class).
#        Logic unchanged; only file paths and output filename generalized.
# Inputs: Update 'csv_path' to your merged segment-stats CSV (must include NameD and *_MEAN fields).
# Outputs: 'ViolinPlots_SegmentStats_ByClass_MEAN_SchemaD.png' written next to the CSV by default.
# Citation: Robillard (2025). *MGISA landform mapping scripts* [Computer software]. GitHub. 
# ------------------------------------------------------------------------

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import patches  # for colored squares
import os

# -------------------------------------------------------------------------
# STEP 1: File Paths (EDIT THIS)
# -------------------------------------------------------------------------
# Path to CSV table with segment-level stats (should include: NameD, TPI1_MEAN, TPI2_MEAN, Slope_MEAN,
# SRI_MEAN, CurvT_MEAN, CurvPr_MEAN, Elev_MEAN)
csv_path = r"C:\path\to\Outputs\Toba_SegmentStats_SMSv7_MERGED.csv"  # <-- replace with your CSV

# Output figure path (defaults to same folder as CSV)
output_path = os.path.join(
    os.path.dirname(csv_path),
    "ViolinPlots_SegmentStats_ByClass_MEAN_SchemaD.png"
)

# -------------------------------------------------------------------------
# STEP 2: Load Data
# -------------------------------------------------------------------------
df = pd.read_csv(csv_path)
name_col = "NameD" if "NameD" in df.columns else "NameB" #NameD reflect Schema D class name
if name_col not in df.columns:
    raise ValueError("Required field with class names ('NameD' or 'NameB') not found in input CSV.")

# -------------------------------------------------------------------------
# STEP 3: Schema D classes, short labels, colors
# -------------------------------------------------------------------------
class_order_full = [  # (Schema D) TERRACE removed
    "WATER BODY", "SMOOTH SNOW/ICEFIELD", "CREVASSE-RICH ICE",
    "RIDGE", "FAN", "SEDIMENTARY SLOPE UNIT", "NON-STEEP BSU",
    "STEEP BSU", "INCISED CHANNEL", "VALLEY BOTTOM"
]

# Short forms for y-axis
label_map = {
    "WATER BODY": "WB",
    "SMOOTH SNOW/ICEFIELD": "SI-S",
    "CREVASSE-RICH ICE": "SI-C",
    "RIDGE": "R",
    "FAN": "F",
    "SEDIMENTARY SLOPE UNIT": "SSU",
    "NON-STEEP BSU": "BSU-NS",
    "STEEP BSU": "BSU-S",
    "INCISED CHANNEL": "IC",
    "VALLEY BOTTOM": "VB",
}
order_short = [label_map[c] for c in class_order_full]

# Preferred LONG labels for legend
legend_long = {
    "WB": "WATER BODY",
    "SI-S": "SNOW/ICE - SMOOTH",
    "SI-C": "SNOW/ICE - CREVASSED",
    "R": "RIDGE",
    "F": "FAN",
    "SSU": "SEDIMENTARY SLOPE UNIT",
    "BSU-NS": "BEDROCK - NON-STEEP",
    "BSU-S": "BEDROCK - STEEP",
    "IC": "INCISED CHANNEL",
    "VB": "VALLEY BOTTOM",
}

# Colors (mapped from original full names)
class_colors_full = {
    "WATER BODY": "#0070FF",
    "SMOOTH SNOW/ICEFIELD": "#B4D9F5",
    "CREVASSE-RICH ICE": "#F19DFE",
    "RIDGE": "#D1007C",
    "FAN": "#A8E33A",
    "SEDIMENTARY SLOPE UNIT": "#9A845F",
    "NON-STEEP BSU": "#555555",
    "STEEP BSU": "#2A2A2A",
    "INCISED CHANNEL": "#23C900",
    "VALLEY BOTTOM": "#63D2BA",
}
short_colors = {label_map[k]: v for k, v in class_colors_full.items()}

# Keep only Schema D rows and add short label column
df = df[df[name_col].isin(class_order_full)].copy()
df["LabelShort"] = df[name_col].map(label_map)

# -------------------------------------------------------------------------
# STEP 4: Variables and grid
# -------------------------------------------------------------------------
gv_fields = ["TPI1_MEAN", "TPI2_MEAN", "Slope_MEAN", "SRI_MEAN",
             "CurvT_MEAN", "CurvPr_MEAN", "Elev_MEAN"]
subplot_titles = [field.replace("_MEAN", "") for field in gv_fields]

# -------------------------------------------------------------------------
# STEP 5: Clip 1st–99th percentiles (to eliminate outliers from plots)
# -------------------------------------------------------------------------
for field in gv_fields:
    lower = df[field].quantile(0.01)
    upper = df[field].quantile(0.99)
    df[field] = df[field].clip(lower, upper)

# -------------------------------------------------------------------------
# STEP 6: Plot grid (2 cols x 4 rows); bottom-right reserved for legend
# -------------------------------------------------------------------------
sns.set(style="whitegrid")
fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(8.5, 13),
                         gridspec_kw={"hspace": 0.35, "wspace": 0.04})
axes = axes.flatten()

# Draw 7 violins into the first 7 axes; leave axes[-1] empty for legend
for i, (field, title) in enumerate(zip(gv_fields, subplot_titles)):
    ax = axes[i]
    sns.violinplot(
        data=df,
        y="LabelShort",
        x=field,
        order=order_short,
        palette=[short_colors[s] for s in order_short],
        ax=ax,
        linewidth=1.0,
        inner="box",
        scale="width",
        cut=0
    )
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    if i % 2 == 1:
        ax.set_yticklabels([])

# -------------------------------------------------------------------------
# STEP 7: Legend panel in bottom-right axis (single column)
# -------------------------------------------------------------------------
legend_ax = axes[-1]
legend_ax.axis("off")
legend_ax.set_xlim(0, 1)
legend_ax.set_ylim(0, 1)

# --- Tunable layout params ---
left_margin = 0.06   # left edge of legend content
title_y     = 0.93   # ~aligns with "Elev" title line; raise/lower as needed
box_size    = 0.040  # color square size
text_pad    = 0.02   # gap between square and text
y_start     = 0.75   # first row y (under the title)
row_h       = 0.075  # vertical spacing between rows (smaller -> tighter)
fs_title    = 12
fs_text     = 9.5
bold_short  = False  # set True to bold the short codes

# Centered legend title to align visually with "CurvPr" title above
legend_ax.text(0.5, title_y, "Legend (Schema D)",
               transform=legend_ax.transAxes,
               ha="center", va="top", fontsize=fs_title, fontweight="bold")

# Single-column rows (10 entries)
for i, short_lbl in enumerate(order_short):
    y = y_start - i * row_h

    # centered color square
    rect = patches.Rectangle(
        (left_margin, y - box_size/2), box_size, box_size,
        transform=legend_ax.transAxes,
        facecolor=short_colors[short_lbl],
        edgecolor="black", linewidth=0.6
    )
    legend_ax.add_patch(rect)

    # text: SHORT = LONG
    if bold_short:
        legend_ax.text(left_margin + box_size + text_pad, y, short_lbl,
                       transform=legend_ax.transAxes, ha="left", va="center",
                       fontsize=fs_text, fontweight="bold")
        legend_ax.text(left_margin + box_size + text_pad + 0.06, y,
                       f"= {legend_long[short_lbl]}",
                       transform=legend_ax.transAxes, ha="left", va="center",
                       fontsize=fs_text)
    else:
        legend_ax.text(left_margin + box_size + text_pad, y,
                       f"{short_lbl} = {legend_long[short_lbl]}",
                       transform=legend_ax.transAxes, ha="left", va="center",
                       fontsize=fs_text)


# -------------------------------------------------------------------------
# STEP 8: Save
# -------------------------------------------------------------------------
fig.suptitle("Violin Plots of Segment-Level GV Means by Landform Class (Schema D)", fontsize=16, y=0.96)
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close()

print(f"✅ Figure saved to: {output_path}")
