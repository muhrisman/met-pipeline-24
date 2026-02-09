# Analysis Scope

This document describes the scope of statistical and spatial analyses implemented in the MET Pipeline. The analyses are designed to evaluate the quality, consistency, and analytical usability of SIPSN waste data across regions in Indonesia, and to generate standardized outputs that can support monitoring, comparison, and downstream analytical tools.

## Data Source for Development

During development, the analysis logic is validated using locally available Excel files. The analysis layer is designed to operate on standardized dataframes so that the data source can later be switched to an API without changing the core calculation logic.