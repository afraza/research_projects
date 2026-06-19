import math
import textwrap
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# -----------------------------
# Settings
# -----------------------------
excel_file = "scientific_projects_iran.xlsx"
sheet_name = 0

disease_column = "disease"

sci_field_lookup_file = "sci-field.xlsx"
sci_field_lookup_fallback_file = "sci-field.xslx"
sci_field_lookup_sheet = 0

sci_field_code_columns = [
    "sci-field-code1",
    "sci-field-code2",
    "sci-field-code3",
]

sci_field_code_column = "sci-field-code"
sci_field_name_column = "sci-field"

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
    "#6D597A",
    "#43AA8B",
    "#F9C74F",
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


def clean_text_series(series):
    return series.astype(str).str.strip()


def normalize_code(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()
    if text.lower() in invalid_values:
        return pd.NA

    numeric_value = pd.to_numeric(text, errors="coerce")
    if pd.isna(numeric_value):
        return text

    if float(numeric_value).is_integer():
        return str(int(numeric_value))

    return str(numeric_value)


def wrap_labels(labels, width=28):
    return ["\n".join(textwrap.wrap(str(label), width=width)) for label in labels]


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

    ax.margins(x=0.16)


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

# -----------------------------
# Load and clean data
# -----------------------------
df = pd.read_excel(excel_file, sheet_name=sheet_name)

missing_sci_field_columns = [
    column for column in sci_field_code_columns if column not in df.columns
]

if missing_sci_field_columns:
    raise ValueError(
        "Missing scientific field code columns in main data: "
        + ", ".join(missing_sci_field_columns)
    )

lookup_path = Path(sci_field_lookup_file)
if not lookup_path.exists():
    fallback_path = Path(sci_field_lookup_fallback_file)
    if fallback_path.exists():
        lookup_path = fallback_path

sci_field_lookup = pd.read_excel(lookup_path, sheet_name=sci_field_lookup_sheet)

lookup_missing_columns = {
    sci_field_code_column,
    sci_field_name_column,
} - set(sci_field_lookup.columns)

if lookup_missing_columns:
    raise ValueError(
        "Missing columns in scientific field lookup file: "
        + ", ".join(sorted(lookup_missing_columns))
    )

sci_field_lookup[sci_field_code_column] = sci_field_lookup[
    sci_field_code_column
].map(normalize_code)

sci_field_lookup[sci_field_name_column] = clean_text_series(
    sci_field_lookup[sci_field_name_column]
)

sci_field_lookup = sci_field_lookup[
    sci_field_lookup[sci_field_code_column].notna()
    & sci_field_lookup[sci_field_name_column].notna()
    & (~sci_field_lookup[sci_field_name_column].str.lower().isin(invalid_values))
].copy()

code_to_sci_field_name = dict(
    zip(
        sci_field_lookup[sci_field_code_column],
        sci_field_lookup[sci_field_name_column]
    )
)

all_scientific_fields = sci_field_lookup[sci_field_name_column].drop_duplicates()

df[disease_column] = clean_text_series(df[disease_column])

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

df["_record_id"] = df.index

long_df = df.melt(
    id_vars=["_record_id", disease_column],
    value_vars=sci_field_code_columns,
    var_name="sci_field_slot",
    value_name=sci_field_code_column
)

long_df[sci_field_code_column] = long_df[sci_field_code_column].map(normalize_code)

long_df = long_df[
    long_df[sci_field_code_column].notna()
    & (~long_df[sci_field_code_column].astype(str).str.lower().isin(invalid_values))
].copy()

long_df = long_df.drop_duplicates(
    subset=["_record_id", disease_column, sci_field_code_column]
)

long_df[sci_field_name_column] = long_df[sci_field_code_column].map(
    lambda code: code_to_sci_field_name.get(code, f"Unknown Scientific Field {code}")
)

top_10_diseases = df[disease_column].value_counts().head(10).index
top_20_diseases = df[disease_column].value_counts().head(20).index

charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

# -----------------------------
# Chart 1:
# All scientific fields in each top 10 disease
# -----------------------------
cols = 2
rows = math.ceil(len(top_10_diseases) / cols)

fig, axes = plt.subplots(rows, cols, figsize=(20, rows * 6.2))
axes = axes.flatten()

for ax, disease in zip(axes, top_10_diseases):
    disease_data = long_df[long_df[disease_column] == disease]
    field_counts = disease_data[sci_field_name_column].value_counts().reindex(
        all_scientific_fields,
        fill_value=0
    )
    sorted_field_counts = field_counts.sort_values()

    sorted_field_counts.plot(
        kind="barh",
        ax=ax,
        color=get_bar_colors(len(sorted_field_counts)),
        edgecolor="#1F4E66",
        linewidth=0.8
    )

    ax.set_title(f"Scientific Fields - {disease}")
    ax.set_xlabel("Number of Records")
    ax.set_ylabel("Scientific Field")
    ax.set_yticklabels(wrap_labels(sorted_field_counts.index, width=30))
    style_horizontal_bar_chart(ax)

for ax in axes[len(top_10_diseases):]:
    ax.axis("off")

plt.tight_layout()

output_path_1 = get_numbered_path(
    charts_dir / "disease_scientific_fields_by_top_10_diseases_bar_chart.png"
)

plt.savefig(output_path_1, dpi=300)
plt.close()

print(f"Chart saved to: {output_path_1}")

# -----------------------------
# Chart 2:
# Top 10 diseases in each scientific field
# -----------------------------
rows = math.ceil(len(all_scientific_fields) / cols)

fig, axes = plt.subplots(rows, cols, figsize=(20, rows * 5.5))
axes = axes.flatten()

for ax, scientific_field in zip(axes, all_scientific_fields):
    field_data = long_df[long_df[sci_field_name_column] == scientific_field]
    top_diseases = field_data[disease_column].value_counts().head(10)
    sorted_top_diseases = top_diseases.sort_values()

    sorted_top_diseases.plot(
        kind="barh",
        ax=ax,
        color=get_bar_colors(len(sorted_top_diseases)),
        edgecolor="#1F4E66",
        linewidth=0.8
    )

    ax.set_title(
        "Top 10 Diseases - "
        + "\n".join(textwrap.wrap(str(scientific_field), width=42))
    )
    ax.set_xlabel("Number of Records")
    ax.set_ylabel("Disease")
    ax.set_yticklabels(wrap_labels(sorted_top_diseases.index, width=30))
    style_horizontal_bar_chart(ax)

for ax in axes[len(all_scientific_fields):]:
    ax.axis("off")

plt.tight_layout()

output_path_2 = get_numbered_path(
    charts_dir / "disease_top_10_diseases_by_scientific_fields_bar_chart.png"
)

plt.savefig(output_path_2, dpi=300)
plt.close()

print(f"Chart saved to: {output_path_2}")

# -----------------------------
# Chart 3:
# Heatmap of top 20 diseases vs all scientific fields
# -----------------------------
df_top_heatmap = long_df[
    long_df[disease_column].isin(top_20_diseases)
    & long_df[sci_field_name_column].isin(all_scientific_fields)
].copy()

heatmap_data = pd.crosstab(
    df_top_heatmap[disease_column],
    df_top_heatmap[sci_field_name_column]
)

heatmap_data = heatmap_data.reindex(
    index=top_20_diseases,
    columns=all_scientific_fields,
    fill_value=0
)

fig, ax = plt.subplots(figsize=(22, 15))
image = ax.imshow(heatmap_data.values, cmap="YlOrRd", aspect="auto")

ax.set_title("20 Most Frequent Diseases by All Scientific Fields")
ax.set_xlabel("Scientific Field")
ax.set_ylabel("Disease")
ax.set_xticks(range(len(heatmap_data.columns)))
ax.set_xticklabels(wrap_labels(heatmap_data.columns, width=18), rotation=45, ha="right")
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels(wrap_labels(heatmap_data.index, width=28))

for row in range(heatmap_data.shape[0]):
    for col in range(heatmap_data.shape[1]):
        value = heatmap_data.iat[row, col]
        if value:
            ax.text(col, row, int(value), ha="center", va="center", fontsize=7)

fig.colorbar(image, ax=ax, label="Number of Records")
plt.tight_layout()

output_path_3 = get_numbered_path(
    charts_dir / "disease_top_20_diseases_by_scientific_fields_heatmap.png"
)

plt.savefig(output_path_3, dpi=300)
plt.close()

print(f"Heatmap chart saved to: {output_path_3}")

# -----------------------------
# Chart 4:
# 100% stacked bar chart of all scientific fields in top 10 diseases
# -----------------------------
stacked_data = heatmap_data.loc[top_10_diseases, all_scientific_fields]
stacked_percent = stacked_data.div(stacked_data.sum(axis=1), axis=0).fillna(0) * 100

fig, ax = plt.subplots(figsize=(18, 9))
stacked_percent.plot(
    kind="bar",
    stacked=True,
    ax=ax,
    color=get_bar_colors(len(all_scientific_fields)),
    edgecolor="white",
    linewidth=0.5
)

ax.set_title("Scientific Field Composition in 10 Most Frequent Diseases")
ax.set_xlabel("Disease")
ax.set_ylabel("Percent of Scientific Field Records")
ax.set_ylim(0, 100)
ax.set_xticklabels(wrap_labels(stacked_percent.index, width=18), rotation=45, ha="right")
ax.grid(axis="y", linestyle="--", linewidth=0.7, alpha=0.35)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(
    title="Scientific Field",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    labels=wrap_labels(stacked_percent.columns, width=24)
)

plt.tight_layout()

output_path_4 = get_numbered_path(
    charts_dir / "disease_scientific_field_composition_100_percent_stacked.png"
)

plt.savefig(output_path_4, dpi=300)
plt.close()

print(f"100% stacked bar chart saved to: {output_path_4}")

# -----------------------------
# Chart 5:
# Bubble chart of top 20 diseases vs all scientific fields
# -----------------------------
bubble_data = heatmap_data.copy()

x_positions = []
y_positions = []
bubble_sizes = []
bubble_colors = []

max_count = bubble_data.values.max()
size_scale = 1600 / max(max_count, 1)

for row_index, disease in enumerate(bubble_data.index):
    for col_index, scientific_field in enumerate(bubble_data.columns):
        count = bubble_data.loc[disease, scientific_field]
        if count:
            x_positions.append(col_index)
            y_positions.append(row_index)
            bubble_sizes.append(max(count * size_scale, 35))
            bubble_colors.append(count)

fig, ax = plt.subplots(figsize=(22, 15))
scatter = ax.scatter(
    x_positions,
    y_positions,
    s=bubble_sizes,
    c=bubble_colors,
    cmap="viridis",
    alpha=0.75,
    edgecolors="#263238",
    linewidths=0.6
)

ax.set_title("Disease and Scientific Field Record Counts")
ax.set_xlabel("Scientific Field")
ax.set_ylabel("Disease")
ax.set_xticks(range(len(bubble_data.columns)))
ax.set_xticklabels(wrap_labels(bubble_data.columns, width=18), rotation=45, ha="right")
ax.set_yticks(range(len(bubble_data.index)))
ax.set_yticklabels(wrap_labels(bubble_data.index, width=28))
ax.invert_yaxis()
ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.25)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.colorbar(scatter, ax=ax, label="Number of Records")
plt.tight_layout()

output_path_5 = get_numbered_path(
    charts_dir / "disease_scientific_field_bubble_chart.png"
)

plt.savefig(output_path_5, dpi=300)
plt.close()

print(f"Bubble chart saved to: {output_path_5}")
