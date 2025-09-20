# Title: zonalstats_2_merge_all.py  (original: ZonalStats_Toba2_MergeAll.py)
# Author: Derek Robillard, with OpenAI assistance
# Purpose: Merge per-raster Zonal Statistics tables into a single flat table,
#          retaining selected fields from each source for downstream analysis.
# Notes: Snapshot of the exact script used for the MGISA final report.
#        Logic unchanged; only file paths and notes generalized.
# Inputs: Update 'output_gdb' and confirm table names/fields in 'zstats_tables'.
# Outputs: A merged table (e.g., 'ZStats_ALL_SMSv7') in the specified GDB.
# Citation: Robillard (2025). *MGISA landform mapping scripts* [Computer software]. GitHub.

import arcpy
import os

# -----------------------------
# USER CONFIGURATION SECTION
# -----------------------------

# Path to the GDB containing all the ZStats tables
output_gdb = r"C:\path\to\Outputs\SegmentStats.gdb"   # <-- replace with your FGDB path

# Name of the final merged table to be created
merged_table_name = "ZStats_ALL_SMSv7"                 # keep or adjust naming as desired

# Full path to output table
merged_table_path = os.path.join(output_gdb, merged_table_name)

# List of input ZStats tables with the fields to keep from each
# NOTE: The first entry will be used as the base table; others will be joined to it
# NOTE: SMSv7 refers to the version (v7) of SMS parameters used in Robillard (2025)
zstats_tables = [
    ("ZStats_Elev_SMSv7", ["Id", "COUNT", "AREA", "Elev_MEAN", "Elev_STDV"]),
    ("ZStats_TPI1_SMSv7", ["TPI1_MEAN", "TPI1_STDV"]),
    ("ZStats_Slope_SMSv7", ["Slope_MEAN", "Slope_STDV"]),
    ("ZStats_CurvT_SMSv7", ["CurvT_MEAN", "CurvT_STDV"]),
    ("ZStats_TPI2_SMSv7", ["TPI2_MEAN", "TPI2_STDV"]),
    ("ZStats_SRI_SMSv7", ["SRI_MEAN", "SRI_STDV"]),
    ("ZStats_CurvPr_SMSv7", ["CurvPr_MEAN", "CurvPr_STDV"])
]

# Allow overwrite of any existing output table
arcpy.env.overwriteOutput = True

# -----------------------------
# STEP 1: COPY INITIAL TABLE WITH ONLY SELECTED FIELDS
# -----------------------------

# Use the first table in the list as the base table to build from
initial_table, initial_fields = zstats_tables[0]
initial_table_path = os.path.join(output_gdb, initial_table)

# Create a FieldMappings object to control which fields are copied
field_mappings = arcpy.FieldMappings()

# Add each desired field (e.g., Id, COUNT, AREA, Elev_MEAN, Elev_STDV) to the mapping
for field in initial_fields:
    field_map = arcpy.FieldMap()
    field_map.addInputField(initial_table_path, field)
    field_mappings.addFieldMap(field_map)

# Export the filtered fields from the base table into a new table (merged output)
arcpy.conversion.TableToTable(
    in_rows=initial_table_path,
    out_path=output_gdb,
    out_name=merged_table_name,
    field_mapping=field_mappings
)

print(f"✅ Created initial table: {merged_table_name}")
print(f"   Included fields: {', '.join(initial_fields)}")

# -----------------------------
# STEP 2: JOIN REMAINING TABLES TO THE MERGED TABLE
# -----------------------------

# Loop through the remaining tables (starting from index 1)
for table_name, fields_to_join in zstats_tables[1:]:
    join_table_path = os.path.join(output_gdb, table_name)

    print(f"\n🔄 Joining fields from: {table_name}")
    print(f"   Fields: {', '.join(fields_to_join)}")

    # Perform attribute join using the common "Id" field
    arcpy.management.JoinField(
        in_data=merged_table_path,   # destination table
        in_field="Id",               # join field in destination
        join_table=join_table_path,  # source table to join
        join_field="Id",             # join field in source table
        fields=fields_to_join        # list of fields to bring in
    )

    print(f"   ✅ Successfully joined {len(fields_to_join)} fields.")

# -----------------------------
# FINAL MESSAGE
# -----------------------------

print("\n🎉 Merge complete!")
print(f"   Output table saved at:\n   {merged_table_path}")
print("   You can now join this table to your segment polygon layer using 'Id'.")
