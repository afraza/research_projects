import pandas as pd
import matplotlib.pyplot as plt

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
})

# -----------------------------
# Count top 15 diseases
# -----------------------------
top_15_diseases = df[disease_column].value_counts().head(15)

print(top_15_diseases)

# -----------------------------
# Plot chart
# -----------------------------
plt.figure(figsize=(12, 7))

top_15_diseases.sort_values().plot(
    kind="barh",
    color="#3A7CA5"
)

plt.title("15 Most Frequent Diseases in Scientific Projects Data")
plt.xlabel("Number of Records")
plt.ylabel("Disease")

from pathlib import Path

charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

output_path = charts_dir / "top_15_diseases.png"

counter = 1
while output_path.exists():
    output_path = charts_dir / f"top_15_diseases_{counter}.png"
    counter += 1

plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.show()

print(f"Chart saved to: {output_path}")