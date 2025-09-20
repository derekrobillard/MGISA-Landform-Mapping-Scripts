# ------------------------------------------------------------------------
# Title: zonalstats_4_join_to_segment_polys.py  (original: ZonalStats_Toba4_JoinToSegmentPolys.py)
# Author: Derek Robillard, with OpenAI assistance
# Purpose: Join the statistical _MEAN and _STDV fields from the merged ZStats table
#          back to the segment polygon feature class (by Id) for mapping, querying,
#          and downstream classification workflows.
# Notes: Snapshot of the exact script used for the MGISA final report.
#        Logic unchanged; only file paths generalized.
# Inputs: Update 'segment_fc' and 'zstats_all' with your own data sources.
# Outputs: The input segment feature class is augmented in place with the selected fields.
# Citation: Robillard (2025). *MGISA landform mapping scripts* [Computer software]. GitHub.
# ------------------------------------------------------------------------

import arcpy

# --- INPUTS (EDIT THESE PATHS) ---
# Segment polygon layer (used as zone layer in zonal stats)
segment_fc = r"C:\path\to\Segmentation.gdb\Segments"

# Merged zonal statistics table with all _MEAN and _STDV fields
zstats_all = r"C:\path\to\Outputs\SegmentStats.gdb\ZStats_ALL_SMSv7"

# --- Define which statistical fields to transfer (custom field names only) ---
# Ensure these names match the fields present in your merged ZStats table.
stats_fields = [
    "Elev_MEAN", "Elev_STDV",
    "TPI1_MEAN", "TPI1_STDV",
    "Slope_MEAN", "Slope_STDV",
    "CurvT_MEAN", "CurvT_STDV",
    "TPI2_MEAN", "TPI2_STDV",
    "SRI_MEAN",  "SRI_STDV",
    "CurvPr_MEAN","CurvPr_STDV"
]

# --- Perform the join on the "Id" field ---
arcpy.management.JoinField(
    in_data=segment_fc,       # destination: polygon feature class
    in_field="Id",            # join key
    join_table=zstats_all,    # source: stats table
    join_field="Id",          # join key
    fields=stats_fields       # only bring in selected fields
)

print(f"✅ Successfully joined {len(stats_fields)} statistical fields to the segment feature class.")
print("   You may now apply symbology or filtering based on these attributes.")
