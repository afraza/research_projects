import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_FILE = "scientific_projects_iran.xlsx"
LOOKUP_FILE = "university_lookup.xlsx"

CHART_DIR = Path("charts/university_keywords")
CHART_DIR.mkdir(parents=True, exist_ok=True)

KEYWORD_COLUMNS = ["keyword1", "keyword2", "keyword3"]
UNIVERSITY_COLUMN = "university-code"
UNIVERSITY_NAME_COLUMN = "university-name"


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


def normalize_code(value):
    if pd.isna(value):
        return None

    try:
        return int(float(value))
    except ValueError:
        return None


def safe_filename(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9_-]+", "_", text)
    return text.strip("_")[:120]


def load_university_lookup(path):
    lookup = pd.read_excel(path)

    required = [UNIVERSITY_COLUMN, UNIVERSITY_NAME_COLUMN]
    missing = [col for col in required if col not in lookup.columns]
    if missing:
        raise ValueError(f"Missing columns in lookup file: {missing}")

    lookup[UNIVERSITY_COLUMN] = lookup[UNIVERSITY_COLUMN].map(normalize_code)
    lookup[UNIVERSITY_NAME_COLUMN] = lookup[UNIVERSITY_NAME_COLUMN].astype(str).str.strip()

    lookup = lookup.dropna(subset=[UNIVERSITY_COLUMN, UNIVERSITY_NAME_COLUMN])
    lookup[UNIVERSITY_COLUMN] = lookup[UNIVERSITY_COLUMN].astype(int)

    return dict(zip(lookup[UNIVERSITY_COLUMN], lookup[UNIVERSITY_NAME_COLUMN]))


def university_label(code, lookup):
    name = lookup.get(code)
    if name:
        return f"{code} - {name}"
    return f"{code} - Unknown university"


university_lookup = load_university_lookup(LOOKUP_FILE)

df = pd.read_excel(INPUT_FILE)

required_columns = KEYWORD_COLUMNS + [UNIVERSITY_COLUMN]
missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing columns in main Excel file: {missing_cols}")

long_keywords = df[[UNIVERSITY_COLUMN] + KEYWORD_COLUMNS].melt(
    id_vars=UNIVERSITY_COLUMN,
    value_vars=KEYWORD_COLUMNS,
    var_name="keyword_field",
    value_name="keyword"
)

long_keywords[UNIVERSITY_COLUMN] = long_keywords[UNIVERSITY_COLUMN].map(normalize_code)
long_keywords["keyword"] = long_keywords["keyword"].map(normalize_keyword)

long_keywords = long_keywords.dropna(subset=[UNIVERSITY_COLUMN, "keyword"])
long_keywords[UNIVERSITY_COLUMN] = long_keywords[UNIVERSITY_COLUMN].astype(int)

university_keyword_counts = (
    long_keywords
    .groupby([UNIVERSITY_COLUMN, "keyword"])
    .size()
    .reset_index(name="frequency")
)

top10_by_university = (
    university_keyword_counts
    .sort_values(
        [UNIVERSITY_COLUMN, "frequency", "keyword"],
        ascending=[True, False, True]
    )
    .groupby(UNIVERSITY_COLUMN, group_keys=False)
    .head(10)
)

university_codes = sorted(top10_by_university[UNIVERSITY_COLUMN].unique())

# Chart 1: one horizontal bar chart per university / higher education institute
for code in university_codes:
    data = top10_by_university[top10_by_university[UNIVERSITY_COLUMN] == code]

    if data.empty:
        continue

    plot_data = data.sort_values("frequency", ascending=True)
    label = university_label(code, university_lookup)

    plt.figure(figsize=(12, 6))
    plt.barh(plot_data["keyword"], plot_data["frequency"], color="#2f6f9f")
    plt.title(f"Top 10 Keywords - {label}")
    plt.xlabel("Frequency")
    plt.ylabel("Keyword")
    plt.tight_layout()

    plt.savefig(
        CHART_DIR / f"top_10_keywords_university_{code}_{safe_filename(university_lookup.get(code, 'unknown'))}.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


# Chart 2: combined heatmap
# Only include the 30 most frequent keywords overall.
TOP_N_HEATMAP_KEYWORDS = 30

top_heatmap_keywords = (
    long_keywords["keyword"]
    .value_counts()
    .head(TOP_N_HEATMAP_KEYWORDS)
    .index
)

heatmap_source = long_keywords[
    long_keywords["keyword"].isin(top_heatmap_keywords)
]

heatmap_data = heatmap_source.pivot_table(
    index="keyword",
    columns=UNIVERSITY_COLUMN,
    values="keyword_field",
    fill_value=0,
    aggfunc="count"
)

heatmap_data = heatmap_data.reindex(
    index=top_heatmap_keywords,
    columns=university_codes,
    fill_value=0
)

heatmap_labels = [
    university_lookup.get(code, str(code))
    for code in heatmap_data.columns
]

plt.figure(figsize=(max(16, len(university_codes) * 0.5), 12))
sns.heatmap(
    heatmap_data,
    cmap="Blues",
    linewidths=0.3,
    linecolor="white",
    annot=False,
    cbar_kws={"label": "Frequency"}
)

plt.title("Top 30 Keywords by University / Higher Education Institute")
plt.xlabel("University / Higher Education Institute")
plt.ylabel("Keyword")
plt.xticks(
    ticks=[i + 0.5 for i in range(len(heatmap_labels))],
    labels=heatmap_labels,
    rotation=90,
    fontsize=7
)
plt.tight_layout()

plt.savefig(
    CHART_DIR / "top_30_keywords_by_university_heatmap.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

print("Done.")
print(f"Universities found in data: {len(university_codes)}")
print(f"University names loaded from lookup: {len(university_lookup)}")
print(f"Saved charts to: {CHART_DIR.resolve()}")