"""Basic usage example for NSE India toolkit.

This example shows how to get a comprehensive summary for any stock symbol.
"""

from tools.nse_india.toolkit import NSEIndiaToolkit


def main():
    # Initialize the toolkit
    toolkit = NSEIndiaToolkit()

    try:
        # Get a comprehensive summary for a stock
        # This calls multiple APIs and returns formatted markdown
        symbol = "RELIANCE"
        print(f"Fetching summary for {symbol}...\n")

        summary = toolkit.get_symbol_summary(symbol)
        print(summary)

    finally:
        # Always close the client when done
        toolkit.client.close()


if __name__ == "__main__":
    main()
