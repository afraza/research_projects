import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
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
                fontsize=9
            )

    ax.margins(x=0.14)


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
charts_dir = Path("charts") / "disease_universities"
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

    ax = top_10.sort_values().plot(
        kind="barh",
        color=get_bar_colors(len(top_10)),
        edgecolor="#1F4E66",
        linewidth=0.8
    )

    plt.title(f"Top 10 Diseases - {university_name}")
    plt.xlabel("Number of Records")
    plt.ylabel("Disease")
    style_horizontal_bar_chart(ax)

    plt.tight_layout()

    filename = f"disease_top_10_diseases_university_{university_code}_{safe_filename(university_name)}.png"
    output_path = get_numbered_path(charts_dir / filename)

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved: {output_path}")

    plt.figure(figsize=(10, 10))
    ax = top_10.plot(
        kind="pie",
        autopct="%1.1f%%",
        startangle=90,
        counterclock=False
    )
    ax.set_ylabel("")

    plt.title(f"Disease Share Among Top 10 Diseases - {university_name}")
    plt.tight_layout()

    pie_filename = f"disease_top_10_diseases_university_{university_code}_{safe_filename(university_name)}_pie.png"
    pie_output_path = get_numbered_path(charts_dir / pie_filename)

    plt.savefig(pie_output_path, dpi=300)
    plt.close()

    print(f"Saved pie chart: {pie_output_path}")

top_20_university_codes = df[university_code_column].value_counts().head(20).index
top_20_diseases = df[disease_column].value_counts().head(20).index

df_top_universities = df[
    df[university_code_column].isin(top_20_university_codes)
].copy()

df_top_universities["university-label"] = df_top_universities[
    university_code_column
].map(
    lambda code: code_to_name.get(code, f"University Code {code}")
)

top_20_university_labels = [
    code_to_name.get(code, f"University Code {code}")
    for code in top_20_university_codes
]

heatmap_data = pd.crosstab(
    df_top_universities["university-label"],
    df_top_universities[disease_column]
)

heatmap_data = heatmap_data.reindex(
    index=top_20_university_labels,
    columns=top_20_diseases,
    fill_value=0
)

fig, ax = plt.subplots(figsize=(20, 14))
image = ax.imshow(heatmap_data.values, cmap="YlOrRd", aspect="auto")

ax.set_title("20 Most Frequent Diseases by 20 Most Prolific Universities")
ax.set_xlabel("Disease")
ax.set_ylabel("University")
ax.set_xticks(range(len(heatmap_data.columns)))
ax.set_xticklabels(heatmap_data.columns, rotation=45, ha="right")
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels(heatmap_data.index)

for row in range(heatmap_data.shape[0]):
    for col in range(heatmap_data.shape[1]):
        value = heatmap_data.iat[row, col]
        if value:
            ax.text(col, row, int(value), ha="center", va="center", fontsize=7)

fig.colorbar(image, ax=ax, label="Number of Records")
plt.tight_layout()

heatmap_output_path = get_numbered_path(
    charts_dir / "disease_top_20_diseases_by_top_20_universities_heatmap.png"
)

plt.savefig(heatmap_output_path, dpi=300)
plt.close()

print(f"Saved heatmap chart: {heatmap_output_path}")
