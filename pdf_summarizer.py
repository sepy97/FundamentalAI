#!/usr/bin/env python3
"""
PDF Financial Report Summarizer
Processes all PDF files in the reports directory and creates comprehensive summaries
focused on business updates and financial performance.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import PyPDF2
import openai
from dotenv import load_dotenv
import markdown
from xhtml2pdf import pisa
import re
from datetime import datetime

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI")

# Configuration
REPORTS_DIR = Path("reports")
OUTPUT_DIR = Path("analysis_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
MODEL = "gpt-5-nano"
SLEEP_BETWEEN_CALLS = 2  # seconds
MAX_CHARS_PER_CHUNK = 15000  # Limit for token management

class PDFSummarizer:
    def __init__(self):
        self.summaries = {}
        self.reports_processed = 0

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def parse_filename_info(self, filename: str) -> Tuple[str, str, str]:
        """Extract date, ticker, and filing type from filename."""
        # Expected format: YYYYMMDD_ticker_filingtype.pdf (e.g., 20151028_aapl_10k.pdf)
        match = re.match(r'(\d{8})_([a-zA-Z]+)_([a-zA-Z0-9]+)\.pdf', filename)
        if match:
            date_str, ticker, filing_type = match.groups()
            # Convert date format
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            period = date_obj.strftime('%Y-%m-%d')
            # Normalize filing type to uppercase with hyphens
            filing_type_normalized = filing_type.upper()
            if filing_type_normalized == "10K":
                filing_type_normalized = "10-K"
            elif filing_type_normalized == "10Q":
                filing_type_normalized = "10-Q"
            return period, ticker.upper(), filing_type_normalized
        return "unknown", "unknown", "unknown"

    def create_basic_prompt(self, text: str, period: str, filing_type: str, ticker: str) -> str:
        """Create basic prompt for document summarization."""

        prompt = f"""Summarize this {filing_type} filing for {ticker} from {period}. Focus on:
1. Business or operational updates
2. Management tone and strategic messaging
3. Notable changes or risks
4. Performance or guidance signals

Keep the summary concise but comprehensive, highlighting the most important information for investors.

