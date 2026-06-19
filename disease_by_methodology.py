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
excel_file = "scientific_projects_iran.xlsx"
methodology_lookup_file = "Methodology-code.xlsx"

sheet_name = 0
methodology_lookup_sheet = 0

disease_column = "disease"
methodology_code_column = "Methodology-code"
methodology_name_column = "Methodology"

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
        color="#3A7CA5"
    )

    ax.set_title(f"Top 10 Diseases - {methodology_name}")
    ax.set_xlabel("Number of Records")
    ax.set_ylabel("Disease")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

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
plt.title("Methodology Share")
plt.tight_layout()

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
