# =============================================================================
# Title: ensemble_E5_classification.py  (original: ensemble_E5_IoU_864_wRULE.py)
# Author: Derek Robillard, with OpenAI assistance
# Purpose: Generates the E5 ensemble classification by combining predictions
#          from four ML classifiers (RT-D50, RT-D60, SVM-D50, SVM-D60) using
#          IoU-weighted voting. Writes the final ensemble label to field E5,
#          along with provenance fields (E5_src, E5_score). Includes an
#          additional WATER BODY rule that overrides the ensemble winner
#          where the SVM-D60 classifier predicts WATER BODY below a defined
#          elevation threshold, using the DEM as input.
# Notes: Snapshot of the exact script used for the MGISA final report.
#        Logic unchanged; only file paths generalized.
#        This method could not be executed until after the accuracy
#        assessments for the four ML classifiers were completed, since
#        IoU metrics from those assessments are required for weighting.
# Inputs: Segment polygons with prediction fields for four classifiers,
#         per-class IoU tables from the accuracy assessments, and a DEM
#         for the WATER BODY elevation rule.
# Outputs: Adds fields to the segment polygons for the ensemble class (E5),
#          source classifiers (E5_src), and ensemble score (E5_score).
# Citation: Robillard (2025). *MGISA landform mapping scripts* [Computer software]. GitHub.
# =============================================================================

import arcpy
from collections import defaultdict
import math

# =============================================================================
# PARAMS — YOUR PROJECT SETTINGS
# =============================================================================

arcpy.env.overwriteOutput = True

# (1) Segment polygons feature class
SEG_FC = r"C:\path\to\Segmentation.gdb\Segments"

# (2) Classifier prediction fields in SEG_FC
CLASS_FIELDS = {
    "RTv11A2D50": "RTv11A2D50_Classname",
    "RTv11A2D60": "RTv11A2D60_Classname",
    "SVMv11A2D50": "SVMv11A2D50_Classname",
    "SVMv11A2D60": "SVMv11A2D60_Classname",
}

# (3) Per-class accuracy tables (with "Class" and chosen metric column)
TBL_RT_D50  = r"C:\path\to\Accuracy_Assessment.gdb\RT_D50_PerClassAccuracy_tbl"
TBL_RT_D60  = r"C:\path\to\Accuracy_Assessment.gdb\RT_D60_PerClassAccuracy_tbl"
TBL_SVM_D50 = r"C:\path\to\Accuracy_Assessment.gdb\SVM_D50_PerClassAccuracy_tbl"
TBL_SVM_D60 = r"C:\path\to\Accuracy_Assessment.gdb\SVM_D60_PerClassAccuracy_tbl"

# (4) Metric column to use for weighting
WEIGHT_METRIC_COL = "IoU"      # Alternatively, "F1_Score"

# (5) Optional sharpening power (>1 = reward clear leaders; 1.0 = off)
WEIGHT_POWER = 1.00

# (6) Low-confidence fallback
USE_LOWCONF_FALLBACK = True
TAU = 0.55

# (7) Classifier priority order for tie-breaking
CLF_PRIORITY = ["SVMv11A2D60", "RTv11A2D60", "SVMv11A2D50", "RTv11A2D50"]

# (8) Output field names to write on SEG_FC
E5_FIELD       = "E5"
E5_SRC_FIELD   = "E5_src"
E5_SCORE_FIELD = "E5_score"
E5_LEN = 50
E5_SRC_LEN = 60

# (9) Export normalized weights to CSV for audit
EXPORT_WEIGHTS_CSV = r"C:\path\to\Outputs\E5_NormalizedWeights.csv"

# (10) >>> WB-ELEV RULE (optional override to capture low-elevation river segments)
ENABLE_WB_ELEV_RULE = True
SVM_RIVER_CLF = "SVMv11A2D60" 
CLS_WATER = "WATER BODY"
ELEV_RASTER = r"C:\path\to\DEMs\YourDEM.tif"
ELEV_THRESH = 220.0  # meters

# =============================================================================
# END PARAMS -- NOTE: No changes to logic below this line
# =============================================================================

def ensure_fields(fc, fields_spec):
    """Add any missing output fields (text length adjustable)."""
    existing = {f.name.upper(): f for f in arcpy.ListFields(fc)}
    for name, ftype, kwargs in fields_spec:
        if name.upper() not in existing:
            arcpy.AddField_management(fc, name, ftype, **kwargs)


