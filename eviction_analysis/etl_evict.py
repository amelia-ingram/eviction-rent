import pandas as pd
from pathlib import Path

# Eviction lab data: https://evictionlab.org/
EVICTION_FULL: str = "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/all_sites_weekly_2020_2021.csv"
EVICTION_NY: str = "https://evictionlab.org/uploads/newyork_weekly_2020_2021.csv"
# Fair market rate data: https://www.huduser.gov/portal/datasets/fmr.html
SMALL_FMR_22: str = (
    "https://www.huduser.gov/portal/datasets/fmr/fmr2022/fy2022_safmrs_revised.xlsx"
)

# Relative paths
PKG_DIR: Path = Path(__file__).parent.resolve()
DATA_DIR: Path = PKG_DIR.joinpath("..", "..", "assets", "data", "raw")
ZIP_TRACT: Path = DATA_DIR.joinpath("ZIP_TRACT_122021.xlsx")


def load_eviction(path: str, pyarrow: bool = False) -> pd.DataFrame:
    """Load and clean Eviction Lab data set.

    Parameters
    ----------
    path: str
        Path to Eviction Lab data as a CSV.
    pyarrow: bool
        Use Apache Arrow if True. Defaults to False because PyArrow support is
        experimental and thus is missing many features.

    Returns
    -------
    pandas.DataFrame
        Loaded data.
    """

    ## read_csv arguments
    dtype: dict[str, str] = {
        "city": "category",
        "racial_majority": "category",
        "type": "category",
    }
    # I'm biased. I like Arrow.
    # infer_datetime_format is only enabled if Arrow is disabled because PyArrow doesn't support it yet.
    # Likewise, low_memory is enabled with PyArrow and disabled otherwise.
    engine: bool = "pyarrow" if pyarrow else None
    # GEOID's missing zip codes are tagged as "sealed" but they should be NaNs.
    na_values: dict[str, str] = {"GEOID": "sealed"}
    # Date columns
    parse_dates: list[str] = ["last_updated", "week_date"]

    df: pd.DataFrame = pd.read_csv(
        path,
        dtype=dtype,
        engine=engine,
        na_values=na_values,
        parse_dates=parse_dates,
        infer_datetime_format=not pyarrow,
        low_memory=pyarrow,
    )

    return df


def load_fmr(path: str, year: int) -> pd.DataFrame:
    """Load and clean Fair Market Rate data set.

    Parameters
    ----------
    path: str
        Path to FMR data as an Excel file.

    Returns
    -------
    pandas.DataFrame
        Loaded data.
    """
    # I want to use RegEx to match the terrible column names, so I can't use
    # names and usecols.
    df: pd.DataFrame = pd.read_excel(path)

    # Rename the horrible Excel columns
    names: List[str] = ["zipcode", "fmr_2br", "fmr_2br_90", "fmr_2br_110"]
    usecols = df.columns.str.match(r"(SAFMR\n2)|(ZIP)")
    df: pd.DataFrame = df[usecols]
    df.columns = names

    # Add in year because we're using multiple FMR data sets
    df["fmr_year"] = year

    return df


def load_zip_city(path: Union[str, Path] = ZIP_TRACT) -> pd.DataFrame:
    """Write later."""

    # Rename zip because it's a keyword and therefore annoying to use.
    # Rename usps-whatever because it's wordy.
    names: List[str] = ["zipcode", "tract", "city", "state"]
    # We don't need the rest of the columns
    usecols: List[str] = ["zip", "tract", "usps_zip_pref_city", "usps_zip_pref_state"]

    zip_tract: pd.DataFrame = pd.read_excel(path, names=names, usecols=usecols)
    # Lower cased city will help with merges
    zip_tract.city = zip_tract.city.str.lower()
    return zip_tract


def merge_evic_fmr(evictions: pd.DataFrame, fmr: pd.DataFrame) -> pd.DataFrame:
    """Write later."""

    # Temporary, lower cased city names as well as states to ease merging
    city_state = evictions.city.str.extract(r"^(\w+),\s(\w+)$")
    city_state.columns = ["temp_city", "temp_state"]
    evictions = pd.concat([evictions, city_state], axis="columns")

    # Zip and census tract data. I want zip codes and tracts to be melted so
    # that they're associated with each city, state pair.
    zip_tract = load_zip_city()
    zip_tract = zip_tract.melt(["city", "state"])

    # Fair market data
    fmr_years = [2020, 2021, 2022]
    fmr_paths = [
        DATA_DIR.joinpath(f"fy{year}_safmrs_revised.xlsx") for year in fmr_years
    ]
