#!/usr/bin/env python3
"""
Refactored SEC Filing PDF Downloader
Removes hardcoded values and uses centralized configuration.
"""

import time
import requests
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from typing import Dict, List
import logging

from config_manager import config

logger = logging.getLogger(__name__)

class FinancialPDFDownloader:
    """Downloads and converts SEC filings to PDF using configuration"""

    def __init__(self):
        self.sec_config = config.sec
        self.pdf_config = config.pdf
        self.directories = config.directories

    def get_cik_for_ticker(self, ticker: str) -> str:
        """Return the 10-digit zero-padded CIK for a ticker."""
        headers = {"User-Agent": self.sec_config.user_agent}
        r = requests.get(
            self.sec_config.company_tickers_url,
            headers=headers,
            timeout=self.sec_config.request_timeout
        )
        r.raise_for_status()
        data = r.json()

        for entry in data.values():
            if entry["ticker"].lower() == ticker.lower():
                return str(entry["cik_str"]).zfill(10)

        raise ValueError(f"CIK not found for ticker {ticker}")

    def get_filing_urls(self, cik: str, filing_type: str, count: int) -> List[Dict]:
        """Return a list of dicts with url and filing date for the latest filings."""
        url = self.sec_config.submissions_url.format(cik=cik)
        headers = {"User-Agent": self.sec_config.user_agent}

        r = requests.get(url, headers=headers, timeout=self.sec_config.request_timeout)
        r.raise_for_status()
        data = r.json()

        filings = []
        recent_data = data["filings"]["recent"]

        # First, get filings from recent data
        for i, form in enumerate(recent_data["form"]):
            if form.lower() == filing_type.lower():
                accession_no = recent_data["accessionNumber"][i]
                accession_no_nodash = accession_no.replace("-", "")
                primary_doc = recent_data["primaryDocument"][i]
                filing_date = recent_data["filingDate"][i]

                url = self.sec_config.archives_url.format(
                    cik=int(cik),
                    accession=accession_no_nodash,
                    document=primary_doc
                )

                filings.append({"url": url, "filing_date": filing_date})
                logger.debug(f"Found {filing_type} #{len(filings)}: {filing_date} [RECENT]")

                if len(filings) >= count:
                    break

        # If we need more filings, check archived data
        if len(filings) < count and 'files' in data['filings']:
            logger.info(f"Need {count - len(filings)} more {filing_type} filings - checking archived data...")
            archived_files = data['filings']['files']

            for file_info in archived_files:
                if len(filings) >= count:
                    break

                archive_name = file_info.get('name', '')
                logger.debug(f"Checking archive: {archive_name}")

                # Download archived filing data
                archive_url = f"https://data.sec.gov/submissions/{archive_name}"
                try:
                    archive_r = requests.get(archive_url, headers=headers, timeout=self.sec_config.request_timeout)
                    archive_r.raise_for_status()
                    archive_data = archive_r.json()

                    # Extract filings from archived data
                    for i, form in enumerate(archive_data.get("form", [])):
                        if len(filings) >= count:
                            break

                        if form.lower() == filing_type.lower():
                            accession_no = archive_data["accessionNumber"][i]
                            accession_no_nodash = accession_no.replace("-", "")
                            primary_doc = archive_data["primaryDocument"][i]
                            filing_date = archive_data["filingDate"][i]

                            url = self.sec_config.archives_url.format(
                                cik=int(cik),
                                accession=accession_no_nodash,
                                document=primary_doc
                            )

                            filings.append({"url": url, "filing_date": filing_date})
                            logger.debug(f"Found {filing_type} #{len(filings)}: {filing_date} [ARCHIVE]")

                    # Rate limiting for archive requests
                    time.sleep(0.5)

                except Exception as e:
                    logger.warning(f"Failed to fetch archive {archive_name}: {e}")
                    continue

        if not filings:
            raise ValueError(f"No {filing_type} filings found for CIK {cik}")

        logger.info(f"Found {len(filings)} {filing_type} filings (requested {count})")
        return filings

    def download_html(self, url: str, out_path: Path):
        """Download HTML with proper User-Agent."""
        headers = {"User-Agent": self.sec_config.user_agent}
        r = requests.get(url, headers=headers, timeout=self.sec_config.request_timeout)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        logger.debug(f"Downloaded HTML to {out_path}")

    def render_local_html_to_pdf(self, local_html: Path, out_pdf: Path):
        """Render a local HTML file to PDF using Playwright."""
        uri = "file://" + str(local_html.resolve())

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(
                viewport={
                    "width": self.pdf_config.viewport_width,
                    "height": self.pdf_config.viewport_height
                }
            )
            page = context.new_page()
            page.goto(uri, wait_until="load", timeout=60_000)

            if self.pdf_config.wait_after_load > 0:
                time.sleep(self.pdf_config.wait_after_load)

            page.emulate_media(media="print")
            page.pdf(
                path=str(out_pdf),
                format=self.pdf_config.paper_format,
                print_background=self.pdf_config.print_background
            )
            context.close()
            browser.close()

        logger.debug(f"Rendered {local_html} -> {out_pdf}")

    def download_company_filings(self, ticker: str, filing_counts: Dict[str, int]) -> bool:
        """Download all specified filings for a company"""
        try:
            logger.info(f"Looking up CIK for {ticker}...")
            cik = self.get_cik_for_ticker(ticker)

            # Create company directory
            output_dir = self.directories.reports / ticker.lower()
            output_dir.mkdir(parents=True, exist_ok=True)

            total_downloads = 0

            for filing_type, count in filing_counts.items():
                logger.info(f"Getting last {count} {filing_type} filings for {ticker}...")
                filings = self.get_filing_urls(cik, filing_type, count)

                for filing in filings:
                    filing_url = filing["url"]
                    filing_date = filing["filing_date"].replace("-", "")

                    # Create standardized filename
                    type_str = filing_type.lower().replace("-", "")
                    html_file = output_dir / f"{filing_date}_{ticker.lower()}_{type_str}.html"
                    pdf_file = output_dir / f"{filing_date}_{ticker.lower()}_{type_str}.pdf"

                    # Skip if PDF already exists
                    if pdf_file.exists():
                        logger.debug(f"PDF already exists: {pdf_file}")
                        continue

                    # Download HTML
                    self.download_html(filing_url, html_file)

                    # Render to PDF
                    self.render_local_html_to_pdf(html_file, pdf_file)

                    total_downloads += 1

                    # Rate limiting
                    time.sleep(self.sec_config.rate_limit_delay)

            logger.info(f"Successfully downloaded {total_downloads} filings for {ticker}")
            return True

        except Exception as e:
            logger.error(f"Error downloading filings for {ticker}: {e}")
            return False
