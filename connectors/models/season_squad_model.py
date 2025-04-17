from pydantic import BaseModel, HttpUrl
from typing import List


class Player(BaseModel):
    name: str
    profile_url: HttpUrl


class Squad(BaseModel):
    year: str
    name: str
    url: HttpUrl
    players: List[Player]
