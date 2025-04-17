from connectors.cd_connector import CDConnector
from connectors.utils.constants import IPL_SERIES_2025_URL
import json
cricket_data = CDConnector()

cricket_scorecard_data = cricket_data.live_match_links()

print("match score data ", json.dumps(cricket_scorecard_data, indent=4))