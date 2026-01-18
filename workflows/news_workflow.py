"""
News Summarization Workflow

This workflow aggregates and summarizes market news:
1. Fetch news from multiple sources (NSE, Yahoo Finance)
2. Filter and categorize news by impact
3. Generate summary with key events and sentiment
4. Store in session state for other workflows to access

Runs hourly during market hours (9 AM - 4 PM).
"""

from datetime import date, datetime

from agno.workflow import Workflow, Step
from agno.workflow.types import StepInput, StepOutput

from workflows import workflow_db
from agents.news_summarizer import news_agent


def store_news_summary(step_input: StepInput) -> StepOutput:
    """
    Store the news summary in session state for other workflows.

    Parses the news agent's output and structures it for consumption.
    """
    news_summary = step_input.previous_step_content
    last_updated = datetime.now().isoformat()

    if step_input.workflow_session:
        # Store raw summary
        step_input.workflow_session.session_data["latest_summary"] = news_summary
        step_input.workflow_session.session_data["last_updated"] = last_updated

        # Try to extract key events if the output is structured
        # The news agent should output structured JSON
        try:
            import json
            # If the summary is JSON, parse it
            if isinstance(news_summary, str) and news_summary.strip().startswith("{"):
                parsed = json.loads(news_summary)
                step_input.workflow_session.session_data["key_events"] = parsed.get("key_events", [])
                step_input.workflow_session.session_data["sentiment"] = parsed.get("overall_sentiment", "NEUTRAL")
                step_input.workflow_session.session_data["affected_symbols"] = parsed.get("stocks_to_watch", [])
        except (json.JSONDecodeError, Exception):
            # If not JSON, store as-is
            pass

    return StepOutput(
        content=f"News summary stored. Last updated: {last_updated}"
    )


# Define the News Workflow
news_workflow = Workflow(
    name="News Summarizer",

    # Database for session storage
    db=workflow_db,

    # Session state for news context
    # This is accessible by other workflows via get_session()
    session_state={
        "key_events": [],
        "sentiment": "NEUTRAL",
        "affected_symbols": [],
        "latest_summary": None,
        "last_updated": None,
    },

    steps=[
        Step(
            name="Fetch and Analyze News",
            agent=news_agent,
            description="Fetch news from multiple sources and analyze impact"
        ),
        Step(
            name="Store Summary",
            executor=store_news_summary,
            description="Store news summary in session state"
        ),
    ]
)


async def run_news_summary(input_text: str = None) -> dict:
    """
    Run the news workflow.

    Args:
        input_text: Optional custom input.

    Returns:
        dict with news summary
    """
    today = date.today().isoformat()
    current_hour = datetime.now().strftime("%H:00")

    if input_text is None:
        input_text = (
            f"Summarize market news for {today} as of {current_hour}. "
            f"Focus on NIFTY 100 stocks and major macro events. "
            f"Identify high-impact news and affected symbols. "
            f"Provide overall market sentiment."
        )

    result = await news_workflow.arun(
        input=input_text,
        session_id=today  # Same day session - aggregates throughout the day
    )

    return {
        "date": today,
        "session_id": today,
        "result": result.content if result else None,
        "key_events": news_workflow.session_state.get("key_events", []),
        "sentiment": news_workflow.session_state.get("sentiment", "NEUTRAL"),
        "affected_symbols": news_workflow.session_state.get("affected_symbols", []),
    }


__all__ = ["news_workflow", "run_news_summary"]