Filing Content:
{text[:MAX_CHARS_PER_CHUNK]}
"""
        return prompt

    def summarize_document(self, text: str, period: str, filing_type: str, ticker: str) -> str:
        """Generate AI summary using basic prompt."""
        prompt = self.create_basic_prompt(text, period, filing_type, ticker)

        try:
            response = openai.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a financial analyst summarizing SEC filings. Provide clear, concise summaries focusing on key business updates, financial performance, and notable changes."},
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[ERROR in summarization]: {e}"

    def process_company_pdfs(self, company_dir: Path) -> Dict:
        """Process all PDF files for a single company and create two separate analyses."""
        ticker = company_dir.name.upper()

        pdf_files = list(company_dir.glob("*.pdf"))
        pdf_files.sort()  # Sort by filename (date)

        print(f"\n📊 Processing {len(pdf_files)} PDF files for {ticker}...")

        # Separate files by type
        k_files = []
        q_files = []

        for pdf_file in pdf_files:
            period, file_ticker, filing_type = self.parse_filename_info(pdf_file.name)
            if filing_type == "10-K":
                k_files.append((pdf_file, period, filing_type))
            elif filing_type == "10-Q":
                q_files.append((pdf_file, period, filing_type))

        # Sort by date (most recent first)
        k_files.sort(key=lambda x: x[1], reverse=True)
        q_files.sort(key=lambda x: x[1], reverse=True)

        # Create stalwart analysis (last 10 years of 10-K reports)
        stalwart_data = {
            "ticker": ticker,
            "analysis_type": "stalwart_10_years",
            "reports": []
        }

        print(f"  📈 Processing last 10 years (10-K reports) for stalwart analysis...")
        for pdf_file, period, filing_type in k_files[:10]:  # Last 10 years
            print(f"    📄 Processing: {pdf_file.name}")
            text = self.extract_text_from_pdf(pdf_file)
            if text.strip():
                summary = self.summarize_document(text, period, filing_type, ticker)
                stalwart_data["reports"].append({
                    "filename": pdf_file.name,
                    "period": period,
                    "filing_type": filing_type,
                    "summary": summary
                })
                self.reports_processed += 1
                time.sleep(SLEEP_BETWEEN_CALLS)

        # Create fast-grower analysis (last 10 quarters: 10-Q + recent 10-K)
        fastgrower_data = {
            "ticker": ticker,
            "analysis_type": "fastgrower_10_quarters",
            "reports": []
        }

        print(f"  🚀 Processing last 10 quarters (10-Q + recent 10-K) for fast-grower analysis...")

        # Add last 10 quarters (10-Q reports)
        for pdf_file, period, filing_type in q_files[:10]:  # Last 10 quarters
            print(f"    📄 Processing: {pdf_file.name}")
            text = self.extract_text_from_pdf(pdf_file)
            if text.strip():
                summary = self.summarize_document(text, period, filing_type, ticker)
                fastgrower_data["reports"].append({
                    "filename": pdf_file.name,
                    "period": period,
                    "filing_type": filing_type,
                    "summary": summary
                })
                self.reports_processed += 1
                time.sleep(SLEEP_BETWEEN_CALLS)

        # Add last 3 annual reports (10-K) for context
        for pdf_file, period, filing_type in k_files[:3]:  # Last 3 years
            print(f"    📄 Processing: {pdf_file.name}")
            text = self.extract_text_from_pdf(pdf_file)
            if text.strip():
                summary = self.summarize_document(text, period, filing_type, ticker)
                fastgrower_data["reports"].append({
                    "filename": pdf_file.name,
                    "period": period,
                    "filing_type": filing_type,
                    "summary": summary
                })
                self.reports_processed += 1
                time.sleep(SLEEP_BETWEEN_CALLS)

        # Sort fastgrower reports by date (most recent first)
        fastgrower_data["reports"].sort(key=lambda x: x["period"], reverse=True)

        return stalwart_data, fastgrower_data

    def save_company_analysis(self, stalwart_data: Dict, fastgrower_data: Dict):
        """Save both stalwart and fast-grower analysis results."""
        ticker = stalwart_data["ticker"]

        # Save Stalwart Analysis (10 years)
        print(f"💾 Saving 10-year stalwart analysis for {ticker}...")
        self.save_analysis_files(stalwart_data, "stalwart_10_years")

        # Save Fast-grower Analysis (10 quarters)
        print(f"💾 Saving 10-quarter fast-grower analysis for {ticker}...")
        self.save_analysis_files(fastgrower_data, "fastgrower_10_quarters")

    def save_analysis_files(self, data: Dict, analysis_type: str):
        """Save analysis files for a specific analysis type."""
        ticker = data["ticker"]

        # Create filenames based on analysis type
        filename_base = f"{ticker.lower()}_{analysis_type}"

        # Save JSON
        json_file = OUTPUT_DIR / f"{filename_base}.json"
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Create markdown report
        markdown_content = self.create_markdown_report(data, analysis_type)

        # Save markdown
        md_file = OUTPUT_DIR / f"{filename_base}.md"
        with open(md_file, 'w') as f:
            f.write(markdown_content)

        # Convert to HTML and PDF
        html_content = markdown.markdown(markdown_content, extensions=['extra', 'tables'])
        title = f"{ticker} {'10-Year Stalwart' if 'stalwart' in analysis_type else '10-Quarter Fast-Grower'} Summary"
        html_full = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                .summary {{ background-color: #f8f9fa; padding: 20px; border-left: 4px solid #007bff; }}
                .stalwart {{ border-left-color: #28a745; }}
                .fastgrower {{ border-left-color: #ffc107; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>{html_content}</body>
        </html>
        """

        # Save HTML
        html_file = OUTPUT_DIR / f"{filename_base}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_full)

        # Generate PDF
        pdf_file = OUTPUT_DIR / f"{filename_base}.pdf"
        with open(pdf_file, 'wb') as f:
            pisa_status = pisa.CreatePDF(html_full, dest=f)

        analysis_name = "10-Year Stalwart Analysis" if "stalwart" in analysis_type else "10-Quarter Fast-Grower Analysis"
        print(f"✅ Saved {analysis_name} for {ticker}:")
        print(f"   📄 JSON: {json_file}")
        print(f"   📝 Markdown: {md_file}")
        print(f"   🌐 HTML: {html_file}")
        print(f"   📄 PDF: {pdf_file}")

    def create_markdown_report(self, data: Dict, analysis_type: str) -> str:
        """Create formatted markdown report for specific analysis type."""
        ticker = data["ticker"]
        reports = data["reports"]

        if "stalwart" in analysis_type:
            title = f"{ticker} - 10-Year Stalwart Analysis"
            description = "Long-term analysis based on annual 10-K reports over the last 10 years"
            focus = "This analysis focuses on long-term trends, consistency, and stability suitable for stalwart investment strategies"
        else:
            title = f"{ticker} - 10-Quarter Fast-Grower Analysis"
            description = "Recent performance analysis based on quarterly 10-Q reports and recent annual reports"
            focus = "This analysis focuses on recent growth trends and quarterly performance suitable for fast-grower investment strategies"

        md_content = f"""# {title}
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Analysis Overview
{description}

**Reports Analyzed:** {len(reports)} filings
**Time Period:** {reports[-1]['period'] if reports else 'N/A'} to {reports[0]['period'] if reports else 'N/A'}

{focus}

---

## Filing Summaries

"""

        for i, report in enumerate(reports, 1):
            md_content += f"""### {i}. {report['filing_type']} Filing - {report['period']}
**File:** `{report['filename']}`

{report['summary']}

---

"""

        md_content += f"""## Analysis Methodology

This {analysis_type.replace('_', ' ').title()} analysis summarizes key aspects of SEC filings, focusing on:

- **Business Updates**: Important operational changes and strategic initiatives
- **Financial Performance**: Revenue, earnings, and key financial metrics trends
- **Management Commentary**: Strategic messaging and forward guidance
- **Risk Assessment**: Notable risks, challenges, and market conditions

### Report Selection Criteria:
"""

        if "stalwart" in analysis_type:
            md_content += """
- **10-K Annual Reports**: Last 10 years of comprehensive annual filings
- **Long-term Focus**: Emphasis on consistency, stability, and sustainable business practices
- **Historical Trends**: Multi-year patterns in performance and strategic direction
"""
        else:
            md_content += """
- **10-Q Quarterly Reports**: Last 10 quarters for recent performance trends
- **Recent 10-K Reports**: Last 3 annual reports for comprehensive context
- **Growth Focus**: Emphasis on recent momentum, quarterly improvements, and acceleration
- **Short-term Trends**: Quarterly patterns and recent strategic developments
"""

        md_content += """
---

*This summary is based on publicly available SEC filings. Please consult with a qualified financial advisor for investment decisions.*
"""

        return md_content

    def process_specific_company(self, ticker: str):
        """Process PDF files for a specific company ticker."""
        company_dir = REPORTS_DIR / ticker.lower()

        if not company_dir.exists():
            print(f"❌ Company directory {company_dir} not found!")
            print(f"Available companies: {[d.name for d in REPORTS_DIR.iterdir() if d.is_dir()]}")
            return

        print(f"🚀 Analyzing company: {ticker.upper()}")
        print(f"{'='*60}")

        try:
            stalwart_data, fastgrower_data = self.process_company_pdfs(company_dir)
            if stalwart_data["reports"] or fastgrower_data["reports"]:
                self.save_company_analysis(stalwart_data, fastgrower_data)
                print(f"\n✅ Analysis complete for {ticker.upper()}!")
                print(f"📊 Processed {self.reports_processed} reports")
                print(f"📁 Files saved to: {OUTPUT_DIR}")
            else:
                print(f"⚠️ No valid reports found for {ticker}")
        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")

    def process_all_companies(self):
        """Process all companies in the reports directory."""
        if not REPORTS_DIR.exists():
            print(f"❌ Reports directory {REPORTS_DIR} not found!")
            return

        company_dirs = [d for d in REPORTS_DIR.iterdir() if d.is_dir()]

        if not company_dirs:
            print("❌ No company directories found in reports folder!")
            return

        print(f"🚀 Found {len(company_dirs)} companies to analyze...")

        for company_dir in company_dirs:
            print(f"\n{'='*60}")
            print(f"🏢 Analyzing company: {company_dir.name.upper()}")
            print(f"{'='*60}")

            try:
                stalwart_data, fastgrower_data = self.process_company_pdfs(company_dir)
                if stalwart_data["reports"] or fastgrower_data["reports"]:
                    self.save_company_analysis(stalwart_data, fastgrower_data)
                else:
                    print(f"⚠️ No valid reports found for {company_dir.name}")
            except Exception as e:
                print(f"❌ Error processing {company_dir.name}: {e}")

        print(f"\n🎉 Analysis complete! Processed {self.reports_processed} reports total.")
        print(f"📁 All analysis files saved to: {OUTPUT_DIR}")

def main():
    """Main execution function."""
    print("📊 PDF Financial Report Summarizer")
    print("=" * 60)

    # Check if OpenAI API key is available
    if not openai.api_key:
        print("❌ OpenAI API key not found! Please set OPENAI environment variable.")
        return

    # ========== CONFIGURATION ==========
    # Set the ticker symbol for the company you want to analyze
    TICKER = "AAPL"  # Change this to analyze a different company
    # Alternatively, set to None to analyze all companies
    # TICKER = None
    # ===================================

    summarizer = PDFSummarizer()

    if TICKER:
        # Analyze specific company
        summarizer.process_specific_company(TICKER)
    else:
        # Analyze all companies
        summarizer.process_all_companies()

if __name__ == "__main__":
    main()
