# Abstract Factory Interface (Factory Pattern)
from abc import ABC, abstractmethod

from connectors.models.scorecard_model import BattingEntry,BowlingEntry,Inning,FullScorecardData
from connectors.models.btb_model import MatchData
from connectors.models.table_model import TableTeamData
class CricketDataInterface(ABC):
    @abstractmethod
    def load_ipl_season_squads(self,series_url:str) -> list[dict]: pass

    @abstractmethod
    def load_match_scorecard(self,series_url:str) -> FullScorecardData: pass

    @abstractmethod
    def load_point_table(self,series_url:str) -> TableTeamData: pass

    @abstractmethod 
    def load_mvps(self,series_url:str) -> list[dict]: pass # need to impliment the scraping
    
    @abstractmethod
    def live_bbb_commentary(self,match_url:str) -> list[dict]: pass

    @abstractmethod
    def live_overwise_summary(self,match_url:str) -> list[dict]: pass

    @abstractmethod
    def live_match_links(self) -> list[dict] : pass

    @abstractmethod
    def btb_innings(self) -> MatchData: pass

class F1DataInterface(ABC):
    pass

class RealTimeIPLDataInterface(ABC):
    pass