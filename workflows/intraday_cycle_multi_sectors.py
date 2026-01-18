"""
Multi-Sector Intraday Trading Cycle Workflow

HAGRID TRADING LLC - Parallel Multi-Sector Analysis System

This workflow orchestrates a comprehensive sector-by-sector analysis:

1. Regime Check - Determine market conditions
2. OI Spurts Scan - Identify stocks with unusual OI activity
3. Fetch Sector Constituents - Dynamically get stocks for each sector
4. Parallel Sector Analysis - 10 sector teams analyze in parallel
5. Cross-Sector Aggregation - Select final 15 stocks across sectors
6. Risk Management - Validate and size positions

Key Features:
- Dynamic stock fetching via NSE India API (no hardcoded lists)
- OI spurts integration for derivatives-based signals
- Max 3 stocks per sector for diversification
- Multi-factor scoring with OI bonus
"""

import json
import re
from datetime import date, datetime
from textwrap import dedent

from agno.workflow import Workflow, Step
from agno.team import Team
from agno.agent import Agent
from agno.workflow.types import StepInput, StepOutput

from workflows import workflow_db, agent_db, logger

# Regime Agent (runs first)
from agents.departments.regime.agent import regime_agent

# Department Analysts (reused by sector teams)
from agents.departments.technical.agent import technical_agent
from agents.departments.fundamentals.agent import fundamentals_agent
from agents.departments.news.agent import news_agent
from agents.departments.options.agent import options_agent

# Cross-Sector Aggregator
from agents.meta.aggregator.cross_sector_aggregator import cross_sector_aggregator

# Risk Agent
from agents.meta.risk.agent import risk_agent

from core.config import get_settings

settings = get_settings()


# ==============================================================================
# SECTOR CONFIGURATION
# ==============================================================================

SECTOR_CONFIG = {
    "banking": {
        "name": "Banking",
        "index_name": "NIFTY BANK",
        "max_picks": 3,
        "description": "Banking sector - HDFC Bank, ICICI, SBI, Kotak, Axis, etc.",
    },
    "it": {
        "name": "Information Technology",
        "index_name": "NIFTY IT",
        "max_picks": 2,
        "description": "IT sector - TCS, Infosys, HCL Tech, Wipro, Tech Mahindra, etc.",
    },
    "financial_services": {
        "name": "Financial Services",
        "index_name": "NIFTY FINANCIAL SERVICES",
        "max_picks": 2,
        "description": "NBFCs and Insurance - Bajaj Finance, HDFC Life, SBI Life, etc.",
    },
    "pharma": {
        "name": "Pharmaceuticals",
        "index_name": "NIFTY PHARMA",
        "max_picks": 2,
        "description": "Pharma sector - Sun Pharma, Dr Reddy's, Cipla, Divi's, etc.",
    },
    "auto": {
        "name": "Automobile",
        "index_name": "NIFTY AUTO",
        "max_picks": 2,
        "description": "Auto sector - Maruti, Tata Motors, M&M, Bajaj Auto, etc.",
    },
    "fmcg": {
        "name": "FMCG",
        "index_name": "NIFTY FMCG",
        "max_picks": 2,
        "description": "Consumer staples - ITC, HUL, Nestle, Britannia, etc.",
    },
    "metals": {
        "name": "Metals & Mining",
        "index_name": "NIFTY METAL",
        "max_picks": 2,
        "description": "Metals sector - Tata Steel, JSW Steel, Hindalco, etc.",
    },
    "energy": {
        "name": "Energy",
        "index_name": "NIFTY ENERGY",
        "max_picks": 2,
        "description": "Energy sector - Reliance, ONGC, NTPC, PowerGrid, etc.",
    },
    "realty": {
        "name": "Real Estate",
        "index_name": "NIFTY REALTY",
        "max_picks": 2,
        "description": "Real estate - DLF, Godrej Properties, Oberoi Realty, etc.",
    },
    "infrastructure": {
        "name": "Infrastructure",
        "index_name": "NIFTY INFRA",
        "max_picks": 2,
        "description": "Infrastructure - L&T, Adani Ports, UltraCemco, Grasim, etc.",
    },
}


# ==============================================================================
# PRE-ANALYSIS FUNCTION STEPS
# ==============================================================================

