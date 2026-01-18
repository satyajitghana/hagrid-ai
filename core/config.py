from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


def get_project_root() -> Path:
    """Find the project root directory by looking for pyproject.toml or .git."""
    current = Path(__file__).resolve().parent  # core/
    # Go up to find project root (where pyproject.toml or .git exists)
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    # Fallback to current working directory
    return Path.cwd()


def get_data_dir() -> Path:
    """Get or create the data directory for Hagrid in the project directory."""
    data_dir = get_project_root() / ".hagrid"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


class Settings(BaseSettings):
    APP_NAME: str = "Hagrid AI"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Debug & Logging
    AGNO_DEBUG: bool = True  # Enable Agno framework debug mode
    AGNO_DEBUG_LEVEL: int = 1  # 1=normal, 2=verbose
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    LOG_TO_FILE: bool = True  # Write logs to file

    # Tracing (OpenTelemetry)
    TRACING_ENABLED: bool = True  # Enable OpenTelemetry tracing
    TRACING_BATCH_SIZE: int = 256  # Spans per batch export
    TRACING_QUEUE_SIZE: int = 1024  # Max spans in queue

    # Market Data Config
    MARKET_DATA_PROVIDER: str = "mock"  # mock, zerodha, etc.

    # Fyers Config
    FYERS_CLIENT_ID: str = ""
    FYERS_SECRET_KEY: str = ""

    # Trading Config
    MAX_RISK_PER_TRADE_PERCENT: float = 1.0
    MAX_DAILY_LOSS_PERCENT: float = 2.0

    # Trading targets
    TARGET_DAILY_RETURN_PERCENT: float = 5.0
    BASE_CAPITAL: float = 100000.0
    MAX_STOCKS_PER_DAY: int = 15

    # Paper Trading Config
    PAPER_TRADE: bool = False  # Enable paper trading mode
    PAPER_TRADE_INITIAL_BALANCE: float = 100000.0  # Starting capital for paper trading
    PAPER_TRADE_LTP_UPDATE_INTERVAL: int = 600  # LTP update interval in seconds (10 minutes)

    # Scheduler settings
    SCHEDULER_ENABLED: bool = True
    MARKET_OPEN_TIME: str = "09:15"
    MARKET_CLOSE_TIME: str = "15:30"

    @property
    def DATA_DIR(self) -> Path:
        """Data directory for all Hagrid files."""
        return get_data_dir()

    @property
    def FYERS_TOKEN_FILE(self) -> str:
        """Path to Fyers token file."""
        return str(self.DATA_DIR / "fyers_token.json")

    @property
    def WORKFLOW_DB_FILE(self) -> str:
        """Path to workflow database file."""
        return str(self.DATA_DIR / "hagrid_workflows.db")

    @property
    def AGENT_DB_FILE(self) -> str:
        """Path to agent database file."""
        return str(self.DATA_DIR / "hagrid_agents.db")

    @property
    def TRADE_DB_FILE(self) -> str:
        """Path to trade database file."""
        return str(self.DATA_DIR / "hagrid_trades.db")

    @property
    def LOG_FILE(self) -> str:
        """Path to log file."""
        return str(self.DATA_DIR / "hagrid.log")

    @property
    def TRACING_DB_FILE(self) -> str:
        """Path to tracing database file."""
        return str(self.DATA_DIR / "hagrid_traces.db")

    @property
    def OUTPUT_DIR(self) -> Path:
        """Directory for workflow output files."""
        output_dir = self.DATA_DIR / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    @property
    def PAPER_TRADE_STATE_FILE(self) -> str:
        """Path to paper trade state file."""
        return str(self.DATA_DIR / "paper_trade_state.json")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra env vars (e.g., GOOGLE_API_KEY for agno)


@lru_cache()
def get_settings():
    return Settings()