#!/usr/bin/env python3
"""
Prompt templates and management for financial analysis.
All AI prompts are centralized here for easy modification and maintenance.
"""

from typing import Dict, Any

class PromptManager:
    """Manages all prompt templates for financial analysis"""

    def __init__(self):
        self.templates = {
            "basic_summary": self._basic_summary_template(),
            "stalwart_analysis": self._stalwart_analysis_template(),
            "fastgrower_analysis": self._fastgrower_analysis_template()
        }

    def _basic_summary_template(self) -> str:
        """Template for basic document summarization"""
        return """Summarize this {filing_type} filing for {ticker} from {period}. Focus on:

1. Business or operational updates
2. Management tone and strategic messaging  
3. Notable changes or risks
4. Performance or guidance signals

Keep the summary concise but comprehensive, highlighting the most important information for investors.

Filing Content:
{content}"""

    def _stalwart_analysis_template(self) -> str:
        """Template for stalwart (long-term) investment analysis"""
        return """You are a long-term investor analyzing a large, established company (a stalwart) over a 10-year period.

Here are yearly summaries from the company's 10-K reports, including business description, management commentary, financial health, and risk factors.

Use this information to assess the company's quality, stability, and investment potential. Pay particular attention to:

1. **Business Consistency**: How stable and predictable is the core business model? Look for:
   - Consistent revenue streams and market position
   - Stable management and strategic direction
   - Predictable cash flows and dividend history

2. **Operational Efficiency & Capital Allocation**: How well does management deploy capital? Examine:
   - Return on invested capital trends
   - Debt management and balance sheet strength
   - Share buybacks, dividends, and reinvestment strategies
   - Operational improvements and cost management

3. **Stability and Resilience**: How well does the company weather economic cycles? Consider:
   - Performance during market downturns
   - Competitive moat strength and sustainability
   - Regulatory and industry risk management
   - Geographic and product diversification

4. **Valuation and Growth Signals**: What are the long-term value creation prospects? Analyze:
   - Sustainable competitive advantages
   - Market expansion opportunities
   - Innovation and adaptation capabilities
   - Long-term earnings growth potential

**SELL SIGNALS** - Flag any of these red flags:
- Declining market share or competitive position
- Persistent margin compression
- Excessive debt or poor capital allocation
- Management turnover or strategic confusion
- Regulatory threats or industry disruption

**CONCLUSION**: Based on your analysis, provide a clear recommendation: **Buy**, **Hold**, or **Avoid**.

Include specific reasoning for your recommendation and highlight the most compelling investment thesis or concerns.

**Company Data:**
{formatted_data}"""

    def _fastgrower_analysis_template(self) -> str:
        """Template for fast-grower investment analysis"""
        return """You are analyzing a fast-growing company based on recent 10-K and 10-Q summaries (last 10 quarters). These include management discussions of growth, strategy, operations, and risks.

Use this information to evaluate whether the company qualifies as a legitimate "fast-grower" with long-term upside potential. Focus on:

1. **Growth Momentum**: Is the growth rate accelerating and sustainable? Examine:
   - Revenue growth trends and acceleration
   - Market share gains and customer acquisition
   - Product/service adoption rates
   - Geographic expansion progress

2. **Expansion Quality & Market Fit**: Is the growth profitable and strategic? Analyze:
   - Unit economics and profitability trends
   - Market size and penetration opportunity
   - Product-market fit indicators
   - Customer retention and satisfaction metrics

3. **Scalability & Capital Discipline**: Can the business scale efficiently? Consider:
   - Operating leverage and margin expansion
   - Capital efficiency and asset utilization
   - Technology and infrastructure scalability
   - Working capital management

4. **Moat Development & Visibility**: Is the company building sustainable advantages? Look for:
   - Network effects or platform benefits
   - Brand strength and customer loyalty
   - Intellectual property and innovation
   - Barriers to entry and competitive positioning

**SELL SIGNALS** - Flag any of these warning signs:
- Decelerating growth without clear explanation
- Deteriorating unit economics or margins
- Excessive capital requirements for growth
- Increased competition or market saturation
- Management overpromising or lack of execution

**CONCLUSION**: Based on your analysis, provide a clear recommendation: **Buy**, **Hold**, or **Avoid**.

Assess whether this truly qualifies as a fast-grower with 10+ year potential or if it's a short-term momentum play.

**Company Data:**
{formatted_data}"""

    def get_template(self, template_name: str, **kwargs) -> str:
        """Get a formatted prompt template"""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found. Available: {list(self.templates.keys())}")

        template = self.templates[template_name]

        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required parameter {e} for template '{template_name}'")

    def list_templates(self) -> list:
        """List available template names"""
        return list(self.templates.keys())

    def add_custom_template(self, name: str, template: str):
        """Add a custom template"""
        self.templates[name] = template

    def get_required_params(self, template_name: str) -> list:
        """Get list of required parameters for a template"""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        import re
        template = self.templates[template_name]
        # Find all {param} patterns
        params = re.findall(r'\{(\w+)\}', template)
        return list(set(params))  # Remove duplicates

# Global prompt manager instance
prompt_manager = PromptManager()
