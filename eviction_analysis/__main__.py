import pandas as pd
import etl_evict

if __name__ == "__main__":
    print("Loading data sets to merge")
    eviction: pd.DataFrame = etl_evict.load_eviction()
    neighborhoods: pd.DataFrame = etl_evict.load_nyc_neighborhoods()

    print("Running merge routine")
    eviction: pd.DataFrame = etl_evict.merge_evic_fmr(
        eviction, neighborhoods=neighborhoods
    )

    print("Saving DataFrame as a Parquet file")
    eviction.to_parquet(
        etl_evict.DATA_DIR.parent.joinpath("evict_merged.parquet"), engine="pyarrow"
    )
