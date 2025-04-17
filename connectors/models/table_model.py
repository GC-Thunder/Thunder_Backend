from pydantic import BaseModel
from typing import List


class MatchSummary(BaseModel):
    match_info: str
    summary: str


class TeamStats(BaseModel):
    M: str
    W: str
    L: str
    T: str
    N_R: str  # N/R (No Result)
    PT: str
    NRR: str


class TableTeamData(BaseModel):
    team: str
    stats: TeamStats
    matches: List[MatchSummary]
