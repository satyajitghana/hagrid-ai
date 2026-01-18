"""
Intraday Trading Cycle Workflow

HAGRID TRADING LLC - Hierarchical Multi-Agent Analysis System

This workflow orchestrates the morning analysis cycle with a hierarchical team structure:

1. Regime Check - Determine market conditions (First!)
2. Department Analysis (In Parallel):
   - Technical Department: Technical + Microstructure + Correlation analysts
   - Fundamentals Department: Fundamentals + Sector + Events analysts
   - Market Intelligence Department: News + Macro + Institutional analysts
   - Derivatives Department: Options analyst
3. CIO Review - Chief Investment Officer synthesizes all department reports
4. Risk Management - Validate and size trades

The execution step is handled by the executor_workflow to separate
analysis from execution.

Session Management:
- Uses date-based session_id (e.g., "2025-01-19")
- Stores picks, regime, department_reports in session_state
- Access past runs via workflow history (last 5 trading days)
"""

import json
import re
from datetime import date, datetime
from pathlib import Path

from agno.workflow import Workflow, Step
from agno.team import Team
from agno.workflow.types import StepInput, StepOutput

from workflows import workflow_db, agent_db, logger

# Regime Agent (runs first)
from agents.departments.regime.agent import regime_agent

# Department Analysts
from agents.departments.technical.agent import technical_agent
from agents.departments.options.agent import options_agent
from agents.departments.fundamentals.agent import fundamentals_agent
from agents.departments.sector.agent import sector_agent
from agents.departments.microstructure.agent import microstructure_agent
from agents.departments.macro.agent import macro_agent
from agents.departments.institutional.agent import institutional_agent
from agents.departments.news.agent import news_agent
from agents.departments.events.agent import events_agent
from agents.departments.correlation.agent import correlation_agent
from agents.departments.position.agent import position_agent

# Department Managers
from agents.managers.technical_manager import technical_manager
from agents.managers.fundamentals_manager import fundamentals_manager
from agents.managers.market_intel_manager import market_intel_manager
from agents.managers.derivatives_manager import derivatives_manager
from agents.managers.cio import chief_investment_officer

# Risk Agent
from agents.meta.risk.agent import risk_agent

from core.config import get_settings

settings = get_settings()

# ==============================================================================
# COMPREHENSIVE INTRADAY ANALYSIS PROMPT
# ==============================================================================

INTRADAY_ANALYSIS_PROMPT = """
# HAGRID TRADING LLC - Daily Trading Analysis

**Date**: {date}
**Objective**: Generate 10-15 high-conviction intraday trades from NIFTY 100
**Target Return**: 5% daily portfolio return
**Risk Parameters**: Max {max_risk_pct}% risk per trade, Max {max_stocks} positions

---

## ORGANIZATIONAL STRUCTURE

### DEPARTMENT HEADS REPORT TO CIO:

**1. HEAD OF TECHNICAL ANALYSIS** - Reviews:
   - Technical Analyst (price action, indicators, setups)
   - Microstructure Analyst (order flow, liquidity)
   - Correlation Analyst (pairs trading)

**2. HEAD OF FUNDAMENTAL RESEARCH** - Reviews:
   - Fundamentals Analyst (company quality, earnings)
   - Sector Analyst (sector rotation)
   - Events Analyst (corporate calendar)

**3. HEAD OF MARKET INTELLIGENCE** - Reviews:
   - News Analyst (catalysts, sentiment)
   - Macro Analyst (global markets, FX)
   - Institutional Analyst (FII/DII flows)

**4. HEAD OF DERIVATIVES** - Reviews:
   - Options Analyst (PCR, OI, Greeks)

---

## ANALYSIS WORKFLOW

### PHASE 1: Market Regime Assessment
Regime Agent determines current conditions:
- TRENDING_UP / TRENDING_DOWN / RANGING
- HIGH_VOLATILITY / LOW_VOLATILITY
This sets the strategic bias for all subsequent analysis.

### PHASE 2: Department Analysis (Parallel)
Each department team analyzes ALL NIFTY 100 stocks:
- Analysts do deep-dive research
- Department managers synthesize findings
- Each department produces ranked recommendations

### PHASE 3: CIO Decision
Chief Investment Officer:
- Reviews all department reports
- Identifies consensus picks (multiple departments agree)
- Resolves conflicts between departments
- Selects final 10-15 trades with conviction levels

### PHASE 4: Risk Validation
Risk Agent validates:
- Position sizing based on ATR
- Portfolio diversification
- Total risk exposure limits

---

## OUTPUT REQUIREMENTS

### FOR EACH ANALYST:
Provide comprehensive analysis for EVERY relevant stock including:
- Symbol and current price
- Department-specific score and signal
- Detailed reasoning with data points
- Entry/Exit levels where applicable
- Confidence level (0.0-1.0)

### FOR EACH DEPARTMENT MANAGER:
Synthesize team analysis into:
- Top 10 LONG candidates with scores
- Top 5 SHORT candidates with scores
- Department conviction assessment
- Key risks and opportunities

### FOR CIO:
Deliver final portfolio:
- 10-15 trades ranked by multi-factor conviction
- Clear entry, stop loss, take profit levels
- Position sizing recommendations
- Sector allocation breakdown
- Risk summary

---

## QUALITY STANDARDS

✓ Every pick must have stop loss defined
✓ Minimum 1.5:1 reward-to-risk ratio
✓ At least 3 departments must agree for HIGH conviction
✓ Maximum 3 positions per sector
✓ Clear, specific reasoning for each trade

---

## LET'S BEGIN THE ANALYSIS
"""


