import json
import re
import textwrap
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.request import urlopen, urlretrieve

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib import cm, colors
from matplotlib.patches import Patch, Polygon
import pandas as pd


# -----------------------------
# Settings
# -----------------------------
PROJECT_DIR = Path(__file__).resolve().parent
EXCEL_FILE = PROJECT_DIR / "scientific_projects_iran.xlsx"
PROVINCE_LOOKUP_FILE = PROJECT_DIR / "province.xlsx"
DISEASE_COLUMN = "disease"
PROVINCE_CODE_COLUMN = "province-code"
PROVINCE_NATIVE_NAME_COLUMN = "استان"

CHARTS_DIR = PROJECT_DIR / "charts"
BOUNDARY_DIR = CHARTS_DIR / "disease_province_map_data"
BOUNDARY_FILE = BOUNDARY_DIR / "iran_provinces_adm1.geojson"
GEOBOUNDARIES_API_URL = "https://www.geoboundaries.org/api/current/gbOpen/IRN/ADM1/"

INVALID_VALUES = {"", "-", "--", "---", "nan", "none", "null", "n/a", "na", "#n/a"}


def get_numbered_path(path):
    if not path.exists():
        return path

    counter = 1
    while True:
        candidate = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def normalize_code(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()
    if text.lower() in INVALID_VALUES:
        return pd.NA

    numeric_value = pd.to_numeric(text, errors="coerce")
    if pd.notna(numeric_value) and float(numeric_value).is_integer():
        return str(int(numeric_value))
    return text


def province_key(value):
    """Normalize English province names from the lookup and boundary files."""
    if pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    text = text.lower().replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\b(province|ostan|va)\b", " ", text)
    return " ".join(text.split())


# Names used by common Iran ADM1 boundary datasets that differ from province.xlsx.
PROVINCE_ALIASES = {
    "east azerbaijan": {"east azerbaijan", "azarbayjan e sharqi", "azarbaijan e sharqi"},
    "west azerbaijan": {"west azerbaijan", "azarbayjan e gharbi", "azarbaijan e gharbi"},
    "north khorasan": {"north khorasan", "khorasan shomali"},
    "south khorasan": {"south khorasan", "khorasan jonoubi", "khorasan jonoobi"},
    "razavi khorasan": {"razavi khorasan", "khorasan razavi"},
    "sistan and baluchestan": {"sistan and baluchestan", "sistan va baluchestan"},
    "chaharmahal and bakhtiari": {
        "chaharmahal and bakhtiari",
        "chahar mahal and bakhtiari",
        "chaharmahal va bakhtiari",
    },
    "kohgiluyeh and boyer ahmad": {
        "kohgiluyeh and boyer ahmad",
        "kohgiluyeh va boyer ahmad",
        "kohgiluyeh and buyer ahmad",
    },
}


def canonical_province_key(value):
    key = province_key(value)
    for canonical, aliases in PROVINCE_ALIASES.items():
        if key in aliases:
            return canonical
    return key


def load_boundary_features():
    """Download GeoBoundaries ADM1 data once, then use the local cached GeoJSON."""
    BOUNDARY_DIR.mkdir(parents=True, exist_ok=True)

    if not BOUNDARY_FILE.exists():
        try:
            with urlopen(GEOBOUNDARIES_API_URL, timeout=30) as response:
                boundary_metadata = json.load(response)
            urlretrieve(boundary_metadata["gjDownloadURL"], BOUNDARY_FILE)
        except Exception as error:
            raise RuntimeError(
                "Iran province boundaries could not be downloaded. Check your internet "
                f"connection, then run the script again. Details: {error}"
            ) from error

    with BOUNDARY_FILE.open(encoding="utf-8") as file:
        return json.load(file)["features"]


def feature_name(feature):
    properties = feature.get("properties", {})
    for key in ("shapeName", "name", "NAME_1", "ADM1_EN", "province"):
        value = properties.get(key)
        if value not in (None, ""):
            return str(value)
    raise ValueError(f"Could not find a province name in boundary properties: {properties}")


def polygon_rings(geometry):
    if geometry.get("type") == "Polygon":
        return [geometry.get("coordinates", [])]
    if geometry.get("type") == "MultiPolygon":
        return geometry.get("coordinates", [])
    return []


def ring_centroid(ring):
    """Calculate a polygon centroid for positioning a compact percentage label."""
    if len(ring) < 3:
        return None

    double_area = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        cross_product = x1 * y2 - x2 * y1
        double_area += cross_product
        centroid_x += (x1 + x2) * cross_product
        centroid_y += (y1 + y2) * cross_product

    if double_area == 0:
        return None
    return centroid_x / (3 * double_area), centroid_y / (3 * double_area)


def clean_disease_data(data):
    data[DISEASE_COLUMN] = data[DISEASE_COLUMN].astype(str).str.strip()
    data = data[
        data[DISEASE_COLUMN].notna()
        & (~data[DISEASE_COLUMN].str.lower().isin(INVALID_VALUES))
    ].copy()
    data[DISEASE_COLUMN] = data[DISEASE_COLUMN].str.lower().str.title()
    data[DISEASE_COLUMN] = data[DISEASE_COLUMN].replace(
        {"Covid-19": "COVID-19", "Cancer": "Cancer (general)"}
    )
    return data[data[DISEASE_COLUMN] != "COVID-19"].copy()


# -----------------------------
# Load and validate data
# -----------------------------
projects = pd.read_excel(EXCEL_FILE)
province_lookup = pd.read_excel(PROVINCE_LOOKUP_FILE)

required_project_columns = {DISEASE_COLUMN, PROVINCE_CODE_COLUMN}
missing_project_columns = required_project_columns - set(projects.columns)
if missing_project_columns:
    raise KeyError(f"Missing column(s) in {EXCEL_FILE.name}: {sorted(missing_project_columns)}")

required_lookup_columns = {PROVINCE_CODE_COLUMN, "province"}
missing_lookup_columns = required_lookup_columns - set(province_lookup.columns)
if missing_lookup_columns:
    raise KeyError(
        f"Missing column(s) in {PROVINCE_LOOKUP_FILE.name}: {sorted(missing_lookup_columns)}"
    )

projects = clean_disease_data(projects)
projects["_province_code"] = projects[PROVINCE_CODE_COLUMN].map(normalize_code)
projects = projects[projects["_province_code"].notna()].copy()

province_lookup = province_lookup.copy()
province_lookup["_province_code"] = province_lookup[PROVINCE_CODE_COLUMN].map(normalize_code)
province_lookup = province_lookup[province_lookup["_province_code"].notna()].copy()
province_lookup["_province_name"] = province_lookup["province"].astype(str).str.strip()

# Province code is the primary key. province.xlsx has repeated code 26, so the
# Persian province name is used only to disambiguate those records when available.
code_counts = province_lookup["_province_code"].value_counts()
unique_lookup = province_lookup[
    province_lookup["_province_code"].map(code_counts).eq(1)
].set_index("_province_code")["_province_name"]
projects["_province_name"] = projects["_province_code"].map(unique_lookup)

if PROVINCE_NATIVE_NAME_COLUMN in projects.columns and PROVINCE_NATIVE_NAME_COLUMN in province_lookup.columns:
    native_lookup = province_lookup.dropna(subset=[PROVINCE_NATIVE_NAME_COLUMN]).drop_duplicates(
        PROVINCE_NATIVE_NAME_COLUMN
    ).set_index(PROVINCE_NATIVE_NAME_COLUMN)["_province_name"]
    projects["_province_name"] = projects["_province_name"].fillna(
        projects[PROVINCE_NATIVE_NAME_COLUMN].map(native_lookup)
    )

unmapped_codes = sorted(projects.loc[projects["_province_name"].isna(), "_province_code"].unique())
if unmapped_codes:
    print(f"Warning: records with unmatched province code(s) were excluded: {unmapped_codes}")

projects = projects[projects["_province_name"].notna()].copy()
province_counts = projects["_province_name"].value_counts()

# -----------------------------
# Draw a geographic heat map on Iran's real province boundaries
# -----------------------------
features = load_boundary_features()
counts_by_key = defaultdict(int)
display_name_by_key = {}
for province_name, count in province_counts.items():
    key = canonical_province_key(province_name)
    counts_by_key[key] += int(count)
    display_name_by_key[key] = province_name

feature_keys = {canonical_province_key(feature_name(feature)) for feature in features}
unmatched_data_provinces = sorted(set(counts_by_key) - feature_keys)
if unmatched_data_provinces:
    unmatched_names = [display_name_by_key[key] for key in unmatched_data_provinces]
    print("Warning: lookup provinces without a matching boundary: " + ", ".join(unmatched_names))

max_count = max(counts_by_key.values(), default=1)
normalizer = colors.Normalize(vmin=0, vmax=max_count)
colormap = plt.get_cmap("YlOrRd")

fig, ax = plt.subplots(figsize=(13, 12))
for feature in features:
    count = counts_by_key.get(canonical_province_key(feature_name(feature)), 0)
    face_color = colormap(normalizer(count)) if count else "#F1F3F5"

    for polygon in polygon_rings(feature.get("geometry", {})):
        if polygon:
            ax.add_patch(
                Polygon(
                    polygon[0],
                    closed=True,
                    facecolor=face_color,
                    edgecolor="#FFFFFF",
                    linewidth=0.7,
                )
            )

ax.autoscale_view()
ax.set_aspect("equal")
ax.axis("off")
ax.set_title(
    "Disease-Related Project Frequency Across Iran Provinces",
    fontsize=16,
    pad=18,
)

colorbar = fig.colorbar(cm.ScalarMappable(norm=normalizer, cmap=colormap), ax=ax, shrink=0.75)
colorbar.set_label("Number of disease-related project records", rotation=90, labelpad=14)

CHARTS_DIR.mkdir(exist_ok=True)
output_path = get_numbered_path(
    CHARTS_DIR / "disease_frequency_across_iran_provinces_geographic_heatmap.png"
)
plt.tight_layout()
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close()

print(f"Geographic heat map saved to: {output_path}")

# -----------------------------
# Create one geographic heat map for each of the 10 most frequent diseases
# -----------------------------
top_10_diseases = projects[DISEASE_COLUMN].value_counts().head(10)
top_disease_max_count = 1

for disease_name in top_10_diseases.index:
    disease_province_counts = projects.loc[
        projects[DISEASE_COLUMN].eq(disease_name), "_province_name"
    ].value_counts()
    if not disease_province_counts.empty:
        top_disease_max_count = max(top_disease_max_count, int(disease_province_counts.max()))

disease_normalizer = colors.Normalize(vmin=0, vmax=top_disease_max_count)
fig, axes = plt.subplots(2, 5, figsize=(23, 10.5))
axes = axes.flatten()

for ax, (disease_name, total_count) in zip(axes, top_10_diseases.items()):
    disease_province_counts = projects.loc[
        projects[DISEASE_COLUMN].eq(disease_name), "_province_name"
    ].value_counts()
    disease_counts_by_key = defaultdict(int)

    for province_name, count in disease_province_counts.items():
        disease_counts_by_key[canonical_province_key(province_name)] += int(count)

    for feature in features:
        count = disease_counts_by_key.get(canonical_province_key(feature_name(feature)), 0)
        face_color = colormap(disease_normalizer(count)) if count else "#F1F3F5"

        for polygon in polygon_rings(feature.get("geometry", {})):
            if polygon:
                ax.add_patch(
                    Polygon(
                        polygon[0],
                        closed=True,
                        facecolor=face_color,
                        edgecolor="#FFFFFF",
                        linewidth=0.35,
                    )
                )

    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"{disease_name}\n({int(total_count)} records)", fontsize=11, pad=7)

