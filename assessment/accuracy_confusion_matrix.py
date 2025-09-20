# =============================================================================
# Title: accuracy_confusion_matrix.py  (original: AA_TrialRun11_864_E5_GenerateConfusionMatrix.py)
# Author: Derek Robillard, with OpenAI assistance
# Purpose: Generates a row-normalized confusion matrix figure from an ArcGIS
#          confusion-matrix table. Produces a labeled PNG image that shows
#          the distribution of predicted vs. reference classes.
# Notes: Snapshot of the exact script used for the MGISA final report.
#        Logic unchanged; only file paths generalized.
#        Although this version was run for the E5 ensemble classification,
#        the same workflow can be applied to any classifier results
#        (e.g., RT_D50, RT_D60, SVM_D50, SVM_D60) by updating field names
#        and inputs accordingly.
#        Requires execution of the 1-pass accuracy assessment script first,
#        which generates the tables that this script uses to plot results.
# Inputs: An ArcGIS confusion-matrix table containing RefClass, <PredField>,
#         and SUM_Shape_Area fields. Update the file paths and predicted
#         class field name as needed.
# Outputs: A row-normalized confusion matrix PNG saved to the specified path.
# Citation: Robillard (2025). *MGISA landform mapping scripts* [Computer software]. GitHub.
# =============================================================================

import arcpy
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# === STEP 1: Define paths (EDIT THESE) ===
conf_matrix_table = r"C:\path\to\Accuracy_Assessment.gdb\TrialRunXX_E5_CM_tbl"
output_img_path   = r"C:\path\to\Outputs\TrialRunXX_E5_CM.png"

# === STEP 2: Define class name abbreviation and order ===
class_label_map = {
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
label_order = ["WB", "SI-S", "SI-C", "R", "F", "SSU", "BSU-NS", "BSU-S", "IC", "VB"]

# === STEP 3: Load confusion matrix table ===
df_cm = pd.DataFrame(arcpy.da.TableToNumPyArray(
    conf_matrix_table, ['RefClass', 'E5_PredClass', 'SUM_Shape_Area']
))

# === STEP 4: Apply label map to abbreviate class names ===
df_cm['Ref_Label'] = df_cm['RefClass'].map(class_label_map)
df_cm['Pred_Label'] = df_cm['E5_PredClass'].map(class_label_map)

# === STEP 5: Pivot to confusion matrix and enforce schema order ===
conf_matrix = pd.pivot_table(
    df_cm, values='SUM_Shape_Area',
    index='Ref_Label', columns='Pred_Label',
    aggfunc='sum', fill_value=0
).reindex(index=label_order, columns=label_order, fill_value=0)

# === STEP 6: Normalize by row for interpretability ===
conf_matrix_norm = conf_matrix.div(conf_matrix.sum(axis=1), axis=0).fillna(0)

# === STEP 7: Plot confusion matrix ===
plt.figure(figsize=(10, 9))
sns.set(font_scale=1.1)
ax = sns.heatmap(conf_matrix_norm, annot=True, fmt=".2f", cmap='Blues', cbar=True,
                 linewidths=0.5, square=True, annot_kws={"size": 12})

# === STEP 8: Format plot ====
plt.title("Confusion Matrix for the E5 Ensemble Classification", fontsize=14, weight='bold', pad=20)
plt.xlabel("Predicted Class", fontsize=12, labelpad=15)
plt.ylabel("Reference Class", fontsize=12, labelpad=15)
plt.xticks(rotation=45, ha='center', fontsize=12)
plt.yticks(rotation=0, fontsize=12)

# Set colorbar label
cbar = ax.collections[0].colorbar
cbar.ax.set_ylabel("Row-Normalized (%)", rotation=270, labelpad=15, fontsize=12)

plt.tight_layout()

# === STEP 9: Save figure to file ===
plt.savefig(output_img_path, dpi=300)
plt.close()
print(f"✅ E5 Ensemble confusion matrix figure saved to:\n{output_img_path}")