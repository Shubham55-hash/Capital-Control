import numpy as np
import pandas as pd
from scipy.optimize import minimize
from app.risk.metrics import risk_metrics
from config.settings import settings

def optimize(mu, scenarios, old, metadata, limit, strict=False):
    n = len(old); old=np.asarray(old, dtype=float); maxes=metadata.max_weight.values
    def objective(w):
        turnover=np.abs(w-old).sum(); cost=(metadata.cost.values*np.abs(w-old)).sum()
        return -(np.asarray(mu)@w - 2.0*cost - .0005*turnover)
    def dc(w): return limit - risk_metrics(w, scenarios)['dcvar']
    constraints=[{'type':'eq','fun':lambda w:w.sum()-1}, {'type':'ineq','fun':lambda w:settings.max_turnover-np.abs(w-old).sum()}, {'type':'ineq','fun':dc}]
    # sector concentration and liquidity must remain operationally valid
    for sector in metadata.sector.unique():
        idx=metadata.sector.eq(sector).values
        if sector != 'Cash': constraints.append({'type':'ineq','fun':lambda w, idx=idx: settings.sector_limit-w[idx].sum()})
    result=minimize(objective, old, method='SLSQP', bounds=[(0,float(x)) for x in maxes], constraints=constraints, options={'maxiter':500,'ftol':1e-10})
    if not result.success or dc(result.x) < -1e-6:
        return {'status':'infeasible','reason':'No allocation satisfies hard DCVaR, position, sector and turnover constraints'}
    w=result.x; metrics=risk_metrics(w, scenarios); turnover=float(np.abs(w-old).sum()); cost=float((metadata.cost.values*np.abs(w-old)).sum())
    return {'status':'optimal','weights':dict(zip(metadata.asset,w)), **metrics,'turnover':turnover,'transaction_cost':cost}
