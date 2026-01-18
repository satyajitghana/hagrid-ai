"""Enums for NSE India API."""

from enum import StrEnum


class AnnouncementIndex(StrEnum):
    """Types of corporate announcements available on NSE India."""

    EQUITIES = "equities"
    DEBT = "debt"
    SME = "sme"
    MF = "mf"
    SLB = "slb"


class FinancialResultPeriod(StrEnum):
    """Financial result period types."""

    QUARTERLY = "Quarterly"
    ANNUAL = "Annual"


class AnnouncementSubject(StrEnum):
    """Common announcement subjects/categories."""

    FINANCIAL_RESULTS = "Financial Results"
    BOARD_MEETING = "Board Meeting"
    AGM_EGM = "AGM/EGM"
    DIVIDEND = "Dividend"
    BONUS = "Bonus"
    RIGHTS_ISSUE = "Rights Issue"
    STOCK_SPLIT = "Stock Split"
    BUYBACK = "Buyback"
    COPY_OF_NEWSPAPER_PUBLICATION = "Copy of Newspaper Publication"
    INVESTOR_PRESENTATION = "Investor Presentation"
    PRESS_RELEASE = "Press Release"
    GENERAL_UPDATES = "General Updates"
    UPDATES = "Updates"
    AGREEMENTS = "Agreements"
    CREDIT_RATING = "Credit rating"
    ALLOTMENT_OF_SECURITIES = "Allotment of Securities"
    OUTCOME_OF_BOARD_MEETING = "Outcome of Board Meeting"
