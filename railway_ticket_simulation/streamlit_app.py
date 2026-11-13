"""
streamlit_app.py
Interactive Browser-Accessible Web Application for Railway Ticket-Counter Simulation.
Course: Solving Problems Using Modelling and Simulation (NEC00091)

An extension of the Railway Ticket Simulation project providing a real-time web UI:
- Interactive Reservation Hall (3 Ticket Counters, IDLE/BUSY indicators, FIFO Queue badges).
- Balking & Reneging Exit Lane tracking.
- Play, Pause, Step (+0.5m), Reset, and Surge (+5) controls.
- Real-time digital clock, KPI scoreboard, and Erlang-C Theoretical Benchmark HUD.
- Multi-scenario comparisons (Normal, Peak, Overloaded) and analytical Matplotlib charts.
- CSV data table previews and direct download buttons.
"""

import os
import tempfile
import time
from typing import Dict, Any, List

# Prevent matplotlib permission warnings on Windows
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import SimulationConfig, SIMULATION_SCENARIOS
from counter import TicketCounter, TicketCounterSystem
from passenger import Passenger
from simulation import RailwaySimulation, run_scenario_comparison
from visualize import (
    plot_simulation_dashboard,
    plot_queue_length_over_time,
    plot_wait_time_distribution,
    plot_counter_utilization,
    plot_passenger_outcomes,
    plot_scenario_comparison,
)

# =============================================================================
# STREAMLIT PAGE CONFIGURATION & STYLING
# =============================================================================

