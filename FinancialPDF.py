#!/usr/bin/env python3
"""
Fetch the latest SEC filing for a given ticker and filing type, download HTML,
then render to PDF via Playwright without visiting sec.gov in the browser.
"""

import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# ==========================
# Hardcoded parameters
# ==========================
TICKER = "AAPL"        # e.g., "AAPL"
FILING_TYPE = "10-K"   # e.g., "10-K", "10-Q"
OUTPUT_DIR = Path("pdfs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "MyCompanyName MyBot/1.0 (admin@mycompany.com)"  # per SEC guidelines
WAIT_SECONDS_AFTER_LOAD = 1.0
PAPER_FORMAT = "letter"
PRINT_BACKGROUND = True

# ==========================
# Helpers
# ==========================
def get_cik_for_ticker(ticker: str) -> str:
    """Return the 10-digit zero-padded CIK for a ticker."""
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    for entry in data.values():
        if entry["ticker"].lower() == ticker.lower():
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"CIK not found for ticker {ticker}")

def get_latest_filing_url(cik: str, filing_type: str) -> str:
    """Return the URL to the main HTML document of the latest filing of a given type."""
    # Get the submissions JSON for the company
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Find the most recent accession number for the filing_type
    for i, form in enumerate(data["filings"]["recent"]["form"]):
        if form.lower() == filing_type.lower():
            accession_no = data["filings"]["recent"]["accessionNumber"][i]
            accession_no_nodash = accession_no.replace("-", "")
            primary_doc = data["filings"]["recent"]["primaryDocument"][i]
            return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_nodash}/{primary_doc}"
    raise ValueError(f"No {filing_type} filing found for CIK {cik}")

def download_html(url: str, out_path: Path):
    """Download HTML with proper User-Agent."""
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    out_path.write_bytes(r.content)
    print(f"[OK] Downloaded HTML to {out_path}")

def render_local_html_to_pdf(local_html: Path, out_pdf: Path):
    """Render a local HTML file to PDF using Playwright."""
    uri = "file://" + str(local_html.resolve())
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1200, "height": 1000})
        page = context.new_page()
        page.goto(uri, wait_until="load", timeout=60_000)
        if WAIT_SECONDS_AFTER_LOAD > 0:
            time.sleep(WAIT_SECONDS_AFTER_LOAD)
        page.emulate_media(media="print")
        page.pdf(path=str(out_pdf), format=PAPER_FORMAT, print_background=PRINT_BACKGROUND)
        context.close()
        browser.close()
    print(f"[OK] Rendered {local_html} -> {out_pdf}")

# ==========================
# Main
# ==========================
if __name__ == "__main__":
    try:
        print(f"[INFO] Looking up CIK for {TICKER}...")
        cik = get_cik_for_ticker(TICKER)

        print(f"[INFO] Getting latest {FILING_TYPE} for CIK {cik}...")
        filing_url = get_latest_filing_url(cik, FILING_TYPE)
        print(f"[INFO] Filing URL: {filing_url}")

        html_file = OUTPUT_DIR / (Path(filing_url).stem + ".html")
        pdf_file = OUTPUT_DIR / (Path(filing_url).stem + ".pdf")

        # Step 1: Download HTML
        download_html(filing_url, html_file)

        # Step 2: Render local HTML to PDF
        render_local_html_to_pdf(html_file, pdf_file)

    except Exception as e:
        print(f"[ERROR] {e}")
