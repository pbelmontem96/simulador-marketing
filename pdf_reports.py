import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4


# -------------------------------------------------
# UTILIDADES GENERALES
# -------------------------------------------------

def _fmt_int(v):
    try:
        return f"{int(round(float(v))):,}".replace(",", ".")
    except Exception:
        return str(v)


def _fmt_float(v, nd=1):
    try:
        return f"{float(v):.{nd}f}"
    except Exception:
        return str(v)


def _fmt_pct(v, nd=1):
    try:
        return f"{float(v) * 100:.{nd}f}%"
    except Exception:
        return str(v)


def _safe_get_comm_total(decision):
    if "comm_total" in decision:
        return float(decision.get("comm_total", 0.0))
    return float(decision.get("ad_spend", 0.0))


def _safe_get_comm_mix(decision):
    if "comm_mix" in decision and isinstance(decision["comm_mix"], dict):
        mix = decision["comm_mix"]
        trad = float(mix.get("trad", 0.0))
        online = float(mix.get("online", 0.0))
        rrss = float(mix.get("rrss", 0.0))
        pr = float(mix.get("pr", 0.0))
        total = trad + online + rrss + pr
        if total <= 0:
            return {"trad": 0.25, "online": 0.25, "rrss": 0.25, "pr": 0.25}
        return {
            "trad": trad / total,
            "online": online / total,
            "rrss": rrss / total,
            "pr": pr / total
        }

    return {"trad": 0.25, "online": 0.25, "rrss": 0.25, "pr": 0.25}


def _safe_get_product_values(decision, team_truth=None):
    perf = None
    design = None
    reliability = None
    quality = None
    product_cost = None

    if isinstance(decision, dict):
        perf = decision.get("product_perf", perf)
        design = decision.get("product_design", design)
        reliability = decision.get("product_reliability", reliability)
        quality = decision.get("quality", quality)
        product_cost = decision.get("estimated_product_investment_cost", product_cost)
        if product_cost is None:
            product_cost = decision.get("estimated_quality_investment_cost", product_cost)

    if isinstance(team_truth, dict):
        perf = team_truth.get("product_perf", perf)
        design = team_truth.get("product_design", design)
        reliability = team_truth.get("product_reliability", reliability)
        quality = team_truth.get("quality", quality)
        product_cost = team_truth.get("product_investment_cost", product_cost)
        if product_cost is None:
            product_cost = team_truth.get("quality_investment_cost", product_cost)

    return {
        "product_perf": float(perf) if perf is not None else 0.0,
        "product_design": float(design) if design is not None else 0.0,
        "product_reliability": float(reliability) if reliability is not None else 0.0,
        "quality": float(quality) if quality is not None else 0.0,
        "product_cost": float(product_cost) if product_cost is not None else 0.0,
    }


def _get_estimated_awareness(research):
    if "estimated_awareness" in research:
        return research["estimated_awareness"]
    if "estimated_knowledge" in research:
        return research["estimated_knowledge"]
    return {}


def _get_comm_knowledge_effect(effects):
    if "awareness" in effects:
        return effects.get("awareness", 0)
    return effects.get("knowledge", 0)


def _split_text(text, max_chars=95):
    words = str(text).split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_wrapped_text(c, x, y, text, max_chars=95, line_gap=14, font_name="Helvetica", font_size=10):
    c.setFont(font_name, font_size)
    yy = y
    for line in _split_text(text, max_chars=max_chars):
        c.drawString(x, yy, line)
        yy -= line_gap
    return yy


# -------------------------------------------------
# DIBUJO BASE
# -------------------------------------------------

def _draw_title(c, title, subtitle=None):
    c.setFillColor(colors.HexColor("#16324F"))
    c.rect(0, PAGE_H - 85, PAGE_W, 85, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, PAGE_H - 45, title)

    if subtitle:
        c.setFont("Helvetica", 11)
        c.drawString(40, PAGE_H - 65, subtitle)


def _draw_section_title(c, text, y):
    c.setFillColor(colors.HexColor("#1F4E79"))
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, y, text)


def _draw_label_value_box(c, x, y, w, h, label, value, fill="#F3F6FA"):
    c.setFillColor(colors.HexColor(fill))
    c.roundRect(x, y - h, w, h, 8, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#4A4A4A"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 10, y - 18, label)

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    c.drawString(x + 10, y - 36, str(value))


def _draw_event_box(c, y, event_info):
    c.setFillColor(colors.HexColor("#FFF4D6"))
    c.roundRect(40, y - 70, PAGE_W - 80, 60, 10, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#6B4E00"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 25, "Evento de la ronda")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 11)

    if event_info:
        line1 = f"{event_info['title']}: {event_info['desc']}"
        c.drawString(50, y - 42, line1[:95])
        extra = event_info.get("extra", "")
        if extra:
            c.drawString(50, y - 56, f"Detalle: {extra}"[:95])
    else:
        c.drawString(50, y - 45, "No hubo evento en esta ronda.")


def _draw_insight_box(c, title, insights, y_top, height=None, fill="#EEF5FF"):
    insights = insights or ["Sin insights disponibles para esta ronda."]
    wrapped_lines = 0
    for insight in insights:
        wrapped_lines += max(1, len(_split_text(insight, max_chars=78)))

    if height is None:
        height = 38 + wrapped_lines * 14 + max(0, len(insights) - 1) * 4

    c.setFillColor(colors.HexColor(fill))
    c.roundRect(40, y_top - height, PAGE_W - 80, height, 10, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_top - 20, title)

    c.setFillColor(colors.black)
    y = y_top - 40
    for insight in insights:
        lines = _split_text(insight, max_chars=78)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(55, y, "•")
        c.setFont("Helvetica", 10)
        c.drawString(68, y, lines[0])
        y -= 14
        for line in lines[1:]:
            c.drawString(68, y, line)
            y -= 14
        y -= 4

    return y_top - height


def _draw_reports_bought_box(c, decision, y_top):
    research = decision.get("research", {})
    research_cost = float(decision.get("research_cost", 0.0))

    labels = []
    if research.get("segments"):
        labels.append("Segmentos")
    if research.get("competition"):
        labels.append("Competitivo")
    if research.get("brand_product"):
        labels.append("Marca + producto")

    text = ", ".join(labels) if labels else "Ninguno"

    c.setFillColor(colors.HexColor("#F4F7FB"))
    c.roundRect(40, y_top - 72, PAGE_W - 80, 60, 10, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y_top - 24, "Informes adquiridos")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(50, y_top - 42, f"Informes: {text}")
    c.drawString(50, y_top - 56, f"Coste de investigación: {_fmt_int(research_cost)} EUR")

    return y_top - 82


# -------------------------------------------------
# GRÁFICOS
# -------------------------------------------------

def _save_bar_chart(data_dict, title, xlabel, output_path):
    labels = list(data_dict.keys())
    values = list(data_dict.values())

    plt.figure(figsize=(8, 4.5))
    plt.bar(labels, values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("")
    plt.xticks(rotation=20)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _save_line_chart(df, title, ylabel, output_path):
    plt.figure(figsize=(8, 4.5))
    for col in df.columns:
        plt.plot(df.index, df[col], marker="o", label=col)
    plt.title(title)
    plt.xlabel("Ronda")
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _save_segment_stacked_chart(segment_brand_mix, output_path):
    df = pd.DataFrame(segment_brand_mix).T * 100

    plt.figure(figsize=(8.5, 4.8))
    bottom = None
    for col in df.columns:
        if bottom is None:
            plt.bar(df.index, df[col], label=col)
            bottom = df[col].copy()
        else:
            plt.bar(df.index, df[col], bottom=bottom, label=col)
            bottom = bottom + df[col]

    plt.title("Compra por segmento y marca")
    plt.xlabel("Segmentos")
    plt.ylabel("% compradores")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _save_comm_mix_chart_for_team(decision, team_name, output_path):
    mix = _safe_get_comm_mix(decision)
    total = _safe_get_comm_total(decision)

    labels = ["Tradicional", "Online", "RRSS", "PR"]
    values = [
        total * mix["trad"],
        total * mix["online"],
        total * mix["rrss"],
        total * mix["pr"],
    ]

    plt.figure(figsize=(7.5, 4.8))
    plt.bar(labels, values)
    plt.title(f"Mix de comunicación - {team_name}")
    plt.ylabel("Inversión")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _save_comm_mix_chart_all_teams(decisions, output_path):
    if not decisions:
        return

    teams = list(decisions.keys())
    trad_vals, online_vals, rrss_vals, pr_vals = [], [], [], []

    for t in teams:
        mix = _safe_get_comm_mix(decisions[t])
        total = _safe_get_comm_total(decisions[t])
        trad_vals.append(total * mix["trad"])
        online_vals.append(total * mix["online"])
        rrss_vals.append(total * mix["rrss"])
        pr_vals.append(total * mix["pr"])

    plt.figure(figsize=(9, 5))
    plt.bar(teams, trad_vals, label="Tradicional")
    plt.bar(teams, online_vals, bottom=trad_vals, label="Online")
    bottom2 = [a + b for a, b in zip(trad_vals, online_vals)]
    plt.bar(teams, rrss_vals, bottom=bottom2, label="RRSS")
    bottom3 = [a + b + c for a, b, c in zip(trad_vals, online_vals, rrss_vals)]
    plt.bar(teams, pr_vals, bottom=bottom3, label="PR")

    plt.title("Mix de comunicación por empresa")
    plt.ylabel("Inversión")
    plt.xticks(rotation=20)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _save_product_profile_chart_for_team(decision, team_truth, team_name, output_path):
    product = _safe_get_product_values(decision, team_truth)

    labels = ["Rendimiento", "Diseño", "Fiabilidad"]
    values = [
        product["product_perf"] * 100,
        product["product_design"] * 100,
        product["product_reliability"] * 100,
    ]

    plt.figure(figsize=(7.5, 4.8))
    plt.bar(labels, values)
    plt.title(f"Perfil de producto - {team_name}")
    plt.ylabel("Nivel (%)")
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _save_product_profile_chart_all_teams(truth_rows, output_path):
    if not truth_rows:
        return

    teams = [r["team"] for r in truth_rows]
    quality_vals = [float(r.get("quality", 0.0)) * 100 for r in truth_rows]

    plt.figure(figsize=(9, 5))
    plt.bar(teams, quality_vals)
    plt.title("Índice global de producto por empresa")
    plt.ylabel("Nivel (%)")
    plt.ylim(0, 100)
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def _save_positioning_map(research, output_path, highlight_team=None):
    prices = research.get("observed_avg_price", {})
    qualities = research.get("estimated_quality", {})

    teams = [t for t in prices.keys() if t in qualities]
    if not teams:
        return

    plt.figure(figsize=(8.2, 5.2))

    x_vals = [prices[t] for t in teams]
    y_vals = [qualities[t] * 100 for t in teams]

    for t, x, y in zip(teams, x_vals, y_vals):
        marker_size = 140 if t == highlight_team else 90
        plt.scatter(x, y, s=marker_size)
        plt.text(x + 0.03, y + 0.6, t, fontsize=9)

    plt.xlabel("Precio observado")
    plt.ylabel("Calidad estimada (%)")
    plt.title("Mapa de posicionamiento: precio y calidad")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


# -------------------------------------------------
# TABLAS Y BLOQUES
# -------------------------------------------------

def _draw_segment_mix_table(c, research, y_start=700):
    if "segment_brand_mix" not in research:
        return

    segment_brand_mix = research["segment_brand_mix"]
    df = pd.DataFrame(segment_brand_mix).T * 100
    df = df.round(1)

    _draw_section_title(c, "Compra por segmento y marca (%)", y_start)

    x0 = 40
    y = y_start - 25
    row_h = 22

    segment_col_w = 120
    team_names = list(df.columns)
    n_teams = len(team_names)
    team_col_w = max(52, int((PAGE_W - 80 - segment_col_w) / max(1, n_teams)))

    c.setFillColor(colors.HexColor("#EAF1F8"))
    c.roundRect(
        40,
        y - (row_h * (len(df.index) + 1)) - 10,
        PAGE_W - 80,
        row_h * (len(df.index) + 1) + 15,
        8,
        fill=1,
        stroke=0
    )

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x0 + 8, y, "Segmento")

    x = x0 + segment_col_w
    for team in team_names:
        c.drawString(x + 4, y, str(team)[:12])
        x += team_col_w

    y -= row_h
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)

    for seg in df.index:
        c.drawString(x0 + 8, y, str(seg)[:18])
        x = x0 + segment_col_w
        for team in team_names:
            c.drawString(x + 4, y, f"{df.loc[seg, team]:.1f}%")
            x += team_col_w
        y -= row_h


def _draw_segment_sizes_block(c, research, y_start):
    if "segment_sizes" not in research:
        return y_start

    segment_sizes = research["segment_sizes"]
    total_market = sum(segment_sizes.values())

    _draw_section_title(c, "Tamaño del mercado", y_start)

    c.setFillColor(colors.HexColor("#F3F6FA"))
    c.roundRect(40, y_start - 135, PAGE_W - 80, 110, 10, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, y_start - 45, "Población total / mercado total")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 11)
    c.drawString(280, y_start - 45, _fmt_int(total_market))

    y = y_start - 70
    for seg, size in segment_sizes.items():
        pct = (size / total_market * 100) if total_market > 0 else 0
        c.drawString(55, y, f"{seg}")
        c.drawString(230, y, _fmt_int(size))
        c.drawString(390, y, f"{pct:.1f}% del total")
        y -= 18

    return y_start - 150


