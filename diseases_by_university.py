import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re

# -----------------------------
# Settings
# -----------------------------
excel_file = "scientific_projects_iran.xlsx"  # change this
sheet_name = 0

disease_column = "disease"
university_code_column = "university-code"

# Optional: if you have a separate file with university codes and names
# It should have columns: university-code, university-name
university_lookup_file = "university_lookup.xlsx"

# -----------------------------
# Helper functions
# -----------------------------
def get_numbered_path(path):
    if not path.exists():
        return path

    counter = 1
    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def safe_filename(text):
    text = str(text).strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:120]


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
# Clean university code field
# -----------------------------
df[university_code_column] = pd.to_numeric(
    df[university_code_column],
    errors="coerce"
)

df = df[df[university_code_column].notna()].copy()
df[university_code_column] = df[university_code_column].astype(int)

# -----------------------------
# Load university names, if available
# -----------------------------
try:
    university_lookup = pd.read_excel(university_lookup_file)

    university_lookup["university-code"] = pd.to_numeric(
        university_lookup["university-code"],
        errors="coerce"
    )

    university_lookup = university_lookup.dropna(subset=["university-code"])
    university_lookup["university-code"] = university_lookup["university-code"].astype(int)

    code_to_name = dict(
        zip(
            university_lookup["university-code"],
            university_lookup["university-name"]
        )
    )

except FileNotFoundError:
    print("University lookup file not found. Charts will use university codes only.")
    code_to_name = {}

# -----------------------------
# Create charts folder
# -----------------------------
charts_dir = Path("charts") / "universities"
charts_dir.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Create one chart per university
# -----------------------------
university_codes = sorted(df[university_code_column].unique())

for university_code in university_codes:
    university_data = df[df[university_code_column] == university_code]

    top_10 = university_data[disease_column].value_counts().head(10)

    if top_10.empty:
        continue

    university_name = code_to_name.get(
        university_code,
        f"University Code {university_code}"
    )

    plt.figure(figsize=(12, 7))

    top_10.sort_values().plot(
        kind="barh",
        color="#3A7CA5"
    )

    plt.title(f"Top 10 Diseases - {university_name}")
    plt.xlabel("Number of Records")
    plt.ylabel("Disease")

    plt.tight_layout()

    filename = f"top_10_diseases_university_{university_code}_{safe_filename(university_name)}.png"
    output_path = get_numbered_path(charts_dir / filename)

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved: {output_path}")