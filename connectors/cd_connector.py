from connectors.base import CricketDataInterface
from connectors.espncrickinfo_connector import ESPNCrickinfo
from connectors.crickbuzz_connector import CrickbuzzCrickinfo
from connectors.cricksheet_connector import CricksheetCrickinfo
from connectors.utils import constants
from connectors.models.scorecard_model import FullScorecardData
from connectors.models.table_model import TableTeamData
from connectors.models.btb_model import MatchData
from connectors.models.season_squad_model import Squad
from connectors.models.live_model import Commentary,OverwiseSummary,DailyMatchLinks

import json
from urllib.parse import urljoin,urlparse
# ESPNCrickinfo will squad data  
class CDConnector(CricketDataInterface):
    def __init__(self):
        self.espn = ESPNCrickinfo(
            constants.headers,
            constants.BASE_URL,
            constants.BASE_FIXTURE_AND_RESULT_URL,
            constants.BASE_TEAMS_URL,
            constants.BASE_SQUADS_URL,
            constants.BASE_MOST_VALUABLE_PLAYER,
            constants.BASE_PONITS_TABLE,
            constants.IPL_SERIES_URLS,
            constants.IPL_SERIES_2025_URL
        )
        self.crickbuzz = CrickbuzzCrickinfo()
        self.cricksheet = CricksheetCrickinfo(cleanup=True)
    
    def load_match_scorecard(self, series_url:str):
        match_url = urljoin(constants.BASE_URL, series_url)
        match_fixture_links: list[dict] = self.espn.scrape_live_scorecard_links_from_fixture_and_Result(match_url)
        
        complete_match_scorecard_data = []
        for i ,_ in enumerate(match_fixture_links):
            match_score_data = self.espn.scrape_match_full_scorecard_innings_data(match_fixture_links[i]["link"])
            complete_match_scorecard_data.append(match_score_data)
        return complete_match_scorecard_data
    
    def load_ipl_season_squads(self,series_url:str) -> Squad:
        return self.espn.scrape_ipl_squards_data(series_url)
        
    def load_point_table(self,series_url:str) -> TableTeamData:
        return self.espn.scrape_ipl_table_data(series_url)
    def load_mvps(self,series_url:str) -> list[dict]: pass # need to impliment the scraping

    def live_match_links(self) -> DailyMatchLinks:
        match_links = self.crickbuzz.scrape_daily_live_match_link_selenium()
        march_links_filtered = [match for match in match_links if match['today'] != '']
        
        return march_links_filtered
    
    def live_bbb_commentary(self,match_url:str): # will define model after testing 
        return self.crickbuzz.scrape_live_bbb_commentary(match_url)
        
    def live_overwise_summary(self,match_url:str): # will define model after testing 
        return self.crickbuzz.scrape_overwise_summary(match_url)

    def btb_innings(self,n:int) -> MatchData:
        return self.cricksheet.run(n)