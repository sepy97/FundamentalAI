# FundamentalAI

**Fundamental analysis of companies for investment purposes via LLMs.**

FundamentalAI is an automated financial analysis system that downloads SEC filings (10-K and 10-Q reports), summarizes them using AI, and performs comprehensive fundamental investment analysis. The system supports both individual company analysis and batch processing, with configurable analysis types for different investment strategies.

## 🚀 Features

- **Automated SEC Filing Download**: Downloads and converts SEC filings (10-K, 10-Q) to PDF format
- **AI-Powered Summarization**: Uses OpenAI GPT models to create concise summaries of financial reports
- **Investment Analysis**: Performs fundamental analysis with different investment strategies:
  - **Stalwart Analysis**: Long-term analysis for established companies (10 years of data)
  - **Fast-Grower Analysis**: Growth-focused analysis for emerging companies (10 quarters of data)
- **Multiple Output Formats**: Generates analysis reports in HTML, PDF, JSON, and Markdown formats
- **Batch Processing**: Process multiple companies simultaneously
- **Configurable Pipeline**: Skip individual steps (download, summarization, analysis) as needed
- **Rate Limiting**: Respects SEC API rate limits and OpenAI usage guidelines

## 📋 Requirements

- Python 3.13
- OpenAI API key
- Playwright (for web scraping and PDF generation)
- Internet connection for SEC API access

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd FundamentalAI
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

4. **Set up your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Or create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## ⚙️ Configuration

The system uses a `config.yaml` file for all configuration settings. Key sections include:

### Company Settings
```yaml
companies:
  default_ticker: "PFE"
  batch_tickers: ["PFE", "AAPL", "AMZN", "CROX"]
```

### Analysis Types
```yaml
filings:
  counts:
    stalwart_years: 10      # Years of 10-K data for stalwart analysis
    fastgrower_quarters: 10 # Quarters of 10-Q data for fast-grower analysis
    fastgrower_context_years: 3 # Additional context years
```

### AI Configuration
```yaml
ai:
  openai:
    model: "gpt-4.1"
    smart_model: "gpt-5"
    summarization_model: "gpt-5-nano"
    max_completion_tokens: 4000
  processing:
    sleep_between_calls: 2
    max_chars_per_chunk: 15000
```

### SEC API Settings
```yaml
sec:
  user_agent: "FundamentalAI Bot/1.0 (your-email@example.com)"
  request_timeout: 30
  rate_limit_delay: 1.0
```

## 🚀 Usage

### Basic Usage

**Analyze a single company (full pipeline):**
```bash
python main.py --ticker AAPL
```

**Analyze multiple companies:**
```bash
python main.py --ticker AAPL MSFT GOOGL
```

**Use batch mode (processes all tickers from config):**
```bash
python main.py --batch
```

### Advanced Usage

**Skip certain pipeline steps:**
```bash
# Skip download if PDFs already exist
python main.py --ticker AAPL --skip-download

# Only run analysis (assumes summaries exist)
python main.py --ticker AAPL --skip-download --skip-summary

# Skip analysis, only download and summarize
python main.py --ticker AAPL --skip-analysis
```

**Enable verbose logging:**
```bash
python main.py --ticker AAPL --verbose
```

**Use custom configuration file:**
```bash
python main.py --ticker AAPL --config custom_config.yaml
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--ticker`, `-t` | Ticker symbol(s) to process |
| `--batch`, `-b` | Process all tickers from config file |
| `--skip-download` | Skip PDF download step |
| `--skip-summary` | Skip summarization step |
| `--skip-analysis` | Skip analysis step |
| `--config` | Path to configuration file (default: config.yaml) |
| `--verbose`, `-v` | Enable verbose logging |

## 📁 Project Structure

```
FundamentalAI/
├── main.py                    # Main orchestrator and CLI entry point
├── config.yaml               # Configuration file
├── config_manager.py         # Configuration management
├── financial_pdf_downloader.py # SEC filing downloader
├── pdf_summarizer.py         # AI-powered PDF summarization
├── fundamental_analyzer.py   # Investment analysis engine
├── prompt_manager.py         # AI prompt templates
├── requirements.txt          # Python dependencies
├── reports/                  # Downloaded SEC filings (PDF/HTML)
│   ├── aapl/
│   ├── pfe/
│   └── ...
└── analysis_outputs/         # Generated analysis reports
    ├── {ticker}_stalwart_analysis.{format}
    ├── {ticker}_fastgrower_analysis.{format}
    └── ...
```

## 📊 Analysis Types

### Stalwart Analysis
- **Purpose**: Long-term investment analysis for established, large companies
- **Data**: 10 years of annual 10-K filings
- **Focus**: Business consistency, operational efficiency, stability, competitive moats
- **Output**: Buy/Hold/Avoid recommendation with detailed reasoning

### Fast-Grower Analysis
- **Purpose**: Growth-focused analysis for emerging or rapidly expanding companies
- **Data**: 10 quarters of 10-Q filings plus 3 years of context
- **Focus**: Growth momentum, scalability, market expansion, competitive positioning
- **Output**: Buy/Hold/Avoid recommendation with growth assessment

## 📈 Output Formats

The system generates analysis reports in multiple formats:

- **HTML**: Interactive web-friendly format
- **PDF**: Print-ready professional reports
- **JSON**: Machine-readable structured data
- **Markdown**: Text-based format for documentation

Reports are saved in the `analysis_outputs/` directory with descriptive filenames.

## 🔧 Customization

### Adding Custom Analysis Types

1. **Update `prompt_manager.py`** to add new prompt templates
2. **Modify `config.yaml`** to define data requirements
3. **Update `fundamental_analyzer.py`** to handle the new analysis type

### Custom Prompts

Edit the prompt templates in `prompt_manager.py` to customize the AI analysis behavior:

```python
def _custom_analysis_template(self) -> str:
    return """Your custom analysis prompt here..."""
```

## 🚨 Important Notes

### SEC API Compliance
- The system respects SEC API rate limits (1 second delay between requests)
- Uses appropriate User-Agent headers as required by SEC
- Downloads are throttled to avoid overwhelming SEC servers

### API Usage
- OpenAI API calls are rate-limited to prevent quota issues
- Large documents are chunked to fit within token limits
- Retry logic handles temporary API failures

### Legal Disclaimer
This tool is for educational and research purposes only. It does not provide financial advice. Always consult with qualified financial professionals before making investment decisions.

## 📝 Logging

The system maintains detailed logs in `financial_analysis.log` and outputs to console. Logs include:
- Download progress and status
- Summarization results
- Analysis completion status
- Error messages and debugging information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
