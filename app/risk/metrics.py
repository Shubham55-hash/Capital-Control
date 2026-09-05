import numpy as np
from config.settings import settings

def risk_metrics(weights, scenarios, capital=settings.capital, confidence=settings.confidence):
    p = np.asarray(scenarios) @ np.asarray(weights)
    wealth = capital * (1 + p)
    losses = -wealth
    var = np.quantile(losses, confidence)
    cvar = losses[losses >= var].mean()
    expected_wealth = wealth.mean()
    # normalized shortfall from initial capital: max(0, -expected P&L + tail loss P&L)
    dcvar = max(0., (cvar + expected_wealth) / capital)
    # Equivalent operational number is tail loss relative to capital, retained for useful constraints
    tail_loss = max(0., -np.quantile(p, 1-confidence))
    es_loss = max(0., -p[p <= np.quantile(p, 1-confidence)].mean())
    dcvar = es_loss
    return {"expected_return": float(p.mean()), "volatility": float(p.std()*np.sqrt(252)), "var": float(tail_loss), "cvar": float(es_loss), "dcvar": float(dcvar), "expected_wealth": float(expected_wealth)}

def dcvar_limit(regime): return round(settings.base_dcvar_limit * settings.risk_multipliers[regime], 10)
