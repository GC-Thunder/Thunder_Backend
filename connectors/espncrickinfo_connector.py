
# Fallback BeautifulSoup scraper ├── utils/
import os 
import requests
import time 
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin,urlparse
# from requests_html import HTMLSession
import json 
from connectors.models.scorecard_model import BattingEntry,BowlingEntry,Inning,FullScorecardData
from connectors.models.table_model import TableTeamData
from connectors.models.season_squad_model import Squad
from connectors.utils import constants
class ESPNCrickinfo():
    def __init__(
        self,
        headers,
        base_url,
        base_fixture_and_results_url,
        base_teams_url,
        base_squads_url,
        base_most_valuable_player,
        base_points_table,
        ipl_series_list_historical,
        ipl_series_2025,
    ):
        self.headers = headers
        self.ipl_series_list_historical = ipl_series_list_historical
        self.ipl_series_2025 = ipl_series_2025
        self.base_url = base_url
        self.base_fixture_and_results_url = base_fixture_and_results_url
        self.base_teams_url = base_teams_url
        self.base_squads_url = base_squads_url
        self.base_most_valuable_player = base_most_valuable_player
        self.base_points_table = base_points_table
    
    def scrape_team_history(self,ipl_team_url):

        description = """
        This function scrapes the historical performance and achievements of an IPL team,
        including season-by-season records, title wins, and notable highs and lows.
        """

        session = requests.Session()
        response = session.get(ipl_team_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch IPL series team page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")

        team_info = {}

        # General info: Captain, Coach, Home ground, Titles, Owners
        info_div = soup.find('div', class_='ds-relative ds-overflow-hidden')
        if info_div:
            bold_tags = info_div.find_all('b')
            try:
                team_info['captain'] = bold_tags[0].text if len(bold_tags) > 0 else None
                team_info['coach'] = bold_tags[1].text if len(bold_tags) > 1 else None
                team_info['home_ground'] = bold_tags[2].text if len(bold_tags) > 2 else None
                team_info['ipl_titles'] = bold_tags[3].text if len(bold_tags) > 3 else None
                team_info['owners'] = bold_tags[4].text if len(bold_tags) > 4 else None
            except IndexError:
                pass  # In case there are not enough bold tags, pass and return None for each key

        # Paragraph history section
        history = []

        # Loop over all inner <div> elements inside info_div
        divs = info_div.find_all('div', recursive=True) if info_div else []
        for div in divs:
            h2 = div.find('h2')
            content = div.get_text(separator=' ', strip=True)
            if h2:
                title = h2.text.strip()
                h2.extract()
            else:
                title = None
            
            if content:  # Only append if content is not empty
                history.append({
                    'section': title,
                    'content': content
                })
        
        team_info['history_sections'] = history if history else None

        # Season-by-season performance
        seasons = []
        season_blocks = info_div.find_all('div') if info_div else []
        for block in season_blocks:
            bold = block.find('b')
            if bold and '-' in bold.text:
                year_line = bold.text.strip()
                details = block.text.replace(year_line, '').strip()
                seasons.append({
                    'summary': year_line,
                    'details': details
                })

        team_info['season_performance'] = seasons if seasons else None

        return team_info
        
    def scrape_ipl_team_links_data(self,series_url: str) -> list[dict]:
        description = """Scrapes the list of IPL team links and normalized names from the given IPL series URL."""

        fixture_and_team_url = urljoin(self.base_url, series_url + '/', self.base_teams_url)
        session = requests.Session()
        response = session.get(fixture_and_team_url, headers=self.base_teams_url)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch IPL series team page: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        season_team_links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/team/" in href:
                span = a.find("span")
                if span:
                    raw_name = span.get_text(strip=True)
                    normalized_name = raw_name.lower().replace(" ", "_")
                    full_url = urljoin(self.base_url, href)

                    # Now, scrape the team history and season performance data
                    try:
                        print(f"Scraping data for: {normalized_name}")
                        team_history = self.scrape_team_history(full_url)

                        # Store the team data along with the history and performance
                        season_team_links.append({
                            "name": normalized_name,
                            "url": full_url,
                            "history": team_history
                        })
                    except Exception as e:
                        print(f"Error scraping {normalized_name}: {e}")

        return season_team_links
    

    def scrape_squad_players_data(self,squad_url: str):
        session = requests.Session()
        response = session.get(squad_url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch squad page: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        
        players_dict = {}
        squad_data = []

        for player_block in soup.find_all("div", class_="ds-flex-1"):
            a_tag = player_block.find("a", href=re.compile(r"^/cricketers/"))
            role_tag = player_block.find("p", class_="ds-text-tight-s ds-font-regular ds-mb-2 ds-mt-1")

            if a_tag and role_tag:
                player_name = a_tag.get("title", "").strip()
                player_href = urljoin(self.base_url, a_tag.get("href", "").strip())
                role = role_tag.get_text(strip=True)

                players_dict[player_name] = player_href
                squad_data.append({
                    "title": player_name,
                    "role": role,
                    "url": player_href
                })

        return players_dict, squad_data


    def scrape_ipl_squards_data(self,series_url: str) -> Squad:
        # Extract year from series_url
        match = re.search(r"\b(20\d{2})\b", series_url)
        ipl_year = match.group(1) if match else "Unknown"

        # Ensure proper formatting
        if not series_url.startswith("/"):
            series_url = "/" + series_url
        if not series_url.endswith("/"):
            series_url += "/"

        seasons_squads_url = urljoin(self.base_url, series_url + self.base_squads_url)

        session = requests.Session()
        response = session.get(seasons_squads_url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch IPL series team page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        season_squads_data = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if series_url in href and "/series-squads" in href:
                span = a.find("span")
                if span:
                    squad_name = span.get_text(strip=True)
                    full_url = urljoin(self.base_url, href)

                    # 👇 Fetch player data for this squad
                    _, players = self.scrape_squad_players_data(full_url)

                    season_squads_data.append({
                        "year": ipl_year,
                        "name": squad_name,
                        "url": full_url,
                        "players": players
                    })

        return season_squads_data


    def get_fall_of_wickets_and_did_not_bat(self,soup):
        part_innings_data = [
            {"fall_of_wickets": [], "did_not_bat": []},
            {"fall_of_wickets": [], "did_not_bat": []}
        ]
        index_1 = 0
        index_2 = 0

        for strong in soup.find_all("strong"):
            heading = strong.text.strip()

            if "Fall of wickets" in heading:
                container = strong.find_parent("div")
                if not container:
                    continue

                for span in container.find_all("span"):
                    text = span.get_text(strip=True)
                    if text and "ov" in text:
                        if index_1 < 2:
                            part_innings_data[index_1]["fall_of_wickets"].append(text)
                index_1 += 1

            elif "Did not bat" in heading:
                container = strong.find_parent("div")
                if not container:
                    continue

                for a in container.find_all("a"):
                    name = a.get_text(strip=True).rstrip(',')
                    if name:
                        if index_2 < 2:
                            part_innings_data[index_2]["did_not_bat"].append(name)
                index_2 += 1

        return part_innings_data


    def get_extras_data(self,soup):
        extras_data = []
        for tr in soup.find_all("tr", class_="ds-text-tight-s"):
            if len(extras_data) == 2:
                break  # Limit to two "Extras" entries

            tds = tr.find_all("td")
            if not tds or "Extras" not in tds[0].get_text(strip=True):
                continue

            extras_total = tr.find("strong")
            extras_total_value = extras_total.get_text(strip=True) if extras_total else None

            extras_breakdown = ""
            for td in tds:
                text = td.get_text(strip=True)
                if text.startswith("(") and text.endswith(")"):
                    extras_breakdown = text
                    break

            extras_data.append({
                "total": extras_total_value,
                "breakdown": extras_breakdown
            })

        return extras_data

    def get_total_data(self , soup):
        total_data = []

        for tr in soup.find_all("tr"):
            if len(total_data) == 2:
                break  # We've already captured two totals

            tds = tr.find_all("td")
            if not tds:
                continue

            # Check if any cell contains the word "Total"
            if any("Total" in td.get_text(strip=True) for td in tds):
                score = tds[2].get_text(strip=True) if len(tds) > 2 else None
                overs_rr = tds[1].get_text(strip=True) if len(tds) > 1 else ""
                overs, rr = None, None

                if "Ov" in overs_rr and "RR" in overs_rr:
                    parts = overs_rr.split("(RR:")
                    overs = parts[0].strip().replace("Ov", "").strip()
                    rr = parts[1].replace(")", "").strip() if len(parts) > 1 else None

                total_data.append({
                    "score": score,
                    "overs": overs,
                    "run_rate": rr
                }) 

        return total_data



    def scrape_match_full_scorecard_match_flow_data_from_soup(self,soup):
        match_flow_data = {}

        innings_ul = soup.find_all(
            "ul",
            class_="ds-text-tight-s ds-font-regular ds-list-disc ds-pt-2 ds-px-4 ds-mb-4"
        )
        
        if len(innings_ul) >= 2:
            first_innings_team = innings_ul[0].find("span").get_text(strip=True)
            first_innings_flow = [li.get_text(strip=True) for li in innings_ul[0].find_all("li")]
            match_flow_data[first_innings_team] = first_innings_flow
            
            second_innings_team = innings_ul[1].find("span").get_text(strip=True)
            second_innings_flow = [li.get_text(strip=True) for li in innings_ul[1].find_all("li")]
            match_flow_data[second_innings_team] = second_innings_flow

        return match_flow_data

    def scrape_match_full_scorecard_match_details_data_from_soup(self,soup):
        match_details_data = {}

        match_details_table = soup.find("table", class_="ds-w-full ds-table ds-table-sm ds-table-auto")
        if not match_details_table:
            return match_details_data  # Fail gracefully

        match_details_rows = match_details_table.find("tbody").find_all("tr")

        for row in match_details_rows:
            cols = row.find_all("td")

            if len(cols) == 1:
                stadium_name = cols[0].get_text(strip=True)
                match_details_data["Stadium name"] = stadium_name
            elif len(cols) == 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                match_details_data[key] = value

        return match_details_data

    def scrape_match_full_scorecard_innings_data(self,full_scorecard_url: str)-> FullScorecardData:
        session = requests.Session()
        response = session.get(full_scorecard_url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch scorecard page: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        innings_data: Inning = []

        innings_divs = [ div for div in soup.find_all("div", class_="ds-p-0") if len(div.find_all("table")) == 2 ]

        for i, inning_div in enumerate(innings_divs):
            batting_table = inning_div.find_all("table", class_="ci-scorecard-table")

            batting_data: BattingEntry = []
            if batting_table:
                # FIXED LINE: get the first table from the list

                batting_rows = batting_table[0].find("tbody").find_all("tr")
                for row in batting_rows:
                    cols = row.find_all("td")
                    if len(cols) >= 8:
                        batting_data.append({
                            "Player": cols[0].get_text(strip=True),
                            "Dismissal": cols[1].get_text(strip=True),
                            "Runs": cols[2].get_text(strip=True),
                            "Balls": cols[3].get_text(strip=True),
                            "4s": cols[5].get_text(strip=True),
                            "6s": cols[6].get_text(strip=True),
                            "SR": cols[7].get_text(strip=True)
                        })
            
            innings_data.append({
                "Innings": f"Innings {i+1}",
                "Batting": batting_data,
                "Extras":[],
                "Total" : [],
                "Bowling": [],
                "Did not bat":[],
                "Fall of wickets":[],
                "Match Flow":[],
            })

        for i, inning_div in enumerate(innings_divs):
            # Filter for bowling tables: class must be "ds-w-full ds-table ds-table-xs ds-table-auto" and not "ci-scorecard-table"
            bowling_table = [table for table in inning_div.find_all("table") if "ci-scorecard-table" not in table.get("class", [])]
            
            bowling_data: BowlingEntry = []
            if bowling_table:
                bowling_rows = bowling_table[0].find("tbody").find_all("tr")  # Similar fix
                for row in bowling_rows:
                    cols = row.find_all("td")
                    if len(cols) >= 11:
                        bowling_data.append({
                            "Bowler": cols[0].get_text(strip=True),
                            "Overs": cols[1].get_text(strip=True),
                            "Maidens": cols[2].get_text(strip=True),
                            "Runs": cols[3].get_text(strip=True),
                            "Wickets": cols[4].get_text(strip=True),
                            "Econ": cols[5].get_text(strip=True),
                            "Dots": cols[6].get_text(strip=True),
                            "4s": cols[7].get_text(strip=True),
                            "6s": cols[8].get_text(strip=True),
                            "WD": cols[9].get_text(strip=True),
                            "NB": cols[10].get_text(strip=True),
                        })

            innings_data[i]["Bowling"] = bowling_data
        extras = self.get_extras_data(soup)
        totals = self.get_total_data(soup)
        match_flow = self.scrape_match_full_scorecard_match_flow_data_from_soup(soup)
        wickets_dnb = self.get_fall_of_wickets_and_did_not_bat(soup)
        match_details = self.scrape_match_full_scorecard_match_details_data_from_soup(soup)
        for i in range(len(innings_data)):
            if i < len(extras):
                innings_data[i]["Extras"] = extras[i]
            if i < len(totals):
                innings_data[i]["Total"] = totals[i]
            if i < len(wickets_dnb):
                innings_data[i]["Fall of wickets"] = wickets_dnb[i]["fall_of_wickets"]
                innings_data[i]["Did not bat"] = wickets_dnb[i]["did_not_bat"]

            # Match flow keys are team names, so we find the correct one by matching order
            flow_keys = list(match_flow.keys())
            if i < len(flow_keys):
                innings_data[i]["Match Flow"] = match_flow[flow_keys[i]]

        # match details will be appended seperat dist as it has intersection with both the innings 

        return {
            "match_details": match_details,
            "innings": innings_data
        }


    def scrape_full_season_matches_data(self, match_url: str) -> list[str]:
        ficture_and_base_url = urljoin(match_url + '/', self.base_fixture_and_results_url)
        session = requests.Session()
        response = session.get(ficture_and_base_url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch IPL series page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # This is the full class string — it must match exactly or use CSS selectors
        span_elements = soup.select("span.ds-text-compact-s.ds-text-typo.ds-underline.ds-decoration-ui-stroke.hover\\:ds-text-typo-primary.hover\\:ds-decoration-ui-stroke-primary.ds-block.ds-mr-2.ds-cursor-pointer")
        
        match_titles = [span.get_text(strip=True) for span in span_elements]
        
        return match_titles

    def scrape_full_scorecard_links_from_fixture_and_Result(self,match_url: str) -> list[dict]:
        """
        Scrapes all full scorecard links and match results from the fixture/results page
        of a given match URL, ensuring that each link belongs to the same series.

        Returns:
            {
                "matches": List[{"link": str, "result": str}]
            }
        Todo : This loads scorecard till the most recent match , but it not loading other I dont know why this happening 
        if we get it we can keep on more element in dict load we can load based on availible data load = false no load or else load (this can be handeled
        diferently) this is the solution I can think of 
        """
        # Extract series path from match_url
        parsed_url = urlparse(match_url)
        path_parts = parsed_url.path.strip("/").split("/")
        series_path = "/".join(path_parts[:2])
        series_path_with_slash = f"/{series_path}"

        # Build the fixture and result page URL
        fixture_and_result_url = urljoin(match_url + '/', self.base_fixture_and_results_url)

        session = requests.Session()
        response = session.get(fixture_and_result_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch series page: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        matches = []

        for match_div in soup.find_all("div", class_="ds-mb-4"):
            a_tags = match_div.find_all("a", href=True)
            for a_tag in a_tags:
                href = a_tag["href"]
                if "/full-scorecard" in href and series_path_with_slash in href:
                    full_scorecard_link = urljoin(self.base_url, href)
                    result_span = next(
                        (span for span in a_tag.find_all("span") if not span.has_attr("class")),
                        None
                    )
                    result_text = result_span.get_text(strip=True) if result_span else "Result not found"
                    matches.append({
                        "link": full_scorecard_link,
                        "result": result_text,
                    })

        return matches
    
    def scrape_live_scorecard_links_from_fixture_and_Result(self, match_url: str) -> list[dict]:
        # Extract series path from match_url
        parsed_url = urlparse(match_url)
        path_parts = parsed_url.path.strip("/").split("/")
        series_path = "/".join(path_parts[:2])
        series_path_with_slash = f"/{series_path}"

        # Build the fixture and result page URL
        fixture_and_result_url = urljoin(match_url + '/', self.base_fixture_and_results_url)

        session = requests.Session()
        response = session.get(fixture_and_result_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch series page: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        matches = []

        for match_div in soup.find_all("div", class_="ds-mb-4"):
            a_tags = match_div.find_all("a", href=True)
            for a_tag in a_tags:
                href = a_tag["href"]
                classes = a_tag.get("class", [])

                if (
                    "/live-cricket-score" in href and
                    series_path_with_slash in href and
                    "ds-no-tap-higlight" in classes
                ):
                    # Replace "/live-cricket-score" with "/full-scorecard"
                    live_scorecard_path = href.replace("/live-cricket-score", "/full-scorecard")
                    live_scorecard_link = urljoin(self.base_url, live_scorecard_path)

                    result_para = a_tag.find("p", class_="ds-text-tight-s ds-font-medium ds-line-clamp-2 ds-text-typo")
                    result_text = result_para.get_text(strip=True) if result_para else "Result not found"

                    if(result_text != "Match yet to begin"):
                        matches.append({
                        "link": live_scorecard_link,
                        "result": result_text,
                    })
                
        return matches


    def scrape_full_scorecard_data(self,series_url: str):
        fixture_and_result = self.scrape_full_scorecard_links_from_fixture_and_Result(series_url)
        
        # Extract series identifier from URL
        series_slug = series_url.strip("/").split("/")[-1].replace("-", "_").upper()
        file_path = f"ipl/{series_slug}/scorecard.json"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Check if file exists and if it's empty
        is_new_file = not os.path.exists(file_path) or os.stat(file_path).st_size == 0

        # Open the file in append mode
        with open(file_path, "a") as f:
            if is_new_file:
                f.write("[\n")  # start of array

            for i, match in enumerate(fixture_and_result):
                try:
                    link = match["link"]
                    result = match["result"]

                    print(link)
                    scorecard: FullScorecardData = self.scrape_match_full_scorecard_innings_data(link)
                    scorecard["result"] = result  # Add match result to the scorecard

                    match_data = {
                        "match_no": i + 1,  # Match number (starting from 1)
                        "scorecard": scorecard
                    }

                    # Write each scorecard one-by-one
                    if not is_new_file:
                        f.write(",\n")  # add comma between JSON objects
                    else:
                        is_new_file = False  # first item written

                    json_data = json.dumps(match_data, indent=2)
                    f.write(json_data)
                    print(f"[{i+1}] ✅ Saved scorecard: {link}")

                except Exception as e:
                    print(f"[{i+1}] ❌ Failed to scrape {link}: {e}")

        # After all done, add closing bracket to complete the JSON array
        with open(file_path, "a") as f:
            f.write("\n]")

    def scrape_full_season_squads_data(self,series_url: str):
        try:
            squads_data = self.scrape_ipl_squards_data(series_url)

            # Extract series identifier from URL
            series_slug = series_url.strip("/").split("/")[-1].replace("-", "_").upper()
            file_path = f"ipl/{series_slug}/squads.json"

            print(file_path)
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write entire squad data as a valid JSON array
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(squads_data, f, indent=4, ensure_ascii=False)

            print(f"✅ All squads saved to {file_path}")

        except Exception as e:
            print(f"❌ Error while scraping full season squads: {e}")

    def scrape_full_season_team_data(self,series_url: str):
        try:
            # Fetch full team data including history and performance
            squads_data = self.scrape_ipl_team_links_data(series_url)

            file_path = os.path.join("ipl", "teams.json")

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(squads_data, f, indent=4, ensure_ascii=False)

            print(f"✅ All team data saved to {file_path}")

        except Exception as e:
            print(f"❌ Error while scraping full season team data: {e}")

    def scrape_ipl_table_data(self,series_url: str) ->list[TableTeamData]:

        fixture_url = urljoin(self.base_url, f"{series_url}/{self.base_points_table}")
        session = requests.Session()
        response = session.get(fixture_url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch IPL series page: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='ds-w-full ds-table ds-table-md ds-table-auto ds-w-full')
        rows = table.find('tbody').find_all('tr')
        
        all_team_data = []
        stat_keys = ["M", "W", "L", "T", "N/R", "PT", "NRR"]
        
        for i in range(0, len(rows), 2):
            points_row = rows[i]
            tds = points_row.find_all('td')
            
            team_name_span = tds[0].find('span', class_='ds-text-tight-s ds-font-bold ds-uppercase ds-text-left ds-text-typo')
            team_name = team_name_span.text.strip() if team_name_span else "Unknown Team"
            
            stat_values = [td.text.strip() for td in tds[1:]]
            stats = dict(zip(stat_keys, stat_values))
            
            match_data = []
            if i + 1 < len(rows):
                match_row = rows[i + 1]
                match_links = match_row.find_all('a', href=True)

                for a_tag in match_links:
                    try:
                        outer_div = a_tag.find('div', class_='ds-my-2 ds-flex ds-flex-row ds-space-x-2 ds-items-start')
                        if not outer_div:
                            continue

                        info_spans = outer_div.find_all('span', class_='ds-text-compact-xs ds-font-medium')
                        match_info = info_spans[0].text.strip() if len(info_spans) > 0 else ""

                        summary_spans = outer_div.find_all('span', class_='ds-text-compact-xs ds-text-typo-mid3 ds-text-left')
                        summary = summary_spans[0].text.strip() if len(summary_spans) > 0 else ""

                        match_data.append({
                            'match_info': match_info,
                            'summary': summary,
                        })
                    except (IndexError, AttributeError):
                        continue

            
            all_team_data.append({
                'team': team_name,
                'stats': stats,
                'matches': match_data
            })
        
        return all_team_data

    def scrape_complete_point_table_data(self ,series_url: str):
        try:
            # Fetch full team data including history and performance
            table_data = self.scrape_ipl_table_data(series_url)

            series_slug = series_url.strip("/").split("/")[-1].replace("-", "_").upper()
            file_path = f"ipl/{series_slug}/table.json"

            print(file_path)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(table_data, f, indent=4, ensure_ascii=False)

            print(f"✅ All Table data saved to {file_path}")

        except Exception as e:
            print(f"❌ Error while scraping full season Table data: {e}")
    def scrape_mvp_data(self, series_url):
        """
        Scrapes the MVP (Most Valuable Player) data for a specific IPL season.
        series_url is the relative URL for the IPL season (e.g., /series/ipl-2025-1449924).
        """
        # Construct the MVP URL for the specific series/season
        mvp_url = urljoin(self.base_url, series_url + "/" + self.base_most_valuable_player)
        
        session = requests.Session()
        response = session.get(mvp_url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch MVP page: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        # MVP data container
        mvp_data = []

        # Find all MVP table rows
        rows = soup.find_all('tr', class_='ds-text-tight-s')

        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 7:
                # Extracting rank and player name (rank is the numeric part)
                rank_player_string = columns[0].get_text(strip=True)
                match = re.match(r"(\d+)([A-Za-z\s]+)", rank_player_string)  # Regex to split number and string

                if match:
                    rank = match.group(1)  # Numeric rank
                    player_name = match.group(2).strip()  # Player name (alphabetic part)
                else:
                    # In case the regex fails (e.g., malformed rank)
                    rank = rank_player_string
                    player_name = ""

                # Extract team name (with error handling if the <a> tag is not found)
                team_tag = columns[1].find('a')
                team = team_tag.get_text(strip=True) if team_tag else "-"

                # Extract other fields (total impact, matches, runs)
                total_impact = columns[2].get_text(strip=True)
                impact_per_match = columns[3].get_text(strip=True)
                matches = columns[4].get_text(strip=True)
                runs = columns[5].get_text(strip=True)

                # Add the data to the list with improved formatting
                mvp_data.append({
                    "rank": rank,
                    "player_name": player_name,
                    "team": team,
                    "total_impact": total_impact,
                    "impact_per_match": impact_per_match,
                    "matches": matches if matches else "-",
                    "runs": runs if runs else "-"
                })

        return mvp_data
    def scrape_full_season_mvp_data(self):
        """
        Scrapes the MVP data for all IPL seasons from the IPL_SERIES_URLS list.
        """
        all_mvp_data = {}

        for series_url in self.ipl_series_list_historical:
            print(f"Scraping MVP data for: {series_url}")
            try:
                mvp_data = self.scrape_mvp_data(series_url)
                all_mvp_data[series_url] = mvp_data
                print(f"MVP data for {series_url}: {json.dumps(mvp_data, indent=4)}")
            except Exception as e:
                print(f"Failed to scrape MVP data for {series_url}: {e}")

        # Optionally, save the data to a file
        with open('mvp_data.json', 'w') as f:
            json.dump(all_mvp_data, f, indent=4)

        return all_mvp_data
if __name__ == "__main__":    
    espn = ESPNCrickinfo(
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
    match_url = urljoin(constants.BASE_URL, constants.IPL_SERIES_2025_URL)
    
    match_fixture_links: list[dict] = espn.scrape_live_scorecard_links_from_fixture_and_Result(match_url)
    print(json.dumps(match_fixture_links,indent=4))
    match_scorecard_data = espn.scrape_match_full_scorecard_innings_data(match_fixture_links[0]["link"])
    print("match score data ", json.dumps(match_scorecard_data, indent=4))
    mvp_data = espn.scrape_full_season_mvp_data()
    print(json.dumps(mvp_data, indent=4))