# ADCC — Adaptive DCVaR Capital Control

> **We don't wait for risk to breach. We adapt the risk budget before it does.**

ADCC is a closed-loop capital-control system that dynamically adjusts risk tolerance, optimizes allocation under a hard DCVaR constraint, stress-tests proposed portfolios, and decides whether to hold, rebalance, or de-risk.

## Problem and solution

A static optimizer may remain “feasible” precisely when market conditions have invalidated its risk assumptions. ADCC runs a continuous **Predict → Budget → Optimize → Stress → Control → Verify** loop. It adapts the DCVaR budget by regime, independently validates the candidate under stress, and can reject the optimizer’s proposal.

## Architecture

```text
CSV/sample data → features/covariance → regime → adaptive budget → scenarios
 → constrained optimization → independent stress engine → safety controller
 → HOLD / REBALANCE / DE-RISK → verified portfolio → next cycle
```

The repository separates `data`, `features`, `regime`, `scenarios`, `risk`, `optimizer`, `stress`, `controller`, `api`, and `dashboard` modules.

## Mathematical formulation

Scenario wealth is `Wj(w) = W0(1 + wᵀRj)`. ADCC uses expected shortfall as the operational, normalized discrete-time DCVaR risk measure. The optimizer maximizes expected return less trading cost and turnover penalty subject to:

- hard adaptive DCVaR limit `DCVaR(w) ≤ Kt`;
- fully invested, long-only weights;
- per-position and sector limits;
- turnover and transaction-cost controls.

`Kt = K0 × R(regime)`: NORMAL = 100%, STRESS = 70%, CRISIS = 40%. With a 5% base budget, the active limits are 5.0%, 3.5%, and 2.0%.

The supplied DCVaR research is the theoretical foundation for explicit DCVaR-constrained optimization. ADCC’s adaptive budget, stress gate, no-trade rule, and closed-loop controls are practical engineering extensions, not claimed as results from that paper.

## Safety controller

GREEN is below 80% utilization; AMBER is 80–100%; RED is over limit or independently stress-vulnerable. A RED result receives a tighter retry; if that fails, deterministic emergency de-risking moves capital to cash and re-verifies. Unsafe allocations are never silently accepted. Before a routine trade, net benefit subtracts transaction cost and turnover penalty; a non-positive result becomes HOLD.

## Scenario engine and dashboard

Historical bootstrap scenarios plus Equity Crash, Rate Shock, Liquidity Freeze, Correlation Spike, Sector Crash, and Custom shocks are supported. Selecting one creates a stressed distribution and re-runs control, rather than merely displaying a loss.

The Streamlit dashboard contains Executive Risk, Allocation, Risk & Control, Decision Center, and Scenario Lab pages. It exposes the regime, budget multiplier, active limit, utilization, headroom, allocation deltas, triggers, reasons, impact, and stress response.

## API

`GET /health`, `/portfolio`, `/risk`, `/regime`, `/decisions`  
`POST /optimize`, `/scenario`, `/stress-test`, `/rebalance`

POST bodies accept `{ "mode": "normal|stress|crisis", "scenario": "Equity Crash", "custom_shock": -0.10 }`.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app/dashboard/dashboard.py
uvicorn app.api.main:app --reload
pytest -q
```

Or run `docker compose up --build`. The dashboard runs on port 8501 and API docs are at `http://localhost:8000/docs`.

## Deterministic demo walkthrough

1. Choose **normal** and Historical: green budget review / HOLD is available.
2. Choose **stress**: recent volatility and drawdown tighten the budget.
3. Select **Equity Crash**: the engine applies a -10% equity shock.
4. The independent stress engine reviews the candidate.
5. The controller retries under tighter limits or creates a defensive allocation (equity down, bonds/cash up).
6. Inspect Decision Center for trigger → reason → action → impact, and Scenario Lab for before/response metrics.

## Testing

The test suite covers CVaR ordering, adaptive budgets, scenario/control end-to-end behavior, position caps, normalized weights, and transaction cost. Add market-data adapters or a database without coupling them to the financial-control modules.

## Limitations and future work

Synthetic returns make the demo deterministic; scenarios are simulations, not forecasts. The discrete operational risk statistic should be validated with an institution’s exact DCVaR convention, data, liquidity model, and governance process. Future work includes CSV upload persistence, calibrated factor scenarios, PostgreSQL storage, solver selection, and backtesting against Equal Weight, Minimum Variance, Mean-Variance, and HRP benchmarks. ADCC does not claim universal outperformance or return guarantees.

# Capital-Control
