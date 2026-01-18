"""Examples of using individual Quote APIs.

This example demonstrates how to use specific NSE Quote APIs
to fetch different types of data for a stock.
"""

import json

from tools.nse_india.client import NSEIndiaClient


def print_json(title: str, data: dict | list):
    """Pretty print JSON data with a title."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print("=" * 60)
    print(json.dumps(data, indent=2, default=str))


def main():
    client = NSEIndiaClient()
    symbol = "TCS"

    try:
        # 1. Get symbol name and company details
        symbol_name = client.get_symbol_name(symbol)
        print_json("Symbol Name", symbol_name)

        # 2. Get metadata (ISIN, F&O status, etc.)
        metadata = client.get_metadata(symbol)
        print_json("Metadata", metadata)

        # 3. Get detailed symbol data (price, volume, market info)
        symbol_data = client.get_symbol_data(symbol)
        print_json("Symbol Data (truncated)", {
            "equityResponse": symbol_data.get("equityResponse", [])[:1]
        })

        # 4. Get shareholding pattern
        shareholding = client.get_shareholding_pattern(symbol)
        print_json("Shareholding Pattern", shareholding)

        # 5. Get financial status (quarterly results)
        financials = client.get_financial_status(symbol)
        print_json("Financial Status", financials[:2] if financials else [])

        # 6. Get year-wise performance data
        yearwise = client.get_yearwise_data(symbol)
        print_json("Year-wise Performance", yearwise)

        # 7. Get recent corporate announcements
        announcements = client.get_corporate_announcements_quote(symbol, no_of_records=3)
        print_json("Recent Announcements", announcements)

        # 8. Get corporate actions (dividends, bonus, splits)
        corp_actions = client.get_corp_actions(symbol, no_of_records=3)
        print_json("Corporate Actions", corp_actions)

        # 9. Get board meetings
        board_meetings = client.get_board_meetings(symbol, no_of_records=2)
        print_json("Board Meetings", board_meetings)

        # 10. Get annual reports
        annual_reports = client.get_annual_reports_quote(symbol, no_of_records=3)
        print_json("Annual Reports", annual_reports)

        # 11. Get BRSR (sustainability) reports
        brsr_reports = client.get_brsr_reports(symbol)
        print_json("BRSR Reports", brsr_reports)

        # 12. Get index membership
        index_list = client.get_index_list(symbol)
        print_json("Index Membership", index_list)

        # 13. Get integrated filing data (consolidated financials)
        integrated_filing = client.get_integrated_filing_data(symbol)
        print_json("Integrated Filing Data", integrated_filing[:2] if integrated_filing else [])

    finally:
        client.close()


if __name__ == "__main__":
    main()