def read_metric_table(tbl_path, metric_col, class_col="Class"):
    """Return dict: class_name -> metric_value (float; NaN/missing => 0.0)."""
    W = {}
    with arcpy.da.SearchCursor(tbl_path, [class_col, metric_col]) as cur:
        for cls, val in cur:
            try:
                v = float(val)
                if math.isnan(v):
                    v = 0.0
            except Exception:
                v = 0.0
            W[str(cls)] = max(0.0, v)
    return W


def normalize_per_class(weight_map, power=1.0):
    """Normalize weights per class so that the four classifier weights sum to 1."""
    out = {}
    for cls, clf_dict in weight_map.items():
        powered = {clf: (w ** power if power != 1.0 else w) for clf, w in clf_dict.items()}
        s = sum(powered.values())
        if s > 0:
            out[cls] = {clf: (w / s) for clf, w in powered.items()}
        else:
            out[cls] = {clf: 0.0 for clf in clf_dict.keys()}
    return out

def build_weight_dict(metric_col):
    """Build normalized weights dict: Wnorm[class][clf] in [0..1]."""
    W_rt50  = read_metric_table(TBL_RT_D50,  metric_col)
    W_rt60  = read_metric_table(TBL_RT_D60,  metric_col)
    W_svm50 = read_metric_table(TBL_SVM_D50, metric_col)
    W_svm60 = read_metric_table(TBL_SVM_D60, metric_col)

    all_classes = set(W_rt50) | set(W_rt60) | set(W_svm50) | set(W_svm60)

    raw = {}
    for cls in all_classes:
        raw[cls] = {
            "RTv11A2D50":  W_rt50.get(cls, 0.0),
            "RTv11A2D60":  W_rt60.get(cls, 0.0),
            "SVMv11A2D50": W_svm50.get(cls, 0.0),
            "SVMv11A2D60": W_svm60.get(cls, 0.0),
        }

    return normalize_per_class(raw, power=WEIGHT_POWER)

