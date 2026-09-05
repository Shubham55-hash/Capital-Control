"""Plain-English, decision-first interface for ADCC."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
import pandas as pd
import plotly.express as px
import streamlit as st
from config.settings import settings
from app.controller import run_control_loop
from app.data import assets, default_weights, sample_market
from app.features import estimate_returns
from app.regime import classify_regime
from app.scenarios import SCENARIOS, apply_scenario, make_scenarios
from app.stress import stress_test

st.set_page_config(page_title="ADCC | Portfolio safety", page_icon=":material/shield:", layout="wide")

@st.cache_data(show_spinner=False)
def load_market(mode): return sample_market(mode=mode)

def plain_status(status, action, use):
    if status == "RED": return "Risk needs attention", "The scenario check found too much potential downside. The suggested response aims to make the mix safer.", "red"
    if status == "AMBER": return "Risk is getting close to the comfort zone", f"The portfolio is using {use:.0%} of its safety budget. The suggested adjustment creates more room.", "orange"
    if action == "HOLD": return "Everything looks steady", "No changes are recommended right now.", "green"
    return "A small improvement is available", "The portfolio is inside its safety budget. A measured rebalance may improve its mix.", "green"

def change_word(value): return "Add" if value > .0005 else "Reduce" if value < -.0005 else "Keep"

def inr(value):
    """Compact Indian currency formatting for the demo interface."""
    value = abs(float(value))
    if value >= 10_000_000:
        return f"₹{value / 10_000_000:.2f} crore"
    if value >= 100_000:
        return f"₹{value / 100_000:.2f} lakh"
    if value >= 1_000:
        return f"₹{value / 1_000:.1f} thousand"
    return f"₹{value:,.0f}"

with st.sidebar:
    st.title("ADCC")
    st.caption("Your portfolio safety guide")
    st.subheader(":material/tune: Try a market situation")
    mode_label = st.segmented_control("Market health", ["Calm", "Unsettled", "Severe downturn"], default="Calm", help="Changes the simulated recent market history.", width="stretch")
    mode = {"Calm":"normal", "Unsettled":"stress", "Severe downturn":"crisis"}[mode_label]
    scenario = st.selectbox("What if this happens?", list(SCENARIOS), help="Tests the portfolio against a simulated event and suggests a response.")
    custom = st.slider("Custom market drop", -.25, 0.0, -.10, .005, format="%.1f%%") if scenario == "Custom" else 0.0
    with st.expander(":material/help: How to use this demo"):
        st.write("1. Pick a market setting.\n2. Pick an event.\n3. Read the answer at the top, then explore the details.")
    st.caption("Demo data only. This tool supports a decision; it does not predict markets or provide investment advice.")

prices, returns = load_market(mode)
current = default_weights()
regime, features = classify_regime(returns)
historical = make_scenarios(returns)
stressed = apply_scenario(historical, assets, scenario, custom)
decision = run_control_loop(estimate_returns(returns), historical, stressed, current.values, assets, regime, scenario)
current_stress = stress_test(current.values, stressed, decision["active_limit"])
metrics = decision["recommended_metrics"]
headline, summary, tone = plain_status(decision["status"], decision["action_name"], decision["utilization"])
status_icon = {"green": ":material/check_circle:", "orange": ":material/warning:", "red": ":material/error:"}[tone]

st.title(":material/shield: Portfolio safety, made simple")
st.caption("See how much downside risk you have, why it matters, and what the system recommends next.")
with st.container(border=True):
    st.subheader(f"{status_icon} {headline}")
    st.write(summary)
    st.badge(f"Recommended: {decision['action_name'].replace('-', ' ').title()}", color=tone)
    st.badge(f"Safety budget used: {decision['utilization']:.0%}", color=tone)
    st.caption(f"Market setting: {mode_label} | Event being tested: {scenario}")

view = st.segmented_control("Choose a view", ["Quick answer", "Suggested changes", "Safety check", "Why this?", "What if?"], default="Quick answer", label_visibility="collapsed", width="stretch")

if view == "Quick answer":
    st.header(":material/visibility: The quick answer")
    st.write("These are the three things to look at first. You do not need to understand financial jargon to use this page.")
    with st.container(horizontal=True):
        st.metric("What to do", decision["action_name"].replace("-", " ").title(), border=True)
        st.metric("Safety room left", f"{max(0,decision['risk_headroom']):.2%}", "More room is safer", border=True)
        st.metric("Potential loss in a bad day", f"{metrics['dcvar']:.2%}", f"Target: below {decision['active_limit']:.2%}", border=True)
        st.metric("Portfolio value", inr(settings.capital), "Demo starting amount", border=True)
    left, right = st.columns([1.45,1])
    with left, st.container(border=True):
        st.subheader("What changed in the market?")
        market = prices.iloc[:,:2].mean(axis=1); indexed = market / market.iloc[0] * 100
        st.line_chart(indexed, x_label="Date", y_label="Market level (started at 100)", height=280)
        st.caption("A simple market health indicator, not a price forecast.")
    with right, st.container(border=True):
        st.subheader("Your safety meter")
        st.progress(min(decision["utilization"],1.0), text=f"{decision['utilization']:.0%} of the current safety budget is used")
        st.write(f"The safety budget is **{decision['active_limit']:.2%}** for the current market setting.")
        (st.success if decision["utilization"] < .8 else st.warning)("There is a comfortable buffer." if decision["utilization"] < .8 else "The buffer is small, so the system is watching closely.")

elif view == "Suggested changes":
    st.header(":material/swap_horiz: Suggested changes")
    st.write("This compares today’s mix with a mix that better fits the selected market situation.")
    frame = pd.DataFrame({"Investment":assets.asset,"Today":current.values,"Suggested":list(decision["weights"].values()),"Maximum allowed":assets.max_weight})
    frame["Change"] = frame["Suggested"]-frame["Today"]; frame["What to do"] = frame["Change"].map(change_word)
    frame["Amount moving"] = frame["Change"].abs() * settings.capital
    left,right = st.columns([1.4,1])
    with left, st.container(border=True):
        fig=px.bar(frame,x="Investment",y=["Today","Suggested"],barmode="group",title="Today compared with the suggested mix"); fig.update_layout(template="plotly_white",yaxis_tickformat=".0%",height=380,legend_title_text="")
        st.plotly_chart(fig,width="stretch")
    with right, st.container(border=True):
        st.subheader("In plain English")
        for _, row in frame.loc[frame["What to do"]!="Keep"].iterrows(): st.write(f"- **{row['What to do']} {row['Investment']}** by {abs(row['Change']):.1%}")
        st.metric("Estimated trading cost", inr(decision['impact']['transaction_cost'] * settings.capital), border=True)
        st.caption(f"About {decision['impact']['turnover']:.1%} of the portfolio would change hands.")
    st.dataframe(frame, column_config={"Today":st.column_config.NumberColumn(format="percent"),"Suggested":st.column_config.NumberColumn(format="percent"),"Maximum allowed":st.column_config.NumberColumn(format="percent"),"Change":st.column_config.NumberColumn(format="%+.1f%%"),"Amount moving":st.column_config.NumberColumn(format="₹%.0f")},hide_index=True,width="stretch")

elif view == "Safety check":
    st.header(":material/fact_check: How we checked the portfolio")
    st.write("We independently test the current portfolio and the suggested one. Lower loss figures are better.")
    check=pd.DataFrame({"Check":["Typical bad-day loss","Average loss in the worst days","Potential loss in this event","Largest single investment"],"Before":[decision["current_metrics"]["var"],decision["current_metrics"]["cvar"],current_stress["worst_scenario_loss"],max(current.values)],"After":[metrics["var"],metrics["cvar"],metrics["worst_scenario_loss"],metrics["concentration"]]})
    with st.container(border=True): st.dataframe(check.style.format({"Before":"{:.2%}","After":"{:.2%}"}),hide_index=True,width="stretch")
    with st.expander(":material/menu_book: What do these words mean?"):
        st.write("**Typical bad-day loss:** a high, but not extreme, daily loss in the simulation.\n\n**Average loss in the worst days:** the average of the toughest simulated days.\n\n**Potential loss in this event:** the main safety measure that summarises the scenario’s downside.\n\n**Largest single investment:** how concentrated your portfolio is in one place.")
    with st.container(horizontal=True):
        st.metric("Recent market movement",f"{features['vol20']:.1%}","Higher means choppier",border=True)
        st.metric("Recent fall from high",f"{features['drawdown']:.1%}","Higher means more pressure",border=True)
        st.metric("Investments moving together",f"{features['average_correlation']:.2f}","Higher means less diversification",border=True)

elif view == "Why this?":
    st.header(":material/lightbulb: Why this recommendation?")
    st.write("The system never gives a suggestion without showing its reasoning.")
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("What we noticed")
        for item in decision["trigger"]:
            st.write(f":material/visibility: {item}")
        st.subheader("Why it matters")
        st.write(f":material/speed: The portfolio is using **{decision['utilization']:.0%}** of its safety budget.")
        st.write(f":material/account_balance: The current market setting is **{mode_label.lower()}**.")
        st.write(f":material/bolt: The event being tested is **{scenario}**.")
    with right, st.container(border=True):
        st.subheader("What the system suggests")
        st.metric("Recommended action", decision['action_name'].replace('-', ' ').title(), border=True)
        st.write("Use **Suggested changes** to see which investments go up or down and how much money is involved.")
        st.subheader("Expected result")
        st.metric("Potential loss in this event", f"{decision['impact']['dcvar_before']:.2%} to {decision['impact']['dcvar_after']:.2%}", border=True)
    with st.container(border=True):
        st.subheader("Safety outcome: before and after")
        outcome = pd.DataFrame({"Portfolio": ["Current mix", "Suggested mix"], "Potential loss": [decision['impact']['dcvar_before'], decision['impact']['dcvar_after']], "Safety limit": [decision['active_limit'], decision['active_limit']]})
        fig = px.bar(outcome, x="Portfolio", y=["Potential loss", "Safety limit"], barmode="group", title="Lower potential loss means a safer outcome")
        fig.update_layout(template="plotly_white", yaxis_tickformat=".0%", height=300, legend_title_text="")
        st.plotly_chart(fig, width="stretch")
    if decision["emergency_used"]: st.warning("The regular response did not pass the independent safety check, so emergency risk reduction was used.")

else:
    st.header(":material/science: What if this happens?")
    st.write(f"The selected event is **{scenario}**. This compares doing nothing with the suggested response.")
    comparison=pd.DataFrame({"Measure":["Potential loss in this event","Average loss in worst days","Expected daily return","Worst one-day simulated loss"],"If no action is taken":[current_stress["dcvar"],current_stress["cvar"],current_stress["expected_return"],current_stress["worst_scenario_loss"]],"With suggested response":[metrics["dcvar"],metrics["cvar"],metrics["expected_return"],metrics["worst_scenario_loss"]]})
    with st.container(border=True): st.dataframe(comparison.style.format({"If no action is taken":"{:.2%}","With suggested response":"{:.2%}"}),hide_index=True,width="stretch")
    st.info(":material/info: A scenario is a controlled ‘what if’, not a prediction of what will happen.")
