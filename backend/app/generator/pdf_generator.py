import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

NAVY        = colors.HexColor("#003366")
LIGHT_BLUE  = colors.HexColor("#E8EEF4")
MID_GRAY    = colors.HexColor("#888888")
DARK_GRAY   = colors.HexColor("#333333")
WHITE       = colors.white
COLOR_BUY   = colors.HexColor("#1a7a1a")   
COLOR_HOLD  = colors.HexColor("#b8860b")   
COLOR_SELL  = colors.HexColor("#cc2200")   

PAGE_W, PAGE_H = A4
L_MARGIN = R_MARGIN = 12 * mm
T_MARGIN = B_MARGIN = 10 * mm
CONTENT_W = PAGE_W - L_MARGIN - R_MARGIN

def _style(name, **kwargs):
    defaults = dict(fontName="Helvetica", fontSize=8, leading=10, textColor=DARK_GRAY)
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)

S_HEADER_COMPANY = _style("hdr_co", fontName="Helvetica-Bold", fontSize=14, textColor=WHITE)
S_HEADER_SMALL   = _style("hdr_sm", fontSize=7, textColor=colors.HexColor("#CCDDEE"))
S_SECTION        = _style("section", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE)
S_BODY           = _style("body", fontSize=7.5, leading=11)
S_BULLET         = _style("bullet", fontSize=7.5, leading=11, leftIndent=8)
S_TABLE_CELL     = _style("tbl_c", fontSize=7, leading=9, alignment=TA_RIGHT)
S_TABLE_LABEL    = _style("tbl_l", fontSize=7, leading=9)
S_SMALL          = _style("small", fontSize=6, textColor=MID_GRAY, leading=8)
S_TITLE          = _style("title", fontName="Helvetica-Bold", fontSize=9, textColor=NAVY)


def val(v, suffix="", prefix="", na="—"):
    if v is None:
        return na
    s = str(v).strip().lstrip("'\"")
    if not s:
        return na
    return f"{prefix}{s}{suffix}"


def _is_banking(data: dict) -> bool:
    sector = (data.get("sector") or "").lower()
    name   = (data.get("company_name") or "").lower()
    if data.get("_is_banking"):
        return True
    return any(k in sector or k in name for k in ["bank", "financial", "nbfc", "insurance"])


def _rating_color(rating: str):
    r = (rating or "").upper()
    if r == "BUY":
        return COLOR_BUY
    if r == "SELL":
        return COLOR_SELL
    return COLOR_HOLD   


def _section_label(text: str) -> Table:
    t = Table([[Paragraph(text, S_SECTION)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
    ]))
    return t


def _base_table_style():
    return [
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7),
        ("BACKGROUND",    (0, 1), (-1, -1), WHITE),        # default white
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("ALIGN",         (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN",         (0, 0), (0, -1),  "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),  # ← add this
    ]


def _make_image(fig) -> Image:
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=85*mm, height=48*mm)


def _revenue_chart(financials: list, label="Revenue (Rs. Cr)") -> Image:
    years = [r.get("year", "") for r in financials]
    sales = [r.get("sales") or 0 for r in financials]
    fig, ax = plt.subplots(figsize=(3.2, 1.8))
    bars = ax.bar(years, sales, color="#003366", width=0.5)
    ax.set_title(label, fontsize=7, pad=4)
    ax.tick_params(axis='both', labelsize=6)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.spines[['top', 'right']].set_visible(False)
    mx = max(sales) if sales else 1
    for bar, s in zip(bars, sales):
        if s:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + mx * 0.01,
                    f"{int(s):,}", ha='center', va='bottom', fontsize=5)
    plt.tight_layout(pad=0.3)
    return _make_image(fig)


def _margin_chart(financials: list, label="EBITDA Margin (%)") -> Image:
    years   = [r.get("year", "") for r in financials]
    margins = [r.get("ebitda_margin") or 0 for r in financials]
    fig, ax = plt.subplots(figsize=(3.2, 1.8))
    ax.plot(years, margins, marker="o", color="#CC6600", linewidth=1.5, markersize=4)
    ax.fill_between(range(len(years)), margins, alpha=0.15, color="#CC6600")
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years)
    ax.set_title(label, fontsize=7, pad=4)
    ax.tick_params(axis='both', labelsize=6)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    ax.spines[['top', 'right']].set_visible(False)
    mx = max(margins) if max(margins) > 0 else 1
    for i, (_, m) in enumerate(zip(years, margins)):
        ax.text(i, m + mx * 0.04, f"{m:.1f}%", ha='center', fontsize=5)
    plt.tight_layout(pad=0.3)
    return _make_image(fig)


