from connectors.base import CricketDataInterface
from espncricinfo.match import Match
from espncricinfo.series import Series
from espncricinfo.player import Player
from espncricinfo.summary import Summary
from espncricinfo.player import Player


# from connectors.espn.fallback import ESPNFallback  # assuming your fallback class is here


class ESPNConnector(CricketDataInterface):
    def __init__(self):
        # self.fallback = ESPNFallback()
        pass

    def load_match_details(self, match_id: str) -> dict:
        match = Match(match_id)
        return match.__dict__

    def load_scorecard(self, match_id: str) -> dict:
        match = Match(match_id)
        return match.scorecard

    def load_commentary(self, match_id: str) -> dict:
        match = Match(match_id)
        return match.commentary

    def load_live_scores(self) -> list[dict]:
        # Not available via API, fallback to scraper
        return self.fallback.scrape_live_scores()

    def load_player_profile(self, player_id: str) -> dict:
        player = Player(player_id)
        return player.__dict__

    # def load_team_info(self, team_id: str) -> dict:
    #     team = Team(team_id)
    #     return team.__dict__

    def load_fixtures(self) -> list[dict]:
        # Not available via API, fallback to scraper
        return self.fallback.scrape_fixtures()

    def load_series_info(self, series_id: str) -> dict:
        series = Series(series_id)
        return series.__dict__

    def load_standings(self) -> list[dict]:
        # Not available via API, fallback to scraper
        return self.fallback.scrape_standings()
