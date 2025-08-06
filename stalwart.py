import json
import openai
from dotenv import load_dotenv
import os

# Load OpenAI API key from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI")

# === CONFIG ===
JSON_FILE = "stalwart_summaries.json"
MODEL = "gpt-4.1-mini"
# ==============

# Load summaries
with open(JSON_FILE, "r") as f:
    summaries = json.load(f)

# Format the JSON into readable text
def format_summaries(summaries):
    formatted = ""
    for entry in sorted(summaries, key=lambda x: x["year"]):
        year = entry["year"]
        summary = entry["summary"]
        formatted += f"\n\n==== {year} ====\n{summary.strip()}"
    return formatted

formatted_data = format_summaries(summaries)

# Compose the full prompt
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

# Call OpenAI API using v1 interface
response = openai.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a financial analyst."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7
)

# Print the response
analysis = response.choices[0].message.content
print("\n====== QUALITATIVE ANALYSIS RESULT ======\n")
print(analysis)

# Save analysis to file
output_file = "stalwart_analysis.txt"
with open(output_file, "w") as f:
    f.write(analysis)
    print(f"✅ Saved qualitative analysis to {output_file}")
