#!/usr/bin/env python3
"""
Refactored PDF Summarizer
Uses centralized configuration and prompt management instead of hardcoded values.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import PyPDF2
import openai
import markdown
from xhtml2pdf import pisa
import re
from datetime import datetime
import logging

from config_manager import config
from prompt_manager import prompt_manager

logger = logging.getLogger(__name__)

class PDFSummarizer:
    """Processes PDF files and creates AI-powered summaries using configuration"""

    def __init__(self):
        self.ai_config = config.ai
        self.directories = config.directories
        self.filing_config = config.filings

        # Set up OpenAI
        if self.ai_config.api_key:
            openai.api_key = self.ai_config.api_key
        else:
            raise ValueError("OpenAI API key not found in environment variables")

        self.summaries_created = 0

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
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def parse_filename_info(self, filename: str) -> Tuple[str, str, str]:
        """Extract date, ticker, and filing type from filename."""
        match = re.match(r'(\d{8})_([a-zA-Z]+)_([a-zA-Z0-9]+)\.pdf', filename)
        if match:
            date_str, ticker, filing_type = match.groups()
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            period = date_obj.strftime('%Y-%m-%d')

            # Normalize filing type
            filing_type_normalized = filing_type.upper()
            if filing_type_normalized == "10K":
                filing_type_normalized = "10-K"
            elif filing_type_normalized == "10Q":
                filing_type_normalized = "10-Q"

            return period, ticker.upper(), filing_type_normalized

        return "unknown", "unknown", "unknown"

    def summarize_document(self, text: str, period: str, filing_type: str, ticker: str) -> str:
        """Generate AI summary using centralized prompt management."""
        try:
            prompt = prompt_manager.get_template(
                "basic_summary",
                filing_type=filing_type,
                ticker=ticker,
                period=period,
                content=text[:self.ai_config.max_chars_per_chunk]
            )

            response = openai.chat.completions.create(
                model=self.ai_config.summarization_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst summarizing SEC filings. Provide clear, concise summaries focusing on key business updates, financial performance, and notable changes."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=self.ai_config.max_completion_tokens,
                #temperature=self.ai_config.temperature # current model does not use temperature
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            # Try with alternative model
            try:
                response = openai.chat.completions.create(
                    model=self.ai_config.alternative_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a financial analyst summarizing SEC filings."
                        },
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content.strip()
            except Exception as e2:
                return f"[ERROR in summarization]: {e2}"

    def process_company_pdfs(self, company_dir: Path) -> Tuple[Dict, Dict]:
        """Process all PDF files for a single company and create analyses."""
        ticker = company_dir.name.upper()
        pdf_files = list(company_dir.glob("*.pdf"))
        pdf_files.sort()

        logger.info(f"Processing {len(pdf_files)} PDF files for {ticker}...")

        # Separate files by type
        k_files = []
        q_files = []

        for pdf_file in pdf_files:
            period, file_ticker, filing_type = self.parse_filename_info(pdf_file.name)
            if filing_type == self.filing_config.annual_type:
                k_files.append((pdf_file, period, filing_type))
            elif filing_type == self.filing_config.quarterly_type:
                q_files.append((pdf_file, period, filing_type))

        # Sort by date (most recent first)
        k_files.sort(key=lambda x: x[1], reverse=True)
        q_files.sort(key=lambda x: x[1], reverse=True)

        # Create stalwart analysis data
        stalwart_data = {
            "ticker": ticker,
            "analysis_type": "stalwart_10_years",
            "reports": []
        }

        logger.info(f"Processing last {self.filing_config.stalwart_years} years (10-K reports) for stalwart analysis...")
        for pdf_file, period, filing_type in k_files[:self.filing_config.stalwart_years]:
            logger.debug(f"Processing: {pdf_file.name}")
            text = self.extract_text_from_pdf(pdf_file)
            if text.strip():
                summary = self.summarize_document(text, period, filing_type, ticker)
                stalwart_data["reports"].append({
                    "filename": pdf_file.name,
                    "period": period,
                    "filing_type": filing_type,
                    "summary": summary
                })
                self.summaries_created += 1
                time.sleep(self.ai_config.sleep_between_calls)

        # Create fast-grower analysis data
        fastgrower_data = {
            "ticker": ticker,
            "analysis_type": "fastgrower_10_quarters",
            "reports": []
        }

        logger.info(f"Processing last {self.filing_config.fastgrower_quarters} quarters for fast-grower analysis...")

        # Add quarterly reports
        for pdf_file, period, filing_type in q_files[:self.filing_config.fastgrower_quarters]:
            logger.debug(f"Processing: {pdf_file.name}")
            text = self.extract_text_from_pdf(pdf_file)
            if text.strip():
                summary = self.summarize_document(text, period, filing_type, ticker)
                fastgrower_data["reports"].append({
                    "filename": pdf_file.name,
                    "period": period,
                    "filing_type": filing_type,
                    "summary": summary
                })
                self.summaries_created += 1
                time.sleep(self.ai_config.sleep_between_calls)

        # Add context annual reports
        for pdf_file, period, filing_type in k_files[:self.filing_config.fastgrower_context_years]:
            logger.debug(f"Processing: {pdf_file.name}")
            text = self.extract_text_from_pdf(pdf_file)
            if text.strip():
                summary = self.summarize_document(text, period, filing_type, ticker)
                fastgrower_data["reports"].append({
                    "filename": pdf_file.name,
                    "period": period,
                    "filing_type": filing_type,
                    "summary": summary
                })
                self.summaries_created += 1
                time.sleep(self.ai_config.sleep_between_calls)

        # Sort fastgrower reports by date
        fastgrower_data["reports"].sort(key=lambda x: x["period"], reverse=True)

        return stalwart_data, fastgrower_data

    def save_analysis_files(self, data: Dict, analysis_type: str):
        """Save analysis files using configured formats and naming."""
        ticker = data["ticker"]
        filename_pattern = config.get_file_naming_pattern("summary")
        filename_base = filename_pattern.format(ticker=ticker.lower(), analysis_type=analysis_type)

        output_formats = config.get_output_formats()

        # Save JSON
        if "json" in output_formats:
            json_file = self.directories.analysis_outputs / f"{filename_base}.json"
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        # Create and save markdown
        if "markdown" in output_formats:
            markdown_content = self.create_markdown_report(data, analysis_type)
            md_file = self.directories.analysis_outputs / f"{filename_base}.md"
            with open(md_file, 'w') as f:
                f.write(markdown_content)

        # Convert to HTML and PDF if requested
        if "html" in output_formats or "pdf" in output_formats:
            html_content = markdown.markdown(markdown_content, extensions=['extra', 'tables'])
            title = f"{ticker} {'10-Year Stalwart' if 'stalwart' in analysis_type else '10-Quarter Fast-Grower'} Summary"
            html_full = self._create_html_document(html_content, title, analysis_type)

            if "html" in output_formats:
                html_file = self.directories.analysis_outputs / f"{filename_base}.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_full)

            if "pdf" in output_formats:
                pdf_file = self.directories.analysis_outputs / f"{filename_base}.pdf"
                with open(pdf_file, 'wb') as f:
                    pisa.CreatePDF(html_full, dest=f)

        analysis_name = "10-Year Stalwart Analysis" if "stalwart" in analysis_type else "10-Quarter Fast-Grower Analysis"
        logger.info(f"Saved {analysis_name} for {ticker}")

    def _create_html_document(self, content: str, title: str, analysis_type: str) -> str:
        """Create full HTML document with styling."""
        style_class = "stalwart" if "stalwart" in analysis_type else "fastgrower"

        return f"""
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
        <body class="{style_class}">{content}</body>
        </html>
        """

    def create_markdown_report(self, data: Dict, analysis_type: str) -> str:
        """Create formatted markdown report."""
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

        md_content += self._get_methodology_text(analysis_type)
        return md_content

    def _get_methodology_text(self, analysis_type: str) -> str:
        """Get methodology text for the analysis type."""
        base_text = """## Analysis Methodology

