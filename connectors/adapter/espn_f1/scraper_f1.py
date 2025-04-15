from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import json


def fetch_f1_race_data(year=None):
    if year is None:
        year = datetime.utcnow().year

    def time_str_to_seconds(t_str):
        parts = t_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(parts[0])

    def get_driver():
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-proxy-server')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        return webdriver.Chrome(options=options)

    def wait_for_element(driver, by, value, timeout=15):
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))

    driver = get_driver()

    # Step 1: Get race URLs
    schedule_url = f"https://www.espn.in/f1/schedule/_/year/{year}"
    driver.get(schedule_url)
    wait_for_element(driver, By.CSS_SELECTOR, "a.AnchorLink")

    race_links = set()
    for link in driver.find_elements(By.CSS_SELECTOR, "a.AnchorLink"):
        href = link.get_attribute("href")
        if href and "/race/_/id/" in href:
            clean_href = href.replace("/race/", "/results/")
            race_links.add(clean_href)

    race_links = list(race_links)
    print(f"📥 Found {len(race_links)} unique races for {year}")

    all_race_data = []

    # Step 2: Visit each race page
    for url in race_links:
        print(f"\n📥 Scraping: {url}")
        try:
            driver.get(url)

            try:
                wait_for_element(driver, By.CSS_SELECTOR, 'table.Table')
            except:
                print("⚠️ No result table found — skipping")
                continue

            race_name = driver.title.split(" - ")[0].strip()
            rows = driver.find_elements(By.CSS_SELECTOR, 'tr.Table__TR')

            if not rows:
                print("⚠️ No table rows found — skipping")
                continue

            base_time = None
            race_results = []

            for row in rows:
                try:
                    columns = row.find_elements(By.TAG_NAME, "td")
                    if len(columns) < 7:
                        continue

                    pos = columns[0].text.strip()
                    try:
                        country = columns[1].find_element(By.TAG_NAME, "img").get_attribute("alt").strip()
                    except:
                        country = "Unknown"

                    try:
                        driver_name = columns[1].find_element(By.CLASS_NAME, "hide-mobile").text.strip()
                    except:
                        driver_name = columns[1].text.strip()

                    team = columns[2].text.strip()
                    race_time_raw = columns[3].text.strip()
                    fastest_lap = columns[6].text.strip()

                    absolute_time = ""

                    if pos == "1":
                        base_time = time_str_to_seconds(race_time_raw)
                        absolute_time = base_time
                    elif race_time_raw.startswith("+") and "Lap" not in race_time_raw:
                        delta = race_time_raw.replace("+", "")
                        delta = time_str_to_seconds(delta) if ":" in delta else float(delta)
                        absolute_time = round(base_time + float(delta), 3)
                    else:
                        continue

                    race_results.append({
                        "Position": pos,
                        "Driver": driver_name,
                        "Country": country,
                        "Team": team,
                        "Race Time": race_time_raw,
                        "Absolute Race Time (s)": absolute_time,
                        "Fastest Lap": fastest_lap
                    })

                except Exception as row_err:
                    print(f"❌ Skipped row due to: {row_err}")
                    continue

            if not race_results:
                print("⚠️ No valid results parsed — skipping race")
                continue

            all_race_data.append({
                "Race": race_name,
                "URL": url,
                "Results": race_results
            })

        except Exception as e:
            print(f"❌ Failed to scrape {url} due to: {e}")
            continue

    driver.quit()

    # Step 3: Save to JSON
    final_output = {
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "year": year,
        "races": all_race_data
    }

    json_filename = f"f1_race_results_{year}.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print(f"\n✅ Saved {len(all_race_data)} races to '{json_filename}'")
    return final_output
