 # OOP class using python-espncricinfo
from connectors.base import CricketDataInterface
from espncricinfo.match import Match
from connectors.espn_fallback import ESPNFallback

class ESPNConnector(CricketDataInterface):
    def __init__(self):
        self.fallback = ESPNFallback()

    def load_match_details(self, match_id: str) -> dict:
        try:
            match = Match(match_id)
            return match.__dict__
        except Exception:
            return self.fallback.scrape_match_details(match_id)

    def load_scorecard(self, match_id: str) -> dict:
        try:
            match = Match(match_id)
            return match.scorecard
        except Exception:
            return self.fallback.scrape_scorecard(match_id)

    def load_commentary(self, match_id: str) -> dict:
        return self.fallback.scrape_commentary(match_id)

    def load_live_scores(self) -> list[dict]:
        return self.fallback.scrape_live_scores()

    def load_player_profile(self, player_id: str) -> dict:
        return self.fallback.scrape_player_profile(player_id)

    def load_team_info(self, team_id: str) -> dict:
        return self.fallback.scrape_team_info(team_id)

    def load_fixtures(self) -> list[dict]:
        return self.fallback.scrape_fixtures()

    def load_series_info(self, series_id: str) -> dict:
        return self.fallback.scrape_series_info(series_id)

    def load_standings(self) -> list[dict]:
        return self.fallback.scrape_standings()