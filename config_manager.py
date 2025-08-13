#!/usr/bin/env python3
"""
Configuration manager for FundamentalAI system.
Handles loading and validation of configuration from YAML files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class SECConfig:
    """SEC API configuration"""
    company_tickers_url: str
    submissions_url: str
    archives_url: str
    user_agent: str
    request_timeout: int
    rate_limit_delay: float

@dataclass
class AIConfig:
    """AI processing configuration"""
    model: str
    smart_model: str
    summarization_model: str
    alternative_model: str
    max_completion_tokens: int
    temperature: float
    sleep_between_calls: int
    max_chars_per_chunk: int
    max_retries: int
    api_key: Optional[str] = None

@dataclass
class PDFConfig:
    """PDF generation configuration"""
    wait_after_load: float
    paper_format: str
    print_background: bool
    viewport_width: int
    viewport_height: int

@dataclass
class FilingConfig:
    """Filing configuration"""
    annual_type: str
    quarterly_type: str
    stalwart_years: int
    fastgrower_quarters: int
    fastgrower_context_years: int #Number of recent annual (10-K) reports to include for context in the fast-grower analysis.

@dataclass
class DirectoryConfig:
    """Directory paths configuration"""
    reports: Path
    analysis_outputs: Path
    config: Path
    templates: Path

class ConfigManager:
    """Centralized configuration management"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _validate_config(self):
        """Validate required configuration sections"""
        required_sections = ['companies', 'filings', 'sec', 'pdf', 'ai', 'directories']
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required configuration section: {section}")

    @property
    def sec(self) -> SECConfig:
        """SEC API configuration"""
        sec_config = self._config['sec']
        return SECConfig(
            company_tickers_url=sec_config['base_urls']['company_tickers'],
            submissions_url=sec_config['base_urls']['submissions'],
            archives_url=sec_config['base_urls']['archives'],
            user_agent=sec_config['user_agent'],
            request_timeout=sec_config['request_timeout'],
            rate_limit_delay=sec_config['rate_limit_delay']
        )

    @property
    def ai(self) -> AIConfig:
        """AI processing configuration"""
        ai_config = self._config['ai']
        openai_config = ai_config['openai']
        processing_config = ai_config['processing']

        return AIConfig(
            model=openai_config['model'],
            smart_model=openai_config['smart_model'],
            summarization_model=openai_config['summarization_model'],
            alternative_model=openai_config['alternative_model'],
            max_completion_tokens=openai_config['max_completion_tokens'],  # Fixed to match config file
            temperature=openai_config['temperature'],
            sleep_between_calls=processing_config['sleep_between_calls'],
            max_chars_per_chunk=processing_config['max_chars_per_chunk'],
            max_retries=processing_config['max_retries'],
            api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI")
        )

    @property
    def pdf(self) -> PDFConfig:
        """PDF generation configuration"""
        pdf_config = self._config['pdf']
        viewport = pdf_config['viewport']

        return PDFConfig(
            wait_after_load=pdf_config['wait_after_load'],
            paper_format=pdf_config['paper_format'],
            print_background=pdf_config['print_background'],
            viewport_width=viewport['width'],
            viewport_height=viewport['height']
        )

    @property
    def filings(self) -> FilingConfig:
        """Filing configuration"""
        filings_config = self._config['filings']
        types = filings_config['types']
        counts = filings_config['counts']

        return FilingConfig(
            annual_type=types['annual'],
            quarterly_type=types['quarterly'],
            stalwart_years=counts['stalwart_years'],
            fastgrower_quarters=counts['fastgrower_quarters'],
            fastgrower_context_years=counts['fastgrower_context_years']
        )

    @property
    def directories(self) -> DirectoryConfig:
        """Directory configuration"""
        dir_config = self._config['directories']

        return DirectoryConfig(
            reports=Path(dir_config['reports']),
            analysis_outputs=Path(dir_config['analysis_outputs']),
            config=Path(dir_config['config']),
            templates=Path(dir_config['templates'])
        )

    def get_default_ticker(self) -> str:
        """Get default ticker symbol"""
        return self._config['companies']['default_ticker']

    def get_batch_tickers(self) -> list:
        """Get list of tickers for batch processing"""
        return self._config['companies'].get('batch_tickers', [])

    def get_analysis_types(self) -> Dict[str, Any]:
        """Get analysis type configurations"""
        return self._config['analysis_types']

    def get_output_formats(self) -> list:
        """Get configured output formats"""
        return self._config['output']['formats']

    def get_file_naming_pattern(self, pattern_type: str) -> str:
        """Get file naming pattern"""
        return self._config['output']['file_naming'][pattern_type]

# Global configuration instance
config = ConfigManager()
