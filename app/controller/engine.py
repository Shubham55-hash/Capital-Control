import numpy as np
from app.optimizer import optimize
from app.risk.metrics import risk_metrics, dcvar_limit
from app.stress import stress_test
from config.settings import settings

def _emergency(old, meta, scenarios, limit):
    w=np.asarray(old,float).copy(); cash=int(meta.index[meta.sector.eq('Cash')][0]); risky=np.where(~meta.sector.eq('Cash'))[0]
    for _ in range(12):
        if risk_metrics(w,scenarios)['dcvar'] <= limit: break
        cut=np.minimum(w[risky], settings.emergency_cash_step*w[risky]/max(w[risky].sum(),1e-8)); w[risky]-=cut; w[cash]+=cut.sum()
    return w

def run_control_loop(mu, historical, scenarios, old, meta, regime, scenario_name='Historical'):
    limit=dcvar_limit(regime); before=risk_metrics(old,scenarios)
    candidate=optimize(mu,scenarios,old,meta,limit)
    used_emergency=False
    if candidate['status'] == 'optimal': proposed=np.array(list(candidate['weights'].values())); validation=stress_test(proposed,scenarios,limit)
    else: validation={'vulnerable':True}; proposed=_emergency(old,meta,scenarios,limit); used_emergency=True
    if validation['vulnerable']:
        tight=limit*.8; retry=optimize(mu,scenarios,old,meta,tight,strict=True)
        if retry['status']=='optimal' and not stress_test(np.array(list(retry['weights'].values())),scenarios,limit)['vulnerable']: candidate=retry; proposed=np.array(list(retry['weights'].values()))
        else: proposed=_emergency(old,meta,scenarios,limit); used_emergency=True
    after=risk_metrics(proposed,scenarios); validation=stress_test(proposed,scenarios,limit)
    utilization=after['dcvar']/limit if limit else 0
    status='RED' if validation['vulnerable'] else ('AMBER' if utilization>=.8 else 'GREEN')
    turnover=float(np.abs(proposed-np.asarray(old)).sum()); cost=float((meta.cost.values*np.abs(proposed-np.asarray(old))).sum())
    improvement=before['dcvar']-after['dcvar']; net=improvement-cost-.001*turnover
    action='DE-RISK' if used_emergency else ('HOLD' if net<=0 and status=='GREEN' else 'REBALANCE')
    if action=='HOLD':
        proposed=np.asarray(old)
        after=before
    # Keep the dashboard's returned portfolio metrics aligned with the final
    # accepted allocation, including independently calculated stress measures.
    validation=stress_test(proposed,scenarios,limit)
    after.update(validation)
    changes=dict(zip(meta.asset, proposed-np.asarray(old)))
    reasons=[f'Regime is {regime}; active DCVaR limit is {limit:.2%}', f'DCVaR utilization is {utilization:.0%}']
    if used_emergency: reasons.append('Independent stress validation failed; deterministic defensive allocation applied')
    return {'status':status,'action_name':action,'regime':regime,'base_limit':settings.base_dcvar_limit,'multiplier':settings.risk_multipliers[regime],'active_limit':limit,'current_metrics':before,'recommended_metrics':after,'risk_headroom':limit-after['dcvar'],'utilization':utilization,'weights':dict(zip(meta.asset,proposed)),'trigger':['Stress vulnerability' if validation['vulnerable'] else 'Risk budget review'],'reasons':reasons,'action':changes,'impact':{'dcvar_before':before['dcvar'],'dcvar_after':after['dcvar'],'turnover':turnover,'transaction_cost':cost,'net_benefit':net},'emergency_used':used_emergency,'scenario':scenario_name}