def get_intraday_prompt() -> str:
    """Generate the intraday analysis prompt with current settings."""
    return INTRADAY_ANALYSIS_PROMPT.format(
        date=date.today().isoformat(),
        max_risk_pct=settings.MAX_RISK_PER_TRADE_PERCENT,
        max_stocks=settings.MAX_STOCKS_PER_DAY,
    )


# ==============================================================================
# FUNCTION STEPS
# ==============================================================================

def store_regime_in_state(step_input: StepInput) -> StepOutput:
    """Store regime check output into session state."""
    regime_result = step_input.previous_step_content
    if step_input.workflow_session:
        step_input.workflow_session.session_data["regime"] = regime_result
    return StepOutput(content=regime_result)


def store_picks_in_state(step_input: StepInput) -> StepOutput:
    """Store risk-validated picks into session state."""
    picks_result = step_input.previous_step_content
    if step_input.workflow_session:
        step_input.workflow_session.session_data["picks"] = picks_result
        step_input.workflow_session.session_data["risk_validated"] = True
    return StepOutput(content=picks_result)


def save_output_to_file(step_input: StepInput) -> StepOutput:
    """Save the final workflow output to a dated file."""
    content = step_input.previous_step_content or ""
    session_data = step_input.workflow_session.session_data if step_input.workflow_session else {}

    # Create dated filename: YYYY-MM-DD_HHMMSS_intraday_analysis.md
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{timestamp}_intraday_analysis.md"
    filepath = settings.OUTPUT_DIR / filename

    # Also save JSON with structured data
    json_filename = f"{timestamp}_intraday_analysis.json"
    json_filepath = settings.OUTPUT_DIR / json_filename

    # Write markdown report
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Hagrid Intraday Analysis\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(content)

    # Write structured JSON
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "session_id": step_input.workflow_session.session_id if step_input.workflow_session else None,
        "regime": session_data.get("regime"),
        "picks": session_data.get("picks", []),
        "risk_validated": session_data.get("risk_validated", False),
        "content": content,
    }
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, default=str)

    logger.info(f"Workflow output saved to {filepath}")
    logger.info(f"Workflow JSON saved to {json_filepath}")

    return StepOutput(
        content=f"Output saved to:\n- {filepath}\n- {json_filepath}\n\n{content}"
    )


# ==============================================================================
# DEPARTMENT TEAMS (Hierarchical Structure)
# ==============================================================================

# 1. TECHNICAL ANALYSIS DEPARTMENT
# Manager: Head of Technical Analysis
# Team: Technical Analyst, Microstructure Analyst, Correlation Analyst
technical_department = Team(
    name="Technical Analysis Department",
    model="google:gemini-3-pro-preview",
    members=[
        technical_manager,    # Head coordinates the department
        technical_agent,      # Price action, indicators, setups
        microstructure_agent, # Order flow, liquidity, bid-ask
        correlation_agent,    # Pairs trading opportunities
    ],
    description="""Technical Analysis Department at Hagrid Trading LLC.

The Head of Technical Analysis coordinates 3 analysts:
1. Technical Analyst - Price action, indicators (RSI, MACD, MAs), chart patterns
2. Microstructure Analyst - Order flow, bid-ask spreads, VWAP, liquidity
3. Correlation Analyst - Pairs trading, spread analysis, mean reversion

DEPARTMENT OBJECTIVE:
Analyze ALL NIFTY 100 stocks from a technical perspective and identify:
- Stocks with strong technical setups (breakouts, breakdowns, trend-continuation)
- Stocks with favorable order flow (buying/selling pressure)
- Pairs trading opportunities with statistical edge

OUTPUT: Department report with TOP 10 LONG and TOP 5 SHORT candidates ranked by technical conviction.""",

    db=agent_db,
    delegate_task_to_all_members=True,
    share_member_interactions=True,
    session_state={"technical_picks": []},
)


