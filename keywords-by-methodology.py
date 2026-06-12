import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_FILE = "scientific_projects_iran.xlsx"
METHODOLOGY_LOOKUP_FILE = "Methodology-code.xlsx"

CHART_DIR = Path("charts/methodology_keywords")
CHART_DIR.mkdir(parents=True, exist_ok=True)

KEYWORD_COLUMNS = ["keyword1", "keyword2", "keyword3"]
METHODOLOGY_CODE_COLUMN = "Methodology-code"
METHODOLOGY_NAME_COLUMN = "Methodology"

TOP_KEYWORDS_PER_METHODOLOGY = 10
TOP_KEYWORDS_FOR_HEATMAP = 20
METHODOLOGY_ORDER = list(range(1, 17))

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


def normalize_methodology_code(value):
    if is_null_like(value):
        return None

    try:
        code = int(float(str(value).strip()))
    except ValueError:
        return None

    if code not in METHODOLOGY_ORDER:
        return None

    return code


def normalize_methodology_name(value):
    if is_null_like(value):
        return None

    text = str(value).strip().lower()

    text = text.replace("_", " ")
    text = text.replace("/", " ")
    text = text.replace("\\", " ")
    text = text.replace("&", " and ")

    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text.title() if text else None


def safe_filename(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9_-]+", "_", text)
    return text.strip("_")[:120]


def load_methodology_lookup(path):
    lookup = pd.read_excel(path)

    required = [METHODOLOGY_CODE_COLUMN, METHODOLOGY_NAME_COLUMN]
    missing = [col for col in required if col not in lookup.columns]
    if missing:
        raise ValueError(f"Missing columns in Methodology-code.xlsx: {missing}")

    lookup[METHODOLOGY_CODE_COLUMN] = lookup[METHODOLOGY_CODE_COLUMN].map(
        normalize_methodology_code
    )
    lookup[METHODOLOGY_NAME_COLUMN] = lookup[METHODOLOGY_NAME_COLUMN].map(
        normalize_methodology_name
    )

    lookup = lookup.dropna(subset=[METHODOLOGY_CODE_COLUMN])
    lookup[METHODOLOGY_CODE_COLUMN] = lookup[METHODOLOGY_CODE_COLUMN].astype(int)

    return dict(zip(lookup[METHODOLOGY_CODE_COLUMN], lookup[METHODOLOGY_NAME_COLUMN]))


def methodology_label(code, lookup):
    name = lookup.get(code)

    if name and not is_null_like(name):
        return name

    return str(code)


methodology_lookup = load_methodology_lookup(METHODOLOGY_LOOKUP_FILE)

df = pd.read_excel(INPUT_FILE)

required_columns = KEYWORD_COLUMNS + [METHODOLOGY_CODE_COLUMN]
missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing columns in main Excel file: {missing_cols}")

# Normalize and discard invalid/null methodology codes.
df[METHODOLOGY_CODE_COLUMN] = df[METHODOLOGY_CODE_COLUMN].map(
    normalize_methodology_code
)
df = df.dropna(subset=[METHODOLOGY_CODE_COLUMN])
df[METHODOLOGY_CODE_COLUMN] = df[METHODOLOGY_CODE_COLUMN].astype(int)

# Convert keyword1/keyword2/keyword3 into long format.
long_keywords = df[[METHODOLOGY_CODE_COLUMN] + KEYWORD_COLUMNS].melt(
    id_vars=METHODOLOGY_CODE_COLUMN,
    value_vars=KEYWORD_COLUMNS,
    var_name="keyword_field",
    value_name="keyword"
)

# Normalize and discard invalid/null keywords.
long_keywords["keyword"] = long_keywords["keyword"].map(normalize_keyword)
long_keywords = long_keywords.dropna(subset=[METHODOLOGY_CODE_COLUMN, "keyword"])
long_keywords[METHODOLOGY_CODE_COLUMN] = long_keywords[METHODOLOGY_CODE_COLUMN].astype(int)

methodology_keyword_counts = (
    long_keywords
    .groupby([METHODOLOGY_CODE_COLUMN, "keyword"])
    .size()
    .reset_index(name="frequency")
)

top10_keywords_by_methodology = (
    methodology_keyword_counts
    .sort_values(
        [METHODOLOGY_CODE_COLUMN, "frequency", "keyword"],
        ascending=[True, False, True]
    )
    .groupby(METHODOLOGY_CODE_COLUMN, group_keys=False)
    .head(TOP_KEYWORDS_PER_METHODOLOGY)
)

# Chart 1: one horizontal bar chart per methodology
for methodology_code in METHODOLOGY_ORDER:
    data = top10_keywords_by_methodology[
        top10_keywords_by_methodology[METHODOLOGY_CODE_COLUMN] == methodology_code
    ]

    if data.empty:
        continue

    plot_data = data.sort_values("frequency", ascending=True)
    label = methodology_label(methodology_code, methodology_lookup)

    plt.figure(figsize=(12, 6))
    plt.barh(plot_data["keyword"], plot_data["frequency"], color="#2f6f9f")
    plt.title(f"Top 10 Keywords - {label}")
    plt.xlabel("Frequency")
    plt.ylabel("Keyword")
    plt.tight_layout()

    plt.savefig(
        CHART_DIR / f"top_10_keywords_methodology_{safe_filename(label)}.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


# Chart 2: heatmap with all 16 methodologies and top 20 overall keywords.
top_keywords_for_heatmap = (
    long_keywords["keyword"]
    .value_counts()
    .head(TOP_KEYWORDS_FOR_HEATMAP)
    .index
    .tolist()
)

heatmap_source = long_keywords[
    long_keywords["keyword"].isin(top_keywords_for_heatmap)
]

heatmap_data = heatmap_source.pivot_table(
    index="keyword",
    columns=METHODOLOGY_CODE_COLUMN,
    values="keyword_field",
    fill_value=0,
    aggfunc="count"
)

heatmap_data = heatmap_data.reindex(
    index=top_keywords_for_heatmap,
    columns=METHODOLOGY_ORDER,
    fill_value=0
)

heatmap_labels = [
    methodology_label(code, methodology_lookup)
    for code in heatmap_data.columns
]

plt.figure(figsize=(20, 10))
sns.heatmap(
    heatmap_data,
    cmap="Blues",
    linewidths=0.4,
    linecolor="white",
    annot=True,
    fmt=".0f",
    cbar_kws={"label": "Frequency"}
)

plt.title("Top 20 Keywords Across All Methodologies")
plt.xlabel("Methodology")
plt.ylabel("Keyword")
plt.xticks(
    ticks=[i + 0.5 for i in range(len(heatmap_labels))],
    labels=heatmap_labels,
    rotation=45,
    ha="right",
    fontsize=8
)
plt.tight_layout()

plt.savefig(
    CHART_DIR / "top_20_keywords_by_all_methodologies_heatmap.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

print("Done.")
print(f"Valid keyword rows used: {len(long_keywords)}")
print(f"Methodologies found: {sorted(long_keywords[METHODOLOGY_CODE_COLUMN].unique())}")
print(f"Saved charts to: {CHART_DIR.resolve()}"