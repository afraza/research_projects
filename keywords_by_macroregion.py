import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_FILE = "scientific_projects_iran.xlsx"

CHART_DIR = Path("charts")
CHART_DIR.mkdir(exist_ok=True)

KEYWORD_COLUMNS = ["keyword1", "keyword2", "keyword3"]
REGION_COLUMN = "macroregion"
MACROREGION_ORDER = list(range(1, 11))


def normalize_keyword(value):
    if pd.isna(value):
        return None

    text = str(value).strip().lower()

    if not text or text in {"nan", "none", "null"}:
        return None

    text = text.replace("_", " ")
    text = text.replace("/", " ")
    text = text.replace("\\", " ")
    text = text.replace("&", " and ")

    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text if text else None


def normalize_macroregion(value):
    if pd.isna(value):
        return None

    try:
        code = int(float(value))
    except ValueError:
        return None

    if code not in MACROREGION_ORDER:
        return None

    return code


df = pd.read_excel(INPUT_FILE)

required_columns = KEYWORD_COLUMNS + [REGION_COLUMN]
missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing columns in Excel file: {missing_cols}")

long_keywords = df[[REGION_COLUMN] + KEYWORD_COLUMNS].melt(
    id_vars=REGION_COLUMN,
    value_vars=KEYWORD_COLUMNS,
    var_name="keyword_field",
    value_name="keyword"
)

long_keywords[REGION_COLUMN] = long_keywords[REGION_COLUMN].map(normalize_macroregion)
long_keywords["keyword"] = long_keywords["keyword"].map(normalize_keyword)

long_keywords = long_keywords.dropna(subset=[REGION_COLUMN, "keyword"])
long_keywords[REGION_COLUMN] = long_keywords[REGION_COLUMN].astype(int)

region_keyword_counts = (
    long_keywords
    .groupby([REGION_COLUMN, "keyword"])
    .size()
    .reset_index(name="frequency")
)

top10_by_region = (
    region_keyword_counts
    .sort_values([REGION_COLUMN, "frequency", "keyword"], ascending=[True, False, True])
    .groupby(REGION_COLUMN, group_keys=False)
    .head(10)
)

# Chart 1: one horizontal bar chart per macroregion, sorted from 1 to 10
for region_code in MACROREGION_ORDER:
    data = top10_by_region[top10_by_region[REGION_COLUMN] == region_code]

    if data.empty:
        continue

    plot_data = data.sort_values("frequency", ascending=True)

    plt.figure(figsize=(10, 6))
    plt.barh(plot_data["keyword"], plot_data["frequency"], color="#2f6f9f")
    plt.title(f"Top 10 Keywords in Macroregion {region_code}")
    plt.xlabel("Frequency")
    plt.ylabel("Keyword")
    plt.tight_layout()

    plt.savefig(
        CHART_DIR / f"top_10_keywords_macroregion_{region_code}.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


# Chart 2: combined heatmap, columns sorted from 1 to 10
heatmap_data = top10_by_region.pivot_table(
    index="keyword",
    columns=REGION_COLUMN,
    values="frequency",
    fill_value=0,
    aggfunc="sum"
)

heatmap_data = heatmap_data.reindex(columns=MACROREGION_ORDER, fill_value=0)

heatmap_data = heatmap_data.loc[
    heatmap_data.sum(axis=1).sort_values(ascending=False).index
]

plt.figure(figsize=(14, max(8, len(heatmap_data) * 0.35)))
sns.heatmap(
    heatmap_data,
    cmap="Blues",
    linewidths=0.4,
    linecolor="white",
    annot=True,
    fmt=".0f",
    cbar_kws={"label": "Frequency"}
)
plt.title("Top Keywords by Macroregion")
plt.xlabel("Macroregion Code")
plt.ylabel("Keyword")
plt.tight_layout()

plt.savefig(
    CHART_DIR / "top_keywords_by_macroregion_heatmap.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

print("Done.")
print(f"Macroregions found: {sorted(top10_by_region[REGION_COLUMN].unique())}")
print(f"Saved charts to: {CHART_DIR.resolve()}")