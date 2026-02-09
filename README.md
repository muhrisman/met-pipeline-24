# MET Pipeline

Documentation for the MET statistical analysis pipeline.

---

## Overview

The MET Pipeline is a backend-oriented analytical framework developed to evaluate the quality, consistency, and usability of SIPSN (Sistem Informasi Pengelolaan Sampah Nasional) waste data across regions in Indonesia.

The pipeline applies automated data quality scoring, statistical analysis, and spatial methods to identify data gaps, inconsistencies, and regional patterns. The outputs are designed to support evidence-based decision making and to be consumed by downstream tools such as the Methane Emission Toolbox and web-based analytical dashboards.

This repository currently focuses on documentation of the analytical design, scope, and methodology.

---

## Objectives

The main objectives of the MET Pipeline are to:

- Evaluate the quality and consistency of publicly available SIPSN waste data
- Identify missing data, outliers, and reporting inconsistencies across regions and years
- Provide automated and reproducible data quality indicators
- Generate analytical features that can support spatial analysis and policy insights
- Enable integration with external tools and applications through structured outputs

---

## Data Sources

The analysis is based on publicly available data from SIPSN, covering national and subnational waste management reporting.

### Administrative Levels
- National
- Province
- Kabupaten / Kota

### Main Datasets
- Timbulan Sampah
- Sumber Sampah
- Komposisi Sampah
- Capaian Pengelolaan Sampah
- Fasilitas Pengelolaan Sampah

The analysis primarily covers reporting years 2019–2024, with variations depending on dataset availability.

---

## Analysis Scope

### Data Quality Evaluation

Each dataset is evaluated using a standardized and automated framework consisting of:

- Completeness  
  Measures whether required variables and time periods are filled for each region.

- Report Rate  
  Measures whether a region participates in reporting in a given year.

- Coverage  
  Measures how many regions or variables are represented within a dataset.

- Outlier and Plausibility Checks  
  Identifies extreme or implausible values using statistical thresholds and anomaly detection methods.

These indicators are combined into a weighted data quality score on a scale of 1–10, categorized as high, medium, or low quality.

---

### Descriptive and Exploratory Analysis

The pipeline includes:

- Descriptive statistics
- Time series analysis of reporting trends
- Missing value analysis by dataset and variable
- Cross-validation between related datasets
- Correlation analysis between reporting intensity and waste generation

---

### Advanced Statistical and Spatial Analysis

The pipeline supports:

- Clustering analysis to group regions with similar patterns
- Principal Component Analysis (PCA) to reduce multiple indicators into interpretable components
- Spatial regression methods, including Ordinary Least Squares (OLS) and Geographically Weighted Regression (GWR)
- Advanced outlier detection using multivariate techniques

---

## Outputs

The MET Pipeline produces structured outputs including:

- Data quality scores per region and dataset
- Flags for missing data and anomalous values
- Cluster labels and regional typologies
- PCA component scores
- Spatial regression coefficients and diagnostics
- Aggregated statistical summaries

Outputs are designed to be machine-readable and suitable for visualization.

---

## System Integration

The analytical outputs are intended to be exposed through an API layer and integrated into external tools such as analytical dashboards and methane emission modeling applications.

---

## Repository Status

This repository is currently focused on documentation. Backend implementation and API development will be added in future iterations.

---

## Next Steps

Future work includes finalizing analytical methodology documentation, defining output schemas, and aligning analytical outputs with downstream applications.

## Data Source for Development

During development, the analysis logic is validated using locally available Excel files. The analysis layer is designed to operate on standardized dataframes so that the data source can later be switched to an API without changing the core calculation logic.