for ax in axes[len(top_10_diseases):]:
    ax.axis("off")

fig.suptitle(
    "Geographic Distribution of the 10 Most Frequent Diseases Across Iran Provinces",
    fontsize=17,
    y=0.98,
)
fig.subplots_adjust(left=0.02, right=0.90, top=0.91, bottom=0.04, wspace=0.02, hspace=0.14)
colorbar_axis = fig.add_axes([0.92, 0.18, 0.014, 0.62])
colorbar = fig.colorbar(
    cm.ScalarMappable(norm=disease_normalizer, cmap=colormap), cax=colorbar_axis
)
colorbar.set_label("Records in a province", rotation=90, labelpad=13)

top_diseases_output_path = get_numbered_path(
    CHARTS_DIR / "disease_top_10_diseases_across_iran_provinces_geographic_heatmaps.png"
)
plt.savefig(top_diseases_output_path, dpi=300, bbox_inches="tight")
plt.close()

print(f"Top-disease geographic heat maps saved to: {top_diseases_output_path}")

# -----------------------------
# Show the disease with the highest share inside each province
# -----------------------------
province_disease_counts = (
    projects.groupby(["_province_name", DISEASE_COLUMN]).size().rename("record_count").reset_index()
)
province_totals = (
    province_disease_counts.groupby("_province_name")["record_count"].sum().rename("province_total")
)
dominant_disease_by_province = (
    province_disease_counts.sort_values(
        ["_province_name", "record_count", DISEASE_COLUMN],
        ascending=[True, False, True],
    )
    .drop_duplicates("_province_name")
    .join(province_totals, on="_province_name")
)
dominant_disease_by_province["percentage"] = (
    dominant_disease_by_province["record_count"]
    / dominant_disease_by_province["province_total"]
    * 100
)