def maybe_export_weights_csv(Wnorm, out_csv):
    """Optional: export normalized weights for audit."""
    if not out_csv:
        return
    import csv
    fields = ["Class"] + list(CLF_PRIORITY) + ["Sum"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for cls, d in sorted(Wnorm.items()):
            row = [cls] + [d.get(clf, 0.0) for clf in CLF_PRIORITY]
            row.append(sum(d.values()))
            w.writerow(row)


def pick_ensemble_label(preds, Wnorm, clf_priority_order, use_lowconf=False, tau=0.55):
    """Compute ensemble winner for one segment with tie-breakers and fallback."""
    score = defaultdict(float)
    voters_by_class = defaultdict(list)

    for clf, cls in preds.items():
        if not cls:
            continue
        w = Wnorm.get(cls, {}).get(clf, 0.0)
        score[cls] += w
        voters_by_class[cls].append((clf, w))

    if not score:
        return (None, [], 0.0)

    max_score = max(score.values())
    winners = [c for c, s in score.items() if abs(s - max_score) < 1e-12]

    if len(winners) == 1:
        winner = winners[0]
    else:
        best_w = -1.0
        tb1_candidates = []
        for c in winners:
            top_single = max((w for (_clf, w) in voters_by_class[c]), default=0.0)
            if top_single > best_w + 1e-15:
                best_w = top_single
                tb1_candidates = [c]
            elif abs(top_single - best_w) <= 1e-15:
                tb1_candidates.append(c)
        if len(tb1_candidates) == 1:
            winner = tb1_candidates[0]
        else:
            def best_priority_rank_for_class(c):
                voters = [clf for (clf, _w) in voters_by_class[c]]
                ranks = [clf_priority_order.index(clf) for clf in voters if clf in clf_priority_order]
                return min(ranks) if ranks else 999
            ranked = sorted(tb1_candidates, key=lambda c: best_priority_rank_for_class(c))
            winner = ranked[0]

    if use_lowconf and max_score < tau:
        voters = voters_by_class[winner]
        if voters:
            best_clf = max(voters, key=lambda t: t[1])[0]
        else:
            best_clf = clf_priority_order[0]
        winner = preds.get(best_clf, winner)
        max_score = sum(Wnorm.get(winner, {}).get(clf, 0.0)
                        for clf, pred in preds.items() if pred == winner)

    src = sorted(
        [clf for clf, pred in preds.items() if pred == winner],
        key=lambda c: clf_priority_order.index(c) if c in clf_priority_order else 999
    )
    return (winner, src, max_score)


# >>> WB-ELEV RULE: helper builds {OID: mean_elev} using ZonalStatisticsAsTable
def build_mean_elev_by_oid(seg_fc, elev_raster):
    """
    Returns dict {OID: mean_elev}. Writes the temp Zonal Stats table to a
    scratch workspace (more reliable than in_memory). Requires Spatial Analyst.
    """
    arcpy.CheckOutExtension("Spatial")
    from arcpy.sa import ZonalStatisticsAsTable  # noqa: F401

    oid_field = arcpy.Describe(seg_fc).OIDFieldName

    # Prefer scratch GDB; fall back gracefully if unset/not present
    scratch_ws = arcpy.env.scratchGDB
    if not scratch_ws or not arcpy.Exists(scratch_ws):
        scratch_ws = arcpy.env.scratchFolder or arcpy.env.workspace

    # Create a unique output table name in the scratch workspace
    try:
        zs_tbl = arcpy.CreateUniqueName("zs_elev_tbl", scratch_ws)
    except Exception:
        # Fallback if CreateUniqueName isn't available in this environment
        import uuid, os
        zs_tbl = os.path.join(scratch_ws, f"zs_elev_tbl_{uuid.uuid4().hex[:8]}")

    # Run Zonal Statistics as Table
    arcpy.sa.ZonalStatisticsAsTable(
        in_zone_data=seg_fc,
        zone_field=oid_field,
        in_value_raster=elev_raster,
        out_table=zs_tbl,
        ignore_nodata="DATA",
        statistics_type="MEAN"
    )

    # Build mapping dict
    elev_by_oid = {}
    with arcpy.da.SearchCursor(zs_tbl, [oid_field, "MEAN"]) as cur:
        for oid, mean_z in cur:
            elev_by_oid[oid] = float(mean_z) if mean_z is not None else None

    # Best-effort cleanup
    try:
        arcpy.Delete_management(zs_tbl)
    except Exception:
        pass

    return elev_by_oid

def main():
    ensure_fields(
        SEG_FC,
        [
            (E5_FIELD, "TEXT", {"field_length": E5_LEN}),
            (E5_SRC_FIELD, "TEXT", {"field_length": E5_SRC_LEN}),
            (E5_SCORE_FIELD, "DOUBLE", {}),
        ],
    )

    Wnorm = build_weight_dict(WEIGHT_METRIC_COL)
    if EXPORT_WEIGHTS_CSV:
        maybe_export_weights_csv(Wnorm, EXPORT_WEIGHTS_CSV)

    # >>> WB-ELEV RULE: precompute mean elevation per segment (once)
    elev_by_oid = {}
    oid_field = arcpy.Describe(SEG_FC).OIDFieldName
    if ENABLE_WB_ELEV_RULE:
        elev_by_oid = build_mean_elev_by_oid(SEG_FC, ELEV_RASTER)

    read_fields = list(CLASS_FIELDS.values())
    write_fields = [E5_FIELD, E5_SRC_FIELD, E5_SCORE_FIELD]

    clf_priority_order = list(CLF_PRIORITY)

    n = 0
    updated = 0
    # >>> include OID at the front so we can look up mean elevation quickly
    with arcpy.da.UpdateCursor(SEG_FC, [oid_field] + read_fields + write_fields) as ucur:
        for row in ucur:
            n += 1
            oid = row[0]
            preds_vals = row[1:1+len(read_fields)]
            preds = {}
            for (clf_key, fld), val in zip(CLASS_FIELDS.items(), preds_vals):
                preds[clf_key] = None if val in (None, "",) else str(val)
            preds = {k: v for k, v in preds.items() if v}

            winner, src_clfs, score = pick_ensemble_label(
                preds, Wnorm, clf_priority_order,
                use_lowconf=USE_LOWCONF_FALLBACK, tau=TAU
            )

            # >>> WB-ELEV RULE: one-directional override to WATER BODY
            if ENABLE_WB_ELEV_RULE:
                mean_z = elev_by_oid.get(oid, None)
                if (mean_z is not None) and (mean_z <= ELEV_THRESH):
                    if preds.get(SVM_RIVER_CLF) == CLS_WATER:
                        winner = CLS_WATER
                        # provenance: list all voters that predicted WATER BODY
                        src_clfs = sorted([clf for clf, cls in preds.items() if cls == CLS_WATER],
                                          key=lambda c: clf_priority_order.index(c) if c in clf_priority_order else 999)
                        score = sum(Wnorm.get(CLS_WATER, {}).get(clf, 0.0)
                                    for clf, pred in preds.items() if pred == CLS_WATER)

            row[1+len(read_fields) + 0] = winner if winner else None
            row[1+len(read_fields) + 1] = "+".join(src_clfs) if src_clfs else None
            row[1+len(read_fields) + 2] = float(score) if score is not None else None
            ucur.updateRow(row)
            updated += 1

    arcpy.AddMessage(f"E5 ensemble complete. Rows processed: {n}, updated: {updated}")

if __name__ == "__main__":
    main()