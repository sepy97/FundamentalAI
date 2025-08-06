import json
import openai
from dotenv import load_dotenv
import os

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI")

# === CONFIG ===
JSON_FILE = "fastgrower_summaries.json"
MODEL = "gpt-4.1-mini"
# ==============

# Load summaries
with open(JSON_FILE, "r") as f:
    summaries = json.load(f)

# Format summaries into readable text
def format_summaries(summaries):
    formatted = ""
    for entry in sorted(summaries, key=lambda x: x["quarter"]):
        quarter = entry["quarter"]
        summary = entry["summary"]
        formatted += f"\n\n==== {quarter} ====\n{summary.strip()}"
    return formatted

formatted_data = format_summaries(summaries)

# Compose full prompt
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

# Send to OpenAI API
response = openai.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a financial analyst."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7
)

# Output result
analysis = response.choices[0].message.content
print("\n====== FAST-GROWER QUALITATIVE ANALYSIS ======\n")
print(analysis)

# Save analysis to file
output_file = "fastgrower_analysis.txt"
with open(output_file, "w") as f:
    f.write(analysis)
    print(f"✅ Saved qualitative analysis to {output_file}")