import json
import openai
from dotenv import load_dotenv
import os
# PDF generation
import markdown
from xhtml2pdf import pisa

# Load OpenAI API key from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI")

# === CONFIG ===
# (Ticker, JSON file path, and model are now configured inside main())
# ==============

# Format the report entries into readable text
def format_summaries(reports):
    formatted = ""
    for entry in sorted(reports, key=lambda x: x.get("period", "")):
        period = entry.get("period", "")
        filing_type = entry.get("filing_type", "")
        summary = entry.get("summary", "")
        formatted += f"\n\n==== {period} ({filing_type}) ====\n{summary.strip()}"
    return formatted

def main():
    # === CONFIG ===
    TICKER = "PFE"  # Change this to analyze a different company ticker
    JSON_FILE = f"analysis_outputs/{TICKER.lower()}_stalwart_10_years.json"
    MODEL = "gpt-5-mini"
    # ==============

    # Load summaries from PDF summarizer output
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        summaries = data.get("reports", [])

    # Format data into text
    formatted_data = format_summaries(summaries)

    # Compose and send to OpenAI
    prompt = f"""
    You are a long-term investor analyzing a large, established company (a stalwart) over a 10-year period.

    Here are yearly summaries from the company’s 10-K reports (2015–2024), including business description, management commentary, financial health, and risk factors.

    Use this information to assess the company's quality, stability, and investment potential. Pay particular attention to the following:

    ---

    1. **Business Consistency**  
       - Has the company maintained focus on its core business?
       - Any unrelated acquisitions or signs of “diworseification”?
       - Are there credible new product lines, or is innovation stalling?

    2. **Operational Efficiency & Capital Allocation**  
       - Has the company been efficient in cost control and reinvestment?
       - Are capital returns strong (buybacks, dividends, R&D)?
       - Is debt rising due to large acquisitions?

    3. **Stability and Resilience**  
       - How did the company behave during recessions or market downturns?
       - Did core divisions stay profitable or suffer?
       - Are insiders (executives/directors) buying shares or not?

    4. **Valuation and Growth Signals**  
       - Is the P/E (or valuation) low relative to history?
       - Are there signs of accelerating growth or strategic expansion?
       - Are new products close to market, or are launches delayed?

    ---

    ### 🔎 Evaluate the following SELL SIGNALS:
    - P/E has significantly increased without earnings growth.
    - Cost cuts failed to restore growth.
    - Major division is exposed to macroeconomic weakness.
    - Insiders did not buy stock over the past year.
    - New product announcements have not materialized.

    ---

    ### 📈 Finally, conclude:
    - Is this company a strong long-term stalwart?
    - What are the key **risks, red flags**, or **catalysts**?
    - Based on this profile, would you **Buy, Hold, or Avoid**?

    Here is the input:
    {formatted_data}
    """

    response = openai.chat.completions.create(
        model=MODEL,
        messages=tuple([
            {"role": "system", "content": "You are a financial analyst."},
            {"role": "user", "content": prompt}
        ]),  # type: ignore[arg-type]
    )
    analysis = response.choices[0].message.content
    print("\n====== QUALITATIVE ANALYSIS RESULT ======\n")
    print(analysis)

    # Save results
    out_txt = f"{TICKER.lower()}_stalwart_analysis.txt"
    with open(out_txt, "w") as f:
        f.write(analysis)
    # HTML and PDF conversion
    html = markdown.markdown(analysis, extensions=['extra'])
    html_full = f"<html><head><meta charset='utf-8'></head><body>{html}</body></html>"
    out_html = f"{TICKER.lower()}_stalwart_analysis.html"
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_full)
    out_pdf = f"{TICKER.lower()}_stalwart_analysis.pdf"
    with open(out_pdf, "wb") as f:
        pisa.CreatePDF(html_full, dest=f)

if __name__ == "__main__":
    main()
