import pandas as pd

# Eviction lab data: https://evictionlab.org/
EVICTION_FULL: str = "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/all_sites_weekly_2020_2021.csv"
EVICTION_NY: str = "https://evictionlab.org/uploads/newyork_weekly_2020_2021.csv"


def load_eviction(path: str, pyarrow: bool = True) -> pd.DataFrame:
    """Load and clean Eviction Lab data set.

    Parameters
    ----------
    path: str
        Path to Eviction Lab data as a CSV.
    pyarrow: bool
        Use Apache Arrow if True

    Returns
    -------
    pandas.DataFrame
        Loaded data.
    """

    ## read_csv arguments
    dtype = {"city": "category", "type": "category", "racial_majority": "category"}
    # I'm biased. I like Arrow.
    # infer_datetime_format is only enabled if Arrow is disabled because pyarrow doesn't support it yet.
    engine = "pyarrow" if pyarrow else None
    # GEOID's missing zip codes are tagged as "sealed"
    na_values = {"GEOID": "sealed"}

    df: pd.DataFrame = pd.read_csv(
        path,
        dtype=dtype,
        engine=engine,
        na_values=na_values,
        parse_dates=["week_date", "last_updated"],
        infer_datetime_format=not pyarrow,
        low_memory=False,
    )

    return df
