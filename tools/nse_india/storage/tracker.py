"""Tracker for processed NSE India announcements using SQLite."""

from datetime import datetime
from pathlib import Path

from sqlmodel import Field, Session, SQLModel, create_engine, select

from ..models.announcement import Announcement, DebtAnnouncement, EquityAnnouncement
from ..models.enums import AnnouncementIndex


class ProcessedAnnouncement(SQLModel, table=True):
    """Database model for tracking processed announcements."""

    __tablename__ = "nse_processed_announcements"

    id: int | None = Field(default=None, primary_key=True)
    unique_id: str = Field(index=True, unique=True)
    index_type: str = Field(index=True)  # equities, debt, sme, mf, slb
    symbol: str | None = Field(index=True, default=None)
    company_name: str
    subject: str
    details: str | None = None
    broadcast_datetime: datetime = Field(index=True)
    attachment_url: str | None = None
    attachment_path: str | None = None  # Local path after download
    processed_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_announcement(
        cls,
        announcement: Announcement,
        index_type: AnnouncementIndex,
        attachment_path: str | None = None,
    ) -> "ProcessedAnnouncement":
        """Create a ProcessedAnnouncement from an Announcement model."""
        symbol = announcement.symbol if isinstance(announcement, EquityAnnouncement) else None

        return cls(
            unique_id=announcement.unique_id,
            index_type=index_type.value,
            symbol=symbol,
            company_name=announcement.company_name,
            subject=announcement.subject,
            details=announcement.details,
            broadcast_datetime=announcement.broadcast_datetime,
            attachment_url=announcement.attachment_url,
            attachment_path=attachment_path,
        )


class AnnouncementTracker:
    """Track processed announcements to avoid reprocessing.

    Uses SQLite database to persist the state of processed announcements.
    """

    def __init__(self, db_path: str | Path = "nse_announcements.db"):
        """Initialize the tracker with a database path.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        SQLModel.metadata.create_all(self._engine)

    def is_processed(self, unique_id: str) -> bool:
        """Check if an announcement has already been processed.

        Args:
            unique_id: Unique identifier of the announcement

        Returns:
            True if already processed, False otherwise
        """
        with Session(self._engine) as session:
            statement = select(ProcessedAnnouncement).where(
                ProcessedAnnouncement.unique_id == unique_id
            )
            result = session.exec(statement).first()
            return result is not None

    def mark_processed(
        self,
        announcement: Announcement,
        index_type: AnnouncementIndex,
        attachment_path: str | None = None,
    ) -> ProcessedAnnouncement:
        """Mark an announcement as processed and store in database.

        Args:
            announcement: The announcement to mark as processed
            index_type: Type of announcement index
            attachment_path: Local path to downloaded attachment (if any)

        Returns:
            The stored ProcessedAnnouncement record
        """
        processed = ProcessedAnnouncement.from_announcement(
            announcement=announcement,
            index_type=index_type,
            attachment_path=attachment_path,
        )

        with Session(self._engine) as session:
            session.add(processed)
            session.commit()
            session.refresh(processed)
            return processed

    def get_unprocessed(
        self,
        announcements: list[Announcement],
    ) -> list[Announcement]:
        """Filter out already processed announcements.

        Args:
            announcements: List of announcements to filter

        Returns:
            List of announcements that haven't been processed yet
        """
        if not announcements:
            return []

        with Session(self._engine) as session:
            # Get all unique IDs from the input
            unique_ids = [a.unique_id for a in announcements]

            # Query for already processed IDs
            statement = select(ProcessedAnnouncement.unique_id).where(
                ProcessedAnnouncement.unique_id.in_(unique_ids)
            )
            processed_ids = set(session.exec(statement).all())

            # Return only unprocessed announcements
            return [a for a in announcements if a.unique_id not in processed_ids]

    def get_processed_count(self, index_type: AnnouncementIndex | None = None) -> int:
        """Get count of processed announcements.

        Args:
            index_type: Optional filter by index type

        Returns:
            Number of processed announcements
        """
        with Session(self._engine) as session:
            statement = select(ProcessedAnnouncement)
            if index_type:
                statement = statement.where(ProcessedAnnouncement.index_type == index_type.value)
            results = session.exec(statement).all()
            return len(results)

    def get_recent(
        self,
        limit: int = 100,
        index_type: AnnouncementIndex | None = None,
        symbol: str | None = None,
    ) -> list[ProcessedAnnouncement]:
        """Get recently processed announcements.

        Args:
            limit: Maximum number of results
            index_type: Optional filter by index type
            symbol: Optional filter by symbol

        Returns:
            List of recent ProcessedAnnouncement records
        """
        with Session(self._engine) as session:
            statement = select(ProcessedAnnouncement).order_by(
                ProcessedAnnouncement.processed_at.desc()
            )

            if index_type:
                statement = statement.where(ProcessedAnnouncement.index_type == index_type.value)

            if symbol:
                statement = statement.where(ProcessedAnnouncement.symbol == symbol)

            statement = statement.limit(limit)
            return list(session.exec(statement).all())

    def clear(self, index_type: AnnouncementIndex | None = None) -> int:
        """Clear processed announcements from database.

        Args:
            index_type: Optional - only clear announcements of this type

        Returns:
            Number of records deleted
        """
        with Session(self._engine) as session:
            statement = select(ProcessedAnnouncement)
            if index_type:
                statement = statement.where(ProcessedAnnouncement.index_type == index_type.value)

            records = session.exec(statement).all()
            count = len(records)

            for record in records:
                session.delete(record)

            session.commit()
            return count