def scan_oi_spurts(step_input: StepInput) -> StepOutput:
    """Scan for stocks with unusual OI activity using NSE India API."""
    from tools.nse_india import NSEIndiaToolkit

    try:
        nse = NSEIndiaToolkit()
        oi_data = nse.client.get_oi_spurts()

        bullish_oi = []  # Long buildup or short covering
        bearish_oi = []  # Short buildup or long unwinding

        if oi_data and oi_data.data:
            for stock in oi_data.data:
                # OI change > 0 = new positions being created
                # OI change < 0 = positions being closed
                oi_change_pct = stock.avg_in_oi if hasattr(stock, 'avg_in_oi') else 0

                # We need price change to determine signal type
                # For now, categorize by OI change direction
                stock_info = {
                    "symbol": stock.symbol,
                    "oi_change_pct": oi_change_pct,
                    "latest_oi": stock.latest_oi if hasattr(stock, 'latest_oi') else 0,
                    "volume": stock.volume if hasattr(stock, 'volume') else 0,
                    "underlying_value": stock.underlying_value if hasattr(stock, 'underlying_value') else 0,
                }

                if oi_change_pct > 0:
                    bullish_oi.append(stock_info)  # OI buildup
                else:
                    bearish_oi.append(stock_info)  # OI unwinding

        oi_spurts_data = {
            "bullish": bullish_oi[:20],  # Top 20
            "bearish": bearish_oi[:20],
            "all_symbols": [s["symbol"] for s in bullish_oi + bearish_oi],
        }

        if step_input.workflow_session:
            step_input.workflow_session.session_data["oi_spurts"] = oi_spurts_data

        logger.info(f"OI Spurts scan: {len(bullish_oi)} bullish, {len(bearish_oi)} bearish signals")
        return StepOutput(
            content=f"OI Spurts Scan Complete:\n"
                    f"- Bullish OI signals: {len(bullish_oi)} stocks\n"
                    f"- Bearish OI signals: {len(bearish_oi)} stocks\n\n"
                    f"Bullish: {', '.join([s['symbol'] for s in bullish_oi[:10]])}\n"
                    f"Bearish: {', '.join([s['symbol'] for s in bearish_oi[:10]])}"
        )

    except Exception as e:
        logger.warning(f"OI spurts scan failed: {e}")
        if step_input.workflow_session:
            step_input.workflow_session.session_data["oi_spurts"] = {"bullish": [], "bearish": [], "all_symbols": []}
        return StepOutput(content=f"OI Spurts scan unavailable: {str(e)}")


def fetch_sector_constituents(step_input: StepInput) -> StepOutput:
    """Fetch all sector index constituents dynamically using NSE India API."""
    from tools.nse_india import NSEIndiaToolkit

    nse = NSEIndiaToolkit()
    sector_stocks = {}
    total_stocks = 0

    for sector_id, config in SECTOR_CONFIG.items():
        try:
            response = nse.client.get_index_constituents(config["index_name"])

            if response and response.data:
                stocks = []
                for constituent in response.data:
                    # Skip the index itself
                    if constituent.priority == 1:
                        continue

                    stock_data = {
                        "symbol": constituent.symbol,
                        "company_name": constituent.meta.company_name if constituent.meta else "",
                        "last_price": constituent.last_price,
                        "change_pct": constituent.pchange,
                        "volume": constituent.total_traded_volume,
                        "near_52w_high": constituent.near_wkh,
                        "near_52w_low": constituent.near_wkl,
                        "yearly_return": constituent.per_change_365d,
                    }
                    stocks.append(stock_data)

                sector_stocks[sector_id] = {
                    "index_name": config["index_name"],
                    "sector_name": config["name"],
                    "max_picks": config["max_picks"],
                    "stocks": stocks,
                    "count": len(stocks),
                    "top_gainers": sorted(stocks, key=lambda x: x["change_pct"] or 0, reverse=True)[:5],
                    "top_losers": sorted(stocks, key=lambda x: x["change_pct"] or 0)[:5],
                }
                total_stocks += len(stocks)
                logger.info(f"Fetched {len(stocks)} stocks for {config['name']}")
            else:
                sector_stocks[sector_id] = {
                    "index_name": config["index_name"],
                    "sector_name": config["name"],
                    "max_picks": config["max_picks"],
                    "stocks": [],
                    "count": 0,
                }
                logger.warning(f"No constituents found for {config['name']}")

        except Exception as e:
            logger.error(f"Failed to fetch {config['name']}: {e}")
            sector_stocks[sector_id] = {
                "index_name": config["index_name"],
                "sector_name": config["name"],
                "max_picks": config["max_picks"],
                "stocks": [],
                "count": 0,
                "error": str(e),
            }

    if step_input.workflow_session:
        step_input.workflow_session.session_data["sector_stocks"] = sector_stocks

    summary = "\n".join([
        f"- {config['name']}: {sector_stocks[sid]['count']} stocks"
        for sid, config in SECTOR_CONFIG.items()
    ])

    return StepOutput(
        content=f"Sector Constituents Fetched:\n{summary}\n\nTotal: {total_stocks} stocks across {len(SECTOR_CONFIG)} sectors"
    )


