# Title: zonalstats_1_batch_processing.py  (original: ZonalStats_Toba1_BatchProcessing.py)
# Author: Derek Robillard, with OpenAI assistance
# Purpose: Calculates MEAN and STDV (plus all other stats available)
#          for multiple raster surfaces based on polygon segments. Outputs zonal
#          statistics tables with consistent naming conventions.
# Notes: Snapshot of the exact script used for the MGISA final report.
#        Logic unchanged; only file paths generalized.
# Inputs: Update the placeholder paths below (segment polygons, rasters, output GDB).
# Outputs: One zonal statistics table per raster, written to the output GDB.
# Citation: Robillard (2025). *MGISA landform mapping scripts* [Computer software]. GitHub.

import arcpy
import os

# --- USER INPUTS ---

# Path to segment feature class (zone data) derived from Segment Mean Shift (SMS) output
segment_fc = r"C:\path\to\Segmentation.gdb\Segments"

# Output GDB for storing Zonal Statistics tables
output_gdb = r"C:\path\to\Outputs\SegmentStats.gdb"

# Snap raster and processing extent (set to DEM to ensure spatial alignment)
snap_raster = r"C:\path\to\DEMs\YourDEM.tif"

# List of tuples: (raster path, prefix for output fields and table)
raster_inputs = [
    (r"C:\path\to\DEMs\YourDEM.tif", "Elev"),
    (r"C:\path\to\Derived_Rasters\TPI\TPI.gdb\TPI_50m", "TPI1"),
    (r"C:\path\to\Derived_Rasters\Slope\Slope.gdb\Slope", "Slope"),
    (r"C:\path\to\Derived_Rasters\Curvature\Curvature.gdb\CurvT_7m", "CurvT"),
    (r"C:\path\to\Derived_Rasters\TPI\TPI.gdb\TPI_5m_30m_Annulus", "TPI2"),
    (r"C:\path\to\Derived_Rasters\SRI\SRI.gdb\SRI_7m", "SRI"),
    (r"C:\path\to\Derived_Rasters\Curvature\Curvature.gdb\CurvProf_7m", "CurvPr")
]

# Field in polygon layer used to join stats (must be integer)
zone_field = "Id"

# --- ENVIRONMENT SETUP ---
arcpy.env.workspace = output_gdb
arcpy.env.snapRaster = snap_raster
arcpy.env.extent = segment_fc
arcpy.env.cellSize = snap_raster
arcpy.env.overwriteOutput = True

# --- PROCESS EACH RASTER ---

for raster_path, prefix in raster_inputs:
    print(f"Processing: {os.path.basename(raster_path)}")

    # Define output table name
    table_name = f"ZStats_{prefix}_SMS" #SMS suffix to indicate version (e.g., SMSv7)

    # Full path for output table
    out_table = os.path.join(output_gdb, table_name)

    # Run Zonal Statistics as Table tool
    arcpy.sa.ZonalStatisticsAsTable(
        in_zone_data=segment_fc,
        zone_field=zone_field,
        in_value_raster=raster_path,
        out_table=out_table,
        ignore_nodata="DATA",
        statistics_type="ALL"
    )

    print(f" -> Output saved to: {out_table}")

print("\nAll zonal statistics tables created successfully.")
