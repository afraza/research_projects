import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import math

excel_file = "scientific_projects_iran.xlsx"  # change this
field_lookup_file = "field-of-study.xlsx"

sheet_name = 0
field_lookup_sheet = 0

disease_column = "disease"
field_code_column = "field-of-study-code"
field_name_column = "field-of-study"


def get_numbered_path(path):
    if not path.exists():
        return path

    counter = 1
    while True:
        new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


df = pd.read_excel(excel_file, sheet_name=sheet_name)

# Clean disease
df[disease_column] = df[disease_column].astype(str).str.strip()

invalid_values = {
    "",
    "-",
    "--",
    "---",
    "nan",
    "none",
    "null",
    "n/a",
    "na",
    "#n/a",
}

df = df[
    df[disease_column].notna()
    & (~df[disease_column].str.lower().isin(invalid_values))
].copy()

df[disease_column] = df[disease_column].str.lower().str.title()
df[disease_column] = df[disease_column].replace({
    "Covid-19": "COVID-19",
})

# Clean field-of-study-code in main data
df[field_code_column] = df[field_code_column].astype(str).str.strip()

df = df[
    ~df[field_code_column].str.lower().isin(invalid_values)
].copy()

df[field_code_column] = pd.to_numeric(df[field_code_column], errors="coerce")
df = df[df[field_code_column].notna()].copy()
df[field_code_column] = df[field_code_column].astype(int)

# Load lookup file
field_lookup = pd.read_excel(field_lookup_file, sheet_name=field_lookup_sheet)

field_lookup[field_code_column] = pd.to_numeric(
    field_lookup[field_code_column],
    errors="coerce"
)

field_lookup = field_lookup.dropna(subset=[field_code_column]).copy()
field_lookup[field_code_column] = field_lookup[field_code_column].astype(int)

field_lookup = field_lookup.dropna(subset=[field_name_column]).copy()
field_lookup[field_name_column] = field_lookup[field_name_column].astype(str).str.strip()

field_lookup = field_lookup[
    ~field_lookup[field_name_column].str.lower().isin(invalid_values)
].copy()

code_to_field_name = dict(
    zip(
        field_lookup[field_code_column],
        field_lookup[field_name_column]
    )
)

# Find top 20 codes from main data
top_20_field_codes = df[field_code_column].value_counts().head(20)

print("20 most frequent field-of-study codes:")
for code, count in top_20_field_codes.items():
    field_name = code_to_field_name.get(code, f"Unknown field name for code {code}")
    print(f"{code} - {field_name}: {count}")

field_codes = top_20_field_codes.index.tolist()

cols = 2
rows = math.ceil(len(field_codes) / cols)

fig, axes = plt.subplots(rows, cols, figsize=(18, rows * 5))
axes = axes.flatten()

for ax, field_code in zip(axes, field_codes):
    field_data = df[df[field_code_column] == field_code]

    top_10_diseases = field_data[disease_column].value_counts().head(10)

    field_name = code_to_field_name.get(
        field_code,
        f"Field of Study Code {field_code}"
    )

    top_10_diseases.sort_values().plot(
        kind="barh",
        ax=ax,
        color="#3A7CA5"
    )

    ax.set_title(f"Top 10 Diseases - {field_name}")
    ax.set_xlabel("Number of Records")
    ax.set_ylabel("Disease")

for ax in axes[len(field_codes):]:
    ax.axis("off")

plt.tight_layout()

charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

output_path = get_numbered_path(
    charts_dir / "top_10_diseases_in_top_20_field_of_studies.png"
)

plt.savefig(output_path, dpi=300)
plt.show()

print(f"\nChart saved to: {output_path}")