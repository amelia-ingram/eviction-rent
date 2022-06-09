import pandas as pd
import logging
from pathlib import Path
from typing import Union, Optional

## Online paths
# Eviction lab data: https://evictionlab.org/
EVICTION_FULL: str = "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/all_sites_weekly_2020_2021.csv"
EVICTION_NY: str = "https://evictionlab.org/uploads/newyork_weekly_2020_2021.csv"
# Fair market rate data: https://www.huduser.gov/portal/datasets/fmr.html
SMALL_FMR_22: str = (
    "https://www.huduser.gov/portal/datasets/fmr/fmr2022/fy2022_safmrs_revised.xlsx"
)

## Relative paths
PKG_DIR: Path = Path(__file__).parents[1].resolve()
DATA_DIR: Path = PKG_DIR.joinpath("assets", "data", "raw")
ZIP_TRACT: Path = DATA_DIR.joinpath("ZIP_TRACT_122021.xlsx")
EVICTION_REL: Path = DATA_DIR.joinpath("evictions_allcities_monthly_2020_2021.csv")
NYC_BOROUGH: Path = DATA_DIR.joinpath("nyc_zip_borough_neighborhoods_pop.csv")


def load_eviction(
    path: Union[str, Path] = EVICTION_REL,
    date_col: str = "month",
    pyarrow: bool = False,
) -> pd.DataFrame:
    """Load and clean Eviction Lab data set.

    Parameters
    ----------
    path: [str, Path]
        Path to Eviction Lab data as a CSV.
    pyarrow: bool
        Use Apache Arrow if True. Defaults to False because PyArrow support is
        experimental and thus is missing many features.

    Returns
    -------
    pandas.DataFrame
        Loaded data.
    """
    logging.info(f"Loading Eviction Lab data set from: {path}")

    ## read_csv arguments
    dtype: dict[str, str] = {
        "city": "category",
        "racial_majority": "category",
        "type": "category",
        "GEOID": "Int64",
    }
    # I'm biased. I like Arrow.
    # infer_datetime_format is only enabled if Arrow is disabled because PyArrow doesn't support it yet.
    # Likewise, low_memory is enabled with PyArrow and disabled otherwise.
    engine: bool = "pyarrow" if pyarrow else None
    # GEOID's missing zip codes are tagged as "sealed" but they should be NaNs.
    na_values: dict[str, str] = {"GEOID": "sealed"}
    # Date columns
    parse_dates: list[str] = ["last_updated", date_col]

    df: pd.DataFrame = pd.read_csv(
        path,
        dtype=dtype,
        engine=engine,
        na_values=na_values,
        parse_dates=parse_dates,
        infer_datetime_format=not pyarrow,
        low_memory=pyarrow,
    )
    df.columns = df.columns.str.lower()

    return df


def load_fmr(path: Union[str, Path], year: int) -> pd.DataFrame:
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
    logging.info(f"Loading {year} Fair Market Rate data from {path}")

    # I want to use RegEx to match the terrible column names, so I can't use
    # names and usecols.
    df: pd.DataFrame = pd.read_excel(path)

    # Rename the horrible Excel columns
    names: List[str] = ["zipcode", "fmr_2br", "fmr_2br_90", "fmr_2br_110"]
    usecols = df.columns.str.match(
        r"(SAFMR\n2)|(ZIP)|(zcta)|(SAFMR|safmr\s{0,1}\d+\s2br)"
    )

    # The columns sometimes don't match up because data distributed as
    # Excel files tend to suck.
    logging.debug(f"FMR usecols: {usecols}")
    logging.debug(f"FMR actual cols: {df.columns}")
    df: pd.DataFrame = df.loc[:, usecols]
    df.columns = names

    # Add in year because we're using multiple FMR data sets
    df["fmr_year"] = year

    return df


