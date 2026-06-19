import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from pathlib import Path
import math
import textwrap

# -----------------------------
# Settings
# -----------------------------
excel_file = "scientific_projects_iran.xlsx"
methodology_lookup_file = "Methodology-code.xlsx"

sheet_name = 0
methodology_lookup_sheet = 0

disease_column = "disease"
methodology_code_column = "Methodology-code"
methodology_name_column = "Methodology"

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


def style_vertical_bar_chart(ax):
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", linestyle="--", linewidth=0.7, alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# -----------------------------
# Load main data
# -----------------------------
df = pd.read_excel(excel_file, sheet_name=sheet_name)

# -----------------------------
# Clean disease field
# -----------------------------
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

# Normalize disease names
df[disease_column] = df[disease_column].str.lower().str.title()

# Preserve special disease names
df[disease_column] = df[disease_column].replace({
    "Covid-19": "COVID-19",
    "Cancer": "Cancer (general)",
})

df = df[df[disease_column] != "COVID-19"].copy()

# -----------------------------
# Clean Methodology-code in main data
# -----------------------------
df[methodology_code_column] = df[methodology_code_column].astype(str).str.strip()

df = df[
    ~df[methodology_code_column].str.lower().isin(invalid_values)
].copy()

df[methodology_code_column] = pd.to_numeric(
    df[methodology_code_column],
    errors="coerce"
)

df = df[df[methodology_code_column].notna()].copy()
df[methodology_code_column] = df[methodology_code_column].astype(int)

# Keep only methodology codes 1 to 16
df = df[df[methodology_code_column].between(1, 16)].copy()

# -----------------------------
# Load methodology lookup file
# -----------------------------
methodology_lookup = pd.read_excel(
    methodology_lookup_file,
    sheet_name=methodology_lookup_sheet
)

methodology_lookup[methodology_code_column] = pd.to_numeric(
    methodology_lookup[methodology_code_column],
    errors="coerce"
)

methodology_lookup = methodology_lookup.dropna(
    subset=[methodology_code_column]
).copy()

methodology_lookup[methodology_code_column] = methodology_lookup[
    methodology_code_column
].astype(int)

methodology_lookup = methodology_lookup.dropna(
    subset=[methodology_name_column]
).copy()

methodology_lookup[methodology_name_column] = methodology_lookup[
    methodology_name_column
].astype(str).str.strip()

methodology_lookup = methodology_lookup[
    ~methodology_lookup[methodology_name_column].str.lower().isin(invalid_values)
].copy()

code_to_methodology_name = dict(
    zip(
        methodology_lookup[methodology_code_column],
        methodology_lookup[methodology_name_column]
    )
)

# -----------------------------
# Print methodology counts
# -----------------------------
methodology_counts = df[methodology_code_column].value_counts().sort_values(
    ascending=False
)

print("Methodology frequencies:")
for code, count in methodology_counts.items():
    methodology_name = code_to_methodology_name.get(
        code,
        f"Unknown Methodology {code}"
    )
    print(f"{code} - {methodology_name}: {count}")

# -----------------------------
# Create chart:
# Top 10 diseases in each methodology
# -----------------------------
methodology_codes = sorted(df[methodology_code_column].unique())

cols = 2
rows = math.ceil(len(methodology_codes) / cols)

fig, axes = plt.subplots(rows, cols, figsize=(18, rows * 5))
axes = axes.flatten()

for ax, methodology_code in zip(axes, methodology_codes):
    methodology_data = df[df[methodology_code_column] == methodology_code]

    top_10_diseases = methodology_data[disease_column].value_counts().head(10)

    methodology_name = code_to_methodology_name.get(
        methodology_code,
        f"Methodology Code {methodology_code}"
    )

    top_10_diseases.sort_values().plot(
        kind="barh",
        ax=ax,
        color=get_bar_colors(len(top_10_diseases)),
        edgecolor="#1F4E66",
        linewidth=0.8
    )

    ax.set_title(f"Top 10 Diseases - {methodology_name}")
    ax.set_xlabel("Number of Records")
    ax.set_ylabel("Disease")
    style_horizontal_bar_chart(ax)

# Hide unused panels
for ax in axes[len(methodology_codes):]:
    ax.axis("off")

plt.tight_layout()

# -----------------------------
# Save chart
# -----------------------------
charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

output_path = get_numbered_path(
    charts_dir / "disease_top_10_diseases_by_methodology.png"
)

plt.savefig(output_path, dpi=300)
plt.close()

print(f"\nChart saved to: {output_path}")

# -----------------------------
# Create pie chart:
# Methodology distribution
# -----------------------------
methodology_labels = [
    code_to_methodology_name.get(code, f"Unknown Methodology {code}")
    for code in methodology_counts.index
]

plt.figure(figsize=(14, 14))
plt.pie(
    methodology_counts.values,
    labels=methodology_labels,
    autopct="%1.1f%%",
    startangle=90,
    counterclock=False,
    labeldistance=1.16,
    pctdistance=0.78,
    rotatelabels=True,
    textprops={"fontsize": 8}
)
plt.title("Methodology Share", y=1.08)
plt.tight_layout(rect=[0, 0, 1, 0.94])

pie_output_path = get_numbered_path(
    charts_dir / "disease_methodology_distribution_pie.png"
)

plt.savefig(pie_output_path, dpi=300)
plt.close()

print(f"Pie chart saved to: {pie_output_path}")

# -----------------------------
# Create heatmap chart:
# Top diseases by methodology
# -----------------------------
top_10_overall_diseases = df[disease_column].value_counts().head(10).index
df["Methodology-name"] = df[methodology_code_column].map(
    lambda code: code_to_methodology_name.get(code, f"Methodology Code {code}")
)

