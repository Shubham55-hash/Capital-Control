import numpy as np
import pandas as pd

assets = pd.DataFrame({
    "asset": ["US Equity", "Global Equity", "Treasury Bonds", "Gold", "Cash"],
    "sector": ["Equity", "Equity", "Bonds", "Alternatives", "Cash"],
    "max_weight": [.42, .32, .55, .22, .60],
    "liquidity": [.95, .78, .99, .70, 1.0],
    "cost": [.0015, .0020, .0008, .0025, .0001],
})

def sample_market(days=260, mode="normal", seed=7):
    """Deterministic market history. Stress mode ends with a broad sell-off."""
    rng = np.random.default_rng(seed)
    means = np.array([.00042,.00036,.00015,.00020,.00005])
    vols = np.array([.012,.011,.0045,.008,.0001])
    corr = np.array([[1,.78,-.18,.12,0],[.78,1,-.15,.1,0],[-.18,-.15,1,.05,0],[.12,.1,.05,1,0],[0,0,0,0,1]])
    cov = np.outer(vols, vols) * corr
    ret = rng.multivariate_normal(means, cov, size=days)
    if mode in ("stress", "crisis"):
        n = 25 if mode == "stress" else 40
        shock = np.array([-.010, -.011, -.002, -.004, 0]) if mode == "stress" else np.array([-.018,-.020,-.004,-.007,0])
        ret[-n:] += shock + rng.normal(0, vols * (1.1 if mode == "stress" else 1.9), (n, 5))
    prices = 100 * np.cumprod(1 + ret, axis=0)
    dates = pd.bdate_range(end=pd.Timestamp("2026-09-04"), periods=days)
    return pd.DataFrame(prices, index=dates, columns=assets.asset), pd.DataFrame(ret, index=dates, columns=assets.asset)

def default_weights():
    return pd.Series([.32,.23,.25,.12,.08], index=assets.asset)