def _draw_team_comm_block(c, decision, research, team_name, y_start):
    total = _safe_get_comm_total(decision)
    mix = _safe_get_comm_mix(decision)
    effects = research.get("estimated_comm_effects", {}).get(team_name, {})

    _draw_section_title(c, "Estrategia de comunicación", y_start)

    c.setFillColor(colors.HexColor("#F3F6FA"))
    c.roundRect(40, y_start - 175, PAGE_W - 80, 150, 10, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, y_start - 45, "Presupuesto total")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 11)
    c.drawString(220, y_start - 45, f"{_fmt_int(total)} EUR")

    rows = [
        ("Tradicional", mix["trad"]),
        ("Online", mix["online"]),
        ("RRSS", mix["rrss"]),
        ("PR", mix["pr"]),
    ]

    y = y_start - 72
    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y, "Canal")
    c.drawString(200, y, "%")
    c.drawString(260, y, "Importe")
    y -= 18

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    for label, pct in rows:
        c.drawString(55, y, label)
        c.drawString(200, y, f"{pct * 100:.1f}%")
        c.drawString(260, y, f"{_fmt_int(total * pct)} EUR")
        y -= 16

    if effects:
        awareness_effect = _get_comm_knowledge_effect(effects)

        c.setFillColor(colors.HexColor("#16324F"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(380, y_start - 72, "Lectura estimada")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(380, y_start - 92, f"Corto plazo: {effects.get('performance', 0) * 100:.1f}%")
        c.drawString(380, y_start - 108, f"Conocimiento: {awareness_effect * 100:.1f}%")
        c.drawString(380, y_start - 124, f"Pos. valor: {effects.get('brand_value', 0) * 100:.1f}%")
        c.drawString(380, y_start - 140, f"Pos. premium: {effects.get('brand_premium', 0) * 100:.1f}%")

    return y_start - 190


def _draw_team_product_block(c, decision, team_truth, research, team_name, y_start):
    product = _safe_get_product_values(decision, team_truth)

    _draw_section_title(c, "Decisión de producto", y_start)

    c.setFillColor(colors.HexColor("#F3F6FA"))
    c.roundRect(40, y_start - 165, PAGE_W - 80, 140, 10, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y_start - 45, "Rendimiento")
    c.drawString(185, y_start - 45, "Diseño")
    c.drawString(300, y_start - 45, "Fiabilidad")
    c.drawString(430, y_start - 45, "Índice global")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 11)
    c.drawString(55, y_start - 68, f"{product['product_perf'] * 100:.1f}%")
    c.drawString(185, y_start - 68, f"{product['product_design'] * 100:.1f}%")
    c.drawString(300, y_start - 68, f"{product['product_reliability'] * 100:.1f}%")
    c.drawString(430, y_start - 68, f"{product['quality'] * 100:.1f}%")

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y_start - 102, "Inversión en producto")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 11)
    c.drawString(195, y_start - 102, f"{_fmt_int(product['product_cost'])} EUR")

    est_perf = research.get("estimated_product_perf", {}).get(team_name)
    est_design = research.get("estimated_product_design", {}).get(team_name)
    est_rel = research.get("estimated_product_reliability", {}).get(team_name)
    est_q = research.get("estimated_quality", {}).get(team_name)

    if est_perf is not None:
        c.setFillColor(colors.HexColor("#16324F"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(55, y_start - 128, "Lectura estimada del mercado")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(220, y_start - 128, f"Rend.: {est_perf * 100:.1f}%")
        c.drawString(315, y_start - 128, f"Diseño: {est_design * 100:.1f}%")
        c.drawString(415, y_start - 128, f"Fiab.: {est_rel * 100:.1f}%")
        c.drawString(220, y_start - 144, f"Calidad global: {est_q * 100:.1f}%")

    return y_start - 185


def _draw_team_positioning_summary(c, research, team_name, y_start):
    price = research.get("observed_avg_price", {}).get(team_name)
    quality = research.get("estimated_quality", {}).get(team_name)

    _draw_section_title(c, "Posicionamiento en el mercado", y_start)

    c.setFillColor(colors.HexColor("#F3F6FA"))
    c.roundRect(40, y_start - 105, PAGE_W - 80, 80, 10, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y_start - 45, "Precio observado")
    c.drawString(240, y_start - 45, "Calidad estimada")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 11)
    c.drawString(55, y_start - 68, f"{price:.2f}" if price is not None else "-")
    c.drawString(240, y_start - 68, f"{quality * 100:.1f}%" if quality is not None else "-")

    c.setFont("Helvetica", 10)
    c.drawString(55, y_start - 88, "Este mapa resume cómo percibe el mercado tu marca en precio y calidad.")

    return y_start - 120


def _draw_facilitator_decisions_table(c, decisions, y_start=700):
    if not decisions:
        return

    _draw_section_title(c, "Precio y estrategias de cada empresa", y_start)

    x0 = 26
    y = y_start - 25
    row_h = 18

    headers = ["Empresa", "Precio", "Com.", "Promo", "Dist.", "Rend.", "Diseño", "Fiab."]
    col_widths = [82, 42, 58, 42, 40, 46, 50, 42]

    total_w = sum(col_widths)
    table_h = row_h * (len(decisions) + 1) + 12

    c.setFillColor(colors.HexColor("#EAF1F8"))
    c.roundRect(x0, y - table_h + 10, total_w, table_h, 8, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 8)

    x = x0 + 6
    for header, w in zip(headers, col_widths):
        c.drawString(x, y, header)
        x += w

    y -= row_h
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)

    for team_name, d in decisions.items():
        total = _safe_get_comm_total(d)
        p = _safe_get_product_values(d, None)

        row_vals = [
            str(team_name)[:14],
            f"{float(d['price']):.2f}",
            _fmt_int(total),
            f"{float(d['promo']) * 100:.0f}%",
            f"{float(d['distribution']) * 100:.0f}%",
            f"{p['product_perf'] * 100:.0f}%",
            f"{p['product_design'] * 100:.0f}%",
            f"{p['product_reliability'] * 100:.0f}%",
        ]

        x = x0 + 6
        for value, w in zip(row_vals, col_widths):
            c.drawString(x, y, str(value)[:12])
            x += w
        y -= row_h


def _draw_team_results_table(c, team_truth, y_start):
    _draw_section_title(c, "Tus resultados reales", y_start)

    boxes = [
        ("Ventas", _fmt_int(team_truth.get("units", 0))),
        ("Beneficio", _fmt_int(team_truth.get("profit", 0))),
        ("Cuota", _fmt_pct(team_truth.get("share", 0))),
        ("Conocimiento", _fmt_pct(team_truth.get("awareness_true", 0))),
        ("Retenidos", _fmt_int(team_truth.get("retained_customers", 0))),
        ("Nuevos", _fmt_int(team_truth.get("new_customers", 0))),
        ("% retenido", _fmt_pct(team_truth.get("retained_pct", 0))),
        ("Retención", _fmt_pct(team_truth.get("retention_rate", 0))),
    ]

    xs = [40, 170, 300, 430]
    y1 = y_start - 15
    y2 = y_start - 78

    for idx, (label, value) in enumerate(boxes[:4]):
        _draw_label_value_box(c, xs[idx], y1, 115, 48, label, value)

    for idx, (label, value) in enumerate(boxes[4:]):
        _draw_label_value_box(c, xs[idx], y2, 115, 48, label, value)

    return y_start - 140


# -------------------------------------------------
# INSIGHTS
# -------------------------------------------------

def _rank_text(rank, total):
    if rank == 1:
        return f"1.º de {total}"
    return f"{rank}.º de {total}"


def _team_segment_leaders(research):
    mix = research.get("segment_brand_mix", {})
    leaders = {}
    for seg, vals in mix.items():
        if vals:
            leaders[seg] = max(vals.items(), key=lambda x: x[1])
    return leaders


def _comm_strategy_label(decision):
    mix = _safe_get_comm_mix(decision)
    ranked = sorted(mix.items(), key=lambda x: x[1], reverse=True)
    top_key, top_val = ranked[0]

    if top_val >= 0.55:
        if top_key == "online":
            return "muy orientada a corto plazo y captación"
        if top_key == "trad":
            return "orientada a conocimiento y construcción de marca"
        if top_key == "rrss":
            return "orientada a visibilidad e interacción"
        if top_key == "pr":
            return "orientada a reputación y marca"
    return "equilibrada entre distintos objetivos"


def _build_team_comm_insights(team_name, research, your_decision):
    insights = []

    mix = _safe_get_comm_mix(your_decision)
    total = _safe_get_comm_total(your_decision)
    effects = research.get("estimated_comm_effects", {}).get(team_name, {})

    strat_label = _comm_strategy_label(your_decision)
    insights.append(
        f"Tu inversión en comunicación es de {_fmt_int(total)} EUR y la estrategia parece {strat_label}."
    )

    dominant = max(mix.items(), key=lambda x: x[1])[0]
    dominant_pct = max(mix.values()) * 100

    if dominant == "online":
        insights.append(
            f"El mayor peso recae en online ({dominant_pct:.1f}%); priorizas ventas inmediatas y captación frente a construcción de marca."
        )
    elif dominant == "trad":
        insights.append(
            f"El mayor peso recae en publicidad tradicional ({dominant_pct:.1f}%); refuerzas conocimiento y presencia sostenida."
        )
    elif dominant == "rrss":
        insights.append(
            f"El mayor peso recae en RRSS ({dominant_pct:.1f}%); apuestas por una mezcla equilibrada entre visibilidad, interacción y conversión."
        )
    else:
        insights.append(
            f"El mayor peso recae en PR ({dominant_pct:.1f}%); priorizas reputación, conocimiento cualitativo y defensa de la marca."
        )

    if effects:
        perf = effects.get("performance", 0)
        aware = _get_comm_knowledge_effect(effects)
        brand_value = effects.get("brand_value", 0)
        brand_premium = effects.get("brand_premium", 0)

        if perf >= aware + 0.10 and perf >= max(brand_value, brand_premium) + 0.10:
            insights.append(
                f"Tu comunicación favorece claramente el corto plazo ({perf * 100:.1f}%) por encima del conocimiento ({aware * 100:.1f}%) y la construcción de marca."
            )
        elif brand_premium >= perf + 0.08 or brand_value >= perf + 0.08:
            insights.append(
                f"Tu mix está construyendo posicionamiento: valor {brand_value * 100:.1f}% y premium {brand_premium * 100:.1f}%, con menor foco en activación inmediata ({perf * 100:.1f}%)."
            )
        elif abs(perf - aware) <= 0.08:
            insights.append(
                f"Tu mix de comunicación está bastante equilibrado entre corto plazo y conocimiento."
            )
        else:
            insights.append(
                f"Tu comunicación combina activación y construcción de marca, aunque sin una dominancia extrema de un único objetivo."
            )

    if mix["online"] >= 0.50:
        insights.append("Una dependencia alta de online puede acelerar ventas esta ronda, pero te deja más expuesto si bajas inversión después.")
    if mix["pr"] + mix["trad"] >= 0.55:
        insights.append("El peso conjunto de PR y tradicional debería ayudar más a conocimiento y reputación que a conversión inmediata.")
    if mix["rrss"] >= 0.35:
        insights.append("Un peso relevante en RRSS suele apoyar una evolución más equilibrada entre captación, conocimiento y vínculo con la marca.")

    return insights[:4]