def store_regime_in_state(step_input: StepInput) -> StepOutput:
    """Store regime check output into session state."""
    regime_result = step_input.previous_step_content
    if step_input.workflow_session:
        step_input.workflow_session.session_data["regime"] = regime_result
    return StepOutput(content=regime_result)


def store_sector_reports(step_input: StepInput) -> StepOutput:
    """Store all sector team reports in session state."""
    sector_reports = step_input.previous_step_content
    if step_input.workflow_session:
        step_input.workflow_session.session_data["sector_reports"] = sector_reports
    return StepOutput(content=sector_reports)


def store_final_picks(step_input: StepInput) -> StepOutput:
    """Store final 15 picks from aggregator."""
    picks = step_input.previous_step_content
    if step_input.workflow_session:
        step_input.workflow_session.session_data["final_picks"] = picks
        step_input.workflow_session.session_data["picks_count"] = 15
    return StepOutput(content=picks)


def save_multi_sector_output(step_input: StepInput) -> StepOutput:
    """Save the multi-sector analysis output to dated files."""
    content = step_input.previous_step_content or ""
    session_data = step_input.workflow_session.session_data if step_input.workflow_session else {}

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{timestamp}_multi_sector_analysis.md"
    filepath = settings.OUTPUT_DIR / filename

    json_filename = f"{timestamp}_multi_sector_analysis.json"
    json_filepath = settings.OUTPUT_DIR / json_filename

    # Ensure output directory exists
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write markdown report
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Hagrid Multi-Sector Intraday Analysis\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(content)

    # Write structured JSON
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "session_id": step_input.workflow_session.session_id if step_input.workflow_session else None,
        "regime": session_data.get("regime"),
        "oi_spurts": session_data.get("oi_spurts"),
        "sector_reports": session_data.get("sector_reports"),
        "final_picks": session_data.get("final_picks"),
        "risk_validated": session_data.get("risk_validated", False),
    }
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, default=str)

    logger.info(f"Multi-sector output saved to {filepath}")

    return StepOutput(
        content=f"Output saved to:\n- {filepath}\n- {json_filepath}\n\n{content}"
    )


# ==============================================================================
# SECTOR TEAM FACTORY
# ==============================================================================

def create_sector_lead(sector_id: str, config: dict) -> Agent:
    """Create a sector-specific lead agent with customized instructions."""

    sector_lead_instructions = dedent(f"""
        You are the SECTOR LEAD for {config['name']} sector at Hagrid Trading LLC.

        ## YOUR SECTOR
        - Sector Index: {config['index_name']}
        - Maximum Picks Allowed: {config['max_picks']}
        - Description: {config['description']}

        ## YOUR TEAM
        You coordinate 4 analysts:
        1. Technical Analyst - Price action, indicators, setups
        2. Fundamentals Analyst - Company quality, earnings, valuations
        3. News Analyst - Sentiment, catalysts, broker ratings
        4. Options Analyst - PCR, OI distribution, IV

        ## YOUR OBJECTIVE
        Analyze ALL stocks in your sector and identify:
        - TOP {config['max_picks']} LONG candidates with highest conviction
        - Optionally 1 SHORT candidate if bearish setup is compelling

        ## ANALYSIS WORKFLOW
        1. Review sector index performance and trend
        2. Delegate analysis to each team member
        3. Collect and synthesize findings
        4. Score each stock using multi-factor model
        5. Select top picks with full justification

        ## SCORING MODEL (Per Stock)
        - Technical Score: ±5 (setup quality, trend alignment)
        - Fundamentals Score: ±3 (earnings quality, valuation)
        - News/Sentiment Score: ±2 (catalysts, sentiment)
        - Options Score: ±2 (derivatives positioning)
        - TOTAL: ±12 points

        ## OI SPURTS BONUS
        Check if any of your sector stocks appear in OI spurts data:
        - Long Buildup: +1 bonus for LONG picks
        - Short Buildup: +1 bonus for SHORT picks

        ## OUTPUT FORMAT
        For each recommended stock:
        ```
        SECTOR: {config['name']}
        RANK: [1-{config['max_picks']}]
        SYMBOL: NSE:SYMBOL-EQ
        DIRECTION: LONG/SHORT

        MULTI-FACTOR SCORES:
        - Technical: [±5] - [Key technical reason]
        - Fundamentals: [±3] - [Key fundamental reason]
        - News: [±2] - [Sentiment/catalyst]
        - Options: [±2] - [Derivatives view]
        - OI Spurts Bonus: [+0/+0.5/+1]
        TOTAL SCORE: [X/13]

        TRADE SETUP:
        - Entry: ₹[X] to ₹[Y]
        - Stop Loss: ₹[Z] ([X%] risk)
        - Target: ₹[W] (1:2 R:R minimum)

        CONVICTION: HIGH/MEDIUM
        KEY THESIS: [2-3 sentences on why this is your top pick]
        ```
    """)

    return Agent(
        name=f"{config['name']} Sector Lead",
        role=f"Head of {config['name']} Analysis",
        model="google:gemini-3-pro-preview",
        instructions=sector_lead_instructions,
        markdown=True,
    )