def _pat_chart(financials: list) -> Image:
    years = [r.get("year", "") for r in financials]
    pats  = [r.get("pat") or 0 for r in financials]
    fig, ax = plt.subplots(figsize=(3.2, 1.8))
    bar_colors = ["#006600" if p >= 0 else "#CC0000" for p in pats]
    bars = ax.bar(years, pats, color=bar_colors, width=0.5)
    ax.set_title("PAT (Rs. Cr)", fontsize=7, pad=4)
    ax.tick_params(axis='both', labelsize=6)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.spines[['top', 'right']].set_visible(False)
    mx = max(pats) if pats else 1
    for bar, p in zip(bars, pats):
        if p:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + mx * 0.01,
                    f"{int(p):,}", ha='center', va='bottom', fontsize=5)
    plt.tight_layout(pad=0.3)
    return _make_image(fig)


def _quarterly_bar_chart(qf: dict, field: str, label: str) -> Image:
    v_yoy    = qf.get(f"{field}_yoy") or 0
    v_latest = qf.get(field) or 0
    fig, ax = plt.subplots(figsize=(3.2, 1.8))
    bars = ax.bar(["Prior Year Q", "Latest Q"], [v_yoy, v_latest],
                  color=["#AAAAAA", "#003366"], width=0.4)
    ax.set_title(label, fontsize=7, pad=4)
    ax.tick_params(axis='both', labelsize=6)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.spines[['top', 'right']].set_visible(False)
    for bar, v in zip(bars, [v_yoy, v_latest]):
        if v:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f"{int(v):,}", ha='center', va='bottom', fontsize=5)
    plt.tight_layout(pad=0.3)
    return _make_image(fig)