# 2. FUNDAMENTALS DEPARTMENT
# Manager: Head of Fundamental Research
# Team: Fundamentals Analyst, Sector Analyst, Events Analyst
fundamentals_department = Team(
    name="Fundamentals Department",
    model="google:gemini-3-pro-preview",
    members=[
        fundamentals_manager,  # Head coordinates the department
        fundamentals_agent,  # Company quality, earnings, valuations
        sector_agent,        # Sector rotation, relative strength
        events_agent,        # Corporate events, earnings calendar
    ],
    description="""Fundamental Research Department at Hagrid Trading LLC.

The Head of Fundamental Research coordinates 3 analysts:
1. Fundamentals Analyst - Earnings quality, valuations, balance sheet health
2. Sector Analyst - Sector trends, rotation signals, relative strength
3. Events Analyst - Earnings dates, dividends, buybacks, corporate actions

DEPARTMENT OBJECTIVE:
Analyze ALL NIFTY 100 stocks from a fundamental perspective and identify:
- Quality stocks (strong fundamentals = prefer longs, avoid shorts)
- Weak stocks (poor fundamentals = prefer shorts, avoid longs)
- Event-driven opportunities (pre-earnings, dividends)
- Sector trends (which sectors to favor/avoid)

OUTPUT: Department report with fundamental quality grades (A/B/C/D) for each stock
and sector recommendations.""",

    db=agent_db,
    delegate_task_to_all_members=True,
    share_member_interactions=True,
    session_state={"fundamental_grades": {}},
)


# 3. MARKET INTELLIGENCE DEPARTMENT
# Manager: Head of Market Intelligence
# Team: News Analyst, Macro Analyst, Institutional Analyst
market_intel_department = Team(
    name="Market Intelligence Department",
    model="google:gemini-3-pro-preview",
    members=[
        market_intel_manager,  # Head coordinates the department
        news_agent,          # Breaking news, sentiment, catalysts
        macro_agent,         # Global markets, USDINR, crude, VIX
        institutional_agent, # FII/DII flows, bulk/block deals
    ],
    description="""Market Intelligence Department at Hagrid Trading LLC.

The Head of Market Intelligence coordinates 3 analysts:
1. News Analyst - Breaking news, sentiment, broker ratings, catalysts
2. Macro Analyst - US markets, USDINR, crude oil, gold, VIX
3. Institutional Analyst - FII/DII flows, bulk deals, holding patterns

DEPARTMENT OBJECTIVE:
Provide market context and identify:
- Overall market risk sentiment (Risk-On/Risk-Off)
- Stocks with positive/negative news catalysts
- Stocks with institutional support/distribution
- Macro factors affecting specific sectors (FX, commodities)

OUTPUT: Market overview + stock-specific intelligence for all stocks with
significant news/flow activity.""",

    db=agent_db,
    delegate_task_to_all_members=True,
    share_member_interactions=True,
    session_state={"market_sentiment": "NEUTRAL"},
)


# 4. DERIVATIVES DEPARTMENT
# Manager: Head of Derivatives
# Team: Options Analyst
derivatives_department = Team(
    name="Derivatives Department",
    model="google:gemini-3-pro-preview",
    members=[
        derivatives_manager,  # Head coordinates the department
        options_agent,  # Options flow, PCR, OI, max pain, Greeks
    ],
    description="""Derivatives Research Department at Hagrid Trading LLC.

The Head of Derivatives coordinates the Options Analyst:
1. Options Analyst - PCR analysis, OI distribution, max pain, IV rank

DEPARTMENT OBJECTIVE:
Analyze options data for ALL NIFTY 100 stocks with active options:
- Identify bullish/bearish options positioning
- Find support/resistance from OI distribution
- Track unusual options activity
- Assess IV for trade timing

OUTPUT: Options positioning score for each stock and index-level
derivatives overview.""",

    db=agent_db,
    delegate_task_to_all_members=True,
    share_member_interactions=True,
    session_state={"options_positioning": {}},
)


# ==============================================================================
# RESEARCH COUNCIL (Top-Level Team with CIO)
# ==============================================================================

