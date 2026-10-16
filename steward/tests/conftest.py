import numpy as np
import pandas as pd
import pytest

from steward.config import load_rules
from steward.data import CASH


def make_prices(paths: dict[str, np.ndarray], start="2010-01-01") -> pd.DataFrame:
    n = len(next(iter(paths.values())))
    idx = pd.bdate_range(start, periods=n)
    df = pd.DataFrame(paths, index=idx)
    df[CASH] = 1.0
    return df


@pytest.fixture
def rules():
    return load_rules()