def create_sector_team(sector_id: str, config: dict) -> Team:
    """Create a sector-specific analysis team."""

    sector_lead = create_sector_lead(sector_id, config)

    return Team(
        name=f"{config['name']} Analysis Team",
        model="google:gemini-3-pro-preview",
        members=[
            sector_lead,
            technical_agent,
            fundamentals_agent,
            news_agent,
            options_agent,
        ],
        description=f"""Sector Analysis Team for {config['name']}.

Coverage: {config['index_name']} index stocks
Target Output: Top {config['max_picks']} LONG picks + optional SHORT

The Sector Lead coordinates analysis across Technical, Fundamentals,
News, and Options dimensions to identify highest conviction trades.
Stocks are fetched dynamically from NSE India API.""",

        db=agent_db,
        delegate_task_to_all_members=True,
        share_member_interactions=True,
        session_state={
            "sector_id": sector_id,
            "sector_name": config['name'],
            "index_name": config['index_name'],
            "picks": [],
        },
    )


# ==============================================================================
# CREATE ALL SECTOR TEAMS
# ==============================================================================

sector_teams = {
    sector_id: create_sector_team(sector_id, config)
    for sector_id, config in SECTOR_CONFIG.items()
}


# ==============================================================================
# PARALLEL SECTOR ANALYSIS TEAM (TEAM OF TEAMS)
# ==============================================================================

parallel_sector_analysis_team = Team(
    name="Parallel Sector Analysis Council",
    model="google:gemini-3-pro-preview",
    members=[
        sector_teams["banking"],
        sector_teams["it"],
        sector_teams["financial_services"],
        sector_teams["pharma"],
        sector_teams["auto"],
        sector_teams["fmcg"],
        sector_teams["metals"],
        sector_teams["energy"],
        sector_teams["realty"],
        sector_teams["infrastructure"],
    ],
    description="""Parallel Sector Analysis Council at Hagrid Trading LLC.

10 sector teams analyzing their respective universes SIMULTANEOUSLY:
- Banking (NIFTY BANK) - Max 3 picks
- IT (NIFTY IT) - Max 2 picks
- Financial Services (NIFTY FINANCIAL SERVICES) - Max 2 picks
- Pharma (NIFTY PHARMA) - Max 2 picks
- Auto (NIFTY AUTO) - Max 2 picks
- FMCG (NIFTY FMCG) - Max 2 picks
- Metals (NIFTY METAL) - Max 2 picks
- Energy (NIFTY ENERGY) - Max 2 picks
- Realty (NIFTY REALTY) - Max 2 picks
- Infrastructure (NIFTY INFRA) - Max 2 picks

Each team produces top picks with multi-factor analysis.
All teams work in PARALLEL for efficiency.
Stock lists are fetched dynamically from NSE India API.
OI spurts data is available for bonus scoring.""",

    db=agent_db,
    delegate_task_to_all_members=True,  # Critical: enables parallel execution
    share_member_interactions=True,
    session_state={
        "sectors_analyzed": [],
        "total_picks": [],
    },
)


