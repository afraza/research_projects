import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_FILE = "scientific_projects_iran.xlsx"

CHART_DIR = Path("charts/keyword_h_index")
CHART_DIR.mkdir(parents=True, exist_ok=True)

KEYWORD_COLUMNS = ["keyword1", "keyword2", "keyword3"]
H_INDEX_COLUMN = "H-index"

TOP_KEYWORDS = 10

NULL_LIKE_VALUES = {
    "",
    "nan",
    "none",
    "null",
    "#n/a",
    "n/a",
    "na",
    "#na",
    "#value!",
    "#ref!",
    "-",
    "--",
    "—",
}


def is_null_like(value):
    if pd.isna(value):
        return True

    text = str(value).strip().lower()
    return text in NULL_LIKE_VALUES


def normalize_keyword(value):
    if is_null_like(value):
        return None

    text = str(value).strip().lower()

    text = text.replace("_", " ")
    text = text.replace("/", " ")
    text = text.replace("\\", " ")
    text = text.replace("&", " and ")

    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if not text or text in NULL_LIKE_VALUES:
        return None

    return text


def normalize_h_index(value):
    if is_null_like(value):
        return None

    h_index = pd.to_numeric(value, errors="coerce")

    if pd.isna(h_index):
        return None

    if h_index < 0:
        return None

    return float(h_index)


df = pd.read_excel(INPUT_FILE)

required_columns = KEYWORD_COLUMNS + [H_INDEX_COLUMN]
missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing columns in main Excel file: {missing_cols}")

df[H_INDEX_COLUMN] = df[H_INDEX_COLUMN].map(normalize_h_index)
df = df.dropna(subset=[H_INDEX_COLUMN])

long_keywords = df[[H_INDEX_COLUMN] + KEYWORD_COLUMNS].melt(
    id_vars=H_INDEX_COLUMN,
    value_vars=KEYWORD_COLUMNS,
    var_name="keyword_field",
    value_name="keyword"
)

long_keywords["keyword"] = long_keywords["keyword"].map(normalize_keyword)
long_keywords = long_keywords.dropna(subset=["keyword", H_INDEX_COLUMN])

top_keywords = (
    long_keywords["keyword"]
    .value_counts()
    .head(TOP_KEYWORDS)
    .index
    .tolist()
)

plot_data = long_keywords[long_keywords["keyword"].isin(top_keywords)].copy()

# Chart 1: box and whisker plot of H-index by top keywords
boxplot_data = [
    plot_data[plot_data["keyword"] == keyword][H_INDEX_COLUMN]
    for keyword in top_keywords
]

plt.figure(figsize=(14, 8))

plt.boxplot(
    boxplot_data,
    tick_labels=top_keywords,
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

plt.title("H-index Distribution in 10 Most Frequent Keywords")
plt.xlabel("Keyword")
plt.ylabel("H-index")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig(
    CHART_DIR / "h_index_boxplot_top_10_keywords.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()


# Chart 2: mean H-index by top keyword
summary = (
    plot_data
    .groupby("keyword", observed=True)[H_INDEX_COLUMN]
    .agg(count="count", mean="mean", median="median")
    .reindex(top_keywords)
    .reset_index()
)

plt.figure(figsize=(14, 7))
sns.barplot(
    data=summary,
    x="keyword",
    y="mean",
    order=top_keywords,
    color="#2f6f9f"
)
plt.title("Mean H-index Across the 10 Most Frequent Keywords")
plt.xlabel("Keyword")
plt.ylabel("Mean H-index")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.savefig(
    CHART_DIR / "mean_h_index_top_10_keywords.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()


# Chart 3: count vs median H-index scatter plot
plt.figure(figsize=(10, 7))
sns.scatterplot(
    data=summary,
    x="count",
    y="median",
    s=120,
    color="#2f6f9f"
)

for _, row in summary.iterrows():
    plt.text(
        row["count"],
        row["median"],
        str(row["keyword"]),
        fontsize=8,
        ha="left",
        va="bottom"
    )

plt.title("Keyword Frequency vs Median H-index")
plt.xlabel("Keyword Frequency")
plt.ylabel("Median H-index")
plt.tight_layout()

plt.savefig(
    CHART_DIR / "keyword_frequency_vs_median_h_index.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

print("Done.")
print(f"Top keywords used: {top_keywords}")
print(f"Valid keyword-H-index rows used: {len(plot_data)}")
print(f"Saved charts to: {CHART_DIR.resolve()}")