dominant_data_by_key = {}
for _, row in dominant_disease_by_province.iterrows():
    dominant_data_by_key[canonical_province_key(row["_province_name"])] = {
        "disease": row[DISEASE_COLUMN],
        "percentage": row["percentage"],
    }

dominant_disease_order = (
    dominant_disease_by_province.groupby(DISEASE_COLUMN)["_province_name"]
    .count()
    .sort_values(ascending=False)
    .index.tolist()
)
dominant_colors = [
    "#A6CEE3",
    "#FDBF6F",
    "#B2DF8A",
    "#CAB2D6",
    "#FB9A99",
    "#FFFFB3",
    "#8DD3C7",
    "#BEBADA",
    "#CCEBC5",
    "#FFED6F",
    "#FCCDE5",
    "#D9D9D9",
    "#BC80BD",
    "#80B1D3",
    "#FFCC99",
    "#C7E9C0",
    "#FDCFE8",
    "#E5C494",
    "#B3E2CD",
    "#CDB4DB",
]
disease_color_map = {
    disease_name: dominant_colors[index % len(dominant_colors)]
    for index, disease_name in enumerate(dominant_disease_order)
}

fig, ax = plt.subplots(figsize=(16, 12))
for feature in features:
    province_details = dominant_data_by_key.get(canonical_province_key(feature_name(feature)))
    face_color = disease_color_map[province_details["disease"]] if province_details else "#F1F3F5"
    polygons = polygon_rings(feature.get("geometry", {}))

    for polygon in polygons:
        if polygon:
            ax.add_patch(
                Polygon(
                    polygon[0],
                    closed=True,
                    facecolor=face_color,
                    edgecolor="#FFFFFF",
                    linewidth=0.7,
                )
            )

    if province_details and polygons:
        largest_polygon = max((polygon for polygon in polygons if polygon), key=lambda polygon: len(polygon[0]))
        centroid = ring_centroid(largest_polygon[0])
        if centroid:
            disease_label = textwrap.fill(province_details["disease"], width=17)
            label_fontsize = 5.2 if len(province_details["disease"]) > 18 else 6.2
            label = ax.text(
                *centroid,
                f"{disease_label}\n{province_details['percentage']:.0f}%",
                ha="center",
                va="center",
                fontsize=label_fontsize,
                color="#1F2933",
                weight="bold",
                linespacing=0.9,
            )
            label.set_path_effects(
                [path_effects.withStroke(linewidth=1.6, foreground="#FFFFFF", alpha=0.9)]
            )