methodology_heatmap_labels = [
    code_to_methodology_name.get(code, f"Methodology Code {code}")
    for code in methodology_codes
]

heatmap_data = pd.crosstab(
    df["Methodology-name"],
    df[disease_column]
)

heatmap_data = heatmap_data.reindex(
    index=methodology_heatmap_labels,
    columns=top_10_overall_diseases,
    fill_value=0
)

fig, ax = plt.subplots(figsize=(16, 10))
image = ax.imshow(heatmap_data.values, cmap="YlOrRd", aspect="auto")

ax.set_title("Top Disease Counts by Methodology")
ax.set_xlabel("Disease")
ax.set_ylabel("Methodology")
ax.set_xticks(range(len(heatmap_data.columns)))
ax.set_xticklabels(heatmap_data.columns, rotation=45, ha="right")
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels(heatmap_data.index)

for row in range(heatmap_data.shape[0]):
    for col in range(heatmap_data.shape[1]):
        value = heatmap_data.iat[row, col]
        if value:
            ax.text(col, row, int(value), ha="center", va="center", fontsize=8)

fig.colorbar(image, ax=ax, label="Number of Records")
plt.tight_layout()

heatmap_output_path = get_numbered_path(
    charts_dir / "disease_top_diseases_by_methodology_heatmap.png"
)

plt.savefig(heatmap_output_path, dpi=300)
plt.close()

print(f"Heatmap chart saved to: {heatmap_output_path}")

# -----------------------------
# Create column chart:
# Number of frequent methodologies used in each top disease
# -----------------------------
top_20_methodology_codes = methodology_counts.head(20).index

df_top_methodologies = df[
    df[methodology_code_column].isin(top_20_methodology_codes)
].copy()

methodology_usage_by_disease = (
    df_top_methodologies[
        df_top_methodologies[disease_column].isin(top_10_overall_diseases)
    ]
    .groupby(disease_column)[methodology_code_column]
    .nunique()
    .reindex(top_10_overall_diseases, fill_value=0)
)

fig, ax = plt.subplots(figsize=(14, 8))
methodology_usage_by_disease.plot(
    kind="bar",
    ax=ax,
    color=get_bar_colors(len(methodology_usage_by_disease)),
    edgecolor="#1F4E66",
    linewidth=0.8
)

ax.set_title("Methodology Coverage in 10 Most Frequent Diseases")
ax.set_xlabel("Disease")
ax.set_ylabel("Number of Methodologies Used")
style_vertical_bar_chart(ax)
ax.set_ylim(0, max(len(top_20_methodology_codes) + 1, 1))
ax.set_xticklabels(methodology_usage_by_disease.index, rotation=45, ha="right")

for bar in ax.patches:
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        int(height),
        ha="center",
        va="bottom"
    )

plt.tight_layout()

coverage_output_path = get_numbered_path(
    charts_dir / "disease_methodology_coverage_in_top_10_diseases.png"
)

plt.savefig(coverage_output_path, dpi=300)
plt.close()

print(f"Methodology coverage chart saved to: {coverage_output_path}")

# -----------------------------
# Create grouped column charts:
# Methodology counts inside each top disease
# -----------------------------
top_disease_methodology_data = df_top_methodologies[
    df_top_methodologies[disease_column].isin(top_10_overall_diseases)
].copy()

methodology_palette = BAR_COLORS

cols = 2
rows = math.ceil(len(top_10_overall_diseases) / cols)
fig, axes = plt.subplots(rows, cols, figsize=(22, rows * 7))
axes = axes.flatten()

for ax, disease in zip(axes, top_10_overall_diseases):
    disease_data = top_disease_methodology_data[
        top_disease_methodology_data[disease_column] == disease
    ]

    methodology_counts_for_disease = (
        disease_data[methodology_code_column]
        .value_counts()
        .reindex(top_20_methodology_codes, fill_value=0)
    )

    methodology_names = [
        code_to_methodology_name.get(code, f"Methodology Code {code}")
        for code in methodology_counts_for_disease.index
    ]

    wrapped_methodology_names = [
        "\n".join(textwrap.wrap(name, width=16)) for name in methodology_names
    ]

    colors = [
        methodology_palette[index % len(methodology_palette)]
        for index in range(len(methodology_counts_for_disease))
    ]

    bars = ax.bar(
        range(len(methodology_counts_for_disease)),
        methodology_counts_for_disease.values,
        color=colors,
        edgecolor="#263238",
        linewidth=0.7
    )

    ax.set_title(f"Methodology Records - {disease}", pad=14)
    ax.set_xlabel("Methodology")
    ax.set_ylabel("Number of Records")
    ax.set_xticks(range(len(wrapped_methodology_names)))
    ax.set_xticklabels(wrapped_methodology_names, rotation=90, ha="center")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", linestyle="--", linewidth=0.7, alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    max_count = methodology_counts_for_disease.max()
    ax.set_ylim(0, max(max_count + 1, 1))

    for bar in bars:
        height = bar.get_height()
        if height:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                int(height),
                ha="center",
                va="bottom",
                fontsize=8
            )

for ax in axes[len(top_10_overall_diseases):]:
    ax.axis("off")

plt.tight_layout()

disease_methodology_counts_output_path = get_numbered_path(
    charts_dir / "disease_methodology_counts_for_each_top_10_disease.png"
)

plt.savefig(disease_methodology_counts_output_path, dpi=300)
plt.close()

print(
    "Disease methodology counts chart saved to: "
    f"{disease_methodology_counts_output_path}"
)