def _build_team_product_insights(team_name, research, your_decision, team_truth=None):
    insights = []

    product = _safe_get_product_values(your_decision, team_truth)
    perf = product["product_perf"]
    design = product["product_design"]
    reliability = product["product_reliability"]
    quality = product["quality"]
    product_cost = product["product_cost"]

    vals = {
        "rendimiento": perf,
        "diseño": design,
        "fiabilidad": reliability
    }
    top_attr = max(vals.items(), key=lambda x: x[1])[0]
    top_val = max(vals.values())

    insights.append(
        f"Tu producto presenta un índice global del {quality * 100:.1f}% con una inversión estimada de {_fmt_int(product_cost)} EUR."
    )

    if top_attr == "rendimiento":
        insights.append(
            f"El rasgo dominante es el rendimiento ({top_val * 100:.1f}%), lo que debería ayudarte especialmente con segmentos más funcionales y sensibles al valor."
        )
    elif top_attr == "diseño":
        insights.append(
            f"El rasgo dominante es el diseño ({top_val * 100:.1f}%), lo que refuerza una propuesta más aspiracional y atractiva para segmentos sensibles a imagen."
        )
    else:
        insights.append(
            f"El rasgo dominante es la fiabilidad ({top_val * 100:.1f}%), lo que debería sostener mejor la satisfacción y la retención."
        )

    spread = max(vals.values()) - min(vals.values())
    if spread <= 0.10:
        insights.append("Tu perfil de producto está bastante equilibrado entre rendimiento, diseño y fiabilidad.")
    elif spread >= 0.25:
        insights.append("Tu producto está claramente especializado; eso puede mejorar el encaje con algunos segmentos, pero limitarlo en otros.")

    est_perf = research.get("estimated_product_perf", {}).get(team_name)
    est_design = research.get("estimated_product_design", {}).get(team_name)
    est_rel = research.get("estimated_product_reliability", {}).get(team_name)
    est_q = research.get("estimated_quality", {}).get(team_name)

    if est_q is not None:
        insights.append(
            f"El mercado parece percibir tu producto en torno al {est_q * 100:.1f}% de calidad global, con lectura estimada de rend. {est_perf * 100:.1f}%, diseño {est_design * 100:.1f}% y fiabilidad {est_rel * 100:.1f}%."
        )

    return insights[:4]


def _build_team_insights(team_name, research, your_decision, team_truth=None, event_info=None):
    insights = []

    est_share = research.get("estimated_share", {})
    est_awareness = _get_estimated_awareness(research)
    est_ret = research.get("estimated_retained_pct", {})
    est_new = research.get("estimated_new_pct", {})
    observed_prices = research.get("observed_avg_price", {})
    segment_mix = research.get("segment_brand_mix", {})
    est_quality = research.get("estimated_quality", {})
    est_coh = research.get("estimated_strategy_coherence", {})

    teams = list(est_share.keys())
    total_teams = len(teams) if teams else 0

    if team_name in est_share and total_teams:
        share_ranking = sorted(est_share.items(), key=lambda x: x[1], reverse=True)
        rank = [t for t, _ in share_ranking].index(team_name) + 1
        insights.append(
            f"Tu cuota estimada te sitúa en {_rank_text(rank, total_teams)} con {est_share[team_name] * 100:.1f}% del mercado."
        )

    if team_name in est_awareness and est_awareness:
        avg_aw = sum(est_awareness.values()) / len(est_awareness)
        diff_aw = (est_awareness[team_name] - avg_aw) * 100
        if diff_aw >= 1.0:
            insights.append(
                f"Tu conocimiento está {diff_aw:.1f} puntos por encima de la media; tu marca gana visibilidad relativa."
            )
        elif diff_aw <= -1.0:
            insights.append(
                f"Tu conocimiento está {abs(diff_aw):.1f} puntos por debajo de la media; necesitas más visibilidad o constancia comunicativa."
            )
        else:
            insights.append("Tu conocimiento está cerca de la media del mercado; no tienes una ventaja clara de visibilidad.")

    if team_name in observed_prices and team_name in est_quality:
        avg_price = sum(observed_prices.values()) / len(observed_prices)
        my_price = float(your_decision["price"])
        my_quality = est_quality[team_name] * 100

        if my_price <= avg_price - 0.35 and my_quality >= 52:
            insights.append(
                f"Tu marca parece bien situada en valor: precio contenido ({my_price:.2f}) y calidad percibida razonable ({my_quality:.1f}%)."
            )
        elif my_price >= avg_price + 0.35 and my_quality >= 60:
            insights.append(
                f"Tu marca apunta a una posición premium: precio superior ({my_price:.2f}) respaldado por una calidad percibida alta ({my_quality:.1f}%)."
            )
        elif my_price >= avg_price + 0.35 and my_quality < 55:
            insights.append(
                f"Tu precio ({my_price:.2f}) está por encima del promedio, pero la calidad percibida ({my_quality:.1f}%) no termina de sostenerlo."
            )
        else:
            insights.append(
                f"Tu posicionamiento precio-calidad es intermedio; compites sin una señal extrema ni de valor ni de premium."
            )

    if team_name in est_ret and team_name in est_new:
        r = est_ret[team_name]
        n = est_new[team_name]
        if r >= n + 0.10:
            insights.append(
                f"Tus ventas parecen apoyarse más en retención ({r * 100:.1f}%) que en captación ({n * 100:.1f}%); tu base actual responde bien."
            )
        elif n >= r + 0.10:
            insights.append(
                f"Tus ventas dependen más de captación ({n * 100:.1f}%) que de retención ({r * 100:.1f}%); creces atrayendo clientes nuevos."
            )
        else:
            insights.append(
                f"Tienes un equilibrio razonable entre retención ({r * 100:.1f}%) y captación ({n * 100:.1f}%); el crecimiento es relativamente equilibrado."
            )

    if team_name in est_coh:
        coh = est_coh[team_name]
        if coh >= 0.18:
            insights.append("Tu estrategia parece bastante coherente: precio, producto y activación comercial están alineados.")
        elif coh <= -0.18:
            insights.append("Tu estrategia muestra incoherencias relevantes: revisa especialmente la relación entre precio, calidad, promociones y distribución.")
        else:
            insights.append("Tu estrategia es razonablemente consistente, aunque todavía hay margen para mejorar el encaje entre tus decisiones.")

    if segment_mix:
        best_seg = None
        best_val = -1
        worst_seg = None
        worst_val = 10
        for seg, values in segment_mix.items():
            if team_name in values:
                val = values[team_name]
                if val > best_val:
                    best_val = val
                    best_seg = seg
                if val < worst_val:
                    worst_val = val
                    worst_seg = seg

        leaders = _team_segment_leaders(research)
        if best_seg is not None and best_seg in leaders:
            leader_team, leader_val = leaders[best_seg]
            if leader_team == team_name:
                insights.append(
                    f"Tu mejor encaje está en {best_seg}, donde lideras con {best_val * 100:.1f}% de preferencia estimada dentro del segmento."
                )
            else:
                insights.append(
                    f"Tu mejor segmento es {best_seg} con {best_val * 100:.1f}%, aunque el líder ahí es {leader_team} ({leader_val * 100:.1f}%)."
                )

        if worst_seg is not None:
            insights.append(
                f"Tu posición más débil está en {worst_seg} ({worst_val * 100:.1f}%); es el segmento donde más margen tienes para mejorar."
            )

    if team_truth:
        retention_rate = team_truth.get("retention_rate", 0) * 100
        if retention_rate >= 70:
            insights.append(f"Tu tasa real de retención es alta ({retention_rate:.1f}%); estás defendiendo bien la base de clientes.")
        elif retention_rate <= 45:
            insights.append(f"Tu tasa real de retención es baja ({retention_rate:.1f}%); estás perdiendo demasiados clientes entre rondas.")

    if event_info:
        extra = event_info.get("extra", "")
        low_extra = extra.lower()
        low_title = event_info.get("title", "").lower()
        if team_name.lower() in low_extra:
            if "viral" in low_title or "distribuidor" in low_title:
                insights.append("El evento de la ronda te favorece directamente; conviene aprovechar la ventaja con una propuesta competitiva en la próxima ronda.")
            elif "crisis" in low_title or "producción" in low_title:
                insights.append("El evento de la ronda te perjudica directamente; conviene proteger margen y retención mientras dura el impacto.")
        else:
            if "sensibilidad" in low_title:
                insights.append("El mercado se ha vuelto más sensible al precio; las marcas caras quedan más expuestas esta ronda.")
            elif "saturación publicitaria" in low_title:
                insights.append("La comunicación rinde peor esta ronda; gastar más no necesariamente se traducirá en más conocimiento inmediato.")
            elif "promociones" in low_title:
                insights.append("Las promociones pierden fuerza esta ronda; descuentos altos pueden dañar margen sin mover suficiente demanda.")

    return insights[:6]


def _build_facilitator_insights(truth_rows, research=None, decisions=None, event_info=None, history=None):
    insights = []
    if not truth_rows:
        return ["Sin datos suficientes para generar insights."]

    truth_sorted = sorted(truth_rows, key=lambda r: r["profit"], reverse=True)
    leader = truth_sorted[0]
    last = truth_sorted[-1]

    insights.append(
        f"El líder de la ronda es {leader['team']} con un beneficio de {_fmt_int(leader['profit'])} y una cuota del {leader['share'] * 100:.1f}%."
    )
    insights.append(
        f"La mayor presión competitiva recae sobre {last['team']}, que cierra la ronda con {_fmt_int(last['profit'])} de beneficio y {last['share'] * 100:.1f}% de cuota."
    )

    if len(truth_sorted) >= 2:
        gap = (truth_sorted[0]["share"] - truth_sorted[1]["share"]) * 100
        insights.append(f"La distancia entre el primer y segundo equipo en cuota es de {gap:.1f} puntos.")

    ret_leader = max(truth_rows, key=lambda r: r.get("retention_rate", 0))
    aware_leader = max(truth_rows, key=lambda r: r.get("awareness_true", 0))
    insights.append(
        f"{ret_leader['team']} lidera en retención ({ret_leader.get('retention_rate', 0) * 100:.1f}%), mientras {aware_leader['team']} lidera en conocimiento ({aware_leader.get('awareness_true', 0) * 100:.1f}%)."
    )

    if decisions:
        prices = {team: float(d["price"]) for team, d in decisions.items()}
        cheapest = min(prices.items(), key=lambda x: x[1])
        expensive = max(prices.items(), key=lambda x: x[1])
        insights.append(
            f"La amplitud de precios va de {cheapest[1]:.2f} ({cheapest[0]}) a {expensive[1]:.2f} ({expensive[0]}), lo que marca la tensión competitiva entre valor y margen."
        )

        comm_totals = {team: _safe_get_comm_total(d) for team, d in decisions.items()}
        comm_leader = max(comm_totals.items(), key=lambda x: x[1])
        insights.append(
            f"La mayor inversión en comunicación la realiza {comm_leader[0]} con {_fmt_int(comm_leader[1])} EUR."
        )

    if research and research.get("segment_brand_mix"):
        leaders = _team_segment_leaders(research)
        leader_parts = []
        for seg, (team, val) in leaders.items():
            leader_parts.append(f"{seg}: {team} ({val * 100:.1f}%)")
        insights.append("Liderazgo por segmento: " + " | ".join(leader_parts) + ".")

    if research and research.get("estimated_comm_effects"):
        comm = research["estimated_comm_effects"]
        perf_leader = max(comm.items(), key=lambda x: x[1].get("performance", 0))
        brand_value_leader = max(comm.items(), key=lambda x: x[1].get("brand_value", 0))
        brand_premium_leader = max(comm.items(), key=lambda x: x[1].get("brand_premium", 0))
        insights.append(
            f"En comunicación, {perf_leader[0]} parece liderar el impacto de corto plazo, {brand_value_leader[0]} el posicionamiento valor y {brand_premium_leader[0]} el posicionamiento premium."
        )

    if truth_rows:
        quality_leader = max(truth_rows, key=lambda r: r.get("quality", 0))
        insights.append(
            f"El mayor índice global de producto lo presenta {quality_leader['team']} con {quality_leader.get('quality', 0) * 100:.1f}%."
        )

    if research and research.get("estimated_strategy_coherence"):
        coh = research["estimated_strategy_coherence"]
        coh_leader = max(coh.items(), key=lambda x: x[1])
        coh_last = min(coh.items(), key=lambda x: x[1])
        insights.append(
            f"La estrategia más coherente parece ser la de {coh_leader[0]} ({coh_leader[1]:.2f}), mientras que {coh_last[0]} muestra más señales de incoherencia ({coh_last[1]:.2f})."
        )

    if event_info:
        desc = event_info.get("title", "evento")
        extra = event_info.get("extra", "")
        insights.append(f"El evento de la ronda ha sido '{desc}'. {extra}".strip())

    if history and len(history) >= 2:
        prev_truth = history[-2].get("truth", [])
        prev_by_team = {r["team"]: r for r in prev_truth}
        movers = []
        for row in truth_rows:
            prev = prev_by_team.get(row["team"])
            if prev:
                diff = (row["share"] - prev["share"]) * 100
                movers.append((row["team"], diff))
        if movers:
            up = max(movers, key=lambda x: x[1])
            down = min(movers, key=lambda x: x[1])
            insights.append(
                f"Frente a la ronda anterior, la mayor subida de cuota es {up[0]} ({up[1]:+.1f} pts) y la mayor caída es {down[0]} ({down[1]:+.1f} pts)."
            )

    return insights[:8]


