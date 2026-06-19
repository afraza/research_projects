import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from pathlib import Path

# -----------------------------
# Settings
# -----------------------------
excel_file = "scientific_projects_iran.xlsx"  # change this
sheet_name = 0
disease_column = "disease"
tier_column = "university-tier"

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
        color=get_bar_colors(len(top_10)),
        edgecolor="#1F4E66",
        linewidth=0.8
    )

    ax.set_title(f"Top 10 Diseases - University Tier {tier}")
    ax.set_xlabel("Number of Records")
    ax.set_ylabel("Disease")
    style_horizontal_bar_chart(ax)

plt.tight_layout()

# -----------------------------
# Save chart with numbered naming
# -----------------------------
charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

output_path = charts_dir / "disease_top_10_diseases_by_university_tier.png"

output_path = get_numbered_path(output_path)

plt.savefig(output_path, dpi=300)
plt.close()

print(f"Chart saved to: {output_path}")

# -----------------------------
# Create pie chart for tier distribution
# -----------------------------
tier_counts = df[tier_column].value_counts().reindex(tiers, fill_value=0)

plt.figure(figsize=(10, 10))
plt.pie(
    tier_counts.values,
    labels=[f"University Tier {tier}" for tier in tier_counts.index],
    autopct="%1.1f%%",
    startangle=90,
    counterclock=False
)
plt.title("University Tier Share")
plt.tight_layout()

pie_output_path = get_numbered_path(
    charts_dir / "disease_university_tier_distribution_pie.png"
)

plt.savefig(pie_output_path, dpi=300)
plt.close()

print(f"Pie chart saved to: {pie_output_path}")

# -----------------------------
# Create heatmap chart for top diseases by tier
# -----------------------------
top_10_overall_diseases = df[disease_column].value_counts().head(10).index

heatmap_data = pd.crosstab(
    df[tier_column],
    df[disease_column]
)

heatmap_data = heatmap_data.reindex(
    index=tiers,
    columns=top_10_overall_diseases,
    fill_value=0
)

fig, ax = plt.subplots(figsize=(14, 8))
image = ax.imshow(heatmap_data.values, cmap="YlOrRd", aspect="auto")

ax.set_title("Top Disease Counts by University Tier")
ax.set_xlabel("Disease")
ax.set_ylabel("University Tier")
ax.set_xticks(range(len(heatmap_data.columns)))
ax.set_xticklabels(heatmap_data.columns, rotation=45, ha="right")
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels([f"Tier {tier}" for tier in heatmap_data.index])

for row in range(heatmap_data.shape[0]):
    for col in range(heatmap_data.shape[1]):
        value = heatmap_data.iat[row, col]
        if value:
            ax.text(col, row, int(value), ha="center", va="center")

fig.colorbar(image, ax=ax, label="Number of Records")
plt.tight_layout()

heatmap_output_path = get_numbered_path(
    charts_dir / "disease_top_diseases_by_university_tier_heatmap.png"
)

plt.savefig(heatmap_output_path, dpi=300)
plt.close()

print(f"Heatmap chart saved to: {heatmap_output_path}")