# ==============================================================================
# COMPREHENSIVE MULTI-SECTOR ANALYSIS PROMPT
# ==============================================================================

MULTI_SECTOR_ANALYSIS_PROMPT = """
# HAGRID TRADING LLC - Multi-Sector Intraday Analysis

**Date**: {date}
**Objective**: Parallel sector analysis to generate 15 high-conviction intraday trades
**Target Return**: 5% daily portfolio return
**Risk Parameters**: Max {max_risk_pct}% risk per trade, Max 15 positions

---

## MARKET CONTEXT

### Regime
{regime}

### OI Spurts Data
{oi_spurts}

### Sector Constituents
{sector_summary}

---

## ANALYSIS WORKFLOW

### PHASE 1: Market Regime Assessment ✓
Current regime has been determined above.

### PHASE 2: OI Spurts Scan ✓
Stocks with unusual OI activity have been identified above.

### PHASE 3: Parallel Sector Analysis (10 Teams)
Each sector team independently analyzes their universe:
1. Banking Team - NIFTY BANK constituents (Max 3 picks)
2. IT Team - NIFTY IT constituents (Max 2 picks)
3. Financial Services Team - NBFCs, Insurance (Max 2 picks)
4. Pharma Team - NIFTY PHARMA constituents (Max 2 picks)
5. Auto Team - NIFTY AUTO constituents (Max 2 picks)
6. FMCG Team - Consumer staples (Max 2 picks)
7. Metals Team - Steel, Aluminum, Mining (Max 2 picks)
8. Energy Team - Oil/Gas, Power (Max 2 picks)
9. Realty Team - Real estate (Max 2 picks)
10. Infrastructure Team - Construction, Cement (Max 2 picks)

### SECTOR TEAM DELIVERABLES
Each sector team outputs:
- Top 2-3 LONG picks with full analysis
- Optional SHORT if compelling setup
- Entry/Stop/Target levels
- Multi-factor conviction scores (including OI bonus)

---

## BEGIN PARALLEL SECTOR ANALYSIS

Analyze all sectors and provide your top picks. Remember:
- Apply OI Spurts bonus (+1) for stocks in the OI data
- Maximum picks per sector as specified
- Every pick needs stop loss and target
- Minimum 1.5:1 reward-to-risk ratio
"""


def get_multi_sector_prompt(regime: str, oi_spurts: dict, sector_stocks: dict) -> str:
    """Generate the multi-sector analysis prompt with context."""

    # Format OI spurts summary
    bullish_symbols = [s["symbol"] for s in oi_spurts.get("bullish", [])[:10]]
    bearish_symbols = [s["symbol"] for s in oi_spurts.get("bearish", [])[:10]]
    oi_summary = f"Bullish OI (Long Buildup): {', '.join(bullish_symbols) if bullish_symbols else 'None'}\n"
    oi_summary += f"Bearish OI (Short Buildup): {', '.join(bearish_symbols) if bearish_symbols else 'None'}"

    # Format sector summary
    sector_lines = []
    for sector_id, data in sector_stocks.items():
        sector_lines.append(f"- {data.get('sector_name', sector_id)}: {data.get('count', 0)} stocks")
    sector_summary = "\n".join(sector_lines)

    return MULTI_SECTOR_ANALYSIS_PROMPT.format(
        date=date.today().isoformat(),
        max_risk_pct=settings.MAX_RISK_PER_TRADE_PERCENT,
        regime=regime or "Not yet determined",
        oi_spurts=oi_summary,
        sector_summary=sector_summary,
    )


# ==============================================================================
# WORKFLOW DEFINITION
# ==============================================================================

