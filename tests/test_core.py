from app.data import sample_market, assets, default_weights
from app.features import estimate_returns
from app.regime import classify_regime
from app.scenarios import make_scenarios, apply_scenario
from app.risk import risk_metrics, dcvar_limit
from app.controller import run_control_loop

def test_cvar_exceeds_var():
    _,r=sample_market(); m=risk_metrics(default_weights().values,make_scenarios(r)); assert m['cvar'] >= m['var'] >= 0
def test_adaptive_budget():
    assert dcvar_limit('NORMAL') == .05 and dcvar_limit('CRISIS') == .02
def test_regime_and_e2e_shock():
    _,r=sample_market(mode='crisis'); regime,_=classify_regime(r)
    hist=make_scenarios(r); stressed=apply_scenario(hist,assets,'Equity Crash')
    d=run_control_loop(estimate_returns(r),hist,stressed,default_weights().values,assets,regime,'Equity Crash')
    assert d['active_limit'] <= .05 and abs(sum(d['weights'].values())-1)<1e-5
def test_position_limits_and_cost():
    _,r=sample_market(); d=run_control_loop(estimate_returns(r),make_scenarios(r),make_scenarios(r),default_weights().values,assets,'NORMAL')
    assert all(d['weights'][a] <= float(mx)+1e-6 for a,mx in zip(assets.asset,assets.max_weight)); assert d['impact']['transaction_cost'] >= 0
