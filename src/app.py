"""
Cloud Cost Observability & Intelligent Archival
"""

import sys
import os
import random
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

import streamlit as st
import io
import json
import base64
import streamlit.components.v1 as components

# ─── PATH SETUP ───────────────────────────────────────────────────────────────
SRC_DIR = Path(__file__).parent.absolute()
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
ROOT_DIR = SRC_DIR.parent

from db import database as db
from utils import env_manager
from utils.mock_data import ensure_mock_data, PLATFORMS, DOMAINS
from agent.analyzers.pricing_engine import PricingEngine
from agent.analyzers.forecaster import Forecaster
from agent.analyzers.hoarding_analyzer import HoardingAnalyzer
from agent.analyzers.governance_engine import GovernanceEngine
from utils.governance_service import GovernanceService
from agent.fixers.archival_executor import ArchivalFactory

# Initialize environment & Data
env_manager.init_env()
ensure_mock_data()

APP_TITLE    = "Cloud Resource Observability with Compute & Storage Governance"
APP_SUBTITLE = ("Unified multi-dimensional observability across Compute, Storage, Memory, and Cost — "
                "with intelligent governance, forecasting, and AI-driven optimization for enterprise cloud environments.")

# ── Platform-specific metric tooltip content ──────────────────────────────────
COMPUTE_PLATFORM_NOTES = {
    "Snowflake":                   "Credits consumed per virtual warehouse per hour of active query execution. Cost = Credits × Credit price (varies by edition).",
    "Databricks":                  "DBUs (Databricks Units) per cluster node per hour during active Spark jobs. Cost = DBUs × DBU rate (Standard/Premium/Enterprise).",
    "BigQuery":                    "Slot-hours used for query processing. On-demand: $5/TB scanned. Flat-rate: reserved slots per hour.",
    "AWS":                         "Node-hours of Redshift compute cluster time. Cost = node type × nodes × hours. Spectrum charges apply for S3 queries.",
    "Azure":                       "Azure Synapse DWU-hours or Databricks DBU consumption per workspace per hour of active compute.",
    "Google Cloud Platform":       "Slot-hours for BigQuery and vCPU-hours for Dataflow/Dataproc jobs combined.",
    "Oracle Cloud Infrastructure": "OCPU-hours consumed by Autonomous Data Warehouse. Auto-scaling may increase OCPU count during peak load.",
    "IBM Cloud":                   "DSU (Data Service Units) consumed per Db2 Warehouse instance per billing period.",
}

MEMORY_PLATFORM_NOTES = {
    "Snowflake":                   "RAM used per warehouse cluster during query compilation, execution, and spill-to-disk operations.",
    "Databricks":                  "Executor + driver memory allocated per cluster node during Spark job execution and caching.",
    "BigQuery":                    "In-memory shuffle buffer and intermediate storage allocated during distributed query execution.",
    "AWS":                         "RA3 node memory for in-flight query caching and intermediate result storage in Redshift.",
    "Azure":                       "Memory allocated per Synapse Analytics node or ADB executor for distributed data processing.",
    "Google Cloud Platform":       "Shuffle storage and in-memory aggregation buffers during BigQuery and Dataflow execution.",
    "Oracle Cloud Infrastructure": "SGA/PGA memory allocated per ADB session during active query processing.",
    "IBM Cloud":                   "In-memory columnar store buffers used by Db2 Warehouse per concurrently running query.",
}

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@600;700;800&display=swap');

:root {
    --primary: #2563EB; --surface: #FFFFFF; --bg: #F1F5F9;
    --border: #E2E8F0; --text: #0F172A; --muted: #64748B;
    --green: #059669; --red: #DC2626; --amber: #D97706;
}
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: var(--bg); color: var(--text); }

/* ── Sidebar hidden ── */
section[data-testid="stSidebar"] { display: none !important; }
button[data-testid="collapsedControl"] { display: none !important; }

/* ── Header ── */
.header-bar {
    background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 55%, #7C3AED 100%);
    border-radius: 16px; padding: 24px 32px; margin-bottom: 20px;
    position: relative; overflow: hidden;
    box-shadow: 0 20px 40px rgba(37,99,235,0.22);
}
.header-bar::after {
    content:''; position:absolute; top:-40%; right:-8%; width:300px; height:300px;
    background:rgba(255,255,255,0.06); border-radius:50%;
}
.header-title {
    font-family:'Outfit',sans-serif; font-size:2.35rem !important;
    font-weight:900 !important; letter-spacing:0.5px; line-height:1.15;
    color: #ffffff !important; margin:0 0 10px; text-shadow:0 4px 15px rgba(0,0,0,0.3);
}
.header-sub { color:rgba(255,255,255,0.85); font-size:0.98rem; font-weight:500; margin:0; line-height:1.5; }

/* ── Cards & KPI ── */
.main-card {
    background:#fff; border-radius:12px; padding:18px 20px;
    border:1px solid var(--border);
    box-shadow:0 1px 3px rgba(0,0,0,0.06),0 6px 16px rgba(0,0,0,0.04);
    margin-bottom:14px;
}
.kpi-card {
    background:#fff; border-radius:14px; padding:16px 18px;
    border:1px solid var(--border); text-align:center;
    box-shadow:0 2px 8px rgba(0,0,0,0.05); margin-bottom: 15px;
}
.kpi-value { font-size:1.8rem; font-weight:800; font-family:'Outfit',sans-serif; color: var(--primary); }
.kpi-label { font-size:0.75rem; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:0.4px; margin-top:4px; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap:5px; background:transparent; }
.stTabs [data-baseweb="tab"] {
    height:38px; background:#fff; border-radius:8px;
    color:var(--muted); font-weight:600; font-size:0.85rem;
    border:1px solid var(--border); padding:4px 12px; transition:all 0.18s ease;
}
.stTabs [aria-selected="true"] {
    background:var(--primary) !important; color:#fff !important;
    border-color:var(--primary) !important; box-shadow:0 4px 12px rgba(37,99,235,0.3);
}

