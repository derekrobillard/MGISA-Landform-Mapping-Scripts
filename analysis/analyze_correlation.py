# ---------------------------------------------------------------------
# Title: analyze_correlation.py  (original: CorrelationAnalysis_Skwawka1_7rasters_v1.py)
# Author: Derek Robillard, with OpenAI assistance
# Purpose: Computes global stats and a Pearson correlation matrix across multiple rasters,
#          producing CSV tables and a heatmap. Helps with geomorphometric variable selection.
# Notes: Snapshot of the exact script used for the MGISA final report (Section 3.5.2).
#        Logic unchanged; only output filenames generalized.
# Inputs: Update raster_dict paths to your own project data before running.
# Outputs: correlation_matrix.csv, global_stats.csv, global_stats_full.csv,
#          correlation_heatmap.png, high_corr_pairs.csv (if any).
# Citation: Robillard (2025). *MGISA landform mapping scripts* [Computer software]. GitHub.
# ---------------------------------------------------------------------

import arcpy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Allow overwriting of outputs
arcpy.env.overwriteOutput = True

# ---------------------------------------------------------------------
# STEP 0: DEFINE OUTPUT DIRECTORY
# ---------------------------------------------------------------------
# All output CSV and image files will be saved here.
# Replace with the path to your own output folder.

output_dir = r"C:\path\to\outputs"
os.makedirs(output_dir, exist_ok=True)

# ---------------------------------------------------------------------
# STEP 1: DEFINE INPUT RASTERS
# ---------------------------------------------------------------------
# Replace each of the paths below with your own raster locations.
# These should all have the same resolution and aligned extents.

raster_dict = {
    "Elevation": r"C:\path\to\DEMs\YourDEM.tif",
    "Slope": r"C:\path\to\Derived_Rasters\Slope\Slope.gdb\Slope",
    "TPI1_50m": r"C:\path\to\Derived_Rasters\TPI\TPI.gdb\TPI_50m",
    "CurvT": r"C:\path\to\Derived_Rasters\Curvature\Curvature.gdb\CurvT_7m",
    "TPI2_Annulus": r"C:\path\to\Derived_Rasters\TPI\TPI.gdb\TPI_5m_30m_Annulus",
    "SRI": r"C:\path\to\Derived_Rasters\SRI\SRI.gdb\SRI_7m",
    "CurvPr": r"C:\path\to\Derived_Rasters\Curvature\Curvature.gdb\CurvProf_7m"
}

# ---------------------------------------------------------------------
# STEP 2: LOAD EACH RASTER INTO A NUMPY ARRAY
# ---------------------------------------------------------------------
# We use RasterToNumPyArray() to convert rasters into arrays.
# This enables pixel-wise statistical comparisons and is the foundation
# for stacking multiple layers for correlation analysis.
# NoData values are converted to NaN for clean handling.

arrays = {}
for name, path in raster_dict.items():
    print(f"Loading raster: {name}")
    arr = arcpy.RasterToNumPyArray(path, nodata_to_value=np.nan).astype(np.float32)
    arrays[name] = arr

# ---------------------------------------------------------------------
# STEP 3: ALIGN ALL ARRAYS TO THE SHARED SPATIAL EXTENT
# ---------------------------------------------------------------------
# If extents differ slightly, this crops each array to the smallest shared number of 
# rows and columns to ensure proper stacking.

min_rows = min(arr.shape[0] for arr in arrays.values())
min_cols = min(arr.shape[1] for arr in arrays.values())

for key in arrays:
    arrays[key] = arrays[key][:min_rows, :min_cols]

# ---------------------------------------------------------------------
# STEP 4: STACK RASTER PIXEL VALUES INTO A PANDAS DATAFRAME
# ---------------------------------------------------------------------
# This flattens each 2D array into a 1D vector, one per raster.
# The resulting DataFrame (`df`) represents the pixel-aligned values across all rasters.
# Rows with any NaN (NoData) are dropped to avoid bias in correlation analysis.

df = pd.DataFrame({name: arr.flatten() for name, arr in arrays.items()})
df = df.dropna()
print(f"✅ {len(df)} valid pixels retained for correlation analysis.")

# ---------------------------------------------------------------------
# STEP 5: Z-SCORE NORMALIZATION
# ---------------------------------------------------------------------
# 📈 Why normalize?
# Terrain variables differ in units and magnitude (e.g., elevation in meters vs curvature).
# Z-score normalization (mean = 0, std = 1) ensures variables contribute equally to correlation.

df_z = (df - df.mean()) / df.std()

# ---------------------------------------------------------------------
# STEP 6: GLOBAL STATISTICS AND CORRELATION MATRIX
# ---------------------------------------------------------------------
# Compute basic summary statistics (mean, std) and full descriptive stats (min, max).
# Calculate the Pearson correlation coefficient (linear association) between all pairs.

summary_stats = df.describe().T[['mean', 'std']]
full_stats = df.describe().T[['min', 'max', 'mean', 'std']]
correlation_matrix = df.corr(method='pearson')

# ---------------------------------------------------------------------
# STEP 7: VISUALIZE CORRELATIONS AS A HEATMAP
# ---------------------------------------------------------------------
# A color-coded matrix makes it easy to identify strongly related or redundant variables.
# Blue = negative correlation; Red = positive; White = neutral.

plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm", square=True)
plt.title("Global Pearson Correlation Matrix (Z-score Normalized)", fontsize=14)
plt.tight_layout()

# Save figure to your specified output folder
heatmap_path = os.path.join(output_dir, "correlation_heatmap.png")
plt.savefig(heatmap_path, dpi=300)
plt.show()

# ---------------------------------------------------------------------
# STEP 8: EXPORT OUTPUT TABLES TO CSV
# ---------------------------------------------------------------------
# These files can be included in your Methods, Results, or Appendix.
# They provide transparent justification for your variable selection choices.

summary_stats.to_csv(os.path.join(output_dir, "global_stats.csv"))
full_stats.to_csv(os.path.join(output_dir, "global_stats_full.csv"))
correlation_matrix.to_csv(os.path.join(output_dir, "correlation_matrix.csv"))

# ---------------------------------------------------------------------
# STEP 9: IDENTIFY HIGHLY CORRELATED PAIRS (|r| > 0.85)
# ---------------------------------------------------------------------
# Useful for feature selection: strong correlation means redundancy.
# You can choose to exclude one of the two strongly correlated variables 
# from your composite image or machine learning input.

threshold = 0.85
# Extract upper triangle of matrix (no repeats)
upper_tri = correlation_matrix.where(np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool))

# Stack into long-form table
high_corr_pairs = upper_tri.stack().reset_index()
high_corr_pairs.columns = ['Variable 1', 'Variable 2', 'Correlation']
high_corr_filtered = high_corr_pairs[high_corr_pairs['Correlation'].abs() > threshold]

# Print or export results
if not high_corr_filtered.empty:
    print("\n⚠️ Highly correlated variable pairs (|r| > 0.85):")
    print(high_corr_filtered.to_string(index=False))
    high_corr_filtered.to_csv(os.path.join(output_dir, "high_corr_pairs.csv"), index=False)
else:
    print("\n✅ No highly correlated variable pairs exceeded the threshold (|r| > 0.85).")
