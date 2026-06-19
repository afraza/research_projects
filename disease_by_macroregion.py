import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from pathlib import Path
import math

# -----------------------------
# Settings
# -----------------------------
excel_file = "scientific_projects_iran.xlsx"  # change this
sheet_name = 0
disease_column = "disease"
macroregion_column = "macroregion"

# -----------------------------
# Load data
# -----------------------------
df = pd.read_excel(excel_file, sheet_name=sheet_name)

# -----------------------------
# Clean disease field
# -----------------------------
df[disease_column] = df[disease_column].astype(str).str.strip()

invalid_disease_values = {
    "",
    "-",
    "--",
    "---",
    "nan",
    "none",
    "null",
    "n/a",
    "na",
}

df = df[
    df[disease_column].notna()
    & (~df[disease_column].str.lower().isin(invalid_disease_values))
].copy()

# Normalize disease names
df[disease_column] = df[disease_column].str.lower().str.title()

# Preserve special disease names
df[disease_column] = df[disease_column].replace({
    "Covid-19": "COVID-19",
    "Cancer": "Cancer (general)",
})

df = df[df[disease_column] != "COVID-19"].copy()


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
# Clean macroregion field
# -----------------------------
df[macroregion_column] = df[macroregion_column].astype(str).str.strip()

df = df[
    df[macroregion_column].notna()
    & (df[macroregion_column] != "")
    & (df[macroregion_column].str.lower() != "nan")
    & (~df[macroregion_column].isin({"0", "0.0"}))
].copy()

macroregions = sorted(df[macroregion_column].unique())

# -----------------------------
# Create top 10 disease chart for each macroregion
# -----------------------------
n_regions = len(macroregions)
cols = 2
rows = math.ceil(n_regions / cols)

fig, axes = plt.subplots(rows, cols, figsize=(18, rows * 5))
axes = axes.flatten()

for ax, macroregion in zip(axes, macroregions):
    region_data = df[df[macroregion_column] == macroregion]

    top_10 = region_data[disease_column].value_counts().head(10)

    top_10.sort_values().plot(
        kind="barh",
        ax=ax,
        color="#3A7CA5"
    )

    ax.set_title(f"Top 10 Diseases - Macroregion {macroregion}")
    ax.set_xlabel("Number of Records")
    ax.set_ylabel("Disease")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

# Hide unused subplots, if any
for ax in axes[len(macroregions):]:
    ax.axis("off")

plt.tight_layout()

# -----------------------------
# Save chart with numbered naming
# -----------------------------
charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

output_path = charts_dir / "disease_top_10_diseases_by_macroregion.png"

output_path = get_numbered_path(output_path)

plt.savefig(output_path, dpi=300)
plt.close()

print(f"Chart saved to: {output_path}")

# -----------------------------
# Create pie chart for macroregion distribution
# -----------------------------
macroregion_counts = df[macroregion_column].value_counts().sort_index()

plt.figure(figsize=(10, 10))
plt.pie(
    macroregion_counts.values,
    labels=[f"Macroregion {label}" for label in macroregion_counts.index],
    autopct="%1.1f%%",
    startangle=90,
    counterclock=False
)
plt.title("Macroregion Share")
plt.tight_layout()

pie_output_path = get_numbered_path(
    charts_dir / "disease_macroregion_distribution_pie.png"
)

plt.savefig(pie_output_path, dpi=300)
plt.close()

print(f"Pie chart saved to: {pie_output_path}")

# -----------------------------
# Create heatmap chart for top diseases by macroregion
# -----------------------------
top_10_overall_diseases = df[disease_column].value_counts().head(10).index

heatmap_data = pd.crosstab(
    df[macroregion_column],
    df[disease_column]
)

heatmap_data = heatmap_data.reindex(
    index=macroregions,
    columns=top_10_overall_diseases,
    fill_value=0
)

fig, ax = plt.subplots(figsize=(14, 8))
image = ax.imshow(heatmap_data.values, cmap="YlOrRd", aspect="auto")

ax.set_title("Top Disease Counts by Macroregion")
ax.set_xlabel("Disease")
ax.set_ylabel("Macroregion")
ax.set_xticks(range(len(heatmap_data.columns)))
ax.set_xticklabels(heatmap_data.columns, rotation=45, ha="right")
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels([f"Macroregion {label}" for label in heatmap_data.index])

for row in range(heatmap_data.shape[0]):
    for col in range(heatmap_data.shape[1]):
        value = heatmap_data.iat[row, col]
        if value:
            ax.text(col, row, int(value), ha="center", va="center")

fig.colorbar(image, ax=ax, label="Number of Records")
plt.tight_layout()

heatmap_output_path = get_numbered_path(
    charts_dir / "disease_top_diseases_by_macroregion_heatmap.png"
)

plt.savefig(heatmap_output_path, dpi=300)
plt.close()

print(f"Heatmap chart saved to: {heatmap_output_path}")
