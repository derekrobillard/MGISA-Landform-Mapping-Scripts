# =============================================================================
# Title: accuracy_1pass_assessment.py  (original: AA_TrialRun11_864_E5_1PassAccuracy.py)
# Author: Derek Robillard, with OpenAI assistance
# Purpose: Performs a one-pass quantitative accuracy assessment by intersecting
#          predicted segment polygons with reference landforms. Can be applied
#          to both individual ML classifiers (RT_D50, RT_D60, SVM_D50, SVM_D60)
#          and the ensemble classifier (E5). Produces per-class metrics
#          (Producer’s Accuracy, User’s Accuracy, IoU, F1, FN/FP) as well as
#          an overall accuracy (OA) measure.
# Notes: Snapshot of the exact script used for the MGISA final report.
#        Logic unchanged; only file paths and names generalized.
#        Although this version includes E5 (ensemble)-related parameters,
#        the script was first run individually for each of the four
#        best-performing ML classifiers before proceeding with the ensemble
#        accuracy assessment.
#        This script must be executed prior to generating confusion matrix
#        figures, as it creates the summary tables required for plotting.
# Inputs: Update the placeholder paths below (segment FC, RLP FC, output GDB).
# Outputs: Intersect FC, confusion-matrix-like area table, totals tables,
#          per-class accuracy table, and OA table (written to output GDB).
# Citation: Robillard (2025). *MGISA landform mapping scripts* [Computer software]. GitHub.
# =============================================================================

import arcpy
import pandas as pd
import numpy as np
from datetime import datetime

arcpy.env.overwriteOutput = True

# ===== PARAMS (EDIT THESE PATHS/NAMES) ======================================
# Inputs
SEG_FC = r"C:\path\to\Segmentation.gdb\Segments"                 # segment polygons (have prediction field)
RLP_FC = r"C:\path\to\Reference_Landforms.gdb\RLPs_SchemaD_864"  # reference landforms (Schema D)

# Fields
REF_CLASS_FIELD = "NameD"   # true class in RLPs (Schema D)
PRED_FIELD      = "E5"      # predicted class field in SEG_FC (change for RT_D50, RT_D60, SVM_D50, SVM_D60, etc.)

# Output GDB & run tags
OUT_GDB = r"C:\path\to\Accuracy_Assessment.gdb"  # destination FGDB for all outputs
RUN_TAG = "TrialRunXX"       # short run label (e.g., "LT_TrialRun11")
TAG     = "E5"               # classifier tag (e.g., "RT_D50", "RT_D60", "SVM_D50", "SVM_D60", "E5")

# Intersect output (feature class)
INTERSECT_FC = fr"{OUT_GDB}\{RUN_TAG}_Segments_Intersect_RLPs_{TAG}"

# Added fields in intersect output
REFCLASS_FIELD  = "RefClass"
PREDCLASS_FIELD = f"{TAG}_PredClass"  # e.g., "E5_PredClass" or "RTv11A2D50_PredClass"
CORRECT_FIELD   = f"{TAG}_Correct"    # e.g., "E5_Correct" or "RTv11A2D50_Correct"

# Summary statistics outputs (feed the per-class metrics)
CM_TBL         = fr"{OUT_GDB}\{RUN_TAG}_{TAG}_CM_tbl"
REFTOTALS_TBL  = fr"{OUT_GDB}\{RUN_TAG}_{TAG}_RefTotals_tbl"
PREDTOTALS_TBL = fr"{OUT_GDB}\{RUN_TAG}_{TAG}_PredTotals_tbl"

# Final accuracy tables
PERCLASS_TBL = fr"{OUT_GDB}\{RUN_TAG}_{TAG}_PerClassAccuracy_tbl"
OA_TBL       = fr"{OUT_GDB}\{RUN_TAG}_{TAG}_OverallAccuracy_tbl"
# ============================================================================

def safe_delete(path):
    if arcpy.Exists(path):
        arcpy.Delete_management(path)

# ----- 1) Intersect (same as UI settings) -----------------------------------
# Attributes to Join: All attributes
# Output type: Same as input (INPUT)
safe_delete(INTERSECT_FC)
arcpy.analysis.Intersect([SEG_FC, RLP_FC], INTERSECT_FC, "ALL", None, "INPUT")

