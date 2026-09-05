import numpy as np
import pandas as pd
from config.settings import settings

def regime_features(returns: pd.DataFrame):
    market = returns.iloc[:, :2].mean(axis=1)
    vol20 = market.tail(20).std() * np.sqrt(252)
    vol60 = market.tail(60).std() * np.sqrt(252)
    wealth = (1 + market).cumprod()
    drawdown = 1 - wealth.iloc[-1] / wealth.cummax().iloc[-1]
    avg_corr = returns.tail(60).corr().values[np.triu_indices(returns.shape[1], 1)].mean()
    return {"vol20": float(vol20), "vol60": float(vol60), "drawdown": float(drawdown), "average_correlation": float(avg_corr), "liquidity_proxy": .88}

def classify_regime(returns: pd.DataFrame):
    f = regime_features(returns)
    ratio = f['vol20'] / max(f['vol60'], 1e-9)
    if ratio > settings.crisis_vol20_ratio and f['drawdown'] > settings.crisis_drawdown:
        return "CRISIS", f
    if ratio > settings.normal_vol20_ratio or f['drawdown'] > settings.stress_drawdown:
        return "STRESS", f
    return "NORMAL", f
