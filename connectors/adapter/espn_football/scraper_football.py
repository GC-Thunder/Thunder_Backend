from selenium import webdriver
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
from datetime import datetime

def fetch_espn_match_data(date="20250409"):
    if date is None:
        date = datetime.utcnow().strftime("%Y%m%d")
    # Set up Chrome WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-proxy-server')
    options.add_argument('--ignore-certificate-errors')  # only for dev
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")


    driver = webdriver.Chrome(options=options)
    url = f"https://www.espn.in/football/scoreboard/_/date/{date}/league/uefa.champions"
    driver.get(url)
    time.sleep(10)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    driver.quit()

    match_data = []

    # Step 1: Extract match scores and teams
    score_sections = soup.select('div.Scoreboard__Column--1')
    for sec in score_sections:
        teams = [t.text.strip() for t in sec.select('.ScoreCell__TeamName')]
        scores = []
        for s in sec.select('.ScoreCell__Score'):
            try:
                scores.append(int(s.text.strip()))
            except ValueError:
                scores.append(-1)

        if len(teams) == 2 and len(scores) == 2:
            match_data.append({
                "score": {
                    "home": scores[0],
                    "away": scores[1]
                },
                "teams": {
                    "home": teams[0],
                    "away": teams[1]
                },
                "headline": "",
                "description": ""
            })

    # Step 2: Extract headlines and descriptions
    sections = soup.select('section.column-content')
    headline_info = []
    for sec in sections:
        try:
            headline = sec.select_one('h1').text.strip()
            description = sec.select_one('p').text.strip()
            headline_info.append({
                "headline": headline,
                "description": description
            })
        except:
            continue

    # Step 3: Assign headlines/descriptions
    for i in range(min(len(match_data), len(headline_info))):
        match_data[i]['headline'] = headline_info[i]['headline']
        match_data[i]['description'] = headline_info[i]['description']

    # Step 4: Create final structured object with timestamp
    final_data = {
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "date": date,
        "matches": match_data
    }

    # Step 5: Save to JSON file
    filename = f"ucl_matches_{date}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)

    print(f"✅ Match data saved to {filename}")
    return final_data


# # Run
# if __name__ == "__main__":
#     from pprint import pprint
#     pprint(fetch_espn_match_data())
