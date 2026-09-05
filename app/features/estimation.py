import numpy as np
import pandas as pd

def estimate_returns(returns: pd.DataFrame) -> pd.Series:
    """Conservative blend of 20-day momentum and 60-day mean."""
    return .6 * returns.tail(20).mean() + .4 * returns.tail(60).mean()

def shrunk_covariance(returns: pd.DataFrame, rho=.25) -> np.ndarray:
    raw = returns.tail(120).cov().values
    target = np.diag(np.diag(raw))
    return (1-rho) * raw + rho * target
