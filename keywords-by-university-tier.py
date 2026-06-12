import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_FILE = "scientific_projects_iran.xlsx"

CHART_DIR = Path("charts")
CHART_DIR.mkdir(exist_ok=True)

KEYWORD_COLUMNS = ["keyword1", "keyword2", "keyword3"]
TIER_COLUMN = "university-tier"
TIER_ORDER = [0, 1, 2, 3]


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


def normalize_tier(value):
    if pd.isna(value):
        return None

    try:
        tier = int(float(value))
    except ValueError:
        return None

    if tier not in TIER_ORDER:
        return None

    return tier


def tier_label(tier):
    labels = {
        0: "Not included in tier",
        1: "Tier 1",
        2: "Tier 2",
        3: "Tier 3",
    }
    return labels[tier]


df = pd.read_excel(INPUT_FILE)

required_columns = KEYWORD_COLUMNS + [TIER_COLUMN]
missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing columns in Excel file: {missing_cols}")

long_keywords = df[[TIER_COLUMN] + KEYWORD_COLUMNS].melt(
    id_vars=TIER_COLUMN,
    value_vars=KEYWORD_COLUMNS,
    var_name="keyword_field",
    value_name="keyword"
)

long_keywords[TIER_COLUMN] = long_keywords[TIER_COLUMN].map(normalize_tier)
long_keywords["keyword"] = long_keywords["keyword"].map(normalize_keyword)

long_keywords = long_keywords.dropna(subset=[TIER_COLUMN, "keyword"])
long_keywords[TIER_COLUMN] = long_keywords[TIER_COLUMN].astype(int)

tier_keyword_counts = (
    long_keywords
    .groupby([TIER_COLUMN, "keyword"])
    .size()
    .reset_index(name="frequency")
)

top10_by_tier = (
    tier_keyword_counts
    .sort_values([TIER_COLUMN, "frequency", "keyword"], ascending=[True, False, True])
    .groupby(TIER_COLUMN, group_keys=False)
    .head(10)
)

# Chart 1: one horizontal bar chart per university tier
for tier in TIER_ORDER:
    data = top10_by_tier[top10_by_tier[TIER_COLUMN] == tier]

    if data.empty:
        continue

    plot_data = data.sort_values("frequency", ascending=True)

    plt.figure(figsize=(10, 6))
    plt.barh(plot_data["keyword"], plot_data["frequency"], color="#2f6f9f")
    plt.title(f"Top 10 Keywords - {tier_label(tier)}")
    plt.xlabel("Frequency")
    plt.ylabel("Keyword")
    plt.tight_layout()

    plt.savefig(
        CHART_DIR / f"top_10_keywords_university_tier_{tier}.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


# Chart 2: combined heatmap
heatmap_data = top10_by_tier.pivot_table(
    index="keyword",
    columns=TIER_COLUMN,
    values="frequency",
    fill_value=0,
    aggfunc="sum"
)

heatmap_data = heatmap_data.reindex(columns=TIER_ORDER, fill_value=0)
heatmap_data.columns = [tier_label(tier) for tier in heatmap_data.columns]

heatmap_data = heatmap_data.loc[
    heatmap_data.sum(axis=1).sort_values(ascending=False).index
]

plt.figure(figsize=(12, max(8, len(heatmap_data) * 0.35)))
sns.heatmap(
    heatmap_data,
    cmap="Blues",
    linewidths=0.4,
    linecolor="white",
    annot=True,
    fmt=".0f",
    cbar_kws={"label": "Frequency"}
)
plt.title("Top Keywords by University Tier")
plt.xlabel("University Tier")
plt.ylabel("Keyword")
plt.tight_layout()

plt.savefig(
    CHART_DIR / "top_keywords_by_university_tier_heatmap.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

print("Done.")
print(f"Tiers found: {sorted(top10_by_tier[TIER_COLUMN].unique())}")
print(f"Saved charts to: {CHART_DIR.resolve()}")