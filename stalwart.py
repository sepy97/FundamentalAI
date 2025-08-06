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
You are a long-term investor analyzing a large, stable company over a 10-year period.

Here are yearly summaries from the company’s 10-K reports (2015–2024), focusing on their business description, management commentary, and risk factors.

Using this data, provide a detailed qualitative assessment:

1. **Business Consistency**  
   - Has the company stayed focused on its core business model?
   - Did it pivot strategies or stay disciplined?

2. **Operational Efficiency & Capital Allocation**  
   - How has management discussed cost control, profitability, and reinvestment?
   - Is there evidence of prudent capital use (R&D, M&A, dividends/buybacks)?

3. **Stability and Resilience**  
   - How did the company perform during downturns (e.g., COVID)?
   - Are there signs of competitive erosion or defensive strength?

4. **Moat and Competitive Position**  
   - Has the company defended its market position effectively?
   - Are there signs of commoditization, disruption, or sustained dominance?

5. **Growth Outlook**  
   - Is the company still growing meaningfully?
   - Are growth areas consistent with long-term secular trends?

Finally, summarize:
- Is this company a strong long-term “stalwart” investment?
- What are the key risks or red flags?
- Would you **Buy, Hold, or Avoid** based on this 10-year qualitative profile?

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
