from connectors.cd_connector import CDConnector
from connectors.utils.constants import IPL_SERIES_2025_URL
import json
cricket_data = CDConnector()
test_match_url = "https://www.cricbuzz.com/live-cricket-scores/115165/dc-vs-rr-32nd-match-indian-premier-league-2025"
cricket_scorecard_data = cricket_data.live_match_links()

print("match score data ", json.dumps(cricket_scorecard_data, indent=4))


# from connectors.tasks.cricket_tasks import schedule_today_matches

# schedule_today_matches.delay("Hyd vs MI", "https://...")


