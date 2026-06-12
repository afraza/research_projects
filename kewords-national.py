import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

INPUT_FILE = "scientific_projects_iran.xlsx"

CHART_DIR = Path("charts")
CHART_DIR.mkdir(exist_ok=True)

KEYWORD_COLUMNS = ["keyword1", "keyword2", "keyword3"]


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


df = pd.read_excel(INPUT_FILE)

missing_cols = [col for col in KEYWORD_COLUMNS if col not in df.columns]
if missing_cols:
    raise ValueError(f"Missing columns in Excel file: {missing_cols}")

keywords = (
    df[KEYWORD_COLUMNS]
    .stack(dropna=True)
    .map(normalize_keyword)
    .dropna()
)

keyword_counts = (
    keywords
    .value_counts()
    .rename_axis("keyword")
    .reset_index(name="frequency")
)

top15 = keyword_counts.head(15)
top20 = keyword_counts.head(20)


def plot_keyword_bar_chart(data, title, output_png):
    plt.figure(figsize=(11, 7))

    plot_data = data.iloc[::-1]

    plt.barh(plot_data["keyword"], plot_data["frequency"], color="#2f6f9f")
    plt.title(title)
    plt.xlabel("Frequency")
    plt.ylabel("Keyword")
    plt.tight_layout()

    plt.savefig(output_png, dpi=300, bbox_inches="tight")
    plt.close()


plot_keyword_bar_chart(
    top15,
    "Top 15 Most Frequent Keywords",
    CHART_DIR / "top_15_keywords.png"
)

plot_keyword_bar_chart(
    top20,
    "Top 20 Most Frequent Keywords",
    CHART_DIR / "top_20_keywords.png"
)

print("Done.")
print(f"Total unique keywords: {len(keyword_counts)}")
print(f"Saved charts to: {CHART_DIR.resolve()}")