ax.autoscale_view()
ax.set_aspect("equal")
ax.axis("off")
ax.set_title(
    "Most Common Disease in Each Iran Province",
    fontsize=16,
    pad=18,
)

legend_handles = [
    Patch(
        facecolor=disease_color_map[disease_name],
        edgecolor="none",
        label=f"{disease_name} ({int((dominant_disease_by_province[DISEASE_COLUMN] == disease_name).sum())} provinces)",
    )
    for disease_name in dominant_disease_order
]
ax.legend(
    handles=legend_handles,
    title="Highest-share disease",
    loc="center left",
    bbox_to_anchor=(1.01, 0.5),
    frameon=False,
    fontsize=9,
    title_fontsize=10,
)
fig.text(
    0.5,
    0.04,
    "Percentage labels show that disease's share of all disease-related project records in the province.",
    ha="center",
    fontsize=9,
)
fig.subplots_adjust(left=0.03, right=0.73, top=0.93, bottom=0.08)

dominant_disease_output_path = get_numbered_path(
    CHARTS_DIR / "disease_most_common_disease_by_iran_province_geographic_map.png"
)
plt.savefig(dominant_disease_output_path, dpi=300, bbox_inches="tight")
plt.close()

print(f"Most-common-disease geographic map saved to: {dominant_disease_output_path}")