def _two_charts(c1, c2, story):
    t = Table([[c1, c2]], colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5])
    t.setStyle(TableStyle([
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)

def _has_real_financials(financials):
    if not financials:
        return False

    for row in financials:
        if (
            row.get("sales") is not None
            or row.get("ebitda") is not None
            or row.get("pat") is not None
        ):
            return True

    return False

def _build_page1(data: dict, story: list):
    banking  = _is_banking(data)
    company  = val(data.get("company_name"), na="Company Name")
    sector   = val(data.get("sector"))
    rating   = (data.get("rating") or "").upper()
    cmp_     = val(data.get("cmp"), prefix="Rs. ")
    target   = val(data.get("target_price"), prefix="Rs. ")
    date_    = val(data.get("report_date"))
    tf       = val(data.get("time_frame"), na="12 Months")
    headline = val(data.get("headline"), na="")
    ret_raw  = data.get("return_pct")
    ret_str  = f"Return {'+' if (ret_raw or 0) >= 0 else ''}{ret_raw}%" if ret_raw is not None else "—"

    badge_color = _rating_color(rating)
    rating_text = rating if rating else "—"

    hdr_data = [
        [
            Paragraph("Retail Equity Research",
                      _style("re", fontSize=7, textColor=colors.HexColor("#AACCEE"))),
            Paragraph(f"Target  {target}",
                      _style("tgt", fontName="Helvetica-Bold", fontSize=10,
                             textColor=WHITE, alignment=TA_RIGHT)),
        ],
        [
            Paragraph(f"<b>{company}</b>", S_HEADER_COMPANY),
            Paragraph(f"CMP  {cmp_}",
                      _style("cmp", fontName="Helvetica-Bold", fontSize=10,
                             textColor=colors.HexColor("#FFDD99"), alignment=TA_RIGHT)),
        ],
        [
            Paragraph(f"Sector: {sector}    {date_}", S_HEADER_SMALL),
           
            Paragraph(f"<b>{rating_text}</b>",
                      _style("rat", fontName="Helvetica-Bold", fontSize=14,
                             textColor=WHITE, alignment=TA_RIGHT, backColor=badge_color)),
        ],
    ]
    hdr_table = Table(hdr_data, colWidths=[CONTENT_W * 0.6, CONTENT_W * 0.4])
    hdr_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("BACKGROUND",    (1, 2), (1, 2),   badge_color),  
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(hdr_table)

    sub_data = [[
        val(data.get("stock_type"), na="Large Cap"),
        val(data.get("bloomberg_code")),
        val(data.get("sensex")),
        val(data.get("nse_code")),
        val(data.get("bse_code")),
        tf, ret_str,
    ]]
    sub_labels = [["Stock Type", "Bloomberg Code", "Sensex", "NSE Code", "BSE Code", "Time Frame", "Return"]]
    sub_table = Table(sub_labels + sub_data, colWidths=[CONTENT_W / 7] * 7)
    sub_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#002244")),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.HexColor("#AACCEE")),
        ("BACKGROUND",    (0, 1), (-1, 1), LIGHT_BLUE),
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 6.5),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 2 * mm))

    if headline:
        story.append(Paragraph(f"<i>{headline}</i>",
                               _style("hl", fontSize=8, textColor=NAVY,
                                      fontName="Helvetica-BoldOblique")))
        story.append(Spacer(1, 2 * mm))

    left_col  = []
    right_col = []

    left_col.append(_section_label("Company Data"))
    co_candidates = [
        ("Market Cap (Rs.cr)",       data.get("market_cap")),
        ("52W High — Low (Rs.)",     f"{val(data.get('week_52_high'))} — {val(data.get('week_52_low'))}"
                                     if data.get("week_52_high") or data.get("week_52_low") else None),
        ("Enterprise Value (Rs.cr)", data.get("ev")),
        ("Outstanding Shares (cr)",  data.get("outstanding_shares")),
        ("Free Float (%)",           data.get("free_float")),
        ("Dividend Yield (%)",       data.get("dividend_yield")),
        ("6m Avg Volume (cr)",       data.get("avg_volume_6m")),
        ("Beta",                     data.get("beta")),
        ("Face value (Rs.)",         data.get("face_value")),
    ]
    co_rows = [
        [Paragraph(k, S_TABLE_LABEL), Paragraph(str(v), S_TABLE_CELL)]
        for k, v in co_candidates if v not in [None, "", "—", "— —"]
    ]
    if not co_rows:
        co_rows = [[Paragraph("Data not available in source document", S_TABLE_LABEL),
                    Paragraph("", S_TABLE_CELL)]]

    co_table = Table(co_rows, colWidths=[CONTENT_W * 0.22, CONTENT_W * 0.13])
    co_table.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_BLUE]),
        ("FONTSIZE",       (0, 0), (-1, -1), 7),
        ("TOPPADDING",     (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING",    (0, 0), (0, -1),  4),
        ("GRID",           (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("ALIGN",          (1, 0), (1, -1),  "RIGHT"),
    ]))
    left_col.append(co_table)
    left_col.append(Spacer(1, 2 * mm))

    sh = data.get("shareholding") or []
    if sh:
        periods   = [s.get("period", "") for s in sh[-3:]]
        sh_header = ["Shareholding (%)"] + periods
        sh_rows   = [
            ["Promoters"] + [val(s.get("promoters")) for s in sh[-3:]],
            ["FII's"]     + [val(s.get("fii"))       for s in sh[-3:]],
            ["MFs/Inst."] + [val(s.get("mf"))        for s in sh[-3:]],
            ["Public"]    + [val(s.get("public"))     for s in sh[-3:]],
            ["Others"]    + [val(s.get("others"))     for s in sh[-3:]],
            ["Total"]     + [val(s.get("total"), na="100.0") for s in sh[-3:]],
        ]
        # Shareholding:
        cw = (CONTENT_W * 0.37 - CONTENT_W * 0.145) / 3

        sh_table = Table([sh_header] + sh_rows, colWidths=[CONTENT_W * 0.145, cw, cw, cw])
        sh_table.setStyle(TableStyle(_base_table_style()))
        left_col.append(_section_label("Shareholding (%)"))
        left_col.append(sh_table)
        left_col.append(Spacer(1, 2 * mm))

    pp = data.get("price_performance") or {}
    pp_header = ["Price Performance", "3M", "6M", "1Y"]
    pp_rows   = [
        ["Absolute Return", val(pp.get("abs_3m")),    val(pp.get("abs_6m")),    val(pp.get("abs_1y"))],
        ["Abs. Sensex",     val(pp.get("sensex_3m")), val(pp.get("sensex_6m")), val(pp.get("sensex_1y"))],
        ["Relative Return", val(pp.get("rel_3m")),    val(pp.get("rel_6m")),    val(pp.get("rel_1y"))],
    ]
    # Price Performance:
    cw2      = (CONTENT_W * 0.37 - CONTENT_W * 0.145) / 3

    pp_table = Table([pp_header] + pp_rows, colWidths=[CONTENT_W * 0.145, cw2, cw2, cw2])
    pp_table.setStyle(TableStyle(_base_table_style()))
    left_col.append(_section_label("Price Performance"))
    left_col.append(pp_table)

    highlights = data.get("highlights") or []
    right_col.append(_section_label("Key Highlights"))
    right_col.append(Spacer(1, 1 * mm))
    for h in highlights[:6]:
        right_col.append(Paragraph(f"• {h}", S_BULLET))
        right_col.append(Spacer(1, 1 * mm))

    strengths = data.get("strengths") or []
    risks     = data.get("risks") or []
    if strengths or risks:
        right_col.append(Spacer(1, 2 * mm))
        right_col.append(_section_label("Analyst View"))
        right_col.append(Spacer(1, 1 * mm))

        if strengths:
            right_col.append(Paragraph(
                "<b>Key Strengths</b>",
                _style("ksh", fontSize=7.5, fontName="Helvetica-Bold", textColor=COLOR_BUY)
            ))
            for s in strengths:
                right_col.append(Paragraph(f"✓  {s}", _style("sr", fontSize=7, leading=10, textColor=DARK_GRAY, leftIndent=6)))
            right_col.append(Spacer(1, 1.5 * mm))

        if risks:
            right_col.append(Paragraph(
                "<b>Key Risks</b>",
                _style("kri", fontSize=7.5, fontName="Helvetica-Bold", textColor=COLOR_SELL)
            ))
            for r in risks:
                right_col.append(Paragraph(f"-  {r}", _style("rr", fontSize=7, leading=10, textColor=DARK_GRAY, leftIndent=6)))
            right_col.append(Spacer(1, 1 * mm))

    outlook = data.get("outlook") or ""
    right_col.append(Spacer(1, 2 * mm))
    right_col.append(_section_label("Outlook & Valuation"))
    right_col.append(Spacer(1, 1 * mm))
    right_col.append(Paragraph(outlook or "—", S_BODY))
    right_col.append(Spacer(1, 2 * mm))

    sales_lbl  = "Net Interest Inc." if banking else "Sales"
    ebitda_lbl = "Core Op. Profit"   if banking else "EBITDA"
    margin_lbl = "NIM (%)"           if banking else "EBITDA Margin"

    fin = data.get("financials") or []
    if _has_real_financials(fin):
        years      = [r.get("year", "") for r in fin]
        fin_header = ["Y.E March (cr)"] + years
        fin_rows   = [
            [sales_lbl]    + [val(r.get("sales"))         for r in fin],
            ["Growth (%)"] + [val(r.get("sales_growth"))  for r in fin],
            [ebitda_lbl]   + [val(r.get("ebitda"))        for r in fin],
            [margin_lbl]   + [val(r.get("ebitda_margin")) for r in fin],
            ["PAT Adj."]   + [val(r.get("pat"))           for r in fin],
            ["Growth (%)"] + [val(r.get("pat_growth"))    for r in fin],
            ["Adj. EPS"]   + [val(r.get("eps"))           for r in fin],
            ["P/E"]        + [val(r.get("pe"))            for r in fin],
            ["EV/EBITDA"]  + [val(r.get("ev_ebitda"))     for r in fin],
            ["ROE (%)"]    + [val(r.get("roe"))           for r in fin],
        ]
        ncols   = len(fin_header)
        fw      = (CONTENT_W * 0.62) / ncols
        f_table = Table([fin_header] + fin_rows,
                        colWidths=[CONTENT_W * 0.62 - fw * (ncols - 1)] + [fw] * (ncols - 1))
        f_table.setStyle(TableStyle(_base_table_style()))
        right_col.append(f_table)
        right_col.append(Spacer(1, 2 * mm))

    qf = data.get("quarterly_financials") or []
    if qf:
        q        = qf[0]
        q_header = ["Rs.cr", "Q(Latest)", "Q(YoY)", "YoY Gr%", "Q(QoQ)", "QoQ Gr%"]
        q_rows   = [
            [sales_lbl]  + [val(q.get(k)) for k in ["sales",  "sales_yoy",  "sales_yoy_gr",  "sales_qoq",  "sales_qoq_gr"]],
            [ebitda_lbl] + [val(q.get(k)) for k in ["ebitda", "ebitda_yoy", "ebitda_yoy_gr", "ebitda_qoq", "ebitda_qoq_gr"]],
            ["PAT"]      + [val(q.get(k)) for k in ["pat",    "pat_yoy",    "pat_yoy_gr",    "pat_qoq",    "pat_qoq_gr"]],
        ]
        qw      = (CONTENT_W * 0.62) / 6
        q_table = Table([q_header] + q_rows, colWidths=[qw] * 6)
        q_table.setStyle(TableStyle(_base_table_style()))
        right_col.append(_section_label("Quarterly Financials"))
        right_col.append(q_table)

    left_inner  = Table([[c] for c in left_col],  colWidths=[CONTENT_W * 0.37])
    right_inner = Table([[c] for c in right_col], colWidths=[CONTENT_W * 0.62])
    left_inner.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),1)]))
    right_inner.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),1)]))

    two_col = Table([[left_inner, right_inner]], colWidths=[CONTENT_W * 0.37, CONTENT_W * 0.63])
    two_col.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(two_col)


