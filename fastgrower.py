import json
import openai
from dotenv import load_dotenv
import os
import markdown
from xhtml2pdf import pisa

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI")

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
    JSON_FILE = f"analysis_outputs/{TICKER.lower()}_fastgrower_10_quarters.json"
    MODEL = "gpt-5-mini"
    # ==============

    # Load summaries
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        summaries = data.get("reports", [])

    # Format data
    formatted_data = format_summaries(summaries)

    # Compose prompt and send to OpenAI
    prompt = f"""
    You are analyzing a fast-growing company based on recent 10-K and 10-Q summaries (last 10 quarters). These include management discussions of growth, strategy, operations, and risks.

    Use this information to evaluate whether the company qualifies as a legitimate “fast-grower” with long-term upside.

    ---

    1. **Growth Momentum**  
       - Are quarterly earnings consistently increasing?
       - Is profitability improving alongside revenue?
       - Is growth accelerating, decelerating, or plateauing?

    2. **Expansion Quality & Market Fit**  
       - Has the company proven success in more than one geography or vertical?
       - Are expansion efforts scaling up (speed, repeatability)?
       - Does the lead product significantly impact overall revenue?

    3. **Scalability & Capital Discipline**  
       - Is operating leverage emerging (margin improvement)?
       - Is debt moderate and well-managed?
       - Are they investing in scalable growth (not just advertising)?

    4. **Moat Development & Visibility**  
       - Is there evidence of a durable competitive edge (tech, brand, network)?
       - Has Wall Street noticed this company yet (low analyst/institutional attention)?

    ---

    ### 🚩 Check for SELL SIGNALS:
    - The company’s valuation (P/E > 30) is not justified by forward growth (<20%).
    - Company has become too recognizable (e.g., heavily advertised, media buzz).
    - Executive turnover is high.
    - Top-line growth is slowing, and profit guidance is reduced.
    - Analysts increasingly covering the stock; fast-grower phase may be ending.

    ---

    ### 🧠 Summary:
    - Is this still a **credible 5–10x fast-grower**?
    - What are the major **risks, turning points, or hype signals**?
    - Would you **Buy, Hold, or Avoid**?

    Here is the input:
    {formatted_data}
    """
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a financial analyst."},
            {"role": "user", "content": prompt}
        ],
    )
    analysis = response.choices[0].message.content
    print("\n====== FAST-GROWER QUALITATIVE ANALYSIS ======\n")
    print(analysis)

    # Save results
    out_txt = f"{TICKER.lower()}_fastgrower_analysis.txt"
    with open(out_txt, "w") as f:
        f.write(analysis)
    html = markdown.markdown(analysis, extensions=['extra'])
    html_full = f"<html><head><meta charset='utf-8'></head><body>{html}</body></html>"
    out_html = f"{TICKER.lower()}_fastgrower_analysis.html"
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_full)
    out_pdf = f"{TICKER.lower()}_fastgrower_analysis.pdf"
    with open(out_pdf, "wb") as f:
        pisa.CreatePDF(html_full, dest=f)

if __name__ == "__main__":
    main()
