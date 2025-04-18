

BASE_URL = "https://www.espncricinfo.com"
BASE_FIXTURE_AND_RESULT_URL = "match-schedule-fixtures-and-results"
BASE_TEAMS_URL = "teams"
BASE_SQUADS_URL = "squads"
BASE_PONITS_TABLE = "points-table-standings"
BASE_MOST_VALUABLE_PLAYER = "most-valuable-players" 

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1"
}  
IPL_SERIES_URLS = [
    "/series/indian-premier-league-2007-08-313494",
    "/series/indian-premier-league-2009-374163",
    "/series/indian-premier-league-2009-10-418064",
    "/series/indian-premier-league-2011-466304",
    "/series/indian-premier-league-2012-520932",
    "/series/indian-premier-league-2013-586733",
    "/series/pepsi-indian-premier-league-2014-695871",
    "/series/pepsi-indian-premier-league-2015-791129",
    "/series/ipl-2016-968923",
    "/series/ipl-2017-1078425",
    "/series/ipl-2018-1131611",
    "/series/ipl-2019-1165643",
    "/series/ipl-2020-21-1210595",
    "/series/ipl-2021-1249214",
    "/series/indian-premier-league-2022-1298423",
    "/series/indian-premier-league-2023-1345038",
    "/series/indian-premier-league-2024-1410320"
]
IPL_SERIES_2025_URL = "/series/ipl-2025-1449924"


LIVE_SCRAPE_URL = "https://www.cricbuzz.com/live-cricket-scores/115140/mi-vs-dc-29th-match-indian-premier-league-2025"
LIVE_IPL_LSG_VS_CSK = "https://www.cricbuzz.com/live-cricket-scores/115149/lsg-vs-csk-30th-match-indian-premier-league-2025"