def _build_page2(data: dict, story: list):
    story.append(PageBreak())
    story.append(_section_label("Financial Charts"))
    story.append(Spacer(1, 3 * mm))

    banking = _is_banking(data)
    fin     = data.get("financials") or []
    qf      = data.get("quarterly_financials") or []

    if _has_real_financials(fin):
        rev_label    = "Net Interest Income (Rs. Cr)" if banking else "Revenue (Rs. Cr)"
        margin_label = "NIM (%)" if banking else "EBITDA Margin (%)"
        _two_charts(_revenue_chart(fin, rev_label), _margin_chart(fin, margin_label), story)
        story.append(Spacer(1, 4 * mm))
        story.append(_section_label("PAT Trend"))
        story.append(Spacer(1, 3 * mm))
        story.append(_pat_chart(fin))

    elif qf:
        q         = qf[0]
        rev_label = "NII — Quarterly (Rs. Cr)" if banking else "Revenue — Quarterly (Rs. Cr)"
        _two_charts(
            _quarterly_bar_chart(q, "sales",  rev_label),
            _quarterly_bar_chart(q, "ebitda", "EBITDA — Quarterly (Rs. Cr)"),
            story
        )
        story.append(Spacer(1, 4 * mm))
        story.append(_section_label("PAT — Quarterly Comparison"))
        story.append(Spacer(1, 3 * mm))
        story.append(_quarterly_bar_chart(q, "pat", "PAT — Quarterly (Rs. Cr)"))
    else:
        story.append(Paragraph("No financial data available for charts.", S_BODY))

    highlights = data.get("highlights") or []
    if len(highlights) > 6:
        story.append(Spacer(1, 4 * mm))
        story.append(_section_label("Additional Highlights"))
        story.append(Spacer(1, 2 * mm))
        for h in highlights[6:]:
            story.append(Paragraph(f"• {h}", S_BULLET))
            story.append(Spacer(1, 1 * mm))


