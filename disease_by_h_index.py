import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# -----------------------------
# Settings
# -----------------------------
excel_file = "scientific_projects_iran.xlsx"
sheet_name = 0

disease_column = "disease"
h_index_column = "H-index"

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
    "#n/a",
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
# Clean H-index field
# -----------------------------
df[h_index_column] = pd.to_numeric(
    df[h_index_column],
    errors="coerce"
)

df = df[df[h_index_column].notna()].copy()

# -----------------------------
# Find 10 most frequent diseases
# -----------------------------
top_10_diseases = df[disease_column].value_counts().head(10).index.tolist()

df_top_10 = df[df[disease_column].isin(top_10_diseases)].copy()

print("10 most frequent diseases:")
print(df_top_10[disease_column].value_counts())

# -----------------------------
# Create box and whisker chart
# -----------------------------
boxplot_data = [
    df_top_10[df_top_10[disease_column] == disease][h_index_column]
    for disease in top_10_diseases
]

plt.figure(figsize=(14, 8))

plt.boxplot(
    boxplot_data,
    tick_labels=top_10_diseases,
    patch_artist=True,
    boxprops=dict(facecolor="#3A7CA5", color="#1F4E66"),
    medianprops=dict(color="white", linewidth=2),
    whiskerprops=dict(color="#1F4E66"),
    capprops=dict(color="#1F4E66"),
    flierprops=dict(
        marker="o",
        markerfacecolor="#D1495B",
        markeredgecolor="#D1495B",
        markersize=4,
        alpha=0.6
    )
)

plt.title("H-index Distribution in 10 Most Frequent Diseases")
plt.xlabel("Disease")
plt.ylabel("H-index")

plt.xticks(rotation=45, ha="right")
plt.tight_layout()

# -----------------------------
# Save chart
# -----------------------------
charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

output_path = get_numbered_path(
    charts_dir / "h_index_boxplot_top_10_diseases.png"
)

plt.savefig(output_path, dpi=300)
plt.show()

print(f"\nChart saved to: {output_path}")