# ----- 2) Add and populate fields -------------------------------------------
#   RefClass       = NameD from RLPs
#   <TAG>_PredClass = prediction from segments (e.g., E5)
#   <TAG>_Correct   = 1 if equal else 0
for name, ftype, kwargs in [
    (REFCLASS_FIELD, "TEXT", {"field_length": 50}),
    (PREDCLASS_FIELD, "TEXT", {"field_length": 50}),
    (CORRECT_FIELD, "SHORT", {}),
]:
    if not any(f.name.upper() == name.upper() for f in arcpy.ListFields(INTERSECT_FC)):
        arcpy.AddField_management(INTERSECT_FC, name, ftype, **kwargs)

# Calculate RefClass and PredClass
arcpy.management.CalculateField(INTERSECT_FC, REFCLASS_FIELD, f"!{REF_CLASS_FIELD}!", "PYTHON3")
arcpy.management.CalculateField(INTERSECT_FC, PREDCLASS_FIELD, f"!{PRED_FIELD}!", "PYTHON3")

# Then calculate Correct (1 if equal)
with arcpy.da.UpdateCursor(INTERSECT_FC, [REFCLASS_FIELD, PREDCLASS_FIELD, CORRECT_FIELD]) as cur:
    for refv, predv, _ in cur:
        cur.updateRow([refv, predv, 1 if (refv is not None and predv is not None and refv == predv) else 0])

# ----- 3) Summary Statistics tables (these drive the metrics) ----------------
# statistics_fields = [["Shape_Area", "SUM"]]
# case fields:
#   - CM table:      [RefClass, <TAG>_PredClass]
#   - RefTotals:     [RefClass]
#   - PredTotals:    [<TAG>_PredClass]
safe_delete(CM_TBL)
safe_delete(REFTOTALS_TBL)
safe_delete(PREDTOTALS_TBL)

arcpy.analysis.Statistics(INTERSECT_FC, CM_TBL, [["Shape_Area", "SUM"]], [REFCLASS_FIELD, PREDCLASS_FIELD])
arcpy.analysis.Statistics(INTERSECT_FC, REFTOTALS_TBL, [["Shape_Area", "SUM"]], [REFCLASS_FIELD])
arcpy.analysis.Statistics(INTERSECT_FC, PREDTOTALS_TBL, [["Shape_Area", "SUM"]], [PREDCLASS_FIELD])

# ----- 4) Build Per-Class Accuracy table -------------------------------------
# Convert summaries to DataFrames
df_cm = pd.DataFrame(arcpy.da.TableToNumPyArray(CM_TBL, [REFCLASS_FIELD, PREDCLASS_FIELD, 'SUM_Shape_Area']))
df_ref = pd.DataFrame(arcpy.da.TableToNumPyArray(REFTOTALS_TBL, [REFCLASS_FIELD, 'SUM_Shape_Area']))
df_pred = pd.DataFrame(arcpy.da.TableToNumPyArray(PREDTOTALS_TBL, [PREDCLASS_FIELD, 'SUM_Shape_Area']))

# Rename columns for clarity/consistency
df_cm   = df_cm.rename(columns={REFCLASS_FIELD: 'Ref', PREDCLASS_FIELD: 'Pred', 'SUM_Shape_Area': 'Area'})
df_ref  = df_ref.rename(columns={REFCLASS_FIELD: 'Class', 'SUM_Shape_Area': 'Ref_Total_Area'})
df_pred = df_pred.rename(columns={PREDCLASS_FIELD: 'Class', 'SUM_Shape_Area': 'Pred_Total_Area'})

# Diagonal (correct) areas per class
df_diag = df_cm[df_cm['Ref'] == df_cm['Pred']].copy()
df_diag = df_diag.rename(columns={'Ref': 'Class', 'Area': 'Correct_Area'})

# Join totals
df_metrics = pd.merge(df_diag, df_ref,  on='Class', how='right')   # keep all Ref classes
df_metrics = pd.merge(df_metrics, df_pred, on='Class', how='left')

# Fill NaNs (e.g., class never predicted)
for col in ['Correct_Area', 'Ref_Total_Area', 'Pred_Total_Area']:
    df_metrics[col] = df_metrics[col].fillna(0.0)

# Metrics
# Producer (Recall) = Correct / Ref_Total
# User (Precision)  = Correct / Pred_Total
# IoU               = Correct / (Ref + Pred - Correct)
# F1                = 2 * (P * U) / (P + U)
# FN_Area           = Ref_Total - Correct; FN_Prop = FN_Area / Ref_Total
# FP_Area           = Pred_Total - Correct; FP_Prop = FP_Area / Pred_Total
def safe_div(a, b):
    return (a / b) if (b and b != 0) else 0.0

