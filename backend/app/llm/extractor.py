import os
import json
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return text.strip()


def _is_banking(company_name: str, sector: str) -> bool:
    keywords = ["bank", "financial", "nbfc", "insurance", "lending"]
    combined = f"{company_name} {sector}".lower()
    return any(k in combined for k in keywords)


def extract_fields(company_name: str, text_context: str) -> dict:
    prompt = f"""
You are a senior equity research analyst. Extract financial data from the document below for {company_name}.

Return ONLY valid JSON. No markdown, no explanation, no code fences.

Rules:
1. All monetary values must be in Rs. Crores. Convert if needed (1 billion = 100 crores, 1 million = 0.1 crores).
2. Extract ALL years of financials available (FY23A, FY24A, FY25A, FY26E, FY27E etc).
3. Rating Rules: If a rating is explicitly stated in the document, use it.

Otherwise infer:

BUY:
- Strong revenue/profit growth
- Improving margins
- Positive outlook
- Strong balance sheet or capital position

HOLD:
- Stable performance
- Mixed indicators
- Moderate growth

SELL:
- Weak growth
- Declining profitability
- Negative outlook

If insufficient evidence exists, return null.

Also return:

"rating_confidence": number between 0 and 100

Higher confidence requires multiple supporting indicators from the document.
4. HEADLINE EXTRACTION RULES

Extract the primary research headline.

Priority:

1. A descriptive sentence summarizing company performance.

Examples:
- "ICICI Bank reports steady credit growth and stable asset quality in Q2-2026"
- "JSW Energy reports strong operational growth in Q2 FY26"

2. If no descriptive headline exists, use the main report title.

Do NOT use generic titles such as:
- Investor Presentation
- Earnings Presentation
- Results Presentation
- Corporate Presentation
- Conference Call
- Quarterly Results

Prefer the most informative business headline available.

5. Quarterly Financial Rules: For fields ending in "_yoy" and "_qoq":

Only extract the comparison-period value.

Do NOT extract:
- absolute change
- increase amount
- decrease amount

Example:

Current Quarter Revenue = 21529
YoY Growth = 7.4%

Then:

sales = 21529

sales_yoy = 20045

sales_yoy_gr = "7.4%"

Never set sales_yoy to the increase amount.
6. For outlook: write a 2-3 sentence analyst paragraph. Never leave null if highlights exist.
7. For highlights: write complete standalone sentences. Maximum 6 bullets.
8. For banking/financial companies: sales = Net Interest Income, ebitda = Core Operating Profit, ebitda_margin = NIM %.
9. strengths: Extract exactly 3 strengths.

Use only evidence explicitly mentioned in the document.

Examples:
- Strong domestic loan growth
- Improving asset quality
- High capital adequacy
- Renewable capacity expansion
- Margin improvement

Do NOT use generic statements.
10. risks: Extract exactly 3 risks.

Priority:

1. Risks explicitly mentioned in the document.
2. Risks directly implied by the financial data.

Examples:
- Deposit growth lagging loan growth
- Margin compression risk
- Declining quarterly profitability
- Project execution risk
- Asset quality deterioration risk

Avoid generic risks such as:
- Political instability
- Economic slowdown
- Interest rate changes

11. Set missing fields to null only after searching the entire document.

If a value appears in:
- another table
- footnotes
- highlights
- outlook section
- management commentary

extract it rather than returning null.

Only return null when the value does not exist anywhere in the document.

JSON structure:
{{
  "company_name": "string",
  "sector": "string",
  "rating": "BUY or HOLD or SELL or null",
  "cmp": number or null,
  "target_price": number or null,
  "return_pct": number or null,
  "report_date": "string",
  "headline": "string",
  "stock_type": "Large Cap or Mid Cap or Small Cap",
  "bloomberg_code": "string or null",
  "sensex": "string or null",
  "nse_code": "string or null",
  "bse_code": "string or null",
  "time_frame": "12 Months",
  "market_cap": "string or null",
  "ev": "string or null",
  "week_52_high": number or null,
  "week_52_low": number or null,
  "outstanding_shares": "string or null",
  "free_float": "string or null",
  "dividend_yield": "string or null",
  "avg_volume_6m": "string or null",
  "beta": "string or null",
  "face_value": "string or null",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "risks": ["risk 1", "risk 2", "risk 3"],
  "highlights": ["sentence 1", "sentence 2"],
  "outlook": "paragraph string",
  "rating_confidence": number or null,
  "financials": [
    {{
      "year": "FY25A",
      "sales": number or null,
      "sales_growth": number or null,
      "ebitda": number or null,
      "ebitda_growth": number or null,
      "ebitda_margin": number or null,
      "pat": number or null,
      "pat_growth": number or null,
      "adj_pat": number or null,
      "eps": number or null,
      "pe": number or null,
      "pb": number or null,
      "ev_ebitda": number or null,
      "ev_sales": number or null,
      "roe": number or null,
      "roce": number or null,
      "net_margin": number or null,
      "depreciation": number or null,
      "ebit": number or null,
      "interest": number or null,
      "other_income": number or null,
      "pbt": number or null,
      "tax": number or null,
      "de": number or null
    }}
  ],
  "shareholding": [
    {{
      "period": "Q1FY26",
      "promoters": number or null,
      "fii": number or null,
      "mf": number or null,
      "public": number or null,
      "others": number or null,
      "total": number or null
    }}
  ],
  "price_performance": {{
    "abs_3m": "string or null",
    "abs_6m": "string or null",
    "abs_1y": "string or null",
    "sensex_3m": "string or null",
    "sensex_6m": "string or null",
    "sensex_1y": "string or null",
    "rel_3m": "string or null",
    "rel_6m": "string or null",
    "rel_1y": "string or null"
  }},
  "quarterly_financials": [
    {{
      "sales": number or null,
      "sales_yoy": number or null,
      "sales_yoy_gr": "string or null",
      "sales_qoq": number or null,
      "sales_qoq_gr": "string or null",
      "ebitda": number or null,
      "ebitda_yoy": number or null,
      "ebitda_yoy_gr": "string or null",
      "ebitda_qoq": number or null,
      "ebitda_qoq_gr": "string or null",
      "pat": number or null,
      "pat_yoy": number or null,
      "pat_yoy_gr": "string or null",
      "pat_qoq": number or null,
      "pat_qoq_gr": "string or null"
    }}
  ],
  "recommendation_history": [
    {{"date": "string", "rating": "string", "target": number}}
  ]
}}

Document:
{text_context}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents= prompt
    )
    raw = _clean_json(response.text)
    data = json.loads(raw)

    sector = data.get("sector", "") or ""
    data["_is_banking"] = _is_banking(company_name, sector)

    return data