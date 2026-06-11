import pandas as pd
import matplotlib.pyplot as plt
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
})

# -----------------------------
# Clean macroregion field
# -----------------------------
df[macroregion_column] = df[macroregion_column].astype(str).str.strip()

df = df[
    df[macroregion_column].notna()
    & (df[macroregion_column] != "")
    & (df[macroregion_column].str.lower() != "nan")
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

# Hide unused subplots, if any
for ax in axes[len(macroregions):]:
    ax.axis("off")

plt.tight_layout()

# -----------------------------
# Save chart with numbered naming
# -----------------------------
charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

output_path = charts_dir / "top_10_diseases_by_macroregion.png"

counter = 1
while output_path.exists():
    output_path = charts_dir / f"top_10_diseases_by_macroregion_{counter}.png"
    counter += 1

plt.savefig(output_path, dpi=300)
plt.show()

print(f"Chart saved to: {output_path}")