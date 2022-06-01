import pandas as pd
from etl_evict import EVICTION_FULL, load_eviction

if __name__ == "__main__":
    eviction: pd.DataFrame = load_eviction(EVICTION_FULL)

    print(eviction.head())
