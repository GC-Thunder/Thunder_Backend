import time 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from connectors.models.live_model import Commentary,OverwiseSummary,DailyMatchLinks


class CrickbuzzCrickinfo():
    def __init__(self):
        self.base_upcoming_matches_url = "https://www.cricbuzz.com/cricket-match/live-scores/upcoming-matches"
        pass

    def scrape_overwise_summary(self,match_url: str) -> OverwiseSummary:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(match_url)

            overwise_data = []
            summary_blocks = driver.find_elements(By.CLASS_NAME, "cb-com-ovr-sum-rw")

            for block in summary_blocks:
                try:
                    over = block.find_element(By.CLASS_NAME, "cb-font-18").text.strip()

                    # 🟡 Runs scored & Over summary
                    runs_block = block.find_elements(By.CLASS_NAME, "cb-com-ovr-sum-itm")[1]
                    runs_scored = runs_block.find_element(By.CLASS_NAME, "text-bold.ng-binding").text.strip()
                    over_summary = runs_block.find_elements(By.CLASS_NAME, "text-bold.ng-binding")[1].text.strip()

                    # 🟢 Score after + team score
                    score_block = block.find_elements(By.CLASS_NAME, "cb-com-ovr-sum-itm")[2]
                    score_after = score_block.find_elements(By.CLASS_NAME, "ng-binding")[0].text.strip()
                    team_score = score_block.find_elements(By.CLASS_NAME, "text-bold.ng-binding")[0].text.strip()

                    # 🔵 Batter info
                    batter_block = block.find_elements(By.CLASS_NAME, "cb-com-ovr-sum-itm")[3]
                    batters = batter_block.find_elements(By.CLASS_NAME, "cb-col.cb-col-67.ng-binding")
                    scores = batter_block.find_elements(By.CLASS_NAME, "cb-col.cb-col-33.text-right.ng-binding")
                    batter1 = batters[0].text.strip()
                    batter1_score = scores[0].text.strip()
                    batter2 = batters[1].text.strip()
                    batter2_score = scores[1].text.strip()

                    # 🔴 Bowler info
                    bowler_block = block.find_elements(By.CLASS_NAME, "cb-com-ovr-sum-itm")[4]
                    bowler = bowler_block.find_elements(By.CLASS_NAME, "ng-binding")[0].text.strip()
                    bowler_figures = bowler_block.find_elements(By.CLASS_NAME, "ng-binding")[1].text.strip()

                    overwise_data.append({
                        "type": "over_summary",
                        "over": over,
                        "runs_scored": runs_scored,
                        "over_summary": over_summary,
                        "score_after": score_after,
                        "team_score": team_score,
                        "batter1": f"{batter1} {batter1_score}",
                        "batter2": f"{batter2} {batter2_score}",
                        "bowler": f"{bowler} {bowler_figures}"
                    })

                except Exception as e:
                    continue  # Skip any faulty block

            return overwise_data

        finally:
            driver.quit()
    # bbb -> ball by ball
    def scrape_live_bbb_commentary(self,match_url: str) -> Commentary:
        # Set up Chrome options to run headlessly
        options = Options()
        options.headless = True  # Ensure this is set to True to run in headless mode

        # Start the browser in headless mode
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        try:
            # Open the match URL
            driver.get(match_url)
            
            # Wait for the page to load (adjust based on your internet speed)
            time.sleep(10)  # You can adjust this sleep duration

            commentary_data = []

            # Find all top-level commentary divs with an ID like "comm_1744553094941"
            commentary_blocks = driver.find_elements(By.CSS_SELECTOR, "div[id^='comm_']")
            
            for block in commentary_blocks:
                try:
                    # Try to find over and commentary elements within each block
                    over_div = block.find_element(By.CSS_SELECTOR, "div.cb-col.cb-col-8.text-bold.ng-scope")
                    commentary_p = block.find_element(By.CSS_SELECTOR, "p.cb-com-ln.ng-binding.ng-scope.cb-col.cb-col-90")
                    
                    # If both elements are found, extract the data
                    if over_div and commentary_p:
                        over = over_div.text.strip()
                        commentary = commentary_p.text.strip()
                        commentary_data.append({
                            "over": over,
                            "commentary": commentary
                        })
                except Exception as e:
                    # Print error message if any element is not found or there are other issues
                    print(f"Error processing a commentary block: {e}")
            
            return commentary_data
        
        finally:
            # Close the browser after scraping
            driver.quit()

    def scrape_score_with_selenium(self,match_url: str):
        # Setup headless Chrome
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-dev-shm-usage")

        # Set path to chromedriver if not in PATH
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(match_url)

            # Wait for the score element to appear
            wait = WebDriverWait(driver, 10)
            score_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2.cb-font-20.text-bold.inline-block.ng-binding"))
            )

            return score_element.text.strip()

        except Exception as e:
            return f"Error: {str(e)}"
        
        finally:
            driver.quit()
    
    def scrape_daily_live_match_link_selenium(self)->DailyMatchLinks:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        url = "https://www.cricbuzz.com/cricket-match/live-scores/upcoming-matches"
        driver.get(url)
        time.sleep(3)

        all_match_link_data = []

        # Find all league sections
        league_sections = driver.find_elements(By.CSS_SELECTOR, "div.cb-col.cb-col-100.cb-plyr-tbody.cb-rank-hdr.cb-lv-main")

        for section in league_sections:
            try:
                # Extract league title
                league_title_element = section.find_element(By.CSS_SELECTOR, "h2")
                league_title = league_title_element.text.strip()
                
                # ✅ Only process IPL matches
                if "premier league" not in league_title.lower():
                    continue

                # Get match blocks within this section
                match_blocks = section.find_elements(By.CSS_SELECTOR, "div.cb-mtch-lst.cb-col.cb-col-100.cb-tms-itm")

                for block in match_blocks:
                    try:
                        a_tag = block.find_element(By.CSS_SELECTOR, "h3.cb-lv-scr-mtch-hdr.inline-block a")
                        match_link = a_tag.get_attribute("href")
                        match_title = a_tag.get_attribute("title")

                        details_div = block.find_element(By.CSS_SELECTOR, "div.text-gray")
                        details_text = details_div.text

                        today_tag = "Today" if "Today" in details_text else ""

                        parts = details_text.split("•")
                        match_time = parts[1].strip().split("at")[0].strip() if len(parts) > 1 else ""
                        stadium = details_text.split("at")[-1].strip() if "at" in details_text else ""

                        all_match_link_data.append({
                            "title": match_title,
                            "link": match_link,
                            "today": today_tag,
                            "time": match_time,
                            "stadium": stadium
                        })

                    except Exception as e:
                        print(f"Error parsing match block: {e}")
                        continue

            except Exception as e:
                print(f"Error parsing league section: {e}")
                continue

        driver.quit()
        return all_match_link_data
