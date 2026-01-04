from agno.workflow import Workflow, Step
from agno.team import Team

from agents.departments.regime.agent import regime_agent
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
from agents.meta.aggregator.agent import aggregator_agent
from agents.meta.risk.agent import risk_agent
from agents.meta.execution.agent import execution_agent

# Initialize Research Team with all 12 department agents
research_team = Team(
    name="Research Team",
    members=[
        technical_agent,      # Technical Analysis
        options_agent,        # Options & Greeks
        fundamentals_agent,   # Fundamental Analysis
        sector_agent,         # Sector Rotation
        microstructure_agent, # Order Book Analysis
        macro_agent,          # Global Macro
        institutional_agent,  # FII/DII Flows
        news_agent,           # News & Sentiment
        events_agent,         # Corporate Events
        correlation_agent,    # Pairs Trading
        position_agent        # Position Management (for existing positions)
    ],
    description="12 specialized agents analyzing NIFTY 100 stocks from multiple perspectives."
)

# Define the Workflow using instantiated agents
intraday_workflow = Workflow(
    name="Intraday Trading Cycle",
    steps=[
        Step(
            name="Regime Check",
            agent=regime_agent,
            description="Check market regime before proceeding."
        ),
        Step(
            name="Multi-Agent Analysis",
            team=research_team,
            description="All 12 department agents analyze given symbols in parallel from technical, fundamental, options, macro, and other perspectives."
        ),
        Step(
            name="Signal Aggregation",
            agent=aggregator_agent,
            description="Aggregate signals into trade candidates."
        ),
        Step(
            name="Risk Management",
            agent=risk_agent,
            description="Validate and size trades."
        ),
        Step(
            name="Execution",
            agent=execution_agent,
            description="Execute approved orders."
        )
    ]
)