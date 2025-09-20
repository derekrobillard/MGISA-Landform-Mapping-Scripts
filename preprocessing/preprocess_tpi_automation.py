# Title: preprocess_tpi_automation.py  (original: Automate_TPI_Processing_MimicGPworkflow_20250618.py)
# Author: Derek Robillard, with OpenAI assistance
# Purpose: Automates Topographic Position Index (TPI) processing steps:
#          (1) DEM - LocalMean → TPI, (2) clamp to ±2σ, (3) normalize to 0–255,
#          and (4) save intermediate and final rasters using a consistent naming scheme.
# Notes: Snapshot of the exact script used for the MGISA final report.
#        Logic unchanged; only file paths and dataset names generalized.
# Inputs: Update the placeholder paths below (DEM, local mean raster, output GDB).
# Outputs: TPI raster, clamped TPI raster, and normalized TPI raster (float).
# Citation: Robillard (2025). *MGISA landform mapping scripts* [Computer software]. GitHub.

import arcpy
import os

# === Set Environment Settings ===
arcpy.env.overwriteOutput = True

# Set consistent environments for projection, extent, resolution, and raster alignment
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(3157)  # NAD_1983_CSRS_UTM_Zone_10N (EPSG:3157)
arcpy.env.extent = r"C:\path\to\DEMs\YourDEM.tif"       # <-- set to your DEM (or other reference raster)
arcpy.env.cellSize = 1                                   # adjust if your DEM cell size differs
arcpy.env.snapRaster = r"C:\path\to\DEMs\YourDEM.tif"    # <-- set to your DEM (or other reference raster)
arcpy.env.compression = "LZ77"                           # FGDB raster compression (informational)

# === Inputs ===
dem = r"C:\path\to\DEMs\YourDEM.tif"                                    # DEM raster
local_mean = r"C:\path\to\Derived_Rasters\TPI.gdb\MEAN_5m_30m_Annulus"   # focal/local mean raster
output_gdb = r"C:\path\to\Derived_Rasters\TPI.gdb"                       # output file geodatabase

# Variant label for output naming (e.g., '50m' or '5m_30m_Annulus')
variant_name = "5m_30m_Annulus"  # modify as needed

# === Output Paths ===
# Dataset names are generalized (no study-area prefix). Adjust if you prefer a different naming style.
tpi_raster = os.path.join(output_gdb, f"TPI_{variant_name}")
clamped_raster = os.path.join(output_gdb, f"{tpi_raster}_2Sclamp")
normalized_raster = os.path.join(output_gdb, f"{clamped_raster}_norm255")

# === Step 1: DEM - Local Mean ===
# Calculate the Topographic Position Index (TPI) by subtracting the focal mean
# (local mean elevation) from the DEM. This enhances relative elevation differences,
# highlighting convex and concave landforms at the specified scale.
tpi = arcpy.sa.Raster(dem) - arcpy.sa.Raster(local_mean)
tpi.save(tpi_raster)

# Force a fresh re-load from disk (often helpful in FGDB workflows)
tpi = arcpy.sa.Raster(tpi_raster)

# === Step 2: Clamp to ±2 SD ===
# This step truncates extreme outlier values by clamping the TPI raster
# to within two standard deviations (±2σ) of its mean.
mean = float(arcpy.management.GetRasterProperties(tpi, "MEAN").getOutput(0))
stddev = float(arcpy.management.GetRasterProperties(tpi, "STD").getOutput(0))

lower_limit = mean - 2 * stddev
upper_limit = mean + 2 * stddev

tpi_clamped = arcpy.sa.Con(
    tpi < lower_limit, lower_limit,
    arcpy.sa.Con(tpi > upper_limit, upper_limit, tpi)
)
tpi_clamped.save(clamped_raster)

# Re-load clamped raster
tpi_clamped = arcpy.sa.Raster(clamped_raster)

# === Step 3: Normalize to 0–255 using ±2σ centered transformation ===
# This formula maps -2σ to 0, +2σ to 255, and 0 (mean) to ~127.5
# Formula: ((value - mean) / (2 * stddev)) * 127.5 + 127.5
mean_val = float(arcpy.management.GetRasterProperties(tpi_clamped, "MEAN").getOutput(0))
stddev_val = float(arcpy.management.GetRasterProperties(tpi_clamped, "STD").getOutput(0))

normalized = ((tpi_clamped - mean_val) / (2 * stddev_val)) * 127.5 + 127.5

# Save the normalized float raster
normalized.save(normalized_raster)

# Re-load normalized raster if needed
normalized = arcpy.sa.Raster(normalized_raster)

print(f"✅ Finished normalized raster (float): {normalized_raster}")

# -----------------------------------------------------------------------------
# Usage (example):
# 1) Set 'dem', 'local_mean', and 'output_gdb' to your own paths.
# 2) Optionally change 'variant_name' to reflect your scale (e.g., '50m').
# 3) Run in the ArcGIS Pro Python environment (arcpy required).
# 4) Outputs will be written into your 'output_gdb'.
# -----------------------------------------------------------------------------