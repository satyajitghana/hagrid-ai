"""Fetch ALL NSE Index APIs to understand their responses."""

import json
import sys
sys.path.insert(0, "/Users/satyajitghana/Projects/hagrid-ai")

from tools.nse_india.core.http_client import NSEIndiaHTTPClient
from pathlib import Path

INDEX = "NIFTY 50"
SYMBOL = "RELIANCE"  # For symbol-specific APIs within index

def get_index_tracker_api(client, function_name, **params):
    query_params = {"functionName": function_name, **params}
    return client.get_json("/api/NextApi/apiClient/indexTrackerApi", params=query_params)

def get_api_client(client, function_name, **params):
    query_params = {"functionName": function_name, **params}
    return client.get_json("/api/NextApi/apiClient", params=query_params)

# ALL Index APIs
ALL_INDEX_APIS = [
    # General Index APIs
    ("apiClient", "getIndexData", {"type": "All"}),
    ("apiClient", "getGiftNifty", {}),

    # Index Tracker APIs
    ("indexTrackerApi", "getAllIndices", {}),
    ("indexTrackerApi", "getIndexData", {"index": INDEX}),
    ("indexTrackerApi", "getIndexChart", {"index": INDEX, "flag": "1D"}),
    ("indexTrackerApi", "getIndexChart", {"index": INDEX, "flag": "1W"}),
    ("indexTrackerApi", "getIndexChart", {"index": INDEX, "flag": "1M"}),
    ("indexTrackerApi", "getIndexChart", {"index": INDEX, "flag": "1Y"}),
    ("indexTrackerApi", "getIndicesReturn", {"index": INDEX}),
    ("indexTrackerApi", "getTopFiveStock", {"index": INDEX, "flag": "G"}),  # Gainers
    ("indexTrackerApi", "getTopFiveStock", {"index": INDEX, "flag": "L"}),  # Losers
    ("indexTrackerApi", "getContributionData", {"index": INDEX, "noofrecords": "0", "flag": "1"}),  # Point contributors
    ("indexTrackerApi", "getContributionData", {"index": INDEX, "flag": "0"}),  # All contributors
    ("indexTrackerApi", "getIndicesHeatMap", {"index": INDEX}),
    ("indexTrackerApi", "getConstituents", {"index": INDEX, "noofrecords": "0"}),  # All constituents
    ("indexTrackerApi", "getConstituents", {"index": INDEX, "noofrecords": "7"}),  # Top 7
    ("indexTrackerApi", "getCorporateAction", {"index": INDEX, "flag": "CAC"}),
    ("indexTrackerApi", "getAnnouncementsIndices", {"index": INDEX, "flag": "CAN"}),
    ("indexTrackerApi", "getBoardMeeting", {"index": INDEX, "flag": "BM"}),
    ("indexTrackerApi", "getIndexFacts", {"index": INDEX}),
    ("indexTrackerApi", "getAdvanceDecline", {"index": INDEX}),
    ("indexTrackerApi", "getAllIndicesSymbols", {"index": INDEX}),

    # Symbol-specific within index context
    ("indexTrackerApi", "getShareHoldingData", {"symbol": SYMBOL}),
    ("indexTrackerApi", "getFinancialResultGraph", {"symbol": SYMBOL}),
]

client = NSEIndiaHTTPClient(timeout=30.0)
output_dir = Path("index_api_responses")
output_dir.mkdir(exist_ok=True)

results = {}

for api_type, api_name, params in ALL_INDEX_APIS:
    # Create unique filename
    filename = api_name
    if "flag" in params:
        filename = f"{api_name}_{params['flag']}"
    if "symbol" in params and params["symbol"]:
        filename = f"{api_name}_{params['symbol']}"
    if "noofrecords" in params:
        filename = f"{api_name}_n{params['noofrecords']}"

    print(f"Fetching {filename}...")
    try:
        if api_type == "indexTrackerApi":
            result = get_index_tracker_api(client, api_name, **params)
        else:
            result = get_api_client(client, api_name, **params)

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
