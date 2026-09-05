from fastapi import FastAPI
from app.models import OptimizeRequest
from app.data import sample_market, assets, default_weights
from app.features import estimate_returns
from app.regime import classify_regime
from app.scenarios import make_scenarios, apply_scenario, SCENARIOS
from app.controller import run_control_loop
from app.risk import risk_metrics, dcvar_limit

app=FastAPI(title='ADCC API', version='1.0')
def state(mode='normal', scenario='Historical', custom_shock=0):
    _,returns=sample_market(mode=mode); weights=default_weights(); regime,features=classify_regime(returns)
    hist=make_scenarios(returns); stressed=apply_scenario(hist,assets,scenario,custom_shock)
    decision=run_control_loop(estimate_returns(returns),hist,stressed,weights.values,assets,regime,scenario)
    return weights, regime, features, decision
@app.get('/health')
def health(): return {'status':'ok','service':'ADCC'}
@app.get('/portfolio')
def portfolio():
    w,_,_,d=state(); return {'current_weights':w.to_dict(),'recommended_weights':d['weights'],'capital':1_000_000}
@app.get('/risk')
def risk():
    w,r,_,_=state(); return {**risk_metrics(w.values,make_scenarios(sample_market()[1])),'regime':r,'limit':dcvar_limit(r)}
@app.get('/regime')
def regime():
    _,r,f,_=state(); return {'regime':r,'features':f,'multiplier':{'NORMAL':1,'STRESS':.7,'CRISIS':.4}[r]}
@app.get('/decisions')
def decisions(): return state()[3]
@app.post('/optimize')
def optimize(request:OptimizeRequest): return state(request.mode,request.scenario,request.custom_shock)[3]
@app.post('/scenario')
def scenario(request:OptimizeRequest): return state(request.mode,request.scenario,request.custom_shock)[3]
@app.post('/stress-test')
def stress_test(request:OptimizeRequest): return state(request.mode,request.scenario,request.custom_shock)[3]['recommended_metrics']
@app.post('/rebalance')
def rebalance(request:OptimizeRequest): return state(request.mode,request.scenario,request.custom_shock)[3]
