import asyncio
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def verify_fyers_broker():
    print("\n--- Verifying FyersBroker ---")
    try:
        from broker.fyers_broker import FyersBroker
        from core.config import get_settings
        
        settings = get_settings()
        
        # Check if credentials exist (even if dummy for test)
        if not settings.FYERS_CLIENT_ID:
            print("❌ FYERS_CLIENT_ID not set")
            return
            
        broker = FyersBroker(
            client_id=settings.FYERS_CLIENT_ID,
            secret_key=settings.FYERS_SECRET_KEY,
            token_file=settings.FYERS_TOKEN_FILE
        )
        print("✅ FyersBroker initialized successfully")
        
        # We can't really call API without real creds, but we can check object structure
        print(f"✅ Client ID: {broker.config.client_id}")
        
    except Exception as e:
        print(f"❌ FyersBroker verification failed: {e}")

async def verify_toolkits():
    print("\n--- Verifying Toolkits ---")
    try:
        from core.market_data_sources import (
            FundamentalsToolkit,
            NewsToolkit,
            EventsToolkit,
            FIIDIIToolkit,
            MacroToolkit
        )
        from core.analysis_toolkit import TechnicalScannerToolkit
        
        print("Initializing Toolkits...")
        
        # Initialize all toolkits to check imports and clients
        fund_tools = FundamentalsToolkit()
        print("✅ FundamentalsToolkit initialized")
        
        news_tools = NewsToolkit()
        print("✅ NewsToolkit initialized")
        
        event_tools = EventsToolkit()
        print("✅ EventsToolkit initialized")
        
        fii_tools = FIIDIIToolkit()
        print("✅ FIIDIIToolkit initialized")
        
        macro_tools = MacroToolkit()
        print("✅ MacroToolkit initialized")
        
        scanner_tools = TechnicalScannerToolkit()
        print("✅ TechnicalScannerToolkit initialized")
        
    except Exception as e:
        print(f"❌ Toolkit verification failed: {e}")

async def verify_agents():
    print("\n--- Verifying Agents ---")
    try:
        # Import all agents to check for dependency errors
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
        from agents.departments.regime.agent import regime_agent
        
        from agents.meta.aggregator.agent import aggregator_agent
        from agents.meta.risk.agent import risk_agent
        from agents.meta.execution.agent import execution_agent
        
        agents = [
            technical_agent, options_agent, fundamentals_agent, sector_agent,
            microstructure_agent, macro_agent, institutional_agent, news_agent,
            events_agent, correlation_agent, position_agent, regime_agent,
            aggregator_agent, risk_agent, execution_agent
        ]
        
        print(f"✅ Successfully imported {len(agents)} agents")
        
        for agent in agents:
            print(f"  - {agent.name}: Ready")
            
    except Exception as e:
        print(f"❌ Agent verification failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("Starting System Verification...")
    await verify_fyers_broker()
    await verify_toolkits()
    await verify_agents()
    print("\nVerification Complete.")

if __name__ == "__main__":
    asyncio.run(main())