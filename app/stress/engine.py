import numpy as np
from app.risk.metrics import risk_metrics

def stress_test(weights, scenarios, limit):
    m=risk_metrics(weights, scenarios)
    concentration=float(np.max(weights))
    # Direct scenarios calculate independently from optimizer feasibility.
    worst=float(np.min(np.asarray(scenarios) @ np.asarray(weights)))
    m.update({'worst_scenario_loss': -worst, 'concentration': concentration, 'vulnerable': m['dcvar'] > limit or -worst > limit*1.5})
    return m