This analysis summarizes key aspects of SEC filings, focusing on:

- **Business Updates**: Important operational changes and strategic initiatives
- **Financial Performance**: Revenue, earnings, and key financial metrics trends
- **Management Commentary**: Strategic messaging and forward guidance
- **Risk Assessment**: Notable risks, challenges, and market conditions

### Report Selection Criteria:
"""

        if "stalwart" in analysis_type:
            criteria = f"""
- **10-K Annual Reports**: Last {self.filing_config.stalwart_years} years of comprehensive annual filings
- **Long-term Focus**: Emphasis on consistency, stability, and sustainable business practices
- **Historical Trends**: Multi-year patterns in performance and strategic direction
"""
        else:
            criteria = f"""
- **10-Q Quarterly Reports**: Last {self.filing_config.fastgrower_quarters} quarters for recent performance trends
- **Recent 10-K Reports**: Last {self.filing_config.fastgrower_context_years} annual reports for comprehensive context
- **Growth Focus**: Emphasis on recent momentum, quarterly improvements, and acceleration
- **Short-term Trends**: Quarterly patterns and recent strategic developments
"""

        return base_text + criteria + """
---

*This summary is based on publicly available SEC filings. Please consult with a qualified financial advisor for investment decisions.*
"""

    def process_company(self, ticker: str) -> bool:
        """Process a single company's PDFs and create summaries."""
        company_dir = self.directories.reports / ticker.lower()

        if not company_dir.exists():
            logger.error(f"Company directory {company_dir} not found!")
            return False

        try:
            stalwart_data, fastgrower_data = self.process_company_pdfs(company_dir)

            if stalwart_data["reports"] or fastgrower_data["reports"]:
                self.save_analysis_files(stalwart_data, "stalwart_10_years")
                self.save_analysis_files(fastgrower_data, "fastgrower_10_quarters")
                logger.info(f"Successfully processed {self.summaries_created} summaries for {ticker}")
                return True
            else:
                logger.warning(f"No valid reports found for {ticker}")
                return False

        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            return False
