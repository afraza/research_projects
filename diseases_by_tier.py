import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# -----------------------------
# Settings
# -----------------------------
excel_file = "scientific_projects_iran.xlsx"  # change this
sheet_name = 0
disease_column = "disease"
tier_column = "university-tier"

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

# Normalize disease names:
# Breast Cancer + Breast cancer -> Breast Cancer
# Colorectal Cancer + Colorectal cancer -> Colorectal Cancer
df[disease_column] = df[disease_column].str.lower().str.title()

# Preserve special disease names if needed
df[disease_column] = df[disease_column].replace({
    "Covid-19": "COVID-19",
})

# -----------------------------
# Clean tier field
# -----------------------------
df[tier_column] = pd.to_numeric(df[tier_column], errors="coerce")
df = df[df[tier_column].isin([0, 1, 2, 3])].copy()
df[tier_column] = df[tier_column].astype(int)

# -----------------------------
# Create top 10 disease chart for each tier
# -----------------------------
tiers = [0, 1, 2, 3]

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.flatten()

for ax, tier in zip(axes, tiers):
    tier_data = df[df[tier_column] == tier]

    top_10 = tier_data[disease_column].value_counts().head(10)

    top_10.sort_values().plot(
        kind="barh",
        ax=ax,
        color="#3A7CA5"
    )

    ax.set_title(f"Top 10 Diseases - University Tier {tier}")
    ax.set_xlabel("Number of Records")
    ax.set_ylabel("Disease")

plt.tight_layout()

# -----------------------------
# Save chart with numbered naming
# -----------------------------
charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

output_path = charts_dir / "top_10_diseases_by_university_tier.png"

counter = 1
while output_path.exists():
    output_path = charts_dir / f"top_10_diseases_by_university_tier_{counter}.png"
    counter += 1

plt.savefig(output_path, dpi=300)
plt.show()

print(f"Chart saved to: {output_path}")