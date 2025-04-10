# Abstract Factory Interface (Factory Pattern)
from abc import ABC, abstractmethod

class CricketDataInterface(ABC):
    @abstractmethod
    def load_match_details(self, match_id: str) -> dict: pass

    @abstractmethod
    def load_player_profile(self, player_id: str) -> dict: pass

    @abstractmethod
    def load_team_info(self, team_id: str) -> dict: pass

    @abstractmethod
    def load_commentary(self, match_id: str) -> dict: pass

    @abstractmethod
    def load_scorecard(self, match_id: str) -> dict: pass

    @abstractmethod
    def load_live_scores(self) -> list[dict]: pass

    @abstractmethod
    def load_fixtures(self) -> list[dict]: pass

    @abstractmethod
    def load_standings(self) -> list[dict]: pass

    @abstractmethod
    def load_series_info(self, series_id: str) -> dict: pass

class F1DataInterface(ABC):
    pass

class RealTimeIPLDataInterface(ABC):
    pass