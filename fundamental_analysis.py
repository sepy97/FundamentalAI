import json
import openai
from dotenv import load_dotenv
import os
import markdown
from xhtml2pdf import pisa

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI")

# Prompt templates for each analysis type
PROMPT_TEMPLATES = {
    "stalwart_10_years": '''
You are a long-term investor analyzing a large, established company (a stalwart) over a 10-year period.

Here are yearly summaries from the company’s 10-K reports (2015–2024), including business description, management commentary, financial health, and risk factors.

Use this information to assess the company's quality, stability, and investment potential. Pay particular attention to:

1. Business Consistency
2. Operational Efficiency & Capital Allocation
3. Stability and Resilience
4. Valuation and Growth Signals

Evaluate SELL SIGNALS and conclude: Buy, Hold, or Avoid.

Input:
{formatted_data}
    ''',
    "fastgrower_10_quarters": '''
You are analyzing a fast-growing company based on recent 10-K and 10-Q summaries (last 10 quarters). These include management discussions of growth, strategy, operations, and risks.

Use this information to evaluate whether the company qualifies as a legitimate “fast-grower” with long-term upside. Focus on:

1. Growth Momentum
2. Expansion Quality & Market Fit
3. Scalability & Capital Discipline
4. Moat Development & Visibility

Check SELL SIGNALS and conclude: Buy, Hold, or Avoid.

Input:
{formatted_data}
    '''
}

def format_summaries(reports):
    formatted = ""
    for entry in sorted(reports, key=lambda x: x.get("period", "")):
        p = entry.get("period", "")
        t = entry.get("filing_type", "")
        s = entry.get("summary", "").strip()
        formatted += f"\n\n==== {p} ({t}) ===={s}"
    return formatted


def run_analysis(ticker, analysis_type):
    # Load summaries
    json_path = f"analysis_outputs/{ticker.lower()}_{analysis_type}.json"
    with open(json_path, 'r') as f:
        data = json.load(f)
    reports = data.get("reports", [])

    formatted_data = format_summaries(reports)
    prompt = PROMPT_TEMPLATES[analysis_type].format(formatted_data=formatted_data)

    # Call OpenAI
    response = openai.chat.completions.create(
        model="gpt-5",
        messages=tuple([
            {"role": "system", "content": "You are a financial analyst."},
            {"role": "user", "content": prompt}
        ]),  # type: ignore[arg-type]
    )
    analysis = response.choices[0].message.content
    print(f"\n===== {analysis_type} ANALYSIS =====\n")
    print(analysis)

    # Save outputs
    base = f"{ticker.lower()}_{analysis_type}_analysis"
    # TXT
    with open(f"{base}.txt", 'w') as f:
        f.write(analysis)
    # HTML
    html = markdown.markdown(analysis, extensions=['extra'])
    html_full = f"<html><head><meta charset='utf-8'></head><body>{html}</body></html>"
    with open(f"{base}.html", 'w', encoding='utf-8') as f:
        f.write(html_full)
    # PDF
    with open(f"{base}.pdf", 'wb') as f:
        pisa.CreatePDF(html_full, dest=f)


def main():
    # Configure ticker here
    TICKER = "PFE"
    for atype in PROMPT_TEMPLATES:
        run_analysis(TICKER, atype)


if __name__ == "__main__":
    main()
