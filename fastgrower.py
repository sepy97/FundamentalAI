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
You are evaluating a potential fast-growing stock investment based on recent company performance.

Here are summaries from the last 10 quarters of 10-Q and 10-K reports (about 2.5 years of data). These include management discussions of growth, operations, market strategy, and financial performance.

Using this data, provide a detailed qualitative evaluation:

1. **Growth Momentum**  
   - What are the main drivers of revenue and earnings growth?
   - Is growth accelerating, decelerating, or plateauing?

2. **Product & Market Expansion**  
   - Is the company entering new markets or expanding its TAM?
   - Are new products or business lines emerging?

3. **Scalability & Efficiency**  
   - Is the business showing signs of operating leverage or improving margins?
   - Are there challenges with hiring, delivery, or logistics?

4. **Capital Allocation & Cash Burn**  
   - How responsibly is the company spending (vs. burning) cash?
   - Is there a clear plan for profitability?

5. **Durability of Advantage**  
   - Are there signs of a developing moat (brand, tech, distribution)?
   - Is the company defending its lead against competitors?

Finally, summarize:
- Does this company look like a credible fast-grower with 5–10x upside?
- What are the biggest risks (macro, competitive, internal)?
- Would you **Buy, Monitor, or Avoid** based on this qualitative trajectory?

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