def load_zip_city(path: Union[str, Path] = ZIP_TRACT) -> pd.DataFrame:
    """Write later."""
    logging.info(f"Loading zip code to census tract data from {path}")

    # Rename zip because it's a keyword and therefore annoying to use.
    # Rename usps-whatever because it's wordy.
    # Also...drop the rest of the columns
    names: List[str] = ["zipcode", "tract", "city", "state"]

    zip_tract: pd.DataFrame = pd.read_excel(path, names=names, usecols=names)
    # Lower cased city will help with merges
    zip_tract.city = zip_tract.city.str.lower()
    return zip_tract


def load_nyc_neighborhoods(path: Union[str, Path] = NYC_BOROUGH) -> pd.DataFrame:
    """Write later"""
    nyc: pd.DataFrame = pd.read_csv(path)
    nyc.rename(columns={"zip": "zipcode"}, inplace=True)
    return nyc


def merge_evic_fmr(
    evictions: pd.DataFrame,
    cities: Optional[Union[list[str], str]] = "New York, NY",
    neighborhoods: Optional[List[pd.DataFrame]] = None,
) -> pd.DataFrame:
    """Write later."""
    logging.info("Merging data sets into the Eviction Labs DataFrame")

    # Sanitize inputs
    # If city is a single string then add it to a list for filtering
    if isinstance(cities, str):
        logging.info("Enabled: filtering on cities")
        cities: list[str] = [cities]

    # Likewise for neighborhoods
    if isinstance(neighborhoods, str):
        logging.info("Enabled: merging neighborhoods into Eviction Labs")
        neighborhoods: list[pd.DataFrame] = [neighborhoods]

    # Filter on cities if requested
    if cities:
        evictions: pd.DataFrame = evictions.loc[evictions.city.isin(cities), :]

    # Temporary, lower cased city names as well as states to ease merging
    city_state: pd.DataFrame = evictions.city.str.extract(r"^(\w+),\s(\w+)$")
    city_state.columns = ["temp_city", "temp_state"]
    evictions: pd.DataFrame = pd.concat([evictions, city_state], axis="columns")

    # Temporary year column to aid merging
    evictions["temp_year"] = evictions.month.dt.year

    # Zip and census tract data. I want zip codes and tracts to be melted so
    # that they're associated with each city, state pair.
    zip_tract = load_zip_city()
    zip_tract = zip_tract.melt(["city", "state"])

    # Filter on cities again if requested
    if cities:
        # City, State is separated into features for zip_tract so I have to
        # replicate the split to filter
        city_temp = [city.split(", ") for city in cities]
        city_zip = [city[0].lower() for city in city_temp]
        state_zip = [city[1] for city in city_temp]
        zip_tract = zip_tract.loc[
            zip_tract.city.isin(city_zip) | zip_tract.state.isin(state_zip)
        ]

    # Fair market data
    fmr_years = [2020, 2021, 2022]
    fmr_paths = [
        DATA_DIR.joinpath(f"fy{year}_safmrs_revised.xlsx") for year in fmr_years
    ]
    fmrs = [load_fmr(fmr_path, year) for fmr_path, year in zip(fmr_paths, fmr_years)]

    # Filter FMRs by zip code if cities were provided
    if cities:
        fmrs = [fmr.loc[fmr.zipcode.isin(zip_tract.zipcode), :] for fmr in fmrs]

    # Merge everything
    evictions = evictions.merge(
        zip_tract,
        left_on=["temp_city", "temp_state"],
        right_on=["city", "state"],
        how="outer",
    )

    # FMRs are merged on zip code and year to produce a long DataFrame where
    # the dates match up
    for fmr in fmrs:
        evictions = evictions.merge(fmr, on=["zipcode", "year"], how="left")
    if neighborhoods:
        for neighborhood in neighborhoods:
            evictions: pd.DataFrame = evictions.merge(
                neighborhood, on="zipcode", how="left"
            )

    # Final DataFrame without temp columns
    evictions.drop(columns=["temp_city", "temp_state", "temp_year"], inplace=True)
    return evictions