df_metrics['Producer_Accuracy'] = [safe_div(c, r) for c, r in zip(df_metrics['Correct_Area'], df_metrics['Ref_Total_Area'])]
df_metrics['User_Accuracy']     = [safe_div(c, p) for c, p in zip(df_metrics['Correct_Area'], df_metrics['Pred_Total_Area'])]
df_metrics['IoU']               = [safe_div(c, (r + p - c)) for c, r, p in zip(df_metrics['Correct_Area'], df_metrics['Ref_Total_Area'], df_metrics['Pred_Total_Area'])]
df_metrics['F1_Score']          = [safe_div(2*(pa*ua), (pa+ua)) if (pa+ua) != 0 else 0.0
                                   for pa, ua in zip(df_metrics['Producer_Accuracy'], df_metrics['User_Accuracy'])]

df_metrics['FN_Area'] = df_metrics['Ref_Total_Area']  - df_metrics['Correct_Area']
df_metrics['FN_Prop'] = [safe_div(fn, r) for fn, r in zip(df_metrics['FN_Area'], df_metrics['Ref_Total_Area'])]
df_metrics['FP_Area'] = df_metrics['Pred_Total_Area'] - df_metrics['Correct_Area']
df_metrics['FP_Prop'] = [safe_div(fp, p) for fp, p in zip(df_metrics['FP_Area'], df_metrics['Pred_Total_Area'])]

# Round like prior outputs
df_metrics = df_metrics.round({
    'Correct_Area': 2, 'Ref_Total_Area': 2, 'Pred_Total_Area': 2,
    'FN_Area': 2, 'FP_Area': 2,
    'Producer_Accuracy': 3, 'User_Accuracy': 3, 'IoU': 3, 'F1_Score': 3,
    'FN_Prop': 3, 'FP_Prop': 3
})

# Reorder columns
df_out = df_metrics[['Class', 'Correct_Area', 'Ref_Total_Area', 'Pred_Total_Area',
                     'FN_Area', 'FN_Prop', 'FP_Area', 'FP_Prop',
                     'Producer_Accuracy', 'User_Accuracy', 'IoU', 'F1_Score']]

# Write PerClass table
safe_delete(PERCLASS_TBL)
structured_array = np.array([(
    row['Class'],
    row['Correct_Area'],
    row['Ref_Total_Area'],
    row['Pred_Total_Area'],
    row['FN_Area'],
    row['FN_Prop'],
    row['FP_Area'],
    row['FP_Prop'],
    row['Producer_Accuracy'],
    row['User_Accuracy'],
    row['IoU'],
    row['F1_Score']
) for _, row in df_out.iterrows()], dtype=[
    ('Class', 'U50'),
    ('Correct_Area', 'f8'),
    ('Ref_Total_Area', 'f8'),
    ('Pred_Total_Area', 'f8'),
    ('FN_Area', 'f8'),
    ('FN_Prop', 'f8'),
    ('FP_Area', 'f8'),
    ('FP_Prop', 'f8'),
    ('Producer_Accuracy', 'f8'),
    ('User_Accuracy', 'f8'),
    ('IoU', 'f8'),
    ('F1_Score', 'f8')
])
arcpy.da.NumPyArrayToTable(structured_array, PERCLASS_TBL)
arcpy.AddMessage(f"Per-class accuracy written: {PERCLASS_TBL}")

# ----- 5) Overall Accuracy table (1 row) -------------------------------------
overall_accuracy = df_out['Correct_Area'].sum() / df_out['Ref_Total_Area'].sum() if df_out['Ref_Total_Area'].sum() else 0.0
oa_array = np.array(
    [(round(overall_accuracy, 4), TAG, datetime.now().strftime('%Y-%m-%d'))],
    dtype=[('Overall_Accuracy', 'f8'), ('Classifier', 'U20'), ('Date', 'U10')]
)

safe_delete(OA_TBL)
arcpy.da.NumPyArrayToTable(oa_array, OA_TBL)
arcpy.AddMessage(f"Overall accuracy ({TAG}) = {round(overall_accuracy,4)}  → {OA_TBL}")

print("✅ Accuracy workflow complete.")
print(f"   • Intersect:        {INTERSECT_FC}")
print(f"   • CM table:         {CM_TBL}")
print(f"   • RefTotals table:  {REFTOTALS_TBL}")
print(f"   • PredTotals table: {PREDTOTALS_TBL}")
print(f"   • Per-class table:  {PERCLASS_TBL}")
print(f"   • OA table:         {OA_TBL}")
