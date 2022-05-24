import pandas as pd

# Eviction lab data: https://evictionlab.org/
EVICTION_FULL: str = "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/all_sites_weekly_2020_2021.csv"
EVICTION_NY: str = "https://evictionlab.org/uploads/newyork_weekly_2020_2021.csv"


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

# Loading FMR data: https://www.huduser.gov/portal/datasets/fmr.html#2022_data
SMALL_FMR_22: str = "https://www.huduser.gov/portal/datasets/fmr/fmr2022/fy2022_safmrs_revised.xlsx"


def load_fmr(path: str, pyarrow: bool = False) -> pd.DataFrame:
    """Load and clean Small FMR data set.

    Parameters
    ----------
    path: str
        Path to FMR data as a xlsx.
    pyarrow: bool
        Use Apache Arrow if True. Defaults to False because PyArrow support is
        experimental and thus is missing many features.

    Returns
    -------
    pandas.DataFrame
        Loaded data.
    """

    ## read_excel arguments
    dtype: dict[str, str] = {
        "HUD.Metro.Fair.Market.Rent.Area.Name": "category",
        "HUD.Area.Code": "category",
        "type": "category",
    }
    # infer_datetime_format is only enabled if Arrow is disabled because PyArrow doesn't support it yet.
    # Likewise, low_memory is enabled with PyArrow and disabled otherwise.
    engine: bool = "pyarrow" if pyarrow else None
    # ZIP.Code doesn't appear to have missing entries, but for consistency.
    na_values: dict[str, str] = {"ZIP.Code": "sealed"}


    df2: pd.DataFrame = pd.read_excel(
        path, header=0, sheet=1,
        dtype=dtype,
        engine=engine,
        na_values=na_values,
        parse_dates=parse_dates,
        infer_datetime_format=not pyarrow,
        low_memory=pyarrow,
    )

    return df2

