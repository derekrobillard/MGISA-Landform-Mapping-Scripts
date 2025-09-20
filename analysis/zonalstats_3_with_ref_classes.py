# ------------------------------------------------------------------------
# # Title: zonalstats_3_with_ref_classes.py  (original: ZonalStats_Toba3_wLandformClasses.py)
# Author: Derek Robillard, with OpenAI assistance
# Purpose: Create a new version of the merged zonal-stats table that includes
#          reference class fields (Schema D: CodeD, NameD), along with PERCENTAGE and gridcode,
#          by joining them from the segment polygon feature class.
# Notes: Snapshot of the exact script used for the MGISA final report.
#        Logic unchanged; only file paths generalized and terminology clarified ("ref_classes").
# Inputs: Update the placeholder paths below (segment_fc, zstats_all, output_gdb).
# Outputs: A flat table (e.g., 'ZStats_ALL_SMSv7_wClasses') in the specified GDB.
# Citation: Robillard (2025). *MGISA landform mapping scripts* [Computer software]. GitHub.
# ------------------------------------------------------------------------

import arcpy
import os

# ------------------------------------------------------------------------
# OVERVIEW:
# This script creates a new version of the ZStats_ALL_SMSv7 table that
# includes additional classification fields (CodeD, NameD, PERCENTAGE, gridcode)
# by joining them from the segmented polygon feature class.
# The output is a flat table useful for comparison, filtering, and export.
# ------------------------------------------------------------------------

# --- INPUTS (EDIT THESE PATHS) ---
# Polygon feature class containing reference class info (Schema D: CodeD, NameD)
segment_fc = r"C:\path\to\Segmentation.gdb\Segments"  # e.g., your segment polygons with ref_classes

# Original merged zonal stats table
zstats_all = r"C:\path\to\Outputs\SegmentStats.gdb\ZStats_ALL_SMSv7"

# GDB to store new output
output_gdb = r"C:\path\to\Outputs\SegmentStats.gdb"
output_table = "ZStats_ALL_SMSv7_wClasses"  # adjust if you prefer a different name

# --- STEP 1: Copy the merged stats table to a new version ---
zstats_with_classes = arcpy.management.CopyRows(
    zstats_all,
    os.path.join(output_gdb, output_table)
)[0]
print(f"✅ Created new table with class info: {output_table}")

# --- STEP 2: Join class fields from the polygon layer ---
# These fields help interpret class membership (Schema D) for each segment Id
fields_to_join = ["CodeD", "NameD", "PERCENTAGE", "gridcode"]  # modify if needed

arcpy.management.JoinField(
    in_data=zstats_with_classes,  # the newly copied stats table
    in_field="Id",                # unique segment Id in the stats table
    join_table=segment_fc,        # polygon FC with reference class labels (ref_classes)
    join_field="Id",              # common join key
    fields=fields_to_join         # fields of interest
)

print(f"✅ Joined class fields: {', '.join(fields_to_join)}")
print(f"   Output table saved as: {output_table}")

# ------------------------------------------------------------------------
# Usage (example):
# 1) Replace the placeholder paths above for 'segment_fc', 'zstats_all', and 'output_gdb'.
# 2) Run in the ArcGIS Pro Python environment (arcpy required).
# 3) Join key is 'Id' in both the stats table and the segment FC.
# 4) Resulting table includes ref_classes per segment for downstream analysis.
# ------------------------------------------------------------------------