from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class MatchLinkData(BaseModel):
    title: str
    link: HttpUrl
    today: Optional[str] = ""
    time: Optional[str] = ""
    stadium: Optional[str] = ""


class DailyMatchLinks(BaseModel):
    matches: List[MatchLinkData]

class Commentary(BaseModel):
    over: str
    commentary: str

class LiveCommentary(BaseModel):
    match_url: str
    commentary_data: List[Commentary]

class OverwiseSummary(BaseModel):
    over: str
    runs_scored: str
    over_summary: str
    score_after: str
    team_score: str
    batter1: str
    batter2: str
    bowler: str


class OverwiseData(BaseModel):
    type: str
    overwise_summary: List[OverwiseSummary]
