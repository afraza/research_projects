import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from pathlib import Path

# -----------------------------
# Settings
# -----------------------------
excel_file = "scientific_projects_iran.xlsx"  # change to your Excel file name
sheet_name = 0  # or use the sheet name, e.g. "Sheet1"
disease_column = "disease"

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

# Make disease names consistent:
# "Breast Cancer" and "Breast cancer" -> "Breast Cancer"
# "Colorectal Cancer" and "Colorectal cancer" -> "Colorectal Cancer"
df[disease_column] = df[disease_column].str.lower().str.title()

df[disease_column] = df[disease_column].replace({
    "Covid-19": "COVID-19",
    "Cancer": "Cancer (general)",
})

df = df[df[disease_column] != "COVID-19"].copy()

# -----------------------------
# Count top 15 diseases
# -----------------------------
top_15_diseases = df[disease_column].value_counts().head(15)

print(top_15_diseases)

# -----------------------------
# Plot bar chart
# -----------------------------
plt.figure(figsize=(12, 7))

top_15_diseases.sort_values().plot(
    kind="barh",
    color="#3A7CA5"
)

plt.title("15 Most Frequent Diseases in Scientific Projects Data")
plt.xlabel("Number of Records")
plt.ylabel("Disease")
plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))

charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

def get_numbered_path(path):
    if not path.exists():
        return path

    counter = 1
    while True:
        new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


output_path = get_numbered_path(charts_dir / "disease_top_15_diseases.png")

plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.close()

print(f"Chart saved to: {output_path}")

# -----------------------------
# Plot pie chart
# -----------------------------
plt.figure(figsize=(10, 10))

ax = top_15_diseases.plot(
    kind="pie",
    autopct="%1.1f%%",
    startangle=90,
    counterclock=False
)
ax.set_ylabel("")

plt.title("Disease Share Among 15 Most Frequent Diseases")
plt.tight_layout()

pie_output_path = get_numbered_path(charts_dir / "disease_top_15_diseases_pie.png")
plt.savefig(pie_output_path, dpi=300)
plt.close()

print(f"Pie chart saved to: {pie_output_path}")