# -------------------------------------------------
# HISTÓRICO
# -------------------------------------------------

def _make_history_charts(history, output_dir):
    if not history:
        return []

    rows = []
    for round_data in history:
        rnum = round_data["round"]
        for row in round_data["truth"]:
            rows.append({
                "round": rnum,
                "team": row["team"],
                "share": row["share"] * 100,
                "profit": row["profit"],
                "awareness": row["awareness_true"] * 100,
                "retention_rate": row.get("retention_rate", 0) * 100
            })

    if not rows:
        return []

    df = pd.DataFrame(rows)

    paths = []

    share_df = df.pivot(index="round", columns="team", values="share")
    path1 = os.path.join(output_dir, "share_history.png")
    _save_line_chart(share_df, "Evolución de cuota de mercado", "Cuota (%)", path1)
    paths.append(path1)

    profit_df = df.copy()
    profit_df["profit_acum"] = profit_df.groupby("team")["profit"].cumsum()
    profit_chart = profit_df.pivot(index="round", columns="team", values="profit_acum")
    path2 = os.path.join(output_dir, "profit_history.png")
    _save_line_chart(profit_chart, "Evolución de beneficio acumulado", "Beneficio acumulado", path2)
    paths.append(path2)

    awareness_df = df.pivot(index="round", columns="team", values="awareness")
    path3 = os.path.join(output_dir, "awareness_history.png")
    _save_line_chart(awareness_df, "Evolución de conocimiento acumulado", "Conocimiento (%)", path3)
    paths.append(path3)

    ret_df = df.pivot(index="round", columns="team", values="retention_rate")
    path4 = os.path.join(output_dir, "retention_history.png")
    _save_line_chart(ret_df, "Evolución de la retención", "Retención (%)", path4)
    paths.append(path4)

    return paths



# -------------------------------------------------
# PDF INFORMES DE COMPRA
# -------------------------------------------------

def _classify_price_position(team_price, avg_price):
    if team_price <= avg_price - 0.35:
        return "Precio competitivo"
    if team_price >= avg_price + 0.35:
        return "Precio alto"
    return "Precio intermedio"


def _classify_promo_level(promo_value):
    if promo_value >= 0.12:
        return "Promoción intensa"
    if promo_value >= 0.06:
        return "Promoción media"
    return "Promoción baja"


def _classify_comm_style_from_truth(row):
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
    total = sum(values.values())
    if total <= 0:
        return "Presión publicitaria baja"

    top_channel, top_value = max(values.items(), key=lambda x: x[1])
    top_share = top_value / total

    if top_share < 0.40:
        return "Mix equilibrado"

    mapping = {
        "tradicional": "Más orientado a conocimiento de marca",
        "online": "Más orientado a captación",
        "rrss": "Más orientado a visibilidad e interacción",
        "pr": "Más orientado a reputación",
    }
    return mapping[top_channel]


def _classify_dist_level_from_truth(row):
    dist = float(row.get("distribution", 0))
    if dist >= 0.75:
        return "Cobertura comercial alta"
    if dist >= 0.55:
        return "Cobertura comercial media"
    return "Cobertura comercial limitada"


def _build_segments_report_insights(team_name, research, event_info=None):
    insights = []

    segment_sizes = research.get("segment_sizes", {})
    segment_mix = research.get("segment_brand_mix", {})

    if not segment_sizes or not segment_mix:
        return ["No hay información suficiente para analizar segmentos."]

    total_market = sum(segment_sizes.values())
    biggest_seg, biggest_size = max(segment_sizes.items(), key=lambda x: x[1])
    insights.append(
        f"El segmento más grande es {biggest_seg}, con {_fmt_int(biggest_size)} clientes potenciales y un peso del {biggest_size / max(total_market, 1.0) * 100:.1f}% del mercado."
    )

    best_seg, best_val = None, -1.0
    worst_seg, worst_val = None, 10.0

    for seg, vals in segment_mix.items():
        my_val = float(vals.get(team_name, 0.0))
        if my_val > best_val:
            best_seg, best_val = seg, my_val
        if my_val < worst_val:
            worst_seg, worst_val = seg, my_val

    if best_seg is not None:
        leader_team, leader_val = max(segment_mix[best_seg].items(), key=lambda x: x[1])
        if leader_team == team_name:
            insights.append(
                f"Tu estrategia encaja mejor en {best_seg}, donde lideras con un {best_val * 100:.1f}% de preferencia estimada."
            )
        else:
            insights.append(
                f"Tu mejor encaje está en {best_seg} ({best_val * 100:.1f}%), aunque el líder del segmento sigue siendo {leader_team} ({leader_val * 100:.1f}%)."
            )

    if worst_seg is not None:
        insights.append(
            f"Tu encaje más débil aparece en {worst_seg} ({worst_val * 100:.1f}%), señal de que tu propuesta actual conecta peor con ese segmento."
        )

    open_segments = []
    for seg, vals in segment_mix.items():
        leader_team, leader_val = max(vals.items(), key=lambda x: x[1])
        if leader_val < 0.38:
            open_segments.append((seg, leader_team, leader_val))

    if open_segments:
        seg, leader_team, leader_val = open_segments[0]
        insights.append(
            f"{seg} parece relativamente abierto: el líder solo alcanza {leader_val * 100:.1f}% ({leader_team}), así que todavía hay espacio competitivo."
        )

    if event_info:
        title = (event_info.get("title") or "").lower()
        if "demanda" in title or "mercado" in title:
            insights.append(
                "El evento de la ronda puede haber cambiado el atractivo relativo de los segmentos, así que conviene revisar si tu foco sigue estando donde mejor encajas."
            )

    return insights[:5]

def _build_competition_report_insights(team_name, truth_rows):
    insights = []
    if not truth_rows:
        return ["No hay datos suficientes de competencia."]

    df = pd.DataFrame(truth_rows).copy()
    avg_price = float(df["price"].mean())
    avg_dist = float(df["distribution"].mean())
    avg_promo = float(df["promo"].mean())
    avg_aw = float(df["awareness_true"].mean())
    avg_quality = float(df["quality"].mean())

    share_leader = df.sort_values("share", ascending=False).iloc[0]
    insights.append(
        f"El líder competitivo es {share_leader['team']} con una cuota del {share_leader['share'] * 100:.1f}%."
    )

    awareness_leader = df.sort_values("awareness_true", ascending=False).iloc[0]
    insights.append(
        f"La marca con mayor conocimiento es {awareness_leader['team']} ({awareness_leader['awareness_true'] * 100:.1f}%)."
    )

    your_row = df[df["team"] == team_name]
    if not your_row.empty:
        r = your_row.iloc[0]

        if float(r["price"]) < avg_price - 0.30:
            insights.append("Tu estrategia es más agresiva en precio que la media del mercado.")
        elif float(r["price"]) > avg_price + 0.30:
            insights.append("Tu precio es superior a la media, así que necesitas una propuesta más sólida para sostenerlo.")
        else:
            insights.append("Tu precio está alineado con la media del mercado.")

        if float(r["distribution"]) > avg_dist:
            insights.append("Estás por encima de la media en distribución, lo que favorece tu capacidad de captación.")
        else:
            insights.append("Tu distribución está por debajo de la media, lo que puede limitar ventas frente a rivales mejor cubiertos.")

        if float(r["promo"]) > avg_promo:
            insights.append("Tu estrategia es más agresiva en promoción que la mayoría de competidores.")
        else:
            insights.append("Tu nivel de promoción es más moderado que el del mercado.")

        better_dims = []
        if float(r["awareness_true"]) > avg_aw:
            better_dims.append("conocimiento")
        if float(r["quality"]) > avg_quality:
            better_dims.append("producto")
        if float(r["distribution"]) > avg_dist:
            better_dims.append("distribución")

        if better_dims:
            dims_txt = ", ".join(better_dims)
            insights.append(
                f"Frente a la competencia, tus principales fortalezas relativas parecen estar en {dims_txt}."
            )
        else:
            insights.append(
                "Frente a la competencia no destaca todavía una ventaja clara; tu estrategia necesita una palanca más diferencial."
            )

    return insights[:6]

def _build_brand_product_report_insights(team_name, research, your_decision, team_truth=None):
    insights = []

    observed_price = research.get("observed_avg_price", {}).get(team_name)
    est_quality = research.get("estimated_quality", {}).get(team_name)
    est_perf = research.get("estimated_product_perf", {}).get(team_name)
    est_design = research.get("estimated_product_design", {}).get(team_name)
    est_rel = research.get("estimated_product_reliability", {}).get(team_name)
    est_coh = research.get("estimated_strategy_coherence", {}).get(team_name)

    product = _safe_get_product_values(your_decision, team_truth)
    price = float(your_decision.get("price", observed_price or 0.0))
    promo = float(your_decision.get("promo", 0.0))
    dist = float(your_decision.get("distribution", 0.0))

    if observed_price is not None and est_quality is not None:
        all_prices = list(research.get("observed_avg_price", {}).values())
        avg_price = sum(all_prices) / len(all_prices) if all_prices else observed_price

        if observed_price >= avg_price + 0.35 and est_quality >= 0.60:
            insights.append(
                f"Tu marca parece ocupar una posición premium relativamente coherente: precio observado {observed_price:.2f} y calidad estimada {est_quality * 100:.1f}%."
            )
        elif observed_price <= avg_price - 0.35 and est_quality >= 0.50:
            insights.append(
                f"Tu marca parece competir en valor: precio observado {observed_price:.2f} y calidad estimada {est_quality * 100:.1f}%."
            )
        elif observed_price >= avg_price + 0.35 and est_quality < 0.55:
            insights.append(
                f"Tu precio observado ({observed_price:.2f}) parece alto para la calidad percibida ({est_quality * 100:.1f}%)."
            )
        else:
            insights.append("Tu posicionamiento actual parece intermedio en el eje calidad-precio.")

    vals = {
        "rendimiento": product["product_perf"],
        "diseño": product["product_design"],
        "fiabilidad": product["product_reliability"],
    }
    top_attr, top_val = max(vals.items(), key=lambda x: x[1])
    insights.append(
        f"El atributo más fuerte de tu producto es {top_attr} ({top_val * 100:.1f}%), lo que condiciona el tipo de segmento donde puedes competir mejor."
    )

    if est_perf is not None and est_design is not None and est_rel is not None:
        insights.append(
            f"El mercado parece leer tu producto así: rendimiento {est_perf * 100:.1f}%, diseño {est_design * 100:.1f}% y fiabilidad {est_rel * 100:.1f}%."
        )

    if promo > 0.12:
        insights.append("El uso intensivo de promociones puede estar debilitando tu posicionamiento de marca.")
    elif promo < 0.05:
        insights.append("Tu presión promocional es baja; eso protege marca, pero puede limitar captación si el mercado se mueve por activación.")

    if dist < 0.50:
        insights.append("Tu nivel de distribución es limitado y puede estar frenando el crecimiento incluso si la propuesta de producto es razonable.")
    elif dist > 0.75:
        insights.append("Tu amplia distribución favorece la captación y sostiene mejor la presencia competitiva en el mercado.")

    if est_coh is not None:
        if est_coh >= 0.70:
            insights.append("La estrategia está siendo bien percibida: precio, producto y activación comercial parecen bastante alineados.")
        elif est_coh >= 0.50:
            insights.append("La estrategia se percibe como razonable, aunque todavía hay margen para mejorar el encaje entre precio, producto y activación.")
        else:
            insights.append("La estrategia presenta incoherencias visibles; conviene revisar sobre todo la relación entre precio, calidad, promociones y distribución.")

    return insights[:6]

