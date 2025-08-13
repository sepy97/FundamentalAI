#!/usr/bin/env python3
"""
Unified Financial Analysis System
Main orchestrator that combines PDF downloading, summarization, and analysis.
All configuration is externalized and the system supports both single and batch processing.
"""

import argparse
import sys
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import our modules
from config_manager import config
from financial_pdf_downloader import FinancialPDFDownloader
from pdf_summarizer import PDFSummarizer
from fundamental_analyzer import FundamentalAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('financial_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FinancialAnalysisOrchestrator:
    """Main orchestrator for the financial analysis pipeline"""

    def __init__(self):
        self.downloader = FinancialPDFDownloader()
        self.summarizer = PDFSummarizer()
        self.analyzer = FundamentalAnalyzer()

        # Create output directories
        config.directories.reports.mkdir(parents=True, exist_ok=True)
        config.directories.analysis_outputs.mkdir(parents=True, exist_ok=True)

        # Statistics tracking
        self.stats = {
            'companies_processed': 0,
            'pdfs_downloaded': 0,
            'summaries_created': 0,
            'analyses_completed': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    def download_filings(self, ticker: str, filing_counts: Optional[Dict[str, int]] = None) -> bool:
        """Download SEC filings for a ticker"""
        try:
            logger.info(f"📥 Downloading filings for {ticker}")

            if filing_counts is None:
                filing_counts = {
                    config.filings.annual_type: config.filings.stalwart_years,
                    config.filings.quarterly_type: config.filings.fastgrower_quarters
                }

            success = self.downloader.download_company_filings(ticker, filing_counts)
            if success:
                logger.info(f"✅ Successfully downloaded filings for {ticker}")
                return True
            else:
                logger.error(f"❌ Failed to download filings for {ticker}")
                self.stats['errors'] += 1
                return False

        except Exception as e:
            logger.error(f"❌ Error downloading filings for {ticker}: {e}")
            self.stats['errors'] += 1
            return False

    def create_summaries(self, ticker: str) -> bool:
        """Create AI summaries of PDF filings"""
        try:
            logger.info(f"📝 Creating summaries for {ticker}")

            success = self.summarizer.process_company(ticker)
            if success:
                logger.info(f"✅ Successfully created summaries for {ticker}")
                self.stats['summaries_created'] += 1
                return True
            else:
                logger.error(f"❌ Failed to create summaries for {ticker}")
                self.stats['errors'] += 1
                return False

        except Exception as e:
            logger.error(f"❌ Error creating summaries for {ticker}: {e}")
            self.stats['errors'] += 1
            return False

    def run_analysis(self, ticker: str, analysis_types: Optional[List[str]] = None) -> bool:
        """Run fundamental analysis on summarized data"""
        try:
            logger.info(f"🔬 Running analysis for {ticker}")

            if analysis_types is None:
                analysis_types = list(config.get_analysis_types().keys())

            success = self.analyzer.analyze_company(ticker, analysis_types)
            if success:
                logger.info(f"✅ Successfully completed analysis for {ticker}")
                self.stats['analyses_completed'] += 1
                return True
            else:
                logger.error(f"❌ Failed to complete analysis for {ticker}")
                self.stats['errors'] += 1
                return False

        except Exception as e:
            logger.error(f"❌ Error running analysis for {ticker}: {e}")
            self.stats['errors'] += 1
            return False

    def process_single_company(self, ticker: str, skip_download: bool = False,
                             skip_summary: bool = False, skip_analysis: bool = False) -> bool:
        """Process a single company through the complete pipeline"""
        logger.info(f"🏢 Processing company: {ticker.upper()}")
        logger.info("=" * 60)

        try:
            # Step 1: Download filings
            if not skip_download:
                if not self.download_filings(ticker):
                    return False
                time.sleep(config.sec.rate_limit_delay)  # Respect SEC rate limits

            # Step 2: Create summaries
            if not skip_summary:
                if not self.create_summaries(ticker):
                    return False

            # Step 3: Run analysis
            if not skip_analysis:
                if not self.run_analysis(ticker):
                    return False

            self.stats['companies_processed'] += 1
            logger.info(f"🎉 Successfully processed {ticker.upper()}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to process {ticker}: {e}")
            self.stats['errors'] += 1
            return False

    def process_batch_companies(self, tickers: List[str], skip_download: bool = False,
                              skip_summary: bool = False, skip_analysis: bool = False) -> Dict[str, bool]:
        """Process multiple companies"""
        logger.info(f"🚀 Processing {len(tickers)} companies in batch mode")

        results = {}
        for i, ticker in enumerate(tickers, 1):
            logger.info(f"\n[{i}/{len(tickers)}] Processing {ticker.upper()}")
            results[ticker] = self.process_single_company(
                ticker, skip_download, skip_summary, skip_analysis
            )

            # Add delay between companies to be respectful to APIs
            if i < len(tickers):
                time.sleep(config.ai.sleep_between_calls)

        return results

    def print_summary_report(self, results: Optional[Dict[str, bool]] = None):
        """Print a summary report of the processing results"""
        duration = datetime.now() - self.stats['start_time']

        logger.info("\n" + "=" * 60)
        logger.info("📊 PROCESSING SUMMARY REPORT")
        logger.info("=" * 60)
        logger.info(f"⏱️  Total Duration: {duration}")
        logger.info(f"🏢 Companies Processed: {self.stats['companies_processed']}")
        logger.info(f"📥 PDFs Downloaded: {self.stats['pdfs_downloaded']}")
        logger.info(f"📝 Summaries Created: {self.stats['summaries_created']}")
        logger.info(f"🔬 Analyses Completed: {self.stats['analyses_completed']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")

        if results:
            successful = sum(1 for success in results.values() if success)
            failed = len(results) - successful
            logger.info(f"✅ Successful: {successful}")
            logger.info(f"❌ Failed: {failed}")

            if failed > 0:
                failed_tickers = [ticker for ticker, success in results.items() if not success]
                logger.info(f"❌ Failed tickers: {', '.join(failed_tickers)}")

        logger.info(f"📁 Output directory: {config.directories.analysis_outputs}")
        logger.info("=" * 60)

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Unified Financial Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single company (full pipeline)
  python main.py --ticker AAPL
  
  # Process multiple companies
  python main.py --ticker AAPL MSFT GOOGL
  
  # Use batch mode from config
  python main.py --batch
  
  # Skip certain steps
  python main.py --ticker AAPL --skip-download --skip-summary
  
  # Only run analysis (assumes summaries exist)
  python main.py --ticker AAPL --skip-download --skip-summary
        """
    )

    # Ticker selection
    parser.add_argument(
        '--ticker', '-t',
        nargs='+',
        help='Ticker symbol(s) to process'
    )

    parser.add_argument(
        '--batch', '-b',
        action='store_true',
        help='Process all tickers from config file'
    )

    # Pipeline control
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip PDF download step'
    )

    parser.add_argument(
        '--skip-summary',
        action='store_true',
        help='Skip summarization step'
    )

    parser.add_argument(
        '--skip-analysis',
        action='store_true',
        help='Skip analysis step'
    )

    # Configuration
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser

def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize orchestrator
        orchestrator = FinancialAnalysisOrchestrator()

        # Determine which tickers to process
        if args.batch:
            tickers = config.get_batch_tickers()
            if not tickers:
                logger.error("❌ No batch tickers configured in config file")
                sys.exit(1)
        elif args.ticker:
            tickers = [t.upper() for t in args.ticker]
        else:
            # Use default ticker
            default_ticker = config.get_default_ticker()
            tickers = [default_ticker]
            logger.info(f"🎯 Using default ticker: {default_ticker}")

        logger.info(f"🚀 Starting Financial Analysis System")
        logger.info(f"📋 Processing tickers: {', '.join(tickers)}")

        # Process companies
        if len(tickers) == 1:
            success = orchestrator.process_single_company(
                tickers[0],
                skip_download=args.skip_download,
                skip_summary=args.skip_summary,
                skip_analysis=args.skip_analysis
            )
            results = {tickers[0]: success}
        else:
            results = orchestrator.process_batch_companies(
                tickers,
                skip_download=args.skip_download,
                skip_summary=args.skip_summary,
                skip_analysis=args.skip_analysis
            )

        # Print summary
        orchestrator.print_summary_report(results)

        # Exit with appropriate code
        if all(results.values()):
            logger.info("🎉 All companies processed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Some companies failed to process. Check logs for details.")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n🛑 Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
