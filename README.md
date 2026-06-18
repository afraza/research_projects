# research_projects

Statistical analysis and visualization scripts for Iranian academic research project data.

## Overview

This project contains standalone Python scripts that read local Excel datasets and generate charts for disease, keyword, academic-rank, methodology, field-of-study, university, macroregion, university-tier, and H-index analyses.

The source Excel workbooks and generated chart outputs are intentionally not tracked in Git. Keep the required `.xlsx` files in the project root when running the scripts locally.

## Requirements

- Python 3.10 or newer
- pandas
- matplotlib
- seaborn
- openpyxl

Install dependencies with:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Required Local Data Files

These files are expected in the project root and are intentionally ignored by Git:

- `scientific_projects_iran.xlsx`
- `Academic-rank.xlsx`
- `field-of-study.xlsx`
- `Methodology-code.xlsx`
- `university_lookup.xlsx`

The main workbook currently uses a `MainData` sheet with columns such as:

- `disease`
- `keyword1`, `keyword2`, `keyword3`
- `university-code`
- `macroregion`
- `university-tier`
- `field-of-study-code`
- `Academic-rank-code`
- `Methodology-code`
- `H-index`

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── *.py
├── *.xlsx                 # local input data, ignored by Git
└── charts/                # generated outputs, ignored by Git
```

## Script Groups

National charts:

- `disease_freq_chart.py`
- `keywords-national.py`

Disease charts by category:

- `disease-by-academic-rank.py`
- `disease-by-field-of-study.py`
- `disease-by-h-index.py`
- `disease-by-methodology.py`
- `diseases_by_macroregion.py`
- `diseases_by_tier.py`
- `diseases_by_university.py`

Keyword charts by category:

- `keywords-by-academic-rank.py`
- `keywords-by-field-of-study.py`
- `keywords-by-h-index.py`
- `keywords-by-macroregion.py`
- `keywords-by-methodology.py`
- `keywords-by-university-tier.py`
- `keywords-by-university.py`

Placeholder or currently empty scripts:

- `keywords_stats_charts.py`
- `main.py`
- `sci-fields-national.py`
- `scientific_field_stat_charts.py`

## Usage

Run scripts from the project root so relative paths resolve correctly:

```bash
python disease_freq_chart.py
python keywords-national.py
python keywords-by-university.py
```

Scripts write chart images under `charts/`. Existing output filenames may be numbered to avoid overwriting previous chart files.

## Notes

- Excel files are ignored intentionally because they are local data inputs.
- Chart outputs are ignored intentionally because they are generated artifacts.
- Some script filenames contain hyphens. They can be run directly with `python script-name.py`, but they cannot be imported as normal Python modules.
