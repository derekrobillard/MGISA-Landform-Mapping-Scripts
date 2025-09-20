# MGISA Landform Mapping Scripts

This repository contains a curated set of Python scripts that supplement the semi-automated landform classification workflow developed for my MGISA research project. These scripts do not constitute a complete workflow on their own; rather, they were created to improve efficiency and reproducibility at key stages of the project. Tasks supported include preprocessing (e.g., automated TPI preparation), statistical analysis of geomorphometric variables, quantitative accuracy assessment of classifier outputs, and IoU-weighted ensemble classification. Each script is a snapshot of those used in the research.

**Note:** File paths have been generalized, but logic is unchanged. Scripts require execution within the ArcGIS Pro Python environment (e.g., `arcgispro-py3`) because they depend on ArcPy.

---

## Folder structure

### preprocessing/
The `preprocessing/` folder contains scripts used to prepare geomorphometric variables prior to statistical analysis and classification. In this study, only the TPI automation script is included, which standardizes the calculation, clamping, and normalization of Topographic Position Index rasters. While additional preprocessing scripts could be developed for other variables or DEM preparation, this folder documents the same preprocessing workflow implemented for this research.

- **`preprocess_tpi_automation.py`** — Automates Topographic Position Index (TPI) processing steps, including calculation from DEM and local mean, clamping to ±2σ, normalization to 0–255, and saving of intermediate and final rasters. Cited in Section 3.5.2 (Robillard, 2025).

---

### analysis/
The `analysis/` folder contains scripts used to quantify and visualize relationships between geomorphometric variables and landform classes. These scripts build upon the preprocessed raster and segment datasets, producing statistical summaries, merged tables, and plots that informed classifier training and evaluation. The workflow flows from correlation analysis of input rasters, to zonal statistics calculated by segment polygons, to merging and joining these statistics with reference classes, and finally to graphical exploration of class–variable relationships through violin plots.

- **`analyze_correlation.py`** — Computes global stats and Pearson correlation among geomorphometric rasters; exports CSVs and a heatmap. Cited in Section 3.5.2 (Robillard, 2025).
- **`zonalstats_1_batch_processing.py`** — Calculates zonal statistics for multiple geomorphometric rasters using segment polygons as zones; exports one statistics table per raster to the specified geodatabase. Cited in Section 3.5.8 (Robillard, 2025).
- **`zonalstats_2_merge_all.py`** — Merges the individual zonal statistics tables into a single flat table containing selected fields from each raster. Cited in Section 3.5.8 (Robillard, 2025).
- **`zonalstats_3_with_ref_classes.py`** — Appends reference class information (Schema D: CodeD, NameD, PERCENTAGE, gridcode) from the segment polygons to the merged zonal statistics table; outputs a table aligned with the final classification schema. Cited in Section 3.5.8 (Robillard, 2025).
- **`zonalstats_4_join_to_segment_polys.py`** — Joins selected zonal statistics fields (e.g., `Elev_MEAN`, `Elev_STDV`) from the merged stats table back onto the segment polygon feature class; enables mapping and visualization of geomorphometric attributes at the polygon level. Cited in Section 3.5.8 (Robillard, 2025).
- **`violinplots_segmentlevel_MEAN_byclass.py`** — Generates violin plots of segment-level mean geomorphometric variables grouped by landform class (Schema D); exports a letter-layout friendly figure with compact legend for inclusion in the thesis. Cited in Section 3.5.8 (Robillard, 2025).

---

### assessment/
The `assessment/` folder contains scripts used to evaluate the performance of both individual machine learning classifiers and the ensemble classifier (E5). These scripts generate per-class and overall accuracy metrics, as well as confusion matrix figures, based on intersections between predicted segment polygons and reference landform polygons. The workflow requires that the one-pass accuracy script be executed first to generate the necessary summary tables, followed by the confusion matrix script for figure production.

- **`accuracy_1pass_assessment.py`** — Performs a one-pass quantitative accuracy assessment by intersecting predicted segment polygons with reference landforms; produces per-class metrics (Producer’s Accuracy, User’s Accuracy, IoU, F1, FN/FP) and overall accuracy (OA). Can be applied to both individual ML classifiers (RT_D50, RT_D60, SVM_D50, SVM_D60) and the ensemble classifier (E5). Cited in Section 3.6.1 (Robillard, 2025).
- **`accuracy_confusion_matrix.py`** — Generates a row-normalized confusion matrix figure from the tables produced by the one-pass accuracy assessment script, showing the distribution of predicted vs. reference classes. Can be applied to both individual ML classifiers and the ensemble classifier (E5). Cited in Section 3.6.1 (Robillard, 2025).

---

### ensemble/
The `ensemble/` folder contains the script used to generate the E5 ensemble classification, which combines the outputs of the four best-performing ML classifiers (RT_D50, RT_D60, SVM_D50, SVM_D60). This method applies IoU-weighted voting to assign the most likely landform class to each segment and incorporates an additional rule to capture low-elevation river segments (WATER BODY) from the SVM-D60 classifier using the DEM. The ensemble workflow could only be completed after accuracy assessments for the four classifiers were finished, since those results provide the weights required for ensemble voting.

- **`ensemble_E5_classification.py`** — Generates the E5 ensemble classification by combining predictions from four ML classifiers (RT_D50, RT_D60, SVM_D50, SVM_D60) using IoU-weighted voting. Writes the final ensemble label (`E5`), source classifiers (`E5_src`), and ensemble score (`E5_score`) to the segment polygons, and applies an additional WATER BODY rule using the DEM to capture low-elevation river segments. Cited in Section 3.7.3 (Robillard, 2025).

---

## How to cite

If you use or adapt these scripts, please cite as follows:

Robillard, D. (2025). *MGISA landform mapping scripts* [Computer software]. GitHub. https://github.com/derekrobillard/MGISA-Landform-Mapping-Scripts