# The CIO leads the Research Council which includes all department teams
# This is the hierarchical structure: CIO -> Department Managers -> Analysts
research_council = Team(
    name="Hagrid Research Council",
    model="google:gemini-3-pro-preview",
    members=[
        chief_investment_officer,  # CIO coordinates all departments
        technical_department,    # Technical Analysis Department
        fundamentals_department, # Fundamentals Department
        market_intel_department, # Market Intelligence Department
        derivatives_department,  # Derivatives Department
        position_agent,          # Position management for existing positions
    ],
    description="""The Hagrid Trading LLC Research Council.

LED BY: Chief Investment Officer (CIO)

DEPARTMENT TEAMS:
1. Technical Analysis Department (3 analysts + manager)
2. Fundamentals Department (3 analysts + manager)
3. Market Intelligence Department (3 analysts + manager)
4. Derivatives Department (1 analyst + manager)
+ Position Analyst for existing position management

WORKFLOW:
1. Each department conducts parallel analysis of NIFTY 100
2. Department managers synthesize and rank their findings
3. CIO reviews all department reports
4. CIO identifies consensus picks across departments
5. CIO resolves conflicts and makes final selections
6. CIO outputs 10-15 high-conviction trades

MULTI-FACTOR SCORING:
- Technical Score: ±5 (from Technical Dept)
- Fundamental Score: ±3 (from Fundamentals Dept)
- Market Intel Score: ±3 (from Market Intel Dept)
- Derivatives Score: ±3 (from Derivatives Dept)
- MAX SCORE: 14 points

CONVICTION LEVELS:
- HIGH (≥8 points, 3+ departments agree): Full position
- MEDIUM (5-7 points): Half position
- LOW (<5 points): Do not trade

The CIO's final output goes to Risk Management for validation.""",

    db=agent_db,
    delegate_task_to_all_members=True,
    add_team_history_to_members=True,
    num_team_history_runs=3,
    share_member_interactions=True,
    session_state={
        "market_context": {},
        "department_reports": {},
        "cio_picks": [],
    },
)


# ==============================================================================
# WORKFLOW DEFINITION
# ==============================================================================

intraday_workflow = Workflow(
    name="Intraday Trading Cycle",
    db=workflow_db,

    # Session state shared across all steps
    session_state={
        "picks": [],
        "regime": None,
        "department_reports": {},
        "cio_analysis": None,
        "risk_validated": False,
    },

    # Enable workflow history for pattern analysis
    add_workflow_history_to_steps=True,
    num_history_runs=5,  # Last 5 trading days

    steps=[
        # Step 1: Determine Market Regime
        Step(
            name="Regime Check",
            agent=regime_agent,
            description="Determine current market regime (TRENDING_UP, TRENDING_DOWN, RANGING, HIGH_VOL, LOW_VOL)"
        ),
        # Step 2: Store regime in session state
        Step(
            name="Store Regime",
            executor=store_regime_in_state,
            description="Store regime result in session state for other workflows"
        ),
        # Step 3: Research Council Analysis (Hierarchical Multi-Agent)
        Step(
            name="Research Council Analysis",
            team=research_council,
            description="""Hierarchical multi-agent analysis:
            - 4 Department Teams analyze NIFTY 100 in parallel
            - Each Department Manager synthesizes their team's findings
            - CIO reviews all department reports and selects 10-15 trades"""
        ),
        # Step 4: Risk Management
        Step(
            name="Risk Management",
            agent=risk_agent,
            description="Validate CIO picks: position sizing, portfolio constraints, risk limits"
        ),
        # Step 5: Store final picks
        Step(
            name="Store Picks",
            executor=store_picks_in_state,
            description="Store risk-validated picks in session state for executor workflow"
        ),
        # Step 6: Save output to file
        Step(
            name="Save Output",
            executor=save_output_to_file,
            description="Save analysis results to dated file in .hagrid/outputs/"
        ),
    ]
)


# ==============================================================================
# RUN FUNCTION
# ==============================================================================

async def run_intraday_analysis(input_text: str = None) -> dict:
    """
    Run the intraday analysis workflow.

    Args:
        input_text: Optional custom input. If None, uses comprehensive prompt.

    Returns:
        dict with workflow result, session info, and output file paths
    """
    # Pre-flight check: ensure Fyers client is authenticated
    from core.fyers_client import ensure_authenticated
    await ensure_authenticated()

    today = date.today().isoformat()

    if input_text is None:
        input_text = get_intraday_prompt()

    logger.info(f"Starting intraday analysis workflow for {today}")

    result = await intraday_workflow.arun(
        input=input_text,
        session_id=today
    )

    result_content = result.content if result else ""

    # Extract output file paths from result
    output_file = None
    json_file = None
    if "Output saved to:" in result_content:
        match = re.search(r'\.hagrid/outputs/[\w\-_]+\.md', result_content)
        if match:
            output_file = match.group(0)
        json_match = re.search(r'\.hagrid/outputs/[\w\-_]+\.json', result_content)
        if json_match:
            json_file = json_match.group(0)

    logger.info(f"Intraday analysis workflow completed. Output: {output_file}")

    return {
        "date": today,
        "session_id": today,
        "result": result_content,
        "output_file": output_file,
        "json_file": json_file,
        "picks": intraday_workflow.session_state.get("picks", []),
        "regime": intraday_workflow.session_state.get("regime"),
        "department_reports": intraday_workflow.session_state.get("department_reports", {}),
    }


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "intraday_workflow",
    "research_council",
    "technical_department",
    "fundamentals_department",
    "market_intel_department",
    "derivatives_department",
    "run_intraday_analysis",
    "get_intraday_prompt",
]