multi_sector_workflow = Workflow(
    name="Multi-Sector Intraday Cycle",
    db=workflow_db,

    session_state={
        "regime": None,
        "oi_spurts": {},
        "sector_stocks": {},
        "sector_reports": {},
        "final_picks": [],
        "risk_validated": False,
    },

    add_workflow_history_to_steps=True,
    num_history_runs=5,

    steps=[
        # Step 1: Market Regime Assessment
        Step(
            name="Regime Check",
            agent=regime_agent,
            description="Determine market regime (TRENDING_UP, TRENDING_DOWN, RANGING)"
        ),

        # Step 2: Store regime
        Step(
            name="Store Regime",
            executor=store_regime_in_state,
            description="Store regime in session state for downstream steps"
        ),

        # Step 3: OI Spurts Scan
        Step(
            name="OI Spurts Scan",
            executor=scan_oi_spurts,
            description="Scan for stocks with unusual OI activity using NSE India API"
        ),

        # Step 4: Fetch Sector Constituents
        Step(
            name="Fetch Sector Constituents",
            executor=fetch_sector_constituents,
            description="Dynamically fetch stocks for each sector from NSE India API"
        ),

        # Step 5: Parallel Sector Analysis (ALL 10 SECTORS AT ONCE)
        Step(
            name="Parallel Sector Analysis",
            team=parallel_sector_analysis_team,
            description="""Run ALL 10 sector teams in parallel:
            - Each team analyzes their sector's stocks
            - Each team outputs top 2-3 picks
            - Total ~20-25 candidates generated
            - OI spurts bonus applied to qualifying stocks"""
        ),

        # Step 6: Store sector reports
        Step(
            name="Store Sector Reports",
            executor=store_sector_reports,
            description="Store all sector team outputs in session state"
        ),

        # Step 7: Cross-Sector Aggregation
        Step(
            name="Cross-Sector Aggregation",
            agent=cross_sector_aggregator,
            description="""Select final 15 stocks from all sector recommendations:
            - Apply diversification rules (max 3 per sector)
            - Ensure direction mix based on regime
            - Apply OI spurts bonus where applicable
            - Rank by conviction and score"""
        ),

        # Step 8: Store final picks
        Step(
            name="Store Final Picks",
            executor=store_final_picks,
            description="Store aggregator's final 15 picks"
        ),

        # Step 9: Risk Management
        Step(
            name="Risk Management",
            agent=risk_agent,
            description="Validate picks: position sizing, portfolio constraints, risk limits"
        ),

        # Step 10: Save output
        Step(
            name="Save Output",
            executor=save_multi_sector_output,
            description="Save analysis to dated files"
        ),
    ]
)


# ==============================================================================
# RUN FUNCTION
# ==============================================================================

async def run_multi_sector_analysis(input_text: str = None) -> dict:
    """
    Run the multi-sector intraday analysis workflow.

    This workflow:
    1. Checks market regime
    2. Scans for OI spurts
    3. Fetches sector constituents dynamically
    4. Runs 10 sector teams in parallel
    5. Aggregates to final 15 picks
    6. Validates risk parameters

    Args:
        input_text: Optional custom input. If None, uses default prompt with context.

    Returns:
        dict with workflow result, session info, and output paths
    """
    from core.fyers_client import ensure_authenticated
    await ensure_authenticated()

    today = date.today().isoformat()

    logger.info(f"Starting multi-sector analysis for {today}")
    logger.info("Running 10 sector teams in parallel...")

    # Run workflow - the prompt will be constructed inside with context
    result = await multi_sector_workflow.arun(
        input=input_text or "Begin multi-sector intraday analysis. Analyze all 10 sectors and provide final 15 stock picks.",
        session_id=f"multi_sector_{today}"
    )

    result_content = result.content if result else ""

    output_file = None
    json_file = None
    if "Output saved to:" in result_content:
        match = re.search(r'\.hagrid/outputs/[\w\-_]+\.md', result_content)
        if match:
            output_file = match.group(0)
        json_match = re.search(r'\.hagrid/outputs/[\w\-_]+\.json', result_content)
        if json_match:
            json_file = json_match.group(0)

    logger.info(f"Multi-sector analysis completed. Output: {output_file}")

    return {
        "date": today,
        "session_id": f"multi_sector_{today}",
        "result": result_content,
        "output_file": output_file,
        "json_file": json_file,
        "final_picks": multi_sector_workflow.session_state.get("final_picks", []),
        "regime": multi_sector_workflow.session_state.get("regime"),
        "oi_spurts": multi_sector_workflow.session_state.get("oi_spurts", {}),
        "sector_reports": multi_sector_workflow.session_state.get("sector_reports", {}),
    }


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Configuration
    "SECTOR_CONFIG",

    # Workflow
    "multi_sector_workflow",

    # Teams
    "parallel_sector_analysis_team",
    "sector_teams",

    # Agents
    "cross_sector_aggregator",

    # Functions
    "run_multi_sector_analysis",
    "get_multi_sector_prompt",
    "create_sector_team",
    "create_sector_lead",

    # Step functions
    "scan_oi_spurts",
    "fetch_sector_constituents",
]
