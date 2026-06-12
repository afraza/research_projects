import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_FILE = "scientific_projects_iran.xlsx"
FIELD_LOOKUP_FILE = "field-of-study.xlsx"

CHART_DIR = Path("charts/field_of_study_keywords")
CHART_DIR.mkdir(parents=True, exist_ok=True)

KEYWORD_COLUMNS = ["keyword1", "keyword2", "keyword3"]
FIELD_CODE_COLUMN = "field-of-study-code"
FIELD_NAME_COLUMN = "field-of-study"

TOP_FIELDS_FOR_BAR_CHARTS = 10
TOP_KEYWORDS_PER_FIELD = 10

TOP_FIELDS_FOR_HEATMAP = 20
TOP_KEYWORDS_FOR_HEATMAP = 20

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


def normalize_field_code(value):
    if is_null_like(value):
        return None

    try:
        code = int(float(str(value).strip()))
    except ValueError:
        return None

    if code < 1 or code > 331:
        return None

    return code


def normalize_field_name(value):
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


def load_field_lookup(path):
    lookup = pd.read_excel(path)

    required = [FIELD_CODE_COLUMN, FIELD_NAME_COLUMN]
    missing = [col for col in required if col not in lookup.columns]
    if missing:
        raise ValueError(f"Missing columns in field lookup file: {missing}")

    lookup[FIELD_CODE_COLUMN] = lookup[FIELD_CODE_COLUMN].map(normalize_field_code)
    lookup[FIELD_NAME_COLUMN] = lookup[FIELD_NAME_COLUMN].map(normalize_field_name)

    lookup = lookup.dropna(subset=[FIELD_CODE_COLUMN])
    lookup[FIELD_CODE_COLUMN] = lookup[FIELD_CODE_COLUMN].astype(int)

    return dict(zip(lookup[FIELD_CODE_COLUMN], lookup[FIELD_NAME_COLUMN]))


def field_label(code, lookup):
    name = lookup.get(code)

    if name and not is_null_like(name):
        return name

    return str(code)


field_lookup = load_field_lookup(FIELD_LOOKUP_FILE)

df = pd.read_excel(INPUT_FILE)

required_columns = KEYWORD_COLUMNS + [FIELD_CODE_COLUMN]
missing_cols = [col for col in required_columns if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing columns in main Excel file: {missing_cols}")

# Normalize and discard invalid/null field-of-study codes.
df[FIELD_CODE_COLUMN] = df[FIELD_CODE_COLUMN].map(normalize_field_code)
df = df.dropna(subset=[FIELD_CODE_COLUMN])
df[FIELD_CODE_COLUMN] = df[FIELD_CODE_COLUMN].astype(int)

# Convert keyword1/keyword2/keyword3 into long format.
long_keywords = df[[FIELD_CODE_COLUMN] + KEYWORD_COLUMNS].melt(
    id_vars=FIELD_CODE_COLUMN,
    value_vars=KEYWORD_COLUMNS,
    var_name="keyword_field",
    value_name="keyword"
)

# Normalize and discard invalid/null keywords.
long_keywords["keyword"] = long_keywords["keyword"].map(normalize_keyword)
long_keywords = long_keywords.dropna(subset=[FIELD_CODE_COLUMN, "keyword"])
long_keywords[FIELD_CODE_COLUMN] = long_keywords[FIELD_CODE_COLUMN].astype(int)

# Most frequent fields are based on number of records/projects.
field_frequency = df[FIELD_CODE_COLUMN].value_counts()

top_fields_for_bar_charts = field_frequency.head(TOP_FIELDS_FOR_BAR_CHARTS).index.tolist()
top_fields_for_heatmap = field_frequency.head(TOP_FIELDS_FOR_HEATMAP).index.tolist()

# Chart 1: top 10 keywords in each of the 10 most frequent fields.
bar_source = long_keywords[
    long_keywords[FIELD_CODE_COLUMN].isin(top_fields_for_bar_charts)
]

field_keyword_counts = (
    bar_source
    .groupby([FIELD_CODE_COLUMN, "keyword"])
    .size()
    .reset_index(name="frequency")
)

top10_keywords_by_field = (
    field_keyword_counts
    .sort_values([FIELD_CODE_COLUMN, "frequency", "keyword"], ascending=[True, False, True])
    .groupby(FIELD_CODE_COLUMN, group_keys=False)
    .head(TOP_KEYWORDS_PER_FIELD)
)

for field_code in top_fields_for_bar_charts:
    data = top10_keywords_by_field[
        top10_keywords_by_field[FIELD_CODE_COLUMN] == field_code
    ]

    if data.empty:
        continue

    plot_data = data.sort_values("frequency", ascending=True)
    label = field_label(field_code, field_lookup)

    plt.figure(figsize=(12, 6))
    plt.barh(plot_data["keyword"], plot_data["frequency"], color="#2f6f9f")
    plt.title(f"Top 10 Keywords - {label}")
    plt.xlabel("Frequency")
    plt.ylabel("Keyword")
    plt.tight_layout()

    plt.savefig(
        CHART_DIR / f"top_10_keywords_field_{safe_filename(label)}.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


# Chart 2: heatmap with top 20 fields and top 20 overall keywords.
top_keywords_for_heatmap = (
    long_keywords["keyword"]
    .value_counts()
    .head(TOP_KEYWORDS_FOR_HEATMAP)
    .index
    .tolist()
)

heatmap_source = long_keywords[
    long_keywords[FIELD_CODE_COLUMN].isin(top_fields_for_heatmap)
    & long_keywords["keyword"].isin(top_keywords_for_heatmap)
]

heatmap_data = heatmap_source.pivot_table(
    index="keyword",
    columns=FIELD_CODE_COLUMN,
    values="keyword_field",
    fill_value=0,
    aggfunc="count"
)

heatmap_data = heatmap_data.reindex(
    index=top_keywords_for_heatmap,
    columns=top_fields_for_heatmap,
    fill_value=0
)

heatmap_labels = [
    field_label(code, field_lookup)
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

plt.title("Top 20 Keywords Across the 20 Most Frequent Field-of-Studies")
plt.xlabel("Field of Study")
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
    CHART_DIR / "top_20_keywords_by_top_20_field_of_studies_heatmap.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

print("Done.")
print(f"Valid keyword rows used: {len(long_keywords)}")
print(f"Saved charts to: {CHART_DIR.resolve()}")