st.set_page_config(
    page_title="Railway Ticket-Counter Simulation | M/M/c",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern dark-mode aesthetic matching the desktop Tkinter application
st.markdown("""
<style>
    /* Global Container Adjustments */
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }
    
    /* Station Canvas Cards */
    .station-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #334155;
    }
    
    /* Counter Booth Cards */
    .booth-box {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .booth-busy {
        border-top: 4px solid #ef4444;
    }
    .booth-idle {
        border-top: 4px solid #10b981;
    }
    
    /* Passenger Queue Pills */
    .p-pill {
        display: inline-block;
        padding: 4px 10px;
        margin: 3px;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.82rem;
        font-family: monospace;
    }
    .p-green {
        background-color: #065f46;
        color: #a7f3d0;
        border: 1px solid #10b981;
    }
    .p-amber {
        background-color: #78350f;
        color: #fde68a;
        border: 1px solid #f59e0b;
    }
    .p-red {
        background-color: #7f1d1d;
        color: #fecaca;
        border: 1px solid #ef4444;
    }

    /* KPI Highlights */
    .kpi-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        color: #f8fafc;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .kpi-sub {
        color: #38bdf8;
        font-size: 0.82rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_simulation(scenario_name: str = "Normal", custom_params: dict = None):
    """Initialize or reset the simulation engine with specified parameters."""
    if custom_params:
        cfg = SimulationConfig(
            scenario_name="Custom",
            **custom_params
        )
    else:
        preset = SIMULATION_SCENARIOS.get(scenario_name, SIMULATION_SCENARIOS["Normal"])
        cfg = SimulationConfig(
            num_counters=preset["counters"],
            arrival_rate=preset["lambda"],
            service_rate=preset["mu"],
            sim_time=480.0,
            scenario_name=scenario_name,
        )

    st.session_state.config = cfg
    st.session_state.sim = RailwaySimulation(cfg)
    st.session_state.sim.prepare()
    st.session_state.is_running = False
    st.session_state.sim_finished = False
    st.session_state.last_step_time = 0.0


if "sim" not in st.session_state:
    init_simulation("Normal")

if "speed" not in st.session_state:
    st.session_state.speed = 2.0


# =============================================================================
# SIDEBAR CONTROLS
# =============================================================================

st.sidebar.title("🚆 Railway Queue Control")
st.sidebar.caption("Course: NEC00091 — Discrete-Event Queuing Model")

# 1. Scenario Selector
st.sidebar.markdown("### 🔀 Simulation Scenario")
scenario_option = st.sidebar.radio(
    "Select Operating Scenario:",
    options=["Normal (λ=0.60)", "Peak (λ=0.80)", "Overloaded (λ=1.00)", "Custom Configuration"],
    index=0 if st.session_state.config.scenario_name == "Normal" else
          (1 if st.session_state.config.scenario_name == "Peak" else
          (2 if st.session_state.config.scenario_name == "Overloaded" else 3))
)

selected_scenario_name = (
    "Normal" if "Normal" in scenario_option else
    ("Peak" if "Peak" in scenario_option else
    ("Overloaded" if "Overloaded" in scenario_option else "Custom"))
)

# Detect scenario switch and reset if changed
if selected_scenario_name != "Custom" and selected_scenario_name != st.session_state.config.scenario_name:
    init_simulation(selected_scenario_name)
    st.rerun()

# 2. Custom Parameters (if Custom is selected)
custom_args = {}
if selected_scenario_name == "Custom":
    with st.sidebar.expander("⚙️ Fine-Tune Parameters", expanded=True):
        c_val = st.slider("Counters (c)", min_value=1, max_value=6, value=3)
        lam_val = st.slider("Arrival Rate (λ passengers/min)", min_value=0.10, max_value=2.00, value=0.60, step=0.05)
        mu_val = st.slider("Service Rate (μ passengers/min/counter)", min_value=0.10, max_value=1.00, value=0.30, step=0.05)
        sim_time_val = st.slider("Shift Duration (minutes)", min_value=60.0, max_value=960.0, value=480.0, step=60.0)
        
        balk_enable = st.checkbox("Enable Balking", value=True)
        balk_thresh = st.number_input("Balking Onset Threshold", min_value=1, max_value=20, value=5)
        balk_max = st.number_input("Balking Max Cap", min_value=balk_thresh + 1, max_value=30, value=15)
        
        renege_enable = st.checkbox("Enable Reneging", value=True)
        renege_mean = st.number_input("Mean Patience (minutes)", min_value=1.0, max_value=30.0, value=10.0, step=1.0)
        
        custom_args = {
            "num_counters": c_val,
            "arrival_rate": lam_val,
            "service_rate": mu_val,
            "sim_time": sim_time_val,
            "enable_balking": balk_enable,
            "balking_threshold": balk_thresh,
            "balking_max_queue": balk_max,
            "enable_reneging": renege_enable,
            "renege_time_mean": renege_mean,
        }
        if st.button("Apply Custom Parameters & Reset"):
            init_simulation("Custom", custom_args)
            st.rerun()

st.sidebar.markdown("---")

# 3. Interactive Execution Controls
st.sidebar.markdown("### ⏯️ Execution Controls")

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.session_state.is_running:
        if st.button("⏸️ Pause", use_container_width=True):
            st.session_state.is_running = False
            st.rerun()
    else:
        if st.button("▶️ Play", use_container_width=True):
            if st.session_state.sim.env.now >= st.session_state.config.sim_time:
                init_simulation(st.session_state.config.scenario_name)
            st.session_state.is_running = True
            st.rerun()

with col_btn2:
    if st.button("⏭️ Step (+0.5m)", use_container_width=True):
        st.session_state.is_running = False
        st.session_state.sim.step_until(st.session_state.sim.env.now + 0.5)
        st.rerun()

col_btn3, col_btn4 = st.sidebar.columns(2)
with col_btn3:
    if st.button("🔄 Reset", use_container_width=True):
        init_simulation(st.session_state.config.scenario_name)
        st.rerun()

with col_btn4:
    if st.button("⚡ Surge (+5)", use_container_width=True):
        for _ in range(5):
            st.session_state.sim.inject_passenger()
        st.toast("⚡ 5 rush-hour passengers injected into the station entrance!")
        st.rerun()

# 4. Instant Complete Shift Button
if st.sidebar.button("⚡ Complete 8h Shift Instantly", use_container_width=True):
    st.session_state.is_running = False
    with st.spinner("Simulating complete shift and post-processing logs..."):
        st.session_state.sim.run()
        st.session_state.sim_finished = True
    st.rerun()

# 5. Speed Slider
st.sidebar.markdown("### ⏩ Animation Speed")
st.session_state.speed = st.sidebar.select_slider(
    "Speed Multiplier",
    options=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
    value=st.session_state.speed,
    format_func=lambda x: f"{x}x"
)


# =============================================================================
# HELPER RENDERING FUNCTIONS
# =============================================================================

def get_live_metrics(sim: RailwaySimulation):
    """Extract instantaneous and cumulative KPIs from the simulation engine."""
    now = sim.env.now
    total_arrivals = len(sim.passengers)
    served = sum(1 for p in sim.passengers if p.status == "SERVED")
    balked = sum(1 for p in sim.passengers if p.status == "BALKED")
    reneged = sum(1 for p in sim.passengers if p.status == "RENEGED")
    in_queue = sum(1 for p in sim.passengers if p.status == "IN_QUEUE")
    in_service = sum(1 for p in sim.passengers if p.status == "IN_SERVICE")
    abandoned = balked + reneged

    served_waits = [p.wait_time for p in sim.passengers if p.status == "SERVED"]
    avg_wait = np.mean(served_waits) if served_waits else 0.0

    served_pct = (served / total_arrivals * 100) if total_arrivals > 0 else 0.0
    abandoned_pct = (abandoned / total_arrivals * 100) if total_arrivals > 0 else 0.0

    util_info = sim.ticket_system.get_utilization_summary(now if now > 0 else 1.0)
    emp_util = util_info["overall_utilization"] * 100

    q_series = [sample["queue_length"] for sample in sim.queue_time_series]
    peak_q = max(q_series) if q_series else in_queue

    return {
        "now": now,
        "total_arrivals": total_arrivals,
        "served": served,
        "balked": balked,
        "reneged": reneged,
        "in_queue": in_queue,
        "in_service": in_service,
        "abandoned": abandoned,
        "served_pct": served_pct,
        "abandoned_pct": abandoned_pct,
        "avg_wait": avg_wait,
        "emp_util": emp_util,
        "peak_q": peak_q,
        "util_info": util_info,
    }


def render_station_hall(sim: RailwaySimulation, metrics: dict):
    """Render the 3 ticket counter booths and animated queue chips."""
    cfg = sim.config
    now = metrics["now"]

    # Header Row: Clock & Theoretical Status Badge
    theo = cfg.calculate_theoretical_mmc()
    rho_pct = cfg.traffic_intensity * 100

    col_h1, col_h2 = st.columns([1, 2])
    with col_h1:
        st.markdown(
            f"### 🕒 Sim Time: `{now:.1f} min` <span style='font-size:0.9rem; color:#94a3b8;'>/ {cfg.sim_time:.0f} min</span>",
            unsafe_allow_html=True
        )
    with col_h2:
        if theo["is_stable"]:
            st.info(
                f"**Erlang-C Status:** ✅ **STABLE** (Traffic Intensity $\\rho = {rho_pct:.1f}\\%$ < 100%) | "
                f"Theoretical $W_q = {theo['expected_wait_time_Wq']:.2f}\\text{{ min}}$ | "
                f"$P_Q = {theo['prob_waiting_erlang_c']*100:.1f}\\%$"
            )
        else:
            st.warning(
                f"**Erlang-C Status:** ⚠️ **UNSTABLE** (Traffic Intensity $\\rho = {rho_pct:.1f}\\%$ ≥ 100%) | "
                f"Queue bounded below $\\infty$ by passenger balking & reneging."
            )

    # 1. Ticket Counters (Booths 1 to 3)
    st.markdown("##### 🏢 Ticket Counter Facility")
    c_cols = st.columns(cfg.num_counters)
    
    for i, counter in enumerate(sim.ticket_system.counters):
        with c_cols[i]:
            status_cls = "booth-busy" if counter.is_busy else "booth-idle"
            status_text = f"🔴 BUSY — Serving P{counter.current_passenger_id}" if counter.is_busy else "🟢 IDLE — Available"
            status_color = "#ef4444" if counter.is_busy else "#10b981"
            
            # Counter Utilization %
            cnt_busy = counter.total_busy_time
            if counter.is_busy and counter.service_start_timestamp is not None:
                cnt_busy += (now - counter.service_start_timestamp)
            u_pct = (cnt_busy / now * 100.0) if now > 0 else 0.0

            st.markdown(f"""
            <div class="booth-box {status_cls}">
                <div style="font-size: 1.1rem; font-weight: 700; color: #f8fafc;">
                    🧑‍💼 Counter #{counter.counter_id}
                </div>
                <div style="font-size: 0.85rem; font-weight: 600; color: {status_color}; margin: 6px 0;">
                    {status_text}
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">
                    Served: <b>{counter.customers_served}</b> | Utilization: <b>{u_pct:.1f}%</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(1.0, max(0.0, u_pct / 100.0)))

    # 2. Central Waiting Queue Display
    waiting_passengers = [p for p in sim.passengers if p.status == "IN_QUEUE"]
    # Active System Roster (Shows serving and waiting passenger numbers)
    st.markdown("##### 📋 Live System Passenger Roster")
    serving_info = []
    for c in sim.ticket_system.counters:
        if c.is_busy and c.current_passenger_id:
            serving_info.append(f"**Counter {c.counter_id}:** `P{c.current_passenger_id}` (Serving)")
        else:
            serving_info.append(f"**Counter {c.counter_id}:** `IDLE`")

    waiting_pids = [f"#{idx+1}: `P{p.passenger_id}` ({(now - (p.queue_enter_time or now)):.1f}m)" for idx, p in enumerate(waiting_passengers)]
    waiting_str = ", ".join(waiting_pids) if waiting_pids else "*No passengers waiting in queue*"

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown(f"**🏢 In Service:** {' | '.join(serving_info)}")
    with col_r2:
        st.markdown(f"**👥 In Queue:** {waiting_str}")
    q_len = len(waiting_passengers)

    st.markdown(
        f"##### 👥 Central Waiting Line ({q_len} waiting) &nbsp; "
        f"<span style='font-size:0.8rem; color:#f59e0b;'>⚠️ Balk Threshold: 5+</span> &nbsp; "
        f"<span style='font-size:0.8rem; color:#ef4444;'>⛔ Capacity Limit: 15</span>",
        unsafe_allow_html=True
    )

    if q_len == 0:
        st.markdown(
            "<div style='background-color:#1e293b; padding:12px; border-radius:8px; border:1px dashed #334155; color:#94a3b8; text-align:center;'>"
            "✨ Queue is currently empty. Arriving passengers obtain immediate counter service."
            "</div>",
            unsafe_allow_html=True
        )
    else:
        pills_html = []
        for p in waiting_passengers:
            wait_so_far = now - (p.queue_enter_time or now)
            # Urgency color class
            if wait_so_far < 3.0:
                cls = "p-green"
            elif wait_so_far < 7.0:
                cls = "p-amber"
            else:
                cls = "p-red"
            pills_html.append(f"<span class='p-pill {cls}'>P{p.passenger_id} ({wait_so_far:.1f}m)</span>")

        st.markdown(
            f"<div style='background-color:#1e293b; padding:12px; border-radius:8px; border:1px solid #334155;'>"
            f"{''.join(pills_html)}"
            f"</div>",
            unsafe_allow_html=True
        )

    # 3. Departures & Exit Lane
    st.markdown(
        f"<div style='margin-top:10px; font-size:0.85rem; color:#94a3b8;'>"
        f"🚪 <b>Exit Activity:</b> "
        f"<span style='color:#10b981;'>✔️ Served: {metrics['served']} ({metrics['served_pct']:.1f}%)</span> &nbsp;|&nbsp; "
        f"<span style='color:#f59e0b;'>⚠️ Balked (Turned Away): {metrics['balked']}</span> &nbsp;|&nbsp; "
        f"<span style='color:#ef4444;'>⛔ Reneged (Queue Abandoned): {metrics['reneged']}</span> &nbsp;|&nbsp; "
        f"Total Abandoned: <b>{metrics['abandoned']} ({metrics['abandoned_pct']:.1f}%)</b>"
        f"</div>",
        unsafe_allow_html=True
    )


def render_kpi_scoreboard(sim: RailwaySimulation, metrics: dict):
    """Render scoreboard with real-time key metrics and accounting check."""
    cfg = sim.config
    theo = cfg.calculate_theoretical_mmc()

    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(
            label="Total Passenger Arrivals",
            value=f"{metrics['total_arrivals']}",
            delta=f"{metrics['served']} served ({metrics['served_pct']:.1f}%)"
        )
    with kpi2:
        st.metric(
            label="Current Queue / Peak",
            value=f"{metrics['in_queue']}",
            delta=f"Peak: {metrics['peak_q']} in line",
            delta_color="inverse"
        )
    with kpi3:
        theo_wq_str = f"{theo['expected_wait_time_Wq']:.2f}m" if theo['is_stable'] else "UNSTABLE"
        st.metric(
            label="Avg Wait (Served)",
            value=f"{metrics['avg_wait']:.2f} min",
            delta=f"Theo Wq: {theo_wq_str}"
        )
    with kpi4:
        st.metric(
            label="Facility Utilization",
            value=f"{metrics['emp_util']:.1f}%",
            delta=f"Theo ρ: {cfg.traffic_intensity*100:.1f}%"
        )

    # Passenger Accounting Identity Check Banner
    total = metrics["total_arrivals"]
    acct_sum = (
        metrics["served"] + metrics["balked"] + metrics["reneged"] +
        metrics["in_queue"] + metrics["in_service"]
    )
    discrepancy = total - acct_sum
    is_valid = (discrepancy == 0)

    status_tag = "VERIFIED [OK]" if is_valid else f"FAILED [Discrepancy: {discrepancy}]"
    badge_color = "#10b981" if is_valid else "#ef4444"

    st.markdown(
        f"<div style='background-color:#0f172a; padding:10px 14px; border-radius:8px; border:1px solid #334155; margin-top:12px; font-size:0.85rem;'>"
        f"⚖️ <b>Passenger Conservation Law:</b> "
        f"<code>Total ({total}) = Served ({metrics['served']}) + Balked ({metrics['balked']}) + "
        f"Reneged ({metrics['reneged']}) + In Queue ({metrics['in_queue']}) + In Service ({metrics['in_service']})</code> &nbsp; "
        f"<span style='background-color:{badge_color}; color:#ffffff; padding:2px 8px; border-radius:4px; font-weight:700;'>{status_tag}</span>"
        f"</div>",
        unsafe_allow_html=True
    )


# =============================================================================
# MAIN LAYOUT RENDERING
# =============================================================================

st.title("🚆 Railway Ticket-Counter Queuing Simulation")
st.caption(
    "Discrete-Event M/M/c Queuing System with Passenger Balking & Reneging | "
    "Course Code: NEC00091 — Solving Problems Using Modelling and Simulation"
)

# Placeholder container for real-time live updates
live_container = st.empty()

# Calculate initial or current metrics
sim = st.session_state.sim
metrics = get_live_metrics(sim)

# Render Live Station and Scoreboard inside live_container
with live_container.container():
    render_station_hall(sim, metrics)
    render_kpi_scoreboard(sim, metrics)

# =============================================================================
# ANALYTICAL CHARTS & DATA TABS
# =============================================================================

st.markdown("---")
st.subheader("📊 Analytical Visualizations & Experiment Logs")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Composite Dashboard",
    "🕒 Queue Dynamics",
    "⏱️ Wait Time Distribution",
    "🏢 Counter Utilization",
    "🔀 Scenario Comparison Matrix",
    "📋 Raw CSV Logs & Export",
])

