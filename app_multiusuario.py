# =========================================================
# APP COMPLETA - RESUMEN FASE 4
# =========================================================
# =========================================================
# RESUMEN PRO - FASE 3: GRAFICOS DASHBOARD
# =========================================================
import io
import os
import zipfile
from typing import Dict

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db import (
    create_game,
    delete_game,
    duplicate_game,
    game_exists,
    get_all_decisions,
    get_decision,
    get_latest_game_id,
    init_db,
    list_games,
    load_game_state,
    rename_game,
    set_professor_password,
    set_review_status,
    update_game_state,
    update_team_password,
    upsert_decision,
    verify_professor_password,
    verify_team_password,
)
from engine import MarketEngine
from pdf_reports import (
    make_brand_product_pdf,
    make_competition_pdf,
    make_facilitator_pdf,
    make_segments_pdf,
)


# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Simulador de Mercado Multiusuario", layout="wide")
init_db()


# =========================================================
# SIDEBAR VISUAL TIPO BOCETO
# =========================================================
def inject_sidebar_boceto_styles():
    st.markdown("""
    <style>
    .stApp { background:#F8FAFC !important; color:#071E49 !important; }
    .block-container { padding-top:1.05rem !important; padding-left:1.55rem !important; padding-right:1.55rem !important; padding-bottom:1.2rem !important; max-width:1500px !important; }
    header[data-testid="stHeader"] { background:rgba(255,255,255,.92) !important; border-bottom:1px solid #E6EDF7; }
    #MainMenu, footer { visibility:hidden !important; }
    [data-testid="stSidebarCollapseButton"] { display:none !important; }
    .main h1:first-child { display:none !important; }
    section[data-testid="stSidebar"] { background:linear-gradient(180deg,#061936 0%,#071D3D 52%,#041326 100%) !important; border-right:1px solid rgba(255,255,255,.08) !important; box-shadow:12px 0 34px rgba(15,23,42,.18) !important; min-width:245px !important; max-width:245px !important; }
    section[data-testid="stSidebar"] > div { padding:1.05rem .82rem .85rem .82rem !important; }
    .sim-sidebar-brand { display:flex; align-items:center; gap:11px; padding:.15rem 4px 1.35rem 4px; margin-bottom:.35rem; }
    .sim-logo { width:42px; height:42px; border-radius:11px; display:flex; align-items:flex-end; justify-content:center; gap:4px; padding:8px; background:linear-gradient(135deg,#60A5FA 0%,#2563EB 100%); box-shadow:0 12px 26px rgba(37,99,235,.35); flex:0 0 42px; }
    .sim-logo span { display:block; width:5px; border-radius:8px; background:#fff; opacity:.98; }
    .sim-logo span:nth-child(1){height:13px}.sim-logo span:nth-child(2){height:24px}.sim-logo span:nth-child(3){height:18px}
    .sim-brand-title { font-size:.84rem; line-height:1.05; font-weight:900; color:#fff !important; white-space:nowrap; }
    .sim-brand-subtitle { margin-top:4px; font-size:.63rem; font-weight:700; color:#B9C8E2 !important; white-space:nowrap; }
    .sim-sidebar-section-label { color:#8295B5 !important; font-size:.62rem !important; font-weight:900 !important; letter-spacing:.075em !important; text-transform:uppercase !important; margin:1.02rem 0 .48rem 0 !important; }
    .sim-sidebar-mini { color:#9FB0C9 !important; font-size:.72rem !important; line-height:1.42 !important; }
    section[data-testid="stSidebar"] hr { margin:1rem 0 !important; border-color:rgba(255,255,255,.12) !important; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] { color:#EAF1FF !important; }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > label { display:none !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] { gap:.46rem !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label { position:relative; min-height:2.65rem !important; padding:.62rem .72rem !important; margin:0 !important; border-radius:11px !important; background:transparent !important; border:1px solid transparent !important; display:flex !important; align-items:center !important; transition:all .16s ease !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display:none !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label p { font-size:.86rem !important; line-height:1.1 !important; font-weight:850 !important; color:#EAF1FF !important; margin:0 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background:rgba(255,255,255,.07) !important; border-color:rgba(255,255,255,.08) !important; transform:translateX(1px); }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) { background:linear-gradient(135deg,#2F80ED 0%,#0F6BFF 100%) !important; border-color:rgba(255,255,255,.12) !important; box-shadow:0 12px 26px rgba(37,99,235,.34) !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p { color:#fff !important; font-weight:900 !important; }
    section[data-testid="stSidebar"] [data-testid="stSelectbox"] label, section[data-testid="stSidebar"] [data-testid="stTextInput"] label { color:#B7C5DB !important; font-size:.72rem !important; font-weight:800 !important; margin-bottom:.14rem !important; }
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div, section[data-testid="stSidebar"] div[data-baseweb="input"] > div, section[data-testid="stSidebar"] input { border-radius:12px !important; min-height:2.35rem !important; background:#fff !important; border-color:rgba(255,255,255,.22) !important; font-size:.84rem !important; }
    section[data-testid="stSidebar"] .stButton > button { width:100% !important; min-height:2.55rem !important; border-radius:12px !important; background:rgba(255,255,255,.10) !important; color:#fff !important; border:1px solid rgba(255,255,255,.16) !important; font-weight:850 !important; text-align:left !important; justify-content:flex-start !important; padding-left:.9rem !important; }
    section[data-testid="stSidebar"] .stButton > button:hover { background:rgba(255,255,255,.16) !important; border-color:rgba(255,255,255,.24) !important; }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar_brand():
    st.markdown("""
    <div class="sim-sidebar-brand">
        <div class="sim-logo"><span></span><span></span><span></span></div>
        <div>
            <div class="sim-brand-title">Simulador de Mercado</div>
            <div class="sim-brand-subtitle">Simulación de Marketing</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


inject_sidebar_boceto_styles()




# =========================================================
# HELPERS GENERALES
# =========================================================
def fmt_eur(value):
    try:
        return f"{float(value):,.0f} €".replace(",", ".")
    except Exception:
        return str(value)


def fmt_pct(value, nd=1):
    try:
        return f"{float(value) * 100:.{nd}f}%"
    except Exception:
        return str(value)


def compute_marketing_roi(profit, marketing_investment):
    """Beneficio generado por cada euro invertido en presupuesto de marketing."""
    try:
        profit = float(profit or 0.0)
        marketing_investment = float(marketing_investment or 0.0)
    except Exception:
        return None
    if marketing_investment <= 0:
        return None
    return profit / marketing_investment


def fmt_roi(value):
    try:
        if value is None:
            return "—"
        return f"{float(value):.2f}x".replace(".", ",")
    except Exception:
        return "—"


def marketing_roi_message(roi):
    if roi is None:
        return "Sin inversión cerrada suficiente", "warning"
    roi = float(roi)
    if roi >= 2.0:
        return "Inversión muy eficiente", "positive"
    if roi >= 1.0:
        return "Inversión rentable", "positive"
    if roi >= 0.0:
        return "Rentabilidad ajustada", "warning"
    return "Inversión no rentable", "danger"


def default_budget_by_num_teams(n):
    table = {3: 170000, 4: 150000, 5: 130000, 6: 120000, 7: 110000, 8: 100000}
    return table.get(n, 120000)


def get_team_index(team_name, teams):
    return teams.index(team_name)


def estimate_reference_units(team_name, teams, engine):
    idx = get_team_index(team_name, teams)
    prev_units = float(engine.customer_base[idx].sum())
    if prev_units > 0:
        return prev_units
    return float((engine.market_base * 0.22) / len(teams))


def estimate_unit_cost(engine, team_name, teams, product_perf, product_design, product_reliability):
    idx = get_team_index(team_name, teams)
    base_cost = float(engine.unit_cost[idx])
    cost_mult = 1.0 + 0.20 * product_perf + 0.10 * product_design + 0.18 * product_reliability
    final_cost = base_cost * cost_mult
    return base_cost, final_cost


def estimate_product_investment_cost(product_perf, product_design, product_reliability):
    return 12000 * product_perf + 9000 * product_design + 14000 * product_reliability


def estimate_research_cost(buy_segments, buy_competition, buy_brand_product):
    return 5000 * int(buy_segments) + 4000 * int(buy_competition) + 4000 * int(buy_brand_product)


def get_budget_floor(base_budget):
    return max(60000.0, float(base_budget) * 0.50)


def get_team_budget_for_round(state, team_name):
    team_budgets = state.get("team_budgets", {}) or {}
    if team_name in team_budgets:
        return float(team_budgets[team_name])
    return float(state.get("budget_per_team", 0.0))


def compute_next_team_budget(base_budget, budget_remaining_actual, profit, reinvestment_rate=0.50):
    next_budget = float(base_budget) + float(budget_remaining_actual) + reinvestment_rate * float(profit)
    return max(get_budget_floor(base_budget), next_budget)


def ensure_first_game_exists():
    if game_exists():
        return

    teams = ["Equipo A", "Equipo B", "Equipo C", "Equipo D"]
    engine = MarketEngine(teams)
    team_passwords = {team: "1234" for team in teams}

    create_game(
        game_name="Partida inicial",
        teams=teams,
        team_passwords=team_passwords,
        budget_per_team=default_budget_by_num_teams(len(teams)),
        round_n=1,
        round_status="open",
        engine_state=engine.get_state(),
        history=[],
        last_truth=None,
        last_research=None,
        last_event=None,
        team_budgets={team: default_budget_by_num_teams(len(teams)) for team in teams},
        event_this_round=False,
        professor_password="admin123",
    )


ensure_first_game_exists()


if "role" not in st.session_state:
    st.session_state["role"] = None
if "team_name" not in st.session_state:
    st.session_state["team_name"] = None
if "professor_ok" not in st.session_state:
    st.session_state["professor_ok"] = False
if "current_game_id" not in st.session_state:
    st.session_state["current_game_id"] = get_latest_game_id()


def logout():
    st.session_state["role"] = None
    st.session_state["team_name"] = None
    st.session_state["professor_ok"] = False


def switch_game(game_id: int):
    st.session_state["current_game_id"] = game_id
    st.session_state["role"] = None
    st.session_state["team_name"] = None
    st.session_state["professor_ok"] = False




def backfill_team_budgets_from_history(state):
    team_budgets = state.get("team_budgets", {}) or {}
    teams = state.get("teams", [])
    if team_budgets and all(t in team_budgets for t in teams):
        return team_budgets

    base_budget = float(state.get("budget_per_team", 0.0))
    history = state.get("history", []) or []
    if not history:
        return {team: base_budget for team in teams}

    last_round = history[-1].get("truth", [])
    if not last_round:
        return {team: base_budget for team in teams}

    rebuilt = {}
    for row in last_round:
        rebuilt[row["team"]] = compute_next_team_budget(
            base_budget=base_budget,
            budget_remaining_actual=row.get("budget_remaining_actual", 0.0),
            profit=row.get("profit", 0.0),
        )
    for team in teams:
        rebuilt.setdefault(team, base_budget)
    return rebuilt

def load_current_state():
    game_id = st.session_state.get("current_game_id")
    if game_id is None:
        latest_id = get_latest_game_id()
        if latest_id is not None:
            st.session_state["current_game_id"] = latest_id
            game_id = latest_id

    if game_id is None:
        return None

    state = load_game_state(game_id)
    if state is None:
        latest_id = get_latest_game_id()
        if latest_id is not None:
            st.session_state["current_game_id"] = latest_id
            return load_game_state(latest_id)
        return None
    return state


# =========================================================
# HELPERS UI / ESTRATEGIA
# =========================================================
def get_strategy_label(price, promo_value, dist_value, product_design_value, product_reliability_value, comm_online, comm_pr, comm_trad):
    premium_signal = (
        (price >= 9.0)
        + (product_design_value >= 0.65)
        + (product_reliability_value >= 0.65)
        + (comm_pr + comm_trad > comm_online)
    )
    value_signal = (
        (price <= 8.0)
        + (promo_value >= 0.08)
        + (dist_value >= 0.70)
        + (comm_online >= comm_pr)
    )

    if premium_signal >= value_signal + 2:
        return "Premium"
    elif value_signal >= premium_signal + 2:
        return "Valor"
    return "Equilibrada"


def get_coherence_label(price, quality_value, promo_value, dist_value, estimated_budget_remaining):
    score = 0.0

    if price > 9.5 and quality_value < 0.58:
        score -= 1.2
    elif price >= 9.0 and quality_value >= 0.60:
        score += 1.0

    if promo_value > 0.12 and price >= 9.0:
        score -= 0.9
    elif promo_value <= 0.10:
        score += 0.4

    if dist_value >= 0.65:
        score += 0.5
    elif dist_value < 0.45:
        score -= 0.5

    if estimated_budget_remaining < 0:
        score -= 2.0
    elif estimated_budget_remaining >= 0:
        score += 0.6

    if score >= 1.2:
        return "Alta"
    elif score >= 0.0:
        return "Media"
    return "Baja"


def build_warnings(price, quality_value, promo_value, dist_value, comm_online, comm_trad, comm_rrss, comm_pr, strategy_label, estimated_budget_remaining):
    warnings = []
    if price > 9.5 and quality_value < 0.58:
        warnings.append("Precio alto para la calidad propuesta.")
    if comm_online > (comm_trad + comm_rrss + comm_pr) and dist_value < 0.55:
        warnings.append("Mucho foco en captación online con distribución limitada.")
    if promo_value > 0.12 and strategy_label == "Premium":
        warnings.append("Una promoción muy alta puede ser incoherente con una estrategia premium.")
    if dist_value < 0.40:
        warnings.append("Una distribución baja limita mucho la conversión, aunque el resto de la estrategia sea buena.")
    if estimated_budget_remaining < 0:
        warnings.append("El presupuesto estimado supera el límite disponible.")
    return warnings


def get_product_fit_label(product_perf_value, product_design_value, product_reliability_value):
    if product_design_value >= product_perf_value and product_design_value >= product_reliability_value:
        return "Exigentes"
    if product_perf_value >= product_design_value and product_perf_value >= product_reliability_value:
        return "Ahorradores"
    return "Equilibrados"


def build_positioning_chart_from_last_research(state, highlight_team=None):
    fig = go.Figure()
    last_research = state.get("last_research")

    if not last_research:
        fig.add_annotation(
            text="No hay informe de marca disponible de la última ronda.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )
        fig.update_layout(height=380, title="Mapa calidad-precio")
        return fig

    prices = last_research.get("observed_avg_price", {})
    qualities = last_research.get("estimated_quality", {})

    for t in prices:
        if t in qualities:
            fig.add_trace(
                go.Scatter(
                    x=[prices[t]],
                    y=[qualities[t] * 100],
                    mode="markers+text",
                    text=[t],
                    textposition="top center",
                    marker=dict(size=18 if t == highlight_team else 11, symbol="diamond" if t == highlight_team else "circle"),
                    showlegend=False,
                )
            )

    fig.update_layout(
        title="Mapa de posicionamiento: precio y calidad estimada",
        xaxis_title="Precio observado",
        yaxis_title="Calidad estimada (%)",
        height=380,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_yaxes(range=[0, 100])
    return fig


def build_decision_positioning_preview_chart(team_name, teams, price, quality_value, state):
    fig = go.Figure()

    last_research = state.get("last_research")
    if last_research and "observed_avg_price" in last_research and "estimated_quality" in last_research:
        for t in teams:
            p = last_research.get("observed_avg_price", {}).get(t)
            q = last_research.get("estimated_quality", {}).get(t)
            if p is not None and q is not None:
                fig.add_trace(
                    go.Scatter(
                        x=[p],
                        y=[q * 100],
                        mode="markers+text",
                        text=[t],
                        textposition="top center",
                        marker=dict(size=13 if t == team_name else 9),
                        showlegend=False,
                    )
                )

    fig.add_trace(
        go.Scatter(
            x=[price],
            y=[quality_value * 100],
            mode="markers+text",
            text=[f"{team_name} (tu decisión)"],
            textposition="bottom center",
            marker=dict(size=18, symbol="diamond"),
            showlegend=False,
        )
    )

    fig.update_layout(
        title="Vista previa de posicionamiento",
        xaxis_title="Precio",
        yaxis_title="Producto / calidad (%)",
        height=380,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_yaxes(range=[0, 100])
    return fig


def build_product_radar_chart(product_perf_value, product_design_value, product_reliability_value):
    categories = ["Rendimiento", "Diseño", "Fiabilidad", "Rendimiento"]
    values = [
        product_perf_value * 100,
        product_design_value * 100,
        product_reliability_value * 100,
        product_perf_value * 100,
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name="Producto",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=340,
        margin=dict(l=20, r=20, t=30, b=20),
        title="Perfil del producto",
    )
    return fig


def build_comm_chart(comm_trad, comm_online, comm_rrss, comm_pr):
    labels = ["Tradicional", "Online", "RRSS", "PR"]
    values = [comm_trad, comm_online, comm_rrss, comm_pr]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                sort=False
            )
        ]
    )
    fig.update_layout(
        title="Mix de comunicación",
        height=340,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=True,
    )
    return fig



def build_funnel_chart(knowledge_score, consideration_score, purchase_score, retention_score):
    fig = go.Figure(
        go.Funnel(
            y=["Conocimiento", "Consideración", "Compra", "Retención"],
            x=[knowledge_score, consideration_score, purchase_score, retention_score],
            textinfo="value+percent initial",
        )
    )
    fig.update_layout(
        title="Funnel estratégico de la ronda",
        height=340,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def compute_funnel_strength_scores(
    price,
    promo_value,
    dist_value,
    quality_value,
    product_perf_value,
    product_design_value,
    product_reliability_value,
    comm_trad,
    comm_online,
    comm_rrss,
    comm_pr,
    comm_total,
    coherence_label,
):
    def clip01(x):
        return max(0.0, min(1.0, float(x)))

    def clip100(x):
        return max(5.0, min(100.0, float(x)))

    # Normalización de presupuesto de comunicación para no sobrerrecompensar el gasto bruto.
    comm_budget_norm = clip01(comm_total / 30000.0)

    mix_total = max(comm_total, 1.0)
    trad_mix = comm_trad / mix_total
    online_mix = comm_online / mix_total
    rrss_mix = comm_rrss / mix_total
    pr_mix = comm_pr / mix_total

    # Precio: 1.0 significa muy competitivo, 0.0 significa claramente alto.
    price_value_score = clip01((10.5 - float(price)) / 4.5)
    price_consideration_score = clip01(1.0 - abs(float(price) - 8.5) / 3.5)

    # Coherencia simplificada para el funnel visual.
    coherence_score_map = {
        "Alta": 0.85,
        "Media": 0.60,
        "Baja": 0.30,
    }
    coherence_score = coherence_score_map.get(coherence_label, 0.60)

    # Posicionamiento: lectura resumida similar al motor.
    brand_value_signal = (
        0.58 * price_value_score
        + 0.22 * clip01(product_perf_value)
        + 0.10 * clip01(rrss_mix)
        + 0.10 * clip01(promo_value / 0.15)
    )
    positioning_value_price = clip01(brand_value_signal)

    premium_comm_signal = 0.65 * pr_mix + 0.35 * trad_mix
    positioning_quality = clip01(
        0.52 * quality_value
        + 0.18 * premium_comm_signal
        + 0.10 * clip01(product_design_value)
        + 0.10 * clip01(product_reliability_value)
        - 0.10 * max(0.0, promo_value - 0.12)
    )

    positioning_score = clip01(0.45 * positioning_value_price + 0.55 * positioning_quality)

    # Satisfacción aproximada para la lectura visual.
    promo_moderation = clip01(1.0 - max(0.0, promo_value - 0.08) / 0.22)
    satisfaction_score = clip01(
        0.42 * quality_value
        + 0.22 * product_reliability_value
        + 0.16 * coherence_score
        + 0.10 * dist_value
        + 0.10 * promo_moderation
    )

    knowledge = clip100(100 * (
        0.28 * clip01(trad_mix)
        + 0.24 * clip01(rrss_mix)
        + 0.16 * clip01(pr_mix)
        + 0.12 * clip01(online_mix)
        + 0.20 * comm_budget_norm
    ))

    consideration = clip100(100 * (
        0.26 * clip01(quality_value)
        + 0.24 * positioning_score
        + 0.14 * price_consideration_score
        + 0.10 * clip01(dist_value)
        + 0.10 * clip01(rrss_mix)
        + 0.08 * clip01(online_mix)
        + 0.08 * clip01(trad_mix)
    ))

    purchase = clip100(100 * (
        0.25 * price_value_score
        + 0.24 * clip01(promo_value / 0.20)
        + 0.22 * clip01(dist_value)
        + 0.16 * clip01(online_mix)
        + 0.13 * positioning_score
    ))

    promo_retention_effect = (
        0.10 * clip01(promo_value / 0.08)
        if promo_value <= 0.08
        else 0.10 * clip01(1.0 - (promo_value - 0.08) / 0.22)
    )

    retention = clip100(100 * (
        0.30 * satisfaction_score
        + 0.24 * clip01(quality_value)
        + 0.16 * coherence_score
        + promo_retention_effect
        + 0.08 * clip01(pr_mix)
        + 0.06 * clip01(rrss_mix)
        + 0.06 * clip01(dist_value)
    ))

    return knowledge, consideration, purchase, retention

def build_market_segment_chart(last_research):
    fig = go.Figure()

    segment_sizes = last_research.get("segment_sizes", {}) if last_research else {}
    if segment_sizes:
        labels = [segment_name_es(k) for k in segment_sizes.keys()]
        values = [float(v) for v in segment_sizes.values()]
        fig.add_trace(
            go.Bar(
                x=labels,
                y=values,
                text=[f"{int(round(v)):,}".replace(",", ".") for v in values],
                textposition="inside",
                insidetextanchor="middle",
                hovertemplate="<b>%{x}</b><br>Tamaño: %{y:,.0f}<extra></extra>",
            )
        )
    else:
        fig.add_annotation(
            text="Aún no hay datos de segmentos de una ronda cerrada.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )

    fig.update_layout(
        title="Tamaño de segmentos",
        xaxis_title="Segmento",
        yaxis_title="Tamaño",
        height=380,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def build_team_segment_sales_chart(last_research, team_name):
    fig = go.Figure()

    if not last_research:
        fig.add_annotation(
            text="Aún no hay datos de segmentos de una ronda cerrada.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )
        fig.update_layout(height=360, title="Tus ventas por segmento")
        return fig

    segment_sizes = last_research.get("segment_sizes", {})
    seg_mix = last_research.get("segment_brand_mix", {})

    segment_sales = {}
    for seg, size in segment_sizes.items():
        vals = seg_mix.get(seg, {})
        team_share = float(vals.get(team_name, 0.0))
        segment_sales[segment_name_es(seg)] = max(0.0, float(size) * team_share)

    total_sales = sum(segment_sales.values())
    if not segment_sales or total_sales <= 0:
        fig.add_annotation(
            text="No hay datos suficientes para calcular tus ventas por segmento.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )
        fig.update_layout(height=360, title="Tus ventas por segmento")
        return fig

    labels = list(segment_sales.keys())
    values = [segment_sales[s] for s in labels]

    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.35,
            sort=False,
            textinfo="label+percent",
            textposition="inside",
            hovertemplate="<b>%{label}</b><br>Ventas estimadas: %{value:,.0f}<br>Peso en tus ventas: %{percent}<extra></extra>",
        )
    )

    total_text = f"{int(round(total_sales)):,}".replace(",", ".")
    fig.update_layout(
        title=f"Tus ventas por segmento<br><sup>Total estimado: {total_text}</sup>",
        height=380,
        margin=dict(l=20, r=20, t=70, b=20),
        showlegend=True,
    )
    return fig


def build_segment_purchase_pie_chart(last_research, segment_name, highlight_team=None):
    fig = go.Figure()

    if not last_research:
        fig.add_annotation(
            text="Aún no hay datos de segmentos de una ronda cerrada.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )
        fig.update_layout(height=320, title=segment_name_es(segment_name))
        return fig

    segment_sizes = last_research.get("segment_sizes", {})
    seg_mix = last_research.get("segment_brand_mix", {})
    segment_total = float(segment_sizes.get(segment_name, 0.0))
    segment_values = seg_mix.get(segment_name, {})

    if not segment_values or segment_total <= 0:
        fig.add_annotation(
            text="No hay datos disponibles para este segmento.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )
        fig.update_layout(height=320, title=segment_name)
        return fig

    labels = list(segment_values.keys())
    values = [max(0.0, float(segment_values[t])) * segment_total for t in labels]
    pull = [0.08 if t == highlight_team else 0.0 for t in labels]

    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.18,
            sort=False,
            pull=pull,
            textinfo="percent",
            textposition="inside",
            hovertemplate="<b>%{label}</b><br>Compradores estimados: %{value:,.0f}<br>Cuota en el segmento: %{percent}<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"{segment_name_es(segment_name)}<br><sup>Total segmento: {int(round(segment_total))}</sup>",
        height=330,
        margin=dict(l=20, r=20, t=70, b=20),
        showlegend=True,
    )
    return fig

def build_public_competitor_share_chart(last_truth):
    fig = go.Figure()

    if last_truth:
        df = pd.DataFrame(last_truth).sort_values("share", ascending=False)
        fig.add_trace(
            go.Bar(
                x=df["team"],
                y=(df["share"] * 100).round(1),
            )
        )
    else:
        fig.add_annotation(
            text="Aún no hay resultados públicos de una ronda cerrada.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )

    fig.update_layout(
        title="Cuota de mercado",
        xaxis_title="Equipo",
        yaxis_title="Cuota (%)",
        height=360,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def build_public_competitor_sales_chart(last_truth):
    fig = go.Figure()

    if last_truth:
        df = pd.DataFrame(last_truth).sort_values("units", ascending=False)
        fig.add_trace(
            go.Bar(
                x=df["team"],
                y=df["units"],
            )
        )
    else:
        fig.add_annotation(
            text="Aún no hay ventas públicas de una ronda cerrada.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )

    fig.update_layout(
        title="Ventas por marca",
        xaxis_title="Equipo",
        yaxis_title="Ventas",
        height=360,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def build_public_competitor_price_chart(last_truth):
    fig = go.Figure()

    if last_truth:
        df = pd.DataFrame(last_truth).sort_values("price", ascending=True)
        fig.add_trace(
            go.Bar(
                x=df["team"],
                y=df["price"].round(2),
            )
        )
    else:
        fig.add_annotation(
            text="Aún no hay precios observados.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )

    fig.update_layout(
        title="Precio medio por marca",
        xaxis_title="Equipo",
        yaxis_title="Precio",
        height=360,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def build_history_line_chart(history, metric, title, y_title, mult=1.0):
    fig = go.Figure()

    if not history:
        fig.add_annotation(
            text="Aún no hay histórico disponible.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )
        fig.update_layout(height=360, title=title)
        return fig

    rows = []
    for round_data in history:
        rnum = round_data["round"]
        for row in round_data["truth"]:
            rows.append({
                "round": rnum,
                "team": row["team"],
                "value": float(row.get(metric, 0.0)) * mult
            })

    df = pd.DataFrame(rows)
    if df.empty:
        fig.add_annotation(
            text="No hay datos para este gráfico.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False
        )
        fig.update_layout(height=360, title=title)
        return fig

    for team in df["team"].unique():
        dft = df[df["team"] == team].sort_values("round")
        fig.add_trace(
            go.Scatter(
                x=dft["round"],
                y=dft["value"],
                mode="lines+markers",
                name=team,
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="Ronda",
        yaxis_title=y_title,
        height=360,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def make_cost_dataframe(
    comm_trad,
    comm_online,
    comm_rrss,
    comm_pr,
    comm_total,
    research_cost,
    estimated_promo_cost,
    estimated_dist_cost,
    estimated_product_investment_cost,
    quality_value,
    base_unit_cost,
    final_unit_cost,
    estimated_production_cost,
    budget_per_team,
    estimated_budget_used,
    estimated_budget_remaining,
):
    return pd.DataFrame([
        {"Concepto": "Publicidad tradicional", "Importe estimado (€)": round(comm_trad, 2)},
        {"Concepto": "Publicidad online", "Importe estimado (€)": round(comm_online, 2)},
        {"Concepto": "RRSS", "Importe estimado (€)": round(comm_rrss, 2)},
        {"Concepto": "Relaciones públicas", "Importe estimado (€)": round(comm_pr, 2)},
        {"Concepto": "Comunicación total", "Importe estimado (€)": round(comm_total, 2)},
        {"Concepto": "Coste informes de investigación", "Importe estimado (€)": round(research_cost, 2)},
        {"Concepto": "Coste promoción estimado", "Importe estimado (€)": round(estimated_promo_cost, 2)},
        {"Concepto": "Coste distribución estimado", "Importe estimado (€)": round(estimated_dist_cost, 2)},
        {"Concepto": "Coste inversión en producto", "Importe estimado (€)": round(estimated_product_investment_cost, 2)},
        {"Concepto": "Índice global de producto (%)", "Importe estimado (€)": round(quality_value * 100, 2)},
        {"Concepto": "Coste unitario base", "Importe estimado (€)": round(base_unit_cost, 2)},
        {"Concepto": "Coste unitario final por producto", "Importe estimado (€)": round(final_unit_cost, 2)},
        {"Concepto": "Coste fabricación estimado (informativo)", "Importe estimado (€)": round(estimated_production_cost, 2)},
        {"Concepto": "Presupuesto disponible", "Importe estimado (€)": round(budget_per_team, 2)},
        {"Concepto": "Presupuesto estimado consumido", "Importe estimado (€)": round(estimated_budget_used, 2)},
        {"Concepto": "Presupuesto estimado restante", "Importe estimado (€)": round(estimated_budget_remaining, 2)},
    ])


def classify_price_position(team_price, avg_price):
    if team_price <= avg_price - 0.35:
        return "Precio competitivo"
    if team_price >= avg_price + 0.35:
        return "Precio alto"
    return "Precio intermedio"


def classify_promo_level(promo_value):
    if promo_value >= 0.12:
        return "Promoción intensa"
    if promo_value >= 0.06:
        return "Promoción media"
    return "Promoción baja"


def classify_comm_style(row):
    comm_trad = float(row.get("comm_trad", 0))
    comm_online = float(row.get("comm_online", 0))
    comm_rrss = float(row.get("comm_rrss", 0))
    comm_pr = float(row.get("comm_pr", 0))

    values = {
        "tradicional": comm_trad,
        "online": comm_online,
        "rrss": comm_rrss,
        "pr": comm_pr,
    }
    top_channel = max(values.items(), key=lambda x: x[1])[0]
    total = sum(values.values())

    if total <= 0:
        return "Presión publicitaria baja"

    top_share = max(values.values()) / total
    if top_share < 0.40:
        return "Mix equilibrado"

    mapping = {
        "tradicional": "Más orientado a conocimiento de marca",
        "online": "Más orientado a captación",
        "rrss": "Más orientado a visibilidad e interacción",
        "pr": "Más orientado a reputación",
    }
    return mapping[top_channel]


def classify_dist_level(row):
    dist = float(row.get("distribution", 0))
    if dist >= 0.75:
        return "Cobertura comercial alta"
    if dist >= 0.55:
        return "Cobertura comercial media"
    return "Cobertura comercial limitada"


def build_competitive_qualitative_diagnosis(row, avg_price):
    team_name = row["team"]
    price_label = classify_price_position(float(row["price"]), float(avg_price))
    promo_label = classify_promo_level(float(row.get("promo", 0.0)))
    comm_label = classify_comm_style(row)
    dist_label = classify_dist_level(row)
    share = float(row.get("share", 0.0))
    retention_rate = float(row.get("retention_rate", 0.0))
    awareness_true = float(row.get("awareness_true", 0.0))

    diagnosis_parts = []

    diagnosis_parts.append(price_label.lower())
    diagnosis_parts.append(promo_label.lower())
    diagnosis_parts.append(comm_label.lower())
    diagnosis_parts.append(dist_label.lower())

    if share >= 0.28:
        diagnosis_parts.append("con fuerte presencia competitiva")
    elif share <= 0.18:
        diagnosis_parts.append("con presencia competitiva limitada")

    if retention_rate >= 0.65:
        diagnosis_parts.append("y buena defensa de su base de clientes")
    elif retention_rate <= 0.45:
        diagnosis_parts.append("pero con dificultades aparentes para retener")

    if awareness_true >= 0.45:
        diagnosis_parts.append("además de una visibilidad de marca relevante")

    text = ", ".join(diagnosis_parts).strip()
    if text.endswith(","):
        text = text[:-1]

    return f"{team_name}: {text}."


def render_strategy_box(strategy_label, coherence_label, warnings):
    col_a, col_b = st.columns([1, 1])

    with col_a:
        if strategy_label == "Premium":
            st.success(f"**Orientación detectada:** {strategy_label}")
        elif strategy_label == "Valor":
            st.info(f"**Orientación detectada:** {strategy_label}")
        else:
            st.warning(f"**Orientación detectada:** {strategy_label}")

    with col_b:
        if coherence_label == "Alta":
            st.success(f"**Coherencia estratégica:** {coherence_label}")
        elif coherence_label == "Media":
            st.warning(f"**Coherencia estratégica:** {coherence_label}")
        else:
            st.error(f"**Coherencia estratégica:** {coherence_label}")

    if warnings:
        for w in warnings:
            st.warning(w)
    else:
        st.success("La decisión parece razonablemente coherente.")


# =========================================================
# CONSTRUCCIÓN DE DECISIÓN
# =========================================================


def inject_decision_pro_styles():
    """Estilos para la versión profesional de la pantalla de toma de decisiones."""
    st.markdown(
        """
        <style>
        .decision-title h1 { margin: 0; font-size: 2.05rem; line-height: 1.05; color: #071E49; font-weight: 900; letter-spacing: -0.04em; }
        .decision-title p { margin: 9px 0 0 0; color: #42526E; font-size: 0.98rem; }
        .decision-kpi-grid { display: grid; grid-template-columns: repeat(3, minmax(185px, 1fr)); gap: 14px; margin: 8px 0 18px 0; }
        .decision-kpi-card { background: #FFFFFF; border: 1px solid #E4EAF3; border-radius: 16px; padding: 16px 18px; box-shadow: 0 8px 26px rgba(9, 30, 66, 0.06); }
        .decision-kpi-label { color: #52627A; font-size: 0.75rem; font-weight: 850; text-transform: uppercase; letter-spacing: .04em; margin-bottom: 5px; }
        .decision-kpi-value { color: #071E49; font-size: 1.45rem; font-weight: 900; line-height: 1.1; }
        .decision-kpi-note { margin-top: 5px; color: #52627A; font-size: 0.82rem; font-weight: 600; }
        .decision-card-title { display:flex; gap: 11px; align-items:flex-start; padding: 4px 0 12px 0; border-bottom: 1px solid #EEF2F7; margin-bottom: 14px; }
        .decision-card-icon { width: 38px; height: 38px; border-radius: 12px; display:flex; align-items:center; justify-content:center; font-size: 1.28rem; flex: 0 0 auto; }
        .decision-card-heading { margin:0; font-size:1.05rem; color:#071E49; font-weight:900; letter-spacing:-0.02em; }
        .decision-card-subtitle { margin: 3px 0 0 0; color:#53657D; font-size:.86rem; line-height:1.25; }
        .soft-blue { background:#EFF6FF; color:#2563EB; }
        .soft-orange { background:#FFF7ED; color:#F97316; }
        .soft-purple { background:#F5F3FF; color:#7C3AED; }
        .soft-green { background:#ECFDF3; color:#16A34A; }
        .quality-box, .research-total-box, .decision-note-box { background:#F4F8FE; border:1px solid #E8EEF7; border-radius:14px; padding:14px 16px; margin-top: 14px; }
        .quality-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; font-weight:900; color:#0A3472; font-size:.88rem; text-transform:uppercase; }
        .quality-value { font-size:1.3rem; color:#2F80ED; }
        .progress-bg { width:100%; height:10px; border-radius:999px; background:#E5EAF2; overflow:hidden; }
        .progress-fill { height:100%; border-radius:999px; background:#2F80ED; }
        .warning-card { background:#FFF7E8; border:1px solid #FFE0A6; border-radius:14px; padding:14px 16px; margin-top: 14px; color:#6B3F00; font-size:.9rem; line-height:1.35; }
        .research-total-box { background:#ECFDF3; color:#067647; font-weight:900; display:flex; justify-content:space-between; align-items:center; }
        .funnel-stage { display:grid; grid-template-columns: minmax(280px, 1.2fr) 130px 110px; align-items:center; gap:16px; margin: 8px 0; }
        .funnel-shape { height:58px; color:white; display:flex; align-items:center; gap:14px; padding-left:30px; font-weight:900; clip-path: polygon(0 0, 100% 0, 88% 100%, 12% 100%); box-shadow: inset 0 -8px 18px rgba(0,0,0,.08); }
        .funnel-shape .emoji { font-size:1.6rem; }
        .funnel-label small { display:block; font-weight:700; opacity:.90; margin-top:2px; }
        .funnel-score { font-size:1.35rem; font-weight:900; text-align:right; }
        .funnel-score small { display:block; color:#53657D; font-size:.72rem; font-weight:700; margin-top:2px; }
        .level-pill { display:inline-flex; align-items:center; gap:7px; font-size:.78rem; font-weight:900; text-transform:uppercase; }
        .level-dot { width:10px; height:10px; border-radius:99px; display:inline-block; }
        .funnel-info-card { border:1px solid #E4EAF3; border-radius:16px; padding:16px; background:#FFFFFF; min-height: 260px; }
        .funnel-info-card h4 { color:#071E49; margin:0 0 10px 0; font-size:.9rem; font-weight:900; }
        .funnel-info-card p { margin:0 0 11px 0; color:#344054; line-height:1.35; font-size:.84rem; }
        .diagnostic-card { border-radius:16px; border:1px solid #E4EAF3; padding:18px; min-height: 155px; }
        .diag-purple { background:#F7F2FF; border-color:#E8D8FF; }
        .diag-green { background:#F1FAF3; border-color:#D6F0DA; }
        .diag-orange { background:#FFF7ED; border-color:#FFD8A8; }
        .diagnostic-card h4 { margin:0 0 10px 0; color:#071E49; font-size:.78rem; font-weight:900; text-transform:uppercase; }
        .diagnostic-main { font-size:1.28rem; font-weight:900; margin-bottom:8px; }
        .diagnostic-card p, .diagnostic-card li { color:#344054; font-size:.86rem; line-height:1.35; }
        @media (max-width: 1200px) { .decision-kpi-grid { grid-template-columns:1fr; } .funnel-stage { grid-template-columns: 1fr; gap:4px; } .funnel-score { text-align:left; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _decision_card_header(icon, title, subtitle, tone):
    st.markdown(
        f"""
        <div class="decision-card-title">
            <div class="decision-card-icon soft-{tone}">{icon}</div>
            <div>
                <div class="decision-card-heading">{title}</div>
                <div class="decision-card-subtitle">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _funnel_level(score):
    score = float(score)
    if score >= 67:
        return "Alto", "#159A63"
    if score >= 45:
        return "Medio", "#F59E0B"
    return "Bajo", "#EF4444"


def _funnel_stage_text(score, stage):
    level, _ = _funnel_level(score)
    if stage == "Conocimiento":
        return "del mercado objetivo" if level == "Alto" else "de visibilidad estimada"
    if stage == "Consideración":
        return "de las personas alcanzadas"
    if stage == "Compra":
        return "de las personas consideradas"
    return "de los clientes actuales"


def render_decision_funnel_html(knowledge_score, consideration_score, purchase_score, retention_score):
    stages = [
        ("📣", "Conocimiento", "Awareness", float(knowledge_score), "#4285F4"),
        ("👥", "Consideración", "Consideration", float(consideration_score), "#F9A825"),
        ("🛒", "Compra", "Purchase", float(purchase_score), "#4CAF72"),
        ("♡", "Retención", "Retention", float(retention_score), "#8755D9"),
    ]
    rows = []
    for icon, title, subtitle, score, color in stages:
        level, level_color = _funnel_level(score)
        rows.append(
            f"""
            <div class="funnel-stage">
                <div class="funnel-shape" style="background:{color};">
                    <span class="emoji">{icon}</span>
                    <span class="funnel-label">{title}<small>({subtitle})</small></span>
                </div>
                <div class="funnel-score" style="color:{color};">{score:.0f}%<small>{_funnel_stage_text(score, title)}</small></div>
                <div class="level-pill" style="color:{level_color};"><span class="level-dot" style="background:{level_color};"></span>{level}</div>
            </div>
            """
        )
    st.markdown("".join(rows), unsafe_allow_html=True)


def render_funnel_explanation_card():
    st.markdown(
        """
        <div class="funnel-info-card">
            <h4>¿QUÉ INFLUYE EN CADA FASE?</h4>
            <p><b style="color:#4285F4;">● Conocimiento:</b><br>Impulsado principalmente por comunicación: medios tradicionales, redes sociales y RR.PP.</p>
            <p><b style="color:#F9A825;">● Consideración:</b><br>Impulsado por la calidad del producto, la comunicación y la percepción de valor.</p>
            <p><b style="color:#4CAF72;">● Compra:</b><br>Impulsado por precio, promoción, distribución y publicidad online.</p>
            <p><b style="color:#8755D9;">● Retención:</b><br>Impulsado por calidad, fiabilidad y experiencia ofrecida a tus clientes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _strategy_description(strategy_label):
    if strategy_label == "Valor":
        return "Tu estrategia se basa en precio competitivo y promoción para ganar cuota de mercado.", "Enfoque en captación de volumen"
    if strategy_label == "Premium":
        return "Tu estrategia se apoya en producto, marca y precio para construir una posición diferencial.", "Enfoque en valor percibido"
    return "Tu estrategia combina palancas de valor y marca sin una orientación extrema.", "Enfoque equilibrado"


def _coherence_description(coherence_label):
    if coherence_label == "Alta":
        return "Alta coherencia", "Tus decisiones están alineadas entre sí. Continúa así.", "#159A63"
    if coherence_label == "Media":
        return "Coherencia media", "La estrategia tiene sentido, pero aún hay variables que pueden alinearse mejor.", "#F59E0B"
    return "Baja coherencia", "Hay señales de desajuste entre precio, producto, promoción o presupuesto.", "#EF4444"



def inject_decision_phase1_styles():
    """Estilos visuales para Mi decisión - Fase 1: cabecera + KPIs superiores."""
    st.markdown("""
    <style>
    .decision-phase1-head{display:grid;grid-template-columns:1fr 128px;gap:18px;align-items:start;margin:4px 0 18px 0}
    .decision-phase1-title-row{display:flex;align-items:flex-start;gap:13px}
    .decision-phase1-main-icon{width:48px;height:48px;border-radius:14px;background:#EAF2FF;color:#2563EB;display:flex;align-items:center;justify-content:center;font-size:1.55rem;font-weight:950;flex:0 0 48px;box-shadow:0 8px 22px rgba(37,99,235,.08)}
    .decision-phase1-title{margin:0;color:#071E49;font-size:1.72rem;line-height:1.04;font-weight:950;letter-spacing:-.04em;text-transform:uppercase}
    .decision-phase1-subtitle{margin-top:7px;color:#53657D;font-size:.91rem;line-height:1.35;font-weight:700}
    .decision-phase1-round-card{background:#fff;border:1px solid #DDE7F3;border-radius:14px;padding:16px 18px;min-height:86px;box-shadow:0 8px 24px rgba(9,30,66,.055);display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
    .decision-phase1-round-label{color:#53657D;font-size:.70rem;font-weight:950;text-transform:uppercase;letter-spacing:.035em;margin-bottom:8px}
    .decision-phase1-round-value{color:#2563EB;font-size:1.55rem;line-height:1;font-weight:950;letter-spacing:-.03em}
    .decision-phase1-kpi-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:6px 0 12px 0}
    .decision-phase1-kpi-card{background:#fff;border:1px solid #DDE7F3;border-radius:16px;padding:18px 20px;min-height:122px;box-shadow:0 8px 24px rgba(9,30,66,.055);display:flex;align-items:center;gap:16px;position:relative;overflow:hidden}
    .decision-phase1-kpi-card:after{content:"";position:absolute;right:-34px;top:-44px;width:108px;height:108px;border-radius:999px;opacity:.42;background:var(--soft-bg)}
    .decision-phase1-kpi-icon{width:58px;height:58px;border-radius:13px;background:var(--soft-bg);color:var(--main-color);display:flex;align-items:center;justify-content:center;font-size:1.55rem;flex:0 0 58px;z-index:1}
    .decision-phase1-kpi-content{z-index:1;min-width:0}
    .decision-phase1-kpi-label{color:#071E49;font-size:.76rem;line-height:1.15;font-weight:950;text-transform:uppercase;letter-spacing:.025em;margin-bottom:7px}
    .decision-phase1-kpi-value{color:#071E49;font-size:1.55rem;line-height:1.05;font-weight:950;letter-spacing:-.035em;white-space:nowrap}
    .decision-phase1-kpi-note{color:#53657D;font-size:.80rem;line-height:1.25;font-weight:800;margin-top:7px}
    .decision-phase1-budget-alert{border-radius:13px;padding:13px 16px;margin:10px 0 18px 0;display:flex;align-items:center;gap:12px;font-size:.86rem;line-height:1.32;font-weight:900;border:1px solid}
    .decision-phase1-budget-alert.ok{background:#ECFDF3;color:#067647;border-color:#C7F2D6}
    .decision-phase1-budget-alert.bad{background:#FEECEC;color:#B42318;border-color:#FECACA}
    .decision-phase1-alert-icon{width:25px;height:25px;border-radius:999px;display:inline-flex;align-items:center;justify-content:center;flex:0 0 25px;background:currentColor;color:white;font-size:.78rem;font-weight:950}
    @media(max-width:1150px){.decision-phase1-head,.decision-phase1-kpi-grid{grid-template-columns:1fr}.decision-phase1-round-card{align-items:flex-start;text-align:left}}
    </style>
    """, unsafe_allow_html=True)


def _decision_phase1_kpi_html(label, value, note, icon, tone="blue"):
    palette = {
        "blue": ("#2563EB", "#EAF2FF"),
        "green": ("#16A34A", "#EAF8EF"),
        "purple": ("#7C3AED", "#F1E9FF"),
        "orange": ("#F59E0B", "#FFF4D8"),
        "red": ("#DC2626", "#FEECEC"),
    }
    color, soft = palette.get(tone, palette["blue"])
    return (
        f"<div class='decision-phase1-kpi-card' style='--main-color:{color}; --soft-bg:{soft};'>"
        f"<div class='decision-phase1-kpi-icon'>{_html_escape(icon)}</div>"
        f"<div class='decision-phase1-kpi-content'>"
        f"<div class='decision-phase1-kpi-label'>{_html_escape(label)}</div>"
        f"<div class='decision-phase1-kpi-value'>{value}</div>"
        f"<div class='decision-phase1-kpi-note'>{_html_escape(note)}</div>"
        f"</div></div>"
    )


def render_decision_phase1_header_and_kpis(round_n, available_budget, planned_spend, selected_reports_count, research_cost, remaining_budget):
    budget_pct = (float(planned_spend) / max(float(available_budget), 1.0)) * 100
    kpi_html = "".join([
        _decision_phase1_kpi_html("Presupuesto disponible", fmt_eur(available_budget), "para esta ronda", "💼", "green"),
        _decision_phase1_kpi_html("Gasto total planificado", fmt_eur(planned_spend), f"{str(f'{budget_pct:.0f}').replace('.', ',')}% del presupuesto", "📈", "blue"),
        _decision_phase1_kpi_html("Informes seleccionados", str(selected_reports_count), fmt_eur(research_cost), "📋", "purple"),
    ])
    alert_cls = "bad" if remaining_budget < 0 else "ok"
    alert_icon = "!" if remaining_budget < 0 else "✓"
    alert_text = (
        f"Presupuesto excedido. Ajusta la decisión para reducir {fmt_eur(abs(remaining_budget))}."
        if remaining_budget < 0
        else f"Presupuesto dentro del límite. Restante estimado: {fmt_eur(remaining_budget)}"
    )
    st.markdown(
        f"""
        <div class="decision-phase1-head">
            <div class="decision-phase1-title-row">
                <div class="decision-phase1-main-icon">🧠</div>
                <div>
                    <div class="decision-phase1-title">TOMA DE DECISIONES</div>
                    <div class="decision-phase1-subtitle">
                        Define tu estrategia para la próxima ronda.<br>
                        Los indicadores se actualizan automáticamente en tiempo real.
                    </div>
                </div>
            </div>
            <div class="decision-phase1-round-card">
                <div class="decision-phase1-round-label">Ronda actual</div>
                <div class="decision-phase1-round-value">{_html_escape(round_n)}</div>
            </div>
        </div>
        <div class="decision-phase1-kpi-grid">{kpi_html}</div>
        <div class="decision-phase1-budget-alert {alert_cls}">
            <span class="decision-phase1-alert-icon">{alert_icon}</span>
            <span>{_html_escape(alert_text)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _session_value(key, default):
    return st.session_state.get(key, default)


def compute_decision_phase1_preview(game_id, team, round_n, available_budget, ref_units, engine, teams, existing, research_existing):
    price_default = float(existing.get("price", 8.0))
    promo_default = int(round(float(existing.get("promo", 0.06)) * 100))
    dist_default = int(round(float(existing.get("distribution", 0.75)) * 100))
    perf_default = int(round(float(existing.get("product_perf", 0.50)) * 100))
    design_default = int(round(float(existing.get("product_design", 0.50)) * 100))
    reliability_default = int(round(float(existing.get("product_reliability", 0.50)) * 100))

    team_idx_for_stock = get_team_index(team, teams)
    stock_acumulado_anterior = float(getattr(engine, "inventory", [0] * len(teams))[team_idx_for_stock])

    price = float(_session_value(f"dec_price_{game_id}_{team}_{round_n}", price_default))
    promo = int(_session_value(f"dec_promo_{game_id}_{team}_{round_n}", promo_default))
    dist = int(_session_value(f"dec_dist_{game_id}_{team}_{round_n}", dist_default))
    product_perf = int(_session_value(f"dec_perf_{game_id}_{team}_{round_n}", perf_default))
    product_design = int(_session_value(f"dec_design_{game_id}_{team}_{round_n}", design_default))
    product_reliability = int(_session_value(f"dec_rel_{game_id}_{team}_{round_n}", reliability_default))

    comm_trad = int(_session_value(f"dec_trad_{game_id}_{team}_{round_n}", int(existing.get("comm_trad", 4000))))
    comm_online = int(_session_value(f"dec_online_{game_id}_{team}_{round_n}", int(existing.get("comm_online", 4000))))
    comm_rrss = int(_session_value(f"dec_rrss_{game_id}_{team}_{round_n}", int(existing.get("comm_rrss", 2000))))
    comm_pr = int(_session_value(f"dec_pr_{game_id}_{team}_{round_n}", int(existing.get("comm_pr", 2000))))

    buy_segments = bool(_session_value(f"dec_segments_{game_id}_{team}_{round_n}", bool(research_existing.get("segments", False))))
    buy_competition = bool(_session_value(f"dec_comp_{game_id}_{team}_{round_n}", bool(research_existing.get("competition", False))))
    buy_brand_product = bool(_session_value(f"dec_brand_{game_id}_{team}_{round_n}", bool(research_existing.get("brand_product", False))))

    product_perf_value = product_perf / 100.0
    product_design_value = product_design / 100.0
    product_reliability_value = product_reliability / 100.0
    promo_value = promo / 100.0
    dist_value = dist / 100.0

    research_cost = estimate_research_cost(buy_segments, buy_competition, buy_brand_product)
    comm_total = float(comm_trad + comm_online + comm_rrss + comm_pr)
    estimated_product_investment_cost_value = globals()["estimate_product_investment_cost"](
        product_perf_value, product_design_value, product_reliability_value
    )
    estimated_promo_cost = promo_value * price * ref_units * 0.55
    estimated_dist_cost = 1500 * dist_value + 2500 * (dist_value ** 2)
    estimated_budget_used = comm_total + estimated_promo_cost + estimated_dist_cost + estimated_product_investment_cost_value + research_cost
    estimated_budget_remaining = float(available_budget) - float(estimated_budget_used)
    selected_reports_count = int(buy_segments) + int(buy_competition) + int(buy_brand_product)

    return estimated_budget_used, estimated_budget_remaining, selected_reports_count, research_cost



def inject_decision_phase2_styles():
    """Estilos visuales para Mi decisión - Fase 2: Producto + Mercado."""
    st.markdown("""
    <style>
    .decision-phase2-safe-head {
        display:flex;
        gap:13px;
        align-items:flex-start;
        padding:2px 0 14px 0;
        margin-bottom:14px;
        border-bottom:1px solid #EEF2F7;
    }
    .decision-phase2-safe-icon {
        width:44px;
        height:44px;
        border-radius:13px;
        background:var(--soft-bg);
        color:var(--main-color);
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:1.35rem;
        flex:0 0 44px;
    }
    .decision-phase2-safe-title {
        color:#071E49;
        font-size:1.02rem;
        line-height:1.12;
        font-weight:950;
        letter-spacing:-.02em;
        margin:0;
        text-transform:uppercase;
    }
    .decision-phase2-safe-subtitle {
        color:#53657D;
        font-size:.82rem;
        line-height:1.35;
        font-weight:750;
        margin-top:4px;
    }
    .decision-phase2-quality {
        background:#F4F8FE;
        border:1px solid #E2EAF5;
        border-radius:15px;
        padding:15px 16px;
        margin-top:14px;
    }
    .decision-phase2-quality-top {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:14px;
        color:#0A3472;
        font-size:.86rem;
        font-weight:950;
        text-transform:uppercase;
        margin-bottom:10px;
    }
    .decision-phase2-quality-value {
        color:#2563EB;
        font-size:1.35rem;
        font-weight:950;
        white-space:nowrap;
    }
    .decision-phase2-progress {
        width:100%;
        height:11px;
        border-radius:999px;
        background:#DDE5F0;
        overflow:hidden;
    }
    .decision-phase2-progress span {
        display:block;
        height:100%;
        border-radius:999px;
        background:linear-gradient(90deg,#0F6BFF 0%,#2F80ED 100%);
        width:var(--pct);
    }
    .decision-phase2-small-note {
        margin-top:9px;
        color:#53657D;
        font-size:.80rem;
        line-height:1.35;
        font-weight:750;
    }
    .decision-phase2-market-summary {
        background:#F4F8FE;
        border:1px solid #E2EAF5;
        border-radius:15px;
        padding:14px 16px;
        margin-top:13px;
        color:#071E49;
        font-size:.82rem;
        line-height:1.50;
        font-weight:800;
    }
    .decision-phase2-alert {
        border-radius:14px;
        padding:13px 15px;
        margin-top:13px;
        font-size:.84rem;
        line-height:1.38;
        font-weight:850;
        border:1px solid;
        display:flex;
        gap:10px;
        align-items:flex-start;
    }
    .decision-phase2-alert.ok {
        background:#ECFDF3;
        color:#067647;
        border-color:#C7F2D6;
    }
    .decision-phase2-alert.warn {
        background:#FFF7E8;
        color:#8A4B00;
        border-color:#FFE0A6;
    }
    .decision-phase2-alert-icon {
        width:24px;
        height:24px;
        border-radius:999px;
        display:inline-flex;
        align-items:center;
        justify-content:center;
        flex:0 0 24px;
        background:currentColor;
        color:white;
        font-size:.75rem;
        font-weight:950;
        margin-top:1px;
    }
    </style>
    """, unsafe_allow_html=True)


def render_decision_phase2_card_header(icon, title, subtitle, tone="blue"):
    palette = {
        "blue": ("#2563EB", "#EAF2FF"),
        "orange": ("#F59E0B", "#FFF4D8"),
        "green": ("#16A34A", "#EAF8EF"),
        "purple": ("#7C3AED", "#F1E9FF"),
    }
    color, soft = palette.get(tone, palette["blue"])
    st.markdown(
        f"""
        <div class="decision-phase2-safe-head" style="--main-color:{color}; --soft-bg:{soft};">
            <div class="decision-phase2-safe-icon">{_html_escape(icon)}</div>
            <div>
                <div class="decision-phase2-safe-title">{_html_escape(title)}</div>
                <div class="decision-phase2-safe-subtitle">{_html_escape(subtitle)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_phase2_quality_box(quality_preview):
    pct = max(0.0, min(100.0, float(quality_preview) * 100.0))
    st.markdown(
        f"""
        <div class="decision-phase2-quality">
            <div class="decision-phase2-quality-top">
                <span>Calidad global del producto</span>
                <span class="decision-phase2-quality-value">{pct:.0f} <span style="font-size:.82rem;color:#344054;">/ 100</span></span>
            </div>
            <div class="decision-phase2-progress" style="--pct:{pct:.0f}%;"><span></span></div>
            <div class="decision-phase2-small-note">Basado en rendimiento, diseño y fiabilidad.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_phase2_market_summary(ref_units, stock_previous, products_available_preview):
    st.markdown(
        f"""
        <div class="decision-phase2-market-summary">
            <b>Predicción de ventas:</b> {_fmt_int_plain(ref_units)} uds.<br>
            <b>Stock acumulado anterior:</b> {_fmt_int_plain(stock_previous)} uds.<br>
            <b>Productos disponibles:</b> {_fmt_int_plain(products_available_preview)} uds.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_phase2_market_alert(price, quality_preview, dist):
    if price > 9.5 and quality_preview < 0.58:
        cls, icon, text = "warn", "!", "<b>El precio es relativamente alto respecto a la calidad.</b><br>Revisa la coherencia precio – calidad."
    elif dist < 45:
        cls, icon, text = "warn", "!", "<b>La distribución es limitada.</b><br>Puede frenar la conversión aunque la propuesta sea atractiva."
    else:
        cls, icon, text = "ok", "✓", "La configuración de mercado no muestra una alerta crítica inmediata."
    st.markdown(
        f"""
        <div class="decision-phase2-alert {cls}">
            <span class="decision-phase2-alert-icon">{icon}</span>
            <span>{text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )



def inject_decision_phase3_styles():
    """Estilos visuales para Mi decisión - Fase 3: Comunicación + Investigación."""
    st.markdown("""
    <style>
    .decision-phase3-head {
        display:flex;
        gap:13px;
        align-items:flex-start;
        padding:2px 0 14px 0;
        margin-bottom:14px;
        border-bottom:1px solid #EEF2F7;
    }
    .decision-phase3-icon {
        width:44px;
        height:44px;
        border-radius:13px;
        background:var(--soft-bg);
        color:var(--main-color);
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:1.35rem;
        flex:0 0 44px;
    }
    .decision-phase3-title {
        color:#071E49;
        font-size:1.02rem;
        line-height:1.12;
        font-weight:950;
        letter-spacing:-.02em;
        margin:0;
        text-transform:uppercase;
    }
    .decision-phase3-subtitle {
        color:#53657D;
        font-size:.82rem;
        line-height:1.35;
        font-weight:750;
        margin-top:4px;
    }
    .decision-phase3-comm-layout {
        display:grid;
        grid-template-columns:.95fr 1.05fr;
        gap:16px;
        align-items:start;
    }
    .decision-phase3-content [data-testid="stNumberInput"] label p,
    .decision-phase3-content [data-testid="stCheckbox"] label p {
        color:#071E49 !important;
        font-size:.82rem !important;
        font-weight:850 !important;
    }
    .decision-phase3-content div[data-baseweb="input"] > div {
        border-radius:10px !important;
        border-color:#DDE7F3 !important;
        background:#FAFCFF !important;
        min-height:39px !important;
    }
    .decision-phase3-total {
        background:#F4F8FE;
        border:1px solid #E2EAF5;
        border-radius:14px;
        padding:13px 15px;
        margin-top:12px;
        color:#071E49;
        font-size:.86rem;
        line-height:1.38;
        font-weight:850;
    }
    .decision-phase3-total b {
        color:#0A3472;
        font-weight:950;
    }
    .decision-phase3-mix-note {
        color:#53657D;
        font-size:.78rem;
        line-height:1.35;
        font-weight:750;
        margin-top:8px;
    }
    .decision-phase3-chartbox {
        background:#fff;
        border:1px solid #E3EAF2;
        border-radius:15px;
        padding:12px 12px 8px 12px;
        box-shadow:0 7px 20px rgba(9,30,66,.045);
        min-height:300px;
    }
    .decision-phase3-chart-title {
        color:#071E49;
        font-size:.90rem;
        line-height:1.12;
        font-weight:950;
        margin-bottom:4px;
    }
    .decision-phase3-research-list {
        display:grid;
        gap:10px;
    }
    .decision-phase3-research-caption {
        color:#64748B;
        font-size:.76rem;
        line-height:1.35;
        font-weight:700;
        margin:-5px 0 6px 29px;
    }
    .decision-phase3-research-total {
        background:#ECFDF3;
        border:1px solid #C7F2D6;
        border-radius:14px;
        padding:14px 16px;
        margin-top:16px;
        color:#067647;
        font-weight:950;
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:12px;
        font-size:.86rem;
    }
    .decision-phase3-research-final-note {
        background:#F8FAFC;
        border:1px solid #E3EAF2;
        border-radius:13px;
        padding:12px 14px;
        margin-top:12px;
        color:#53657D;
        font-size:.78rem;
        line-height:1.38;
        font-weight:750;
    }
    @media(max-width:1150px){
        .decision-phase3-comm-layout { grid-template-columns:1fr; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_decision_phase3_card_header(icon, title, subtitle, tone="purple"):
    palette = {
        "blue": ("#2563EB", "#EAF2FF"),
        "orange": ("#F59E0B", "#FFF4D8"),
        "green": ("#16A34A", "#EAF8EF"),
        "purple": ("#7C3AED", "#F1E9FF"),
        "red": ("#DC2626", "#FEECEC"),
    }
    color, soft = palette.get(tone, palette["purple"])
    st.markdown(
        f"""
        <div class="decision-phase3-head" style="--main-color:{color}; --soft-bg:{soft};">
            <div class="decision-phase3-icon">{_html_escape(icon)}</div>
            <div>
                <div class="decision-phase3-title">{_html_escape(title)}</div>
                <div class="decision-phase3-subtitle">{_html_escape(subtitle)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_comm_chart_phase3(comm_trad, comm_online, comm_rrss, comm_pr):
    labels = ["Tradicional", "Online", "RRSS", "RR.PP."]
    values = [float(comm_trad), float(comm_online), float(comm_rrss), float(comm_pr)]
    colors = ["#0F6BFF", "#60A5FA", "#EF4444", "#FCA5A5"]
    total = sum(values)

    fig = go.Figure()
    if total <= 0:
        fig.add_annotation(
            text="Sin inversión en comunicación.",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(color="#64748B", size=12),
        )
    else:
        fig.add_trace(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                sort=False,
                marker=dict(colors=colors, line=dict(color="white", width=3)),
                textinfo="percent",
                textposition="inside",
                insidetextfont=dict(size=12, color="white"),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} €<br>%{percent}<extra></extra>",
            )
        )
        fig.add_annotation(
            text=f"<b>{fmt_eur(total)}</b><br><span style='font-size:10px;color:#64748B'>total</span>",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color="#071E49", size=14),
        )

    fig.update_layout(
        height=230,
        margin=dict(l=0, r=0, t=0, b=34),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.04,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#071E49"),
            itemwidth=70,
        ),
        font=dict(family="Inter, Arial, sans-serif", color="#071E49"),
    )
    return fig



def render_decision_phase3_comm_summary(comm_trad, comm_online, comm_rrss, comm_pr):
    comm_total_preview = float(comm_trad + comm_online + comm_rrss + comm_pr)
    if comm_total_preview > 0:
        p_trad = comm_trad / comm_total_preview * 100
        p_online = comm_online / comm_total_preview * 100
        p_rrss = comm_rrss / comm_total_preview * 100
        p_pr = comm_pr / comm_total_preview * 100
        mix_text = f"Mix: Tradicional {p_trad:.0f}% · Online {p_online:.0f}% · RRSS {p_rrss:.0f}% · RR.PP. {p_pr:.0f}%"
    else:
        mix_text = "Mix: sin inversión asignada."
    st.markdown(
        f"""
        <div class="decision-phase3-total">
            <b>Comunicación total:</b> {fmt_eur(comm_total_preview)}
            <div class="decision-phase3-mix-note">{_html_escape(mix_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_phase3_research_total(research_cost_preview):
    st.markdown(
        f"""
        <div class="decision-phase3-research-total">
            <span>Coste total de investigación</span>
            <span>{fmt_eur(research_cost_preview)}</span>
        </div>
        <div class="decision-phase3-research-final-note">
            Los informes no cambian el mercado: reducen incertidumbre y mejoran la lectura estratégica.
        </div>
        """,
        unsafe_allow_html=True,
    )



def inject_decision_phase4_styles():
    """Estilos visuales para Mi decisión - Fase 4: Embudo de ventas."""
    st.markdown("""
    <style>
    .decision-phase4-section {
        background:#fff;
        border:1px solid #DDE7F3;
        border-radius:18px;
        padding:18px 20px 16px 20px;
        margin:18px 0;
        box-shadow:0 10px 28px rgba(9,30,66,.055);
    }
    .decision-phase4-head {
        display:flex;
        align-items:flex-start;
        justify-content:space-between;
        gap:14px;
        margin-bottom:14px;
    }
    .decision-phase4-title {
        color:#071E49;
        font-size:1.05rem;
        line-height:1.12;
        font-weight:950;
        letter-spacing:-.02em;
        text-transform:uppercase;
        margin:0;
    }
    .decision-phase4-subtitle {
        color:#53657D;
        font-size:.86rem;
        line-height:1.35;
        font-weight:700;
        margin-top:5px;
    }
    .decision-phase4-info {
        width:28px;
        height:28px;
        border-radius:50%;
        border:1px solid #BFD7FF;
        background:#EEF6FF;
        color:#0F6BFF;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:.86rem;
        font-weight:950;
        flex:0 0 28px;
    }
    .decision-phase4-layout {
        display:grid;
        grid-template-columns:1.35fr .95fr;
        gap:18px;
        align-items:stretch;
    }
    .decision-phase4-funnel {
        display:grid;
        gap:9px;
        padding:4px 0;
    }
    .decision-phase4-stage {
        display:grid;
        grid-template-columns:minmax(300px,1fr) 120px 90px;
        gap:14px;
        align-items:center;
    }
    .decision-phase4-shape {
        height:58px;
        color:#fff;
        display:flex;
        align-items:center;
        gap:14px;
        padding-left:26px;
        padding-right:28px;
        font-weight:950;
        clip-path:polygon(0 0,100% 0,88% 100%,12% 100%);
        box-shadow:inset 0 -8px 18px rgba(0,0,0,.10);
        position:relative;
        overflow:hidden;
    }
    .decision-phase4-shape:after {
        content:"";
        position:absolute;
        right:-26px;
        top:-38px;
        width:104px;
        height:104px;
        border-radius:999px;
        background:rgba(255,255,255,.14);
    }
    .decision-phase4-emoji {
        font-size:1.55rem;
        line-height:1;
        z-index:1;
    }
    .decision-phase4-label {
        z-index:1;
        font-size:.95rem;
        line-height:1.05;
    }
    .decision-phase4-label small {
        display:block;
        font-size:.68rem;
        font-weight:800;
        opacity:.88;
        margin-top:3px;
    }
    .decision-phase4-score {
        text-align:right;
        font-size:1.35rem;
        line-height:1.05;
        font-weight:950;
    }
    .decision-phase4-score small {
        display:block;
        color:#64748B;
        font-size:.70rem;
        line-height:1.2;
        font-weight:800;
        margin-top:4px;
    }
    .decision-phase4-level {
        display:flex;
        align-items:center;
        gap:8px;
        font-size:.74rem;
        font-weight:950;
        text-transform:uppercase;
        white-space:nowrap;
    }
    .decision-phase4-level-dot {
        width:12px;
        height:12px;
        border-radius:999px;
        display:inline-block;
        box-shadow:0 4px 10px rgba(9,30,66,.12);
    }
    .decision-phase4-explain {
        background:#fff;
        border:1px solid #E4EAF3;
        border-radius:16px;
        padding:17px 18px;
        min-height:270px;
        box-shadow:0 8px 22px rgba(9,30,66,.035);
    }
    .decision-phase4-explain h4 {
        color:#071E49;
        margin:0 0 12px 0;
        font-size:.88rem;
        font-weight:950;
        text-transform:uppercase;
    }
    .decision-phase4-explain p {
        margin:0 0 11px 0;
        color:#344054;
        line-height:1.35;
        font-size:.82rem;
        font-weight:700;
    }
    .decision-phase4-note {
        background:#F4F8FE;
        border:1px solid #DDE7F3;
        border-radius:12px;
        padding:10px 13px;
        color:#53657D;
        font-size:.78rem;
        font-weight:750;
        margin-top:12px;
    }
    @media(max-width:1200px){
        .decision-phase4-layout { grid-template-columns:1fr; }
        .decision-phase4-stage { grid-template-columns:1fr; gap:5px; }
        .decision-phase4-score { text-align:left; }
    }
    </style>
    """, unsafe_allow_html=True)


def _decision_phase4_level(score):
    score = float(score)
    if score >= 67:
        return "Alto", "#159A63"
    if score >= 45:
        return "Medio", "#F59E0B"
    return "Bajo", "#EF4444"


def _decision_phase4_stage_text(score, stage):
    level, _ = _decision_phase4_level(score)
    if stage == "Conocimiento":
        return "del mercado objetivo" if level == "Alto" else "de visibilidad estimada"
    if stage == "Consideración":
        return "de las personas alcanzadas"
    if stage == "Compra":
        return "de las personas consideradas"
    return "de los clientes actuales"


def render_decision_phase4_funnel(knowledge_score, consideration_score, purchase_score, retention_score):
    stages = [
        ("📣", "Conocimiento", "Awareness", float(knowledge_score), "#4285F4"),
        ("👥", "Consideración", "Consideration", float(consideration_score), "#F9A825"),
        ("🛒", "Compra", "Purchase", float(purchase_score), "#4CAF72"),
        ("♡", "Retención", "Retention", float(retention_score), "#8755D9"),
    ]
    rows = []
    for icon, title, subtitle, score, color in stages:
        level, level_color = _decision_phase4_level(score)
        stage_text = _decision_phase4_stage_text(score, title)
        rows.append(
            "<div class='decision-phase4-stage'>"
            f"<div class='decision-phase4-shape' style='background:{color};'>"
            f"<span class='decision-phase4-emoji'>{_html_escape(icon)}</span>"
            f"<span class='decision-phase4-label'>{_html_escape(title)}<small>({_html_escape(subtitle)})</small></span>"
            "</div>"
            f"<div class='decision-phase4-score' style='color:{color};'>{score:.0f}%<small>{_html_escape(stage_text)}</small></div>"
            f"<div class='decision-phase4-level' style='color:{level_color};'>"
            f"<span class='decision-phase4-level-dot' style='background:{level_color};'></span>{_html_escape(level)}"
            "</div>"
            "</div>"
        )
    return "<div class='decision-phase4-funnel'>" + "".join(rows) + "</div>"


def render_decision_phase4_explanation():
    return (
        "<div class='decision-phase4-explain'>"
        "<h4>¿Qué influye en cada fase?</h4>"
        "<p><b style='color:#4285F4;'>● Conocimiento:</b><br>Combina notoriedad previa, comunicación actual, base retenida, satisfacción y cuota previa.</p>"
        "<p><b style='color:#F9A825;'>● Consideración:</b><br>Depende de conocimiento, producto, posicionamiento, precio, distribución, satisfacción y coherencia.</p>"
        "<p><b style='color:#4CAF72;'>● Compra:</b><br>Mide fuerza comercial: consideración, precio, promoción, distribución, online, posicionamiento y disponibilidad.</p>"
        "<p><b style='color:#8755D9;'>● Retención:</b><br>Combina satisfacción acumulada, calidad, fiabilidad, coherencia, relación con clientes y distribución.</p>"
        "</div>"
    )


def render_decision_phase4_section(knowledge_score, consideration_score, purchase_score, retention_score):
    funnel_html = render_decision_phase4_funnel(knowledge_score, consideration_score, purchase_score, retention_score)
    explanation_html = render_decision_phase4_explanation()
    html = (
        "<div class='decision-phase4-section'>"
        "<div class='decision-phase4-head'>"
        "<div>"
        "<div class='decision-phase4-title'>5. Impacto estimado en el embudo de ventas</div>"
        "<div class='decision-phase4-subtitle'>Este embudo muestra la fuerza estimada de tu marca en cada fase, combinando la situación acumulada de la marca con la estrategia que estás diseñando.</div>"
        "</div>"
        "<div class='decision-phase4-info'>i</div>"
        "</div>"
        "<div class='decision-phase4-layout'>"
        f"{funnel_html}"
        f"{explanation_html}"
        "</div>"
        "<div class='decision-phase4-note'>ⓘ Los porcentajes representan fuerza estimada, no ventas garantizadas. Una marca puede tener alto conocimiento y no convertir si falla precio, producto, distribución o coherencia.</div>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)



def inject_decision_phase5_styles():
    """Estilos visuales para Mi decisión - Fase 5: diagnóstico + envío."""
    st.markdown("""
    <style>
    .decision-phase5-section {
        margin:18px 0 10px 0;
    }
    .decision-phase5-title {
        color:#071E49;
        font-size:1.08rem;
        line-height:1.12;
        font-weight:950;
        letter-spacing:-.02em;
        text-transform:uppercase;
        margin:0 0 5px 0;
    }
    .decision-phase5-subtitle {
        color:#53657D;
        font-size:.86rem;
        line-height:1.35;
        font-weight:700;
        margin-bottom:12px;
    }
    .decision-phase5-grid {
        display:grid;
        grid-template-columns:repeat(3,minmax(0,1fr));
        gap:16px;
        align-items:stretch;
        margin-bottom:16px;
    }
    .decision-phase5-card {
        border-radius:17px;
        border:1px solid;
        padding:18px 20px;
        min-height:158px;
        box-shadow:0 9px 24px rgba(9,30,66,.045);
        position:relative;
        overflow:hidden;
    }
    .decision-phase5-card:after {
        content:"";
        position:absolute;
        right:-36px;
        top:-46px;
        width:112px;
        height:112px;
        border-radius:999px;
        opacity:.32;
        background:currentColor;
    }
    .decision-phase5-card h4 {
        margin:0 0 12px 0;
        color:#071E49;
        font-size:.79rem;
        line-height:1.15;
        font-weight:950;
        text-transform:uppercase;
        letter-spacing:.02em;
        display:flex;
        gap:9px;
        align-items:center;
    }
    .decision-phase5-main {
        font-size:1.22rem;
        line-height:1.12;
        font-weight:950;
        margin-bottom:8px;
        position:relative;
        z-index:1;
    }
    .decision-phase5-card p {
        color:#344054;
        font-size:.84rem;
        line-height:1.38;
        font-weight:720;
        margin:0 0 12px 0;
        position:relative;
        z-index:1;
    }
    .decision-phase5-pill {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        border-radius:999px;
        padding:7px 13px;
        font-size:.76rem;
        font-weight:900;
        position:relative;
        z-index:1;
    }
    .decision-phase5-dots {
        letter-spacing:6px;
        font-size:1.34rem;
        line-height:1;
        position:relative;
        z-index:1;
    }
    .decision-phase5-card ul {
        margin:0;
        padding-left:1.05rem;
        position:relative;
        z-index:1;
    }
    .decision-phase5-card li {
        color:#344054;
        font-size:.84rem;
        line-height:1.38;
        font-weight:720;
        margin-bottom:7px;
    }
    .decision-phase5-purple {
        background:#F7F2FF;
        border-color:#E8D8FF;
        color:#7C3AED;
    }
    .decision-phase5-purple .decision-phase5-pill {
        background:#E9D5FF;
        color:#6D28D9;
    }
    .decision-phase5-green {
        background:#F1FAF3;
        border-color:#D6F0DA;
        color:#159A63;
    }
    .decision-phase5-orange {
        background:#FFF7ED;
        border-color:#FFD8A8;
        color:#F59E0B;
    }

    .decision-phase5-submit {
        background:#fff;
        border:1px solid #DDE7F3;
        border-radius:18px;
        padding:16px 18px 18px 18px;
        box-shadow:0 10px 28px rgba(9,30,66,.055);
        margin:10px 0 6px 0;
    }
    .decision-phase5-submit-title {
        color:#071E49;
        font-size:1.04rem;
        line-height:1.12;
        font-weight:950;
        letter-spacing:-.02em;
        text-transform:uppercase;
        margin-bottom:10px;
        display:flex;
        gap:9px;
        align-items:center;
    }
    .decision-phase5-ready {
        border-radius:13px;
        padding:12px 15px;
        margin-bottom:12px;
        display:flex;
        gap:10px;
        align-items:center;
        font-size:.84rem;
        line-height:1.35;
        font-weight:900;
        border:1px solid;
    }
    .decision-phase5-ready.ok {
        background:#ECFDF3;
        color:#067647;
        border-color:#C7F2D6;
    }
    .decision-phase5-ready.bad {
        background:#FEECEC;
        color:#B42318;
        border-color:#FECACA;
    }
    .decision-phase5-ready-icon {
        width:24px;
        height:24px;
        border-radius:999px;
        background:currentColor;
        color:white;
        display:inline-flex;
        align-items:center;
        justify-content:center;
        flex:0 0 24px;
        font-size:.74rem;
        font-weight:950;
    }
    .decision-phase5-submit-note {
        background:#F4F8FE;
        border:1px solid #DDE7F3;
        border-radius:12px;
        padding:10px 13px;
        color:#53657D;
        font-size:.78rem;
        font-weight:750;
        line-height:1.35;
        margin-top:12px;
    }
    @media(max-width:1200px){
        .decision-phase5-grid { grid-template-columns:1fr; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_decision_phase5_diagnostic(strategy_label, coherence_label, warnings):
    desc, pill = _strategy_description(strategy_label)
    coh_main, coh_desc, coh_color = _coherence_description(coherence_label)
    warn_items = warnings[:3] if warnings else ["No aparecen alertas críticas con la decisión actual."]
    warn_html = "".join(f"<li>{_html_escape(w)}</li>" for w in warn_items)

    # Nivel visual de coherencia manteniendo el formato de puntos de la maqueta.
    active_map = {"Alta": 5, "Media": 3, "Baja": 1}
    active = active_map.get(coherence_label, 3)
    dots = "".join(
        f"<span style='opacity:{'1' if i < active else '.25'};'>●</span>"
        for i in range(5)
    )

    html = (
        "<div class='decision-phase5-section'>"
        "<div class='decision-phase5-title'>6. Diagnóstico estratégico</div>"
        "<div class='decision-phase5-subtitle'>Interpretación global de tu estrategia actual.</div>"
        "<div class='decision-phase5-grid'>"
        "<div class='decision-phase5-card decision-phase5-purple'>"
        "<h4>🎯 Orientación estratégica detectada</h4>"
        f"<div class='decision-phase5-main'>Orientación a {_html_escape(str(strategy_label).lower())}</div>"
        f"<p>{_html_escape(desc)}</p>"
        f"<div class='decision-phase5-pill'>{_html_escape(pill)}</div>"
        "</div>"
        "<div class='decision-phase5-card decision-phase5-green'>"
        "<h4>⚖️ Coherencia estratégica</h4>"
        f"<div class='decision-phase5-main' style='color:{coh_color};'>{_html_escape(coh_main)}</div>"
        f"<p>{_html_escape(coh_desc)}</p>"
        f"<div class='decision-phase5-dots' style='color:{coh_color};'>{dots}</div>"
        "</div>"
        "<div class='decision-phase5-card decision-phase5-orange'>"
        "<h4>⚠️ Alertas estratégicas</h4>"
        f"<ul>{warn_html}</ul>"
        "</div>"
        "</div>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_decision_phase5_submit_block(estimated_budget_remaining):
    is_ok = estimated_budget_remaining >= 0
    cls = "ok" if is_ok else "bad"
    icon = "✓" if is_ok else "!"
    text = (
        "La decisión está lista para enviarse. Revisa los datos y envíalos cuando estés preparado."
        if is_ok
        else f"Tu presupuesto estimado está excedido. Ajusta la decisión antes de enviarla. Exceso: {fmt_eur(abs(estimated_budget_remaining))}."
    )
    st.markdown(
        f"""
        <div class="decision-phase5-submit">
            <div class="decision-phase5-submit-title">7. Envío de la decisión 🔗</div>
            <div class="decision-phase5-ready {cls}">
                <span class="decision-phase5-ready-icon">{icon}</span>
                <span>{_html_escape(text)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_decision_payload(game_id, team, teams, engine, available_budget, round_n, state):
    inject_decision_pro_styles()
    inject_decision_phase1_styles()
    inject_decision_phase2_styles()
    inject_decision_phase3_styles()
    inject_decision_phase4_styles()
    inject_decision_phase5_styles()

    existing_entry = get_decision(game_id, team, round_n)
    existing = existing_entry["decision"] if existing_entry else {}
    ref_units = estimate_reference_units(team, teams, engine)

    price_default = float(existing.get("price", 8.0))
    promo_default = int(round(float(existing.get("promo", 0.06)) * 100))
    dist_default = int(round(float(existing.get("distribution", 0.75)) * 100))
    perf_default = int(round(float(existing.get("product_perf", 0.50)) * 100))
    design_default = int(round(float(existing.get("product_design", 0.50)) * 100))
    reliability_default = int(round(float(existing.get("product_reliability", 0.50)) * 100))
    research_existing = existing.get("research", {})

    phase1_spend, phase1_remaining, phase1_reports_count, phase1_research_cost = compute_decision_phase1_preview(
        game_id=game_id,
        team=team,
        round_n=round_n,
        available_budget=available_budget,
        ref_units=ref_units,
        engine=engine,
        teams=teams,
        existing=existing,
        research_existing=research_existing,
    )
    render_decision_phase1_header_and_kpis(
        round_n=round_n,
        available_budget=available_budget,
        planned_spend=phase1_spend,
        selected_reports_count=phase1_reports_count,
        research_cost=phase1_research_cost,
        remaining_budget=phase1_remaining,
    )

    input_row_1 = st.columns(2)

    with input_row_1[0]:
        with st.container(border=True):
            render_decision_phase2_card_header("📦", "1. Producto", "Invierte en las características de tu producto.", "blue")
            product_perf = st.slider("Rendimiento (%)", 0, 100, perf_default, key=f"dec_perf_{game_id}_{team}_{round_n}")
            product_design = st.slider("Diseño (%)", 0, 100, design_default, key=f"dec_design_{game_id}_{team}_{round_n}")
            product_reliability = st.slider("Fiabilidad (%)", 0, 100, reliability_default, key=f"dec_rel_{game_id}_{team}_{round_n}")
            quality_preview = 0.40 * (product_perf / 100) + 0.25 * (product_design / 100) + 0.35 * (product_reliability / 100)
            render_decision_phase2_quality_box(quality_preview)

    with input_row_1[1]:
        with st.container(border=True):
            render_decision_phase2_card_header("🏷️", "2. Mercado (go-to-market)", "Decisiones sobre precio, promoción y distribución.", "orange")
            price = st.number_input("Precio de venta por unidad (€)", 5.0, 15.0, price_default, step=0.1, key=f"dec_price_{game_id}_{team}_{round_n}")
            promo = st.slider("Promoción (% sobre precio)", 0, 30, promo_default, key=f"dec_promo_{game_id}_{team}_{round_n}")
            dist = st.slider("Distribución (% cobertura mercado)", 5, 100, dist_default, key=f"dec_dist_{game_id}_{team}_{round_n}")
            team_idx_for_stock = get_team_index(team, teams)
            stock_acumulado_anterior = float(getattr(engine, "inventory", [0] * len(teams))[team_idx_for_stock])
            production_default = int(round(float(existing.get("production_units", max(ref_units * 1.05 - stock_acumulado_anterior, 0.0)))))
            production_units = st.number_input(
                "Unidades a fabricar",
                min_value=0,
                max_value=2_000_000,
                value=max(0, production_default),
                step=500,
                key=f"dec_production_{game_id}_{team}_{round_n}",
            )
            products_available_preview = float(production_units) + stock_acumulado_anterior
            render_decision_phase2_market_summary(ref_units, stock_acumulado_anterior, products_available_preview)
            render_decision_phase2_market_alert(price, quality_preview, dist)

    input_row_2 = st.columns(2)

    with input_row_2[0]:
        with st.container(border=True):
            render_decision_phase3_card_header("📣", "3. Comunicación", "Invierte para construir marca y generar demanda.", "purple")
            c_comm_inputs, c_comm_chart = st.columns([0.88, 1.12])
            with c_comm_inputs:
                comm_trad = st.number_input("Medios tradicionales (€)", min_value=0, max_value=200000, value=int(existing.get("comm_trad", 4000)), step=1000, key=f"dec_trad_{game_id}_{team}_{round_n}")
                comm_online = st.number_input("Publicidad online (€)", min_value=0, max_value=200000, value=int(existing.get("comm_online", 4000)), step=1000, key=f"dec_online_{game_id}_{team}_{round_n}")
                comm_rrss = st.number_input("Redes sociales (€)", min_value=0, max_value=200000, value=int(existing.get("comm_rrss", 2000)), step=1000, key=f"dec_rrss_{game_id}_{team}_{round_n}")
                comm_pr = st.number_input("Relaciones públicas (€)", min_value=0, max_value=200000, value=int(existing.get("comm_pr", 2000)), step=1000, key=f"dec_pr_{game_id}_{team}_{round_n}")
                render_decision_phase3_comm_summary(comm_trad, comm_online, comm_rrss, comm_pr)
            with c_comm_chart:
                st.markdown('<div class="decision-phase3-chart-title">Mix de comunicación</div>', unsafe_allow_html=True)
                st.plotly_chart(
                    build_comm_chart_phase3(comm_trad, comm_online, comm_rrss, comm_pr),
                    use_container_width=True,
                    config={"displayModeBar": False, "responsive": True},
                )
                st.markdown(
                    '<div class="decision-phase3-mix-note">Los canales impactan de forma distinta en cada fase del embudo.</div>',
                    unsafe_allow_html=True,
                )

    with input_row_2[1]:
        with st.container(border=True):
            render_decision_phase3_card_header("📋", "4. Investigación de mercado", "Selecciona los informes que quieres comprar.", "green")
            buy_segments = st.checkbox("Informe de segmentos (5.000 €)", value=bool(research_existing.get("segments", False)), key=f"dec_segments_{game_id}_{team}_{round_n}")
            st.markdown('<div class="decision-phase3-research-caption">Tamaño de cada segmento, reparto de compra por segmento y lectura de oportunidad.</div>', unsafe_allow_html=True)

            buy_competition = st.checkbox("Informe competitivo (4.000 €)", value=bool(research_existing.get("competition", False)), key=f"dec_comp_{game_id}_{team}_{round_n}")
            st.markdown('<div class="decision-phase3-research-caption">Lectura aproximada de precio, promoción, distribución y comunicación de los rivales.</div>', unsafe_allow_html=True)

            buy_brand_product = st.checkbox("Informe de marca y producto (4.000 €)", value=bool(research_existing.get("brand_product", False)), key=f"dec_brand_{game_id}_{team}_{round_n}")
            st.markdown('<div class="decision-phase3-research-caption">Mapa calidad-precio, atributos estimados, coherencia percibida y posicionamiento.</div>', unsafe_allow_html=True)

            research_cost_preview = estimate_research_cost(buy_segments, buy_competition, buy_brand_product)
            render_decision_phase3_research_total(research_cost_preview)

    product_perf_value = product_perf / 100.0
    product_design_value = product_design / 100.0
    product_reliability_value = product_reliability / 100.0
    promo_value = promo / 100.0
    dist_value = dist / 100.0
    comm_total = float(comm_trad + comm_online + comm_rrss + comm_pr)

    quality_value = 0.40 * product_perf_value + 0.25 * product_design_value + 0.35 * product_reliability_value
    research_cost = estimate_research_cost(buy_segments, buy_competition, buy_brand_product)
    base_unit_cost, final_unit_cost = estimate_unit_cost(engine, team, teams, product_perf_value, product_design_value, product_reliability_value)
    estimated_production_cost = final_unit_cost * float(production_units)
    estimated_product_investment_cost_value = globals()["estimate_product_investment_cost"](product_perf_value, product_design_value, product_reliability_value)
    estimated_promo_cost = promo_value * price * ref_units * 0.55
    estimated_dist_cost = 1500 * dist_value + 2500 * (dist_value ** 2)
    estimated_budget_used = comm_total + estimated_promo_cost + estimated_dist_cost + estimated_product_investment_cost_value + research_cost
    estimated_budget_remaining = available_budget - estimated_budget_used
    selected_reports_count = int(buy_segments) + int(buy_competition) + int(buy_brand_product)

    strategy_label = get_strategy_label(price, promo_value, dist_value, product_design_value, product_reliability_value, comm_online, comm_pr, comm_trad)
    coherence_label = get_coherence_label(price, quality_value, promo_value, dist_value, estimated_budget_remaining)
    warnings = build_warnings(price, quality_value, promo_value, dist_value, comm_online, comm_trad, comm_rrss, comm_pr, strategy_label, estimated_budget_remaining)

    # Funnel de fuerza estimada de marca:
    # combina memoria acumulada de la marca + la decisión actual.
    funnel_decision = {
        "price": float(price),
        "promo": float(promo_value),
        "distribution": float(dist_value),
        "production_units": float(production_units),
        "products_available": float(products_available_preview),
        "estimated_units_for_budget": float(ref_units),
        "product_perf": float(product_perf_value),
        "product_design": float(product_design_value),
        "product_reliability": float(product_reliability_value),
        "quality": float(quality_value),
        "comm_trad": float(comm_trad),
        "comm_online": float(comm_online),
        "comm_rrss": float(comm_rrss),
        "comm_pr": float(comm_pr),
    }

    if hasattr(engine, "estimate_brand_funnel_strength"):
        funnel_strength = engine.estimate_brand_funnel_strength(team, funnel_decision)
        knowledge_score = funnel_strength["knowledge"]
        consideration_score = funnel_strength["consideration"]
        purchase_score = funnel_strength["purchase"]
        retention_score = funnel_strength["retention"]
    else:
        # Compatibilidad con motores antiguos.
        knowledge_score, consideration_score, purchase_score, retention_score = compute_funnel_strength_scores(
            price=price,
            promo_value=promo_value,
            dist_value=dist_value,
            quality_value=quality_value,
            product_perf_value=product_perf_value,
            product_design_value=product_design_value,
            product_reliability_value=product_reliability_value,
            comm_trad=comm_trad,
            comm_online=comm_online,
            comm_rrss=comm_rrss,
            comm_pr=comm_pr,
            comm_total=comm_total,
            coherence_label=coherence_label,
        )

    budget_pct = (estimated_budget_used / max(float(available_budget), 1.0)) * 100

    render_decision_phase4_section(knowledge_score, consideration_score, purchase_score, retention_score)

    render_decision_phase5_diagnostic(strategy_label, coherence_label, warnings)

    render_decision_phase5_submit_block(estimated_budget_remaining)

    mix_total_for_legacy = comm_total if comm_total > 0 else 1.0
    payload = {
        "price": float(price), "promo": float(promo_value), "distribution": float(dist_value), "production_units": float(production_units),
        "product_perf": float(product_perf_value), "product_design": float(product_design_value), "product_reliability": float(product_reliability_value), "quality": float(quality_value),
        "comm_trad": float(comm_trad), "comm_online": float(comm_online), "comm_rrss": float(comm_rrss), "comm_pr": float(comm_pr), "comm_total": float(comm_total),
        "comm_mix": {"trad": float(comm_trad / mix_total_for_legacy), "online": float(comm_online / mix_total_for_legacy), "rrss": float(comm_rrss / mix_total_for_legacy), "pr": float(comm_pr / mix_total_for_legacy)},
        "research": {"segments": bool(buy_segments), "competition": bool(buy_competition), "brand_product": bool(buy_brand_product)},
        "research_cost": float(research_cost), "budget_available": float(available_budget), "estimated_units_for_budget": float(ref_units), "stock_acumulado_anterior": float(stock_acumulado_anterior), "products_available": float(products_available_preview),
        "estimated_promo_cost": float(estimated_promo_cost), "estimated_dist_cost": float(estimated_dist_cost), "estimated_product_investment_cost": float(estimated_product_investment_cost_value), "estimated_quality_investment_cost": float(estimated_product_investment_cost_value),
        "estimated_unit_cost": float(final_unit_cost), "estimated_production_cost": float(estimated_production_cost), "budget_estimated_used": float(estimated_budget_used), "budget_estimated_remaining": float(estimated_budget_remaining),
    }
    return payload, estimated_budget_remaining


# =========================================================
# VISTAS DEL EQUIPO
# =========================================================
def inject_dashboard_styles():
    """Estilos visuales PRO para el dashboard de resumen."""
    st.markdown(
        """
        <style>
        .summary-page { width:100%; }
        .summary-topbar { display:flex; justify-content:space-between; align-items:center; margin:.15rem 0 1.05rem 0; }
        .summary-title-wrap { display:flex; align-items:center; gap:14px; }
        .summary-title-icon { width:52px; height:52px; border-radius:14px; background:#FFFFFF; border:1px solid #DDE7F3; box-shadow:0 8px 22px rgba(9,30,66,.055); display:flex; align-items:center; justify-content:center; font-size:1.65rem; color:#071E49; }
        .summary-title { color:#071E49; font-size:1.72rem; font-weight:950; line-height:1.05; letter-spacing:-.035em; margin:0; }
        .summary-subtitle { color:#53657D; font-size:.86rem; font-weight:650; margin-top:7px; }
        .summary-chips { display:flex; gap:12px; align-items:center; }
        .summary-chip { background:#fff; border:1px solid #DDE7F3; border-radius:14px; padding:12px 18px; color:#071E49; font-size:.88rem; font-weight:850; box-shadow:0 6px 18px rgba(9,30,66,.035); white-space:nowrap; }
        .summary-chip b { color:#071E49; }
        .summary-grid-4 { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:16px; margin-bottom:16px; }
        .summary-grid-3 { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:16px; margin-bottom:16px; }
        .summary-grid-2 { display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:16px; margin-bottom:16px; }
        .summary-kpi-card { background:#FFFFFF; border:1px solid #DDE7F3; border-radius:14px; padding:16px 18px; min-height:116px; box-shadow:0 8px 24px rgba(9,30,66,.045); display:flex; gap:14px; align-items:center; overflow:hidden; }
        .summary-kpi-row-4 { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:14px; margin:0 0 14px 0; }
        .summary-kpi-row-3 { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:14px; margin:0 0 16px 0; }
        .summary-kpi-content { min-width:0; }
        .summary-icon-circle { width:58px; height:58px; border-radius:50%; flex:0 0 58px; color:#fff; display:flex; align-items:center; justify-content:center; font-size:1.55rem; font-weight:900; box-shadow:0 10px 22px rgba(9,30,66,.10); }
        .summary-icon-soft { width:60px; height:60px; border-radius:50%; flex:0 0 60px; display:flex; align-items:center; justify-content:center; font-size:1.55rem; font-weight:900; }
        .summary-kpi-label { color:#071E49; font-size:.82rem; font-weight:950; line-height:1.15; margin-bottom:7px; }
        .summary-kpi-value { color:#060B2A; font-size:1.55rem; line-height:1.05; font-weight:950; letter-spacing:-.03em; white-space:nowrap; }
        .summary-kpi-note { color:#071E49; opacity:.72; font-size:.76rem; font-weight:650; margin-top:7px; line-height:1.25; }
        .summary-kpi-delta { color:#05943B; font-size:.74rem; font-weight:900; margin-top:8px; }
        .summary-chart-card { background:#FFFFFF; border:1px solid #DDE7F3; border-radius:14px; padding:16px 18px 12px 18px; min-height:330px; box-shadow:0 8px 24px rgba(9,30,66,.045); }
        .summary-card-title { display:flex; align-items:center; gap:9px; color:#071E49; font-size:1.02rem; font-weight:950; margin-bottom:8px; }
        .summary-insight-card { border-radius:14px; padding:20px 23px; min-height:144px; border:1px solid transparent; box-shadow:0 6px 18px rgba(9,30,66,.035); }
        .summary-insight-title { display:flex; align-items:center; gap:12px; font-size:1.35rem; line-height:1.1; font-weight:950; margin-bottom:16px; }
        .summary-insight-card ul { margin:0; padding-left:0; list-style:none; color:#071E49; font-size:.91rem; font-weight:600; line-height:1.55; }
        .summary-insight-card li { margin-bottom:9px; display:flex; gap:10px; align-items:flex-start; }
        .summary-good { background:#F0FBF4; border-color:#BFEBD0; color:#07933F; }
        .summary-bad { background:#FFF1F1; border-color:#F8C6C6; color:#C91515; }
        .summary-improve { background:#FFF8E8; border-color:#F6DCA8; color:#C87500; }
        .summary-advice { background:#EEF6FF; border:1px solid #CFE3FF; border-radius:12px; padding:13px 17px; color:#0F6BFF; font-size:.86rem; font-weight:650; margin-top:2px; }
        .summary-empty { background:#fff; border:1px dashed #CBD5E1; border-radius:14px; padding:24px; color:#53657D; }
        @media (max-width: 1150px) { .summary-grid-4, .summary-grid-3, .summary-grid-2, .summary-kpi-row-4, .summary-kpi-row-3 { grid-template-columns:1fr; } .summary-topbar { flex-direction:column; align-items:flex-start; gap:12px; } .summary-chips { flex-wrap:wrap; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_visual_card(label, value, note="", tone="info", icon="•", delta="", soft=False):
    """Tarjeta KPI del resumen. Versión sin HTML indentado para evitar que Streamlit muestre etiquetas como texto."""
    palette = {
        "blue": ("#0F6BFF", "#EAF2FF"),
        "purple": ("#7C3AED", "#F1E9FF"),
        "green": ("#16A34A", "#EAF8EF"),
        "teal": ("#06A7B4", "#E6FAFB"),
        "orange": ("#F59E0B", "#FFF4D8"),
        "mint": ("#25B987", "#E7F8F2"),
        "info": ("#0F6BFF", "#EAF2FF"),
        "positive": ("#16A34A", "#EAF8EF"),
        "warning": ("#F59E0B", "#FFF4D8"),
        "danger": ("#DC2626", "#FEECEC"),
    }
    color, soft_bg = palette.get(tone, palette["info"])
    icon_cls = "summary-icon-soft" if soft else "summary-icon-circle"
    bg_style = f"background:{soft_bg}; color:{color};" if soft else f"background:{color};"
    delta_html = f'<div class="summary-kpi-delta">{_html_escape(delta)}</div>' if delta else ""
    html = (
        f'<div class="summary-kpi-card">'
        f'<div class="{icon_cls}" style="{bg_style}">{_html_escape(icon)}</div>'
        f'<div class="summary-kpi-content">'
        f'<div class="summary-kpi-label">{_html_escape(label)}</div>'
        f'<div class="summary-kpi-value">{value}</div>'
        f'{delta_html}'
        f'<div class="summary-kpi-note">{_html_escape(note)}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)




def _summary_card_html(label, value, note="", tone="info", icon="•", delta="", soft=False):
    """Devuelve HTML de una tarjeta KPI para renderizar filas como grid estable."""
    palette = {
        "blue": ("#0F6BFF", "#EAF2FF"),
        "purple": ("#7C3AED", "#F1E9FF"),
        "green": ("#16A34A", "#EAF8EF"),
        "teal": ("#06A7B4", "#E6FAFB"),
        "orange": ("#F59E0B", "#FFF4D8"),
        "mint": ("#25B987", "#E7F8F2"),
        "info": ("#0F6BFF", "#EAF2FF"),
        "positive": ("#16A34A", "#EAF8EF"),
        "warning": ("#F59E0B", "#FFF4D8"),
        "danger": ("#DC2626", "#FEECEC"),
    }
    color, soft_bg = palette.get(tone, palette["info"])
    icon_cls = "summary-icon-soft" if soft else "summary-icon-circle"
    bg_style = f"background:{soft_bg}; color:{color};" if soft else f"background:{color};"
    delta_html = f'<div class="summary-kpi-delta">{_html_escape(delta)}</div>' if delta else ""
    return (
        f'<div class="summary-kpi-card">'
        f'<div class="{icon_cls}" style="{bg_style}">{_html_escape(icon)}</div>'
        f'<div class="summary-kpi-content">'
        f'<div class="summary-kpi-label">{_html_escape(label)}</div>'
        f'<div class="summary-kpi-value">{value}</div>'
        f'{delta_html}'
        f'<div class="summary-kpi-note">{_html_escape(note)}</div>'
        f'</div>'
        f'</div>'
    )


def render_summary_card_grid(cards, columns=4):
    """Renderiza KPIs en una sola rejilla HTML para evitar desalineaciones de columnas Streamlit."""
    cls = "summary-kpi-row-4" if columns == 4 else "summary-kpi-row-3"
    html = f'<div class="{cls}">' + "".join(_summary_card_html(**card) for card in cards) + '</div>'
    st.markdown(html, unsafe_allow_html=True)

def build_team_quick_reading(team_truth, current_team_budget):
    """Genera una lectura breve y estratégica de la última ronda."""
    profit = float(team_truth.get("profit", 0.0))
    share = float(team_truth.get("share", 0.0))
    units = float(team_truth.get("units", 0.0))
    demand = float(team_truth.get("demand_potential", units))
    stock_final = float(team_truth.get("inventory_final", 0.0))
    stockout = float(team_truth.get("stockout_units", max(0.0, demand - units)))
    fulfilment = float(team_truth.get("fulfilment_rate", 1.0 if demand <= 0 else units / max(demand, 1.0)))
    awareness = float(team_truth.get("awareness_true", 0.0))
    quality = float(team_truth.get("quality", 0.0))
    distribution = float(team_truth.get("distribution", 0.0))
    retention = float(team_truth.get("retention_rate", 0.0))

    if profit > 0 and fulfilment >= 0.95:
        best = "Has cerrado la ronda con beneficio positivo y has cubierto prácticamente toda la demanda generada."
    elif profit > 0:
        best = "Has cerrado la ronda con beneficio positivo, lo que aumenta tu capacidad de inversión para la siguiente ronda."
    elif share >= 0.25:
        best = "Aunque el beneficio no ha sido fuerte, has conseguido una presencia relevante en cuota de mercado."
    elif quality >= 0.65:
        best = "Tu producto tiene una base sólida; puede ayudarte a construir mejor posicionamiento y retención."
    elif awareness >= 0.45:
        best = "Tu marca empieza a tener un nivel de conocimiento relevante en el mercado."
    else:
        best = "Has generado información útil para ajustar mejor tu estrategia en la siguiente ronda."

    if stockout > 0:
        weak = "La principal debilidad ha sido la falta de stock: había más demanda potencial de la que pudiste atender."
    elif stock_final > max(demand * 0.25, 1.0):
        weak = "Has acumulado bastante stock, señal de que la producción ha quedado por encima de la demanda real."
    elif profit < 0:
        weak = "La ronda ha terminado con pérdidas; los costes han superado los ingresos generados."
    elif share < 0.12:
        weak = "Tu cuota de mercado sigue siendo baja frente al conjunto de competidores."
    elif distribution < 0.45:
        weak = "La distribución parece limitada y puede estar frenando la conversión de la demanda."
    elif awareness < 0.25:
        weak = "El conocimiento de marca todavía es bajo, lo que limita la entrada de nuevos clientes."
    else:
        weak = "No aparece una debilidad crítica, pero aún hay margen para optimizar la relación entre ventas, costes y posicionamiento."

    if stockout > 0:
        improve = "Ajusta mejor la producción a la previsión de ventas para no perder demanda por falta de inventario."
    elif stock_final > max(demand * 0.25, 1.0):
        improve = "Reduce o afina la fabricación de la próxima ronda si no esperas un crecimiento claro de la demanda."
    elif profit < 0:
        improve = "Revisa margen, costes de fabricación, comunicación y promoción para volver a beneficio positivo."
    elif share < 0.12:
        improve = "Refuerza los motores de demanda: comunicación, distribución, producto y coherencia de precio."
    elif retention > 0 and retention < 0.45:
        improve = "Trabaja la retención con mejor calidad, fiabilidad, coherencia estratégica y experiencia de marca."
    else:
        improve = "Puedes seguir optimizando la estrategia para aumentar beneficio sin disparar costes ni acumular stock innecesario."

    return best, weak, improve


def render_team_profit_chart(team, history):
    """Gráfico PRO de evolución de beneficio: solo rondas reales, línea suavizada y etiquetas limpias."""
    fig = go.Figure()
    rows = []

    for round_data in history or []:
        rnum = round_data.get("round")
        for row in round_data.get("truth", []) or []:
            if row.get("team") == team:
                rows.append({
                    "round": rnum,
                    "round_label": f"Ronda {rnum}",
                    "profit": float(row.get("profit", 0.0)),
                })

    if not rows:
        fig.add_annotation(
            text="Aún no hay histórico de beneficios disponible.",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(color="#64748B", size=13),
        )
    else:
        df = pd.DataFrame(rows).sort_values("round")
        x_labels = df["round_label"].tolist()
        y_values = df["profit"].tolist()
        point_text = [fmt_eur(v) for v in y_values]

        # Área suave bajo la línea para aspecto dashboard.
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_values,
            mode="lines",
            line=dict(color="rgba(124,58,237,0)", width=0, shape="spline", smoothing=1.1),
            fill="tozeroy",
            fillcolor="rgba(124,58,237,0.12)",
            hoverinfo="skip",
            showlegend=False,
        ))

        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_values,
            mode="lines+markers+text",
            name="Beneficio",
            text=point_text,
            textposition=["top center"] * len(y_values),
            textfont=dict(color="#071E49", size=12),
            line=dict(color="#7C3AED", width=4, shape="spline", smoothing=1.1),
            marker=dict(size=11, color="#7C3AED", line=dict(width=2, color="#FFFFFF")),
            hovertemplate="<b>%{x}</b><br>Beneficio: %{y:,.0f} €<extra></extra>",
        ))

        # Etiqueta final destacada.
        fig.add_annotation(
            x=x_labels[-1],
            y=y_values[-1],
            text=f"<b>{fmt_eur(y_values[-1])}</b>",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-34 if y_values[-1] >= 0 else 34,
            bgcolor="#7C3AED",
            bordercolor="#7C3AED",
            font=dict(color="white", size=12),
            borderpad=5,
        )

        min_y = min(0.0, min(y_values))
        max_y = max(0.0, max(y_values))
        pad = max((max_y - min_y) * 0.18, max(abs(max_y), 1.0) * 0.08, 1000.0)
        fig.update_yaxes(range=[min_y - pad, max_y + pad])

    fig.update_layout(
        height=315,
        margin=dict(l=18, r=18, t=14, b=22),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        font=dict(family="Inter, Arial, sans-serif", color="#071E49"),
        hovermode="x unified",
        xaxis=dict(
            title="",
            type="category",
            categoryorder="array",
            categoryarray=[f"Ronda {r.get('round')}" for r in rows],
            showgrid=False,
            tickfont=dict(color="#64748B", size=12),
            fixedrange=True,
        ),
        yaxis=dict(
            title="",
            gridcolor="#E8EEF6",
            zeroline=True,
            zerolinecolor="#CBD5E1",
            tickfont=dict(color="#64748B", size=12),
            tickformat=",.0f",
            ticksuffix=" €",
            fixedrange=True,
        ),
    )
    return fig


def render_team_share_chart(team, history):
    """Gráfico PRO de evolución de cuota: solo rondas reales y formato % limpio."""
    fig = go.Figure()
    rows = []

    for round_data in history or []:
        rnum = round_data.get("round")
        for row in round_data.get("truth", []) or []:
            if row.get("team") == team:
                rows.append({
                    "round": rnum,
                    "round_label": f"Ronda {rnum}",
                    "share_pct": float(row.get("share", 0.0)) * 100,
                })

    if not rows:
        fig.add_annotation(
            text="Aún no hay histórico de cuota disponible.",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(color="#64748B", size=13),
        )
    else:
        df = pd.DataFrame(rows).sort_values("round")
        x_labels = df["round_label"].tolist()
        y_values = df["share_pct"].tolist()
        point_text = [f"{v:.1f}%".replace(".", ",") for v in y_values]

        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_values,
            mode="lines",
            line=dict(color="rgba(22,163,74,0)", width=0, shape="spline", smoothing=1.1),
            fill="tozeroy",
            fillcolor="rgba(22,163,74,0.10)",
            hoverinfo="skip",
            showlegend=False,
        ))

        fig.add_trace(go.Scatter(
            x=x_labels,
            y=y_values,
            mode="lines+markers+text",
            name="Cuota",
            text=point_text,
            textposition=["top center"] * len(y_values),
            textfont=dict(color="#071E49", size=12),
            line=dict(color="#16A34A", width=4, shape="spline", smoothing=1.1),
            marker=dict(size=11, color="#16A34A", line=dict(width=2, color="#FFFFFF")),
            hovertemplate="<b>%{x}</b><br>Cuota: %{y:.1f}%<extra></extra>",
        ))

        fig.add_annotation(
            x=x_labels[-1],
            y=y_values[-1],
            text=f"<b>{point_text[-1]}</b>",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-34,
            bgcolor="#16A34A",
            bordercolor="#16A34A",
            font=dict(color="white", size=12),
            borderpad=5,
        )

        min_y = max(0.0, min(y_values) - max(1.0, (max(y_values) - min(y_values)) * 0.35))
        max_y = min(100.0, max(y_values) + max(1.5, (max(y_values) - min(y_values)) * 0.35))
        if abs(max_y - min_y) < 3:
            max_y = min(100.0, max_y + 2)
            min_y = max(0.0, min_y - 2)
        fig.update_yaxes(range=[min_y, max_y])

    fig.update_layout(
        height=315,
        margin=dict(l=18, r=18, t=14, b=22),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        font=dict(family="Inter, Arial, sans-serif", color="#071E49"),
        hovermode="x unified",
        xaxis=dict(
            title="",
            type="category",
            categoryorder="array",
            categoryarray=[f"Ronda {r.get('round')}" for r in rows],
            showgrid=False,
            tickfont=dict(color="#64748B", size=12),
            fixedrange=True,
        ),
        yaxis=dict(
            title="",
            gridcolor="#E8EEF6",
            zeroline=False,
            tickfont=dict(color="#64748B", size=12),
            ticksuffix="%",
            fixedrange=True,
        ),
    )
    return fig


def _get_team_stock_previous(engine, team, teams):
    try:
        idx = get_team_index(team, teams)
        return float(getattr(engine, "inventory", [0] * len(teams))[idx])
    except Exception:
        return 0.0


def _get_profit_values(team, history):
    values = []
    for round_data in history or []:
        rnum = round_data.get("round")
        for row in round_data.get("truth", []):
            if row.get("team") == team:
                values.append((rnum, float(row.get("profit", 0.0))))
    return values


def _get_marketing_investment_values(team, history):
    """Inversión real de marketing por ronda cerrada.

    Usa budget_used_actual si existe; si no, reconstruye la inversión con
    comunicación, promoción, distribución, producto e investigación.
    """
    values = []
    for round_data in history or []:
        rnum = round_data.get("round")
        for row in round_data.get("truth", []) or []:
            if row.get("team") == team:
                if "budget_used_actual" in row:
                    investment = float(row.get("budget_used_actual", 0.0))
                else:
                    investment = (
                        float(row.get("comm_total", 0.0))
                        + float(row.get("promo_cost", 0.0))
                        + float(row.get("dist_cost", 0.0))
                        + float(row.get("product_investment_cost", 0.0))
                        + float(row.get("research_cost", 0.0))
                    )
                values.append((rnum, investment))
    return values


def build_budget_distribution_chart(comm_total, product_cost, dist_cost, promo_cost, research_cost, available_budget=None):
    """Gráfico donut de distribución total del presupuesto.

    Incluye el presupuesto no utilizado para que el gráfico siempre represente el 100%
    del presupuesto disponible, no solo el gasto ya asignado.
    """
    raw_items = [
        ("Comunicación", float(comm_total or 0.0), "#0F6BFF"),
        ("Producto", float(product_cost or 0.0), "#7C3AED"),
        ("Distribución", float(dist_cost or 0.0), "#16A34A"),
        ("Promoción", float(promo_cost or 0.0), "#F59E0B"),
        ("Informes", float(research_cost or 0.0), "#06A7B4"),
    ]

    total_invested = sum(v for _, v, _ in raw_items)
    budget_total = float(available_budget or 0.0)
    unused_budget = max(0.0, budget_total - total_invested) if budget_total > 0 else 0.0

    items = [(label, value, color) for label, value, color in raw_items if value > 0]
    if budget_total > 0:
        items.append(("No utilizado", unused_budget, "#DDE5F0"))

    if not items or sum(v for _, v, _ in items) <= 0:
        fig = go.Figure()
        fig.add_annotation(
            text="<b>Sin inversión asignada</b><br><span style='font-size:11px;color:#64748B'>Guarda una decisión para ver la distribución.</span>",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(color="#071E49", size=14),
        )
        fig.update_layout(
            height=315,
            margin=dict(l=8, r=8, t=8, b=8),
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    labels = [label for label, _, _ in items]
    values = [value for _, value, _ in items]
    colors = [color for _, _, color in items]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                sort=False,
                marker=dict(colors=colors, line=dict(color="white", width=3)),
                textinfo="percent",
                textposition="inside",
                insidetextfont=dict(size=12, color="white"),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} €<br>%{percent}<extra></extra>",
            )
        ]
    )

    center_total = budget_total if budget_total > 0 else total_invested
    center_label = "presupuesto" if budget_total > 0 else "invertido"
    fig.add_annotation(
        text=f"<b>{fmt_eur(center_total)}</b><br><span style='font-size:10px;color:#64748B'>{center_label}</span>",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(color="#071E49", size=14),
    )

    fig.update_layout(
        height=315,
        margin=dict(l=8, r=8, t=8, b=38),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.04,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#071E49"),
        ),
        font=dict(family="Inter, Arial, sans-serif", color="#071E49"),
    )
    return fig


def build_production_sales_chart(predicted_sales, products_available):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=["Predicción de ventas", "Productos disponibles"],
        x=[predicted_sales, products_available],
        orientation="h",
        text=[_fmt_int_plain(predicted_sales), _fmt_int_plain(products_available)],
        textposition="outside",
        hovertemplate="%{y}: %{x:,.0f} uds.<extra></extra>",
    ))
    fig.update_layout(height=245, margin=dict(l=10, r=30, t=15, b=20), xaxis_title="Unidades", yaxis_title="", showlegend=False)
    return fig


def render_budget_metric_card(title, value, note="", tone="info", icon=""):
    color = {"info": "#0B5CCB", "positive": "#2E9547", "warning": "#F59E0B", "danger": "#D92D20", "purple": "#6846B7"}.get(tone, "#0B5CCB")
    st.markdown(
        f"""
        <div class="decision-kpi-card" style="min-height:104px;">
            <div class="decision-kpi-label">{_html_escape(title)}</div>
            <div class="decision-kpi-value" style="color:{color};">{icon} {value}</div>
            <div class="decision-kpi-note">{_html_escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def inject_budget_phase1_styles():
    """Estilos visuales para Presupuesto - Fase 1: cabecera + estado del presupuesto."""
    st.markdown("""
    <style>
    .budget-hero {background:linear-gradient(135deg,#083763 0%,#072B55 100%);color:#fff;border-radius:18px;padding:22px 26px;margin:6px 0 20px 0;display:grid;grid-template-columns:72px 1fr 230px;gap:18px;align-items:center;box-shadow:0 12px 34px rgba(8,43,85,.22);} 
    .budget-hero-icon {width:58px;height:58px;border-radius:15px;border:2px solid rgba(150,210,255,.60);background:rgba(255,255,255,.08);display:flex;align-items:center;justify-content:center;font-size:2rem;}
    .budget-hero-title {font-size:2rem;font-weight:950;letter-spacing:-.04em;line-height:1.05;color:#fff;margin:0;}
    .budget-hero-subtitle {font-size:1rem;font-weight:750;opacity:.88;margin-top:7px;}
    .budget-hero-meta {border-left:1px solid rgba(255,255,255,.28);padding-left:22px;font-weight:850;font-size:.90rem;line-height:1.8;}
    .budget-hero-meta span {display:inline-block;min-width:76px;opacity:.82;}
    .budget-section {background:#fff;border:1px solid #DDE7F3;border-radius:18px;padding:18px 18px 20px 18px;margin:16px 0;box-shadow:0 12px 32px rgba(9,30,66,.06);}
    .budget-section-title {color:#0B4B93;font-size:1.12rem;font-weight:950;text-transform:uppercase;margin:0 0 14px 0;letter-spacing:-.02em;}
    .budget-note {background:#EAF4FF;border-radius:13px;padding:12px 16px;color:#0A3472;font-size:.88rem;font-weight:850;margin-bottom:16px;}
    .budget-kpi-grid {display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-bottom:16px;}
    .budget-kpi-card {background:#fff;border:1px solid #DCE6F2;border-radius:15px;min-height:154px;padding:18px 14px;box-shadow:0 7px 22px rgba(9,30,66,.055);display:flex;gap:13px;align-items:center;overflow:hidden;position:relative;}
    .budget-kpi-card:after {content:"";position:absolute;right:-34px;top:-44px;width:105px;height:105px;border-radius:999px;opacity:.55;background:var(--soft-bg);}
    .budget-kpi-icon {width:62px;height:62px;border-radius:50%;flex:0 0 62px;display:flex;align-items:center;justify-content:center;font-size:1.55rem;color:var(--main-color);background:var(--soft-bg);z-index:1;}
    .budget-kpi-content {z-index:1;min-width:0;}
    .budget-kpi-label {color:#071E49;font-size:.82rem;font-weight:950;line-height:1.15;margin-bottom:8px;}
    .budget-kpi-value {color:#061A44;font-size:1.45rem;font-weight:950;line-height:1.05;letter-spacing:-.03em;white-space:nowrap;}
    .budget-kpi-note {color:#52627A;font-size:.78rem;font-weight:800;margin-top:7px;line-height:1.25;}
    .budget-kpi-note.positive {color:#16A34A;} .budget-kpi-note.warning {color:#F59E0B;} .budget-kpi-note.danger {color:#DC2626;}
    .budget-status-bar-wrap {background:#F4F8FE;border:1px solid #E3EAF2;border-radius:14px;padding:14px 16px;margin-top:4px;}
    .budget-status-top {display:flex;justify-content:space-between;align-items:center;gap:14px;color:#071E49;font-size:.88rem;font-weight:900;margin-bottom:10px;}
    .budget-status-pill {display:inline-flex;align-items:center;gap:7px;padding:7px 12px;border-radius:999px;font-size:.78rem;font-weight:950;background:#EAF8EF;color:#168A4A;white-space:nowrap;}
    .budget-status-pill.warning {background:#FFF4D8;color:#B56A00;} .budget-status-pill.danger {background:#FEECEC;color:#B42318;}
    .budget-progress {height:12px;border-radius:999px;background:#DDE5F0;overflow:hidden;}
    .budget-progress span {display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#0F6BFF 0%,#16A34A 100%);width:var(--pct);}
    .budget-progress.warning span {background:linear-gradient(90deg,#F59E0B 0%,#F97316 100%);} .budget-progress.danger span {background:linear-gradient(90deg,#EF4444 0%,#B42318 100%);}
    @media(max-width:1250px){.budget-hero,.budget-kpi-grid{grid-template-columns:1fr}.budget-hero-meta{border-left:0;padding-left:0}}
    </style>
    """, unsafe_allow_html=True)


def _budget_phase1_kpi_card(label, value, note="", icon="•", tone="blue", note_tone=""):
    palette = {
        "blue": ("#0F6BFF", "#EAF2FF"), "green": ("#16A34A", "#EAF8EF"),
        "orange": ("#F59E0B", "#FFF4D8"), "purple": ("#7C3AED", "#F1E9FF"),
        "red": ("#DC2626", "#FEECEC"), "teal": ("#06A7B4", "#E6FAFB"),
    }
    color, soft = palette.get(tone, palette["blue"])
    note_cls = f" {note_tone}" if note_tone else ""
    return (
        f"<div class='budget-kpi-card' style='--main-color:{color}; --soft-bg:{soft};'>"
        f"<div class='budget-kpi-icon'>{_html_escape(icon)}</div>"
        f"<div class='budget-kpi-content'>"
        f"<div class='budget-kpi-label'>{_html_escape(label)}</div>"
        f"<div class='budget-kpi-value'>{value}</div>"
        f"<div class='budget-kpi-note{note_cls}'>{_html_escape(note)}</div>"
        f"</div></div>"
    )


def _render_budget_phase1_header(team, round_display, status, current_team_budget):
    st.markdown(
        f"""
        <div class="budget-hero">
            <div class="budget-hero-icon">💼</div>
            <div>
                <div class="budget-hero-title">Presupuesto</div>
                <div class="budget-hero-subtitle">Gestiona tu presupuesto y consulta la previsión económica de esta ronda.</div>
            </div>
            <div class="budget-hero-meta">
                <div><span>Ronda:</span>{_html_escape(round_display)}</div>
                <div><span>Estado:</span>{_html_escape(status)}</div>
                <div><span>Equipo:</span>{_html_escape(team)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_budget_phase1_status(current_team_budget, budget_used, budget_remaining, last_profit, accumulated_profit, accumulated_marketing_investment=0.0):
    budget_pct_raw = (float(budget_used) / max(float(current_team_budget), 1.0)) * 100
    budget_pct = max(0.0, min(100.0, budget_pct_raw))
    remaining_pct = max(0.0, 100.0 - budget_pct_raw)
    status_cls = "danger" if budget_remaining < 0 else "warning" if budget_pct_raw >= 85 else ""
    status_label = "Presupuesto excedido" if budget_remaining < 0 else "Uso elevado" if budget_pct_raw >= 85 else "Dentro del límite"
    remaining_note_tone = "danger" if budget_remaining < 0 else "warning" if budget_pct_raw >= 85 else "positive"
    pct_text = str(f"{budget_pct_raw:.1f}").replace(".", ",")
    rem_pct_text = str(f"{remaining_pct:.1f}").replace(".", ",")
    accumulated_roi = compute_marketing_roi(accumulated_profit, accumulated_marketing_investment)
    accumulated_roi_note, accumulated_roi_tone = marketing_roi_message(accumulated_roi)
    cards = [
        _budget_phase1_kpi_card("Presupuesto total disponible", fmt_eur(current_team_budget), "Total para invertir", "💼", "green", "positive"),
        _budget_phase1_kpi_card("Presupuesto utilizado", fmt_eur(budget_used), f"{pct_text}% del total", "◔", "blue"),
        _budget_phase1_kpi_card("Presupuesto restante", fmt_eur(budget_remaining), f"{rem_pct_text}% disponible", "🎯", "orange", remaining_note_tone),
        _budget_phase1_kpi_card("Beneficio última ronda", fmt_eur(last_profit), "Última ronda cerrada", "📈", "purple"),
        _budget_phase1_kpi_card("ROI de marketing", fmt_roi(accumulated_roi), "Beneficio / inversión acumulada", "📊", "teal", accumulated_roi_tone),
    ]
    st.markdown(
        f"""
        <div class="budget-section">
            <div class="budget-section-title">1. Estado del presupuesto</div>
            <div class="budget-note">ⓘ Estas métricas muestran el presupuesto disponible, la inversión actual y la eficiencia acumulada del marketing.</div>
            <div class="budget-kpi-grid">{''.join(cards)}</div>
            <div class="budget-status-bar-wrap">
                <div class="budget-status-top">
                    <span>Presupuesto utilizado: {pct_text}%</span>
                    <span class="budget-status-pill {status_cls}">● {status_label}</span>
                </div>
                <div class="budget-progress {status_cls}" style="--pct:{budget_pct:.1f}%;"><span></span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def inject_budget_phase2_styles():
    """Estilos visuales para Presupuesto - Fase 2: Previsión económica."""
    st.markdown("""
    <style>
    .budget-forecast-section {
        background:#fff;
        border:1px solid #DDE7F3;
        border-radius:18px;
        padding:18px 18px 20px 18px;
        margin:16px 0;
        box-shadow:0 12px 32px rgba(9,30,66,.06);
    }
    .budget-forecast-title {
        color:#0B4B93;
        font-size:1.12rem;
        font-weight:950;
        text-transform:uppercase;
        margin:0 0 14px 0;
        letter-spacing:-.02em;
    }
    .budget-forecast-note {
        background:#EAF4FF;
        border-radius:13px;
        padding:12px 16px;
        color:#0A3472;
        font-size:.88rem;
        font-weight:850;
        margin-bottom:16px;
    }
    .budget-forecast-grid {
        display:grid;
        grid-template-columns:repeat(4,minmax(0,1fr));
        gap:14px;
        margin-bottom:16px;
    }
    .budget-forecast-card {
        background:#fff;
        border:1px solid #DCE6F2;
        border-radius:15px;
        min-height:152px;
        padding:18px 16px;
        box-shadow:0 7px 22px rgba(9,30,66,.055);
        display:flex;
        gap:14px;
        align-items:center;
        overflow:hidden;
        position:relative;
    }
    .budget-forecast-card:after {
        content:"";
        position:absolute;
        right:-34px;
        top:-44px;
        width:105px;
        height:105px;
        border-radius:999px;
        opacity:.55;
        background:var(--soft-bg);
    }
    .budget-forecast-icon {
        width:62px;
        height:62px;
        border-radius:50%;
        flex:0 0 62px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:1.55rem;
        color:var(--main-color);
        background:var(--soft-bg);
        z-index:1;
    }
    .budget-forecast-content { z-index:1; min-width:0; }
    .budget-forecast-label {
        color:#071E49;
        font-size:.84rem;
        font-weight:950;
        line-height:1.15;
        margin-bottom:8px;
    }
    .budget-forecast-value {
        color:#061A44;
        font-size:1.48rem;
        font-weight:950;
        line-height:1.05;
        letter-spacing:-.03em;
        white-space:nowrap;
    }
    .budget-forecast-note-small {
        color:#52627A;
        font-size:.78rem;
        font-weight:800;
        margin-top:7px;
        line-height:1.25;
    }
    .budget-forecast-note-small.positive { color:#16A34A; }
    .budget-forecast-note-small.danger { color:#DC2626; }
    .budget-forecast-note-small.warning { color:#F59E0B; }
    .budget-forecast-summary {
        background:#F4F8FE;
        border:1px solid #E3EAF2;
        border-radius:14px;
        padding:14px 16px;
        display:grid;
        grid-template-columns:1fr auto;
        gap:14px;
        align-items:center;
    }
    .budget-forecast-summary-title {
        color:#071E49;
        font-size:.90rem;
        font-weight:950;
        margin-bottom:4px;
    }
    .budget-forecast-summary-text {
        color:#53657D;
        font-size:.82rem;
        font-weight:750;
        line-height:1.35;
    }
    .budget-forecast-pill {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        padding:10px 14px;
        border-radius:999px;
        font-size:.84rem;
        font-weight:950;
        white-space:nowrap;
        background:#EAF8EF;
        color:#168A4A;
    }
    .budget-forecast-pill.danger { background:#FEECEC; color:#B42318; }
    @media(max-width:1250px){
        .budget-forecast-grid { grid-template-columns:1fr; }
        .budget-forecast-summary { grid-template-columns:1fr; }
    }
    </style>
    """, unsafe_allow_html=True)


def _budget_forecast_card_html(label, value, note, icon, tone="blue", note_tone=""):
    palette = {
        "blue": ("#0F6BFF", "#EAF2FF"),
        "green": ("#16A34A", "#EAF8EF"),
        "orange": ("#F59E0B", "#FFF4D8"),
        "purple": ("#7C3AED", "#F1E9FF"),
        "red": ("#DC2626", "#FEECEC"),
        "teal": ("#06A7B4", "#E6FAFB"),
    }
    color, soft = palette.get(tone, palette["blue"])
    note_cls = f" {note_tone}" if note_tone else ""
    return (
        f"<div class='budget-forecast-card' style='--main-color:{color}; --soft-bg:{soft};'>"
        f"<div class='budget-forecast-icon'>{_html_escape(icon)}</div>"
        f"<div class='budget-forecast-content'>"
        f"<div class='budget-forecast-label'>{_html_escape(label)}</div>"
        f"<div class='budget-forecast-value'>{value}</div>"
        f"<div class='budget-forecast-note-small{note_cls}'>{_html_escape(note)}</div>"
        f"</div></div>"
    )


def render_budget_phase2_forecast(expected_revenue, production_cost, marketing_investment, expected_profit):
    margin = (float(expected_profit) / max(float(expected_revenue), 1.0)) * 100
    margin_text = f"{margin:.1f}".replace(".", ",")
    profit_positive = expected_profit >= 0
    cards = [
        _budget_forecast_card_html("Ingresos esperados", fmt_eur(expected_revenue), "Ventas previstas × precio", "🛒", "green", "positive"),
        _budget_forecast_card_html("Gastos de fabricación", fmt_eur(production_cost), "Producción × coste unitario", "🏭", "red", "danger"),
        _budget_forecast_card_html("Gastos de marketing", fmt_eur(marketing_investment), "Inversión estratégica total", "📣", "blue"),
        _budget_forecast_card_html("Beneficio esperado de la ronda", fmt_eur(expected_profit), f"{margin_text}% sobre ingresos", "💰", "green" if profit_positive else "red", "positive" if profit_positive else "danger"),
    ]
    pill_cls = "" if profit_positive else "danger"
    pill_text = "Beneficio esperado positivo" if profit_positive else "Beneficio esperado negativo"
    html = (
        "<div class='budget-forecast-section'>"
        "<div class='budget-forecast-title'>2. Previsión económica de la ronda</div>"
        "<div class='budget-forecast-note'>ⓘ Estimación económica de la ronda según ingresos esperados, fabricación, marketing y beneficio previsto.</div>"
        f"<div class='budget-forecast-grid'>{''.join(cards)}</div>"
        "<div class='budget-forecast-summary'>"
        "<div>"
        "<div class='budget-forecast-summary-title'>Lectura económica</div>"
        "<div class='budget-forecast-summary-text'>El beneficio esperado se calcula como ingresos esperados menos gastos de fabricación y gastos de marketing.</div>"
        "</div>"
        f"<div class='budget-forecast-pill {pill_cls}'>● {pill_text}</div>"
        "</div>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)



def inject_budget_phase3_styles():
    """Estilos visuales para Presupuesto - Fase 3: Producción y ventas."""
    st.markdown("""
    <style>
    .budget-production-section {
        background:#fff;
        border:1px solid #DDE7F3;
        border-radius:18px;
        padding:18px 18px 20px 18px;
        margin:16px 0;
        box-shadow:0 12px 32px rgba(9,30,66,.06);
    }
    .budget-production-title {
        color:#0B4B93;
        font-size:1.12rem;
        font-weight:950;
        text-transform:uppercase;
        margin:0 0 14px 0;
        letter-spacing:-.02em;
    }
    .budget-production-note {
        background:#EAF4FF;
        border-radius:13px;
        padding:12px 16px;
        color:#0A3472;
        font-size:.88rem;
        font-weight:850;
        margin-bottom:16px;
    }
    .budget-production-grid {
        display:grid;
        grid-template-columns:repeat(3,minmax(0,1fr));
        gap:14px;
        margin-bottom:16px;
    }
    .budget-production-card {
        background:#fff;
        border:1px solid #DCE6F2;
        border-radius:15px;
        min-height:170px;
        padding:20px 18px;
        box-shadow:0 7px 22px rgba(9,30,66,.055);
        display:flex;
        gap:16px;
        align-items:center;
        overflow:hidden;
        position:relative;
    }
    .budget-production-card:after {
        content:"";
        position:absolute;
        right:-36px;
        top:-48px;
        width:116px;
        height:116px;
        border-radius:999px;
        opacity:.55;
        background:var(--soft-bg);
    }
    .budget-production-icon {
        width:68px;
        height:68px;
        border-radius:50%;
        flex:0 0 68px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:1.72rem;
        color:var(--main-color);
        background:var(--soft-bg);
        z-index:1;
    }
    .budget-production-content { z-index:1; min-width:0; }
    .budget-production-label {
        color:#071E49;
        font-size:.90rem;
        font-weight:950;
        line-height:1.15;
        margin-bottom:9px;
    }
    .budget-production-value {
        color:#061A44;
        font-size:1.72rem;
        font-weight:950;
        line-height:1.05;
        letter-spacing:-.035em;
        white-space:nowrap;
    }
    .budget-production-note-small {
        color:#52627A;
        font-size:.80rem;
        font-weight:850;
        margin-top:8px;
        line-height:1.30;
    }
    .budget-production-note-small.positive { color:#16A34A; }
    .budget-production-note-small.warning { color:#F59E0B; }
    .budget-production-note-small.danger { color:#DC2626; }

    .budget-production-body {
        display:grid;
        grid-template-columns:1.25fr .95fr;
        gap:16px;
        align-items:stretch;
    }
    .budget-production-chartbox {
        background:#fff;
        border:1px solid #E3EAF2;
        border-radius:16px;
        padding:14px 16px;
        box-shadow:0 8px 24px rgba(9,30,66,.045);
        min-height:310px;
    }
    .budget-production-reading {
        background:linear-gradient(180deg,#EEF6FF 0%,#F4F9FF 100%);
        border:1px solid #CFE3FF;
        border-left:6px solid #0F6BFF;
        border-radius:18px;
        padding:20px 22px;
        min-height:310px;
        box-shadow:0 10px 28px rgba(9,30,66,.055);
    }
    .budget-production-reading-title {
        display:flex;
        align-items:center;
        gap:10px;
        color:#071E49;
        font-size:1.06rem;
        font-weight:950;
        margin-bottom:18px;
    }
    .budget-production-reading-icon {
        width:36px;
        height:36px;
        border-radius:50%;
        background:#0F6BFF;
        color:#fff;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:1.05rem;
        flex:0 0 36px;
    }
    .budget-production-reading-list {
        list-style:none;
        margin:0;
        padding:0;
    }
    .budget-production-reading-list li {
        display:flex;
        gap:12px;
        align-items:flex-start;
        margin-bottom:15px;
        color:#071E49;
        font-size:.90rem;
        line-height:1.42;
        font-weight:750;
    }
    .budget-production-bullet {
        width:24px;
        height:24px;
        border-radius:50%;
        background:#0F6BFF;
        color:#fff;
        display:inline-flex;
        align-items:center;
        justify-content:center;
        flex:0 0 24px;
        font-size:.72rem;
        font-weight:950;
        margin-top:1px;
    }
    .budget-production-tip {
        background:white;
        border:1px solid #DDE7F3;
        border-radius:14px;
        padding:13px 15px;
        color:#0A3472;
        font-size:.84rem;
        line-height:1.42;
        font-weight:850;
        margin-top:16px;
    }
    @media(max-width:1250px){
        .budget-production-grid,
        .budget-production-body { grid-template-columns:1fr; }
    }
    </style>
    """, unsafe_allow_html=True)


def _budget_phase3_card_html(label, value, note, icon, tone="blue", note_tone=""):
    palette = {
        "blue": ("#0F6BFF", "#EAF2FF"),
        "green": ("#16A34A", "#EAF8EF"),
        "orange": ("#F59E0B", "#FFF4D8"),
        "purple": ("#7C3AED", "#F1E9FF"),
        "red": ("#DC2626", "#FEECEC"),
        "teal": ("#06A7B4", "#E6FAFB"),
    }
    color, soft = palette.get(tone, palette["blue"])
    note_cls = f" {note_tone}" if note_tone else ""
    return (
        f"<div class='budget-production-card' style='--main-color:{color}; --soft-bg:{soft};'>"
        f"<div class='budget-production-icon'>{_html_escape(icon)}</div>"
        f"<div class='budget-production-content'>"
        f"<div class='budget-production-label'>{_html_escape(label)}</div>"
        f"<div class='budget-production-value'>{value}</div>"
        f"<div class='budget-production-note-small{note_cls}'>{_html_escape(note)}</div>"
        f"</div></div>"
    )


def build_budget_production_phase3_chart(predicted_sales, production_units, stock_previous):
    products_available = float(production_units) + float(stock_previous)
    values = [float(predicted_sales), float(production_units), float(stock_previous)]
    labels = ["Predicción de ventas", "Productos fabricados", "Stock acumulado"]

    max_value = max(values + [1.0])
    colors = ["#0F6BFF", "#16A34A", "#F59E0B"]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            text=[_fmt_int_plain(v) for v in values],
            textposition="outside",
            marker=dict(color=colors, line=dict(width=0)),
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{x:,.0f} uds.<extra></extra>",
        )
    )
    fig.update_layout(
        height=300,
        margin=dict(l=150, r=42, t=8, b=24),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        font=dict(family="Inter, Arial, sans-serif", color="#071E49"),
        xaxis=dict(
            title="Unidades",
            showgrid=True,
            gridcolor="#E8EEF6",
            zeroline=False,
            range=[0, max_value * 1.18],
            fixedrange=True,
            tickfont=dict(color="#64748B", size=11),
        ),
        yaxis=dict(
            title="",
            autorange="reversed",
            fixedrange=True,
            tickfont=dict(color="#071E49", size=12),
        ),
    )
    return fig


def render_budget_phase3_production(predicted_sales, production_units, stock_previous):
    products_available = float(production_units) + float(stock_previous)
    coverage_pct = (products_available / max(float(predicted_sales), 1.0)) * 100
    stock_pct = (float(stock_previous) / max(float(predicted_sales), 1.0)) * 100

    if coverage_pct >= 105:
        coverage_note = "Hay margen para cubrir la demanda prevista."
        coverage_tone = "positive"
    elif coverage_pct >= 95:
        coverage_note = "La producción está alineada con la demanda prevista."
        coverage_tone = "positive"
    else:
        coverage_note = "Podrías quedarte corto si la previsión se cumple."
        coverage_tone = "warning"

    stock_label = "Stock bajo" if stock_pct < 10 else "Stock controlado" if stock_pct < 25 else "Stock elevado"
    stock_note_tone = "positive" if stock_pct < 25 else "warning"

    cards = [
        _budget_phase3_card_html(
            "Predicción de ventas",
            _fmt_int_plain(predicted_sales),
            "unidades previstas",
            "📈",
            "blue",
        ),
        _budget_phase3_card_html(
            "Productos fabricados",
            _fmt_int_plain(production_units),
            f"{str(f'{coverage_pct:.1f}').replace('.', ',')}% de la previsión",
            "🏭",
            "green",
            coverage_tone,
        ),
        _budget_phase3_card_html(
            "Stock acumulado",
            _fmt_int_plain(stock_previous),
            f"{stock_label} · {str(f'{stock_pct:.1f}').replace('.', ',')}% de la previsión",
            "📦",
            "orange",
            stock_note_tone,
        ),
    ]

    reading_items = [
        f"Productos disponibles: {_fmt_int_plain(products_available)} unidades.",
        coverage_note,
        f"El stock acumulado representa el {str(f'{stock_pct:.1f}').replace('.', ',')}% de la predicción de ventas.",
    ]
    lis = "".join(
        f"<li><span class='budget-production-bullet'>✓</span><span>{_html_escape(item)}</span></li>"
        for item in reading_items
    )

    st.markdown(
        f"""
        <div class="budget-production-section">
            <div class="budget-production-title">3. Producción y ventas</div>
            <div class="budget-production-note">ⓘ Estas métricas muestran la predicción de ventas, los productos fabricados y el stock acumulado.</div>
            <div class="budget-production-grid">{''.join(cards)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prod_cols = st.columns([1.35, 1])
    with prod_cols[0]:
        with st.container(border=True):
            st.markdown(
                """
                <div style="color:#071E49;font-size:1rem;font-weight:950;margin-bottom:4px;">
                    Comparativa de producción
                </div>
                <div style="color:#53657D;font-size:.84rem;font-weight:700;margin-bottom:8px;">
                    Predicción de ventas, fabricación y stock acumulado.
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                build_budget_production_phase3_chart(predicted_sales, production_units, stock_previous),
                use_container_width=True,
                config={"displayModeBar": False, "responsive": True},
            )

    with prod_cols[1]:
        st.markdown(
            f"""
            <div class="budget-production-reading">
                <div class="budget-production-reading-title">
                    <span class="budget-production-reading-icon">💡</span>
                    <span>Lectura rápida</span>
                </div>
                <ul class="budget-production-reading-list">{lis}</ul>
                <div class="budget-production-tip">
                    <b>Clave:</b> ajusta fabricación y stock para cubrir ventas previstas sin inmovilizar demasiadas unidades.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_team_budget(team, teams, engine, state, current_team_budget, round_n, game_id):
    """Pantalla visual PRO de presupuesto, producción y previsión económica."""
    inject_decision_pro_styles()
    inject_dashboard_styles()
    inject_budget_phase1_styles()
    inject_budget_phase2_styles()
    inject_budget_phase3_styles()

    existing_entry = get_decision(game_id, team, round_n)
    decision = existing_entry["decision"] if existing_entry else {}
    if not decision:
        st.info("Aún no hay una decisión guardada en esta ronda. Esta pantalla se completará con tu decisión actual cuando la guardes.")

    predicted_sales = float(decision.get("estimated_units_for_budget", estimate_reference_units(team, teams, engine)))
    stock_previous = float(decision.get("stock_acumulado_anterior", _get_team_stock_previous(engine, team, teams)))
    production_units = float(decision.get("production_units", max(predicted_sales * 1.05 - stock_previous, 0.0)))
    products_available = float(decision.get("products_available", production_units + stock_previous))

    price = float(decision.get("price", 8.0))
    unit_cost = float(decision.get("estimated_unit_cost", estimate_unit_cost(engine, team, teams, 0.5, 0.5, 0.5)[1]))
    comm_total = float(decision.get("comm_total", 0.0))
    promo_cost = float(decision.get("estimated_promo_cost", 0.0))
    dist_cost = float(decision.get("estimated_dist_cost", 0.0))
    product_cost = float(decision.get("estimated_product_investment_cost", decision.get("estimated_quality_investment_cost", 0.0)))
    research_cost = float(decision.get("research_cost", 0.0))

    marketing_investment = comm_total + promo_cost + dist_cost + product_cost + research_cost
    production_cost = float(decision.get("estimated_production_cost", production_units * unit_cost))
    expected_revenue = price * min(predicted_sales, products_available)
    expected_profit = expected_revenue - production_cost - marketing_investment
    budget_used = marketing_investment
    budget_remaining = float(current_team_budget) - budget_used
    budget_pct = max(0.0, min(100.0, budget_used / max(float(current_team_budget), 1.0) * 100))

    profit_values = _get_profit_values(team, state.get("history", []))
    marketing_investment_values = _get_marketing_investment_values(team, state.get("history", []))
    last_profit = profit_values[-1][1] if profit_values else 0.0
    accumulated_profit = sum(v for _, v in profit_values)
    accumulated_marketing_investment = sum(v for _, v in marketing_investment_values)
    accumulated_roi = compute_marketing_roi(accumulated_profit, accumulated_marketing_investment)
    accumulated_roi_note, accumulated_roi_tone = marketing_roi_message(accumulated_roi)

    round_display = state.get("round_n", round_n)
    status_display = "abierta" if state.get("round_status") == "open" else state.get("round_status", "-")

    _render_budget_phase1_header(team, round_display, status_display, current_team_budget)
    _render_budget_phase1_status(current_team_budget, budget_used, budget_remaining, last_profit, accumulated_profit, accumulated_marketing_investment)

    render_budget_phase2_forecast(expected_revenue, production_cost, marketing_investment, expected_profit)

    render_budget_phase3_production(predicted_sales, production_units, stock_previous)

    graph_cols = st.columns(2)

    with graph_cols[0]:
        with st.container(border=True):
            st.markdown('<div style="font-weight:900; color:#071E49; font-size:1.0rem;">◔ DISTRIBUCIÓN DEL PRESUPUESTO</div><div style="color:#53657D; font-size:.85rem;">Cómo distribuyes tu inversión en esta ronda</div>', unsafe_allow_html=True)
            st.plotly_chart(
                build_budget_distribution_chart(comm_total, product_cost, dist_cost, promo_cost, research_cost, current_team_budget),
                use_container_width=True,
                config={"displayModeBar": False, "responsive": True},
            )
            st.markdown(f"<div class='decision-note-box'><b>Total invertido:</b> <span style='float:right; color:#0B5CCB; font-weight:900;'>{fmt_eur(marketing_investment)} ({budget_pct:.0f}% del presupuesto)</span></div>", unsafe_allow_html=True)

    with graph_cols[1]:
        with st.container(border=True):
            st.markdown('<div style="font-weight:900; color:#071E49; font-size:1.0rem;">📈 EVOLUCIÓN DEL BENEFICIO</div><div style="color:#53657D; font-size:.85rem;">Beneficio obtenido en cada ronda</div>', unsafe_allow_html=True)
            st.plotly_chart(
                render_team_profit_chart(team, state.get("history", [])),
                use_container_width=True,
                config={"displayModeBar": False, "responsive": True},
            )
            render_budget_metric_card("Beneficio acumulado", fmt_eur(accumulated_profit), "hasta la ronda anterior", "purple", "📈")
            st.markdown(
                f"<div class='decision-note-box'>"
                f"<b>Inversión acumulada:</b> <span style='float:right; color:#0B5CCB; font-weight:900;'>{fmt_eur(accumulated_marketing_investment)}</span><br>"
                f"<b>ROI acumulado:</b> <span style='float:right; font-weight:900;'>{fmt_roi(accumulated_roi)}</span><br>"
                f"<span style='color:#52627A;'>{_html_escape(accumulated_roi_note)}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.caption("ℹ️ El coste de fabricación no se descuenta del presupuesto, pero sí afecta al beneficio de la ronda.")
def inject_summary_pro_styles():
    st.markdown("""
    <style>
    .summary-page-head { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin:2px 0 14px 0; }
    .summary-title-wrap { display:flex; align-items:center; gap:12px; }
    .summary-title-icon { width:48px; height:48px; border:1px solid #E4EAF3; border-radius:14px; display:flex; align-items:center; justify-content:center; background:#fff; color:#2563EB; font-size:1.45rem; box-shadow:0 8px 22px rgba(9,30,66,.045); }
    .summary-title { margin:0; color:#071E49; font-size:1.62rem; font-weight:950; letter-spacing:-.04em; line-height:1.05; }
    .summary-subtitle { margin-top:5px; color:#53657D; font-size:.90rem; font-weight:650; }
    .summary-pills { display:flex; gap:9px; flex-wrap:wrap; justify-content:flex-end; }
    .summary-pill { background:#fff; border:1px solid #E3EAF2; border-radius:999px; padding:9px 13px; color:#071E49; font-size:.82rem; font-weight:850; box-shadow:0 5px 16px rgba(9,30,66,.035); }
    .summary-kpi-card { background:#fff; border:1px solid #E4EAF3; border-radius:14px; padding:14px 14px; min-height:106px; box-shadow:0 8px 24px rgba(9,30,66,.055); display:flex; gap:12px; align-items:center; }
    .summary-kpi-icon { width:44px; height:44px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-size:1.12rem; font-weight:900; flex:0 0 44px; }
    .summary-kpi-title { color:#334155; font-size:.72rem; font-weight:950; line-height:1.15; margin-bottom:5px; }
    .summary-kpi-value { color:#071E49; font-size:1.42rem; font-weight:950; letter-spacing:-.03em; line-height:1; }
    .summary-kpi-note { margin-top:5px; color:#64748B; font-size:.73rem; font-weight:700; }
    .summary-kpi-note.good { color:#16A34A; } .summary-kpi-note.bad { color:#DC2626; } .summary-kpi-note.warn { color:#D97706; }
    .summary-panel { background:#fff; border:1px solid #E4EAF3; border-radius:16px; padding:14px 16px; box-shadow:0 8px 24px rgba(9,30,66,.055); min-height:355px; }
    .summary-panel-title { display:flex; align-items:center; gap:8px; color:#071E49; font-size:.96rem; font-weight:950; margin-bottom:2px; }
    .summary-panel-subtitle { color:#64748B; font-size:.78rem; font-weight:650; margin-bottom:8px; }
    .summary-market-card { background:#fff; border:1px solid #E4EAF3; border-radius:14px; padding:12px 14px; box-shadow:0 5px 18px rgba(9,30,66,.035); min-height:88px; margin:12px 0; }
    .summary-market-label { color:#64748B; font-size:.72rem; font-weight:900; text-transform:uppercase; letter-spacing:.03em; }
    .summary-market-value { color:#071E49; font-size:1.08rem; font-weight:950; margin-top:5px; }
    .summary-market-note { color:#64748B; font-size:.74rem; margin-top:3px; }
    .summary-insight { border-radius:16px; padding:18px 20px; border:1px solid; min-height:158px; box-shadow:0 8px 22px rgba(9,30,66,.045); }
    .summary-insight h4 { margin:0 0 12px 0; font-size:1.05rem; font-weight:950; color:#071E49; letter-spacing:-.02em; display:flex; align-items:center; gap:10px; }
    .summary-insight-title-icon { font-size:1.35rem; line-height:1; }
    .summary-insight ul { list-style:none; margin:0; padding:0; }
    .summary-insight li { display:flex; gap:10px; align-items:flex-start; margin-bottom:10px; color:#071E49; font-size:.88rem; line-height:1.35; font-weight:700; }
    .summary-dot { width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex:0 0 24px; color:#fff; font-size:.74rem; font-weight:950; }
    .insight-good { background:#F0FDF4; border-color:#BBF7D0; } .insight-good .summary-dot{background:#22C55E;}
    .insight-warn { background:#FFFBEB; border-color:#FDE68A; } .insight-warn .summary-dot{background:#F59E0B;}
    .insight-risk { background:#FEF2F2; border-color:#FECACA; } .insight-risk .summary-dot{background:#EF4444;}
    .summary-tip { background:#EFF6FF; color:#1D4ED8; border:1px solid #BFDBFE; border-radius:12px; padding:11px 14px; font-size:.82rem; font-weight:750; margin-top:12px; }
    .summary-empty { background:#fff; border:1px dashed #CBD5E1; border-radius:16px; padding:20px; color:#64748B; }
    .summary-insight { border-radius:18px !important; padding:18px 20px !important; border:1px solid !important; min-height:190px !important; box-shadow:0 10px 26px rgba(9,30,66,.06) !important; position:relative !important; overflow:hidden !important; }
    .summary-insight:before { content:""; position:absolute; inset:0 auto 0 0; width:5px; opacity:.95; }
    .summary-insight h4 { margin:0 0 14px 0 !important; font-size:1.08rem !important; font-weight:950 !important; color:#071E49 !important; letter-spacing:-.02em; display:flex !important; align-items:center !important; gap:11px !important; }
    .summary-insight-title-icon { width:34px; height:34px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; color:#fff; font-size:1.05rem; line-height:1; box-shadow:0 8px 18px rgba(9,30,66,.12); }
    .summary-insight ul { list-style:none !important; margin:0 !important; padding:0 !important; }
    .summary-insight li { list-style:none !important; display:flex !important; gap:10px !important; align-items:flex-start !important; margin:0 0 11px 0 !important; color:#071E49 !important; font-size:.88rem !important; line-height:1.38 !important; font-weight:700 !important; }
    .summary-dot { width:23px; height:23px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; flex:0 0 23px; color:#fff; font-size:.72rem; font-weight:950; margin-top:1px; }
    .insight-good { background:linear-gradient(180deg,#F0FDF4 0%,#ECFDF5 100%) !important; border-color:#BBF7D0 !important; } .insight-good:before,.insight-good .summary-dot,.insight-good .summary-insight-title-icon{background:#16A34A;}
    .insight-warn { background:linear-gradient(180deg,#FFFBEB 0%,#FFF7E6 100%) !important; border-color:#FDE68A !important; } .insight-warn:before,.insight-warn .summary-dot,.insight-warn .summary-insight-title-icon{background:#F59E0B;}
    .insight-risk { background:linear-gradient(180deg,#FEF2F2 0%,#FFF1F2 100%) !important; border-color:#FECACA !important; } .insight-risk:before,.insight-risk .summary-dot,.insight-risk .summary-insight-title-icon{background:#EF4444;}
    @media (max-width:1100px){ .summary-page-head{flex-direction:column;} .summary-pills{justify-content:flex-start;} }
    </style>
    """, unsafe_allow_html=True)


def render_summary_kpi_card(title, value, note, icon, color, note_tone=""):
    st.markdown(
        f"""
        <div class="summary-kpi-card">
            <div class="summary-kpi-icon" style="background:{color};">{icon}</div>
            <div>
                <div class="summary-kpi-title">{_html_escape(title)}</div>
                <div class="summary-kpi-value">{value}</div>
                <div class="summary-kpi-note {note_tone}">{_html_escape(note)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_market_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="summary-market-card">
            <div class="summary-market-label">{_html_escape(label)}</div>
            <div class="summary-market-value">{value}</div>
            <div class="summary-market-note">{_html_escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_insight_box(title, items, tone):
    bullet_icon = {"good":"✓", "warn":"•", "risk":"!"}.get(tone, "•")
    title_icon = {"good":"★", "warn":"💡", "risk":"−"}.get(tone, "★")
    cls = {"good":"insight-good", "warn":"insight-warn", "risk":"insight-risk"}.get(tone, "insight-good")
    clean_items = [str(item).strip() for item in (items or []) if str(item).strip()]
    lis = "".join(
        f"<li><span class='summary-dot'>{bullet_icon}</span><span>{_html_escape(item)}</span></li>"
        for item in clean_items[:4]
    )
    st.markdown(
        f"""
        <div class="summary-insight {cls}">
            <h4><span class="summary-insight-title-icon">{title_icon}</span><span>{_html_escape(title)}</span></h4>
            <ul>{lis}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_reading_card(title, body, tone="info"):
    """Tarjeta de lectura final del resumen: Lo mejor / Lo más débil / Qué mejorar."""
    inject_summary_pro_styles()
    tone_map = {
        "positive": "good",
        "danger": "risk",
        "warning": "warn",
        "info": "good",
        "good": "good",
        "risk": "risk",
        "warn": "warn",
    }
    final_tone = tone_map.get(tone, "good")
    items = body if isinstance(body, list) else [body]
    render_summary_insight_box(title, items, final_tone)


def _summary_market_snapshot(state, team):
    last_research = state.get("last_research") or {}
    last_truth = state.get("last_truth") or []
    seg = _market_segment_insights(last_research, team) if last_research else {}
    public = _market_public_insights(last_truth) if last_truth else {}
    biggest = segment_name_es(seg.get("biggest_segment")) if seg.get("biggest_segment") else "-"
    total_market = seg.get("total_market", 0.0)
    leader = public.get("share_leader_team", "-") if public else "-"
    leader_share = public.get("share_leader_value", 0.0) if public else 0.0
    best_segment = segment_name_es(seg.get("best_segment")) if seg.get("best_segment") else "-"
    best_value = seg.get("best_value", 0.0) if seg else 0.0
    return biggest, total_market, leader, leader_share, best_segment, best_value


def render_team_summary(team, state, current_team_budget, round_n):
    """Resumen visual estable: Fase 1 + Fase 2, sin HTML residual."""
    inject_dashboard_styles()

    def _num(value, default=0.0):
        try:
            return float(value)
        except Exception:
            return default

    def _fmt_units(value):
        try:
            return f"{int(round(float(value))):,}".replace(",", ".")
        except Exception:
            return str(value)

    def _delta_pct(current, previous):
        if previous is None or abs(_num(previous)) < 1e-9:
            return "— vs ronda anterior", "neutral"
        delta = (_num(current) - _num(previous)) / abs(_num(previous)) * 100
        arrow = "↑" if delta >= 0 else "↓"
        tone = "good" if delta >= 0 else "bad"
        return f"{arrow} {abs(delta):.1f}% vs ronda anterior".replace(".", ","), tone

    def _delta_pp(current, previous):
        if previous is None:
            return "— vs ronda anterior", "neutral"
        delta = (_num(current) - _num(previous)) * 100
        arrow = "↑" if delta >= 0 else "↓"
        tone = "good" if delta >= 0 else "bad"
        return f"{arrow} {abs(delta):.1f} p.p. vs ronda anterior".replace(".", ","), tone

    def _team_rows():
        rows = []
        for rd in state.get("history", []) or []:
            rnum = rd.get("round")
            for row in rd.get("truth", []) or []:
                if row.get("team") == team:
                    copy = dict(row)
                    copy["round"] = rnum
                    rows.append(copy)
        return rows

    def _ranking(last_truth):
        if not last_truth:
            return "—", "Sin ranking disponible"
        rows = list(last_truth)
        max_units = max([_num(r.get("units")) for r in rows] + [1.0])
        max_profit = max([abs(_num(r.get("profit"))) for r in rows] + [1.0])
        scores = []
        for r in rows:
            score = (_num(r.get("share")) * 45) + ((_num(r.get("units")) / max_units) * 30) + ((_num(r.get("profit")) / max_profit) * 25)
            scores.append((r.get("team"), score))
        scores.sort(key=lambda x: x[1], reverse=True)
        pos = next((i + 1 for i, (t, _) in enumerate(scores) if t == team), None)
        if pos is None:
            return "—", "Ranking por ventas, beneficio y cuota"
        return f"{pos}º / {len(scores)}", "Ranking por ventas, beneficio y cuota"

    def _kpi_card(title, icon, value, subtitle, delta="", tone="neutral"):
        tone_class = {"good": "kpi-good", "bad": "kpi-bad", "neutral": "kpi-neutral"}.get(tone, "kpi-neutral")
        delta_html = f"<div class='resume-kpi-delta {tone_class}'>{_html_escape(delta)}</div>" if delta else ""
        return (
            "<div class='resume-kpi-card'>"
            f"<div class='resume-kpi-icon'>{_html_escape(icon)}</div>"
            f"<div class='resume-kpi-title'>{_html_escape(title)}</div>"
            f"<div class='resume-kpi-value'>{value}</div>"
            f"<div class='resume-kpi-subtitle'>{_html_escape(subtitle)}</div>"
            f"{delta_html}"
            "</div>"
        )

    def _op_card(title, icon, value, subtitle, detail, progress=0.0, tone="blue"):
        progress = max(0, min(100, _num(progress)))
        return (
            f"<div class='resume-op-card op-{tone}'>"
            "<div class='resume-op-bg'></div>"
            f"<div class='resume-op-icon'>{_html_escape(icon)}</div>"
            "<div class='resume-op-content'>"
            f"<div class='resume-op-title'>{_html_escape(title)}</div>"
            f"<div class='resume-op-value'>{_html_escape(value)}</div>"
            f"<div class='resume-op-subtitle'>{_html_escape(subtitle)}</div>"
            f"<div class='resume-op-detail'>{_html_escape(detail)}</div>"
            "<div class='resume-progress'><span style='width:" + f"{progress:.0f}" + "%'></span></div>"
            "</div>"
            "</div>"
        )

    def _insight_card(title, icon, items, tone):
        rows = "".join(f"<li><span>{icon}</span>{_html_escape(x)}</li>" for x in items)
        return (
            f"<div class='resume-insight-card insight-{tone}'>"
            f"<div class='resume-insight-head'>{_html_escape(title)}</div>"
            f"<ul>{rows}</ul>"
            "</div>"
        )

    st.markdown("""
    <style>
    .resume-hero {background:linear-gradient(135deg,#083763 0%,#072B55 100%); color:white; border-radius:18px; padding:22px 26px; margin:6px 0 20px 0; display:grid; grid-template-columns:72px 1fr 290px; gap:18px; align-items:center; box-shadow:0 12px 34px rgba(8,43,85,.22);} 
    .resume-hero-icon {width:58px;height:58px;border-radius:15px;border:2px solid rgba(150,210,255,.6);background:rgba(255,255,255,.08);display:flex;align-items:center;justify-content:center;font-size:2rem;}
    .resume-hero-title {font-size:2rem;font-weight:950;letter-spacing:-.04em;line-height:1.05;color:#fff;margin:0;}
    .resume-hero-subtitle {font-size:1rem;font-weight:750;opacity:.88;margin-top:7px;}
    .resume-hero-meta {border-left:1px solid rgba(255,255,255,.28);padding-left:24px;font-weight:850;font-size:.92rem;line-height:1.9;}
    .resume-hero-meta span {display:inline-block;min-width:92px;opacity:.82;}
    .resume-section {background:#fff;border:1px solid #DDE7F3;border-radius:18px;padding:18px 18px 20px 18px;margin:16px 0;box-shadow:0 12px 32px rgba(9,30,66,.06);} 
    .resume-section-title {color:#0B4B93;font-size:1.12rem;font-weight:950;text-transform:uppercase;margin:0 0 14px 0;letter-spacing:-.02em;}
    .resume-note {background:#EAF4FF;border-radius:13px;padding:12px 16px;color:#0A3472;font-size:.88rem;font-weight:800;margin-bottom:16px;}
    .resume-kpi-grid {display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;}
    .resume-kpi-card {background:#fff;border:1px solid #DCE6F2;border-radius:15px;min-height:164px;padding:18px 14px;text-align:center;box-shadow:0 7px 22px rgba(9,30,66,.055);display:flex;flex-direction:column;justify-content:center;align-items:center;}
    .resume-kpi-icon {font-size:1.9rem;margin-bottom:8px;}
    .resume-kpi-title {font-size:.76rem;font-weight:950;text-transform:uppercase;color:#071E49;min-height:28px;display:flex;align-items:center;}
    .resume-kpi-value {font-size:1.62rem;font-weight:950;color:#061A44;line-height:1.05;margin-top:7px;}
    .resume-kpi-subtitle {font-size:.78rem;font-weight:850;color:#52627A;margin-top:5px;}
    .resume-kpi-delta {font-size:.76rem;font-weight:950;margin-top:12px;line-height:1.25;}
    .kpi-good{color:#06833D}.kpi-bad{color:#E11D1D}.kpi-neutral{color:#8A97AA}
    .resume-op-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;}
    .resume-op-card {position:relative;overflow:hidden;background:#fff;border:1px solid #DCE6F2;border-radius:18px;min-height:190px;padding:25px 28px;display:grid;grid-template-columns:86px 1fr;gap:18px;align-items:center;box-shadow:0 10px 28px rgba(9,30,66,.055);} 
    .resume-op-bg {position:absolute;right:-34px;top:-54px;width:128px;height:128px;border-radius:999px;opacity:.55;}
    .op-blue .resume-op-bg{background:#EAF2FF}.op-yellow .resume-op-bg{background:#FFF4D8}.op-green .resume-op-bg{background:#E7F8F2}
    .resume-op-icon {width:66px;height:66px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:1.7rem;font-weight:900;}
    .op-blue .resume-op-icon{background:#EAF2FF;color:#0F6BFF}.op-yellow .resume-op-icon{background:#FFF1C7;color:#F59E0B}.op-green .resume-op-icon{background:#DDF8EC;color:#18A46B}
    .resume-op-title {font-size:.98rem;font-weight:950;color:#071E49;margin-bottom:8px;}
    .resume-op-value {font-size:1.75rem;font-weight:950;color:#061A44;line-height:1.05;}
    .resume-op-subtitle {font-size:.82rem;color:#52627A;font-weight:850;margin-top:7px;}
    .resume-op-detail {font-size:.82rem;color:#8A97AA;font-weight:850;margin-top:10px;line-height:1.35;}
    .resume-progress {height:9px;background:#DDE5F0;border-radius:999px;overflow:hidden;margin-top:12px;}
    .resume-progress span {display:block;height:100%;background:#18A46B;border-radius:999px;}
    .resume-chart-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:16px 0;}
    .resume-chart-card {background:#fff;border:1px solid #DDE7F3;border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(9,30,66,.055);}
    .resume-chart-title {font-size:1rem;font-weight:950;color:#071E49;margin:0 0 8px 0;}
    .resume-insight-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:16px;}
    .resume-insight-card {border-radius:18px;border:1px solid;padding:0;min-height:232px;overflow:hidden;background:#fff;box-shadow:0 10px 26px rgba(9,30,66,.055);} 
    .resume-insight-head {font-weight:950;font-size:.88rem;margin:0;padding:13px 16px;text-transform:uppercase;text-align:center;color:#fff;letter-spacing:.01em;}
    .resume-insight-card ul{list-style:none;margin:0;padding:18px 22px 10px 22px}.resume-insight-card li{display:flex;gap:10px;margin-bottom:13px;font-size:.88rem;font-weight:750;line-height:1.38;color:#1D2738}
    .resume-insight-card li span:first-child{width:22px;height:22px;border-radius:999px;display:inline-flex;align-items:center;justify-content:center;flex:0 0 22px;font-size:.78rem;}
    .insight-good{border-color:#BBF7D0}.insight-good .resume-insight-head{background:#2E974B}.insight-good li span:first-child{background:#E8F5E9;color:#168A4A}
    .insight-warning{border-color:#FDE68A}.insight-warning .resume-insight-head{background:#F59E0B}.insight-warning li span:first-child{background:#FFF4D6;color:#B56A00}
    .insight-danger{border-color:#BFDBFE}.insight-danger .resume-insight-head{background:#0B63B6}.insight-danger li span:first-child{background:#E6F1FF;color:#0B63B6}
    .resume-reminder{background:#06345F;color:white;border-radius:14px;padding:14px 18px;font-weight:850;margin:16px 0;}
    @media(max-width:1200px){.resume-hero,.resume-kpi-grid,.resume-op-grid,.resume-chart-grid,.resume-insight-grid{grid-template-columns:1fr}.resume-hero-meta{border-left:0;padding-left:0}}
    </style>
    """, unsafe_allow_html=True)

    last_truth = state.get("last_truth") or []
    team_truth = next((row for row in last_truth if row.get("team") == team), None)

    if not team_truth:
        st.markdown(
            f"""
            <div class="resume-hero">
                <div class="resume-hero-icon">📊</div>
                <div><div class="resume-hero-title">RESUMEN DE TU EMPRESA</div><div class="resume-hero-subtitle">Resultados y desempeño de tu empresa en la ronda actual</div></div>
                <div class="resume-hero-meta"><div><span>⚙️ Ronda:</span>{_html_escape(round_n)}</div><div><span>👥 Equipo:</span>{_html_escape(team)}</div><div><span>🏆 Ranking:</span>—</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info("Aún no hay resultados de una ronda cerrada. Cuando cierres la primera ronda, aparecerá el resumen visual del equipo.")
        return

    history_rows = _team_rows()
    prev = history_rows[-2] if len(history_rows) >= 2 else None

    units = _num(team_truth.get("units", 0.0))
    profit = _num(team_truth.get("profit", 0.0))
    share = _num(team_truth.get("share", 0.0))
    produced = _num(team_truth.get("production_units", team_truth.get("units_produced", units)))
    demand = _num(team_truth.get("demand_potential", units))
    stock = _num(team_truth.get("inventory_final", 0.0))
    lost_sales = max(0.0, demand - units)

    prev_units = _num(prev.get("units"), None) if prev else None
    prev_profit = _num(prev.get("profit"), None) if prev else None
    prev_share = _num(prev.get("share"), None) if prev else None
    prev_produced = _num(prev.get("production_units", prev.get("units_produced", produced)), None) if prev else None
    prev_demand = _num(prev.get("demand_potential", prev.get("units", demand)), None) if prev else None
    prev_stock = _num(prev.get("inventory_final", stock), None) if prev else None

    units_delta, units_tone = _delta_pct(units, prev_units)
    profit_delta, profit_tone = _delta_pct(profit, prev_profit)
    share_delta, share_tone = _delta_pp(share, prev_share)
    produced_delta, _ = _delta_pct(produced, prev_produced)
    demand_delta, _ = _delta_pct(demand, prev_demand)
    stock_delta, _ = _delta_pct(stock, prev_stock)
    ranking, ranking_note = _ranking(last_truth)
    round_display = (state.get("history") or [{}])[-1].get("round", round_n) if state.get("history") else round_n

    st.markdown(
        f"""
        <div class="resume-hero">
            <div class="resume-hero-icon">📊</div>
            <div>
                <div class="resume-hero-title">RESUMEN DE TU EMPRESA</div>
                <div class="resume-hero-subtitle">Resultados y desempeño de tu empresa en la ronda actual</div>
            </div>
            <div class="resume-hero-meta">
                <div><span>⚙️ Ronda:</span>{_html_escape(round_display)}</div>
                <div><span>👥 Equipo:</span>{_html_escape(team)}</div>
                <div><span>🏆 Ranking:</span>{_html_escape(ranking)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    kpis = "".join([
        _kpi_card("Ventas", "🛍️", _fmt_units(units), "unidades", units_delta, units_tone),
        _kpi_card("Beneficio", "🪙", fmt_eur(profit), "resultado neto", profit_delta, profit_tone),
        _kpi_card("Cuota de mercado", "◔", f"{share*100:.1f}%".replace(".", ","), "peso competitivo", share_delta, share_tone),
        _kpi_card("Caja", "💼", fmt_eur(current_team_budget), "disponible", "Para la próxima decisión", "neutral"),
        _kpi_card("Posición global", "🏆", ranking, "ranking del juego", ranking_note, "neutral"),
    ])
    st.markdown(
        f"""
        <div class="resume-section">
            <div class="resume-section-title">1. INDICADORES PRINCIPALES</div>
            <div class="resume-note">ⓘ Estos son los resultados clave de tu empresa y su evolución respecto a la ronda anterior.</div>
            <div class="resume-kpi-grid">{kpis}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stock_pct = 0.0 if demand <= 0 else (stock / max(demand, 1.0)) * 100
    stock_label = "Stock bajo" if stock_pct < 10 else "Stock controlado" if stock_pct < 25 else "Stock elevado"
    ops = "".join([
        _op_card("Unidades fabricadas", "🏭", _fmt_units(produced), "unidades producidas", produced_delta, progress=min(100, produced / max(demand, 1) * 100), tone="blue"),
        _op_card("Demanda potencial", "⚡", _fmt_units(demand), "unidades", f"{_fmt_units(lost_sales)} ventas perdidas · {demand_delta}", progress=min(100, units / max(demand, 1) * 100), tone="yellow"),
        _op_card("Stock acumulado", "📦", _fmt_units(stock), stock_label, f"{stock_pct:.1f}% de la demanda potencial · {stock_delta}".replace(".", ","), progress=stock_pct, tone="green"),
    ])
    st.markdown(
        f"""
        <div class="resume-section">
            <div class="resume-section-title">2. OPERACIONES Y MERCADO</div>
            <div class="resume-note">ⓘ Estas métricas muestran si tu producción está alineada con la demanda y cuánto inventario arrastras.</div>
            <div class="resume-op-grid">{ops}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Gráficos e insights actuales se mantienen debajo para no perder información.
    g1, g2 = st.columns(2)
    with g1:
        with st.container(border=True):
            st.markdown('<div class="resume-chart-title">Evolución del beneficio</div>', unsafe_allow_html=True)
            st.plotly_chart(render_team_profit_chart(team, state.get("history", [])), use_container_width=True, config={"displayModeBar": False})
    with g2:
        with st.container(border=True):
            st.markdown('<div class="resume-chart-title">Evolución de cuota de mercado</div>', unsafe_allow_html=True)
            st.plotly_chart(render_team_share_chart(team, state.get("history", [])), use_container_width=True, config={"displayModeBar": False})

    # =========================================================
    # FASE 4: ANÁLISIS DE DESEMPEÑO / CONCLUSIONES PRO
    # =========================================================
    best, weak, improve = build_team_quick_reading(team_truth, current_team_budget)

    def _short_items(main_text, fallback_items):
        items = []
        if main_text:
            items.append(main_text)
        for item in fallback_items:
            if item and item not in items:
                items.append(item)
        return items[:3]

    best_items = _short_items(best, [
        f"Ventas conseguidas: {_fmt_units(units)} unidades.",
        f"Cuota actual: {share * 100:.1f}% del mercado.".replace('.', ','),
        f"Caja disponible para decidir: {fmt_eur(current_team_budget)}.",
    ])
    improve_items = _short_items(improve, [
        "Ajusta producción, inversión y foco de mercado.",
        "Revisa la relación entre demanda potencial, ventas y stock.",
        "Prioriza las palancas que más impacto tengan en la siguiente ronda.",
    ])
    critical_items = _short_items(weak, [
        "Vigila tu posición frente al resto de equipos.",
        "Evita que el stock o las ventas perdidas condicionen la próxima decisión.",
        "Contrasta este resumen con los informes antes de decidir.",
    ])

    st.markdown(
        "<div class='resume-section'>"
        "<div class='resume-section-title'>4. ANÁLISIS DE DESEMPEÑO</div>"
        "<div class='resume-note'>ⓘ Lectura ejecutiva de lo que funciona, lo que conviene ajustar y el punto más delicado de la ronda.</div>"
        "<div class='resume-insight-grid'>" +
        _insight_card("Lo estás haciendo bien", "✅", best_items, "good") +
        _insight_card("Aspectos a mejorar", "⚠️", improve_items, "warning") +
        _insight_card("Punto crítico", "🎯", critical_items, "danger") +
        "</div>"
        "</div>"
        "<div class='resume-reminder'>💡 RECUERDA: Entender tu desempeño es el primer paso para tomar mejores decisiones.</div>",
        unsafe_allow_html=True,
    )

def _html_escape(value):
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _fmt_int_plain(value):
    try:
        return f"{int(round(float(value))):,}".replace(",", ".")
    except Exception:
        return str(value)


SEGMENT_NAME_MAP = {
    "Price Seekers": "Ahorradores",
    "Mainstream": "Equilibrados",
    "Brand Lovers": "Exigentes",
}


def segment_name_es(name):
    return SEGMENT_NAME_MAP.get(str(name), str(name))


def _market_segment_insights(last_research, team):
    segment_sizes = last_research.get("segment_sizes", {}) if last_research else {}
    seg_mix = last_research.get("segment_brand_mix", {}) if last_research else {}
    total_market = sum(float(v) for v in segment_sizes.values()) if segment_sizes else 0.0

    biggest_segment = None
    biggest_size = 0.0
    biggest_pct = 0.0
    if segment_sizes:
        biggest_segment, biggest_size = max(segment_sizes.items(), key=lambda x: float(x[1]))
        biggest_size = float(biggest_size)
        biggest_pct = biggest_size / max(total_market, 1.0)

    best_segment = None
    best_value = 0.0
    if seg_mix:
        for seg, vals in seg_mix.items():
            val = float(vals.get(team, 0.0))
            if best_segment is None or val > best_value:
                best_segment = seg
                best_value = val

    segment_sales = {}
    if segment_sizes and seg_mix:
        for seg, size in segment_sizes.items():
            segment_sales[seg] = float(size) * float(seg_mix.get(seg, {}).get(team, 0.0))

    main_sales_segment = None
    main_sales_value = 0.0
    main_sales_pct = 0.0
    total_team_segment_sales = sum(segment_sales.values()) if segment_sales else 0.0
    if segment_sales and total_team_segment_sales > 0:
        main_sales_segment, main_sales_value = max(segment_sales.items(), key=lambda x: x[1])
        main_sales_pct = main_sales_value / max(total_team_segment_sales, 1.0)

    return {
        "total_market": total_market,
        "biggest_segment": biggest_segment,
        "biggest_size": biggest_size,
        "biggest_pct": biggest_pct,
        "best_segment": best_segment,
        "best_value": best_value,
        "main_sales_segment": main_sales_segment,
        "main_sales_value": main_sales_value,
        "main_sales_pct": main_sales_pct,
        "total_team_segment_sales": total_team_segment_sales,
    }


def _market_public_insights(last_truth):
    if not last_truth:
        return {}
    df = pd.DataFrame(last_truth).copy()
    if df.empty:
        return {}
    share_leader = df.sort_values("share", ascending=False).iloc[0]
    sales_leader = df.sort_values("units", ascending=False).iloc[0]
    avg_price = float(df["price"].mean()) if "price" in df.columns else 0.0
    return {
        "share_leader_team": share_leader.get("team", "-"),
        "share_leader_value": float(share_leader.get("share", 0.0)),
        "sales_leader_team": sales_leader.get("team", "-"),
        "sales_leader_value": float(sales_leader.get("units", 0.0)),
        "avg_price": avg_price,
    }


def _build_market_reading(last_research, last_truth, team):
    seg = _market_segment_insights(last_research, team) if last_research else {}
    public = _market_public_insights(last_truth) if last_truth else {}

    opportunity = "Aún no hay datos suficientes para detectar una oportunidad clara."
    risk = "Aún no hay datos suficientes para detectar un riesgo claro."
    recommendation = "Cierra una ronda para generar una lectura estratégica del mercado."

    best_segment = seg.get("best_segment")
    best_value = float(seg.get("best_value", 0.0) or 0.0)
    biggest_segment = seg.get("biggest_segment")
    biggest_pct = float(seg.get("biggest_pct", 0.0) or 0.0)
    main_sales_segment = seg.get("main_sales_segment")
    main_sales_pct = float(seg.get("main_sales_pct", 0.0) or 0.0)

    if best_segment:
        opportunity = (
            f"Tu mejor encaje aparece en {segment_name_es(best_segment)}, con una afinidad estimada del "
            f"{best_value * 100:.1f}%. Puede ser una buena zona para defender o reforzar tu propuesta."
        )
    elif biggest_segment:
        opportunity = (
            f"El segmento más grande es {segment_name_es(biggest_segment)}, con un peso aproximado del "
            f"{biggest_pct * 100:.1f}% del mercado."
        )

    if main_sales_segment and main_sales_pct >= 0.50:
        risk = (
            f"Tus ventas dependen mucho de {segment_name_es(main_sales_segment)} "
            f"({main_sales_pct * 100:.1f}% de tus ventas segmentadas). Si cambia ese segmento, tu cuota puede resentirse."
        )
    elif public and public.get("share_leader_value", 0.0) >= 0.30:
        risk = (
            f"{public.get('share_leader_team')} concentra una cuota elevada "
            f"({public.get('share_leader_value', 0.0) * 100:.1f}%). El mercado puede estar empezando a concentrarse."
        )
    elif biggest_segment:
        risk = "No se aprecia una dependencia extrema, pero conviene vigilar cómo evoluciona el liderazgo por segmentos."

    if best_segment and main_sales_segment and best_segment != main_sales_segment:
        recommendation = (
            f"Tu mejor afinidad está en {segment_name_es(best_segment)}, pero tu mayor peso de ventas parece estar en {segment_name_es(main_sales_segment)}. "
            f"Revisa si tu comunicación, precio y distribución están empujando el segmento correcto."
        )
    elif best_segment:
        recommendation = f"Refuerza las variables que más encajan con {segment_name_es(best_segment)}: producto, distribución, comunicación y precio coherente."
    elif last_truth:
        recommendation = "Compara tu cuota, ventas y precio con los líderes para identificar qué palanca competitiva debes reforzar."

    return opportunity, risk, recommendation


def render_market_info_panel(title, lines, tone="info"):
    body = "".join(f"<li>{_html_escape(line)}</li>" for line in lines if line)
    if not body:
        body = "<li>No hay datos suficientes para generar esta lectura.</li>"
    tone_class = {
        "positive": "sim-reading-positive",
        "warning": "sim-reading-warning",
        "danger": "sim-reading-danger",
        "info": "sim-reading-info",
    }.get(tone, "sim-reading-info")
    st.markdown(
        f'''
        <div class="sim-reading-card {tone_class}" style="min-height: 220px;">
            <div class="sim-reading-title">{_html_escape(title)}</div>
            <div class="sim-reading-body"><ul style="margin-top:0; padding-left:1.1rem;">{body}</ul></div>
        </div>
        ''',
        unsafe_allow_html=True,
    )





# =========================================================
# HELPERS INFORME DE MERCADO - VARIACIÓN DE COMPRADORES
# =========================================================
def _market_get_segment_active_buyers(research, seg=None):
    """Devuelve compradores activos estimados del mercado o de un segmento.

    Prioridad:
    1) Datos explícitos del engine: segment_active_buyers / segment_buyers
    2) Tasas explícitas: segment_activation_rate / segment_activation_rates
    3) Fallback compatible con rondas antiguas: _segment_active_buyers
    """
    if not research:
        return 0.0

    active = research.get("segment_active_buyers") or research.get("segment_buyers") or {}
    if isinstance(active, dict) and active:
        if seg is None:
            return sum(float(v or 0.0) for v in active.values())
        return float(active.get(seg, active.get(segment_name_es(seg), 0.0)) or 0.0)

    sizes = research.get("segment_sizes", {}) or {}
    activation = research.get("segment_activation_rate") or research.get("segment_activation_rates") or {}

    if seg is None:
        total = 0.0
        for i, (s, size) in enumerate(sizes.items()):
            rate = activation.get(s, activation.get(segment_name_es(s), None)) if isinstance(activation, dict) else None
            if rate is None:
                total += _segment_active_buyers(research, s, i)
            else:
                total += float(size or 0.0) * float(rate or 0.0)
        return total

    size = float(sizes.get(seg, sizes.get(segment_name_es(seg), 0.0)) or 0.0)
    rate = activation.get(seg, activation.get(segment_name_es(seg), None)) if isinstance(activation, dict) else None
    if rate is None:
        try:
            seg_idx = list(sizes.keys()).index(seg)
        except Exception:
            seg_idx = 0
        return _segment_active_buyers(research, seg, seg_idx)
    return size * float(rate or 0.0)

def _market_buyers_variation_pct(current_research, previous_research, seg=None):
    """Calcula la variación porcentual de compradores activos frente a la ronda anterior."""
    current = _market_get_segment_active_buyers(current_research, seg)
    previous = _market_get_segment_active_buyers(previous_research, seg)

    if previous <= 0:
        return None

    return ((current - previous) / previous) * 100.0


def _format_buyer_variation_html(v):
    """Devuelve HTML seguro para mostrar la variación de compradores."""
    if v is None:
        return "<span style='color:#667085;font-weight:800;'>—</span>"

    try:
        v = float(v)
    except Exception:
        return "<span style='color:#667085;font-weight:800;'>—</span>"

    if v > 0:
        return f"<span style='color:#168A4A;font-weight:900;'>▲ +{v:.1f}%</span>".replace(".", ",")
    if v < 0:
        return f"<span style='color:#B42318;font-weight:900;'>▼ {v:.1f}%</span>".replace(".", ",")

    return "<span style='color:#667085;font-weight:900;'>0,0%</span>"


def inject_market_phase1_styles():
    """Estilos PRO para la pantalla Mercado (fase 1)."""
    st.markdown(
        """
        <style>
        .market-page-hero {
            background: linear-gradient(135deg,#083763 0%,#072B55 100%);
            color:#fff;
            border-radius:18px;
            padding:22px 26px;
            margin:6px 0 20px 0;
            display:grid;
            grid-template-columns:72px 1fr 220px;
            gap:18px;
            align-items:center;
            box-shadow:0 12px 34px rgba(8,43,85,.22);
        }
        .market-page-hero-icon {
            width:58px;
            height:58px;
            border-radius:15px;
            border:2px solid rgba(150,210,255,.60);
            background:rgba(255,255,255,.08);
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:2rem;
        }
        .market-page-hero-title {
            font-size:2rem;
            font-weight:950;
            letter-spacing:-.04em;
            line-height:1.05;
            color:#fff;
            margin:0;
        }
        .market-page-hero-subtitle {
            font-size:1rem;
            font-weight:750;
            opacity:.88;
            margin-top:7px;
        }
        .market-page-hero-meta {
            border-left:1px solid rgba(255,255,255,.28);
            padding-left:22px;
            font-weight:850;
            font-size:.90rem;
            line-height:1.75;
        }
        .market-page-hero-meta span {
            display:inline-block;
            min-width:76px;
            opacity:.82;
        }
        .market-section-title {
            color:#071E49;
            font-size:1.02rem;
            font-weight:950;
            margin:4px 0 12px 0;
            letter-spacing:-.02em;
        }
        .market-kpi-grid {
            display:grid;
            grid-template-columns:repeat(3,minmax(0,1fr));
            gap:16px;
            margin:0 0 18px 0;
        }
        .market-kpi-card-pro {
            background:#fff;
            border:1px solid #DDE7F3;
            border-radius:16px;
            padding:18px 20px;
            min-height:126px;
            box-shadow:0 8px 24px rgba(9,30,66,.055);
            display:flex;
            align-items:center;
            gap:16px;
        }
        .market-kpi-icon-pro {
            width:64px;
            height:64px;
            border-radius:50%;
            color:#fff;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:1.72rem;
            flex:0 0 64px;
            box-shadow:0 12px 24px rgba(9,30,66,.13);
        }
        .market-kpi-label-pro {
            color:#071E49;
            font-size:.80rem;
            font-weight:950;
            line-height:1.15;
            margin-bottom:7px;
        }
        .market-kpi-value-pro {
            color:#071E49;
            font-size:1.62rem;
            font-weight:950;
            line-height:1.05;
            letter-spacing:-.03em;
        }
        .market-kpi-note-pro {
            margin-top:7px;
            color:#64748B;
            font-size:.80rem;
            font-weight:750;
        }
        .market-chart-title-pro {
            display:flex;
            align-items:center;
            gap:9px;
            color:#071E49;
            font-size:1.02rem;
            font-weight:950;
            margin-bottom:4px;
        }
        .market-chart-subtitle-pro {
            color:#53657D;
            font-size:.86rem;
            font-weight:700;
            margin-bottom:8px;
        }
        .market-reading-card-pro {
            background:linear-gradient(180deg,#EEF6FF 0%,#F4F9FF 100%);
            border:1px solid #CFE3FF;
            border-left:6px solid #0F6BFF;
            border-radius:18px;
            padding:21px 23px;
            min-height:430px;
            box-shadow:0 10px 28px rgba(9,30,66,.055);
        }
        .market-reading-title-pro {
            display:flex;
            align-items:center;
            gap:10px;
            color:#071E49;
            font-size:1.15rem;
            font-weight:950;
            margin-bottom:22px;
        }
        .market-reading-title-icon-pro {
            width:38px;
            height:38px;
            border-radius:50%;
            background:#0F6BFF;
            color:white;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:1.15rem;
            flex:0 0 38px;
        }
        .market-reading-list-pro {
            list-style:none;
            margin:0;
            padding:0;
        }
        .market-reading-list-pro li {
            display:flex;
            gap:12px;
            align-items:flex-start;
            margin-bottom:18px;
            color:#071E49;
            font-size:.94rem;
            line-height:1.45;
            font-weight:750;
        }
        .market-reading-bullet-pro {
            width:26px;
            height:26px;
            border-radius:50%;
            background:#0F6BFF;
            color:#fff;
            display:inline-flex;
            align-items:center;
            justify-content:center;
            flex:0 0 26px;
            font-size:.78rem;
            font-weight:950;
            margin-top:1px;
        }
        .market-reading-tip-pro {
            background:white;
            border:1px solid #DDE7F3;
            border-radius:14px;
            padding:14px 16px;
            color:#0A3472;
            font-size:.88rem;
            line-height:1.45;
            font-weight:850;
            margin-top:18px;
        }

        .market-sales-grid-pro {
            display:grid;
            grid-template-columns: .95fr 1.35fr;
            gap:16px;
            align-items:stretch;
            margin-bottom:18px;
        }
        .market-sales-card-pro {
            background:#fff;
            border:1px solid #DDE7F3;
            border-radius:18px;
            padding:18px 20px;
            box-shadow:0 10px 28px rgba(9,30,66,.055);
            min-height:390px;
        }
        .market-sales-metric-grid-pro {
            display:grid;
            grid-template-columns:repeat(2,minmax(0,1fr));
            gap:14px;
            margin-top:0;
        }
        .market-sales-mini-card-pro {
            background:#fff;
            border:1px solid #DDE7F3;
            border-radius:16px;
            padding:16px 18px;
            min-height:132px;
            box-shadow:0 8px 22px rgba(9,30,66,.045);
            display:flex;
            gap:13px;
            align-items:flex-start;
        }
        .market-sales-mini-icon-pro {
            width:46px;
            height:46px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            color:#fff;
            font-size:1.20rem;
            flex:0 0 46px;
            box-shadow:0 10px 20px rgba(9,30,66,.12);
        }
        .market-sales-mini-label-pro {
            color:#071E49;
            font-size:.78rem;
            font-weight:950;
            line-height:1.16;
            margin-bottom:6px;
        }
        .market-sales-mini-value-pro {
            color:#071E49;
            font-size:1.22rem;
            font-weight:950;
            line-height:1.08;
            letter-spacing:-.025em;
        }
        .market-sales-mini-note-pro {
            margin-top:7px;
            color:#64748B;
            font-size:.78rem;
            line-height:1.30;
            font-weight:700;
        }
        .market-sales-insight-pro {
            background:#EEF6FF;
            border:1px solid #CFE3FF;
            border-radius:16px;
            padding:15px 18px;
            margin-top:14px;
            color:#0A3472;
            font-size:.90rem;
            line-height:1.45;
            font-weight:850;
        }
        .market-sales-segment-list-pro {
            margin-top:14px;
            display:grid;
            gap:9px;
        }
        .market-sales-segment-row-pro {
            display:grid;
            grid-template-columns: 13px 1fr auto;
            gap:10px;
            align-items:center;
            padding:10px 12px;
            border:1px solid #E7EEF7;
            border-radius:12px;
            background:#FAFCFF;
            color:#071E49;
            font-size:.84rem;
            font-weight:850;
        }
        .market-sales-dot-pro {
            width:11px;
            height:11px;
            border-radius:50%;
            display:block;
        }
        .market-sales-row-sub-pro {
            display:block;
            color:#64748B;
            font-size:.72rem;
            font-weight:700;
            margin-top:2px;
        }

        .market-public-kpi-pro { display:flex; align-items:center; gap:14px; min-height:106px; margin-bottom:16px; }
        .market-public-kpi-icon-pro { width:58px; height:58px; border-radius:50%; color:white; display:flex; align-items:center; justify-content:center; font-size:1.45rem; flex:0 0 58px; box-shadow:0 12px 24px rgba(9,30,66,.12); }
        .market-public-kpi-label-pro { color:#071E49; font-size:.80rem; font-weight:950; line-height:1.15; margin-bottom:6px; }
        .market-public-kpi-value-pro { color:#071E49; font-size:1.52rem; font-weight:950; line-height:1.05; letter-spacing:-.03em; }
        .market-public-kpi-note-pro { margin-top:7px; color:#64748B; font-size:.80rem; font-weight:750; }
        .market-public-chart-title-pro { color:#071E49; font-size:1.02rem; font-weight:950; margin:2px 0 4px 0; }
        .market-public-chart-subtitle-pro { color:#53657D; font-size:.84rem; line-height:1.25; font-weight:750; margin-bottom:8px; }

        .market-summary-section-pro { background:#fff; border:1px solid #DDE7F3; border-radius:18px; padding:18px 18px 24px 18px; margin:20px 0 16px 0; box-shadow:0 12px 32px rgba(9,30,66,.06); }
        .market-summary-section-title-pro { color:#0B4B93; font-size:1.12rem; font-weight:950; text-transform:uppercase; margin:0 0 14px 0; letter-spacing:-.02em; }
        .market-summary-note-pro { background:#EAF4FF; border-radius:13px; padding:12px 16px; color:#0A3472; font-size:.88rem; font-weight:850; margin-bottom:20px; }
        .market-summary-insight-grid-pro { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:18px; }
        .market-summary-insight-card-pro { border-radius:18px; border:1px solid; overflow:hidden; background:#fff; min-height:315px; box-shadow:0 10px 26px rgba(9,30,66,.055); }
        .market-summary-insight-head-pro { color:white; font-weight:950; font-size:.90rem; margin:0; padding:14px 16px; text-transform:uppercase; text-align:center; letter-spacing:.01em; }
        .market-summary-insight-body-pro { padding:24px 28px 18px 28px; }
        .market-summary-insight-body-pro ul { list-style:none; margin:0; padding:0; }
        .market-summary-insight-body-pro li { display:flex; gap:13px; align-items:flex-start; margin-bottom:18px; color:#071E49; font-size:.92rem; line-height:1.45; font-weight:800; }
        .market-summary-bullet-pro { width:24px; height:24px; border-radius:999px; display:inline-flex; align-items:center; justify-content:center; flex:0 0 24px; font-size:.78rem; font-weight:950; margin-top:1px; }
        .market-summary-good-pro { border-color:#BBF7D0; } .market-summary-good-pro .market-summary-insight-head-pro { background:#2E974B; } .market-summary-good-pro .market-summary-bullet-pro { background:#E8F5E9; color:#168A4A; }
        .market-summary-warn-pro { border-color:#FDE68A; } .market-summary-warn-pro .market-summary-insight-head-pro { background:#F59E0B; } .market-summary-warn-pro .market-summary-bullet-pro { background:#FFF4D6; color:#B56A00; }
        .market-summary-blue-pro { border-color:#BFDBFE; } .market-summary-blue-pro .market-summary-insight-head-pro { background:#0B63B6; } .market-summary-blue-pro .market-summary-bullet-pro { background:#E6F1FF; color:#0B63B6; }

        .market-action-shell-pro {
            background:#fff;
            border:1px solid #DDE7F3;
            border-radius:18px;
            padding:18px 20px;
            box-shadow:0 10px 28px rgba(9,30,66,.055);
            margin-bottom:18px;
        }
        .market-action-head-pro {
            display:flex;
            align-items:flex-start;
            justify-content:space-between;
            gap:16px;
            margin-bottom:16px;
        }
        .market-action-title-pro {
            color:#071E49;
            font-size:1.10rem;
            line-height:1.12;
            font-weight:950;
            letter-spacing:-.025em;
            margin:0;
        }
        .market-action-subtitle-pro {
            color:#53657D;
            font-size:.86rem;
            font-weight:700;
            line-height:1.35;
            margin-top:5px;
        }
        .market-action-badge-pro {
            background:#EEF6FF;
            color:#0B63B6;
            border:1px solid #CFE3FF;
            border-radius:999px;
            padding:8px 13px;
            font-size:.78rem;
            font-weight:950;
            white-space:nowrap;
        }
        .market-action-grid-pro {
            display:grid;
            grid-template-columns:repeat(3,minmax(0,1fr));
            gap:14px;
            margin-bottom:14px;
        }
        .market-action-card-pro {
            border:1px solid #E3EAF2;
            border-radius:16px;
            padding:16px 17px;
            background:#FAFCFF;
            min-height:190px;
            position:relative;
            overflow:hidden;
        }
        .market-action-card-pro:before {
            content:"";
            position:absolute;
            inset:0 auto 0 0;
            width:5px;
            background:#0F6BFF;
        }
        .market-action-card-pro.action-green:before { background:#16A34A; }
        .market-action-card-pro.action-orange:before { background:#F59E0B; }
        .market-action-card-pro.action-purple:before { background:#7C3AED; }
        .market-action-card-title-pro {
            display:flex;
            align-items:center;
            gap:10px;
            color:#071E49;
            font-size:.92rem;
            font-weight:950;
            margin-bottom:10px;
        }
        .market-action-icon-pro {
            width:34px;
            height:34px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            color:white;
            font-size:1rem;
            flex:0 0 34px;
            background:#0F6BFF;
            box-shadow:0 8px 18px rgba(9,30,66,.12);
        }
        .action-green .market-action-icon-pro { background:#16A34A; }
        .action-orange .market-action-icon-pro { background:#F59E0B; }
        .action-purple .market-action-icon-pro { background:#7C3AED; }
        .market-action-main-pro {
            color:#071E49;
            font-size:1.18rem;
            font-weight:950;
            line-height:1.12;
            margin-bottom:8px;
            letter-spacing:-.02em;
        }
        .market-action-text-pro {
            color:#344054;
            font-size:.86rem;
            line-height:1.38;
            font-weight:700;
        }
        .market-action-check-grid-pro {
            display:grid;
            grid-template-columns:repeat(4,minmax(0,1fr));
            gap:10px;
        }
        .market-action-check-pro {
            background:#F4F8FE;
            border:1px solid #E3EAF2;
            border-radius:14px;
            padding:12px 13px;
            color:#071E49;
            font-size:.82rem;
            font-weight:850;
            line-height:1.32;
            min-height:74px;
        }
        .market-action-check-pro b {
            display:block;
            color:#0B63B6;
            font-size:.75rem;
            text-transform:uppercase;
            letter-spacing:.03em;
            margin-bottom:4px;
        }
        @media(max-width:1200px){
            .market-page-hero,.market-kpi-grid{grid-template-columns:1fr;}
            .market-page-hero-meta{border-left:0;padding-left:0;}
            .market-reading-card-pro{min-height:auto;}
            .market-sales-grid-pro,.market-sales-metric-grid-pro{grid-template-columns:1fr;}
            .market-sales-card-pro{min-height:auto;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_market_page_kpi(label, value, note, icon, color):
    st.markdown(
        f"""
        <div class="market-kpi-card-pro">
            <div class="market-kpi-icon-pro" style="background:{color};">{icon}</div>
            <div>
                <div class="market-kpi-label-pro">{_html_escape(label)}</div>
                <div class="market-kpi-value-pro">{value}</div>
                <div class="market-kpi-note-pro">{_html_escape(note)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_market_segment_chart_phase1(last_research):
    fig = go.Figure()
    segment_sizes = last_research.get("segment_sizes", {}) if last_research else {}

    if segment_sizes:
        labels = [segment_name_es(k) for k in segment_sizes.keys()]
        values = [float(v) for v in segment_sizes.values()]
        colors = [_segment_color(i) if "_segment_color" in globals() else "#0F6BFF" for i in range(len(labels))]
        fig.add_trace(
            go.Bar(
                x=labels,
                y=values,
                text=[_fmt_int_plain(v) for v in values],
                textposition="inside",
                insidetextanchor="middle",
                marker=dict(color=colors, line=dict(width=0)),
                hovertemplate="<b>%{x}</b><br>Tamaño: %{y:,.0f}<extra></extra>",
            )
        )
    else:
        fig.add_annotation(
            text="Aún no hay datos de segmentos de una ronda cerrada.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(color="#64748B", size=13),
        )

    max_value = max([float(v) for v in segment_sizes.values()], default=1.0)
    fig.update_layout(
        height=430,
        margin=dict(l=18, r=18, t=12, b=38),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        font=dict(family="Inter, Arial, sans-serif", color="#071E49"),
        bargap=0.28,
        xaxis=dict(
            title="Segmento",
            showgrid=False,
            tickfont=dict(color="#64748B", size=12),
            fixedrange=True,
        ),
        yaxis=dict(
            title="Tamaño (unidades)",
            gridcolor="#E8EEF6",
            zeroline=False,
            range=[0, max_value * 1.18],
            tickfont=dict(color="#64748B", size=12),
            fixedrange=True,
        ),
    )
    return fig



def build_team_segment_sales_chart_phase2(last_research, team_name):
    fig = go.Figure()

    if not last_research:
        fig.add_annotation(
            text="Aún no hay datos de segmentos de una ronda cerrada.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
            font=dict(color="#64748B", size=13),
        )
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="white", plot_bgcolor="white")
        return fig

    segment_sizes = last_research.get("segment_sizes", {})
    seg_mix = last_research.get("segment_brand_mix", {})
    segment_sales = {}
    for seg, size in segment_sizes.items():
        vals = seg_mix.get(seg, {})
        team_share = float(vals.get(team_name, 0.0))
        segment_sales[segment_name_es(seg)] = max(0.0, float(size) * team_share)

    total_sales = sum(segment_sales.values())
    if not segment_sales or total_sales <= 0:
        fig.add_annotation(
            text="No hay datos suficientes para calcular tus ventas por segmento.",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
            font=dict(color="#64748B", size=13),
        )
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="white", plot_bgcolor="white")
        return fig

    labels = list(segment_sales.keys())
    values = [segment_sales[s] for s in labels]
    colors = [_segment_color(i) if "_segment_color" in globals() else "#0F6BFF" for i in range(len(labels))]
    fig.add_trace(
        go.Pie(
            labels=labels, values=values, hole=0.54, sort=False,
            marker=dict(colors=colors, line=dict(color="white", width=3)),
            textinfo="percent", textposition="inside",
            hovertemplate="<b>%{label}</b><br>Ventas estimadas: %{value:,.0f}<br>Peso en tus ventas: %{percent}<extra></extra>",
        )
    )
    fig.add_annotation(
        text=f"<b>{_fmt_int_plain(total_sales)}</b><br><span style='font-size:11px;color:#64748B'>uds.</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(color="#071E49", size=17),
    )
    fig.update_layout(
        height=330, margin=dict(l=0, r=0, t=8, b=8), paper_bgcolor="white", plot_bgcolor="white",
        showlegend=True, legend=dict(orientation="v", x=0.72, y=0.5, font=dict(size=12, color="#071E49")),
        font=dict(family="Inter, Arial, sans-serif", color="#071E49"),
    )
    return fig


def _render_market_sales_mini_card(label, value, note, icon, color):
    st.markdown(
        f"""
        <div class="market-sales-mini-card-pro">
            <div class="market-sales-mini-icon-pro" style="background:{color};">{icon}</div>
            <div>
                <div class="market-sales-mini-label-pro">{_html_escape(label)}</div>
                <div class="market-sales-mini-value-pro">{value}</div>
                <div class="market-sales-mini-note-pro">{_html_escape(note)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_market_segment_sales_rows(last_research, team):
    segment_sizes = (last_research or {}).get("segment_sizes", {})
    seg_mix = (last_research or {}).get("segment_brand_mix", {})
    rows = []
    for i, (seg, size) in enumerate(segment_sizes.items()):
        team_share = float(seg_mix.get(seg, {}).get(team, 0.0))
        sales = float(size) * team_share
        rows.append((i, seg, sales, team_share))
    total_sales = max(sum(r[2] for r in rows), 1.0)
    html_rows = ""
    for i, seg, sales, team_share in rows:
        pct = sales / total_sales * 100 if total_sales else 0.0
        color = _segment_color(i) if "_segment_color" in globals() else "#0F6BFF"
        html_rows += (
            f"<div class='market-sales-segment-row-pro'>"
            f"<span class='market-sales-dot-pro' style='background:{color};'></span>"
            f"<div>{_html_escape(segment_name_es(seg))}<span class='market-sales-row-sub-pro'>Afinidad: {team_share*100:.1f}%</span></div>"
            f"<div>{_fmt_int_plain(sales)}<span class='market-sales-row-sub-pro' style='text-align:right;'>{pct:.1f}% ventas</span></div>"
            f"</div>"
        )
    st.markdown(f"<div class='market-sales-segment-list-pro'>{html_rows}</div>", unsafe_allow_html=True)


def _render_market_sales_phase2(last_research, team, seg):
    main_seg = seg.get("main_sales_segment")
    main_pct = float(seg.get("main_sales_pct", 0.0) or 0.0)
    best_seg = seg.get("best_segment")
    best_value = float(seg.get("best_value", 0.0) or 0.0)
    total_sales = float(seg.get("total_team_segment_sales", 0.0) or 0.0)

    dependency_label = "Alta" if main_pct >= 0.60 else "Media" if main_pct >= 0.40 else "Baja"
    dependency_note = (
        "Tus ventas están muy concentradas en un solo segmento."
        if dependency_label == "Alta"
        else "Existe cierta concentración, pero no es extrema."
        if dependency_label == "Media"
        else "Tus ventas están bastante repartidas entre segmentos."
    )
    dependency_color = "#EF4444" if dependency_label == "Alta" else "#F59E0B" if dependency_label == "Media" else "#16A34A"

    insight = "Todavía no hay datos suficientes para leer tus ventas por segmento."
    if main_seg and best_seg:
        if main_seg == best_seg:
            insight = f"Tu mayor peso de ventas coincide con tu mejor afinidad: {segment_name_es(main_seg)}. Es una posición coherente para defender y reforzar."
        else:
            insight = f"Tu mayor peso de ventas está en {segment_name_es(main_seg)}, pero tu mejor afinidad aparece en {segment_name_es(best_seg)}. Revisa si tu inversión está empujando el segmento correcto."
    elif main_seg:
        insight = f"Tu segmento principal de ventas es {segment_name_es(main_seg)}. Vigila si esa concentración aumenta en próximas rondas."

    st.markdown('<div class="market-section-title" style="margin-top:20px;">Tus ventas por segmento</div>', unsafe_allow_html=True)
    chart_col, detail_col = st.columns([.95, 1.35])
    with chart_col:
        with st.container(border=True):
            st.markdown(
                '<div class="market-chart-title-pro">◔ Tus ventas por segmento</div>'
                '<div class="market-chart-subtitle-pro">Peso estimado de cada segmento dentro de tus ventas.</div>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                build_team_segment_sales_chart_phase2(last_research, team),
                use_container_width=True,
                config={"displayModeBar": False, "responsive": True},
            )
            _render_market_segment_sales_rows(last_research, team)
    with detail_col:
        d1, d2 = st.columns(2)
        with d1:
            _render_market_sales_mini_card("Lectura de tus ventas", _fmt_int_plain(total_sales) if total_sales else "—", "Ventas estimadas distribuidas por segmento", "📈", "#0F6BFF")
        with d2:
            _render_market_sales_mini_card("Segmento principal de ventas", segment_name_es(main_seg) if main_seg else "—", f"{main_pct*100:.1f}% de tus ventas" if main_seg else "Sin datos segmentados", "👥", "#16A34A")
        d3, d4 = st.columns(2)
        with d3:
            _render_market_sales_mini_card("Dependencia de un segmento", dependency_label if main_seg else "—", dependency_note if main_seg else "Sin datos suficientes", "⚠️", dependency_color)
        with d4:
            _render_market_sales_mini_card("Mejor afinidad de tu marca", segment_name_es(best_seg) if best_seg else "—", f"Afinidad estimada: {best_value*100:.1f}%" if best_seg else "Sin datos de afinidad", "🎯", "#7C3AED")
        st.markdown(f"<div class='market-sales-insight-pro'>💡 <b>Insight:</b> {_html_escape(insight)}</div>", unsafe_allow_html=True)


def _build_public_competitor_chart_compact(last_truth, metric):
    """Gráficos compactos para la Fase 3 de Mercado, sin huecos verticales."""
    fig = go.Figure()
    if not last_truth:
        fig.add_annotation(text="Aún no hay datos públicos de una ronda cerrada.", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(color="#64748B", size=12))
    else:
        df = pd.DataFrame(last_truth).copy()
        if metric == "share":
            df = df.sort_values("share", ascending=True)
            x = (df["share"] * 100).round(1)
            text_values = [f"{v:.1f}%" for v in x]
            color_main = "#0F6BFF"
        elif metric == "units":
            df = df.sort_values("units", ascending=True)
            x = df["units"].astype(float)
            text_values = [_fmt_int_plain(v) for v in x]
            color_main = "#16A34A"
        else:
            df = df.sort_values("price", ascending=True)
            x = df["price"].astype(float).round(2)
            text_values = [f"{v:.2f}" for v in x]
            color_main = "#F59E0B"
        colors = [color_main if i == len(df) - 1 else "#BFC7D4" for i in range(len(df))]
        fig.add_trace(go.Bar(y=df["team"], x=x, orientation="h", text=text_values, textposition="outside", marker=dict(color=colors, line=dict(width=0)), cliponaxis=False, hovertemplate="<b>%{y}</b><br>%{x}<extra></extra>"))
        max_x = max([float(v) for v in x] + [1.0])
        fig.update_xaxes(range=[0, max_x * 1.22])
    fig.update_layout(height=260, margin=dict(l=70, r=28, t=8, b=20), plot_bgcolor="white", paper_bgcolor="white", showlegend=False, font=dict(family="Inter, Arial, sans-serif", color="#071E49"), xaxis=dict(showgrid=True, gridcolor="#E8EEF6", zeroline=False, title="", fixedrange=True, tickfont=dict(color="#64748B", size=11)), yaxis=dict(title="", fixedrange=True, tickfont=dict(color="#64748B", size=11)))
    return fig


def _market_public_kpi_html(label, value, note, icon, color):
    return (f"<div class='market-public-kpi-pro'>"
            f"<div class='market-public-kpi-icon-pro' style='background:{color};'>{icon}</div>"
            f"<div><div class='market-public-kpi-label-pro'>{_html_escape(label)}</div>"
            f"<div class='market-public-kpi-value-pro'>{value}</div>"
            f"<div class='market-public-kpi-note-pro'>{_html_escape(note)}</div></div></div>")


def _render_market_public_phase3(last_truth, public):
    """Bloque Información pública del mercado: KPI + gráfico dentro de la misma card."""
    cards = [
        {"label": "Líder en cuota", "value": public.get("share_leader_team", "-"), "note": f"{public.get('share_leader_value', 0.0) * 100:.1f}% de cuota" if public else "Sin datos", "icon": "🏆", "color": "#0F6BFF", "title": "Cuota de mercado por equipo", "subtitle": "Peso competitivo público por marca.", "metric": "share"},
        {"label": "Marca con más ventas", "value": public.get("sales_leader_team", "-"), "note": f"{_fmt_int_plain(public.get('sales_leader_value', 0.0))} unidades" if public else "Sin datos", "icon": "🛍️", "color": "#16A34A", "title": "Ventas por marca", "subtitle": "Unidades públicas vendidas por equipo.", "metric": "units"},
        {"label": "Precio medio del mercado", "value": f"{public.get('avg_price', 0.0):.2f}", "note": "Media simple de marcas", "icon": "🏷️", "color": "#F59E0B", "title": "Precio medio por marca", "subtitle": "Comparativa de precio observado.", "metric": "price"},
    ]
    cols = st.columns(3)
    for col, card in zip(cols, cards):
        with col:
            with st.container(border=True):
                st.markdown(_market_public_kpi_html(card["label"], card["value"], card["note"], card["icon"], card["color"]), unsafe_allow_html=True)
                st.markdown(f"<div class='market-public-chart-title-pro'>{_html_escape(card['title'])}</div><div class='market-public-chart-subtitle-pro'>{_html_escape(card['subtitle'])}</div>", unsafe_allow_html=True)
                st.plotly_chart(_build_public_competitor_chart_compact(last_truth, card["metric"]), use_container_width=True, config={"displayModeBar": False, "responsive": True})



def _build_market_phase5_recommendations(last_research, last_truth, team, seg, public):
    """Genera un plan de acción estratégico para la Fase 5 del apartado Mercado."""
    rows = _market_opportunity_rows(last_research, team) if last_research else []
    best_opp = None
    if rows:
        # Priorizamos oportunidad alta, después tamaño y después el encaje propio.
        def _opp_score(row):
            opp_score = 3 if row.get("opp") == "ALTA" else 2 if row.get("opp") == "MEDIA" else 1
            return (opp_score, float(row.get("pct", 0.0)), float(row.get("my_val", 0.0)))
        best_opp = max(rows, key=_opp_score)

    best_segment = seg.get("best_segment") if seg else None
    main_segment = seg.get("main_sales_segment") if seg else None
    main_pct = float(seg.get("main_sales_pct", 0.0) or 0.0) if seg else 0.0

    priority_seg = best_opp.get("seg") if best_opp else (best_segment or main_segment)
    priority_name = segment_name_es(priority_seg) if priority_seg else "Pendiente"

    if best_opp:
        priority_reason = (
            f"Combina {best_opp.get('pct', 0.0) * 100:.1f}% del mercado, liderazgo del "
            f"{best_opp.get('leader_val', 0.0) * 100:.1f}% y oportunidad {str(best_opp.get('opp', '')).lower()}."
        )
    elif best_segment:
        priority_reason = f"Es el segmento donde tu marca muestra mayor afinidad ({float(seg.get('best_value', 0.0) or 0.0) * 100:.1f}%)."
    else:
        priority_reason = "Aún faltan datos para priorizar un segmento con seguridad."

    if best_segment and main_segment and best_segment != main_segment:
        move_title = "Reorientar inversión"
        move_main = f"Alinear ventas con {segment_name_es(best_segment)}"
        move_text = (
            f"Tu mejor afinidad está en {segment_name_es(best_segment)}, pero tus ventas pesan más en "
            f"{segment_name_es(main_segment)}. Revisa comunicación, distribución y precio para empujar el segmento correcto."
        )
    elif main_segment and main_pct >= 0.60:
        move_title = "Reducir dependencia"
        move_main = f"No depender solo de {segment_name_es(main_segment)}"
        move_text = (
            f"El {main_pct * 100:.1f}% de tus ventas segmentadas se concentra en ese grupo. Mantén foco, pero prepara una segunda vía de crecimiento."
        )
    elif priority_seg:
        move_title = "Defender y escalar"
        move_main = f"Reforzar {priority_name}"
        move_text = "Mantén una propuesta coherente y concentra recursos en las palancas que mejor conviertan: producto, precio, distribución y comunicación."
    else:
        move_title = "Generar información"
        move_main = "Comprar informes y cerrar ronda"
        move_text = "Necesitas más información histórica para convertir el mercado en decisiones accionables."

    leader_team = public.get("share_leader_team") if public else None
    leader_share = float(public.get("share_leader_value", 0.0) or 0.0) if public else 0.0
    avg_price = float(public.get("avg_price", 0.0) or 0.0) if public else 0.0
    if leader_team and leader_share >= 0.45:
        watch_main = f"Vigilar a {leader_team}"
        watch_text = f"Concentra el {leader_share * 100:.1f}% de cuota. Evita atacarle frontalmente si no tienes una ventaja clara de propuesta o cobertura."
    elif leader_team:
        watch_main = "Mercado abierto"
        watch_text = f"{leader_team} lidera, pero la ventaja no parece insalvable. Busca segmentos con liderazgo menor y mejor encaje para tu marca."
    else:
        watch_main = "Sin líder claro"
        watch_text = "Todavía no hay suficientes datos públicos para leer el poder competitivo de cada marca."

    checks = [
        ("Precio", f"Compáralo con la media del mercado ({avg_price:.2f}) antes de decidir." if avg_price else "Comprueba si tu precio refuerza el segmento objetivo."),
        ("Distribución", f"Asegura cobertura suficiente en {priority_name}." if priority_seg else "Aumenta cobertura si la conversión es débil."),
        ("Comunicación", "Concentra mensajes en el segmento prioritario; evita repartir inversión sin foco."),
        ("Producto", "Ajusta atributos al motivo de compra del segmento elegido."),
    ]

    cards = [
        {"tone": "green", "icon": "🎯", "title": "Prioridad estratégica", "main": priority_name, "text": priority_reason},
        {"tone": "orange", "icon": "🧭", "title": move_title, "main": move_main, "text": move_text},
        {"tone": "purple", "icon": "👁️", "title": "Vigilancia competitiva", "main": watch_main, "text": watch_text},
    ]
    return cards, checks


def _render_market_phase5_action_plan(last_research, last_truth, team, seg, public):
    """Renderiza la Fase 5: plan de acción recomendado del apartado Mercado."""
    cards, checks = _build_market_phase5_recommendations(last_research, last_truth, team, seg, public)
    card_html = ""
    for card in cards:
        tone = card.get("tone", "green")
        card_html += (
            f"<div class='market-action-card-pro action-{tone}'>"
            f"<div class='market-action-card-title-pro'><span class='market-action-icon-pro'>{_html_escape(card.get('icon', '•'))}</span><span>{_html_escape(card.get('title', ''))}</span></div>"
            f"<div class='market-action-main-pro'>{_html_escape(card.get('main', ''))}</div>"
            f"<div class='market-action-text-pro'>{_html_escape(card.get('text', ''))}</div>"
            f"</div>"
        )

    check_html = ""
    for title, text in checks:
        check_html += f"<div class='market-action-check-pro'><b>{_html_escape(title)}</b>{_html_escape(text)}</div>"

    st.markdown(
        f"""
        <div class="market-action-shell-pro">
            <div class="market-action-head-pro">
                <div>
                    <div class="market-action-title-pro">5. Plan de acción recomendado</div>
                    <div class="market-action-subtitle-pro">Traduce la lectura del mercado en decisiones concretas para la próxima ronda.</div>
                </div>
                <div class="market-action-badge-pro">Fase 5 · Decisión accionable</div>
            </div>
            <div class="market-action-grid-pro">{card_html}</div>
            <div class="market-action-check-grid-pro">{check_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_market_quick_reading(segment_lines, seg):
    clean_lines = [x for x in segment_lines if x]
    if seg.get("best_segment"):
        clean_lines.append(
            f"Tu mejor encaje aparece en {segment_name_es(seg['best_segment'])}, con una afinidad estimada del {seg.get('best_value', 0.0) * 100:.1f}%."
        )
    if not clean_lines:
        clean_lines = ["Todavía no hay datos suficientes para generar una lectura rápida del mercado."]

    lis = "".join(
        f"<li><span class='market-reading-bullet-pro'>✓</span><span>{_html_escape(line)}</span></li>"
        for line in clean_lines[:4]
    )
    st.markdown(
        f"""
        <div class="market-reading-card-pro">
            <div class="market-reading-title-pro"><span class="market-reading-title-icon-pro">💡</span><span>Lectura rápida</span></div>
            <ul class="market-reading-list-pro">{lis}</ul>
            <div class="market-reading-tip-pro"><b>Consejo:</b> prioriza el segmento donde coincidan tamaño, oportunidad y encaje de marca.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _split_market_reading_items(text, fallback_items=None):
    """Convierte una lectura larga en 2-3 bullets para el formato visual tipo Resumen."""
    fallback_items = fallback_items or []
    items = []
    raw = str(text or "").strip()
    if raw:
        items.append(raw)
    for item in fallback_items:
        item = str(item or "").strip()
        if item and item not in items:
            items.append(item)
    return items[:3]


def _market_summary_insight_card(title, items, tone):
    cfg = {
        "good": ("market-summary-good-pro", "✅"),
        "warn": ("market-summary-warn-pro", "⚠️"),
        "blue": ("market-summary-blue-pro", "🎯"),
    }.get(tone, ("market-summary-blue-pro", "•"))
    cls, icon = cfg
    lis = "".join(
        f"<li><span class='market-summary-bullet-pro'>{icon}</span><span>{_html_escape(item)}</span></li>"
        for item in (items or []) if str(item).strip()
    )
    return (
        f"<div class='market-summary-insight-card-pro {cls}'>"
        f"<div class='market-summary-insight-head-pro'>{_html_escape(title)}</div>"
        f"<div class='market-summary-insight-body-pro'><ul>{lis}</ul></div>"
        f"</div>"
    )


def _render_market_reading_summary_section(last_research, last_truth, team, seg, public):
    """Lectura del mercado con el mismo formato visual del bloque de análisis del Resumen."""
    opportunity, risk, recommendation = _build_market_reading(last_research, last_truth, team)

    best_segment = seg.get("best_segment") if seg else None
    best_value = float(seg.get("best_value", 0.0) or 0.0) if seg else 0.0
    main_segment = seg.get("main_sales_segment") if seg else None
    main_pct = float(seg.get("main_sales_pct", 0.0) or 0.0) if seg else 0.0
    leader_team = public.get("share_leader_team") if public else None
    leader_share = float(public.get("share_leader_value", 0.0) or 0.0) if public else 0.0

    opportunity_items = _split_market_reading_items(opportunity, [
        f"Mejor encaje: {segment_name_es(best_segment)} ({best_value * 100:.1f}%)." if best_segment else "Busca el segmento donde coincidan tamaño, oportunidad y encaje.",
        "Prioriza inversión donde puedas crecer sin enfrentarte directamente al líder dominante.",
    ])
    risk_items = _split_market_reading_items(risk, [
        f"Vigila la dependencia de {segment_name_es(main_segment)} ({main_pct * 100:.1f}% de tus ventas)." if main_segment else "Vigila la concentración de ventas por segmento.",
        f"{leader_team} lidera con {leader_share * 100:.1f}% de cuota." if leader_team else "Observa si aparece un líder claro en próximas rondas.",
    ])
    recommendation_items = _split_market_reading_items(recommendation, [
        "Ajusta precio, distribución, comunicación y producto al segmento prioritario.",
        "Contrasta esta lectura con los informes antes de tomar la siguiente decisión.",
    ])

    html = (
        "<div class='market-summary-section-pro'>"
        "<div class='market-summary-section-title-pro'>5. LECTURA DEL MERCADO</div>"
        "<div class='market-summary-note-pro'>ⓘ Lectura ejecutiva de la oportunidad, el riesgo y la recomendación para la próxima ronda.</div>"
        "<div class='market-summary-insight-grid-pro'>"
        + _market_summary_insight_card("Oportunidad", opportunity_items, "good")
        + _market_summary_insight_card("Riesgo", risk_items, "warn")
        + _market_summary_insight_card("Recomendación", recommendation_items, "blue")
        + "</div></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_team_market(team, state):
    inject_dashboard_styles()
    inject_market_phase1_styles()

    last_research = state.get("last_research")
    last_truth = state.get("last_truth")
    round_n = state.get("round_n", "-")
    status = state.get("round_status", "-")

    last_history = (state.get("history") or [])[-1] if state.get("history") else {}
    round_display = last_history.get("round", round_n)

    last_research_for_total = last_research or {}
    total_market = _market_total_size(last_research_for_total) if "_market_total_size" in globals() else 0.0

    st.markdown(
        f"""
        <div class="market-page-hero">
            <div class="market-page-hero-icon">📊</div>
            <div>
                <div class="market-page-hero-title">Mercado</div>
                <div class="market-page-hero-subtitle">Resumen visual de segmentos, ventas por segmento e información pública de la competencia.</div>
            </div>
            <div class="market-page-hero-meta">
                <div><span>Ronda:</span>{_html_escape(round_display)}</div>
                <div><span>Estado:</span>{_html_escape(status)}</div>
                <div><span>Mercado:</span>{_fmt_int_plain(total_market) if total_market else '—'}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not last_research and not last_truth:
        st.info("Aún no hay una ronda cerrada. El análisis de mercado aparecerá cuando exista información de mercado.")
        st.markdown('<div class="market-kpi-grid">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            _render_market_page_kpi("Estado", "Sin datos", "Cierra la primera ronda", "⏳", "#F59E0B")
        with c2:
            _render_market_page_kpi("Equipo", _html_escape(team), "Marca seleccionada", "👥", "#0F6BFF")
        with c3:
            _render_market_page_kpi("Mercado", "Pendiente", "Aún no hay histórico", "📈", "#7C3AED")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    seg = _market_segment_insights(last_research, team) if last_research else {}
    public = _market_public_insights(last_truth) if last_truth else {}

    st.markdown('<div class="market-section-title">Indicadores clave del mercado</div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    with k1:
        biggest = segment_name_es(seg.get("biggest_segment")) if seg.get("biggest_segment") else "-"
        biggest_note = f"{seg.get('biggest_pct', 0.0) * 100:.1f}% del mercado" if seg.get("biggest_segment") else "Sin datos segmentados"
        _render_market_page_kpi("Segmento más grande", biggest, biggest_note, "👥", "#16A34A")
    with k2:
        total_market = seg.get("total_market", 0.0)
        _render_market_page_kpi("Tamaño total del mercado", _fmt_int_plain(total_market) if total_market else "-", "Unidades potenciales", "📊", "#0F6BFF")
    with k3:
        best_segment = segment_name_es(seg.get("best_segment")) if seg.get("best_segment") else "-"
        best_note = f"Afinidad estimada: {seg.get('best_value', 0.0) * 100:.1f}%" if seg.get("best_segment") else "Sin datos de afinidad"
        _render_market_page_kpi("Mejor encaje de tu marca", best_segment, best_note, "🎯", "#F59E0B")

    if last_research:
        chart_col, reading_col = st.columns([1.65, 1])
        with chart_col:
            with st.container(border=True):
                st.markdown(
                    '<div class="market-chart-title-pro">📊 Tamaño de los segmentos</div>'
                    '<div class="market-chart-subtitle-pro">Distribución del mercado potencial por segmento.</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    build_market_segment_chart_phase1(last_research),
                    use_container_width=True,
                    config={"displayModeBar": False, "responsive": True},
                )
        with reading_col:
            segment_lines = []
            if seg.get("biggest_segment"):
                segment_lines.append(
                    f"{segment_name_es(seg['biggest_segment'])} es el segmento más grande, con aproximadamente {seg['biggest_pct'] * 100:.1f}% del mercado."
                )
            sizes = last_research.get("segment_sizes", {})
            if sizes:
                ordered = sorted(sizes.items(), key=lambda x: float(x[1]), reverse=True)
                total = max(sum(float(v) for _, v in ordered), 1.0)
                if len(ordered) >= 2:
                    segment_lines.append(
                        f"{segment_name_es(ordered[1][0])} es el segundo segmento en tamaño, con {float(ordered[1][1]) / total * 100:.1f}% del mercado."
                    )
                if len(ordered) >= 3:
                    segment_lines.append(
                        f"{segment_name_es(ordered[2][0])} completa la estructura con {float(ordered[2][1]) / total * 100:.1f}% del mercado."
                    )
            _render_market_quick_reading(segment_lines, seg)

        _render_market_sales_phase2(last_research, team, seg)

    if last_truth:
        st.markdown('<div class="market-section-title" style="margin-top:20px;">Información pública del mercado</div>', unsafe_allow_html=True)
        _render_market_public_phase3(last_truth, public)

    # =========================================================
    # FASE 5 AJUSTADA: LECTURA DEL MERCADO EN FORMATO RESUMEN
    # =========================================================
    # Mismo contenido estratégico, pero con el layout visual del bloque
    # "Análisis de desempeño" del Resumen: tres columnas con cabecera sólida.
    _render_market_reading_summary_section(last_research, last_truth, team, seg, public)

    if last_research and last_research.get("notes"):
        st.caption(last_research.get("notes"))

def render_team_competitors(team, state):
    st.markdown("## Competidores")

    last_truth = state.get("last_truth")
    if not last_truth:
        st.info("Aún no hay datos públicos de competidores. Aparecerán tras cerrar la primera ronda.")
        return

    t1, t2, t3 = st.columns(3)
    with t1:
        st.plotly_chart(build_public_competitor_share_chart(last_truth), use_container_width=True)
    with t2:
        st.plotly_chart(build_public_competitor_sales_chart(last_truth), use_container_width=True)
    with t3:
        st.plotly_chart(build_public_competitor_price_chart(last_truth), use_container_width=True)

    df = pd.DataFrame(last_truth).copy()
    df = df.sort_values("share", ascending=False)
    df["share_pct"] = (df["share"] * 100).round(1)
    df["is_you"] = df["team"].apply(lambda x: "← Tu equipo" if x == team else "")

    public_df = df[["team", "units", "share_pct", "price", "is_you"]].rename(columns={
        "team": "Equipo",
        "units": "Ventas",
        "share_pct": "Cuota (%)",
        "price": "Precio medio",
        "is_you": ""
    })
    st.markdown("### Información pública del mercado")
    st.dataframe(public_df, use_container_width=True, hide_index=True)

    st.markdown("### Ranking actual")
    leader = df.iloc[0]["team"]
    st.success(f"Líder de la ronda cerrada: **{leader}**.")
    your_row = df[df["team"] == team]
    if not your_row.empty:
        your_rank = int(your_row.index[0]) + 1
        st.info(f"Tu equipo está actualmente en la posición **{your_rank}** del ranking por cuota.")

    st.markdown("### Evolución respecto a la ronda anterior")
    history = state.get("history", [])
    if len(history) >= 2:
        prev_truth = history[-2]["truth"]
        prev_by_team = {r["team"]: r for r in prev_truth}
        rows = []
        for row in last_truth:
            prev = prev_by_team.get(row["team"])
            prev_share = prev["share"] if prev else 0.0
            prev_units = prev["units"] if prev else 0.0
            diff = (row["share"] - prev_share) * 100
            diff_units = row["units"] - prev_units
            rows.append({
                "Equipo": row["team"],
                "Cambio cuota (pts)": round(diff, 1),
                "Cambio ventas": round(diff_units),
                "Precio actual": round(float(row["price"]), 2),
            })
        evo_df = pd.DataFrame(rows).sort_values("Cambio cuota (pts)", ascending=False)
        st.dataframe(evo_df, use_container_width=True, hide_index=True)
    else:
        st.info("La comparación entre rondas aparecerá cuando haya al menos dos rondas cerradas.")


def render_team_history(state):
    st.markdown("## Historial")

    history = state.get("history", [])
    if not history:
        st.info("Aún no hay histórico disponible.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            build_history_line_chart(history, "share", "Evolución de cuota", "Cuota (%)", mult=100.0),
            use_container_width=True
        )
    with c2:
        st.plotly_chart(
            build_history_line_chart(history, "profit", "Evolución de beneficio", "Beneficio", mult=1.0),
            use_container_width=True
        )

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(
            build_history_line_chart(history, "awareness_true", "Evolución de conocimiento", "Conocimiento (%)", mult=100.0),
            use_container_width=True
        )
    with c4:
        st.plotly_chart(
            build_history_line_chart(history, "retention_rate", "Evolución de retención", "Retención (%)", mult=100.0),
            use_container_width=True
        )

    st.markdown("### Resumen histórico por ronda")
    rows = []
    for round_data in history:
        rnum = round_data["round"]
        for row in round_data["truth"]:
            rows.append({
                "Ronda": rnum,
                "Equipo": row["team"],
                "Ventas": round(row["units"]),
                "Cuota (%)": round(row["share"] * 100, 1),
                "Beneficio": round(row["profit"], 0),
                "Conocimiento (%)": round(row["awareness_true"] * 100, 1),
                "Retención (%)": round(row["retention_rate"] * 100, 1),
            })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)



# =========================================================
# INFORMES VISUALES PRO - MERCADO
# =========================================================
def inject_reports_pro_styles():
    """Estilos visuales para los informes tipo dashboard."""
    st.markdown(
        """
        <style>
        .report-shell { width:100%; }
        .report-hero {
            background: linear-gradient(135deg, #06345F 0%, #082B55 100%);
            color: white; border-radius: 16px; padding: 18px 22px; margin: 4px 0 18px 0;
            display:grid; grid-template-columns: 74px 1fr 290px; gap:18px; align-items:center;
            box-shadow: 0 10px 26px rgba(8, 43, 85, .18);
        }
        .report-hero-icon { width:58px; height:58px; border:2px solid rgba(150,210,255,.60); border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:2rem; background:rgba(255,255,255,.06); }
        .report-hero-title { font-size:2.05rem; font-weight:950; letter-spacing:-.04em; line-height:1.05; margin:0; }
        .report-hero-subtitle { margin-top:5px; font-size:1rem; font-weight:700; opacity:.86; }
        .report-hero-meta { border-left:1px solid rgba(255,255,255,.30); padding-left:22px; font-weight:800; font-size:.92rem; line-height:1.9; }
        .report-hero-meta span { display:inline-block; min-width:106px; opacity:.82; }
        .report-card { background:#fff; border:1px solid #E3EAF2; border-radius:16px; padding:16px 17px; box-shadow:0 8px 24px rgba(9,30,66,.055); margin-bottom:14px; }
        .report-section-title { color:#0B4B93; font-weight:950; font-size:1.05rem; text-transform:uppercase; margin:0 0 12px 0; letter-spacing:-.015em; }
        .report-muted { color:#516175; font-size:.88rem; line-height:1.45; }
        .market-summary-grid { display:grid; grid-template-columns: 1.55fr repeat(5, minmax(122px, 1fr)); gap:10px; align-items:stretch; }
        .market-summary-text { background:#F5F9FD; border:1px solid #E6EEF7; border-radius:14px; padding:15px; min-height:150px; }
        .market-kpi { background:#fff; border:1px solid #DCE6F2; border-radius:13px; padding:13px 10px; text-align:center; min-height:150px; box-shadow:0 4px 14px rgba(9,30,66,.05); }
        .market-kpi-icon { font-size:1.8rem; color:#557398; margin:4px 0 6px 0; }
        .market-kpi-title { color:#1D2738; font-size:.73rem; font-weight:950; text-transform:uppercase; line-height:1.2; min-height:31px; }
        .market-kpi-value { color:#071E49; font-size:1.38rem; font-weight:950; line-height:1.1; margin-top:8px; }
        .market-kpi-note { color:#53657D; font-size:.74rem; font-weight:750; margin-top:3px; }
        .market-kpi-good { color:#168A4A; } .market-kpi-warn { color:#F59E0B; } .market-kpi-bad { color:#D94C3D; }
        .market-two-grid { display:grid; grid-template-columns: .90fr 1.35fr; gap:14px; }
        .market-working-grid { display:grid; grid-template-columns: .9fr 1.35fr; gap:14px; }
        .market-table { width:100%; border-collapse:collapse; font-size:.84rem; }
        .market-table th { color:#1D2738; text-align:left; font-weight:950; padding:8px 6px; border-bottom:1px solid #DDE6F1; }
        .market-table td { padding:8px 6px; border-bottom:1px solid #EEF2F7; color:#1D2738; font-weight:700; }
        .market-table tr.total td { font-weight:950; background:#F7FAFD; }
        .seg-dot { width:11px; height:11px; border-radius:50%; display:inline-block; margin-right:7px; vertical-align:middle; }
        .market-note { background:#EEF6FF; border-radius:12px; padding:10px 12px; color:#173B66; font-size:.84rem; font-weight:750; margin-top:9px; line-height:1.35; }
        .working-item { display:grid; grid-template-columns:54px 1fr; gap:12px; border:1px solid #E3EAF2; border-radius:12px; padding:11px; margin-bottom:8px; background:#fff; }
        .working-icon { width:44px; height:44px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1.4rem; }
        .working-title { font-weight:950; color:#0B4B93; margin-bottom:3px; font-size:.88rem; }
        .working-body { color:#344054; font-size:.80rem; line-height:1.35; }
        .opp-grid { display:grid; grid-template-columns:1fr 170px; gap:13px; }
        .opp-side { background:#EEF6FF; border-radius:12px; padding:12px; color:#173B66; font-size:.80rem; line-height:1.35; }
        .opp-pill { padding:6px 12px; border-radius:10px; font-weight:950; font-size:.78rem; text-align:center; display:inline-block; min-width:80px; }
        .opp-high { background:#E8F5E9; color:#138244; } .opp-mid { background:#FFF4D6; color:#B56A00; } .opp-low { background:#FDECEA; color:#C62828; }
        .bar-mini { width:84px; height:8px; background:#D8DEE8; border-radius:99px; display:inline-block; overflow:hidden; vertical-align:middle; margin-right:6px; }
        .bar-mini-fill { height:100%; background:#0B4B93; border-radius:99px; display:block; }
        .conclusion-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:14px; }
        .conclusion-box { border-radius:15px; border:1px solid #E3EAF2; overflow:hidden; background:white; min-height:205px; }
        .conclusion-head { color:white; font-weight:950; text-align:center; padding:10px 12px; font-size:.82rem; text-transform:uppercase; }
        .conclusion-body { padding:13px 15px; font-size:.84rem; color:#344054; line-height:1.45; }
        .conclusion-body ul { padding-left:0; margin:0; list-style:none; }
        .conclusion-body li { margin-bottom:9px; }
        .conclusion-footer { margin:8px 12px 12px 12px; padding:10px; border-radius:11px; font-weight:850; font-size:.82rem; text-align:center; }
        .footer-good { background:#E8F5E9; color:#168A4A; } .footer-bad { background:#FFF4D6; color:#9A5A00; } .footer-opp { background:#E6F1FF; color:#0B4B93; }
        .market-reminder { background:#06345F; color:white; border-radius:13px; padding:12px 18px; font-weight:800; margin: 4px 0 14px 0; }
        .report-selector-card { border:1px solid #DCE6F2; background:#fff; border-radius:13px; padding:12px 14px; }

        .buyer-var { display:inline-flex; align-items:center; justify-content:center; min-width:70px; padding:5px 9px; border-radius:999px; font-size:.78rem; font-weight:950; }
        .buyer-var.up { background:#EAF8EF; color:#168A4A; }
        .buyer-var.down { background:#FEECEC; color:#B42318; }
        .buyer-var.neutral { background:#EEF2F7; color:#64748B; }
        @media (max-width: 1150px) {
            .report-hero { grid-template-columns: 1fr; }
            .report-hero-meta { border-left:0; padding-left:0; }
            .market-summary-grid, .market-two-grid, .market-working-grid, .opp-grid, .conclusion-grid { grid-template-columns:1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _market_total_size(last_research):
    sizes = (last_research or {}).get("segment_sizes", {})
    return sum(float(v) for v in sizes.values()) if sizes else 0.0


def _segment_activation_rate(last_research, segment_name, idx=0):
    """Porcentaje del segmento que compra en la ronda. Usa datos nuevos del engine si existen; si no, fallback compatible."""
    lr = last_research or {}
    for key in ("segment_activation_rate", "segment_activation_rates"):
        vals = lr.get(key, {}) or {}
        if segment_name in vals:
            return max(0.0, min(1.0, float(vals.get(segment_name, 0.0))))
        seg_es = segment_name_es(segment_name)
        if seg_es in vals:
            return max(0.0, min(1.0, float(vals.get(seg_es, 0.0))))
    active = (lr.get("segment_active_buyers", {}) or {}).get(segment_name)
    size = (lr.get("segment_sizes", {}) or {}).get(segment_name)
    if active is not None and size:
        return max(0.0, min(1.0, float(active) / max(float(size), 1.0)))
    # Compatibilidad con rondas antiguas: valores base históricos del simulador.
    return max(0.0, min(1.0, 0.41 + 0.05 * int(idx)))


def _segment_active_buyers(last_research, segment_name, idx=0):
    lr = last_research or {}
    vals = lr.get("segment_active_buyers", {}) or {}
    if segment_name in vals:
        return float(vals.get(segment_name, 0.0))
    seg_es = segment_name_es(segment_name)
    if seg_es in vals:
        return float(vals.get(seg_es, 0.0))
    size = float((lr.get("segment_sizes", {}) or {}).get(segment_name, 0.0))
    return size * _segment_activation_rate(lr, segment_name, idx)


def _segment_buyers_variation_pct(last_research, previous_research, segment_name, idx=0):
    if not previous_research:
        return None
    current = _segment_active_buyers(last_research, segment_name, idx)
    previous = _segment_active_buyers(previous_research, segment_name, idx)
    if previous <= 0:
        return None
    return ((current - previous) / previous) * 100.0


def _format_buyer_variation_html(v):
    """Devuelve HTML seguro para mostrar la variación porcentual de compradores vs ronda anterior."""
    if v is None:
        return "<span style='color:#667085; font-weight:800;'>—</span>"
    try:
        value = float(v)
    except Exception:
        return "<span style='color:#667085; font-weight:800;'>—</span>"

    if value > 0.05:
        return f"<span style='display:inline-flex;align-items:center;gap:5px;color:#168A4A;font-weight:950;'>▲ +{value:.1f}%</span>"
    if value < -0.05:
        return f"<span style='display:inline-flex;align-items:center;gap:5px;color:#B42318;font-weight:950;'>▼ {value:.1f}%</span>"
    return "<span style='color:#667085; font-weight:900;'>0.0%</span>"


def _market_active_total(last_research):
    lr = last_research or {}
    vals = lr.get("segment_active_buyers", {}) or {}
    if vals:
        return sum(float(v) for v in vals.values())
    sizes = lr.get("segment_sizes", {}) or {}
    return sum(_segment_active_buyers(lr, seg, i) for i, seg in enumerate(sizes.keys()))


def _market_non_buyers_total(last_research):
    total = _market_total_size(last_research)
    return max(0.0, total - _market_active_total(last_research))


def _previous_research_from_state(state):
    history = (state or {}).get("history", []) or []
    if len(history) < 2:
        return None
    prev_round = history[-2] or {}
    return prev_round.get("research") or prev_round.get("last_research") or prev_round.get("market_research")


def _segment_color(idx):
    palette = ["#2E974B", "#0B63B6", "#8755D9", "#F59E0B", "#9AA4B2"]
    return palette[idx % len(palette)]


def _market_event_label(event_info):
    if not event_info:
        return "Sin evento", "Sin evento relevante en esta ronda.", "Medio"
    title = event_info.get("title", "Evento")
    desc = event_info.get("desc", "")
    extra = event_info.get("extra", "")
    impact = "Alto" if any(w in (title + desc + extra).lower() for w in ["sensibilidad", "caída", "saturación", "crecimiento"]) else "Medio"
    return title, f"{title}: {desc} {extra}".strip(), impact


def _market_opportunity_rows(last_research, team):
    sizes = (last_research or {}).get("segment_sizes", {})
    mix = (last_research or {}).get("segment_brand_mix", {})
    total = max(sum(float(v) for v in sizes.values()), 1.0)
    rows = []
    for seg, size in sizes.items():
        vals = mix.get(seg, {})
        if vals:
            leader, leader_val = max(vals.items(), key=lambda x: float(x[1]))
        else:
            leader, leader_val = "-", 0.0
        pct = float(size) / total
        if leader_val < 0.38:
            comp, opp, cls = "Baja", "ALTA", "opp-high"
        elif leader_val < 0.50:
            comp, opp, cls = "Media", "MEDIA", "opp-mid"
        else:
            comp, opp, cls = "Alta", "BAJA", "opp-low"
        rows.append({
            "seg": seg,
            "size": float(size),
            "pct": pct,
            "leader": leader,
            "leader_val": float(leader_val),
            "comp": comp,
            "opp": opp,
            "cls": cls,
            "my_val": float(vals.get(team, 0.0)) if vals else 0.0,
        })
    return rows


def _market_best_worst_segments(last_research, team):
    rows = _market_opportunity_rows(last_research, team)
    if not rows:
        return None, None, None
    best = max(rows, key=lambda r: r["my_val"])
    worst = min(rows, key=lambda r: r["my_val"])
    best_opp = max(rows, key=lambda r: (1 if r["opp"] == "ALTA" else 0, r["pct"]))
    return best, worst, best_opp


def _market_summary_text(last_research, event_info):
    total = _market_total_size(last_research)
    sizes = (last_research or {}).get("segment_sizes", {})
    event_title, event_desc, event_impact = _market_event_label(event_info)
    if sizes:
        biggest_seg, biggest_size = max(sizes.items(), key=lambda x: float(x[1]))
        biggest_pct = float(biggest_size) / max(total, 1.0) * 100
        base = f"El mercado alcanza {_fmt_int_plain(total)} unidades potenciales. De ellas, aproximadamente el {_market_active_total(last_research) / max(total, 1.0) * 100:.1f}% han comprado esta ronda y el {_market_non_buyers_total(last_research) / max(total, 1.0) * 100:.1f}% no han comprado. El mayor volumen se concentra en {segment_name_es(biggest_seg)} ({biggest_pct:.1f}%)."
    else:
        base = "El mercado aún no tiene información segmentada suficiente."
    if event_info:
        return f"{base} {event_desc} El análisis combina tamaño, liderazgo y espacio competitivo para detectar oportunidades reales."
    return f"{base} No hubo evento relevante en esta ronda. El análisis combina tamaño, liderazgo y espacio competitivo para detectar oportunidades reales."


def _build_market_donut(last_research):
    sizes = (last_research or {}).get("segment_sizes", {})
    fig = go.Figure()
    if sizes:
        labels = [segment_name_es(k) for k in sizes.keys()]
        values = [float(v) for v in sizes.values()]
        colors_ = [_segment_color(i) for i in range(len(labels))]
        fig.add_trace(go.Pie(labels=labels, values=values, hole=.48, marker=dict(colors=colors_), textinfo="percent", sort=False))
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=5, b=5), showlegend=True, legend=dict(orientation="v", x=.72, y=.5, font=dict(size=12)))
    return fig


def _build_segment_purchase_bar(last_research, segment_name, team):
    vals = ((last_research or {}).get("segment_brand_mix", {}) or {}).get(segment_name, {})
    fig = go.Figure()
    if vals:
        items = sorted(vals.items(), key=lambda x: float(x[1]), reverse=True)[:6]
        labels = [x[0] for x in items][::-1]
        values = [float(x[1]) * 100 for x in items][::-1]
        marker_colors = ["#0B4B93" if label == team else ("#2E974B" if i == len(labels)-1 else "#BFC5CD") for i, label in enumerate(labels)]
        fig.add_trace(go.Bar(x=values, y=labels, orientation="h", marker_color=marker_colors, text=[f"{v:.1f}%" for v in values], textposition="outside", cliponaxis=False))
    sizes = (last_research or {}).get("segment_sizes", {})
    total = max(sum(float(v) for v in sizes.values()), 1.0)
    pct = float(sizes.get(segment_name, 0.0)) / total * 100 if sizes else 0
    fig.update_layout(
        height=245,
        margin=dict(l=8, r=25, t=18, b=18),
        xaxis=dict(range=[0, max(60, max([float(v)*100 for v in vals.values()], default=0)+10)], ticksuffix="%", showgrid=True, gridcolor="#EEF2F7"),
        yaxis=dict(tickfont=dict(size=11)),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


def _render_market_header(round_label, team, last_research):
    total = _market_total_size(last_research)
    st.markdown(
        f"""
        <div class="report-hero">
            <div class="report-hero-icon">📈</div>
            <div>
                <div class="report-hero-title">INFORME DE MERCADO</div>
                <div class="report-hero-subtitle">Situación y oportunidades del mercado</div>
            </div>
            <div class="report-hero-meta">
                <div><span>⚙️ Ronda:</span>{_html_escape(round_label)}</div>
                <div><span>📅 Fecha:</span>—</div>
                <div><span>🌐 Mercado total:</span>{_fmt_int_plain(total)} unidades</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_market_kpi(title, icon, value, note="", tone=""):
    tone_cls = {"good":"market-kpi-good", "warn":"market-kpi-warn", "bad":"market-kpi-bad"}.get(tone, "")
    st.markdown(
        f"""
        <div class="market-kpi">
            <div class="market-kpi-title">{_html_escape(title)}</div>
            <div class="market-kpi-icon">{icon}</div>
            <div class="market-kpi-value {tone_cls}">{_html_escape(value)}</div>
            <div class="market-kpi-note">{_html_escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def _segment_research_driver(seg):
    name = segment_name_es(seg)
    if name == "Ahorradores":
        return {
            "icon": "💸",
            "tone": "green",
            "profile": "Este grupo decide principalmente por precio final, ahorro percibido y promociones fáciles de entender.",
            "barrier": "Cuando no detectan una ventaja económica clara, tienden a retrasar la compra o a comparar más alternativas.",
            "driver_up": "El aumento de compradores sugiere que la propuesta de valor y la visibilidad promocional están reduciendo la barrera de entrada.",
            "driver_down": "La caída de compradores apunta a una menor percepción de ahorro o a una comunicación de valor insuficientemente clara.",
            "driver_flat": "El comportamiento se mantiene estable: el segmento parece seguir esperando una ventaja económica más evidente para moverse con fuerza.",
        }
    if name == "Equilibrados":
        return {
            "icon": "⚖️",
            "tone": "blue",
            "profile": "Este grupo busca una combinación razonable de precio, calidad, disponibilidad y confianza.",
            "barrier": "Si la propuesta parece descompensada o poco clara, el consumidor duda y reduce su intención de compra.",
            "driver_up": "El crecimiento de compradores sugiere que el mercado está transmitiendo una propuesta más equilibrada y fácil de justificar.",
            "driver_down": "La caída de compradores puede indicar falta de claridad en la propuesta o dudas sobre la relación calidad-precio.",
            "driver_flat": "El segmento se mantiene estable: no aparecen señales fuertes de mejora ni de deterioro en la percepción de valor.",
        }
    return {
        "icon": "💎",
        "tone": "purple",
        "profile": "Este grupo valora especialmente calidad percibida, reputación, fiabilidad y coherencia de marca.",
        "barrier": "Las estrategias basadas solo en precio o promoción tienen menos impacto si no vienen acompañadas de confianza y diferenciación.",
        "driver_up": "El aumento de compradores sugiere una mejor percepción de calidad, reputación o diferenciación dentro del segmento.",
        "driver_down": "La caída de compradores apunta a menor confianza percibida, falta de diferenciación o una propuesta premium poco convincente.",
        "driver_flat": "El comportamiento se mantiene estable: el segmento no percibe aún un cambio suficiente en calidad, marca o propuesta diferencial.",
    }


def _consumer_research_block_html(last_research, previous_research, team):
    sizes = ((last_research or {}).get("segment_sizes", {}) or {})
    if not sizes:
        return "<div class='market-note'>No hay datos suficientes para generar insights del consumidor por segmento.</div>"

    css = """
<style>
.consumer-insight-intro{background:#F4F8FE;border:1px solid #DDE7F3;border-radius:13px;padding:11px 13px;color:#173B66;font-size:.82rem;font-weight:750;line-height:1.35;margin:8px 0 12px 0;}
.consumer-insight-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;}\n@media(max-width:1200px){.consumer-insight-grid{grid-template-columns:1fr;}}
.consumer-insight-card{border:1px solid #E3EAF2;border-left:5px solid var(--tone);border-radius:15px;padding:13px 14px;background:#fff;box-shadow:0 6px 18px rgba(9,30,66,.045);}
.consumer-insight-head{display:grid;grid-template-columns:36px 1fr auto;gap:10px;align-items:center;margin-bottom:10px;}
.consumer-insight-icon{width:34px;height:34px;border-radius:50%;background:var(--soft);color:var(--tone);display:flex;align-items:center;justify-content:center;font-size:1.05rem;font-weight:950;}
.consumer-insight-title{color:#071E49;font-size:.91rem;font-weight:950;line-height:1.05;text-transform:uppercase;}
.consumer-insight-subtitle{color:#64748B;font-size:.70rem;font-weight:800;margin-top:2px;}
.consumer-insight-delta{border-radius:999px;padding:6px 9px;font-size:.75rem;font-weight:950;white-space:nowrap;}
.consumer-insight-metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;}
.consumer-insight-metrics div{background:#F8FAFC;border:1px solid #EEF2F7;border-radius:11px;padding:8px 7px;text-align:center;}
.consumer-insight-metrics b{display:block;color:#071E49;font-size:1.05rem;font-weight:950;line-height:1;}
.consumer-insight-metrics span{display:block;color:#64748B;font-size:.70rem;font-weight:850;margin-top:4px;}
.consumer-insight-body p{margin:0 0 8px 0;color:#344054;font-size:.79rem;line-height:1.36;font-weight:650;}
.consumer-insight-body p:last-child{margin-bottom:0;}
.consumer-insight-body b{color:#0B4B93;font-weight:950;}
</style>
"""
    intro = "<div class='consumer-insight-intro'>🧪 Lectura tipo investigación comercial: explica qué puede estar afectando a la decisión de compra de cada segmento. Es una interpretación basada en los datos del simulador, no una afirmación absoluta.</div>"
    cards = []
    for idx, seg in enumerate(list(sizes.keys())[:3]):
        driver = _segment_research_driver(seg)
        activation = _segment_activation_rate(last_research, seg, idx)
        non_rate = max(0.0, 1.0 - activation)
        variation = _segment_buyers_variation_pct(last_research, previous_research, seg, idx)
        vals = ((last_research or {}).get("segment_brand_mix", {}) or {}).get(seg, {}) or {}
        if vals:
            leader, leader_val = max(vals.items(), key=lambda x: float(x[1]))
            leader_text = f"La marca que mejor está convirtiendo en este segmento es {leader}, con una cuota aproximada del {float(leader_val) * 100:.1f}% entre quienes compran."
        else:
            leader_text = "Aún no hay una marca claramente identificada como referencia dentro de este segmento."

        if variation is None:
            move_value = "—"
            movement = "Sin histórico comparable todavía. La lectura se basa en la ronda actual y debe contrastarse en la siguiente ronda."
            move_cls = "neutral"
        else:
            move_value = (f"+{variation:.1f}%" if variation > 0 else f"{variation:.1f}%").replace(".", ",")
            if variation > 2:
                movement = driver["driver_up"]
                move_cls = "up"
            elif variation < -2:
                movement = driver["driver_down"]
                move_cls = "down"
            else:
                movement = driver["driver_flat"]
                move_cls = "neutral"

        tone_color = {"green": "#168A4A", "blue": "#0B63B6", "purple": "#8755D9"}.get(driver["tone"], "#0B63B6")
        soft_bg = {"green": "#E8F5E9", "blue": "#EAF4FF", "purple": "#F5F0FF"}.get(driver["tone"], "#EAF4FF")
        movement_color = {"up": "#168A4A", "down": "#B42318", "neutral": "#64748B"}.get(move_cls, "#64748B")
        movement_bg = {"up": "#E8F5E9", "down": "#FEECEC", "neutral": "#F1F5F9"}.get(move_cls, "#F1F5F9")
        cards.append(
            "<div class='consumer-insight-card' style='--tone:" + tone_color + "; --soft:" + soft_bg + ";'>"
            "<div class='consumer-insight-head'>"
            "<div class='consumer-insight-icon'>" + _html_escape(driver["icon"]) + "</div>"
            "<div><div class='consumer-insight-title'>" + _html_escape(segment_name_es(seg)) + "</div>"
            "<div class='consumer-insight-subtitle'>Investigación comercial del segmento</div></div>"
            "<div class='consumer-insight-delta' style='background:" + movement_bg + "; color:" + movement_color + ";'>" + _html_escape(move_value) + "</div>"
            "</div>"
            "<div class='consumer-insight-metrics'>"
            "<div><b>" + f"{activation*100:.1f}%" + "</b><span>compran</span></div>"
            "<div><b>" + f"{non_rate*100:.1f}%" + "</b><span>no compran</span></div>"
            "</div>"
            "<div class='consumer-insight-body'>"
            "<p><b>Qué valora:</b> " + _html_escape(driver["profile"]) + "</p>"
            "<p><b>Barrera detectada:</b> " + _html_escape(driver["barrier"]) + "</p>"
            "<p><b>Lectura de la ronda:</b> " + _html_escape(movement) + "</p>"
            "<p><b>Conversión de marcas:</b> " + _html_escape(leader_text) + "</p>"
            "</div></div>"
        )
    return css + intro + "<div class='consumer-insight-grid'>" + "".join(cards) + "</div>"




# =========================================================
# HELPERS INFORME DE MERCADO - TARJETAS DE ACTIVACIÓN
# =========================================================
def _market_get_segment_activation_rate(research, seg):
    """Obtiene el porcentaje de activación/compradores de un segmento."""
    if not research:
        return 0.0

    activation = research.get("segment_activation_rate", {}) or {}
    if isinstance(activation, dict) and activation:
        return float(activation.get(seg, activation.get(segment_name_es(seg), 0.0)) or 0.0)

    size = float((research.get("segment_sizes", {}) or {}).get(seg, 0.0) or 0.0)
    buyers = _market_get_segment_active_buyers(research, seg)
    if size <= 0:
        return 0.0
    return buyers / size


def _render_segment_activation_card(last_research, seg, i=0):
    """Tarjeta compacta de activación/no compra para el apartado 3 del informe."""
    palette = [
        ("#168A4A", "#EAF8EF", "🟢"),
        ("#0B63B6", "#EAF4FF", "🔵"),
        ("#8755D9", "#F3ECFF", "🟣"),
    ]
    color, soft, icon = palette[int(i) % len(palette)]

    seg_label = segment_name_es(seg)
    size = float((last_research.get("segment_sizes", {}) or {}).get(seg, 0.0) or 0.0)
    activation_rate = _market_get_segment_activation_rate(last_research, seg)
    activation_rate = max(0.0, min(1.0, activation_rate))
    non_buy_rate = 1.0 - activation_rate

    buyers = _market_get_segment_active_buyers(last_research, seg)
    if buyers <= 0 and size > 0:
        buyers = size * activation_rate
    non_buyers = max(0.0, size - buyers)

    buy_pct = activation_rate * 100.0
    no_pct = non_buy_rate * 100.0

    st.markdown(
        f"""
        <div class="segment-activation-mini" style="--tone:{color}; --soft:{soft};">
            <div class="segment-activation-mini-head">
                <span class="segment-activation-mini-icon">{icon}</span>
                <div>
                    <div class="segment-activation-mini-title">{_html_escape(seg_label)}</div>
                    <div class="segment-activation-mini-subtitle">Activación del segmento</div>
                </div>
            </div>
            <div class="segment-activation-bar">
                <span class="segment-activation-buy" style="width:{buy_pct:.1f}%;"></span>
                <span class="segment-activation-nobuy" style="width:{no_pct:.1f}%;"></span>
            </div>
            <div class="segment-activation-legend">
                <span><b>{buy_pct:.1f}%</b> compran</span>
                <span><b>{no_pct:.1f}%</b> no compran</span>
            </div>
            <div class="segment-activation-foot">
                Activos: <b>{_fmt_int_plain(buyers)}</b> · No activados: <b>{_fmt_int_plain(non_buyers)}</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_market_report_dashboard(team, state):
    inject_reports_pro_styles()
    st.markdown(
        """
        <style>
        .market-dashboard-title {
            color:#0B4B93;
            font-weight:950;
            font-size:1.10rem;
            text-transform:uppercase;
            margin:2px 0 10px 0;
            letter-spacing:-.02em;
        }
        .market-dashboard-subtitle {
            color:#516175;
            font-size:.86rem;
            line-height:1.38;
            font-weight:650;
            margin:-4px 0 12px 0;
        }
        .market-panel-note {
            background:#EEF6FF;
            border:1px solid #D7E9FF;
            border-radius:12px;
            padding:10px 12px;
            color:#173B66;
            font-size:.82rem;
            font-weight:750;
            line-height:1.35;
            margin-top:10px;
        }
        .segment-activation-mini {
            background:#fff;
            border:1px solid #E3EAF2;
            border-left:5px solid var(--tone);
            border-radius:14px;
            padding:11px 12px;
            box-shadow:0 6px 18px rgba(9,30,66,.045);
            margin-bottom:8px;
        }
        .segment-activation-mini-head {
            display:flex;
            gap:9px;
            align-items:center;
            margin-bottom:9px;
        }
        .segment-activation-mini-icon {
            width:32px;
            height:32px;
            border-radius:50%;
            background:var(--soft);
            color:var(--tone);
            display:inline-flex;
            align-items:center;
            justify-content:center;
            font-size:1rem;
            flex:0 0 32px;
        }
        .segment-activation-mini-title {
            color:#071E49;
            font-size:.82rem;
            line-height:1.05;
            font-weight:950;
            text-transform:uppercase;
        }
        .segment-activation-mini-subtitle {
            color:#64748B;
            font-size:.68rem;
            font-weight:800;
            margin-top:2px;
        }
        .segment-activation-bar {
            display:flex;
            width:100%;
            height:12px;
            border-radius:999px;
            overflow:hidden;
            background:#E8EEF6;
            margin-bottom:8px;
        }
        .segment-activation-buy { background:var(--tone); height:100%; }
        .segment-activation-nobuy { background:#D8DEE8; height:100%; }
        .segment-activation-legend {
            display:flex;
            justify-content:space-between;
            gap:8px;
            color:#344054;
            font-size:.72rem;
            font-weight:800;
            line-height:1.2;
        }
        .segment-activation-legend b { color:#071E49; font-weight:950; }
        .segment-activation-foot {
            color:#64748B;
            font-size:.69rem;
            font-weight:750;
            line-height:1.25;
            margin-top:7px;
        }
        .segment-activation-foot b { color:#173B66; }
        .market-right-stack [data-testid="stVerticalBlock"] { gap: 0.75rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    last_research = state.get("last_research") or {}
    event_info = state.get("last_event")
    history = state.get("history", []) or []
    previous_research = _previous_research_from_state(state)
    round_label = history[-1].get("round", state.get("round_n", "-")) if history else state.get("round_n", "-")
    total = _market_total_size(last_research)
    event_title, event_desc, event_impact = _market_event_label(event_info)
    best, worst, best_opp = _market_best_worst_segments(last_research, team)

    _render_market_header(round_label, team, last_research)

    # 1. Resumen
    st.markdown('<div class="market-summary-grid">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="market-summary-text"><div class="report-section-title">1. RESUMEN DEL MERCADO</div>'
        f'<div class="report-muted" style="font-size:.92rem; font-weight:650; color:#1D2738;">{_html_escape(_market_summary_text(last_research, event_info))}</div></div>',
        unsafe_allow_html=True,
    )
    kpi_cols = st.columns(5)
    active_total = _market_active_total(last_research)
    non_total = _market_non_buyers_total(last_research)
    active_pct = active_total / max(total, 1.0) * 100 if total else 0.0
    non_pct = non_total / max(total, 1.0) * 100 if total else 0.0
    with kpi_cols[0]:
        _render_market_kpi("Tamaño total del mercado", "👥", _fmt_int_plain(total), "unidades potenciales", "")
    with kpi_cols[1]:
        _render_market_kpi("Mercado activo", "🛒", _fmt_int_plain(active_total), f"{active_pct:.1f}% compran", "good")
    with kpi_cols[2]:
        _render_market_kpi("No compran", "🚫", _fmt_int_plain(non_total), f"{non_pct:.1f}% no compran", "bad")
    with kpi_cols[3]:
        _render_market_kpi("Sensibilidad a la promoción", "📣", "Media", "lectura de ronda", "warn")
    with kpi_cols[4]:
        _render_market_kpi("Evento de la ronda", "⚠️", event_title[:18], f"Impacto: {event_impact}", "bad" if event_impact == "Alto" else "")
    st.markdown('</div>', unsafe_allow_html=True)

    sizes = last_research.get("segment_sizes", {}) or {}

    # Layout recomendado: izquierda 2; derecha 3 + 5 apilados.
    left, right = st.columns([0.45, 0.55], gap="large")

    with left:
        with st.container(border=True):
            st.markdown('<div class="market-dashboard-title">2. ESTRUCTURA DEL MERCADO POR SEGMENTOS</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="market-dashboard-subtitle">Tamaño potencial de cada segmento y variación de compradores frente a la ronda anterior.</div>',
                unsafe_allow_html=True,
            )
            rows_html = ""
            if sizes:
                for i, (seg, size) in enumerate(sizes.items()):
                    pct = float(size) / max(total, 1.0) * 100
                    buyer_var = _segment_buyers_variation_pct(last_research, previous_research, seg, i)
                    rows_html += (
                        f"<tr>"
                        f"<td><span class='seg-dot' style='background:{_segment_color(i)}'></span>{_html_escape(segment_name_es(seg))}</td>"
                        f"<td>{_fmt_int_plain(size)}</td>"
                        f"<td>{pct:.1f}%</td>"
                        f"<td>{_format_buyer_variation_html(buyer_var)}</td>"
                        f"</tr>"
                    )
                total_buyer_var = _market_buyers_variation_pct(last_research, previous_research)
                rows_html += (
                    f"<tr class='total'><td>TOTAL MERCADO</td><td>{_fmt_int_plain(total)}</td>"
                    f"<td>100%</td><td>{_format_buyer_variation_html(total_buyer_var)}</td></tr>"
                )
            st.markdown(
                f"<table class='market-table'><thead><tr><th>Segmento</th><th>Tamaño</th><th>% mercado</th><th>Δ compradores</th></tr></thead><tbody>{rows_html}</tbody></table>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(_build_market_donut(last_research), use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                '<div class="market-panel-note">📈 La columna <b>Δ compradores</b> indica si el segmento ha generado más o menos compradores que en la ronda anterior.</div>',
                unsafe_allow_html=True,
            )

    with right:
        with st.container(border=True):
            st.markdown('<div class="market-dashboard-title">3. REPARTO DE COMPRA POR SEGMENTO</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="market-dashboard-subtitle">Cuota de cada marca entre los consumidores que sí compran en cada segmento.</div>',
                unsafe_allow_html=True,
            )
            seg_cols = st.columns(3)
            for i, seg in enumerate(list(sizes.keys())[:3]):
                with seg_cols[i]:
                    seg_total = float((last_research.get("segment_sizes", {}) or {}).get(seg, 0.0))
                    seg_pct = seg_total / max(total, 1.0) * 100 if total else 0.0
                    st.markdown(
                        f'<div style="color:#0B4B93;font-weight:950;font-size:.88rem;text-transform:uppercase;margin:0 0 8px 0;line-height:1.15;">{_html_escape(segment_name_es(seg).upper())} ({seg_pct:.1f}%)</div>',
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(
                        _build_segment_purchase_bar(last_research, seg, team),
                        use_container_width=True,
                        config={"displayModeBar": False},
                    )
            if best and best_opp:
                st.markdown(
                    f'<div class="market-panel-note">⭐ <b>{_html_escape(team)}</b> destaca más en <b>{segment_name_es(best["seg"])}</b>. '
                    f'<b>{segment_name_es(best_opp["seg"])}</b> parece el segmento con más oportunidad por tamaño y liderazgo actual.</div>',
                    unsafe_allow_html=True,
                )

        with st.container(border=True):
            st.markdown('<div class="market-dashboard-title">5. MAPA DE OPORTUNIDADES</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="market-dashboard-subtitle">Cruza tamaño del segmento, liderazgo competitivo y espacio disponible para priorizar dónde actuar.</div>',
                unsafe_allow_html=True,
            )
            rows = _market_opportunity_rows(last_research, team)
            body_parts = []
            for i, r in enumerate(rows):
                fill_w = max(4, min(100, r["leader_val"] * 100))
                body_parts.append(
                    f"<tr>"
                    f"<td><span class='seg-dot' style='background:{_segment_color(i)}'></span>{_html_escape(segment_name_es(r['seg']))}</td>"
                    f"<td>{_fmt_int_plain(r['size'])}<br><span class='report-muted'>({r['pct']*100:.1f}%)</span></td>"
                    f"<td><span class='bar-mini'><span class='bar-mini-fill' style='width:{fill_w:.0f}%;'></span></span><b>{r['leader_val']*100:.1f}%</b></td>"
                    f"<td>{_html_escape(r['comp'])}</td>"
                    f"<td><span class='opp-pill {r['cls']}'>{_html_escape(r['opp'])}</span></td>"
                    f"</tr>"
                )
            body = "".join(body_parts)
            st.markdown(
                f"""
                <div class="opp-grid">
                    <div>
                        <table class="market-table">
                            <thead>
                                <tr><th>Segmento</th><th>Tamaño</th><th>Liderazgo</th><th>Compet.</th><th>Oportunidad</th></tr>
                            </thead>
                            <tbody>{body}</tbody>
                        </table>
                    </div>
                    <div class="opp-side">
                        <b>Claves del mapa:</b><br><br>
                        • Segmentos grandes y con liderazgo bajo = mayor oportunidad.<br><br>
                        • Liderazgo alto indica entrada más difícil.<br><br>
                        • Prioriza encaje, no solo tamaño.
                    </div>
                </div>
                <div class="market-panel-note">Nivel de oportunidad: 🟢 Alta &nbsp;&nbsp; 🟡 Media &nbsp;&nbsp; 🔴 Baja</div>
                """,
                unsafe_allow_html=True,
            )

    # 4. Informes cualitativos por segmento debajo del bloque principal.
    with st.container(border=True):
        st.markdown('<div class="market-dashboard-title">4. INSIGHTS DEL CONSUMIDOR POR SEGMENTO</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="market-dashboard-subtitle">Lectura tipo investigación comercial sobre qué afecta a la decisión de compra de cada segmento.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(_consumer_research_block_html(last_research, previous_research, team), unsafe_allow_html=True)

    # 6 conclusiones
    if best:
        good_items = [
            f"✅ Tu mejor posición aparece en <b>{segment_name_es(best['seg'])}</b> ({best['my_val']*100:.1f}%).",
            "✅ El informe permite identificar dónde compensa reforzar inversión.",
            "✅ Ya puedes priorizar segmentos con criterio de tamaño y oportunidad.",
        ]
    else:
        good_items = ["✅ Ya tienes una primera lectura estructurada del mercado."]
    if worst:
        bad_items = [
            f"⚠️ Tu presencia más débil está en <b>{segment_name_es(worst['seg'])}</b> ({worst['my_val']*100:.1f}%).",
            "⚠️ Evita repartir inversión sin una prioridad clara por segmento.",
            "⚠️ No confundas tamaño de mercado con oportunidad si el segmento está dominado.",
        ]
    else:
        bad_items = ["⚠️ Aún faltan datos para detectar debilidades por segmento."]
    if best_opp:
        opp_items = [
            f"⭐ <b>{segment_name_es(best_opp['seg'])}</b> muestra oportunidad {best_opp['opp'].lower()}.",
            f"⭐ El líder actual tiene {best_opp['leader_val']*100:.1f}% de cuota en ese segmento.",
            "⭐ Ajusta precio, distribución y comunicación al grupo con mayor potencial.",
        ]
    else:
        opp_items = ["⭐ Cierra una ronda adicional para detectar oportunidades más precisas."]
    st.markdown(
        f"""
        <div class="report-card"><div class="report-section-title">6. CONCLUSIONES Y RECOMENDACIONES</div>
            <div class="conclusion-grid">
                <div class="conclusion-box"><div class="conclusion-head" style="background:#2E974B;">LO ESTÁS HACIENDO BIEN</div><div class="conclusion-body"><ul>{''.join('<li>'+x+'</li>' for x in good_items)}</ul></div><div class="conclusion-footer footer-good">Sigue reforzando lo que funciona.</div></div>
                <div class="conclusion-box"><div class="conclusion-head" style="background:#F59E0B;">LO ESTÁS HACIENDO MAL</div><div class="conclusion-body"><ul>{''.join('<li>'+x+'</li>' for x in bad_items)}</ul></div><div class="conclusion-footer footer-bad">Ajusta tu enfoque para atacar mejor cada segmento.</div></div>
                <div class="conclusion-box"><div class="conclusion-head" style="background:#0B63B6;">OPORTUNIDADES</div><div class="conclusion-body"><ul>{''.join('<li>'+x+'</li>' for x in opp_items)}</ul></div><div class="conclusion-footer footer-opp">Actúa sobre estos segmentos para crecer.</div></div>
            </div>
        </div>
        <div class="market-reminder">💡 RECUERDA: Entender el mercado es el primer paso para tomar decisiones ganadoras.</div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# INFORME COMPETITIVO VISUAL PRO (APP)
# =========================================================
def _inject_competitive_report_styles():
    st.markdown(
        """
        <style>
        .comp-summary-grid { display:grid; grid-template-columns: 1.65fr repeat(5, minmax(120px, 1fr)); gap:10px; align-items:stretch; }
        .comp-summary-text { background:#FFFFFF; border:1px solid #E3EAF2; border-radius:16px; padding:15px 16px; min-height:150px; box-shadow:0 8px 24px rgba(9,30,66,.045); }
        .comp-kpi { background:#fff; border:1px solid #DCE6F2; border-radius:13px; padding:13px 10px; text-align:center; min-height:150px; box-shadow:0 4px 14px rgba(9,30,66,.05); }
        .comp-kpi-title { color:#1D2738; font-size:.73rem; font-weight:950; text-transform:uppercase; line-height:1.2; min-height:31px; }
        .comp-kpi-icon { font-size:1.85rem; color:#557398; margin:6px 0 8px 0; }
        .comp-kpi-value { color:#071E49; font-size:1.35rem; font-weight:950; line-height:1.1; }
        .comp-kpi-note { color:#53657D; font-size:.74rem; font-weight:750; margin-top:5px; line-height:1.2; }
        .comp-danger { color:#D94C3D; } .comp-good { color:#168A4A; } .comp-warn { color:#F59E0B; }
        .comp-grid-2 { display:grid; grid-template-columns: 1.05fr 1.12fr; gap:14px; }
        .comp-grid-4-5 { display:grid; grid-template-columns: 1.05fr 1.05fr; gap:14px; }
        .comp-table { width:100%; border-collapse:collapse; font-size:.78rem; }
        .comp-table th { color:#1D2738; text-align:center; font-weight:950; padding:8px 6px; border:1px solid #E4EAF3; background:#F6F9FC; }
        .comp-table td { padding:8px 6px; border:1px solid #E9EEF5; color:#1D2738; font-weight:700; vertical-align:middle; }
        .comp-table td.num { text-align:center; }
        .team-dot { width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:7px; vertical-align:middle; }
        .comp-note { background:#EEF6FF; border-radius:12px; padding:10px 12px; color:#173B66; font-size:.84rem; font-weight:750; margin-top:10px; line-height:1.35; }
        .strategy-pill { display:inline-block; padding:6px 11px; border-radius:8px; font-size:.72rem; font-weight:950; text-transform:uppercase; }
        .pill-premium { background:#DFF2DF; color:#138244; } .pill-balanced { background:#EFE3FF; color:#6D3FB1; } .pill-low { background:#FFE8C7; color:#B65D00; } .pill-value { background:#FDE1DF; color:#C4312B; } .pill-min { background:#EEF1F5; color:#56616D; }
        .dynamic-grid { display:grid; grid-template-columns: .92fr 1.05fr .85fr; gap:12px; }
        .dynamic-card { background:#fff; border:1px solid #E3EAF2; border-radius:13px; padding:12px; min-height:220px; }
        .dynamic-title { font-weight:950; color:#0B4B93; text-transform:uppercase; font-size:.78rem; margin-bottom:9px; }
        .group-box { border-radius:12px; padding:10px 12px; margin-bottom:8px; border:1px solid #E3EAF2; font-size:.82rem; }
        .group-box b { display:block; text-transform:uppercase; margin-bottom:3px; }
        .g-premium { background:#E8F5E9; color:#138244; border-color:#CFEAD2; } .g-balanced { background:#F5EEFF; color:#6D3FB1; border-color:#E2D2F5; } .g-low { background:#FFF4D6; color:#B56A00; border-color:#F5DDA2; } .g-value { background:#FDECEC; color:#C4312B; border-color:#F5C7C7; }
        .intensity-gauge { width:142px; height:72px; border-radius:142px 142px 0 0; background:conic-gradient(from 270deg, #D92D20 0deg 130deg, #E5EAF2 130deg 180deg, transparent 180deg 360deg); margin:6px auto 4px auto; position:relative; }
        .intensity-gauge:after { content:""; position:absolute; left:30px; top:30px; width:82px; height:42px; border-radius:82px 82px 0 0; background:#fff; }
        .relative-grid { display:grid; grid-template-columns: repeat(6, minmax(110px, 1fr)); gap:11px; }
        .relative-card { background:#fff; border:1px solid #E3EAF2; border-radius:13px; padding:12px; text-align:center; min-height:138px; }
        .relative-title { font-weight:950; color:#1D2738; font-size:.78rem; min-height:28px; }
        .relative-value { font-size:1.28rem; font-weight:950; color:#071E49; margin-top:5px; }
        .relative-note { color:#53657D; font-size:.76rem; font-weight:750; margin-top:2px; }
        .relative-bar { height:8px; background:#E4EAF3; border-radius:99px; margin:10px 0 7px 0; overflow:hidden; }
        .relative-fill { height:8px; background:#0B4B93; border-radius:99px; display:block; }
        .relative-read { font-size:.76rem; font-weight:900; }
        .comp-map-help { background:#EEF6FF; border-radius:12px; padding:13px; color:#173B66; font-size:.78rem; line-height:1.45; font-weight:700; }
        .comp-ranking-card { background:#FFFFFF; border:1px solid #E3EAF2; border-radius:14px; padding:13px; min-height:350px; }
        .comp-ranking-top { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-bottom:12px; }
        .comp-podium { border:1px solid #E3EAF2; border-radius:13px; padding:12px 10px; background:#FAFCFF; text-align:center; min-height:106px; }
        .comp-podium.pos1 { background:#FFF7E6; border-color:#FDE6B1; }
        .comp-podium.pos2 { background:#F4F7FB; border-color:#D9E2EF; }
        .comp-podium.pos3 { background:#FFF1E8; border-color:#FFD3B8; }
        .comp-podium-medal { font-size:1.55rem; line-height:1; margin-bottom:5px; }
        .comp-podium-team { color:#071E49; font-size:.90rem; font-weight:950; line-height:1.12; }
        .comp-podium-score { color:#53657D; font-size:.74rem; font-weight:850; margin-top:5px; }
        .comp-ranking-table { width:100%; border-collapse:separate; border-spacing:0 8px; font-size:.78rem; }
        .comp-ranking-table th { color:#53657D; text-align:left; font-size:.70rem; font-weight:950; text-transform:uppercase; padding:0 8px 2px 8px; }
        .comp-ranking-table td { background:#fff; border-top:1px solid #E6EDF7; border-bottom:1px solid #E6EDF7; padding:10px 8px; color:#1D2738; font-weight:800; vertical-align:middle; }
        .comp-ranking-table td:first-child { border-left:1px solid #E6EDF7; border-radius:12px 0 0 12px; }
        .comp-ranking-table td:last-child { border-right:1px solid #E6EDF7; border-radius:0 12px 12px 0; }
        .comp-ranking-table tr.is-you td { background:#EEF6FF; border-color:#BFD7FF; color:#071E49; }
        .comp-rank-position { font-size:1.05rem; font-weight:950; color:#0B63B6; white-space:nowrap; }
        .comp-rank-scorebar { display:inline-block; width:78px; height:8px; border-radius:999px; background:#E4EAF3; overflow:hidden; vertical-align:middle; margin-right:6px; }
        .comp-rank-scorebar span { display:block; height:100%; border-radius:999px; background:#0B63B6; }
        .comp-rank-help { background:#EEF6FF; border-radius:12px; padding:12px 13px; color:#173B66; font-size:.79rem; line-height:1.45; font-weight:750; margin-top:10px; }
        @media (max-width: 1150px) {
            .comp-summary-grid, .comp-grid-2, .comp-grid-4-5, .dynamic-grid, .relative-grid { grid-template-columns:1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _comp_team_color(i):
    palette = ["#0B63B6", "#2E974B", "#8755D9", "#F59E0B", "#D64545", "#9AA4B2", "#00A3A3", "#B76E00"]
    return palette[i % len(palette)]


def _comp_df(last_truth):
    df = pd.DataFrame(last_truth or []).copy()
    if df.empty:
        return df
    defaults = {
        "quality": 0.0,
        "distribution": 0.0,
        "promo": 0.0,
        "comm_total": 0.0,
        "product_investment_cost": 0.0,
        "share": 0.0,
        "units": 0.0,
        "awareness_true": 0.0,
        "price": 0.0,
        "profit": 0.0,
    }
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val
    df["product_investment_cost"] = df.get("product_investment_cost", 0.0).fillna(0.0)
    return df


def _comp_summary(df):
    sorted_df = df.sort_values("share", ascending=False)
    leader = sorted_df.iloc[0]
    second = sorted_df.iloc[1] if len(sorted_df) > 1 else leader
    gap = (float(leader.get("share", 0.0)) - float(second.get("share", 0.0))) * 100
    score = max(1.0, min(10.0, 10.0 - gap / 2.0))
    intensity = "Alta" if score >= 8 else "Media" if score >= 6 else "Baja"
    return {
        "leader": str(leader.get("team", "-")),
        "leader_share": float(leader.get("share", 0.0)),
        "second": str(second.get("team", "-")),
        "second_share": float(second.get("share", 0.0)),
        "gap": gap,
        "score": score,
        "intensity": intensity,
        "avg_comm": float(df["comm_total"].mean()),
        "avg_dist": float(df["distribution"].mean()),
        "avg_price": float(df["price"].mean()),
        "avg_quality": float(df["quality"].mean()),
        "avg_promo": float(df["promo"].mean()),
        "avg_product": float(df["product_investment_cost"].mean()),
    }


def _comp_strategy(row, avg_price, avg_quality):
    price = float(row.get("price", 0.0))
    quality = float(row.get("quality", 0.0))
    promo = float(row.get("promo", 0.0))
    dist = float(row.get("distribution", 0.0))
    if price >= avg_price + 0.35 and quality >= avg_quality:
        return "PREMIUM", "Calidad + Marca", "pill-premium"
    if price <= avg_price - 0.35 and promo >= 0.10:
        return "BAJO COSTE", "Precio + Promoción", "pill-low"
    if price <= avg_price and quality >= avg_quality:
        return "VALOR", "Valor funcional", "pill-value"
    if price <= avg_price - 0.25:
        return "BAJO COSTE", "Precio mínimo", "pill-min"
    return "EQUILIBRADA", "Equilibrio valor/calidad", "pill-balanced"


def _comp_comm_label(row):
    return classify_comm_style(row)


def _comp_strength(row, df):
    parts = []
    if float(row.get("quality", 0.0)) >= float(df["quality"].mean()):
        parts.append("alta calidad percibida")
    if float(row.get("distribution", 0.0)) >= float(df["distribution"].mean()):
        parts.append("buena cobertura")
    if float(row.get("comm_total", 0.0)) >= float(df["comm_total"].mean()):
        parts.append("comunicación sólida")
    if float(row.get("promo", 0.0)) >= float(df["promo"].mean()):
        parts.append("activación promocional")
    return ", ".join(parts[:3]) if parts else "estrategia discreta, sin ventaja clara"


def _comp_market_text(summary):
    return (
        f"El mercado está liderado por {summary['leader']} con una cuota de mercado del "
        f"{summary['leader_share'] * 100:.1f}%, seguido de cerca por {summary['second']} "
        f"({summary['second_share'] * 100:.1f}%). La competencia se divide entre estrategias de precio, "
        f"valor y diferenciación por calidad. La intensidad competitiva es {summary['intensity'].lower()}."
    )


def _render_comp_kpi(title, icon, value, note="", tone=""):
    tone_cls = {"good":"comp-good", "warn":"comp-warn", "bad":"comp-danger"}.get(tone, "")
    st.markdown(
        f"""
        <div class="comp-kpi">
            <div class="comp-kpi-title">{_html_escape(title)}</div>
            <div class="comp-kpi-icon">{icon}</div>
            <div class="comp-kpi-value {tone_cls}">{_html_escape(value)}</div>
            <div class="comp-kpi-note">{_html_escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _build_comp_position_map(df, team):
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No hay datos competitivos.", x=.5, y=.5, xref="paper", yref="paper", showarrow=False)
        fig.update_layout(height=360)
        return fig
    avg_price = max(float(df["price"].mean()), 0.01)
    avg_quality = float(df["quality"].mean()) * 10
    for i, (_, r) in enumerate(df.iterrows()):
        is_you = str(r.get("team")) == team
        fig.add_trace(go.Scatter(
            x=[float(r.get("price", 0.0)) / avg_price * 100],
            y=[float(r.get("quality", 0.0)) * 10],
            mode="markers+text",
            text=[f"{r.get('team')} (Tú)" if is_you else str(r.get("team"))],
            textposition="top center",
            marker=dict(size=18 if is_you else 13, color=_comp_team_color(i), line=dict(width=1, color="white")),
            showlegend=False,
            hovertemplate="<b>%{text}</b><br>Precio índice: %{x:.0f}<br>Calidad: %{y:.1f}/10<extra></extra>",
        ))
    fig.add_vline(x=100, line_dash="dash", line_color="#CBD5E1")
    fig.add_hline(y=avg_quality, line_dash="dash", line_color="#CBD5E1")
    fig.update_layout(
        title="Precio vs. calidad percibida",
        xaxis_title="Precio percibido (índice)",
        yaxis_title="Calidad percibida",
        height=350,
        margin=dict(l=10, r=10, t=42, b=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_yaxes(range=[0, 10])
    return fig


def _comp_bar(value, max_value=1.0, color="#0B4B93"):
    pct = max(6, min(100, float(value) / max(float(max_value), 0.01) * 100))
    return f"<span class='bar-mini'><span class='bar-mini-fill' style='width:{pct:.0f}%; background:{color};'></span></span>"


def _comp_comparison_table(df, team):
    max_comm = max(float(df["comm_total"].max()), 1.0)
    rows = []
    for i, (_, r) in enumerate(df.sort_values("share", ascending=False).iterrows()):
        color = _comp_team_color(i)
        name = f"{r['team']} (Tú)" if r["team"] == team else str(r["team"])
        rows.append(
            f"<tr>"
            f"<td><span class='team-dot' style='background:{color}'></span><b>{_html_escape(name)}</b></td>"
            f"<td class='num'>{float(r['price']):.2f}</td>"
            f"<td class='num'>{float(r['quality']) * 10:.1f}</td>"
            f"<td class='num'>{float(r['distribution']) * 100:.0f}%</td>"
            f"<td class='num'>{float(r['promo']) * 100:.1f}%</td>"
            f"<td class='num'>{_fmt_int_plain(r['product_investment_cost'])} €</td>"
            f"<td class='num'>{_fmt_int_plain(r['comm_total'])} €</td>"
            f"</tr>"
        )
    return "".join(rows)


def _comp_profile_table(df, team, summary):
    rows = []
    for i, (_, r) in enumerate(df.sort_values("share", ascending=False).iterrows()):
        strat, focus, cls = _comp_strategy(r, summary["avg_price"], summary["avg_quality"])
        name = f"{r['team']} (Tú)" if r["team"] == team else str(r["team"])
        rows.append(
            f"<tr>"
            f"<td><span class='team-dot' style='background:{_comp_team_color(i)}'></span><b>{_html_escape(name)}</b></td>"
            f"<td class='num'><span class='strategy-pill {cls}'>{_html_escape(strat)}</span></td>"
            f"<td>{_html_escape(focus)}</td>"
            f"<td>{_html_escape(_comp_comm_label(r))}</td>"
            f"<td>{_html_escape(_comp_strength(r, df))}</td>"
            f"</tr>"
        )
    return "".join(rows)


def _comp_groups(df, team, summary):
    groups = {"PREMIUM": [], "EQUILIBRADA": [], "BAJO COSTE": [], "VALOR": []}
    for _, r in df.iterrows():
        strat, _, _ = _comp_strategy(r, summary["avg_price"], summary["avg_quality"])
        groups.setdefault(strat, []).append(f"{r['team']} (Tú)" if r["team"] == team else str(r["team"]))
    return groups


def _comp_relative_metrics(team, df, summary):
    row_df = df[df["team"] == team]
    if row_df.empty:
        return []
    r = row_df.iloc[0]
    return [
        ("Precio (índice)", f"{float(r['price']) / max(summary['avg_price'], 0.01) * 100:.0f}", f"vs. media: 100", float(r['price']) - summary['avg_price'], "Más caro que la media" if float(r['price']) > summary['avg_price'] else "Más barato que la media"),
        ("Calidad (0-10)", f"{float(r['quality']) * 10:.1f}", f"vs. media: {summary['avg_quality'] * 10:.1f}", float(r['quality']) - summary['avg_quality'], "Por encima de la media" if float(r['quality']) >= summary['avg_quality'] else "Por debajo de la media"),
        ("Distribución (%)", f"{float(r['distribution']) * 100:.0f}%", f"vs. media: {summary['avg_dist'] * 100:.0f}%", float(r['distribution']) - summary['avg_dist'], "Mayor cobertura" if float(r['distribution']) >= summary['avg_dist'] else "Menor cobertura"),
        ("Promoción (% ventas)", f"{float(r['promo']) * 100:.1f}%", f"vs. media: {summary['avg_promo'] * 100:.1f}%", float(r['promo']) - summary['avg_promo'], "Más agresiva" if float(r['promo']) >= summary['avg_promo'] else "Por debajo de la media"),
        ("Comunicación total (€)", fmt_eur(float(r['comm_total'])), f"vs. media: {fmt_eur(summary['avg_comm'])}", float(r['comm_total']) - summary['avg_comm'], "Mayor inversión" if float(r['comm_total']) >= summary['avg_comm'] else "Menor inversión"),
        ("Inversión producto (€)", fmt_eur(float(r['product_investment_cost'])), f"vs. media: {fmt_eur(summary['avg_product'])}", float(r['product_investment_cost']) - summary['avg_product'], "Mayor inversión" if float(r['product_investment_cost']) >= summary['avg_product'] else "Menor inversión"),
    ]


def _render_relative_card(title, value, note, diff, read):
    color = "#178A46" if diff >= 0 else "#D92D20"
    fill = 62 if diff >= 0 else 38
    st.markdown(
        f"""
        <div class="relative-card">
            <div class="relative-title">{_html_escape(title)}</div>
            <div class="relative-value">{_html_escape(value)}</div>
            <div class="relative-note">{_html_escape(note)}</div>
            <div class="relative-bar"><span class="relative-fill" style="width:{fill}%;"></span></div>
            <div class="relative-read" style="color:{color};">{_html_escape(read)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _comp_three_boxes(team, df, summary):
    row_df = df[df["team"] == team]
    if row_df.empty:
        return ["Sin datos específicos de tu marca."], ["No se encontró tu equipo."], ["Revisa la configuración de la partida."]
    r = row_df.iloc[0]
    good, bad, opp = [], [], []
    if float(r["quality"]) >= summary["avg_quality"]:
        good.append("Tu calidad percibida está por encima de la media.")
    else:
        bad.append("Tu calidad percibida no destaca frente a la media.")
    if float(r["comm_total"]) >= summary["avg_comm"]:
        good.append("Tu inversión en comunicación está por encima de la media.")
    else:
        opp.append("Aumentar comunicación puede ayudarte a ganar visibilidad.")
    if float(r["distribution"]) >= summary["avg_dist"]:
        good.append("Tu distribución está por encima o alineada con la media.")
    else:
        bad.append("Tu distribución está por debajo de la media competitiva.")
    if float(r["price"]) > summary["avg_price"] + 0.35 and float(r["quality"]) < summary["avg_quality"]:
        bad.append("Tu precio es superior a la media sin ser líder claro en calidad.")
    elif float(r["price"]) < summary["avg_price"] - 0.35:
        good.append("Tienes una posición de precio competitiva frente al mercado.")
    low_quality = df.sort_values("quality", ascending=True).iloc[0]
    leader = df.sort_values("share", ascending=False).iloc[0]
    opp.append(f"{low_quality['team']} muestra menor calidad percibida: puede ser una oportunidad de diferenciación.")
    opp.append(f"Analiza a {leader['team']}: lidera cuota y marca el estándar competitivo.")
    return good[:4] or ["Mantienes una posición competitiva razonable."], bad[:4] or ["No aparece una debilidad competitiva crítica."], opp[:4]


def _render_comp_conclusion(title, items, head_color, footer, footer_cls):
    lis = "".join(f"<li>{_html_escape(x)}</li>" for x in items)
    st.markdown(
        f"""
        <div class="conclusion-box">
            <div class="conclusion-head" style="background:{head_color};">{_html_escape(title)}</div>
            <div class="conclusion-body"><ul>{lis}</ul></div>
            <div class="conclusion-footer {footer_cls}">{_html_escape(footer)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_competitive_header(round_label, team):
    st.markdown(
        f"""
        <div class="report-hero">
            <div class="report-hero-icon">🏆</div>
            <div>
                <div class="report-hero-title">INFORME COMPETITIVO</div>
                <div class="report-hero-subtitle">Análisis de la competencia y posicionamiento relativo</div>
            </div>
            <div class="report-hero-meta">
                <div><span>⚙️ Ronda:</span>{_html_escape(round_label)}</div>
                <div><span>📅 Fecha:</span>—</div>
                <div><span>🎯 Tu marca:</span>{_html_escape(team)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def _comp_game_ranking(df, team):
    """Ranking competitivo ponderado por cuota, ventas y beneficio."""
    if df.empty:
        return pd.DataFrame()

    work = df.copy()
    for col in ["share", "units", "profit"]:
        if col not in work.columns:
            work[col] = 0.0
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0.0)

    max_units = max(float(work["units"].max()), 1.0)
    max_profit_abs = max(float(work["profit"].abs().max()), 1.0)

    # Mismo enfoque que el resumen: cuota + ventas + beneficio.
    work["ranking_score"] = (
        work["share"].clip(lower=0) * 45
        + (work["units"].clip(lower=0) / max_units) * 30
        + (work["profit"] / max_profit_abs) * 25
    )
    work = work.sort_values(["ranking_score", "share", "units"], ascending=[False, False, False]).reset_index(drop=True)
    work["position"] = work.index + 1
    work["is_you"] = work["team"].astype(str) == str(team)
    return work


def _render_comp_game_ranking(df, team):
    ranking = _comp_game_ranking(df, team)
    if ranking.empty:
        st.info("No hay datos suficientes para construir el ranking del juego.")
        return

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    podium_html = ""
    for pos in [1, 2, 3]:
        row_df = ranking[ranking["position"] == pos]
        if row_df.empty:
            continue
        r = row_df.iloc[0]
        team_name = f"{r['team']} (Tú)" if bool(r.get("is_you")) else str(r["team"])
        podium_html += (
            f"<div class='comp-podium pos{pos}'>"
            f"<div class='comp-podium-medal'>{medals.get(pos, '🏅')}</div>"
            f"<div class='comp-podium-team'>{_html_escape(team_name)}</div>"
            f"<div class='comp-podium-score'>{float(r.get('share', 0.0)) * 100:.1f}% cuota · {fmt_eur(float(r.get('profit', 0.0)))}</div>"
            f"</div>"
        )

    max_score = max(float(ranking["ranking_score"].max()), 1.0)
    rows_html = ""
    for _, r in ranking.iterrows():
        is_you_cls = " class='is-you'" if bool(r.get("is_you")) else ""
        team_name = f"{r['team']} (Tú)" if bool(r.get("is_you")) else str(r["team"])
        score_pct = max(4.0, min(100.0, float(r.get("ranking_score", 0.0)) / max_score * 100))
        rows_html += (
            f"<tr{is_you_cls}>"
            f"<td><span class='comp-rank-position'>{int(r['position'])}º</span></td>"
            f"<td><b>{_html_escape(team_name)}</b></td>"
            f"<td>{_fmt_int_plain(r.get('units', 0.0))}</td>"
            f"<td>{fmt_eur(r.get('profit', 0.0))}</td>"
            f"<td>{float(r.get('share', 0.0)) * 100:.1f}%</td>"
            f"<td><span class='comp-rank-scorebar'><span style='width:{score_pct:.0f}%;'></span></span>{float(r.get('ranking_score', 0.0)):.1f}</td>"
            f"</tr>"
        )

    you_row = ranking[ranking["is_you"]]
    if not you_row.empty:
        you_pos = int(you_row.iloc[0]["position"])
        you_text = f"Tu equipo está en {you_pos}ª posición de {len(ranking)}. El ranking combina cuota de mercado, ventas y beneficio."
    else:
        you_text = "El ranking combina cuota de mercado, ventas y beneficio para resumir la posición global."

    st.markdown(
        f"""
        <div class="comp-ranking-card">
            <div class="comp-ranking-top">{podium_html}</div>
            <table class="comp-ranking-table">
                <thead>
                    <tr><th>Pos.</th><th>Equipo</th><th>Ventas</th><th>Beneficio</th><th>Cuota</th><th>Puntuación</th></tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
            <div class="comp-rank-help">🏆 {_html_escape(you_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_competitive_report_dashboard_visual(team, state):
    _inject_competitive_report_styles()
    last_truth = state.get("last_truth") or []
    df = _comp_df(last_truth)
    if df.empty:
        st.info("No hay datos competitivos disponibles.")
        return
    history = state.get("history", []) or []
    round_label = history[-1].get("round", state.get("round_n", "-")) if history else state.get("round_n", "-")
    summary = _comp_summary(df)
    _render_competitive_header(round_label, team)

    st.markdown('<div class="comp-summary-grid">', unsafe_allow_html=True)
    st.markdown(f'<div class="comp-summary-text"><div class="report-section-title">1. RESUMEN COMPETITIVO</div><div class="report-muted" style="font-size:.92rem; font-weight:650; color:#1D2738;">{_html_escape(_comp_market_text(summary))}</div></div>', unsafe_allow_html=True)
    c = st.columns(5)
    with c[0]: _render_comp_kpi("Líder en cuota de mercado", "♕", summary["leader"], f"{summary['leader_share'] * 100:.1f}%")
    with c[1]: _render_comp_kpi("Diferencia entre 1º y 2º", "◔", f"{summary['gap']:.1f} p.p.", "Muy ajustada" if summary["gap"] < 5 else "Brecha relevante")
    with c[2]: _render_comp_kpi("Intensidad competitiva", "📈", summary["intensity"], "Mercado muy competido" if summary["intensity"] == "Alta" else "Competencia moderada", "bad" if summary["intensity"] == "Alta" else "warn")
    with c[3]: _render_comp_kpi("Inversión media en comunicación", "📣", fmt_eur(summary["avg_comm"]), "Por empresa")
    with c[4]: _render_comp_kpi("Nivel medio de distribución", "🎯", f"{summary['avg_dist'] * 100:.0f}%", "Cobertura ponderada")
    st.markdown('</div>', unsafe_allow_html=True)

    left, right = st.columns([1.05, 1.12])
    with left:
        st.markdown(f"""
        <div class="report-card">
            <div class="report-section-title">2. COMPARATIVA DE EMPRESAS</div>
            <table class="comp-table">
                <thead><tr><th>Empresa</th><th>Precio</th><th>Calidad<br>(0-10)</th><th>Distrib.</th><th>Promo.</th><th>Producto</th><th>Comunicación</th></tr></thead>
                <tbody>{_comp_comparison_table(df, team)}</tbody>
            </table>
            <div class="comp-note">📊 { _html_escape(_comp_strength(df[df['team']==team].iloc[0], df) if not df[df['team']==team].empty else 'Analiza tu posición frente a los rivales.') }</div>
        </div>
        """, unsafe_allow_html=True)
    with right:
        st.markdown('<div class="report-card"><div class="report-section-title">3. RANKING DEL JUEGO <span style="font-size:.82rem; text-transform:none;">(posición global competitiva)</span></div>', unsafe_allow_html=True)
        _render_comp_game_ranking(df, team)
        st.markdown('</div>', unsafe_allow_html=True)

    left2, right2 = st.columns([1.05, 1.05])
    with left2:
        st.markdown(f"""
        <div class="report-card">
            <div class="report-section-title">4. PERFIL ESTRATÉGICO DE LOS COMPETIDORES</div>
            <table class="comp-table">
                <thead><tr><th>Empresa</th><th>Tipo de estrategia</th><th>Enfoque principal</th><th>Estilo comunicación</th><th>Fortaleza clave</th></tr></thead>
                <tbody>{_comp_profile_table(df, team, summary)}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    with right2:
        leaders = {
            "Calidad percibida": df.sort_values("quality", ascending=False).iloc[0]["team"],
            "Distribución": df.sort_values("distribution", ascending=False).iloc[0]["team"],
            "Comunicación total": df.sort_values("comm_total", ascending=False).iloc[0]["team"],
            "Agresividad promocional": df.sort_values("promo", ascending=False).iloc[0]["team"],
            "Precio más bajo": df.sort_values("price", ascending=True).iloc[0]["team"],
        }
        groups = _comp_groups(df, team, summary)
        leader_lines = "".join(f"<b>{_html_escape(k)}:</b><br>• {_html_escape(v)}<br>" for k, v in leaders.items())
        group_blocks = ""
        for label, cls in [("PREMIUM", "g-premium"), ("EQUILIBRADA", "g-balanced"), ("BAJO COSTE", "g-low"), ("VALOR", "g-value")]:
            items = groups.get(label, [])
            item_txt = "<br>• " + "<br>• ".join(_html_escape(x) for x in items) if items else "<br>• -"
            group_blocks += f"<div class='group-box {cls}'><b>{label}</b>{item_txt}</div>"
        st.markdown(f"""
        <div class="report-card">
            <div class="report-section-title">5. DINÁMICA COMPETITIVA</div>
            <div class="dynamic-grid">
                <div class="dynamic-card"><div class="dynamic-title">Líderes por dimensión</div><div style="font-size:.82rem; line-height:1.55; color:#344054;">{leader_lines}</div></div>
                <div class="dynamic-card"><div class="dynamic-title">Grupos estratégicos</div>{group_blocks}</div>
                <div class="dynamic-card" style="text-align:center;"><div class="dynamic-title" style="text-align:left;">Intensidad competitiva</div><div class="intensity-gauge"></div><div style="font-size:2.1rem; font-weight:950; color:#071E49;">{summary['score']:.1f}<span style="font-size:.9rem;">/10</span></div><div style="color:#D92D20; font-weight:950;">{summary['intensity']}</div><div style="margin-top:8px; color:#344054; font-size:.82rem; line-height:1.35;">Mercado con propuestas cercanas. Diferenciar tu marca será clave.</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="report-card"><div class="report-section-title">6. TU POSICIÓN RELATIVA FRENTE A LA MEDIA DE COMPETIDORES</div>', unsafe_allow_html=True)
    metrics = _comp_relative_metrics(team, df, summary)
    cols = st.columns(6)
    for col, item in zip(cols, metrics):
        with col:
            _render_relative_card(*item)
    st.markdown('<div class="comp-note">⭐ Tu posición relativa muestra dónde estás por encima o por debajo de la media. Úsalo para decidir si quieres competir en valor, premium o equilibrio.</div></div>', unsafe_allow_html=True)

    good, bad, opp = _comp_three_boxes(team, df, summary)
    st.markdown('<div class="report-card"><div class="report-section-title">7. CONCLUSIONES Y RECOMENDACIONES</div><div class="conclusion-grid">', unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    with b1:
        _render_comp_conclusion("Lo estás haciendo bien", good, "#2E974B", "Sigue reforzando tu propuesta diferencial.", "footer-good")
    with b2:
        _render_comp_conclusion("Lo estás haciendo mal", bad, "#F59E0B", "Ajusta las palancas donde estás por debajo.", "footer-bad")
    with b3:
        _render_comp_conclusion("Oportunidades", opp, "#0B63B6", "Aprovecha los huecos estratégicos del mercado.", "footer-opp")
    st.markdown('</div></div><div class="market-reminder">💡 RECUERDA: Conoce a tu competencia, diferencia tu propuesta y comunica lo que te hace único.</div>', unsafe_allow_html=True)


# -------------------------------------------------
# INFORME DE MARCA VISUAL PRO
# -------------------------------------------------
def _brand_team_row(state, team):
    rows = state.get("last_truth") or []
    return next((r for r in rows if r.get("team") == team), None) or {}


def _brand_history_rows(state, team):
    out = []
    for item in state.get("history", []) or []:
        rnum = item.get("round")
        for row in item.get("truth", []) or []:
            if row.get("team") == team:
                out.append({"round": rnum, **row})
    return out


def _brand_delta(history_rows, key, mult=1.0):
    if len(history_rows) < 2:
        return None
    return (float(history_rows[-1].get(key, 0.0)) - float(history_rows[-2].get(key, 0.0))) * mult


def _brand_satisfaction_score(row):
    # El motor guarda satisfacción como valor interno. La llevamos a escala 0-10 para que sea más pedagógica.
    raw = float(row.get("satisfaction", 0.0))
    return max(0.0, min(10.0, 5.0 + raw * 2.0))


def _brand_strategy_type(row, research, team):
    price = float(row.get("price", (research or {}).get("observed_avg_price", {}).get(team, 0.0) or 0.0))
    quality = float(row.get("quality", (research or {}).get("estimated_quality", {}).get(team, 0.0) or 0.0))
    promo = float(row.get("promo", 0.0))
    comm_pr = float(row.get("comm_pr", 0.0))
    comm_trad = float(row.get("comm_trad", 0.0))
    comm_online = float(row.get("comm_online", 0.0))
    premium_signal = int(price >= 9.0) + int(quality >= .62) + int(comm_pr + comm_trad > comm_online) + int(promo <= .10)
    value_signal = int(price <= 8.2) + int(promo >= .08) + int(float(row.get("distribution", 0.0)) >= .70) + int(comm_online >= comm_pr)
    if premium_signal >= value_signal + 2:
        return "DIFERENCIACIÓN PREMIUM", "Basada en calidad y marca, con un precio superior al promedio."
    if value_signal >= premium_signal + 2:
        return "ESTRATEGIA DE VALOR", "Basada en precio competitivo, cobertura y activación comercial."
    return "ESTRATEGIA EQUILIBRADA", "Combina señales de valor y marca sin una orientación extrema."


def _build_brand_health_chart(state, team):
    rows = _brand_history_rows(state, team)
    fig = go.Figure()
    if not rows:
        fig.add_annotation(text="Aún no hay histórico de marca.", x=.5, y=.5, xref="paper", yref="paper", showarrow=False)
    else:
        xs = [r.get("round") for r in rows]
        awareness = [float(r.get("awareness_true", 0.0)) * 100 for r in rows]
        satisfaction = [_brand_satisfaction_score(r) for r in rows]
        retention = [float(r.get("retention_rate", 0.0)) * 100 for r in rows]
        fig.add_trace(go.Scatter(x=xs, y=awareness, mode="lines+markers+text", text=[f"{v:.0f}%" for v in awareness], textposition="top center", name="Conocimiento (%)", line=dict(color="#0B4B93", width=3), marker=dict(size=8)))
        fig.add_trace(go.Scatter(x=xs, y=retention, mode="lines+markers+text", text=[f"{v:.0f}%" for v in retention], textposition="bottom center", name="Retención (%)", line=dict(color="#8755D9", width=3), marker=dict(size=8)))
        fig.add_trace(go.Scatter(x=xs, y=[v*10 for v in satisfaction], mode="lines+markers+text", text=[f"{v:.1f}" for v in satisfaction], textposition="top center", name="Satisfacción (0-10)", line=dict(color="#168A4A", width=3), marker=dict(size=8), yaxis="y2"))
    fig.update_layout(height=330, margin=dict(l=15, r=15, t=25, b=20), plot_bgcolor="white", paper_bgcolor="white", legend=dict(orientation="h", y=1.12, x=.02), yaxis=dict(title="%", range=[0,100], gridcolor="#EEF2F7"), yaxis2=dict(title="0-10", overlaying="y", side="right", range=[0,10]))
    return fig


def _build_brand_positioning_chart(state, team):
    research = state.get("last_research") or {}
    prices = research.get("observed_avg_price", {}) or {}
    qualities = research.get("estimated_quality", {}) or {}
    fig = go.Figure()
    if not prices or not qualities:
        return build_positioning_chart_from_last_research(state, highlight_team=team)
    xs = [float(v) for k, v in prices.items() if k in qualities]
    avg_price = sum(xs) / len(xs) if xs else 8.5
    colors = ["#0B4B93", "#2E974B", "#8755D9", "#F59E0B", "#D92D20", "#9AA4B2"]
    for i, t in enumerate(prices):
        if t not in qualities:
            continue
        fig.add_trace(go.Scatter(x=[float(prices[t])], y=[float(qualities[t])*100], mode="markers+text", text=[f"{t} (Tú)" if t == team else t], textposition="top center", marker=dict(size=18 if t == team else 13, color="#0B4B93" if t == team else colors[i % len(colors)]), showlegend=False))
    fig.add_vline(x=avg_price, line_dash="dash", line_color="#BFC7D5")
    fig.add_hline(y=60, line_dash="dash", line_color="#BFC7D5")
    fig.update_layout(height=330, margin=dict(l=15, r=15, t=20, b=20), xaxis_title="Precio percibido", yaxis_title="Calidad percibida", plot_bgcolor="white", paper_bgcolor="white")
    fig.update_yaxes(range=[0,100])
    return fig


def _brand_funnel_values(row, research, team, truth_rows):
    avg = {}
    for key in ["funnel_knowledge", "funnel_consideration", "funnel_purchase", "funnel_retention"]:
        vals = [float(r.get(key, 0.0)) for r in truth_rows or []]
        avg[key] = sum(vals) / len(vals) if vals else 0.0
    vals = {
        "Conocimiento": (float(row.get("funnel_knowledge", row.get("awareness_true", 0.0))), avg.get("funnel_knowledge", 0.0)),
        "Consideración": (float((research or {}).get("estimated_funnel_consideration", {}).get(team, row.get("funnel_consideration", 0.0))), avg.get("funnel_consideration", 0.0)),
        "Compra": (float(row.get("share", 0.0)), sum(float(r.get("share", 0.0)) for r in (truth_rows or [])) / max(len(truth_rows or []), 1)),
        "Retención": (float(row.get("retention_rate", 0.0)), avg.get("funnel_retention", 0.0) or float(row.get("retention_rate", 0.0))),
    }
    return vals


def _brand_three_boxes(row, research, team, truth_rows):
    quality = float(row.get("quality", 0.0))
    awareness = float(row.get("awareness_true", 0.0))
    retention = float(row.get("retention_rate", 0.0))
    price = float(row.get("price", 0.0))
    dist = float(row.get("distribution", 0.0))
    promo = float(row.get("promo", 0.0))
    avg_quality = sum(float(r.get("quality", 0.0)) for r in truth_rows) / max(len(truth_rows), 1) if truth_rows else quality
    avg_aw = sum(float(r.get("awareness_true", 0.0)) for r in truth_rows) / max(len(truth_rows), 1) if truth_rows else awareness
    avg_ret = sum(float(r.get("retention_rate", 0.0)) for r in truth_rows) / max(len(truth_rows), 1) if truth_rows else retention
    good = []
    if quality >= avg_quality: good.append("Calidad percibida por encima de la media del mercado.")
    if awareness >= avg_aw: good.append("Buen nivel de conocimiento: tu marca mantiene visibilidad relativa.")
    if retention >= avg_ret: good.append("Retención superior a la media: los clientes confían y repiten más.")
    if float(row.get("strategy_coherence", 0.0)) >= 0: good.append("La estrategia mantiene una coherencia razonable entre producto, precio y activación.")
    bad = []
    if price > sum(float(r.get("price", 0.0)) for r in truth_rows) / max(len(truth_rows),1) + .30 and quality < avg_quality + .05: bad.append("Precio percibido alto sin una ventaja clara de calidad frente a la media.")
    if retention < avg_ret: bad.append("La retención está por debajo de la media y puede indicar clientes probando alternativas.")
    if dist < .55: bad.append("Distribución limitada: puede frenar disponibilidad y conversión.")
    if promo > .12: bad.append("Promoción elevada: puede dañar margen y posicionamiento si se mantiene.")
    opp = []
    seg_mix = (research or {}).get("segment_brand_mix", {}) or {}
    if seg_mix:
        best_seg = max(seg_mix.keys(), key=lambda s: float(seg_mix[s].get(team, 0.0)))
        opp.append(f"Segmento {segment_name_es(best_seg)}: buen encaje para aumentar cuota.")
    opp.append("Ajuste de precio o comunicación: mejorar percepción de valor y conversión.")
    if dist < .75: opp.append("Aumentar inversión en distribución: más cobertura para captar clientes.")
    opp.append("Fidelización: programas de retención pueden elevar repetición de compra.")
    return (good or ["Tu marca ya tiene una base desde la que seguir construyendo."], bad or ["No aparece una debilidad crítica, pero todavía puedes mejorar conversión y foco."], opp[:4])


def _render_brand_kpi(title, icon, value, delta=None, tone="good"):
    color = "#168A4A" if tone == "good" else ("#D92D20" if tone == "bad" else "#53657D")
    delta_html = f"<div class='brand-kpi-delta' style='color:{color};'>{_html_escape(delta)}</div>" if delta else ""
    st.markdown(f"""
    <div class="brand-kpi">
      <div class="brand-kpi-title">{_html_escape(title)}</div>
      <div class="brand-kpi-icon">{icon}</div>
      <div class="brand-kpi-value">{value}</div>
      {delta_html}
    </div>
    """, unsafe_allow_html=True)


def _render_brand_conclusion(title, items, head_color, footer, footer_class, icon):
    lis = "".join(f"<li><span>{icon}</span>{_html_escape(x)}</li>" for x in items[:4])
    st.markdown(f"""
      <div class="conclusion-box">
        <div class="conclusion-head" style="background:{head_color};">{_html_escape(title)}</div>
        <div class="conclusion-body"><ul>{lis}</ul></div>
        <div class="conclusion-footer {footer_class}">{_html_escape(footer)}</div>
      </div>
    """, unsafe_allow_html=True)



def _render_brand_header(round_label, team):
    st.markdown(
        f"""
        <div class="report-hero">
            <div class="report-hero-icon">🏷️</div>
            <div>
                <div class="report-hero-title">INFORME DE MARCA</div>
                <div class="report-hero-subtitle">Análisis completo de tu marca</div>
            </div>
            <div class="report-hero-meta">
                <div><span>⚙️ Ronda:</span>{_html_escape(round_label)}</div>
                <div><span>📅 Fecha:</span>Última ronda cerrada</div>
                <div><span>🌐 Tu marca:</span>{_html_escape(team)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
def render_brand_report_dashboard_visual(team, state):
    inject_reports_pro_styles()
    st.markdown("""
    <style>
    .brand-kpi { background:#fff; border:1px solid #DCE6F2; border-radius:13px; padding:13px 10px; text-align:center; min-height:150px; box-shadow:0 4px 14px rgba(9,30,66,.05); }
    .brand-kpi-title { color:#1D2738; font-size:.78rem; font-weight:950; line-height:1.15; min-height:33px; }
    .brand-kpi-icon { font-size:2rem; color:#557398; margin:8px 0; }
    .brand-kpi-value { color:#071E49; font-size:1.75rem; font-weight:950; line-height:1.05; }
    .brand-kpi-delta { font-size:.82rem; font-weight:950; margin-top:8px; }
    .brand-summary-grid { display:grid; grid-template-columns: .78fr repeat(5, 1fr); gap:10px; align-items:stretch; }
    .brand-two-grid { display:grid; grid-template-columns: 1fr 1fr; gap:14px; }
    .brand-diag-grid { display:grid; grid-template-columns: .92fr 1.2fr; gap:14px; align-items:stretch; }
    .brand-gauge-wrap { display:grid; grid-template-columns: 1fr 1fr; gap:18px; align-items:center; }
    .brand-gauge { width:190px; height:95px; border-radius:190px 190px 0 0; background:conic-gradient(from 180deg, #2E974B 0deg, #A6C50F 115deg, #E6E9EF 116deg, #E6E9EF 180deg); margin:8px auto 0 auto; position:relative; overflow:hidden; }
    .brand-gauge:after { content:''; position:absolute; width:128px; height:64px; border-radius:128px 128px 0 0; background:white; left:31px; bottom:0; }
    .brand-gauge-number { text-align:center; margin-top:-50px; position:relative; z-index:3; font-size:2rem; font-weight:950; color:#071E49; }
    .brand-strategy-name { color:#0B4B93; font-size:1.35rem; font-weight:950; text-align:center; margin:14px 0; }
    .brand-analysis-box { background:#EEF6FF; border-radius:12px; padding:13px 15px; color:#344054; font-size:.86rem; line-height:1.45; margin-top:12px; }
    .brand-funnel-grid { display:grid; grid-template-columns: .95fr 1.35fr; gap:16px; align-items:center; }
    .brand-funnel-visual { display:flex; flex-direction:column; align-items:center; gap:5px; }
    .brand-funnel-shape { height:54px; color:white; font-weight:950; display:flex; align-items:center; justify-content:center; clip-path: polygon(0 0, 100% 0, 86% 100%, 14% 100%); }
    .brand-funnel-table { width:100%; border-collapse:separate; border-spacing:0 5px; font-size:.86rem; }
    .brand-funnel-table td { padding:8px; background:#F7FAFD; font-weight:800; color:#1D2738; }
    .brand-funnel-table td:nth-child(3), .brand-funnel-table td:nth-child(4) { text-align:center; font-size:1.08rem; font-weight:950; }
    .brand-note { background:#EEF6FF; border-radius:12px; padding:10px 12px; color:#173B66; font-size:.84rem; font-weight:750; margin-top:10px; }
    @media (max-width: 1150px) { .brand-summary-grid, .brand-two-grid, .brand-diag-grid, .brand-funnel-grid { grid-template-columns:1fr; } }
    </style>
    """, unsafe_allow_html=True)

    research = state.get("last_research") or {}
    truth_rows = state.get("last_truth") or []
    row = _brand_team_row(state, team)
    if not row:
        st.info("No hay datos suficientes para construir el informe de marca.")
        return
    history_rows = _brand_history_rows(state, team)
    closed_round = state["history"][-1].get("round") if state.get("history") else state.get("round_n", "-")
    _render_brand_header(closed_round, team)

    awareness = float(row.get("awareness_true", 0.0))
    satisfaction = _brand_satisfaction_score(row)
    retention = float(row.get("retention_rate", 0.0))
    coherence = max(0.0, min(1.0, .55 + float(row.get("strategy_coherence", 0.0))))
    share = float(row.get("share", 0.0))
    d_aw = _brand_delta(history_rows, "awareness_true", 100)
    d_sat = None
    if len(history_rows) >= 2:
        d_sat = _brand_satisfaction_score(history_rows[-1]) - _brand_satisfaction_score(history_rows[-2])
    d_ret = _brand_delta(history_rows, "retention_rate", 100)
    d_coh = _brand_delta(history_rows, "strategy_coherence", 100)
    d_share = _brand_delta(history_rows, "share", 100)

    st.markdown('<div class="report-card"><div class="brand-summary-grid"><div><div class="report-section-title">1. RESUMEN EJECUTIVO</div>', unsafe_allow_html=True)
    summary_text = f"Tu marca mantiene una cuota del {share*100:.1f}% y un conocimiento del {awareness*100:.1f}%. La satisfacción estimada es {satisfaction:.1f}/10 y la retención se sitúa en {retention*100:.1f}%. El informe analiza si el precio, la calidad y la comunicación sostienen tu posicionamiento."
    st.markdown(f'<div style="font-size:.90rem; line-height:1.55; color:#1D2738; font-weight:650;">{_html_escape(summary_text)}</div></div>', unsafe_allow_html=True)
    kcols = st.columns(5)
    with kcols[0]: _render_brand_kpi("Conocimiento", "📣", f"{awareness*100:.0f}%", f"{'▲' if (d_aw or 0)>=0 else '▼'} {abs(d_aw):.1f} p.p." if d_aw is not None else "—", "good" if (d_aw or 0) >= 0 else "bad")
    with kcols[1]: _render_brand_kpi("Satisfacción", "♡", f"{satisfaction:.1f} / 10", f"{'▲' if (d_sat or 0)>=0 else '▼'} {abs(d_sat):.1f}" if d_sat is not None else "—", "good" if (d_sat or 0) >= 0 else "bad")
    with kcols[2]: _render_brand_kpi("Retención", "↻", f"{retention*100:.0f}%", f"{'▲' if (d_ret or 0)>=0 else '▼'} {abs(d_ret):.1f} p.p." if d_ret is not None else "—", "good" if (d_ret or 0) >= 0 else "bad")
    with kcols[3]: _render_brand_kpi("Coherencia estratégica", "🎯", f"{coherence*100:.0f}%", f"{'▲' if (d_coh or 0)>=0 else '▼'} {abs(d_coh):.1f} p.p." if d_coh is not None else "—", "good" if (d_coh or 0) >= 0 else "bad")
    with kcols[4]: _render_brand_kpi("Cuota de mercado", "◔", f"{share*100:.1f}%", f"{'▲' if (d_share or 0)>=0 else '▼'} {abs(d_share):.1f} p.p." if d_share is not None else "—", "good" if (d_share or 0) >= 0 else "bad")
    st.markdown('</div><div class="report-muted" style="text-align:center; margin-top:6px;">(Entre paréntesis: evolución vs. ronda anterior)</div></div>', unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="report-card"><div class="report-section-title">2. POSICIONAMIENTO DE MARCA</div><div class="report-muted">Mapa precio percibido vs. calidad percibida</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1.8, .8])
        with c1:
            st.plotly_chart(_build_brand_positioning_chart(state, team), use_container_width=True, config={"displayModeBar": False})
        with c2:
            st.markdown('<div class="brand-note"><b>¿Qué significa?</b><br><br>La posición resume si el precio está respaldado por la calidad percibida. Cuanto más arriba, mayor calidad; cuanto más a la derecha, mayor precio.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="report-card"><div class="report-section-title">3. SALUD DE MARCA (EVOLUCIÓN)</div>', unsafe_allow_html=True)
        st.plotly_chart(_build_brand_health_chart(state, team), use_container_width=True, config={"displayModeBar": False})
        st.markdown('<div class="brand-note">El seguimiento conjunto de conocimiento, satisfacción y retención permite detectar si la marca crece de forma sana o solo por captación táctica.</div></div>', unsafe_allow_html=True)

    left2, right2 = st.columns([.95, 1.25])
    strategy_name, strategy_desc = _brand_strategy_type(row, research, team)
    with left2:
        st.markdown(f"""
        <div class="report-card">
          <div class="report-section-title">4. DIAGNÓSTICO ESTRATÉGICO</div>
          <div class="brand-diag-grid">
            <div><div style="font-weight:950; text-align:center; color:#1D2738;">COHERENCIA ESTRATÉGICA</div><div class="brand-gauge"></div><div class="brand-gauge-number">{coherence*100:.0f}%</div><div style="text-align:center; color:#53657D; font-size:.80rem; font-weight:800;">Nivel de coherencia</div></div>
            <div><div style="font-weight:950; color:#1D2738; text-align:center;">TIPO DE ESTRATEGIA ACTUAL</div><div class="brand-strategy-name">{_html_escape(strategy_name)}</div><div style="text-align:center; color:#344054; line-height:1.45;">{_html_escape(strategy_desc)}</div></div>
          </div>
          <div class="brand-analysis-box"><b>ANÁLISIS</b><br>La lectura estratégica combina precio, producto, promoción, distribución y comunicación. Una marca fuerte necesita coherencia entre lo que promete y lo que entrega al mercado.</div>
        </div>
        """, unsafe_allow_html=True)
    with right2:
        funnel = _brand_funnel_values(row, research, team, truth_rows)
        rows_html = ""
        colors_f = {"Conocimiento":"#0B4B93", "Consideración":"#2E974B", "Compra":"#F59E0B", "Retención":"#8755D9"}
        for name, (mine, avgv) in funnel.items():
            desc = {"Conocimiento":"Personas que conocen tu marca", "Consideración":"Personas que considerarían comprar", "Compra":"Personas que compran tu marca", "Retención":"Clientes que repiten compra"}.get(name, "")
            rows_html += f"<tr><td style='color:{colors_f[name]}; font-weight:950;'>{name}<br><span style='font-size:.70rem;color:#53657D;'>{desc}</span></td><td></td><td>{mine*100:.0f}%</td><td>{avgv*100:.0f}%</td></tr>"
        st.markdown(f"""
        <div class="report-card">
          <div class="report-section-title">5. FUNNEL DE MARCA</div>
          <div class="brand-funnel-grid">
            <div class="brand-funnel-visual">
              <div class="brand-funnel-shape" style="background:#0B4B93; width:100%;">CONOCIMIENTO</div>
              <div class="brand-funnel-shape" style="background:#2E974B; width:82%;">CONSIDERACIÓN</div>
              <div class="brand-funnel-shape" style="background:#F59E0B; width:64%;">COMPRA</div>
              <div class="brand-funnel-shape" style="background:#8755D9; width:46%;">RETENCIÓN</div>
            </div>
            <table class="brand-funnel-table"><thead><tr><td></td><td></td><td>TU MARCA</td><td>VS. MEDIA</td></tr></thead><tbody>{rows_html}</tbody></table>
          </div>
          <div class="brand-note">Tu funnel resume dónde la marca es fuerte y dónde pierde eficiencia. La oportunidad suele estar en la fase con mayor distancia frente a la media.</div>
        </div>
        """, unsafe_allow_html=True)

    good, bad, opp = _brand_three_boxes(row, research, team, truth_rows)
    st.markdown('<div class="report-card"><div class="report-section-title">6. CONCLUSIONES Y RECOMENDACIONES CLAVE</div><div class="conclusion-grid">', unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    with b1:
        _render_brand_conclusion("Lo estás haciendo bien", good, "#2E974B", "Sigue reforzando la calidad y la experiencia para mantener ventaja competitiva.", "footer-good", "✅")
    with b2:
        _render_brand_conclusion("Lo estás haciendo mal", bad, "#F59E0B", "Revisa tu propuesta de valor y ajusta las palancas menos alineadas.", "footer-bad", "⚠️")
    with b3:
        _render_brand_conclusion("Oportunidades", opp, "#0B63B6", "Enfócate en estos puntos para acelerar tu crecimiento.", "footer-opp", "⭐")
    st.markdown('</div></div><div class="market-reminder">💡 RECUERDA: Las decisiones consistentes hoy construyen marcas fuertes mañana.</div>', unsafe_allow_html=True)
def render_team_reports(team, teams, state, current_decisions):
    """
    Pantalla de informes con tarjetas clicables:
    - Las 3 cajas superiores funcionan como selector.
    - Si el informe está comprado, al pinchar se muestra ese informe.
    - Si no está comprado, se informa al alumno sin mostrar contenido bloqueado.
    - Se elimina el selector/radio antiguo y no se muestran todos los informes a la vez.
    """
    inject_reports_pro_styles()
    st.markdown("## Informes")

    st.markdown(
        """
        <style>
        .report-click-helper {
            background:#EAF4FF;
            border:1px solid #DDEBFA;
            border-radius:14px;
            padding:12px 16px;
            color:#0A3472;
            font-weight:850;
            margin:4px 0 14px 0;
        }
        .report-selector-card {
            min-height:150px;
            transition:all .15s ease;
        }
        .report-selector-card.report-active {
            border:2px solid #0F6BFF !important;
            box-shadow:0 12px 30px rgba(15,107,255,.16) !important;
            transform:translateY(-1px);
        }
        .report-selector-card.report-locked {
            opacity:.78;
        }
        .report-card-selected-pill {
            display:inline-flex;
            align-items:center;
            gap:6px;
            margin-top:8px;
            padding:6px 10px;
            border-radius:999px;
            background:#EAF2FF;
            color:#0F6BFF;
            font-size:.76rem;
            font-weight:950;
        }
        div[data-testid="stButton"] > button {
            border-radius:13px !important;
            min-height:42px !important;
            font-weight:900 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    last_research = state.get("last_research")
    last_truth = state.get("last_truth")
    if not last_truth:
        st.info("Los informes aparecerán cuando cierres la primera ronda.")
        return

    # Leer los informes comprados en la última ronda cerrada, no en la ronda actual abierta.
    closed_round = None
    if state.get("history"):
        closed_round = state["history"][-1].get("round")
    closed_decisions = get_all_decisions(state["game_id"], closed_round) if closed_round is not None else current_decisions
    team_entry = closed_decisions.get(team)
    bought = team_entry["decision"].get("research", {}) if team_entry else {}

    report_options = [
        {
            "id": "segments",
            "label": "Mercado",
            "title": "Informe de Mercado",
            "subtitle": "Situación y oportunidades",
            "icon": "📈",
            "bought_key": "segments",
            "button": "Ver informe de mercado",
        },
        {
            "id": "competition",
            "label": "Competitivo",
            "title": "Informe Competitivo",
            "subtitle": "Competencia y posicionamiento",
            "icon": "🏆",
            "bought_key": "competition",
            "button": "Ver informe competitivo",
        },
        {
            "id": "brand_product",
            "label": "Marca y producto",
            "title": "Informe de Marca",
            "subtitle": "Análisis completo de tu marca",
            "icon": "🏷️",
            "bought_key": "brand_product",
            "button": "Ver informe de marca",
        },
    ]

    session_key = f"selected_report_{state.get('game_id')}_{team}"

    if session_key not in st.session_state:
        first_bought = next((opt["id"] for opt in report_options if bought.get(opt["bought_key"])), "segments")
        st.session_state[session_key] = first_bought

    st.markdown(
        "<div class='report-click-helper'>ⓘ Haz clic en una tarjeta para abrir el informe comprado. Si no lo compraste, verás un aviso.</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for col, opt in zip(cols, report_options):
        with col:
            is_bought = bool(bought.get(opt["bought_key"]))
            is_active = st.session_state.get(session_key) == opt["id"]
            status = "✅ Comprado" if is_bought else "🔒 No comprado"
            status_color = "#168A4A" if is_bought else "#9AA4B2"
            active_cls = " report-active" if is_active else ""
            locked_cls = " report-locked" if not is_bought else ""
            selected_pill = "<div class='report-card-selected-pill'>● Seleccionado</div>" if is_active else ""
            st.markdown(
                (
                    f"<div class='report-selector-card{active_cls}{locked_cls}'>"
                    f"<div style='font-size:1.35rem'>{opt['icon']}</div>"
                    f"<div style='font-weight:950;color:#071E49'>{_html_escape(opt['title'])}</div>"
                    f"<div class='report-muted'>{_html_escape(opt['subtitle'])}</div>"
                    f"<div style='margin-top:8px;font-weight:900;color:{status_color}'>{_html_escape(status)}</div>"
                    f"{selected_pill}"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            if st.button(opt["button"], key=f"btn_report_{state.get('game_id')}_{team}_{opt['id']}", use_container_width=True):
                st.session_state[session_key] = opt["id"]
                st.rerun()

    selected_report = st.session_state.get(session_key, "segments")
    selected = next((opt for opt in report_options if opt["id"] == selected_report), report_options[0])

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    if selected_report == "segments":
        if bought.get("segments") and last_research:
            render_market_report_dashboard(team, state)
        else:
            st.info("No compraste el informe de mercado en la última ronda cerrada.")

    elif selected_report == "competition":
        if bought.get("competition") and last_truth:
            render_competitive_report_dashboard_visual(team, state)
        else:
            st.info("No compraste el informe competitivo en la última ronda cerrada.")

    elif selected_report == "brand_product":
        if bought.get("brand_product") and last_research:
            render_brand_report_dashboard_visual(team, state)
        else:
            st.info("No compraste el informe de marca y producto en la última ronda cerrada.")



# =========================================================
# APP
# =========================================================
st.markdown("""<style>.main-title-hidden{display:none;}</style><div class="main-title-hidden">Simulador de Mercado Multiusuario</div>""", unsafe_allow_html=True)

state = load_current_state()
if state is None:
    st.error("No hay ninguna partida disponible.")
    st.stop()

migrated_team_budgets = backfill_team_budgets_from_history(state)
if migrated_team_budgets != (state.get("team_budgets", {}) or {}):
    update_game_state(state["game_id"], team_budgets=migrated_team_budgets)
    state = load_current_state()

game_id = state["game_id"]
game_name = state["game_name"]
teams = state["teams"]
engine = MarketEngine(teams)
engine.set_state(state["engine_state"])
round_n = state["round_n"]
budget_per_team = state["budget_per_team"]
round_status = state["round_status"]
all_decisions = get_all_decisions(game_id, round_n)
all_games = list_games()

team_section = None

with st.sidebar:
    render_sidebar_brand()

    team_section_options = {
        "⌂  Resumen": "Resumen",
        "◎  Mercado": "Mercado",
        "◫  Presupuesto": "Presupuesto",
        "◉  Mi decisión": "Mi decisión",
        "☷  Informes": "Informes",
    }

    if st.session_state["role"] == "team" and st.session_state["team_name"]:
        st.markdown('<div class="sim-sidebar-section-label">Navegación</div>', unsafe_allow_html=True)
        current_plain_section = st.session_state.get("team_section", "Resumen")
        icon_labels = list(team_section_options.keys())
        current_icon_index = next(
            (i for i, label in enumerate(icon_labels) if team_section_options[label] == current_plain_section),
            0,
        )
        selected_section_icon = st.radio(
            "Sección",
            icon_labels,
            index=current_icon_index,
            key="team_section_icon_radio",
        )
        team_section = team_section_options[selected_section_icon]
        st.session_state["team_section"] = team_section
        st.divider()

    st.markdown('<div class="sim-sidebar-section-label">Partida activa</div>', unsafe_allow_html=True)
    game_labels = [
        f"{g['game_name']} | R{g['round_n']} | {'abierta' if g['round_status'] == 'open' else 'cerrada'}"
        for g in all_games
    ]
    game_ids = [g["game_id"] for g in all_games]
    current_index = game_ids.index(game_id) if game_id in game_ids else 0

    selected_label = st.selectbox("Selecciona partida", game_labels, index=current_index)
    selected_game_id = game_ids[game_labels.index(selected_label)]

    if selected_game_id != game_id:
        switch_game(selected_game_id)
        st.rerun()

    st.markdown(
        f"""
        <div class="sim-sidebar-mini">
            ID: {game_id}<br>
            Ronda actual: {round_n} | Estado: {'abierta' if round_status == 'open' else 'cerrada'}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown('<div class="sim-sidebar-section-label">Acceso</div>', unsafe_allow_html=True)

    role_options = {"♟  Equipo": "Equipo", "▥  Profesor": "Profesor"}
    selected_role_icon = st.radio(
        "Rol",
        list(role_options.keys()),
        index=0 if st.session_state["role"] != "professor" else 1,
        key="role_icon_radio",
    )
    selected_role = role_options[selected_role_icon]

    if selected_role == "Equipo":
        team_name = st.selectbox(
            "Equipo",
            teams,
            index=teams.index(st.session_state["team_name"]) if st.session_state["team_name"] in teams else 0,
        )
        team_password = st.text_input("Clave del equipo", type="password")
        if st.button("Entrar como equipo"):
            if verify_team_password(game_id, team_name, team_password):
                st.session_state["role"] = "team"
                st.session_state["team_name"] = team_name
                st.success(f"Acceso concedido a {team_name}")
                st.rerun()
            else:
                st.error("Clave incorrecta")
    else:
        professor_password = st.text_input("Clave del profesor", type="password")
        if st.button("Entrar como profesor"):
            if verify_professor_password(game_id, professor_password):
                st.session_state["role"] = "professor"
                st.session_state["professor_ok"] = True
                st.success("Acceso de profesor concedido")
                st.rerun()
            else:
                st.error("Clave incorrecta")

    if st.session_state["role"]:
        st.divider()
        st.button("⇱  Cerrar sesión", on_click=logout, use_container_width=True)

round_status_label = "abierta" if round_status == "open" else "cerrada"
st.markdown(f"<div class=\"sim-app-topline\"><span>Partida: <b>{_html_escape(game_name)}</b></span><span>Ronda {round_n}</span><span>{round_status_label}</span></div>", unsafe_allow_html=True)


# =========================================================
# VISTA EQUIPO
# =========================================================
if st.session_state["role"] == "team" and st.session_state["team_name"]:
    team = st.session_state["team_name"]
    current_team_budget = get_team_budget_for_round(state, team)
    st.markdown(f"<div class=\"sim-view-caption\">Vista del equipo: <b>{_html_escape(team)}</b></div>", unsafe_allow_html=True)

    existing_entry = get_decision(game_id, team, round_n)
    if existing_entry:
        st.caption(f"Último envío: {existing_entry['submitted_at']}")
        if existing_entry["reviewed"]:
            st.success("El profesor ya ha revisado esta decisión.")
        if existing_entry["review_notes"]:
            st.info(f"Notas del profesor: {existing_entry['review_notes']}")

    if team_section == "Resumen":
        render_team_summary(team, state, current_team_budget, round_n)

    elif team_section == "Mercado":
        render_team_market(team, state)

    elif team_section == "Mi decisión":
        payload, estimated_budget_remaining = build_decision_payload(
            game_id, team, teams, engine, current_team_budget, round_n, state
        )

        
        if round_status != "open":
            st.warning("La ronda está cerrada. Ya no se pueden modificar decisiones.")
            st.button("Guardar / enviar decisión", disabled=True, use_container_width=True)
        elif estimated_budget_remaining < 0:
            st.error("No puedes enviar la decisión porque el presupuesto estimado supera el límite disponible.")
            st.button("Guardar / enviar decisión", disabled=True, use_container_width=True)
        else:
            
            if st.button("Guardar / enviar decisión", use_container_width=True):
                upsert_decision(game_id, team, round_n, payload)
                st.success("Decisión guardada correctamente.")
                st.rerun()

    elif team_section == "Presupuesto":
        render_team_budget(team, teams, engine, state, current_team_budget, round_n, game_id)

    elif team_section == "Informes":
        render_team_reports(team, teams, state, all_decisions)


# =========================================================
# VISTA PROFESOR
# =========================================================
elif st.session_state["role"] == "professor" and st.session_state["professor_ok"]:
    st.subheader("Panel del profesor")

    with st.expander("Gestión de partidas", expanded=True):
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("#### Crear nueva partida")
            new_game_name = st.text_input("Nombre de la nueva partida", value="Nueva partida")
            num_teams_new = st.selectbox("Número de equipos", list(range(3, 9)), index=1, key="new_num_teams")
            default_names_new = ", ".join([f"Equipo {chr(65+i)}" for i in range(num_teams_new)])
            new_team_names = st.text_input(
                "Nombres de equipos separados por comas",
                value=default_names_new,
                key="new_team_names",
            )
            new_budget = st.number_input(
                "Presupuesto por equipo y ronda",
                min_value=50000,
                max_value=500000,
                value=default_budget_by_num_teams(num_teams_new),
                step=5000,
                key="new_budget",
            )
            new_prof_password = st.text_input(
                "Clave del profesor para la nueva partida",
                type="password",
                value="admin123",
                key="new_prof_password",
            )
            new_team_password = st.text_input(
                "Clave inicial para todos los equipos",
                type="password",
                value="1234",
                key="new_team_password",
            )

            if st.button("Crear partida nueva"):
                clean_teams = [x.strip() for x in new_team_names.split(",") if x.strip()]
                if not new_game_name.strip():
                    st.error("Escribe un nombre para la partida.")
                elif len(clean_teams) < 3:
                    st.error("Debe haber al menos 3 equipos.")
                else:
                    try:
                        new_engine = MarketEngine(clean_teams)
                        team_passwords = {team: (new_team_password or "1234") for team in clean_teams}
                        new_game_id = create_game(
                            game_name=new_game_name.strip(),
                            teams=clean_teams,
                            team_passwords=team_passwords,
                            budget_per_team=int(new_budget),
                            round_n=1,
                            round_status="open",
                            engine_state=new_engine.get_state(),
                            history=[],
                            last_truth=None,
                            last_research=None,
                            last_event=None,
                            team_budgets={team: int(new_budget) for team in clean_teams},
                            event_this_round=False,
                            professor_password=new_prof_password or "admin123",
                        )
                        switch_game(new_game_id)
                        st.success("Partida creada correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo crear la partida: {e}")

        with col_g2:
            st.markdown("#### Operaciones sobre la partida actual")
            rename_value = st.text_input("Nuevo nombre de la partida actual", value=game_name, key="rename_game")
            if st.button("Renombrar partida actual"):
                try:
                    rename_game(game_id, rename_value.strip())
                    st.success("Partida renombrada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo renombrar: {e}")

            duplicate_name = st.text_input(
                "Nombre de la copia",
                value=f"{game_name} (copia)",
                key="duplicate_game_name",
            )
            if st.button("Duplicar partida actual"):
                try:
                    new_copy_id = duplicate_game(game_id, duplicate_name.strip())
                    if new_copy_id is not None:
                        switch_game(new_copy_id)
                        st.success("Partida duplicada.")
                        st.rerun()
                    else:
                        st.error("No se pudo duplicar la partida.")
                except Exception as e:
                    st.error(f"No se pudo duplicar: {e}")

            st.warning("Eliminar una partida borra también sus claves, decisiones e histórico.")
            confirm_delete = st.checkbox("Confirmo que quiero borrar esta partida", key="confirm_delete_game")
            if st.button("Borrar partida actual", disabled=not confirm_delete):
                try:
                    delete_game(game_id)
                    remaining_id = get_latest_game_id()
                    if remaining_id is not None:
                        switch_game(remaining_id)
                    else:
                        st.session_state["current_game_id"] = None
                        st.session_state["role"] = None
                        st.session_state["team_name"] = None
                        st.session_state["professor_ok"] = False
                    st.success("Partida borrada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo borrar la partida: {e}")

    with st.expander("Configuración de la partida actual", expanded=False):
        num_teams = st.selectbox("Número de equipos", list(range(3, 9)), index=max(0, len(teams) - 3), key="cfg_num_teams")
        default_names = ", ".join([f"Equipo {chr(65+i)}" for i in range(num_teams)])
        team_names = st.text_input(
            "Nombres de equipos separados por comas",
            value=", ".join(teams) if len(teams) == num_teams else default_names,
            key="cfg_team_names",
        )
        budget_per_team_input = st.number_input(
            "Presupuesto por equipo y ronda",
            min_value=50000,
            max_value=500000,
            value=int(budget_per_team),
            step=5000,
            key="cfg_budget",
        )
        professor_new_password = st.text_input(
            "Nueva clave del profesor (opcional)",
            type="password",
            key="cfg_prof_pwd",
        )
        default_password = "1234"
        st.caption("Si reinicias esta partida, puedes poner una misma clave inicial para todos los equipos.")
        team_default_password = st.text_input(
            "Clave inicial para todos los equipos",
            type="password",
            value=default_password,
            key="cfg_team_pwd",
        )

        if st.button("Reiniciar esta partida desde cero"):
            new_teams = [x.strip() for x in team_names.split(",") if x.strip()]
            if len(new_teams) < 3:
                st.error("Debe haber al menos 3 equipos.")
            else:
                try:
                    new_engine = MarketEngine(new_teams)
                    team_passwords = {team: team_default_password or default_password for team in new_teams}
                    current_prof_password = professor_new_password or "admin123"

                    delete_game(game_id)
                    recreated_game_id = create_game(
                        game_name=game_name,
                        teams=new_teams,
                        team_passwords=team_passwords,
                        budget_per_team=int(budget_per_team_input),
                        round_n=1,
                        round_status="open",
                        engine_state=new_engine.get_state(),
                        history=[],
                        last_truth=None,
                        last_research=None,
                        last_event=None,
                        team_budgets={team: int(budget_per_team_input) for team in new_teams},
                        event_this_round=False,
                        professor_password=current_prof_password,
                    )
                    switch_game(recreated_game_id)
                    st.success("Partida reiniciada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo reiniciar la partida: {e}")

        if professor_new_password and st.button("Cambiar solo la clave del profesor"):
            set_professor_password(game_id, professor_new_password)
            st.success("Clave del profesor actualizada")

    with st.expander("Claves de equipos", expanded=False):
        for team in teams:
            new_team_password = st.text_input(
                f"Nueva clave para {team}",
                type="password",
                key=f"pwd_{game_id}_{team}",
            )
            if st.button(f"Guardar clave de {team}", key=f"save_pwd_{game_id}_{team}"):
                if new_team_password:
                    update_team_password(game_id, team, new_team_password)
                    st.success(f"Clave actualizada para {team}")
                else:
                    st.warning("Escribe una clave antes de guardar.")

    st.markdown("### Estado de entrega")
    status_rows = []
    for t in teams:
        entry = all_decisions.get(t)
        status_rows.append(
            {
                "Equipo": t,
                "Entregado": "Sí" if entry else "No",
                "Revisado": "Sí" if entry and entry["reviewed"] else "No",
                "Último envío": entry["submitted_at"] if entry else "-",
                "Notas": entry["review_notes"] if entry else "",
            }
        )
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)

    st.markdown("### Revisar decisiones")
    selected_team_review = st.selectbox("Equipo a revisar", teams)
    selected_entry = all_decisions.get(selected_team_review)
    if selected_entry:
        decision = selected_entry["decision"]
        review_df = pd.DataFrame([
            ("Precio", decision.get("price")),
            ("Promoción", decision.get("promo", 0) * 100),
            ("Distribución", decision.get("distribution", 0) * 100),
            ("Rendimiento", decision.get("product_perf", 0) * 100),
            ("Diseño", decision.get("product_design", 0) * 100),
            ("Fiabilidad", decision.get("product_reliability", 0) * 100),
            ("Comunicación total", decision.get("comm_total", 0)),
            ("Coste investigación", decision.get("research_cost", 0)),
            ("Presupuesto estimado consumido", decision.get("budget_estimated_used", 0)),
            ("Presupuesto estimado restante", decision.get("budget_estimated_remaining", 0)),
        ], columns=["Variable", "Valor"])
        st.table(review_df)

        note = st.text_area(
            "Notas para el equipo",
            value=selected_entry["review_notes"],
            key=f"notes_{game_id}_{selected_team_review}",
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Marcar como revisada"):
                set_review_status(game_id, selected_team_review, round_n, True, note)
                st.success("Decisión revisada")
                st.rerun()
        with col_b:
            if st.button("Dejar pendiente"):
                set_review_status(game_id, selected_team_review, round_n, False, note)
                st.info("Decisión marcada como pendiente")
                st.rerun()
    else:
        st.info("Ese equipo aún no ha enviado decisión.")

    st.markdown("### Evento aleatorio")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Habrá evento aleatorio"):
            update_game_state(game_id, event_this_round=True)
            st.success("Esta ronda tendrá evento aleatorio")
            st.rerun()
    with col2:
        if st.button("No habrá evento"):
            update_game_state(game_id, event_this_round=False)
            st.info("Esta ronda no tendrá evento")
            st.rerun()

    pending = [t for t in teams if t not in all_decisions]
    not_reviewed = [t for t in teams if t in all_decisions and not all_decisions[t]["reviewed"]]

    st.markdown("### Control de ronda")
    st.info(f"Estado actual de la ronda: **{'abierta' if round_status == 'open' else 'cerrada'}**")
    if pending:
        st.warning("Faltan decisiones de: " + ", ".join(pending))
    if not_reviewed:
        st.warning("Aún no revisadas: " + ", ".join(not_reviewed))

    can_close = (not pending) and (round_status == "open")
    close_help = "Puedes cerrar la ronda cuando todos los equipos hayan entregado." if can_close else "No se puede cerrar todavía porque faltan decisiones o la ronda ya está cerrada."
    st.caption(close_help)
    if st.button("Cerrar ronda", disabled=not can_close, use_container_width=True):
        state = load_game_state(game_id)
        engine = MarketEngine(state["teams"])
        engine.set_state(state["engine_state"])
        decisions_payload: Dict[str, dict] = {team: all_decisions[team]["decision"] for team in state["teams"]}

        if state["event_this_round"]:
            event = engine.random_event()
        else:
            engine._reset_round_modifiers()
            event = None

        truth, research, _ = engine.step(decisions_payload)
        history = state["history"] + [{
            "round": state["round_n"],
            "truth": truth,
            "research": research,
            "event": event,
        }]

        next_team_budgets = {}
        for row in truth:
            next_team_budgets[row["team"]] = compute_next_team_budget(
                base_budget=state["budget_per_team"],
                budget_remaining_actual=row.get("budget_remaining_actual", 0.0),
                profit=row.get("profit", 0.0),
            )

        update_game_state(
            game_id,
            engine_state=engine.get_state(),
            history=history,
            last_truth=truth,
            last_research=research,
            last_event=event,
            team_budgets=next_team_budgets,
            round_status="closed",
            event_this_round=False,
        )
        st.success("Ronda cerrada correctamente")
        st.rerun()

    can_open_next = round_status == "closed"
    st.caption("La siguiente ronda solo se puede abrir cuando la ronda actual ya está cerrada.")
    if st.button("Abrir siguiente ronda", disabled=not can_open_next, use_container_width=True):
        update_game_state(
            game_id,
            round_n=round_n + 1,
            round_status="open",
            event_this_round=False,
        )
        st.success("Siguiente ronda abierta")
        st.rerun()

    state = load_game_state(game_id)
    if state["last_truth"]:
        st.markdown("### Resultados de la última ronda cerrada")
        df = pd.DataFrame(state["last_truth"]).sort_values("profit", ascending=False)
        df["share"] = (df["share"] * 100).round(1)
        df["retention_rate"] = (df["retention_rate"] * 100).round(1)
        df["awareness_true"] = (df["awareness_true"] * 100).round(1)
        df["quality"] = (df["quality"] * 100).round(1)

        cols_to_show = ["team", "price", "units", "share", "profit", "awareness_true", "quality", "retention_rate"]
        if "research_cost" in df.columns:
            cols_to_show.append("research_cost")

        show_df = df[cols_to_show].rename(columns={
            "team": "Equipo",
            "price": "Precio",
            "units": "Ventas",
            "share": "Cuota (%)",
            "profit": "Beneficio",
            "awareness_true": "Conocimiento (%)",
            "quality": "Producto (%)",
            "retention_rate": "Retención (%)",
            "research_cost": "Investigación (€)",
        })
        st.dataframe(show_df, use_container_width=True, hide_index=True)

        if st.button("Generar PDFs"):
            folder = f"outputs/game_{game_id}_ronda_{round_n}"
            os.makedirs(folder, exist_ok=True)
            closed_round = state["history"][-1]["round"] if state["history"] else round_n
            closed_decisions = get_all_decisions(game_id, closed_round)

            for t in teams:
                team_truth = next((row for row in state["last_truth"] if row["team"] == t), None)
                team_decision = closed_decisions[t]["decision"] if t in closed_decisions else {}
                research_flags = team_decision.get("research", {})

                if research_flags.get("segments"):
                    make_segments_pdf(
                        os.path.join(folder, f"{t}_segmentos.pdf"),
                        closed_round,
                        t,
                        state["last_event"],
                        state["last_research"],
                        team_decision,
                        team_truth,
                    )

                if research_flags.get("competition"):
                    make_competition_pdf(
                        os.path.join(folder, f"{t}_competitivo.pdf"),
                        closed_round,
                        t,
                        state["last_event"],
                        state["last_research"],
                        state["last_truth"],
                        team_decision,
                        team_truth,
                    )

                if research_flags.get("brand_product"):
                    make_brand_product_pdf(
                        os.path.join(folder, f"{t}_marca_producto.pdf"),
                        closed_round,
                        t,
                        state["last_event"],
                        state["last_research"],
                        team_decision,
                        team_truth,
                    )

            make_facilitator_pdf(
                os.path.join(folder, "facilitador.pdf"),
                closed_round,
                state["last_event"],
                state["last_truth"],
                state["history"],
                state["last_research"],
                {t: closed_decisions[t]["decision"] for t in closed_decisions},
            )

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for file in os.listdir(folder):
                    file_path = os.path.join(folder, file)
                    zf.write(file_path, arcname=file)
            zip_buffer.seek(0)

            safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in game_name)
            st.download_button(
                label="Descargar PDFs (ZIP)",
                data=zip_buffer,
                file_name=f"{safe_name}_ronda_{closed_round}_pdfs.zip",
                mime="application/zip",
            )

# =========================================================
# SIN LOGIN
# =========================================================
else:
    st.info("Accede desde la barra lateral como equipo o como profesor.")
    st.markdown(
        """
        **Claves iniciales por defecto al crear una partida nueva:**
        - Profesor: `admin123`
        - Equipos: `1234`
        """
    )
