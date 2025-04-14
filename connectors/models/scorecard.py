from typing import TypedDict, List, Dict, Union

class BattingEntry(TypedDict):
    Player: str
    Dismissal: str
    Runs: str
    Balls: str
    Four: str
    Six: str
    SR: str

class BowlingEntry(TypedDict):
    Bowler: str
    Overs: str
    Maidens: str
    Runs: str
    Wickets: str
    Econ: str
    Dots: str
    Four: str
    Six: str
    WD: str
    NB: str

class Inning(TypedDict):
    Innings: str
    Batting: List[BattingEntry]
    Extras: List[Dict[str, str]]
    Total: List[Dict[str, str]]
    Bowling: List[BowlingEntry]
    Did_not_bat: List[str]
    Fall_of_wickets: List[str]
    Match_Flow: List[Dict[str, Union[int, str]]]

class FullScorecardData(TypedDict):
    match_details: Dict[str, str]
    innings: List[Inning]