# Ensure DataFrames exist for rendering
if sim.passengers_df is None or sim.passengers_df.empty:
    sim._build_dataframes()

with tab1:
    st.markdown("#### Comprehensive 4-Panel Simulation Dashboard")
    try:
        fig_dash = plot_simulation_dashboard(sim)
        st.pyplot(fig_dash)
        plt.close(fig_dash)
    except Exception as e:
        st.info("Run or advance the simulation to generate the integrated dashboard.")

with tab2:
    st.markdown("#### Queue Length Over Time & Event Incidents")
    try:
        fig_q = plot_queue_length_over_time(sim)
        st.pyplot(fig_q)
        plt.close(fig_q)
    except Exception as e:
        st.info("Run or advance the simulation to plot queue dynamics.")

with tab3:
    st.markdown("#### Passenger Wait Time Distribution vs. Theoretical Erlang-C Wq")
    try:
        fig_w = plot_wait_time_distribution(sim)
        st.pyplot(fig_w)
        plt.close(fig_w)
    except Exception as e:
        st.info("No passengers served yet to compute wait time distribution.")

with tab4:
    st.markdown("#### Counter Utilization & Throughput Balancing")
    try:
        fig_u = plot_counter_utilization(sim)
        st.pyplot(fig_u)
        plt.close(fig_u)
    except Exception as e:
        st.info("Advance simulation to record counter busy times.")