def _draw_simple_table(c, x0, y0, headers, rows, col_widths, row_h=20, font_size=9):
    total_h = row_h * (len(rows) + 1) + 12
    c.setFillColor(colors.HexColor("#EAF1F8"))
    c.roundRect(x0, y0 - total_h + 8, sum(col_widths), total_h, 8, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", font_size)
    x = x0 + 6
    for header, w in zip(headers, col_widths):
        c.drawString(x, y0, str(header)[:22])
        x += w

    y = y0 - row_h
    c.setFillColor(colors.black)
    c.setFont("Helvetica", font_size)
    for row in rows:
        x = x0 + 6
        for value, w in zip(row, col_widths):
            c.drawString(x, y, str(value)[:22])
            x += w
        y -= row_h
    return y0 - total_h


def _draw_competition_table(c, truth_rows, team_name, y_start):
    df = pd.DataFrame(truth_rows).copy()
    avg_price = float(df["price"].mean())

    rows = []
    for _, row in df.sort_values("share", ascending=False).iterrows():
        marker = "← tú" if row["team"] == team_name else ""
        rows.append([
            f"{row['team']} {marker}".strip(),
            f"{row['share'] * 100:.1f}%",
            f"{row['awareness_true'] * 100:.1f}%",
            _classify_price_position(float(row["price"]), avg_price),
            _classify_promo_level(float(row.get("promo", 0.0))),
            _classify_dist_level_from_truth(row),
            _classify_comm_style_from_truth(row),
        ])

    headers = ["Equipo", "Cuota", "Conoc.", "Precio", "Promo", "Dist.", "Com."]
    col_widths = [88, 44, 50, 78, 72, 78, 104]
    _draw_section_title(c, "Lectura competitiva aproximada", y_start)
    return _draw_simple_table(c, 18, y_start - 24, headers, rows, col_widths, row_h=18, font_size=7.6)


def _draw_brand_product_metrics(c, team_name, research, your_decision, team_truth, y_start):
    observed_price = research.get("observed_avg_price", {}).get(team_name)
    est_quality = research.get("estimated_quality", {}).get(team_name)
    est_perf = research.get("estimated_product_perf", {}).get(team_name)
    est_design = research.get("estimated_product_design", {}).get(team_name)
    est_rel = research.get("estimated_product_reliability", {}).get(team_name)
    est_coh = research.get("estimated_strategy_coherence", {}).get(team_name)
    product = _safe_get_product_values(your_decision, team_truth)

    _draw_section_title(c, "Lectura de marca y producto", y_start)
    _draw_label_value_box(c, 40, y_start - 18, 115, 48, "Precio obs.", f"{observed_price:.2f}" if observed_price is not None else "-")
    _draw_label_value_box(c, 170, y_start - 18, 115, 48, "Calidad est.", f"{est_quality * 100:.1f}%" if est_quality is not None else "-")
    _draw_label_value_box(c, 300, y_start - 18, 115, 48, "Coherencia", f"{est_coh * 100:.1f}%" if est_coh is not None else "-")
    _draw_label_value_box(c, 430, y_start - 18, 115, 48, "Producto real", f"{product['quality'] * 100:.1f}%")

    c.setFillColor(colors.HexColor("#F3F6FA"))
    c.roundRect(40, y_start - 145, PAGE_W - 80, 70, 10, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y_start - 98, "Atributos estimados")
    c.drawString(220, y_start - 98, "Rendimiento")
    c.drawString(320, y_start - 98, "Diseño")
    c.drawString(410, y_start - 98, "Fiabilidad")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(220, y_start - 118, f"{est_perf * 100:.1f}%" if est_perf is not None else "-")
    c.drawString(320, y_start - 118, f"{est_design * 100:.1f}%" if est_design is not None else "-")
    c.drawString(410, y_start - 118, f"{est_rel * 100:.1f}%" if est_rel is not None else "-")

    return y_start - 160




# -------------------------------------------------
# INFORME DE MERCADO PRO (dashboard visual)
# -------------------------------------------------

_PRO_BLUE = "#063763"
_PRO_BLUE_2 = "#0B4F8A"
_PRO_LIGHT = "#F4F8FC"
_PRO_BORDER = "#D8E3EF"
_PRO_GREEN = "#239954"
_PRO_ORANGE = "#F59E0B"
_PRO_RED = "#D64545"
_PRO_PURPLE = "#7A3FA1"
_PRO_GREY = "#97A3B3"


def _pdf_segment_name_es(name):
    mapping = {
        "Price Seekers": "Ahorradores",
        "Mainstream": "Equilibrados",
        "Brand Lovers": "Exigentes",
        "Ahorradores": "Ahorradores",
        "Equilibrados": "Equilibrados",
        "Exigentes": "Exigentes",
    }
    return mapping.get(str(name), str(name))


def _market_pro_palette(index):
    colors_list = [_PRO_GREEN, "#0B5CAD", _PRO_PURPLE, "#F97316", _PRO_RED, _PRO_GREY, "#00A6A6", "#6D28D9"]
    return colors_list[index % len(colors_list)]


def _draw_market_header(c, title, subtitle, round_n, team_name, market_total):
    c.setFillColor(colors.HexColor(_PRO_BLUE))
    c.roundRect(18, PAGE_H - 78, PAGE_W - 36, 64, 8, fill=1, stroke=0)

    # Icon block
    c.setStrokeColor(colors.HexColor("#78B7E5"))
    c.setLineWidth(1.4)
    c.line(78, PAGE_H - 68, 78, PAGE_H - 24)
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.white)
    c.drawString(33, PAGE_H - 55, "▥")

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(95, PAGE_H - 40, title.upper())
    c.setFont("Helvetica", 12)
    c.drawString(96, PAGE_H - 59, subtitle)

    c.setStrokeColor(colors.HexColor("#78B7E5"))
    c.line(PAGE_W - 205, PAGE_H - 68, PAGE_W - 205, PAGE_H - 24)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(colors.white)
    x_lab = PAGE_W - 190
    c.drawString(x_lab, PAGE_H - 31, "Ronda:")
    c.drawString(x_lab, PAGE_H - 48, "Tu marca:")
    c.drawString(x_lab, PAGE_H - 65, "Mercado total:")
    c.setFont("Helvetica", 8.5)
    c.drawString(x_lab + 78, PAGE_H - 31, str(round_n))
    c.drawString(x_lab + 78, PAGE_H - 48, str(team_name)[:18])
    c.drawString(x_lab + 78, PAGE_H - 65, f"{_fmt_int(market_total)} uds.")


def _draw_round_card(c, x, y, w, h, title, value, note="", accent=_PRO_BLUE_2, icon=None):
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor(_PRO_BORDER))
    c.setLineWidth(0.8)
    c.roundRect(x, y - h, w, h, 7, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#0F1F3D"))
    c.setFont("Helvetica-Bold", 7.4)
    for i, line in enumerate(_split_text(title.upper(), max_chars=18)[:2]):
        c.drawCentredString(x + w / 2, y - 13 - i * 9, line)
    if icon:
        c.setFillColor(colors.HexColor("#476B93"))
        c.setFont("Helvetica", 18)
        c.drawCentredString(x + w / 2, y - 42, icon)
    c.setFillColor(colors.HexColor(accent))
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(x + w / 2, y - 62, str(value))
    if note:
        c.setFillColor(colors.HexColor("#44546A"))
        c.setFont("Helvetica", 7.2)
        c.drawCentredString(x + w / 2, y - 77, str(note)[:26])


def _draw_panel(c, x, y, w, h, title=None):
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor(_PRO_BORDER))
    c.setLineWidth(0.8)
    c.roundRect(x, y - h, w, h, 8, fill=1, stroke=1)
    if title:
        c.setFillColor(colors.HexColor("#064A90"))
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(x + 10, y - 18, title)


def _draw_small_note(c, x, y, w, h, text, icon="☆"):
    c.setFillColor(colors.HexColor("#EAF4FF"))
    c.roundRect(x, y - h, w, h, 7, fill=1, stroke=0)
    c.setFillColor(colors.HexColor(_PRO_BLUE_2))
    c.setFont("Helvetica", 16)
    c.drawString(x + 10, y - 21, icon)
    c.setFillColor(colors.HexColor("#1A2B45"))
    c.setFont("Helvetica-Bold", 7.8)
    yy = y - 14
    for line in _split_text(text, max_chars=72)[:3]:
        c.drawString(x + 34, yy, line)
        yy -= 10


def _save_market_donut_chart(segment_sizes, output_path):
    labels = [_pdf_segment_name_es(k) for k in segment_sizes.keys()]
    values = [float(v) for v in segment_sizes.values()]
    if not values or sum(values) <= 0:
        return
    fig, ax = plt.subplots(figsize=(3.2, 2.1))
    ax.pie(values, labels=None, autopct=lambda p: f"{p:.1f}%", startangle=90, pctdistance=0.78,
           wedgeprops=dict(width=0.38, edgecolor="white"))
    ax.axis("equal")
    plt.tight_layout(pad=0.1)
    plt.savefig(output_path, dpi=180, transparent=True)
    plt.close(fig)


def _save_segment_horizontal_chart(segment_name, values, team_name, output_path):
    items = sorted(values.items(), key=lambda x: float(x[1]), reverse=True)
    labels = [t for t, _ in items]
    vals = [float(v) * 100 for _, v in items]
    fig, ax = plt.subplots(figsize=(2.2, 1.85))
    bar_colors = ["#0B5CAD" if t == team_name else "#B8B8B8" for t in labels]
    if labels:
        leader = labels[0]
        if leader != team_name:
            bar_colors[0] = "#2F9E55"
    ax.barh(labels[::-1], vals[::-1], color=bar_colors[::-1])
    ax.set_xlim(0, max(60, max(vals) + 8 if vals else 60))
    ax.tick_params(axis='y', labelsize=6.5)
    ax.tick_params(axis='x', labelsize=6)
    ax.grid(axis="x", alpha=0.18)
    ax.set_title(_pdf_segment_name_es(segment_name).upper(), fontsize=8, fontweight="bold", color="#064A90")
    for i, v in enumerate(vals[::-1]):
        ax.text(v + 1, i, f"{v:.1f}%", va='center', fontsize=6)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    plt.tight_layout(pad=0.35)
    plt.savefig(output_path, dpi=180, transparent=True)
    plt.close(fig)


def _get_market_prev_segment_sizes(research):
    # El motor actual no siempre guarda histórico por segmento en research.
    # Si existe algún campo futuro, lo leemos sin romper compatibilidad.
    return research.get("prev_segment_sizes") or research.get("segment_sizes_previous") or {}


def _calc_segment_rows(research):
    segment_sizes = research.get("segment_sizes", {}) or {}
    prev_sizes = _get_market_prev_segment_sizes(research)
    total = sum(float(v) for v in segment_sizes.values()) or 1.0
    rows = []
    for seg, size in segment_sizes.items():
        size = float(size)
        pct = size / total
        prev = prev_sizes.get(seg)
        if prev is not None and float(prev) > 0:
            evo = (size / float(prev) - 1.0)
            evo_txt = f"{evo:+.1%}".replace(".", ",")
        else:
            evo_txt = "—"
        rows.append((seg, size, pct, evo_txt))
    return rows, total


