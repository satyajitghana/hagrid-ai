"""Fetch ALL NSE Quote APIs to understand their responses."""

import json
import sys
sys.path.insert(0, "/Users/satyajitghana/Projects/hagrid-ai")

from tools.nse_india.core.http_client import NSEIndiaHTTPClient
from pathlib import Path

SYMBOL = "RELIANCE"
SYMBOL_SERIES = f"{SYMBOL}EQN"

def get_quote_api(client, function_name, **params):
    query_params = {"functionName": function_name, **params}
    return client.get_json("/api/NextApi/apiClient/GetQuoteApi", params=query_params)

# ALL APIs from the user's list
ALL_APIS = [
    # Symbol-specific APIs
    ("getSymbolName", {"symbol": SYMBOL}),
    ("getMetaData", {"symbol": SYMBOL}),
    ("getSymbolData", {"symbol": SYMBOL, "marketType": "N", "series": "EQ"}),
    ("getRegDetails", {"symbol": SYMBOL, "series": "EQ"}),
    ("getSymbolChartData", {"symbol": SYMBOL_SERIES, "days": "1D"}),
    ("getYearwiseData", {"symbol": SYMBOL_SERIES}),
    ("getIndexList", {"symbol": SYMBOL}),

    # Corporate APIs
    ("getCorporateAnnouncement", {"symbol": SYMBOL, "marketApiType": "equities", "noOfRecords": "3"}),
    ("getCorpAction", {"symbol": SYMBOL, "marketApiType": "equities", "noOfRecords": "3"}),
    ("getCorpAnnualReport", {"symbol": SYMBOL, "marketApiType": "equities", "noOfRecords": "6"}),
    ("getCorpBrsr", {"symbol": SYMBOL}),
    ("getCorpEventCalender", {"symbol": SYMBOL, "noOfRecords": "3", "marketApiType": "equities"}),
    ("getCorpBoardMeeting", {"symbol": SYMBOL, "marketApiType": "equities", "type": "W", "noOfRecords": "4"}),

    # Financial APIs
    ("getShareholdingPattern", {"symbol": SYMBOL, "noOfRecords": "5"}),
    ("getFinancialStatus", {"symbol": SYMBOL}),
    ("getIntegratedFilingData", {"symbol": SYMBOL}),
    ("getFinancialResultData", {"symbol": SYMBOL, "marketApiType": "equities", "noOfRecords": "5"}),

    # Derivatives APIs
    ("getDerivativesMostActive", {"symbol": SYMBOL, "callType": "C"}),  # Most Active Calls
    ("getDerivativesMostActive", {"symbol": SYMBOL, "callType": "P"}),  # Most Active Puts
    ("getDerivativesMostActive", {"symbol": SYMBOL, "callType": "O"}),  # Most Active by OI
    ("getSymbolDerivativesFilter", {"isSymbolIndex": "S", "symbol": SYMBOL}),
    ("getSymbolDerivativesData", {"symbol": SYMBOL}),  # All Contracts

    # Option Chain
    ("getOptionChainDropdown", {"symbol": SYMBOL}),
    ("getOptionChainData", {"symbol": SYMBOL, "params": "expiryDate=27-Jan-2026"}),

    # Market-wide APIs (not symbol specific)
    ("getPreOpenMarketStatus", {}),
    ("getQuoteIndexData", {}),
    ("getTopTenStock", {}),
]

client = NSEIndiaHTTPClient(timeout=30.0)
output_dir = Path("all_api_responses")
output_dir.mkdir(exist_ok=True)

results = {}

for api_name, params in ALL_APIS:
    # Create unique filename for APIs called with different params
    filename = api_name
    if "callType" in params:
        filename = f"{api_name}_{params['callType']}"

    print(f"Fetching {filename}...")
    try:
        result = get_quote_api(client, api_name, **params)
        results[filename] = {"status": "success", "params": params, "data": result}

        # Save individual response
        with open(output_dir / f"{filename}.json", "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"  ✓ {filename}")
    except Exception as e:
        results[filename] = {"status": "error", "params": params, "error": str(e)}
        print(f"  ✗ {filename} - {e}")

# Save summary
with open(output_dir / "_all_responses.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nAll responses saved to {output_dir}/")
client.close()
