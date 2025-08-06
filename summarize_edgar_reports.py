import os
import time
import json
import openai
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv

# Load OpenAI API key
dotenv_path = find_dotenv(usecwd=True)
print(f"Found .env at: {dotenv_path}")
load_dotenv(dotenv_path=dotenv_path)
openai.api_key = os.getenv("OPENAI")

print("OpenAI API key loaded")
print(os.getenv("OPENAI"))
print("Email can be scanned:")
print(os.getenv("EMAIL"))
print("Like this")

# ========== CONFIG ==========
TICKER = "AAPL"  # ← Change this to any ticker
DOWNLOAD_DIR = "./sec-edgar-filings"
SLEEP_BETWEEN_CALLS = 2  # seconds
MAX_TOKEN_TEXT_CHARS = 12000  # limit input to avoid token overflow
STALWART_FILE = "stalwart_summaries.json"
FASTGROWER_FILE = "fastgrower_summaries.json"
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
    # initialize section boundaries
    business_start = business_end = mdna_start = mdna_end = None
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

    # if any boundary not found or invalid, return empty
    if None in (business_start, business_end, mdna_start, mdna_end):
        return ""
    if business_end <= business_start or mdna_end <= mdna_start:
        return ""
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
        resp = openai.chat.completions.create(
            model="gpt-4.1-nano",
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
    # walk pre-populated local filings
    root_dir = os.path.join(DOWNLOAD_DIR, ticker.upper(), form_type)
    file_paths = []
    for root, _, files in os.walk(root_dir):
        for fname in files:
            if fname.endswith(".txt"):
                file_paths.append(os.path.join(root, fname))
    file_paths = sorted(file_paths, reverse=True)[:limit]

    for file_path in file_paths:
        try:
            print(f"Processing {label} - {file_path}")
            period = os.path.basename(os.path.dirname(file_path))
            raw = extract_text_from_html(file_path)
            section = extract_sections(raw)
            summary = summarize_section(section, period, form_type)
            key = "year" if form_type == "10-K" and label == "10-K" else "quarter"
            summaries.append({ key: period, "summary": summary })
            time.sleep(SLEEP_BETWEEN_CALLS)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    return summaries

# Summarize 10-Ks for stalwart
print("\n🧱 Summarizing 10-Ks for stalwart analysis...")
stalwart_summaries = summarize_filings(TICKER, "10-K", 10, "10-K")

# Summarize 10-Qs + recent 10-Ks for fast-grower
print("\n🚀 Summarizing 10-Ks and 10-Qs for fast-grower analysis...")
fastgrower_10qs = summarize_filings(TICKER, "10-Q", 10, "10-Q")
fastgrower_10ks = summarize_filings(TICKER, "10-K", 3, "Recent 10-Ks")  # include a few annuals
fastgrower_combined = sorted(fastgrower_10qs + fastgrower_10ks, key=lambda x: x.get("quarter", x.get("year")), reverse=True)[:10]

# Save to JSON files
with open(STALWART_FILE, "w") as f:
    json.dump(stalwart_summaries, f, indent=2)
    print(f"\n✅ Saved stalwart summaries to {STALWART_FILE}")

with open(FASTGROWER_FILE, "w") as f:
    json.dump(fastgrower_combined, f, indent=2)
    print(f"✅ Saved fast-grower summaries to {FASTGROWER_FILE}")