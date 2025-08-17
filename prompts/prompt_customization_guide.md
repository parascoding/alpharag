# LLM Prompt Customization Guide

## Overview

The AlphaRAG system now supports **external prompt templates** that can be modified without touching any code. This allows you to easily customize the AI analysis prompts for different investment strategies, risk profiles, or analysis styles.

## How It Works

1. **Prompt Manager** (`src/prompt_manager.py`) loads templates from `prompts/` directory
2. **LLM Providers** use the prompt manager instead of hardcoded prompts
3. **Template Files** in `prompts/` can be edited directly
4. **Automatic Fallback** to default prompts if template loading fails

## Files Created

### 1. `prompts/llm_analysis_prompt.txt`
- **Main prompt template** used by all LLM providers
- Contains the investment analysis instructions sent to Claude/Gemini/GPT
- Supports variable substitution for dynamic data

### 2. `src/prompt_manager.py`
- **Prompt management system** that loads templates from files
- Handles template parsing, caching, and formatting
- Provides fallback mechanisms if files are missing

### 3. Updated `src/llm_providers/base_llm_provider.py`
- **Modified to use prompt manager** instead of hardcoded prompts
- All LLM providers (Claude, Gemini, GPT) inherit this behavior

## How to Customize Prompts

### Quick Customization
1. **Edit** `prompts/llm_analysis_prompt.txt`
2. **Modify** the sections you want to change
3. **Save** the file
4. **Run** the analysis - changes take effect immediately

### Template Variables Available
- `{total_investment}` - Total amount invested
- `{total_current_value}` - Current portfolio value  
- `{total_pnl_percent}` - P&L percentage
- `{portfolio_holdings}` - Formatted list of holdings
- `{market_data}` - Current market prices and technical data
- `{sentiment_data}` - News sentiment analysis
- `{available_cash}` - Available cash for new investments

### Example Customizations

#### Conservative Investment Focus
```
1. RISK ASSESSMENT PRIORITY:
Before any recommendations, assess risk levels:
- Portfolio concentration risk
- Sector exposure analysis  
- Debt-to-equity concerns
- Market volatility impact

2. CONSERVATIVE STOCK RECOMMENDATIONS:
Focus on dividend-paying, low-volatility stocks:
- Dividend Yield: Minimum 3%+
- Beta: Less than 1.2 preferred
- Debt-to-Equity: Less than 0.5 preferred
```

#### Growth-Focused Analysis  
```
1. GROWTH STOCK IDENTIFICATION:
Prioritize high-growth potential stocks:
- Revenue Growth: 15%+ YoY preferred
- Earnings Growth: 20%+ YoY preferred  
- ROE: 15%+ preferred
- Sector: Technology, Healthcare, Consumer Discretionary focus

2. MOMENTUM ANALYSIS:
- RSI: Look for oversold conditions (RSI < 30)
- Price trends: Identify breakout patterns
- Volume analysis: Confirm buying/selling pressure
```

#### Value Investment Strategy
```
1. VALUE SCREENING CRITERIA:
Focus on undervalued opportunities:
- P/E Ratio: Below sector average
- P/B Ratio: Less than 2.0 preferred
- P/S Ratio: Below peer group average
- Free Cash Flow: Positive and growing

2. MARGIN OF SAFETY:
- Target Price: At least 20% below intrinsic value
- Downside Protection: Strong balance sheet required
```

## Advanced Customizations

### Multiple Prompt Templates
Create specialized templates for different scenarios:

- `prompts/conservative_analysis_prompt.txt` - For risk-averse investors
- `prompts/aggressive_growth_prompt.txt` - For growth-focused analysis  
- `prompts/value_investing_prompt.txt` - For value investment strategy
- `prompts/sector_rotation_prompt.txt` - For sector-specific analysis

### Dynamic Template Selection
Modify `prompt_manager.py` to select templates based on:
- Portfolio size
- Risk tolerance settings
- Market conditions
- Investment goals

### Custom Formatting Functions
Add new formatting functions in `prompt_manager.py` for:
- Technical analysis data
- Financial ratios presentation
- Risk metrics display
- Sector comparison tables

## Testing Your Changes

### 1. Validate Template Syntax
```bash
python -c "from src.prompt_manager import PromptManager; pm = PromptManager(); print('Template loaded:', pm.load_prompt_template('llm_analysis_prompt') is not None)"
```

### 2. Test Analysis with Custom Prompt
```bash
python main.py --mode analyze
```

### 3. Check Logs for Template Loading
Look for these log messages:
- `"Loaded prompt template: llm_analysis_prompt"` ✅ Success
- `"Using external prompt template"` ✅ Template being used
- `"Failed to load external prompt template"` ❌ Error - check file

## Troubleshooting

### Template Not Loading
1. **Check file path**: `prompts/llm_analysis_prompt.txt` exists?
2. **Check syntax**: Template section marked with `# PROMPT TEMPLATE:`?
3. **Check permissions**: File readable?

### Variable Substitution Errors
1. **Check variable names**: Use exact names like `{total_investment}`
2. **Check formatting**: Use proper Python string formatting syntax
3. **Check required variables**: All template variables have data?

### Fallback Mode Triggered
1. **Template file missing**: Create `prompts/llm_analysis_prompt.txt`
2. **Template format invalid**: Follow the example format
3. **Permissions issue**: Ensure file is readable

## Benefits of External Prompts

### ✅ **Easy Customization**
- Modify investment analysis style without code changes
- Quick A/B testing of different prompt strategies
- No need to restart application

### ✅ **Investment Strategy Flexibility**  
- Switch between conservative/aggressive analysis
- Customize for different market conditions
- Adapt prompts for specific sectors or themes

### ✅ **Risk Management**
- Code changes can't break the prompt system
- Automatic fallback to working defaults
- Template validation before use

### ✅ **Collaboration Friendly**
- Investment advisors can modify prompts directly
- Version control for prompt changes
- Easy backup and restore of prompt templates

## Next Steps

1. **Try different prompt styles** - Conservative vs aggressive analysis
2. **Create specialized templates** - For different investment strategies  
3. **Add custom variables** - Extend prompt manager with new data
4. **Implement template selection** - Dynamic prompt choice based on criteria

This system gives you full control over how the AI analyzes your portfolio, without needing to understand or modify the underlying code!