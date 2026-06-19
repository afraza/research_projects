import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from pathlib import Path
import math

excel_file = "scientific_projects_iran.xlsx"  # change this
field_lookup_file = "field-of-study.xlsx"

sheet_name = 0
field_lookup_sheet = 0

disease_column = "disease"
field_code_column = "field-of-study-code"
field_name_column = "field-of-study"

BAR_COLORS = [
    "#3A7CA5",
    "#D1495B",
    "#EDAE49",
    "#00798C",
    "#7A5195",
    "#4D908E",
    "#F3722C",
    "#577590",
    "#90BE6D",
    "#B56576",
]


def get_bar_colors(count):
    return [BAR_COLORS[index % len(BAR_COLORS)] for index in range(count)]


def get_numbered_path(path):
    if not path.exists():
        return path

    counter = 1
    while True:
        new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def style_horizontal_bar_chart(ax):
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="x", linestyle="--", linewidth=0.7, alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar in ax.patches:
        width = bar.get_width()
        if width:
            ax.text(
                width,
                bar.get_y() + bar.get_height() / 2,
                int(width),
                ha="left",
                va="center",
                fontsize=8
            )

    ax.margins(x=0.14)


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
    "Cancer": "Cancer (general)",
})

df = df[df[disease_column] != "COVID-19"].copy()

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
        color=get_bar_colors(len(top_10_diseases)),
        edgecolor="#1F4E66",
        linewidth=0.8
    )

    ax.set_title(f"Top 10 Diseases - {field_name}")
    ax.set_xlabel("Number of Records")
    ax.set_ylabel("Disease")
    style_horizontal_bar_chart(ax)

for ax in axes[len(field_codes):]:
    ax.axis("off")

plt.tight_layout()

charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

output_path = get_numbered_path(
    charts_dir / "disease_top_10_diseases_in_top_20_field_of_studies.png"
)

plt.savefig(output_path, dpi=300)
plt.close()

print(f"\nChart saved to: {output_path}")

# Create pie chart for the field-of-study distribution.
field_labels = [
    code_to_field_name.get(code, f"Unknown field name for code {code}")
    for code in top_20_field_codes.index
]

plt.figure(figsize=(12, 12))
plt.pie(
    top_20_field_codes.values,
    labels=field_labels,
    autopct="%1.1f%%",
    startangle=90,
    counterclock=False
)
plt.title("Field-of-study Share Among Top 20 Field Codes")
plt.tight_layout()

pie_output_path = get_numbered_path(
    charts_dir / "disease_top_20_field_of_studies_pie.png"
)

plt.savefig(pie_output_path, dpi=300)
plt.close()

print(f"Pie chart saved to: {pie_output_path}")

# Create heatmap of top diseases across the top field-of-study codes.
top_10_overall_diseases = df[disease_column].value_counts().head(10).index
df_top_fields = df[df[field_code_column].isin(field_codes)].copy()
df_top_fields["Field-of-study"] = df_top_fields[field_code_column].map(
    lambda code: code_to_field_name.get(code, f"Field of Study Code {code}")
)

heatmap_data = pd.crosstab(
    df_top_fields["Field-of-study"],
    df_top_fields[disease_column]
)

heatmap_data = heatmap_data.reindex(
    index=field_labels,
    columns=top_10_overall_diseases,
    fill_value=0
)

fig, ax = plt.subplots(figsize=(16, 12))
image = ax.imshow(heatmap_data.values, cmap="YlOrRd", aspect="auto")

ax.set_title("Top Disease Counts by Field-of-study")
ax.set_xlabel("Disease")
ax.set_ylabel("Field-of-study")
ax.set_xticks(range(len(heatmap_data.columns)))
ax.set_xticklabels(heatmap_data.columns, rotation=45, ha="right")
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels(heatmap_data.index)

for row in range(heatmap_data.shape[0]):
    for col in range(heatmap_data.shape[1]):
        value = heatmap_data.iat[row, col]
        if value:
            ax.text(col, row, int(value), ha="center", va="center", fontsize=7)

fig.colorbar(image, ax=ax, label="Number of Records")
plt.tight_layout()

heatmap_output_path = get_numbered_path(
    charts_dir / "disease_top_diseases_by_field_of_study_heatmap.png"
)

plt.savefig(heatmap_output_path, dpi=300)
plt.close()

print(f"Heatmap chart saved to: {heatmap_output_path}")