def _segment_opportunity_data(team_name, research):
    rows, total = _calc_segment_rows(research)
    mix = research.get("segment_brand_mix", {}) or {}
    out = []
    for seg, size, pct, evo in rows:
        vals = mix.get(seg, {}) or {}
        if vals:
            leader, leader_val = max(vals.items(), key=lambda x: float(x[1]))
            my_val = float(vals.get(team_name, 0.0))
        else:
            leader, leader_val, my_val = "-", 0.0, 0.0
        if leader_val < 0.37:
            comp, opp = "Baja", "ALTA"
        elif leader_val < 0.48:
            comp, opp = "Media", "MEDIA"
        else:
            comp, opp = "Alta", "BAJA"
        # Si la marca tiene buen encaje en un segmento grande, subimos lectura de oportunidad.
        if pct >= 0.30 and my_val >= leader_val - 0.06 and opp != "ALTA":
            opp = "MEDIA"
        out.append({
            "segment": seg, "size": size, "pct": pct, "evo": evo,
            "leader": leader, "leader_val": float(leader_val), "my_val": my_val,
            "competition": comp, "opportunity": opp,
        })
    return out


def _market_summary_text(team_name, research, event_info):
    rows, total = _calc_segment_rows(research)
    if not rows:
        return "El mercado aún no tiene información suficiente para extraer una lectura completa."
    biggest = max(rows, key=lambda r: r[1])
    event_txt = "No hubo evento relevante en esta ronda."
    if event_info:
        event_txt = f"El evento de la ronda ({event_info.get('title', 'evento')}) puede alterar la lectura del mercado."
    return (
        f"El mercado alcanza {_fmt_int(total)} unidades potenciales. El mayor volumen se concentra en "
        f"{_pdf_segment_name_es(biggest[0])} ({biggest[2] * 100:.1f}%). {event_txt} "
        "El análisis combina tamaño, liderazgo y espacio competitivo para detectar oportunidades reales."
    )


def _market_working_blocks(team_name, research, event_info):
    opp_rows = _segment_opportunity_data(team_name, research)
    mix = research.get("segment_brand_mix", {}) or {}
    lines_strategy = []
    for r in opp_rows[:3]:
        seg = _pdf_segment_name_es(r["segment"])
        leader = r["leader"]
        if leader == team_name:
            lines_strategy.append(f"{seg}: tu marca lidera; defiende posición con coherencia y foco.")
        else:
            lines_strategy.append(f"{seg}: lidera {leader}; observa su combinación de propuesta y cobertura.")
    if not lines_strategy:
        lines_strategy = ["Aún no hay suficiente información para identificar estrategias ganadoras."]

    lines_factors = [
        "La distribución ayuda a convertir la demanda generada en ventas reales.",
        "La calidad y la coherencia pesan más en segmentos menos sensibles al precio.",
        "La promoción puede acelerar compra, pero no sustituye una propuesta clara."
    ]
    if event_info:
        lines_trends = [f"Evento de ronda: {event_info.get('title', 'Evento')}. {event_info.get('desc', '')}"[:130]]
    else:
        lines_trends = ["Sin evento relevante: la evolución responde sobre todo a decisiones de precio, producto, distribución y comunicación."]
    lines_trends.append("Los segmentos grandes con liderazgo bajo concentran las mejores oportunidades.")
    return lines_strategy, lines_factors, lines_trends


def _market_conclusion_boxes(team_name, research):
    opp_rows = _segment_opportunity_data(team_name, research)
    if not opp_rows:
        return ["Sin datos suficientes."], ["Sin datos suficientes."], ["Compra o espera a cerrar una ronda para analizar el mercado."]
    best = max(opp_rows, key=lambda r: r["my_val"])
    weakest = min(opp_rows, key=lambda r: r["my_val"])
    best_opp = sorted(opp_rows, key=lambda r: (0 if r["opportunity"] == "ALTA" else 1 if r["opportunity"] == "MEDIA" else 2, -r["pct"]))[0]
    good = [
        f"Tu mejor posición aparece en {_pdf_segment_name_es(best['segment'])} ({best['my_val'] * 100:.1f}%).",
        "Ya cuentas con una base para orientar mejor tus decisiones por segmento.",
        "El informe permite identificar dónde compensa reforzar inversión."
    ]
    bad = [
        f"Tu presencia más débil está en {_pdf_segment_name_es(weakest['segment'])} ({weakest['my_val'] * 100:.1f}%).",
        "Evita repartir inversión sin una prioridad clara por segmento.",
        "No confundas tamaño de mercado con oportunidad si el segmento está dominado."
    ]
    opportunity = [
        f"{_pdf_segment_name_es(best_opp['segment'])} muestra oportunidad {best_opp['opportunity'].lower()}.",
        f"El líder actual tiene {best_opp['leader_val'] * 100:.1f}% de cuota en ese segmento.",
        "Ajusta precio, distribución y comunicación al grupo con mayor potencial."
    ]
    return good, bad, opportunity