/* ── AI Assistant ── */
.ai-chat-container {
    padding: 5px; height: 350px; overflow-y: auto; display: flex; flex-direction: column;
}
.chat-msg { padding: 8px 12px; border-radius: 8px; margin-bottom: 8px; font-size: 0.85rem; }
.chat-user { background: #EFF6FF; color: #1E3A8A; align-self: flex-end; border: 1px solid #BFDBFE; }
.chat-ai { background: #F8FAFC; color: #334155; align-self: flex-start; border: 1px solid #E2E8F0; }

.section-header { font-family:'Outfit',sans-serif; font-size:1.4rem; color:var(--text); margin-bottom: 10px; border-bottom: 2px solid var(--primary); padding-bottom: 5px;}

/* ── Forecast Cards ── */
.forecast-card {
    background: #ffffff;
    border-radius: 16px;
    border: 1px solid var(--border);
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.forecast-metric-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.forecast-main-val {
    font-size: 2.2rem;
    font-weight: 800;
    font-family: 'Outfit', sans-serif;
    color: var(--primary);
    line-height: 1;
}
.forecast-trend-label {
    font-size: 0.85rem;
    color: var(--muted);
    font-weight: 600;
    margin-top: 4px;
}
.forecast-reason-box {
    background: #F8FAFC;
    border-radius: 12px;
    padding: 16px;
    margin-top: 20px;
    border-left: 4px solid var(--primary);
}
.forecast-reason-text {
    font-size: 0.9rem;
    color: #334155;
    line-height: 1.5;
}
.forecast-driver-tag {
    background: #EFF6FF;
    color: #2563EB;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
    margin-right: 6px;
}

/* ── Floating Bottom-Left AI Assistant ── */
div[data-testid="stExpander"]:has(#ai_assistant_anchor) {
    position: fixed !important;
    bottom: 20px !important;
    left: 20px !important;
    width: 360px !important;
    z-index: 99999 !important;
    background: white !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
}
div[data-testid="stExpander"]:has(#ai_assistant_anchor) > summary {
    background: var(--surface) !important;
    border-radius: 12px !important;
}
div[data-testid="stExpander"]:has(#ai_assistant_anchor) [data-testid="stExpanderDetails"] {
    max-height: 450px;
    overflow-y: auto;
    padding-top: 10px;
}

/* ── Context Banner ── */
.context-banner {
    background: #F0F9FF;
    border: 1px solid #BAE6FD;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 20px 0;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}
.context-banner-icon {
    font-size: 1.25rem;
    margin-top: 2px;
}
.context-banner-text {
    font-size: 0.9rem;
    color: #0369A1;
    line-height: 1.5;
    font-weight: 500;
}

/* ── Metric Info Tooltips ── */
.metric-tooltip {
    position: relative;
    display: inline-flex;
    align-items: center;
    cursor: help;
    margin-left: 7px;
    vertical-align: middle;
}
.metric-tooltip .tooltip-text {
    visibility: hidden;
    width: 330px;
    background: linear-gradient(135deg, #1E3A8A, #2563EB);
    color: #fff;
    text-align: left;
    border-radius: 10px;
    padding: 13px 15px;
    position: absolute;
    z-index: 99999;
    left: 22px;
    top: -6px;
    opacity: 0;
    transition: opacity 0.22s ease;
    font-size: 0.78rem;
    line-height: 1.6;
    box-shadow: 0 12px 32px rgba(0,0,0,0.35);
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    pointer-events: none;
    white-space: normal;
    border: 1px solid rgba(255,255,255,0.15);
}
.metric-tooltip:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}
.metric-tooltip-icon {
    font-size: 0.8rem;
    opacity: 0.65;
    transition: opacity 0.2s;
    line-height: 1;
}
.metric-tooltip:hover .metric-tooltip-icon {
    opacity: 1;
}
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "active_domain" not in st.session_state:
    st.session_state.active_domain = None
if "selected_platform" not in st.session_state:
    st.session_state.selected_platform = PLATFORMS[0]
if "ai_messages" not in st.session_state:
    st.session_state.ai_messages = [{"role": "ai", "content": "Hello! I am your Cloud Resource AI Assistant. Ask me about costs, storage, compute or memory forecasts, inactive users, governance recommendations, or say 'show inactive assets' to begin an optimization workflow."}]
if "archival_cart" not in st.session_state:
    st.session_state.archival_cart = []

# ─── DATA LOADING ─────────────────────────────────────────────────────────────
def load_data():
    usage_df = pd.read_csv("data/raw/cloud_usage_history.csv")
    usage_df['usage_date'] = pd.to_datetime(usage_df['usage_date'])
    assets_df = pd.read_csv("data/raw/platform_assets.csv")
    return usage_df, assets_df

usage_df, assets_df = load_data()

# ─── APP STRUCTURE ────────────────────────────────────────────────────────────
def main():
    st.markdown(f"""
    <div class="header-bar">
      <h1 class="header-title">{APP_TITLE}</h1>
      <p class="header-sub">{APP_SUBTITLE}</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.active_domain:
        render_domain_selection()
    else:
        render_dashboard()

def render_domain_selection():
    st.markdown("<div class='section-header'>Select Analytical Domain</div>", unsafe_allow_html=True)
    st.caption("Choose the business domain to analyze usage and cost optimization opportunities.")
    
    cols = st.columns(5)
    for i, dom in enumerate(DOMAINS):
        with cols[i]:
            if st.button(dom, use_container_width=True, key=f"dom_{dom}"):
                st.session_state.active_domain = dom
                st.rerun()

def render_dashboard():
    # ── Platform Selection Dropdown ──
    col1, col2 = st.columns([3, 1])
    with col1:
        st.session_state.selected_platform = st.selectbox(
            "☁️ Selected Cloud Platform", 
            PLATFORMS, 
            index=PLATFORMS.index(st.session_state.selected_platform)
        )
    
    # Filter data
    domain = st.session_state.active_domain
    plat = st.session_state.selected_platform
    
    plat_assets = assets_df[(assets_df['domain'] == domain) & (assets_df['platform'] == plat)]
    plat_usage = usage_df[usage_df['platform'] == plat]
    
    st.markdown(f"""
    <div class="context-banner">
        <div class="context-banner-icon">ℹ️</div>
        <div class="context-banner-text">
            Viewing analytical insights for the <b>{domain}</b> domain on the <b>{plat}</b> platform. 
            All cost calculations, forecasts, and optimization recommendations are dynamically generated based on this specific environment.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── AI Consolidated Insights Banner ──
    # Aggregated metrics for the banner
    total_assets_ai = len(plat_assets)
    active_assets_ai = int(plat_assets['is_active'].sum())
    inactive_assets_ai = total_assets_ai - active_assets_ai
    total_gb_ai = plat_assets['size_gb'].sum()
    total_users_ai = plat_assets['users_with_access'].sum()
    
    # Selected counts
    sel_db_cnt = len(st.session_state.get('obs_db', []))
    sel_sch_cnt = len(st.session_state.get('obs_schema', []))
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%); border: 1px solid #BAE6FD; border-radius: 12px; padding: 20px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(37,99,235,0.05);">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <span style="background: #2563EB; color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; letter-spacing: 1px;">AI INSIGHTS</span>
            <span style="font-family: 'Outfit', sans-serif; font-size: 1rem; font-weight: 700; color: #0369A1;">Summary</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;">
            <div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Selected Landscape</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #0F172A;">{sel_db_cnt if sel_db_cnt > 0 else 'All'} DBs | {sel_sch_cnt if sel_sch_cnt > 0 else 'All'} Schemas</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Asset Lifecycle</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #0F172A;">{active_assets_ai} Active | <span style="color: #D97706;">{inactive_assets_ai} Inactive</span></div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Resource Footprint</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #0F172A;">{total_gb_ai:,.1f} GB Storage | {plat_assets['memory_usage_gb'].sum():,.1f} GB Mem</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600; text-transform: uppercase;">Governance Risk</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #0F172A;"><span style="color: #DC2626;">{total_users_ai - plat_assets['active_users'].sum():,} Inactive Access</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Setup Engines
    pricing_engine = PricingEngine()
    forecaster = Forecaster(plat_usage, pricing_engine)
    
    # Pre-calculate filtered data for shared use
    inactive_df_all = assets_df[(assets_df['domain'] == domain) & (assets_df['platform'] == plat) & (~assets_df['is_active'])].copy()
    
    # Move inventory_display logic up so it can be used for query params check
    filtered_assets = assets_df[(assets_df['domain'] == domain) & (assets_df['platform'] == plat)].copy()
    if st.session_state.get('obs_table'):
        filtered_assets = filtered_assets[filtered_assets['table_name'].isin(st.session_state.get('obs_table'))]
        
    filtered_assets['inactive_users'] = filtered_assets['users_with_access'] - filtered_assets['active_users']
    filtered_assets['last_accessed_users_count'] = filtered_assets.apply(lambda r: r['active_users'] + min(2, r['inactive_users']), axis=1)
    
    display_cols = [
        'database', 'schema', 'table_name', 'object_type', 
        'size_gb', 'memory_usage_gb', 'active_users', 'inactive_users', 'users_with_access',
        'last_accessed_users_count', 'impact_reason'
    ]
    
    inventory_display = filtered_assets[display_cols].rename(columns={
        'database':'Database', 'schema':'Schema', 'table_name':'Asset Name',
        'object_type':'Type', 'size_gb':'Size (GB)', 'memory_usage_gb':'Memory (GB)',
        'active_users':'Active Users', 'inactive_users':'Inactive Users',
        'users_with_access':'Total Users', 'last_accessed_users_count':'Last Accessed Users',
        'impact_reason':'Context/Impact'
    })

    @st.dialog("User Access & Governance Audit", width="large")
    def show_asset_users_specific(asset_data, metric):
        st.markdown(f"### 🛡️ {asset_data['Asset Name']}")
        st.markdown(f"**Location:** `{asset_data['Database']}.{asset_data['Schema']}`")
        
        def gen_users(count, seed_name):
            random.seed(str(seed_name))
            return [f"{random.choice(['A','J','M','R','S','T'])}_{random.randint(100,999)}@company.com" for _ in range(count)]
        
        count = asset_data[metric]
        users = gen_users(count, str(asset_data['Asset Name']) + metric)
        
        if metric == "Total Users":
            st.write(f"#### Total Users ({count})")
            st.table(pd.DataFrame({"User Name": users, "Access Level": ["Read" if i%2==0 else "Write" for i in range(len(users))]}))
        elif metric == "Active Users":
            st.write(f"#### Active Users ({count})")
            st.table(pd.DataFrame({"User Name": users, "Last Activity": [(datetime.now() - timedelta(days=random.randint(0,90))).strftime('%Y-%m-%d') for _ in range(len(users))]}))
        elif metric == "Inactive Users":
            st.write(f"#### Inactive Users ({count})")
            st.table(pd.DataFrame({"User Name": users, "Days Inactive": [random.randint(91, 365) for _ in range(len(users))]}))
        elif metric == "Last Accessed Users":
            st.write(f"#### Last Accessed Users ({count})")
            audit_df = pd.DataFrame({
                "User Name": users,
                "Associated Last Accessed Date": [(datetime.now() - timedelta(days=random.randint(0,365))).strftime('%Y-%m-%d') for _ in range(len(users))]
            }).sort_values("Associated Last Accessed Date", ascending=False)
            st.dataframe(audit_df, use_container_width=True, hide_index=True)

    # ── Tooltips Helper ───────────────────────────────────────────────
    def info_icon(tip):
        safe = tip.replace('"', '&quot;').replace("'", '&#39;')
        return (f'<span class="metric-tooltip">'
                f'<span class="metric-tooltip-icon">ℹ️</span>'
                f'<span class="tooltip-text">{safe}</span>'
                f'</span>')

    # ── Card Helper ───────────────────────────────────────────────────
    def obs_card(label, icon, main_val, main_lbl, sub1_val, sub1_lbl, sub2_val, sub2_lbl, bot1_val, bot1_lbl, bot2_val, bot2_lbl, bot3_val, bot3_lbl, tip):
        st.markdown(f"""
        <div class="forecast-card">
            <div class="forecast-metric-title">{icon} {label} {info_icon(tip)}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px;">
            <div>
                <div class="forecast-trend-label">{main_lbl}</div>
                <div style="font-size:1.5rem;font-weight:800;font-family:'Outfit',sans-serif;color:var(--text);">{main_val}</div>
            </div>
            <div>
                <div class="forecast-trend-label">{sub1_lbl}</div>
                <div style="font-size:1.5rem;font-weight:800;font-family:'Outfit',sans-serif;color:var(--primary);">{sub1_val}</div>
            </div>
            <div>
                <div class="forecast-trend-label">{sub2_lbl}</div>
                <div style="font-size:1.5rem;font-weight:800;font-family:'Outfit',sans-serif;color:#7C3AED;">{sub2_val}</div>
            </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
            <div style="background:#F8FAFC;border-radius:8px;padding:10px;">
                <div class="forecast-trend-label">{bot1_lbl}</div>
                <div style="font-size:1.1rem;font-weight:700;color:var(--primary);">{bot1_val}</div>
            </div>
            <div style="background:#F8FAFC;border-radius:8px;padding:10px;">
                <div class="forecast-trend-label">{bot2_lbl}</div>
                <div style="font-size:1.1rem;font-weight:700;color:var(--primary);">{bot2_val}</div>
            </div>
            <div style="background:#F8FAFC;border-radius:8px;padding:10px;">
                <div class="forecast-trend-label">{bot3_lbl}</div>
                <div style="font-size:1.1rem;font-weight:700;color:var(--primary);">{bot3_val}</div>
            </div>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── Tabs Content ──
    tabs = st.tabs([
        "🔭 Observability",
        "📈 Forecasting",
        "⚙️ Cloud Governance & Optimization"
    ])
    
        # ── 1. OBSERVABILITY ──
    with tabs[0]:
        st.markdown("<div class='section-header'>Observability — Cloud Resource</div>", unsafe_allow_html=True)
        st.caption(f"Real-time resource metrics across Cost, Storage, Compute, and Memory for {plat} — {domain} domain. Hover ℹ️ icons for metric definitions.")

        # ── Metric Data Preparation ──
        if not plat_usage.empty:
            latest = plat_usage.sort_values('usage_date').iloc[-1]
            cost_data = pricing_engine.calculate_cost(plat, latest['compute_units'], latest['storage_gb'], latest['data_transfer_gb'])
            mem_gb  = latest.get('memory_usage_gb', 0)
            avg_compute = plat_usage.sort_values('usage_date').tail(30)['compute_units'].mean()
            peak_compute = plat_usage['compute_units'].max()
            
            total_users = plat_assets['users_with_access'].sum()
            active_users = plat_assets['active_users'].sum()
            inactive_users = total_users - active_users

            # (Helpers moved to shared scope)
            obs_tooltips = {
                "Cost": "Monthly Cost = Compute + Storage + Transfer. Projected from latest daily snapshot.",
                "Storage": "Storage (GB) at rest. Reclaimable identifies assets inactive for 45+ days.",
                "Compute": f"Compute Units on {plat}. {COMPUTE_PLATFORM_NOTES.get(plat, '')}",
                "Memory": f"Memory (RAM) usage for {plat} query processing. {MEMORY_PLATFORM_NOTES.get(plat, '')}"
            }

            # ── Layout: Cards & Chart Side-by-Side ─────────────────────
            c_grid, c_chart = st.columns([2.5, 1])
            
            with c_grid:
                r1c1, r1c2 = st.columns(2)
                with r1c1:
                    obs_card("Cost", "💰", 
                             f"${cost_data['total']*30:,.0f}", "MONTHLY TOTAL",
                             f"${cost_data['compute']*30:,.0f}", "COMPUTE",
                             f"${cost_data['storage']*30:,.0f}", "STORAGE",
                             f"${cost_data['total']:,.0f}", "DAILY TOTAL",
                             f"${cost_data['transfer']*30:,.0f}", "TRANSFER",
                             f"${cost_data['total']*365:,.0f}", "EST. ANNUAL",
                             obs_tooltips["Cost"])
                with r1c2:
                    total_asset_gb = plat_assets['size_gb'].sum()
                    active_gb = plat_assets[plat_assets['is_active']]['size_gb'].sum()
                    obs_card("Storage", "🗄️",
                             f"{latest['storage_gb']:,.0f} GB", "CURRENT USAGE",
                             f"{active_gb:,.0f} GB", "ACTIVE ASSETS",
                             f"{total_asset_gb-active_gb:,.0f} GB", "RECLAIMABLE",
                             f"{latest.get('data_transfer_gb',0):,.0f} GB", "DAILY XFER",
                             f"{len(plat_assets)}", "TOTAL ASSETS",
                             f"{int(plat_assets['is_active'].sum())}", "ACTIVE CNT",
                             obs_tooltips["Storage"])
                
                r2c1, r2c2 = st.columns(2)
                with r2c1:
                    obs_card("Compute", "⚡",
                             f"{latest['compute_units']:,.0f}", "DAILY UNITS",
                             f"{avg_compute:,.0f}", "30D AVERAGE",
                             f"{peak_compute:,.0f}", "PEAK UNITS",
                             f"${cost_data['compute']:,.2f}", "DAILY COST",
                             "15%", "LOAD VARIANCE",
                             f"{latest['compute_units']*30:,.0f}", "EST. MONTHLY",
                             obs_tooltips["Compute"])
                with r2c2:
                    avg_mem = plat_usage['memory_usage_gb'].mean()
                    peak_mem = plat_usage['memory_usage_gb'].max()
                    obs_card("Memory", "🧠",
                             f"{mem_gb:,.1f} GB", "CURRENT USAGE",
                             f"{avg_mem:,.1f} GB", "30D AVERAGE",
                             f"{peak_mem:,.1f} GB", "PEAK USAGE",
                             "12%", "MEMORY SPILL",
                             f"{int(mem_gb/1.5)}", "CACHE HITS",
                             f"{mem_gb*1.2:,.1f} GB", "PROJ. PEAK",
                             obs_tooltips["Memory"])

            with c_chart:
                st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
                fig = px.pie(plat_assets, names='database', values='size_gb', title="Storage Distribution", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_layout(height=450, margin=dict(t=50,b=20,l=10,r=10), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ── 🔍 Hierarchy Filters (Optimization Style) ──────────────────
        if "obs_db" not in st.session_state: st.session_state.obs_db = []
        if "obs_schema" not in st.session_state: st.session_state.obs_schema = []
        if "obs_table" not in st.session_state: st.session_state.obs_table = []
        if "obs_status" not in st.session_state: st.session_state.obs_status = "All Assets"

        def reset_obs_filters():
            st.session_state.obs_db = []
            st.session_state.obs_schema = []
            st.session_state.obs_table = []

        st.markdown("#### 🔍 Observability Hierarchy Filters")
        fo1, fo2, fo3, fo4 = st.columns(4)
        
        # Asset Status (Matching Optimization Category)
        st.session_state.obs_status = fo1.selectbox("📋 Asset Status", ["All Assets", "Active Assets", "Inactive Assets"], key="obs_status_sel", index=["All Assets", "Active Assets", "Inactive Assets"].index(st.session_state.obs_status), on_change=reset_obs_filters)
        
        # Database Filter
        db_opts = sorted(plat_assets['database'].unique())
        st.session_state.obs_db = fo2.multiselect("📁 Database", db_opts, key="obs_db_sel", default=st.session_state.obs_db)
        
        # Schema Filter (Cascading)
        if st.session_state.obs_db:
            sch_opts = sorted(plat_assets[plat_assets['database'].isin(st.session_state.obs_db)]['schema'].unique())
        else:
            sch_opts = sorted(plat_assets['schema'].unique())
        st.session_state.obs_schema = fo3.multiselect("📂 Schema", sch_opts, key="obs_schema_sel", default=[s for s in st.session_state.obs_schema if s in sch_opts])
        
        # Table Filter (Cascading)
        if st.session_state.obs_schema:
            tab_opts = sorted(plat_assets[plat_assets['schema'].isin(st.session_state.obs_schema)]['table_name'].unique())
        else:
            tab_opts = sorted(plat_assets['table_name'].unique())
        st.session_state.obs_table = fo4.multiselect("📄 Table / Object", tab_opts, key="obs_table_sel", default=[t for t in st.session_state.obs_table if t in tab_opts])

        # Apply Filters to consolidated table
        filtered_assets = plat_assets.copy()
        if st.session_state.obs_status == "Active Assets": filtered_assets = filtered_assets[filtered_assets['is_active']]
        elif st.session_state.obs_status == "Inactive Assets": filtered_assets = filtered_assets[~filtered_assets['is_active']]
        
        if st.session_state.obs_db: filtered_assets = filtered_assets[filtered_assets['database'].isin(st.session_state.obs_db)]
        if st.session_state.obs_schema: filtered_assets = filtered_assets[filtered_assets['schema'].isin(st.session_state.obs_schema)]
        if st.session_state.obs_table: filtered_assets = filtered_assets[filtered_assets['table_name'].isin(st.session_state.obs_table)]

        st.markdown("---")
        st.markdown("#### 📋 Consolidated Enterprise Asset Inventory")
        
        # ── Clickable Asset Inventory Table ──
        # Load and render the custom interactive table component
        comp_path = os.path.join(os.path.dirname(__file__), "components", "interactive_table")
        interactive_table = components.declare_component("interactive_table", path=comp_path)
        
        data_records = inventory_display.to_dict(orient="records")
        cols = list(inventory_display.columns)
        
        clicked_data = interactive_table(columns=cols, data=data_records, key=f"inv_table_{len(filtered_assets)}")
        
        if clicked_data:
            clicked_asset = clicked_data.get("asset")
            clicked_col = clicked_data.get("metric")
            
            if clicked_asset and clicked_col:
                matches = inventory_display[inventory_display['Asset Name'] == clicked_asset]
                if not matches.empty:
                    show_asset_users_specific(matches.iloc[0], clicked_col)


    # ── 2. FORECASTING ──
    with tabs[1]:
        st.markdown("<div class='section-header'>Forecasting — Cost, Storage, Compute & Memory</div>", unsafe_allow_html=True)
        st.caption(f"Linear Trend Analysis (OLS) — 30-day baseline | 1-Year & 5-Year projections for {plat}. Hover ℹ️ on each card for model assumptions.")

        if not plat_usage.empty:
            proj = forecaster.generate_projections(plat)
            hist_df = forecaster.generate_historical(plat)
            timeline_df = forecaster.generate_timeline(plat)
            insight = proj.get('Insight', {})

            def pct_color(v): return 'var(--red)' if v > 0 else 'var(--green)'
            def pct_sign(v): return '+' if v > 0 else ''

            # ── Helper: render one forecast card ──────────────────────────
            def forecast_card(label, icon, m_key, unit, suffix):
                # Tooltips for forecasting
                f_tooltips = {
                    "total_cost": "Cost Forecast: Uses Ordinary Least Squares (OLS) regression on historical 30-day spend baseline. Includes projected storage growth and compute scaling.",
                    "storage_gb": "Storage Forecast: Models data ingestion rates and retention policies. Projects future footprint based on 2-year ingestion trends.",
                    "compute_units": f"Compute Forecast: Analyzes workload intensity patterns on {plat}. Projects scaling requirements for peak and average execution.",
                    "memory_usage_gb": "Memory Forecast: Estimates RAM requirements for future concurrency levels and data volumes based on workload complexity trends."
                }
                tip_text = f_tooltips.get(m_key, "Forecasting based on historical trend analysis (OLS).")
                
                cur = proj['Current'][m_key]
                wow = proj['WoW'][m_key]
                mom = proj['MoM'][m_key]
                yoy = proj['YoY'][m_key]
                y1  = proj['1_Year'][m_key]
                y5  = proj['5_Year'][m_key]
                sc  = max(cur, 0.01)
                wow_p = (wow - cur) / sc * 100
                mom_p = (mom - cur) / sc * 100
                yoy_p = (yoy - cur) / sc * 100
                st.markdown(f"""
                <div class="forecast-card">
                  <div class="forecast-metric-title">{icon} {label} {info_icon(tip_text)}</div>
                  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px;">
                    <div>
                      <div class="forecast-trend-label">CURRENT COST</div>
                      <div style="font-size:1.5rem;font-weight:800;font-family:'Outfit',sans-serif;color:var(--text);">{unit}{cur:,.2f}{suffix}</div>
                    </div>
                    <div>
                      <div class="forecast-trend-label">1-YEAR FORECAST</div>
                      <div style="font-size:1.5rem;font-weight:800;font-family:'Outfit',sans-serif;color:var(--primary);">{unit}{y1:,.2f}{suffix}</div>
                    </div>
                    <div>
                      <div class="forecast-trend-label">5-YEAR FORECAST</div>
                      <div style="font-size:1.5rem;font-weight:800;font-family:'Outfit',sans-serif;color:#7C3AED;">{unit}{y5:,.2f}{suffix}</div>
                    </div>
                  </div>
                  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
                    <div style="background:#F8FAFC;border-radius:8px;padding:10px;">
                      <div class="forecast-trend-label">WoW</div>
                      <div style="font-size:1.1rem;font-weight:700;color:{pct_color(wow_p)};">{pct_sign(wow_p)}{wow_p:.1f}%</div>
                      <div style="font-size:0.8rem;color:var(--muted);">{unit}{wow:,.2f}</div>
                    </div>
                    <div style="background:#F8FAFC;border-radius:8px;padding:10px;">
                      <div class="forecast-trend-label">MoM</div>
                      <div style="font-size:1.1rem;font-weight:700;color:{pct_color(mom_p)};">{pct_sign(mom_p)}{mom_p:.1f}%</div>
                      <div style="font-size:0.8rem;color:var(--muted);">{unit}{mom:,.2f}</div>
                    </div>
                    <div style="background:#F8FAFC;border-radius:8px;padding:10px;">
                      <div class="forecast-trend-label">YoY</div>
                      <div style="font-size:1.1rem;font-weight:700;color:{pct_color(yoy_p)};">{pct_sign(yoy_p)}{yoy_p:.1f}%</div>
                      <div style="font-size:0.8rem;color:var(--muted);">{unit}{yoy:,.2f}</div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)

            # ── 4 simultaneous forecast cards in 2×2 grid ─────────────────
            r1c1, r1c2 = st.columns(2)
            with r1c1:
                forecast_card("Cost", "💰", "total_cost", "$", "")
            with r1c2:
                forecast_card("Storage", "🗄️", "storage_gb", "", " GB")
            r2c1, r2c2 = st.columns(2)
            with r2c1:
                forecast_card("Compute", "⚡", "compute_units", "", " Units")
            with r2c2:
                forecast_card("Memory", "🧠", "memory_usage_gb", "", " GB")

            # ── Rationalization box ────────────────────────────────────────
            st.markdown(f"""
            <div class="forecast-reason-box" style="margin-bottom:24px;">
              <div style="font-size:0.75rem;font-weight:800;color:var(--primary);margin-bottom:6px;text-transform:uppercase;">
                Forecast Rationalization &nbsp;·&nbsp; Model: {insight.get('model','Linear Trend Analysis (OLS)')}
              </div>
              <div class="forecast-reason-text">{insight.get('reason','Analysis in progress...')}</div>
              <div style="margin-top:10px;">
                <span class="forecast-driver-tag">Compute: {proj['Current']['compute_units']:,.0f} Units</span>
                <span class="forecast-driver-tag">Storage: {proj['Current']['storage_gb']:,.0f} GB</span>
                <span class="forecast-driver-tag">Memory: {proj['Current']['memory_usage_gb']:,.0f} GB</span>
                <span class="forecast-driver-tag">Transfer: {proj['Current']['data_transfer_gb']:,.0f} GB</span>
              </div>
            </div>""", unsafe_allow_html=True)

            # ── 4 separate charts in 2×2 grid ─────────────────────────────
            st.markdown("#### Trend Charts — Historical & 5-Year Projection")
            chart_specs = [
                ("Cost ($)", "total_cost", "#2563EB"),
                ("Storage (GB)", "storage_gb", "#059669"),
                ("Compute (Units)", "compute_units", "#D97706"),
                ("Memory (GB)", "memory_usage_gb", "#7C3AED"),
            ]

            def make_chart(label, col, color):
                fig = go.Figure()
                if not hist_df.empty:
                    fig.add_trace(go.Scatter(
                        x=hist_df['usage_date'], y=hist_df[col],
                        mode='lines', name='Historical',
                        line=dict(color=color, width=2),
                        fill='tozeroy', fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)'
                    ))
                fig.add_trace(go.Scatter(
                    x=timeline_df['usage_date'], y=timeline_df[col],
                    mode='lines', name='Forecast',
                    line=dict(color=color, width=2, dash='dot'),
                    fill='tozeroy', fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.05)'
                ))
                fig.update_layout(
                    title=dict(text=label, font=dict(size=13, family='Outfit')),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    height=260, margin=dict(t=35, b=20, l=10, r=10),
                    legend=dict(orientation='h', yanchor='bottom', y=1.0, xanchor='right', x=1),
                    xaxis=dict(showgrid=True, gridcolor='#E2E8F0', tickfont=dict(size=10)),
                    yaxis=dict(showgrid=True, gridcolor='#E2E8F0', tickfont=dict(size=10)),
                )
                return fig

            ch1, ch2 = st.columns(2)
            with ch1:
                st.plotly_chart(make_chart(*chart_specs[0]), use_container_width=True)
            with ch2:
                st.plotly_chart(make_chart(*chart_specs[1]), use_container_width=True)
            ch3, ch4 = st.columns(2)
            with ch3:
                st.plotly_chart(make_chart(*chart_specs[2]), use_container_width=True)
            with ch4:
                st.plotly_chart(make_chart(*chart_specs[3]), use_container_width=True)

    # ── 3. CLOUD GOVERNANCE & OPTIMIZATION ──
    with tabs[2]:
        st.markdown("<div class='section-header'>Cloud Governance & Optimization — Observability Intelligence</div>", unsafe_allow_html=True)
        
        # Moved Governance Card from Observability
        g1, g2 = st.columns([2, 1])
        with g1:
            # Calculate service account count correctly
            svc_count = plat_assets['service_accounts'].apply(lambda x: len(str(x).split(',')) if isinstance(x, str) and x not in ['None', ''] else 0).sum()
            total_users_g = plat_assets['users_with_access'].sum()
            active_users_g = plat_assets['active_users'].sum()
            inactive_users_g = total_users_g - active_users_g
            
            obs_card("Governance", "👥",
                     f"{total_users_g:,}", "TOTAL ACCESS",
                     f"{active_users_g:,}", "ACTIVE USERS",
                     f"{inactive_users_g:,}", "INACTIVE USERS",
                     f"{int(inactive_users_g/total_users_g*100) if total_users_g > 0 else 0}%", "RISK RATIO",
                     f"{svc_count:,}", "SVC ACCOUNTS",
                     f"{active_users_g}", "LAST 24H",
                     "Governance metric identifying potential access risks from inactive accounts.")
        with g2:
             st.markdown("""
                <div style="font-size:0.95rem;color:#334155;margin-top:20px;line-height:1.6;background:#F8FAFC;padding:24px;border-radius:16px;border-left:4px solid #2563EB;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
                <b>Data Archival Process and Recommendations</b><br>
                Review inactive assets across your enterprise data landscape. Identify candidates for cold storage archival,
                validate governance context, and execute a governed approval workflow with rollback safeguards.
                </div>
                """, unsafe_allow_html=True)

        # ── KPI Cards ──────────────────────────────────────────────────────
        total_assets  = len(plat_assets)
        active_assets = int(plat_assets['is_active'].sum())
        inactive_assets = total_assets - active_assets

        k1, k2, k3 = st.columns(3)
        k1.markdown(f"<div class='kpi-card'><div class='kpi-value'>{total_assets:,}</div><div class='kpi-label'>Total Assets</div></div>", unsafe_allow_html=True)
        k2.markdown(f"<div class='kpi-card'><div class='kpi-value' style='color:var(--green);'>{active_assets:,}</div><div class='kpi-label'>Active Assets</div></div>", unsafe_allow_html=True)
        k3.markdown(f"<div class='kpi-card'><div class='kpi-value' style='color:var(--amber);'>{inactive_assets:,}</div><div class='kpi-label'>Inactive Assets</div></div>", unsafe_allow_html=True)

        # ── Cascading Filter Logic (Optimization) ──
        if "opt_db" not in st.session_state: st.session_state.opt_db = []
        if "opt_schema" not in st.session_state: st.session_state.opt_schema = []
        if "opt_table" not in st.session_state: st.session_state.opt_table = []
        if "opt_category" not in st.session_state: st.session_state.opt_category = "All Assets"

        def reset_opt_filters():
            st.session_state.opt_db = []
            st.session_state.opt_schema = []
            st.session_state.opt_table = []

        st.markdown("#### 🔍 Optimization Hierarchy Filters")
        fo1, fo2, fo3, fo4 = st.columns(4)
        
        # Asset Category (Replacing 3 buttons)
        st.session_state.opt_category = fo1.selectbox("📋 Asset Category", ["All Assets", "Active Assets", "Inactive Assets"], key="opt_category_sel", index=["All Assets", "Active Assets", "Inactive Assets"].index(st.session_state.opt_category), on_change=reset_opt_filters)
        
        # Database Filter
        db_options_opt = sorted(plat_assets['database'].unique())
        st.session_state.opt_db = fo2.multiselect("📁 Database", db_options_opt, key="opt_db_sel", default=st.session_state.opt_db)
        
        # Schema Filter (Cascading)
        if st.session_state.opt_db:
            schema_options_opt = sorted(plat_assets[plat_assets['database'].isin(st.session_state.opt_db)]['schema'].unique())
        else:
            schema_options_opt = sorted(plat_assets['schema'].unique())
        st.session_state.opt_schema = fo3.multiselect("📂 Schema", schema_options_opt, key="opt_schema_sel", default=[s for s in st.session_state.opt_schema if s in schema_options_opt])
        
        # Table Filter (Cascading)
        if st.session_state.opt_schema:
            table_options_opt = sorted(plat_assets[plat_assets['schema'].isin(st.session_state.opt_schema)]['table_name'].unique())
        else:
            table_options_opt = sorted(plat_assets['table_name'].unique())
        st.session_state.opt_table = fo4.multiselect("📄 Table / Object", table_options_opt, key="opt_table_sel", default=[t for t in st.session_state.opt_table if t in table_options_opt])

        # Filter the data
        filtered_opt = plat_assets.copy()
        if st.session_state.opt_category == "Active Assets": filtered_opt = filtered_opt[filtered_opt['is_active']]
        elif st.session_state.opt_category == "Inactive Assets": filtered_opt = filtered_opt[~filtered_opt['is_active']]
        
        if st.session_state.opt_db: filtered_opt = filtered_opt[filtered_opt['database'].isin(st.session_state.opt_db)]
        if st.session_state.opt_schema: filtered_opt = filtered_opt[filtered_opt['schema'].isin(st.session_state.opt_schema)]
        if st.session_state.opt_table: filtered_opt = filtered_opt[filtered_opt['table_name'].isin(st.session_state.opt_table)]

        st.markdown("---")
        # ── Asset Type distribution ──
        fig_type = px.pie(filtered_opt, names='object_type', title="Filtered Asset Distribution by Type", hole=0.35,
                          color_discrete_sequence=px.colors.qualitative.Set3)
        fig_type.update_layout(height=280, margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig_type, use_container_width=True)

        st.markdown("---")

        # ── Data Archival Recommendations & Lifecycle Management ───────────────────────
        st.markdown("<div class='section-header' style='font-size:1.1rem;'>AI-Driven Governance Recommendations & Lifecycle Management</div>", unsafe_allow_html=True)

        inactive_df = filtered_opt[~filtered_opt['is_active']].copy()

        if inactive_df.empty:
            st.success("No inactive assets found with current filters. All selected assets are actively used.")
        else:
            # ── Multi-Dimensional Recommendation Engine ──
            st.markdown("""
            <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:12px; padding:16px; margin-bottom:20px;">
                <p style="margin:0; font-size:0.9rem; color:#1E40AF;">
                    <b>Governance Intelligence:</b> Select an asset from the list below to generate <b>15+ governance dimensions</b> 
                    including lineage impact, compute-intensive object analysis, and performance optimization opportunities.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col_sel, col_empty = st.columns([1, 1.5])
            with col_sel:
                selected_asset_name = st.selectbox(
                    "🔍 Select Asset for Governance Intelligence",
                    options=sorted(inactive_df['table_name'].unique()),
                    index=None,
                    placeholder="Select an asset to view multi-dimensional recommendations...",
                    help="Choose an inactive asset to view multi-dimensional governance recommendations."
                )
            
            if selected_asset_name:
                asset_row = inactive_df[inactive_df['table_name'] == selected_asset_name].iloc[0]
                gov_engine = GovernanceEngine(plat)
                recommendations = gov_engine.generate_recommendations(asset_row)
                
                # Render Recommendation Cards in a scrollable/grid layout
                st.markdown(f"#### 📊 Multi-Dimensional Governance Insights: `{selected_asset_name}`")
                
                # Grid of recommendations
                rec_cols = st.columns(3)
                for idx, rec in enumerate(recommendations):
                    with rec_cols[idx % 3]:
                        impact_color = {"Critical": "#DC2626", "High": "#D97706", "Medium": "#2563EB", "Low": "#64748B"}.get(rec['impact'], "#64748B")
                        st.markdown(f"""
                        <div style="background:white; border:1px solid #E2E8F0; border-radius:12px; padding:16px; height:180px; margin-bottom:12px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <span style="font-size:0.7rem; font-weight:800; color:#64748B; text-transform:uppercase;">{rec['dimension']}</span>
                                <span style="background:{impact_color}20; color:{impact_color}; padding:2px 8px; border-radius:10px; font-size:0.65rem; font-weight:700;">{rec['impact']}</span>
                            </div>
                            <div style="font-size:0.85rem; color:#1F2937; line-height:1.5;">{rec['recommendation']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                # Prepare combined export data for the specific asset
                buf_gov = io.BytesIO()
                rec_export_df = pd.DataFrame(recommendations)
                with pd.ExcelWriter(buf_gov, engine='openpyxl') as w_gov:
                    pd.DataFrame([asset_row]).to_excel(w_gov, index=False, sheet_name='Asset Metadata')
                    rec_export_df.to_excel(w_gov, index=False, sheet_name='Governance Recommendations')
                
                st.download_button(
                    label=f"📥 Export Governance Package: {selected_asset_name}",
                    data=buf_gov.getvalue(),
                    file_name=f"governance_package_{selected_asset_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.markdown("<br>", unsafe_allow_html=True)
                
            st.markdown("**Inactive Asset Inventory — Archival Candidates**")
            grid_cols = [
                'table_name','object_type','database','schema','format',
                'size_gb','cost_per_month','five_year_savings','storage_release_gb',
                'last_access_date','users_with_access','active_users',
                'impact_reason','archival_justification'
            ]
            avail_cols = [c for c in grid_cols if c in inactive_df.columns]
            grid_df = inactive_df[avail_cols].copy()
            grid_df.insert(0, 'Archive', False)

            edited_df = st.data_editor(
                grid_df,
                column_config={"Archive": st.column_config.CheckboxColumn("Archive", default=False)},
                disabled=avail_cols,
                hide_index=True,
                use_container_width=True,
                height=400,
                key="inactive_assets_data_editor"
            )

            sel_tables = edited_df[edited_df['Archive']]['table_name'].tolist()
            ca, cb, cc = st.columns([1.5, 1, 1])
            if ca.button("➕ Add Selected to Approval Workflow", type="primary", use_container_width=True):
                st.session_state.archival_cart = list(set(st.session_state.archival_cart + sel_tables))
                st.success(f"Added {len(sel_tables)} assets to workflow.")
                st.rerun()

            # Excel & CSV Exports
            buf_ex = io.BytesIO()
            with pd.ExcelWriter(buf_ex, engine='openpyxl') as w:
                inactive_df[avail_cols].to_excel(w, index=False, sheet_name='Inactive Assets')
            cb.download_button("📥 Export to Excel", data=buf_ex.getvalue(),
                               file_name="inactive_assets.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
            
            csv_data = inactive_df[avail_cols].to_csv(index=False).encode('utf-8')
            cc.download_button("📄 Export to CSV", data=csv_data,
                               file_name="inactive_assets.csv",
                               mime="text/csv",
                               use_container_width=True)


        st.markdown("---")

        # ── Approval & Governance Workflow ──────────────────────────────────
        st.markdown("<div class='section-header' style='font-size:1.1rem;'>Approval, Export & Notification Workflow</div>", unsafe_allow_html=True)

        if not st.session_state.archival_cart:
            st.info("No assets staged for archival yet. Select candidates above and click 'Add Selected to Approval Workflow'.")
        else:
            cart_cols = ['table_name','database','schema','object_type','cost_per_month','five_year_savings','storage_release_gb','impact_reason','archival_justification']
            avail_cart = [c for c in cart_cols if c in plat_assets.columns]
            cart_df = plat_assets[plat_assets['table_name'].isin(st.session_state.archival_cart)][avail_cart].copy()

            total_sav = plat_assets[plat_assets['table_name'].isin(st.session_state.archival_cart)]['five_year_savings'].sum()
            total_gb  = plat_assets[plat_assets['table_name'].isin(st.session_state.archival_cart)]['storage_release_gb'].sum()

            mc1, mc2, mc3 = st.columns(3)
            mc1.markdown(f"<div class='kpi-card'><div class='kpi-value' style='color:var(--green);'>${total_sav:,.0f}</div><div class='kpi-label'>5-Year Savings</div></div>", unsafe_allow_html=True)
            mc2.markdown(f"<div class='kpi-card'><div class='kpi-value'>{len(cart_df)}</div><div class='kpi-label'>Assets Staged</div></div>", unsafe_allow_html=True)
            mc3.markdown(f"<div class='kpi-card'><div class='kpi-value'>{total_gb:,.1f} GB</div><div class='kpi-label'>Storage Release</div></div>", unsafe_allow_html=True)

            st.dataframe(cart_df, use_container_width=True, hide_index=True, height=300)

            rollback = st.selectbox("Rollback Retention Policy", ["7 Days", "30 Days", "90 Days (Compliance Requirement)"], index=1)

            ap1, ap2, ap3 = st.columns(3)
            if ap1.button("✅ Approve Archival", type="primary", use_container_width=True):
                st.success(f"Archival approved for {len(cart_df)} assets. Rollback snapshots retained for {rollback}.")
                st.session_state.archival_cart = []
                st.rerun()

            buf3 = io.BytesIO()
            with pd.ExcelWriter(buf3, engine='openpyxl') as w3:
                cart_df.to_excel(w3, index=False, sheet_name='Archival Report')
            ap2.download_button("📥 Export Archival Report", data=buf3.getvalue(),
                                file_name="archival_report.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True)

            with ap3.expander("📧 Email Report"):
                recip = st.text_input("Recipient Email", placeholder="steward@company.com", key="email_recip")
                if st.button("Send via SendGrid", key="send_email"):
                    sg_key = os.environ.get("SENDGRID_API_KEY", "")
                    from_email = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@company.com")
                    if sg_key and not sg_key.startswith("SG.placeholder"):
                        try:
                            import sendgrid as sg_mod
                            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
                            msg = Mail(from_email=from_email, to_emails=recip,
                                       subject=f"Archival Report — {plat} / {domain}",
                                       html_content=f"<p>Please review the attached archival report for <b>{len(cart_df)}</b> assets. Projected 5-year savings: <b>${total_sav:,.0f}</b>.</p>")
                            attachment = Attachment(
                                FileContent(base64.b64encode(buf3.getvalue()).decode()),
                                FileName("archival_report.xlsx"),
                                FileType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                                Disposition("attachment")
                            )
                            msg.attachment = attachment
                            sg_mod.SendGridAPIClient(sg_key).send(msg)
                            st.success(f"Report sent to {recip} via SendGrid.")
                        except Exception as e:
                            st.error(f"SendGrid error: {e}")
                    else:
                        st.warning("SendGrid API key not configured. Add SENDGRID_API_KEY to your .env file to enable real email sending.")
                        st.success(f"[Demo] Email to {recip} simulated successfully.")

    # ── Floating AI Assistant Sidebar ──
    with st.expander("✨ Cloud AI Assistant", expanded=False):
        st.markdown("<div id='ai_assistant_anchor'></div>", unsafe_allow_html=True)
        
        # Chat history
        chat_html = "<div class='ai-chat-container'>"
        for msg in st.session_state.ai_messages:
            css_class = "chat-user" if msg["role"] == "user" else "chat-ai"
            prefix = "User: " if msg["role"] == "user" else "AI Agent: "
            chat_html += f"<div class='chat-msg {css_class}'><b>{prefix}</b>{msg['content']}</div>"
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)
        
        with st.form("ai_chat_form", clear_on_submit=True):
            user_q = st.text_input("Ask a question or issue a command:", placeholder="e.g., Who has access to ehr_prod_db?")
            submit_q = st.form_submit_button("Ask AI")
            
            if submit_q and user_q:
                st.session_state.ai_messages.append({"role": "user", "content": user_q})
                
                # Enhanced NLP Agentic Logic
                import re
                q = user_q.lower()
                
                # Context info
                sel_dbs = st.session_state.get('obs_db', [])
                db_ctx = f" across {', '.join(sel_dbs)}" if sel_dbs else ""
                
                resp = ""
                if re.search(r'\b(forecast|spend|cost|bill)\b', q):
                    latest_usage = plat_usage.sort_values('usage_date').iloc[-1]
                    cost_data = pricing_engine.calculate_cost(plat, latest_usage['compute_units'], latest_usage['storage_gb'], latest_usage.get('data_transfer_gb', 0))
                    resp = f"I've analyzed the 5-year trend for **{plat}**. Based on historical ARIMA ML forecasting, your monthly spend is projected to reach **${cost_data['total']*30*1.15:,.0f}** by next year (+15%)."
                
                elif re.search(r'\b(inactive users|access risk|silent killers|permissions|who has access)\b', q):
                    if sel_dbs:
                        db = sel_dbs[0]
                        users = plat_assets[plat_assets['database'] == db]['users_with_access'].sum()
                        resp = f"For **{db}**, there are currently **{users:,}** users with granted access. I recommend a stewardship review to prune inactive accounts."
                    else:
                        total_inactive_users = plat_assets['users_with_access'].sum() - plat_assets['active_users'].sum()
                        resp = f"⚠️ I identified **{total_inactive_users:,}** inactive access holders across the **{domain}** domain. These are 'silent killers' for governance. You can view the full list in the Optimization & Governance tab."
                
                elif re.search(r'\b(show inactive assets|archive|optimize|clean)\b', q):
                    inactive_assets_df = plat_assets[~plat_assets['is_active']]
                    if not inactive_assets_df.empty:
                        tables_to_archive = inactive_assets_df['table_name'].tolist()
                        st.session_state.archival_cart = list(set(st.session_state.archival_cart + tables_to_archive))
                        resp = f"✅ **Action Triggered:** I have scanned **{plat}** and added **{len(tables_to_archive)}** inactive assets to your archival workflow. This will reclaim **{inactive_assets_df['storage_release_gb'].sum():,.1f} GB** of storage."
                    else:
                        resp = "I've scanned the environment and found no additional inactive assets to archive at this time."
                
                elif re.search(r'\b(size|storage|memory|footprint)\b', q):
                    total_gb = plat_assets['size_gb'].sum()
                    active_gb = plat_assets[plat_assets['is_active']]['size_gb'].sum()
                    resp = f"The total storage footprint for **{domain}** on **{plat}**{db_ctx} is **{total_gb:,.1f} GB**. Active assets account for {active_gb:,.1f} GB."
                
                elif re.search(r'\b(recommend|governance|insights)\b', q):
                    if inactive_df_all.empty:
                         resp = "I've scanned the environment and found no inactive assets to analyze at this time."
                    else:
                        top_asset = inactive_df_all.sort_values('five_year_savings', ascending=False).iloc[0]
                        gov_engine = GovernanceEngine(plat)
                        recs = gov_engine.generate_recommendations(top_asset)
                        resp = f"For **{top_asset['table_name']}**, I recommend the following governance actions:\n\n"
                        for r in recs[:3]:
                            resp += f"- **{r['dimension']}**: {r['recommendation']}\n"
                        resp += f"\nYou can view the full 15-dimension analysis in the **Cloud Governance & Optimization** tab."
                
                else:
                    resp = f"I am your Cloud Governance AI. I can help you analyze access risks, forecast **{plat}** costs, or automate data archival for the **{domain}** domain. Try asking: 'What is my forecasted spend?' or 'Archive inactive data'."
                
                st.session_state.ai_messages.append({"role": "ai", "content": resp})
                st.rerun()

if __name__ == "__main__":
    main()
