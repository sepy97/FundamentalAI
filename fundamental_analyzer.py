#!/usr/bin/env python3
"""
Refactored Fundamental Analyzer
Uses centralized configuration and prompt management for investment analysis.
"""

import json
import openai
import markdown
from xhtml2pdf import pisa
from typing import List, Dict
import logging

from config_manager import config
from prompt_manager import prompt_manager

logger = logging.getLogger(__name__)

class FundamentalAnalyzer:
    """Performs fundamental investment analysis using AI and centralized configuration"""

    def __init__(self):
        self.ai_config = config.ai
        self.directories = config.directories

        # Set up OpenAI
        if self.ai_config.api_key:
            openai.api_key = self.ai_config.api_key
        else:
            raise ValueError("OpenAI API key not found in environment variables")

    def format_summaries(self, reports: List[Dict]) -> str:
        """Format report summaries for analysis prompts."""
        formatted = ""
        for entry in sorted(reports, key=lambda x: x.get("period", "")):
            period = entry.get("period", "")
            filing_type = entry.get("filing_type", "")
            summary = entry.get("summary", "").strip()
            formatted += f"\n\n==== {period} ({filing_type}) ====\n{summary}"
        return formatted

    def run_analysis(self, ticker: str, analysis_type: str) -> str:
        """Run fundamental analysis for a specific analysis type."""
        # Map analysis type keys to their full names from config
        analysis_config = config.get_analysis_types()
        if analysis_type in analysis_config:
            full_analysis_name = analysis_config[analysis_type]["name"]
        else:
            full_analysis_name = analysis_type  # fallback to original name

        # Load summaries using the full analysis name
        filename_pattern = config.get_file_naming_pattern("summary")
        json_filename = filename_pattern.format(
            ticker=ticker.lower(),
            analysis_type=full_analysis_name
        )
        json_path = self.directories.analysis_outputs / f"{json_filename}.json"

        if not json_path.exists():
            raise FileNotFoundError(f"Summary file not found: {json_path}")

        with open(json_path, 'r') as f:
            data = json.load(f)

        reports = data.get("reports", [])
        if not reports:
            raise ValueError(f"No reports found in {json_path}")

        # Format data for analysis
        formatted_data = self.format_summaries(reports)

        # Determine which prompt template to use (use original analysis_type for template mapping)
        template_name = f"{analysis_type}_analysis"  # stalwart_analysis or fastgrower_analysis

        try:
            prompt = prompt_manager.get_template(
                template_name,
                formatted_data=formatted_data
            )
        except ValueError as e:
            logger.error(f"Prompt template error: {e}")
            raise

        # Call OpenAI for analysis
        try:
            response = openai.chat.completions.create(
                model=self.ai_config.smart_model,
                messages=[
                    {"role": "system", "content": "You are an expert financial analyst providing investment recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=self.ai_config.max_completion_tokens,
                #temperature=self.ai_config.temperature # current model does not use temperature
            )

            analysis = response.choices[0].message.content
            logger.info(f"Successfully completed {analysis_type} analysis for {ticker}")
            return analysis

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            # Try with alternative model
            try:
                logger.info(f"Retrying with alternative model: {self.ai_config.alternative_model}")
                response = openai.chat.completions.create(
                    model=self.ai_config.alternative_model,
                    messages=[
                        {"role": "system", "content": "You are an expert financial analyst."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e2:
                logger.error(f"Alternative model also failed: {e2}")
                raise

    def save_analysis_outputs(self, ticker: str, analysis_type: str, analysis_content: str):
        """Save analysis results in multiple formats."""
        filename_pattern = config.get_file_naming_pattern("analysis")
        filename_base = filename_pattern.format(
            ticker=ticker.lower(),
            analysis_type=analysis_type
        )

        output_formats = config.get_output_formats()

        # Save TXT
        if "txt" in output_formats or True:  # Always save txt as backup
            txt_file = self.directories.analysis_outputs / f"{filename_base}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(analysis_content)
            logger.debug(f"Saved TXT: {txt_file}")

        # Save HTML
        if "html" in output_formats:
            html_content = markdown.markdown(analysis_content, extensions=['extra', 'tables'])
            html_full = self._create_analysis_html(html_content, ticker, analysis_type)

            html_file = self.directories.analysis_outputs / f"{filename_base}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_full)
            logger.debug(f"Saved HTML: {html_file}")

        # Save PDF
        if "pdf" in output_formats:
            html_content = markdown.markdown(analysis_content, extensions=['extra', 'tables'])
            html_full = self._create_analysis_html(html_content, ticker, analysis_type)

            pdf_file = self.directories.analysis_outputs / f"{filename_base}.pdf"
            with open(pdf_file, 'wb') as f:
                pisa_status = pisa.CreatePDF(html_full, dest=f)

            if pisa_status.err:
                logger.warning(f"PDF generation had errors for {pdf_file}")
            else:
                logger.debug(f"Saved PDF: {pdf_file}")

    def _create_analysis_html(self, content: str, ticker: str, analysis_type: str) -> str:
        """Create styled HTML document for analysis."""
        title = f"{ticker.upper()} - {analysis_type.replace('_', ' ').title()} Analysis"
        style_class = "stalwart" if "stalwart" in analysis_type else "fastgrower"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{ 
                    font-family: Georgia, serif; 
                    margin: 40px; 
                    line-height: 1.8; 
                    color: #333; 
                    max-width: 800px;
                }}
                h1, h2, h3 {{ 
                    color: #2c3e50; 
                    font-family: Arial, sans-serif;
                }}
                h1 {{ 
                    border-bottom: 3px solid #3498db; 
                    padding-bottom: 10px; 
                }}
                .stalwart h1 {{ border-bottom-color: #27ae60; }}
                .fastgrower h1 {{ border-bottom-color: #f39c12; }}
                
                .recommendation {{ 
                    background-color: #ecf0f1; 
                    padding: 20px; 
                    border-left: 5px solid #3498db; 
                    margin: 20px 0; 
                    font-weight: bold;
                }}
                .buy {{ border-left-color: #27ae60; background-color: #d5f4e6; }}
                .hold {{ border-left-color: #f39c12; background-color: #fef5e7; }}
                .avoid {{ border-left-color: #e74c3c; background-color: #fadbd8; }}
                
                blockquote {{ 
                    border-left: 4px solid #bdc3c7; 
                    margin: 0; 
                    padding-left: 20px; 
                    font-style: italic; 
                }}
                
                ul, ol {{ margin-left: 20px; }}
                li {{ margin-bottom: 8px; }}
                
                .footer {{ 
                    margin-top: 40px; 
                    padding-top: 20px; 
                    border-top: 1px solid #bdc3c7; 
                    font-size: 0.9em; 
                    color: #7f8c8d; 
                }}
            </style>
        </head>
        <body class="{style_class}">
            {content}
            <div class="footer">
                <p><em>Analysis generated by FundamentalAI System. This is not financial advice. Please consult with a qualified financial advisor before making investment decisions.</em></p>
            </div>
        </body>
        </html>
        """

    def analyze_company(self, ticker: str, analysis_types: List[str]) -> bool:
        """Run all specified analyses for a company."""
        available_types = list(config.get_analysis_types().keys())

        success_count = 0
        for analysis_type in analysis_types:
            if analysis_type not in available_types:
                logger.warning(f"Unknown analysis type: {analysis_type}. Available: {available_types}")
                continue

            try:
                logger.info(f"Running {analysis_type} analysis for {ticker}...")
                analysis_content = self.run_analysis(ticker, analysis_type)

                self.save_analysis_outputs(ticker, analysis_type, analysis_content)
                success_count += 1

                logger.info(f"✅ Completed {analysis_type} analysis for {ticker}")

            except Exception as e:
                logger.error(f"❌ Failed {analysis_type} analysis for {ticker}: {e}")

        if success_count > 0:
            logger.info(f"Successfully completed {success_count}/{len(analysis_types)} analyses for {ticker}")
            return True
        else:
            logger.error(f"All analyses failed for {ticker}")
            return False

    def get_available_analysis_types(self) -> List[str]:
        """Get list of available analysis types from configuration."""
        return list(config.get_analysis_types().keys())