def _draw_market_segment_table_and_donut(c, x, y, w, h, research, donut_path):
    _draw_panel(c, x, y, w, h, "2. ESTRUCTURA DEL MERCADO POR SEGMENTOS")
    rows, total = _calc_segment_rows(research)
    table_x = x + 12
    table_y = y - 45
    c.setFont("Helvetica-Bold", 7.8)
    c.setFillColor(colors.HexColor("#24364B"))
    c.drawString(table_x, table_y, "Segmento")
    c.drawRightString(table_x + 150, table_y, "Tamaño")
    c.drawRightString(table_x + 220, table_y, "% mercado")
    c.drawRightString(table_x + 282, table_y, "Evolución")
    c.setStrokeColor(colors.HexColor(_PRO_BORDER))
    c.line(table_x, table_y - 7, x + w - 12, table_y - 7)
    yy = table_y - 25
    for i, (seg, size, pct, evo) in enumerate(rows):
        c.setFillColor(colors.HexColor(_market_pro_palette(i)))
        c.circle(table_x + 5, yy + 3, 3, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#1A2B45"))
        c.setFont("Helvetica", 8)
        c.drawString(table_x + 15, yy, _pdf_segment_name_es(seg))
        c.drawRightString(table_x + 150, yy, _fmt_int(size))
        c.drawRightString(table_x + 220, yy, f"{pct * 100:.1f}%")
        if evo.startswith("+"):
            c.setFillColor(colors.HexColor(_PRO_GREEN))
        elif evo.startswith("-"):
            c.setFillColor(colors.HexColor(_PRO_RED))
        else:
            c.setFillColor(colors.HexColor("#667085"))
        c.drawRightString(table_x + 282, yy, evo)
        yy -= 20
    c.setFillColor(colors.HexColor("#F4F8FC"))
    c.roundRect(table_x, yy - 10, w - 24, 22, 5, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1A2B45"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(table_x + 8, yy - 2, "TOTAL MERCADO")
    c.drawRightString(table_x + 150, yy - 2, _fmt_int(total))
    c.drawRightString(table_x + 220, yy - 2, "100%")

    if os.path.exists(donut_path):
        c.drawImage(donut_path, x + 58, y - h + 38, width=120, height=82, preserveAspectRatio=True, mask='auto')
        legend_x = x + 205
        legend_y = y - h + 84
        for i, (seg, size, pct, evo) in enumerate(rows):
            c.setFillColor(colors.HexColor(_market_pro_palette(i)))
            c.circle(legend_x, legend_y, 3, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#41556E"))
            c.setFont("Helvetica", 7.4)
            c.drawString(legend_x + 9, legend_y - 2, f"{_pdf_segment_name_es(seg)} ({pct * 100:.1f}%)")
            legend_y -= 14
    note = "Los segmentos muestran dónde está el volumen y qué grupos conviene priorizar en la siguiente ronda."
    _draw_small_note(c, x + 12, y - h + 16, w - 24, 32, note, icon="↗")


def _draw_market_purchase_by_segment(c, x, y, w, h, research, team_name, tmp_dir):
    _draw_panel(c, x, y, w, h, "3. REPARTO DE COMPRA POR SEGMENTO")
    c.setFillColor(colors.HexColor("#3B4A5F"))
    c.setFont("Helvetica", 7.2)
    c.drawString(x + 12, y - 31, "Cuota de cada marca en las compras estimadas de cada segmento.")
    mix = research.get("segment_brand_mix", {}) or {}
    segs = list(mix.keys())[:3]
    chart_w = (w - 42) / 3
    chart_paths = []
    for i, seg in enumerate(segs):
        path = os.path.join(tmp_dir, f"market_seg_{i}.png")
        _save_segment_horizontal_chart(seg, mix.get(seg, {}), team_name, path)
        chart_paths.append(path)
        c.drawImage(path, x + 12 + i * (chart_w + 9), y - 160, width=chart_w, height=112, preserveAspectRatio=True, mask='auto')
    if segs:
        data = _segment_opportunity_data(team_name, research)
        best = max(data, key=lambda r: r["my_val"])
        open_seg = sorted(data, key=lambda r: r["leader_val"])[0]
        note = f"{team_name} destaca más en {_pdf_segment_name_es(best['segment'])}. {_pdf_segment_name_es(open_seg['segment'])} parece el segmento más abierto por liderazgo bajo."
        _draw_small_note(c, x + 12, y - h + 15, w - 24, 34, note, icon="☆")


def _draw_market_working_panel(c, x, y, w, h, team_name, research, event_info):
    _draw_panel(c, x, y, w, h, "4. QUÉ ESTÁ FUNCIONANDO EN EL MERCADO")
    blocks = _market_working_blocks(team_name, research, event_info)
    titles = ["Estrategias ganadoras por segmento", "Factores clave de éxito", "Tendencias relevantes"]
    icons = ["◇", "▥", "↗"]
    fills = ["#ECFDF3", "#EFF6FF", "#F7F2FF"]
    y0 = y - 42
    for idx, (title, lines) in enumerate(zip(titles, blocks)):
        bh = 54
        bx = x + 12
        by = y0 - idx * 62
        c.setFillColor(colors.HexColor(fills[idx]))
        c.setStrokeColor(colors.HexColor(_PRO_BORDER))
        c.roundRect(bx, by - bh, w - 24, bh, 7, fill=1, stroke=1)
        c.setFillColor(colors.HexColor(_market_pro_palette(idx)))
        c.setFont("Helvetica", 17)
        c.drawCentredString(bx + 23, by - 30, icons[idx])
        c.setFillColor(colors.HexColor("#064A90" if idx != 0 else _PRO_GREEN))
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(bx + 48, by - 14, title)
        c.setFillColor(colors.HexColor("#1A2B45"))
        c.setFont("Helvetica", 6.7)
        yy = by - 27
        for line in lines[:3]:
            for wrapped in _split_text("• " + line, max_chars=62)[:2]:
                c.drawString(bx + 48, yy, wrapped)
                yy -= 8


def _draw_market_opportunity_map(c, x, y, w, h, team_name, research):
    _draw_panel(c, x, y, w, h, "5. MAPA DE OPORTUNIDADES")
    data = _segment_opportunity_data(team_name, research)
    tx = x + 12
    ty = y - 42
    headers = ["Segmento", "Tamaño", "Liderazgo", "Compet.", "Oportunidad"]
    colw = [75, 70, 95, 55, 70]
    c.setFillColor(colors.HexColor("#24364B"))
    c.setFont("Helvetica-Bold", 7)
    xx = tx
    for head, cw in zip(headers, colw):
        c.drawString(xx, ty, head)
        xx += cw
    c.setStrokeColor(colors.HexColor(_PRO_BORDER))
    c.line(tx, ty - 8, x + w - 120, ty - 8)
    yy = ty - 27
    for i, r in enumerate(data):
        c.setFillColor(colors.HexColor(_market_pro_palette(i)))
        c.circle(tx + 4, yy + 3, 3, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#1A2B45"))
        c.setFont("Helvetica", 7.2)
        c.drawString(tx + 12, yy, _pdf_segment_name_es(r["segment"]))
        c.drawString(tx + colw[0], yy, f"{_fmt_int(r['size'])}\n"[:12])
        c.drawString(tx + colw[0] + 40, yy, f"({r['pct'] * 100:.1f}%)")
        c.drawString(tx + colw[0] + colw[1], yy, f"{r['leader']} ({r['leader_val'] * 100:.1f}%)"[:18])
        comp_color = _PRO_GREEN if r["competition"] == "Baja" else _PRO_ORANGE if r["competition"] == "Media" else _PRO_RED
        c.setFillColor(colors.HexColor(comp_color))
        c.setFont("Helvetica-Bold", 7.2)
        c.drawString(tx + colw[0] + colw[1] + colw[2], yy, r["competition"])
        opp_color = "#E8F5E9" if r["opportunity"] == "ALTA" else "#FFF3D6" if r["opportunity"] == "MEDIA" else "#FDECEC"
        opp_txt_color = _PRO_GREEN if r["opportunity"] == "ALTA" else _PRO_ORANGE if r["opportunity"] == "MEDIA" else _PRO_RED
        ox = tx + colw[0] + colw[1] + colw[2] + colw[3]
        c.setFillColor(colors.HexColor(opp_color))
        c.roundRect(ox - 5, yy - 8, 64, 18, 4, fill=1, stroke=0)
        c.setFillColor(colors.HexColor(opp_txt_color))
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(ox + 27, yy - 2, r["opportunity"])
        yy -= 28
    # right explanatory box
    bx = x + w - 108
    c.setFillColor(colors.HexColor("#EAF4FF"))
    c.roundRect(bx, y - h + 16, 96, h - 56, 7, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#064A90"))
    c.setFont("Helvetica-Bold", 7.4)
    c.drawString(bx + 10, y - 45, "Claves del mapa:")
    c.setFillColor(colors.HexColor("#1A2B45"))
    c.setFont("Helvetica", 6.5)
    yy = y - 62
    notes = [
        "Segmentos grandes y con liderazgo bajo = mayor oportunidad.",
        "Liderazgo alto indica entrada más difícil.",
        "Tu marca debe priorizar encaje, no solo tamaño."
    ]
    for note in notes:
        for line in _split_text("• " + note, max_chars=24):
            c.drawString(bx + 9, yy, line)
            yy -= 8
        yy -= 4
    # legend
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor(_PRO_BORDER))
    c.roundRect(x + 12, y - h + 18, w - 132, 24, 5, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#1A2B45"))
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 25, y - h + 27, "Nivel de oportunidad:")
    lx = x + 138
    for label, col in [("Alta", _PRO_GREEN), ("Media", _PRO_ORANGE), ("Baja", _PRO_RED)]:
        c.setFillColor(colors.HexColor(col))
        c.circle(lx, y - h + 29, 4, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#1A2B45"))
        c.setFont("Helvetica", 7)
        c.drawString(lx + 8, y - h + 26, label)
        lx += 60


def _draw_market_conclusion_cards(c, x, y, w, h, team_name, research):
    _draw_panel(c, x, y, w, h, "6. CONCLUSIONES Y RECOMENDACIONES")
    good, bad, opp = _market_conclusion_boxes(team_name, research)
    cards = [
        ("LO ESTÁS HACIENDO BIEN", good, _PRO_GREEN, "✓", "Sigue reforzando lo que funciona."),
        ("LO ESTÁS HACIENDO MAL", bad, _PRO_ORANGE, "!", "Ajusta tu enfoque para atacar mejor cada segmento."),
        ("OPORTUNIDADES", opp, _PRO_BLUE_2, "★", "Actúa sobre estos segmentos para crecer."),
    ]
    gap = 10
    cw = (w - 24 - 2 * gap) / 3
    cy = y - 42
    for idx, (title, lines, color_hex, bullet, footer) in enumerate(cards):
        cx = x + 12 + idx * (cw + gap)
        c.setFillColor(colors.HexColor("#F8FBFE"))
        c.setStrokeColor(colors.HexColor(_PRO_BORDER))
        c.roundRect(cx, cy - 112, cw, 112, 8, fill=1, stroke=1)
        c.setFillColor(colors.HexColor(color_hex))
        c.roundRect(cx, cy - 20, cw, 20, 8, fill=1, stroke=0)
        c.rect(cx, cy - 20, cw, 10, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 7.2)
        c.drawCentredString(cx + cw / 2, cy - 13, title)
        yy = cy - 34
        for line in lines[:3]:
            c.setFillColor(colors.HexColor(color_hex))
            c.setFont("Helvetica-Bold", 7.4)
            c.drawString(cx + 11, yy, bullet)
            c.setFillColor(colors.HexColor("#1A2B45"))
            c.setFont("Helvetica", 6.7)
            wrapped = _split_text(line, max_chars=34)[:2]
            for j, l in enumerate(wrapped):
                c.drawString(cx + 24, yy - j * 8, l)
            yy -= 20
        c.setFillColor(colors.HexColor("#EAF7EC" if idx == 0 else "#FFF7E6" if idx == 1 else "#EAF4FF"))
        c.roundRect(cx + 8, cy - 104, cw - 16, 18, 5, fill=1, stroke=0)
        c.setFillColor(colors.HexColor(color_hex))
        c.setFont("Helvetica-Bold", 6.6)
        c.drawCentredString(cx + cw / 2, cy - 98, footer[:48])


def _draw_market_footer(c):
    c.setFillColor(colors.HexColor(_PRO_BLUE))
    c.roundRect(18, 16, PAGE_W - 36, 24, 6, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(38, 26, "RECUERDA:")
    c.setFont("Helvetica", 7.5)
    c.drawString(82, 26, "Entender el mercado es el primer paso para tomar decisiones ganadoras.")


def make_segments_pdf(out_path, round_n, team_name, event_info, research, your_decision, team_truth=None):
    """Genera el Informe de Mercado PRO.

    Mantiene la firma original para que la app no tenga que cambiar nada.
    El diseño está preparado como una página-dashboard similar al mockup validado:
    cabecera, KPIs, estructura de segmentos, reparto de compra, mapa de oportunidades
    y tres cajas finales de diagnóstico.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp_dir = tempfile.mkdtemp()

    research = research or {}
    segment_sizes = research.get("segment_sizes", {}) or {}
    segment_mix = research.get("segment_brand_mix", {}) or {}
    rows, market_total = _calc_segment_rows(research)

    donut_path = os.path.join(tmp_dir, "market_donut.png")
    _save_market_donut_chart(segment_sizes, donut_path)

    c = canvas.Canvas(out_path, pagesize=A4)

    # Página única principal: dashboard completo.
    _draw_market_header(
        c,
        "Informe de mercado",
        "Situación y oportunidades del mercado",
        round_n,
        team_name,
        market_total,
    )

    # 1. Resumen + KPIs
    y_top = PAGE_H - 92
    _draw_panel(c, 18, y_top, PAGE_W - 36, 118, "1. RESUMEN DEL MERCADO")
    summary = _market_summary_text(team_name, research, event_info)
    c.setFillColor(colors.HexColor("#1A2B45"))
    c.setFont("Helvetica-Bold", 8)
    yy = y_top - 39
    for line in _split_text(summary, max_chars=55)[:6]:
        c.drawString(30, yy, line)
        yy -= 11

    # KPIs de mercado
    kpi_x = 205
    kpi_y = y_top - 10
    kpi_w = 70
    kpi_h = 92
    event_label = "Sin evento" if not event_info else str(event_info.get("title", "Evento"))[:18]
    _draw_round_card(c, kpi_x, kpi_y, kpi_w, kpi_h, "Tamaño total del mercado", _fmt_int(market_total), "unidades", _PRO_BLUE, "☷")
    _draw_round_card(c, kpi_x + 78, kpi_y, kpi_w, kpi_h, "Crecimiento del mercado", "—", "vs ronda anterior", _PRO_GREEN, "↗")
    _draw_round_card(c, kpi_x + 156, kpi_y, kpi_w, kpi_h, "Sensibilidad al precio", "Media", "lectura de ronda", _PRO_ORANGE, "⌁")
    _draw_round_card(c, kpi_x + 234, kpi_y, kpi_w, kpi_h, "Sensibilidad a la promoción", "Media", "lectura de ronda", _PRO_ORANGE, "◉")
    _draw_round_card(c, kpi_x + 312, kpi_y, 83, kpi_h, "Evento de la ronda", event_label, "impacto estimado", _PRO_RED if event_info else _PRO_BLUE_2, "⚠")

    # 2 y 3
    mid_y = PAGE_H - 225
    _draw_market_segment_table_and_donut(c, 18, mid_y, 248, 218, research, donut_path)
    _draw_market_purchase_by_segment(c, 274, mid_y, PAGE_W - 292, 218, research, team_name, tmp_dir)

    # 4 y 5
    lower_y = PAGE_H - 455
    _draw_market_working_panel(c, 18, lower_y, 248, 170, team_name, research, event_info)
    _draw_market_opportunity_map(c, 274, lower_y, PAGE_W - 292, 170, team_name, research)

    # 6 conclusiones
    _draw_market_conclusion_cards(c, 18, 200, PAGE_W - 36, 138, team_name, research)
    _draw_market_footer(c)

    # Página 2 opcional: lectura ampliada más limpia, útil si se imprime.
    c.showPage()
    _draw_market_header(
        c,
        "Informe de mercado",
        "Lectura ampliada y detalle de oportunidades",
        round_n,
        team_name,
        market_total,
    )

    insights = _build_segments_report_insights(team_name, research, event_info=event_info)
    _draw_insight_box(c, "Lectura de oportunidad", insights, PAGE_H - 105, fill="#EAF4FF")

    c.setFillColor(colors.HexColor("#064A90"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, PAGE_H - 330, "Mapa de oportunidades detallado")

    data = _segment_opportunity_data(team_name, research)
    headers = ["Segmento", "Tamaño", "% mercado", "Líder", "Competencia", "Oportunidad"]
    table_rows = []
    for r in data:
        table_rows.append([
            _pdf_segment_name_es(r["segment"]),
            _fmt_int(r["size"]),
            f"{r['pct'] * 100:.1f}%",
            f"{r['leader']} ({r['leader_val'] * 100:.1f}%)",
            r["competition"],
            r["opportunity"],
        ])
    _draw_simple_table(c, 40, PAGE_H - 360, headers, table_rows, [80, 70, 60, 120, 80, 80], row_h=22, font_size=8)

    c.setFillColor(colors.HexColor("#F4F8FC"))
    c.roundRect(40, 120, PAGE_W - 80, 125, 8, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#064A90"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, 220, "Cómo usar este informe")
    c.setFillColor(colors.HexColor("#1A2B45"))
    c.setFont("Helvetica", 9)
    guide = [
        "1. Prioriza segmentos con buen tamaño y liderazgo bajo: son zonas con más espacio competitivo.",
        "2. Si ya tienes buen encaje en un segmento, decide si quieres defender posición o crecer en otro grupo.",
        "3. No tomes decisiones solo por volumen: un segmento grande puede estar muy competido.",
        "4. Ajusta precio, comunicación, distribución y producto al tipo de segmento que quieras atacar.",
    ]
    yy = 200
    for line in guide:
        for wrapped in _split_text(line, max_chars=88):
            c.drawString(55, yy, wrapped)
            yy -= 13
    _draw_market_footer(c)

    c.save()


def make_competition_pdf(out_path, round_n, team_name, event_info, research, truth_rows, your_decision, team_truth=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp_dir = tempfile.mkdtemp()

    share_chart_path = os.path.join(tmp_dir, "share_chart.png")
    know_chart_path = os.path.join(tmp_dir, "knowledge_chart.png")

    share_pct = {r["team"]: r["share"] * 100 for r in truth_rows}
    know_pct = {r["team"]: r["awareness_true"] * 100 for r in truth_rows}
    _save_bar_chart(share_pct, "Cuota estimada por marca", "Equipos", share_chart_path)
    _save_bar_chart(know_pct, "Conocimiento estimado por marca", "Equipos", know_chart_path)

    insights = _build_competition_report_insights(team_name, truth_rows)

    c = canvas.Canvas(out_path, pagesize=A4)

    _draw_title(c, "Informe competitivo", f"Equipo: {team_name} | Ronda {round_n}")
    _draw_event_box(c, PAGE_H - 105, event_info)
    y_after = _draw_competition_table(c, truth_rows, team_name, PAGE_H - 190)
    _draw_insight_box(c, "Lectura competitiva", insights, y_after - 12, fill="#EAF4FF")

    c.showPage()
    _draw_title(c, "Informe competitivo", f"Equipo: {team_name} | Ronda {round_n}")
    _draw_section_title(c, "Cuota de mercado", PAGE_H - 110)
    c.drawImage(share_chart_path, 40, 420, width=515, height=250, preserveAspectRatio=True, mask='auto')

    _draw_section_title(c, "Conocimiento de marca", 380)
    c.drawImage(know_chart_path, 40, 120, width=515, height=230, preserveAspectRatio=True, mask='auto')

    c.showPage()
    _draw_title(c, "Informe competitivo", f"Equipo: {team_name} | Ronda {round_n}")
    c.setFillColor(colors.HexColor("#F3F6FA"))
    c.roundRect(40, PAGE_H - 430, PAGE_W - 80, 270, 10, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(55, PAGE_H - 180, "Cómo leer este informe")
    c.setFillColor(colors.black)
    y_text = PAGE_H - 205
    paragraphs = [
        "Este informe no copia exactamente las decisiones de los rivales: ofrece una lectura aproximada de su estrategia de precio, promoción, distribución y comunicación.",
        "La idea es detectar patrones competitivos: quién parece presionar con precio, quién construye más marca, quién empuja distribución y quién está priorizando captación.",
        "La mejor utilidad del informe no es adivinar una cifra exacta, sino identificar la lógica estratégica dominante de cada competidor."
    ]
    for p in paragraphs:
        y_text = _draw_wrapped_text(c, 55, y_text, p, max_chars=88, line_gap=15, font_size=10)
        y_text -= 10

    c.save()


def make_brand_product_pdf(out_path, round_n, team_name, event_info, research, your_decision, team_truth=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp_dir = tempfile.mkdtemp()

    positioning_chart_path = os.path.join(tmp_dir, "positioning_chart.png")
    team_product_chart_path = os.path.join(tmp_dir, "team_product_chart.png")
    team_comm_chart_path = os.path.join(tmp_dir, "team_comm_chart.png")

    _save_positioning_map(research, positioning_chart_path, highlight_team=team_name)
    _save_product_profile_chart_for_team(your_decision, team_truth, team_name, team_product_chart_path)
    _save_comm_mix_chart_for_team(your_decision, team_name, team_comm_chart_path)

    insights = _build_brand_product_report_insights(team_name, research, your_decision, team_truth=team_truth)

    c = canvas.Canvas(out_path, pagesize=A4)

    _draw_title(c, "Informe de marca y producto", f"Equipo: {team_name} | Ronda {round_n}")
    _draw_event_box(c, PAGE_H - 105, event_info)
    y = _draw_brand_product_metrics(c, team_name, research, your_decision, team_truth, PAGE_H - 190)
    _draw_insight_box(c, "Lectura de posicionamiento", insights, y - 8, fill="#FFF5E8")

    _draw_section_title(c, "Mapa calidad-precio", 255)
    c.drawImage(positioning_chart_path, 35, 40, width=525, height=185, preserveAspectRatio=True, mask='auto')

    c.showPage()
    _draw_title(c, "Informe de marca y producto", f"Equipo: {team_name} | Ronda {round_n}")
    _draw_section_title(c, "Perfil estimado del producto", PAGE_H - 110)
    c.drawImage(team_product_chart_path, 40, 360, width=515, height=250, preserveAspectRatio=True, mask='auto')

    _draw_section_title(c, "Mix de comunicación de tu marca", 330)
    c.drawImage(team_comm_chart_path, 40, 70, width=515, height=220, preserveAspectRatio=True, mask='auto')

    c.showPage()
    _draw_title(c, "Informe de marca y producto", f"Equipo: {team_name} | Ronda {round_n}")
    c.setFillColor(colors.HexColor("#F3F6FA"))
    c.roundRect(40, PAGE_H - 430, PAGE_W - 80, 270, 10, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(55, PAGE_H - 180, "Cómo leer este informe")
    c.setFillColor(colors.black)
    y_text = PAGE_H - 205
    paragraphs = [
        "El mapa calidad-precio resume cómo percibe el mercado a tu marca, no solo lo que tú declaras en la decisión.",
        "Los atributos estimados ayudan a entender qué dimensión del producto sobresale más y si eso encaja con el precio que estás defendiendo.",
        "La coherencia estratégica sintetiza si la combinación entre producto, precio, promociones, distribución y comunicación parece razonable desde fuera."
    ]
    for p in paragraphs:
        y_text = _draw_wrapped_text(c, 55, y_text, p, max_chars=88, line_gap=15, font_size=10)
        y_text -= 10

    c.save()


# -------------------------------------------------
# PDF FACILITADOR
# -------------------------------------------------

def make_facilitator_pdf(out_path, round_n, event_info, truth_rows, history, research=None, decisions=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp_dir = tempfile.mkdtemp()

    chart_paths = _make_history_charts(history, tmp_dir)

    segment_chart_path = None
    if research and "segment_brand_mix" in research:
        segment_chart_path = os.path.join(tmp_dir, "fac_segment_mix_chart.png")
        _save_segment_stacked_chart(research["segment_brand_mix"], segment_chart_path)

    share_chart = os.path.join(tmp_dir, "fac_share.png")
    know_chart = os.path.join(tmp_dir, "fac_knowledge.png")
    comm_mix_chart = os.path.join(tmp_dir, "fac_comm_mix.png")
    product_chart = os.path.join(tmp_dir, "fac_product.png")
    positioning_chart = os.path.join(tmp_dir, "fac_positioning.png")

    share_pct = {r["team"]: r["share"] * 100 for r in truth_rows}
    know_pct = {r["team"]: r["awareness_true"] * 100 for r in truth_rows}

    _save_bar_chart(share_pct, "Cuota de mercado (%)", "Equipos", share_chart)
    _save_bar_chart(know_pct, "Conocimiento (%)", "Equipos", know_chart)
    _save_product_profile_chart_all_teams(truth_rows, product_chart)

    if decisions:
        _save_comm_mix_chart_all_teams(decisions, comm_mix_chart)

    if research:
        _save_positioning_map(research, positioning_chart)

    facilitator_insights = _build_facilitator_insights(
        truth_rows=truth_rows,
        research=research,
        decisions=decisions,
        event_info=event_info,
        history=history
    )

    c = canvas.Canvas(out_path, pagesize=A4)

    # Página 1: resultados de la ronda
    _draw_title(c, "Informe del facilitador", f"Resumen de la ronda {round_n}")
    _draw_event_box(c, PAGE_H - 105, event_info)
    _draw_section_title(c, "Resultados de la ronda", PAGE_H - 190)

    truth_sorted = sorted(truth_rows, key=lambda r: r["profit"], reverse=True)

    c.setFillColor(colors.HexColor("#F3F6FA"))
    c.roundRect(22, PAGE_H - 455, 552, 235, 10, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(28, PAGE_H - 245, "Pos.")
    c.drawString(50, PAGE_H - 245, "Equipo")
    c.drawString(108, PAGE_H - 245, "Precio")
    c.drawString(146, PAGE_H - 245, "Com.")
    c.drawString(192, PAGE_H - 245, "Cuota")
    c.drawString(236, PAGE_H - 245, "Ventas")
    c.drawString(292, PAGE_H - 245, "Benef.")
    c.drawString(350, PAGE_H - 245, "Prod.")
    c.drawString(392, PAGE_H - 245, "Nuevos")
    c.drawString(445, PAGE_H - 245, "Ret.%")
    c.drawString(492, PAGE_H - 245, "Conoc.")

    y = PAGE_H - 268
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.black)

    pos = 1
    for r in truth_sorted:
        comm_total = r.get("comm_total", r.get("ad_spend", 0))
        c.drawString(28, y, str(pos))
        c.drawString(50, y, str(r["team"])[:10])
        c.drawString(108, y, f"{r['price']:.2f}")
        c.drawString(146, y, _fmt_int(comm_total))
        c.drawString(192, y, f"{r['share'] * 100:.1f}%")
        c.drawString(236, y, f"{r['units']:.0f}")
        c.drawString(292, y, f"{r['profit']:.0f}")
        c.drawString(350, y, f"{r.get('quality', 0) * 100:.0f}%")
        c.drawString(392, y, f"{r['new_customers']:.0f}")
        c.drawString(445, y, f"{r['retention_rate'] * 100:.1f}%")
        c.drawString(492, y, f"{r['awareness_true'] * 100:.1f}%")
        y -= 22
        pos += 1

    leader = truth_sorted[0]["team"]
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#1F4E79"))
    c.drawString(40, 255, f"Líder de la ronda: {leader}")

    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    c.drawString(40, 233, "Este informe muestra resultados reales del mercado y evolución histórica.")

    if research and "segment_sizes" in research:
        _draw_segment_sizes_block(c, research, 205)

    # Página 2: insights del facilitador
    c.showPage()
    _draw_title(c, "Lectura rápida de la ronda", f"Ronda {round_n}")
    _draw_insight_box(c, "Insights automáticos del facilitador", facilitator_insights, PAGE_H - 110, fill="#EAF4FF")

    # Página 3: decisiones de empresas
    if decisions:
        c.showPage()
        _draw_title(c, "Decisiones de la ronda", f"Ronda {round_n}")
        _draw_facilitator_decisions_table(c, decisions, y_start=PAGE_H - 110)

    # Página 4: cuota y conocimiento
    c.showPage()
    _draw_title(c, "Resultados clave", f"Ronda {round_n}")

    _draw_section_title(c, "Cuota de mercado", PAGE_H - 110)
    c.drawImage(share_chart, 40, 420, width=515, height=250, preserveAspectRatio=True, mask='auto')

    _draw_section_title(c, "Conocimiento", 380)
    c.drawImage(know_chart, 40, 110, width=515, height=250, preserveAspectRatio=True, mask='auto')

    # Página 5: comunicación
    if decisions:
        c.showPage()
        _draw_title(c, "Comunicación y posicionamiento táctico", f"Ronda {round_n}")
        _draw_section_title(c, "Mix de comunicación por empresa", PAGE_H - 110)
        c.drawImage(comm_mix_chart, 35, 220, width=525, height=360, preserveAspectRatio=True, mask='auto')

    # Página 6: producto
    c.showPage()
    _draw_title(c, "Producto y propuesta de valor", f"Ronda {round_n}")
    _draw_section_title(c, "Índice global de producto por empresa", PAGE_H - 110)
    c.drawImage(product_chart, 35, 250, width=525, height=330, preserveAspectRatio=True, mask='auto')

    c.setFillColor(colors.HexColor("#F3F6FA"))
    c.roundRect(40, 110, 515, 100, 10, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#16324F"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, 185, "Lectura rápida")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(55, 165, "El índice global de producto resume rendimiento, diseño y fiabilidad.")
    c.drawString(55, 149, "No indica el mismo encaje en todos los segmentos: cada segmento valora atributos distintos.")
    c.drawString(55, 133, "Úsalo como referencia comparativa, no como una verdad única sobre posicionamiento.")

    # Página 7: posicionamiento
    if research:
        c.showPage()
        _draw_title(c, "Mapa de posicionamiento", f"Ronda {round_n}")
        _draw_section_title(c, "Posicionamiento de las marcas en precio y calidad", PAGE_H - 110)
        c.drawImage(positioning_chart, 35, 220, width=525, height=340, preserveAspectRatio=True, mask='auto')

        c.setFillColor(colors.HexColor("#F3F6FA"))
        c.roundRect(40, 95, 515, 90, 10, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(55, 160, "El eje horizontal representa el precio observado en el mercado.")
        c.drawString(55, 144, "El eje vertical representa la calidad estimada percibida por el mercado.")
        c.drawString(55, 128, "Una posición premium coherente combina mayor precio con mayor calidad percibida.")
        c.drawString(55, 112, "Una posición de valor combina precio contenido con una calidad competitiva.")

    # Página 8: compra por segmento
    if research and "segment_brand_mix" in research:
        c.showPage()
        _draw_title(c, "Compra por segmento", f"Ronda {round_n}")
        _draw_section_title(c, "Compra por segmento de cada grupo", PAGE_H - 110)
        c.drawImage(segment_chart_path, 35, 360, width=525, height=250, preserveAspectRatio=True, mask='auto')
        _draw_segment_mix_table(c, research, y_start=320)

    # Páginas de gráficos históricos
    for path in chart_paths:
        c.showPage()
        _draw_title(c, "Evolución del mercado", f"Ronda {round_n}")
        c.drawImage(path, 35, 170, width=525, height=330, preserveAspectRatio=True, mask='auto')

    c.save()