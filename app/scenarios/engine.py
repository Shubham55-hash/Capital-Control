import numpy as np
import pandas as pd

SCENARIOS = {
 "Historical": {}, "Equity Crash": {"Equity": -.10}, "Rate Shock": {"Bonds": -.045},
 "Liquidity Freeze": {"Equity": -.055, "Alternatives": -.07}, "Correlation Spike": {"all": -.035},
 "Sector Crash": {"Equity": -.075}, "Custom": {}
}
def make_scenarios(returns: pd.DataFrame, n=400, seed=10):
    rng = np.random.default_rng(seed)
    return returns.iloc[rng.choice(len(returns), min(n, len(returns)), replace=True)].values
def apply_scenario(scenarios, metadata: pd.DataFrame, name, custom_shock=0.0):
    result = np.array(scenarios, dtype=float, copy=True)
    shocks = dict(SCENARIOS.get(name, {}))
    if name == "Custom": shocks['all'] = custom_shock
    for sector, shock in shocks.items():
        if sector == 'all': result += shock
        else: result[:, metadata.sector.eq(sector).values] += shock
    return result
