# Data Quality Metrics

This project distinguishes between two different concepts of data quality
that are often conflated in reporting systems.

## Field Completeness

Field completeness measures whether a required variable is filled
for records that exist in the dataset.

Example:
- Timbulan Sampah Tahunan(ton) is present for all reported rows
- Field-level completeness for this variable is therefore 100%

This metric reflects data entry consistency, not reporting coverage.

## Coverage (Reporting Completeness)

Coverage measures whether an expected reporting entity
(e.g. kabupaten/kota) appears in the dataset for a given year.

Coverage is computed by comparing reported data against
a reference list of all valid kabupaten/kota.

This metric captures:
- missing reporting regions
- uneven reporting across years
- true data availability gaps

## Design Implication

For SIPSN timbulan data:
- Field completeness is trivial
- Coverage is the primary quality signal

Downstream analyses should prioritize coverage-based indicators
when assessing data reliability.