def _build_page3(data: dict, story: list):
    story.append(PageBreak())
    story.append(_section_label("Consolidated Financials"))
    story.append(Spacer(1, 2 * mm))

    banking = _is_banking(data)
    fin     = data.get("financials") or []
    qf      = data.get("quarterly_financials") or []

    if _has_real_financials(fin):
        years   = [r.get("year", "") for r in fin]
        yr_cols = len(years)

        def fin_table(title, rows, col_w_label=55 * mm):
            cw     = (CONTENT_W - col_w_label) / yr_cols
            header = [
                Paragraph(title, _style("fth", fontName="Helvetica-Bold", fontSize=7, textColor=WHITE))
            ] + [
                Paragraph(y, _style("fty", fontSize=7, textColor=WHITE, alignment=TA_CENTER))
                for y in years
            ]
            body = []
            for lbl, key in rows:
                row = [Paragraph(lbl, S_TABLE_LABEL)]
                for r in fin:
                    v = val(r.get(key))
                    # Ensure it's never an empty string that ReportLab misreads
                    row.append(Paragraph(v if v else "—", S_TABLE_CELL))
                body.append(row)
            t = Table([header] + body, colWidths=[col_w_label] + [cw] * yr_cols)
            t.setStyle(TableStyle(_base_table_style()))
            return t

        sales_lbl  = "Net Interest Inc." if banking else "Sales"
        ebitda_lbl = "Core Op. Profit"   if banking else "EBITDA"

        pl_rows = [
            (sales_lbl,       "sales"),
            ("% change",      "sales_growth"),
            (ebitda_lbl,      "ebitda"),
            ("% change",      "ebitda_growth"),
            ("Depreciation",  "depreciation"),
            ("EBIT",          "ebit"),
            ("Interest",      "interest"),
            ("Other Income",  "other_income"),
            ("PBT",           "pbt"),
            ("Tax",           "tax"),
            ("Reported PAT",  "pat"),
            ("Adj. PAT",      "adj_pat"),
            ("Adj EPS (Rs.)", "eps"),
        ]
        story.append(fin_table("Profit & Loss  (Y.E March, Rs. Cr)", pl_rows))
        story.append(Spacer(1, 3 * mm))

        margin_lbl = "NIM (%)" if banking else "EBITDA margin (%)"
        ratio_rows = [
            (margin_lbl,           "ebitda_margin"),
            ("Net profit mgn.(%)", "net_margin"),
            ("ROE (%)",            "roe"),
            ("ROCE (%)",           "roce"),
            ("P/E (x)",            "pe"),
            ("P/BV (x)",           "pb"),
            ("EV/EBITDA (x)",      "ev_ebitda"),
            ("EV/Sales (x)",       "ev_sales"),
            ("D/E",                "de"),
        ]
        story.append(fin_table("Key Ratios  (Y.E March)", ratio_rows))

    elif qf:
        story.append(_section_label("Quarterly Performance"))
        story.append(Spacer(1, 2 * mm))
        sales_lbl  = "Net Interest Inc." if banking else "Revenue (Rs.Cr)"
        ebitda_lbl = "Core Op. Profit"   if banking else "EBITDA (Rs.Cr)"
        q          = qf[0]
        q_header   = ["Metric", "Latest Quarter", "Prior Year Qtr", "YoY Growth"]
        q_rows     = [
            [sales_lbl,  val(q.get("sales")),  val(q.get("sales_yoy")),  val(q.get("sales_yoy_gr"))],
            [ebitda_lbl, val(q.get("ebitda")), "—",                       val(q.get("ebitda_yoy_gr"))],
            ["PAT",      val(q.get("pat")),    "—",                       val(q.get("pat_yoy_gr"))],
        ]
        cw      = CONTENT_W / 4
        q_table = Table([q_header] + q_rows, colWidths=[cw] * 4)
        q_table.setStyle(TableStyle(_base_table_style()))
        story.append(q_table)
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            "Note: Annual financials not available in source document. Quarterly data shown above.",
            S_SMALL
        ))
    else:
        story.append(Paragraph("No detailed financial data available.", S_BODY))


