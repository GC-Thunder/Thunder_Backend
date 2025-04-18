from pydantic import BaseModel
from typing import List, Dict, Optional


class OutcomeBy(BaseModel):
    wickets: Optional[int] = None
    runs: Optional[int] = None


class Outcome(BaseModel):
    winner: str
    by: OutcomeBy


class Toss(BaseModel):
    decision: str
    winner: str


class Event(BaseModel):
    name: str
    match_number: int


class Officials(BaseModel):
    match_referees: List[str]
    reserve_umpires: List[str]
    tv_umpires: List[str]
    umpires: List[str]


class Info(BaseModel):
    balls_per_over: int
    city: str
    dates: List[str]
    event: Event
    gender: str
    match_type: str
    officials: Officials
    outcome: Outcome
    overs: int
    player_of_match: List[str]
    players: Dict[str, List[str]]
    registry: Dict[str, Dict[str, str]]
    season: str
    team_type: str
    teams: List[str]
    toss: Toss
    venue: str


class Meta(BaseModel):
    data_version: str
    created: str
    revision: int


class Runs(BaseModel):
    batter: int
    extras: int
    total: int


class Delivery(BaseModel):
    batter: str
    bowler: str
    non_striker: str
    runs: Runs


class Over(BaseModel):
    over: int
    deliveries: List[Delivery]


class Inning(BaseModel):
    team: str
    overs: List[Over]


class MatchData(BaseModel):
    meta: Meta
    info: Info
    innings: List[Inning]
