import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import math

# -----------------------------
# Settings
# -----------------------------
excel_file = "scientific_projects_iran.xlsx"
academic_rank_lookup_file = "Academic-rank.xlsx"

sheet_name = 0
academic_rank_lookup_sheet = 0

disease_column = "disease"
academic_rank_code_column = "Academic-rank-code"
academic_rank_name_column = "Academic-rank"

# -----------------------------
# Helper function for numbered filenames
# -----------------------------
def get_numbered_path(path):
    if not path.exists():
        return path

    counter = 1
    while True:
        new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


# -----------------------------
# Load main data
# -----------------------------
df = pd.read_excel(excel_file, sheet_name=sheet_name)

# -----------------------------
# Clean disease field
# -----------------------------
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

df[disease_column] = df[disease_column].astype(str).str.strip()

df = df[
    df[disease_column].notna()
    & (~df[disease_column].str.lower().isin(invalid_values))
].copy()

df[disease_column] = df[disease_column].str.lower().str.title()

df[disease_column] = df[disease_column].replace({
    "Covid-19": "COVID-19",
})

# -----------------------------
# Clean Academic-rank-code
# -----------------------------
df[academic_rank_code_column] = df[academic_rank_code_column].astype(str).str.strip()

df = df[
    ~df[academic_rank_code_column].str.lower().isin(invalid_values)
].copy()

df[academic_rank_code_column] = pd.to_numeric(
    df[academic_rank_code_column],
    errors="coerce"
)

df = df[df[academic_rank_code_column].notna()].copy()
df[academic_rank_code_column] = df[academic_rank_code_column].astype(int)

# -----------------------------
# Load Academic-rank lookup file
# -----------------------------
academic_rank_lookup = pd.read_excel(
    academic_rank_lookup_file,
    sheet_name=academic_rank_lookup_sheet
)

academic_rank_lookup[academic_rank_code_column] = pd.to_numeric(
    academic_rank_lookup[academic_rank_code_column],
    errors="coerce"
)

academic_rank_lookup = academic_rank_lookup.dropna(
    subset=[academic_rank_code_column]
).copy()

academic_rank_lookup[academic_rank_code_column] = academic_rank_lookup[
    academic_rank_code_column
].astype(int)

academic_rank_lookup = academic_rank_lookup.dropna(
    subset=[academic_rank_name_column]
).copy()

academic_rank_lookup[academic_rank_name_column] = academic_rank_lookup[
    academic_rank_name_column
].astype(str).str.strip()

academic_rank_lookup = academic_rank_lookup[
    ~academic_rank_lookup[academic_rank_name_column].str.lower().isin(invalid_values)
].copy()

code_to_rank_name = dict(
    zip(
        academic_rank_lookup[academic_rank_code_column],
        academic_rank_lookup[academic_rank_name_column]
    )
)

df["Academic-rank-name"] = df[academic_rank_code_column].map(
    lambda code: code_to_rank_name.get(code, f"Academic Rank Code {code}")
)

# Keep academic ranks ordered by code 1 to 5
ordered_rank_codes = [1, 2, 3, 4, 5]

ordered_rank_names = [
    code_to_rank_name.get(code, f"Academic Rank Code {code}")
    for code in ordered_rank_codes
]

df = df[df[academic_rank_code_column].isin(ordered_rank_codes)].copy()

df["Academic-rank-name"] = pd.Categorical(
    df["Academic-rank-name"],
    categories=ordered_rank_names,
    ordered=True
)

# -----------------------------
# Chart 1:
# Academic-rank distribution in each top 10 disease
# -----------------------------
top_10_diseases = df[disease_column].value_counts().head(10).index.tolist()

df_top_diseases = df[df[disease_column].isin(top_10_diseases)].copy()

rank_by_disease = pd.crosstab(
    df_top_diseases[disease_column],
    df_top_diseases["Academic-rank-name"]
)

rank_by_disease = rank_by_disease.reindex(
    columns=ordered_rank_names,
    fill_value=0
)

rank_by_disease = rank_by_disease.loc[top_10_diseases]

plt.figure(figsize=(16, 8))

rank_by_disease.plot(
    kind="bar",
    stacked=True,
    figsize=(16, 8),
    colormap="tab20"
)

plt.title("Academic-rank Distribution in 10 Most Frequent Diseases")
plt.xlabel("Disease")
plt.ylabel("Number of Records")
plt.xticks(rotation=45, ha="right")
plt.legend(title="Academic-rank", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()

charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

output_path_1 = get_numbered_path(
    charts_dir / "academic_rank_distribution_in_top_10_diseases.png"
)

plt.savefig(output_path_1, dpi=300)
plt.show()

print(f"Chart saved to: {output_path_1}")

# -----------------------------
# Chart 2:
# Top 10 diseases in each Academic-rank
# -----------------------------
academic_ranks = ordered_rank_names

cols = 2
rows = math.ceil(len(academic_ranks) / cols)

fig, axes = plt.subplots(rows, cols, figsize=(18, rows * 5))
axes = axes.flatten()

for ax, academic_rank in zip(axes, academic_ranks):
    rank_data = df[df["Academic-rank-name"] == academic_rank]

    top_10_for_rank = rank_data[disease_column].value_counts().head(10)

    top_10_for_rank.sort_values().plot(
        kind="barh",
        ax=ax,
        color="#3A7CA5"
    )

    ax.set_title(f"Top 10 Diseases - {academic_rank}")
    ax.set_xlabel("Number of Records")
    ax.set_ylabel("Disease")

for ax in axes[len(academic_ranks):]:
    ax.axis("off")

plt.tight_layout()

output_path_2 = get_numbered_path(
    charts_dir / "top_10_diseases_by_academic_rank.png"
)

plt.savefig(output_path_2, dpi=300)
plt.show()

print(f"Chart saved to: {output_path_2}")