def _build_page4(data: dict, story: list):
    story.append(PageBreak())

    rec = data.get("recommendation_history") or []

    if rec:
        story.append(_section_label("Recommendation Summary (last 3 years)"))
        story.append(Spacer(1, 2 * mm))
        rec_header = ["Date", "Rating", "Target"]
        rec_rows   = [[val(r.get("date")), val(r.get("rating")), val(r.get("target"))] for r in rec]
        rec_table  = Table([rec_header] + rec_rows,
                           colWidths=[CONTENT_W * 0.25, CONTENT_W * 0.25, CONTENT_W * 0.25])
        rec_table.setStyle(TableStyle(_base_table_style() + [("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(rec_table)
        story.append(Spacer(1, 5 * mm))

    strengths = data.get("strengths") or []
    risks     = data.get("risks") or []
    fin       = data.get("financials") or []
    qf        = data.get("quarterly_financials") or []

    if strengths or risks:
        story.append(_section_label("Investment Thesis"))
        story.append(Spacer(1, 2 * mm))

        thesis_rows = []
        if strengths:
            thesis_rows.append([
                Paragraph("<b>Key Strengths</b>",
                          _style("ths", fontName="Helvetica-Bold", fontSize=7.5, textColor=COLOR_BUY)),
                Paragraph("", S_BODY)
            ])
            for s in strengths:
                thesis_rows.append([
                    Paragraph(f"&#10003; {s}", _style("tsi", fontSize=7.5, textColor=COLOR_BUY, leftIndent=4)),
                    Paragraph("", S_BODY)
                ])

        if risks:
            thesis_rows.append([Paragraph("", S_BODY), Paragraph("", S_BODY)])
            thesis_rows.append([
                Paragraph("<b>Key Risks</b>",
                          _style("thr", fontName="Helvetica-Bold", fontSize=7.5, textColor=COLOR_SELL)),
                Paragraph("", S_BODY)
            ])
            for r in risks:
                thesis_rows.append([
                    Paragraph(f"-  {r}", _style("tri", fontSize=7.5, textColor=COLOR_SELL, leftIndent=4)),
                    Paragraph("", S_BODY)
                ])

        if thesis_rows:
            tt = Table(thesis_rows, colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5])
            tt.setStyle(TableStyle([
                ("TOPPADDING",    (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING",   (0, 0), (-1, -1), 4),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(tt)
        story.append(Spacer(1, 5 * mm))

    if not rec:
        story.append(_section_label("Key Metrics Summary"))
        story.append(Spacer(1, 2 * mm))
        summary = []
        if _has_real_financials(fin):
            latest  = fin[-1]
            summary += [
                ["Year",                        val(latest.get("year"))],
                ["Revenue (Rs.Cr)",              val(latest.get("sales"))],
                ["EBITDA / Op. Profit (Rs.Cr)",  val(latest.get("ebitda"))],
                ["PAT (Rs.Cr)",                  val(latest.get("pat"))],
                ["EPS (Rs.)",                    val(latest.get("eps"))],
                ["ROE (%)",                      val(latest.get("roe"))],
                ["EBITDA / NIM (%)",             val(latest.get("ebitda_margin"))],
            ]
        if qf:
            q        = qf[0]
            summary += [
                ["Latest Qtr Revenue",   val(q.get("sales"))],
                ["Revenue YoY Growth",   val(q.get("sales_yoy_gr"))],
                ["EBITDA YoY Growth",    val(q.get("ebitda_yoy_gr"))],
                ["PAT YoY Growth",       val(q.get("pat_yoy_gr"))],
            ]
        if summary:
            t = Table(summary, colWidths=[CONTENT_W * 0.4, CONTENT_W * 0.3])
            t.setStyle(TableStyle(_base_table_style()))
            story.append(t)
        story.append(Spacer(1, 5 * mm))

    story.append(_section_label("Investment Rating Criteria"))
    story.append(Spacer(1, 2 * mm))
    crit_header = ["Ratings", "Large caps", "Midcaps", "Small Caps"]
    crit_rows   = [
        ["Buy",         "Upside > 10%",  "Upside > 15%",  "Upside > 20%"],
        ["Hold",        "Upside 0-10%",  "Upside 0-10%",  "Upside 0-10%"],
        ["Reduce/Sell", "Downside > 0%", "Downside > 0%", "Downside > 0%"],
    ]
    crit_table = Table([crit_header] + crit_rows, colWidths=[CONTENT_W * 0.2] * 4)
    crit_style = _base_table_style() + [
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#e8f5e9")),   # Buy row green tint
        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#fff8e1")),   # Hold row amber tint
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#ffebee")),   # Sell row red tint
    ]
    crit_table.setStyle(TableStyle(crit_style))
    story.append(crit_table)

    story.append(Spacer(1, 5 * mm))
    story.append(HRFlowable(width=CONTENT_W, thickness=0.5, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("DISCLAIMER & DISCLOSURES", S_TITLE))
    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph(
        "This report has been prepared for information purposes only and does not constitute "
        "an offer or solicitation to buy or sell any securities. The information contained herein "
        "is based on sources believed to be reliable but is not guaranteed as to accuracy or "
        "completeness. Investment in securities markets is subject to market risks. Read all "
        "related documents carefully before investing. Past performance is not indicative of "
        "future results. The recommendations are based on a 12-month horizon unless otherwise specified.",
        S_SMALL
    ))

def generate_pdf(data: dict) -> bytes:
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=L_MARGIN, rightMargin=R_MARGIN,
        topMargin=T_MARGIN,  bottomMargin=B_MARGIN,
    )
    story = []
    _build_page1(data, story)
    _build_page2(data, story)
    _build_page3(data, story)
    _build_page4(data, story)
    doc.build(story)
    return buffer.getvalue()