with tab5:
    st.markdown("#### 3-Scenario Comparative Matrix (Normal vs. Peak vs. Overloaded)")
    st.write(
        "Executes all 3 academic course scenarios sequentially under identical service capacity "
        "($c=3, \\mu=0.30$) and plots comparative KPIs."
    )
    if st.button("🚀 Run Scenario Comparison Now"):
        with st.spinner("Executing comparative simulation matrix..."):
            comp_results = run_scenario_comparison(sim_time=480.0, random_seed=sim.config.random_seed)
            
            # Comparison Matrix Table
            rows = []
            for name, data in comp_results.items():
                s = data["stats"]
                cfg_i = data["config"]
                t_wq = s["theoretical_mmc"].get("expected_wait_time_Wq")
                t_wq_str = f"{t_wq:.2f} min" if t_wq is not None else "UNSTABLE"
                abn_pct = s["passenger_counts"].get("percent_abandoned", 0.0)
                rows.append({
                    "Scenario": name,
                    "Arrival Rate (λ)": f"{cfg_i.arrival_rate:.2f}/min",
                    "Theoretical ρ": f"{s['utilization']['theoretical_traffic_intensity_rho']*100:.1f}%",
                    "Sim Utilization": f"{s['utilization']['empirical_overall_utilization']*100:.1f}%",
                    "Avg Wait (Served)": f"{s['timing_metrics']['avg_wait_time_served']:.2f} min",
                    "Theo Erlang-C Wq": t_wq_str,
                    "Served Customers": s["passenger_counts"]["num_served"],
                    "Abandoned (Balk+Renege)": f"{s['passenger_counts']['num_abandoned']} ({abn_pct:.1f}%)",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            
            fig_comp = plot_scenario_comparison(comp_results)
            st.pyplot(fig_comp)
            plt.close(fig_comp)

with tab6:
    st.markdown("#### Exportable Simulation Datasets (Pandas DataFrames)")
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("**Passenger Event Logs (`passenger_logs.csv`)**")
        if sim.passengers_df is not None and not sim.passengers_df.empty:
            st.dataframe(sim.passengers_df.head(100), height=280, use_container_width=True)
            csv_p = sim.passengers_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Passenger Logs (CSV)",
                data=csv_p,
                file_name="passenger_logs.csv",
                mime="text/csv",
            )
        else:
            st.info("No passenger records logged yet.")

    with col_t2:
        st.markdown("**Queue Time Series (`queue_time_series.csv`)**")
        if sim.queue_df is not None and not sim.queue_df.empty:
            st.dataframe(sim.queue_df.head(100), height=280, use_container_width=True)
            csv_q = sim.queue_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Queue Time Series (CSV)",
                data=csv_q,
                file_name="queue_time_series.csv",
                mime="text/csv",
            )
        else:
            st.info("No queue samples logged yet.")

    st.markdown("**Event Stream (`events_log.csv`)**")
    if sim.events_df is not None and not sim.events_df.empty:
        st.dataframe(sim.events_df.tail(100), height=240, use_container_width=True)
        csv_e = sim.events_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Events Log (CSV)",
            data=csv_e,
            file_name="events_log.csv",
            mime="text/csv",
        )


# =============================================================================
# CONTINUOUS ANIMATION LOOP (PLAY MODE)
# =============================================================================

if st.session_state.is_running and sim.env.now < sim.config.sim_time:
    # Advance discrete step
    sim.step_until(sim.env.now + 0.5)
    
    # Calculate delay based on speed multiplier
    # Base: 1 real second = 1 sim minute at 1x
    delay = 0.5 / (st.session_state.speed * 2.0)
    time.sleep(delay)
    
    # Check if shift completed
    if sim.env.now >= sim.config.sim_time:
        st.session_state.is_running = False
        st.session_state.sim_finished = True
        st.toast("🏁 8-Hour Simulation Shift Complete!")
    
    st.rerun()
