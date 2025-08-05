import os
import time
import openai
from bs4 import BeautifulSoup
from sec_edgar_downloader import Downloader
from dotenv import load_dotenv

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OpenAI")

print("OpenAI API key loaded")
print(os.getenv("OPENAI"))
print("Email can be scanned:")
print(os.getenv("EMAIL"))
print("Like this")

# ========== CONFIG ==========
TICKER = "AAPL"  # ← Change this to any ticker
DOWNLOAD_DIR = "./sec_filings"
SLEEP_BETWEEN_CALLS = 2  # seconds
MAX_TOKEN_TEXT_CHARS = 12000  # limit input to avoid token overflow
# ============================

dl = Downloader(DOWNLOAD_DIR, os.getenv("Email"))
dl.get("10-K", TICKER, amount=10)
dl.get("10-Q", TICKER, amount=10)

# Helper to clean HTML/text
def extract_text_from_html(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        return soup.get_text(separator="\n")

# Extract relevant sections if possible
def extract_sections(text):
    lines = text.split("\n")
    lower_lines = [line.lower() for line in lines]
    business_text, mdna_text = "", ""

    for i, line in enumerate(lower_lines):
        if "item 1." in line and "business" in line:
            business_start = i
        if "item 1a." in line and "risk" in line:
            business_end = i
        if "item 7." in line and "management" in line:
            mdna_start = i
        if "item 7a." in line and "quantitative" in line:
            mdna_end = i

    business_text = "\n".join(lines[business_start:business_end])
    mdna_text = "\n".join(lines[mdna_start:mdna_end])
    return (business_text + "\n\n" + mdna_text).strip()

# Summarize via ChatGPT
def summarize_section(text, period, type_):
    prompt = f"""Summarize this {type_} filing for {period}. Focus on:
1. Business or operational updates
2. Management tone and strategic messaging
3. Notable changes or risks
4. Performance or guidance signals

Text:
{text[:MAX_TOKEN_TEXT_CHARS]}
"""

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial analyst summarizing SEC filings."},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR summarizing]: {e}"

# Unified summarization logic
def summarize_filings(ticker, form_type, limit, label):
    summaries = []
    path = os.path.join(DOWNLOAD_DIR, "SEC-Edgar-Data", ticker.upper(), form_type)
    files = sorted([f for f in os.listdir(path) if f.endswith(".txt")], reverse=True)[:limit]

    for f in files:
        try:
            print(f"Processing {label} - {f}")
            period = f.split("_")[0]
            raw = extract_text_from_html(os.path.join(path, f))
            section = extract_sections(raw)
            summary = summarize_section(section, period, form_type)
            summaries.append({ "period": period, "summary": summary })
            time.sleep(SLEEP_BETWEEN_CALLS)
        except Exception as e:
            print(f"Error processing {f}: {e}")
    return summaries

# Run for stalwart (10-Ks)
print("\n🧱 Summarizing 10-Ks for stalwart analysis...")
stalwart_summaries = summarize_filings(TICKER, "10-K", 10, "10-K")

# Run for fast-grower (recent 10-Qs + 10-Ks combined)
print("\n🚀 Summarizing 10-Ks and 10-Qs for fast-grower analysis...")
fastgrower_10qs = summarize_filings(TICKER, "10-Q", 10, "10-Q")
fastgrower_10ks = summarize_filings(TICKER, "10-K", 3, "10-K")  # Add a few annuals too
fastgrower_summaries = sorted(fastgrower_10qs + fastgrower_10ks, key=lambda x: x["period"], reverse=True)[:10]

# Output summaries
print("\n\n🧱 FINAL STALWART SUMMARY INPUT (10 Years):")
print("[")
for s in sorted(stalwart_summaries, key=lambda x: x["period"]):
    print(f'  {{ "year": "{s["period"]}", "summary": """{s["summary"]}""" }},')
print("]")

print("\n🚀 FINAL FAST-GROWER SUMMARY INPUT (Last 10 Quarters):")
print("[")
for s in sorted(fastgrower_summaries, key=lambda x: x["period"]):
    print(f'  {{ "quarter": "{s["period"]}", "summary": """{s["summary"]}""" }},')
print("]")
