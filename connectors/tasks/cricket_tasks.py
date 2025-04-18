import os 
import pytz
import time
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from connectors.tasks.celery import app
from celery import shared_task
from connectors.cd_connector import CDConnector
from connectors.utils.constants import IPL_SERIES_2025_URL
cd = CDConnector()

executor = ThreadPoolExecutor(max_workers=2)
seen_commentary_overs = set()
seen_overwise_summary_overs = set()

test_object = {
    "title": "Royal Challengers Bengaluru vs Punjab Kings",
    "link": "https://www.cricbuzz.com/live-cricket-scores/115174/rcb-vs-pbks-34th-match-indian-premier-league-2025",
    "today": "Today",
    "time": "7:30 PM",
    "stadium": "Bengaluru, M.Chinnaswamy Stadium"
}

def fetch_commentary(match_url):
    return cd.live_bbb_commentary(match_url)

def fetch_summary(match_url):
    return cd.live_overwise_summary(match_url)

def ensure_file(file_path):
    """Ensures file exists and returns its loaded data or an empty list."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(file_path, data):
    """Writes JSON data to the specified path."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

@shared_task(bind=True, soft_time_limit=14400, time_limit=15500)
def run_match_scraper(self, title: str, match_url: str):
    print(f"Starting async scraping: {title}")

    async def run_scraper():
        start_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        end_time = start_time + timedelta(hours=4)

        commentary_path = os.path.join('ipl', 'btb_commentary.json')
        summary_path = os.path.join('ipl', 'overwise_summary.json')

        commentary_store = ensure_file(commentary_path)
        summary_store = ensure_file(summary_path)

        while datetime.now(pytz.timezone('Asia/Kolkata')) < end_time:
            try:
                loop = asyncio.get_event_loop()

                # Run fetches in parallel
                commentary_future = loop.run_in_executor(executor, fetch_commentary, match_url)
                summary_future = loop.run_in_executor(executor, fetch_summary, match_url)

                commentary, summary = await asyncio.gather(commentary_future, summary_future)

                # Commentary
                new_commentary_entries = []
                for entry in commentary:
                    over = entry.get("over")
                    if over and over not in seen_commentary_overs:
                        new_commentary_entries.append(entry)
                        seen_commentary_overs.add(over)

                if new_commentary_entries:
                    print(f"[NEW COMMENTARY] {title}: {len(new_commentary_entries)} new entries")
                    commentary_store.extend(new_commentary_entries[::-1])
                    save_json(commentary_path, commentary_store)
                else:
                    print(f"[NO NEW COMMENTARY DATA] {title}")

                # Summary
                new_summary_entries = []
                for entry in summary:
                    over = entry.get("over")
                    if over and over not in seen_overwise_summary_overs:
                        new_summary_entries.append(entry)
                        seen_overwise_summary_overs.add(over)

                if new_summary_entries:
                    print(f"[NEW SUMMARY] {title}: {len(new_summary_entries)} new entries")
                    summary_store.extend(new_summary_entries.reverse())
                    save_json(summary_path, summary_store)
                else:
                    print(f"[NO NEW SUMMARY DATA] {title}")

            except Exception as e:
                print(f"Error in scraping loop: {e}")

            await asyncio.sleep(60)

    # Run the async loop and handle retry
    try:
        asyncio.run(run_scraper())
    except Exception as e:
        print(f"Fatal error in task: {e}")
        self.retry(countdown=60, exc=e, max_retries=3)


@app.task
def schedule_today_table():
    try:
        table_point_data = cd.load_point_table(IPL_SERIES_2025_URL)
        
        os.makedirs('ipl', exist_ok=True)
        
        file_path = os.path.join('ipl', 'table.json')
        
        with open(file_path, 'w') as f:
            json.dump(table_point_data, f, indent=4)

        print(f"Table data written to {file_path}")
        return "Point table data saved successfully."
    
    except Exception as e:
        print(f"Error in schedule_today_table: {e}")
        return f"Failed due to: {str(e)}"

@app.task
def schedule_today_mvp():
    print("🏅 Calculating MVP of the day...")
    # Logic for MVP computation
    return "MVP calculated."

@app.task
def schedule_today_scorecard():
    try:        
        scorecard_data = cd.load_match_scorecard(IPL_SERIES_2025_URL)
        os.makedirs('ipl', exist_ok=True)
        
        file_path = os.path.join('ipl', 'scorecard.json')
        
        with open(file_path, 'w') as f:
            json.dump(scorecard_data, f, indent=4)
        
        print(f"Scorecard data written to {file_path}")

        return "Scorecard data saved successfully."

    except Exception as e:
        print(f"Error in schedule_today_scorecard: {e}")
        return f"Failed due to: {str(e)}"

@app.task
def schedule_today_btb():
    try:
        live_matches = cd.live_match_links()
        l = len(live_matches)
        print(f"🔗 Found {l} live matches")

        json_files = cd.btb_innings(l)
        print(f"📄 Received {len(json_files)} BTB innings JSONs")

        # Make sure base directory exists
        base_dir = 'ipl'
        os.makedirs(base_dir, exist_ok=True)

        # Write each JSON to a separate file
        for i, json_data in enumerate(json_files, 1):
            file_path = os.path.join(base_dir, f'btb_{i}.json')
            with open(file_path, 'w') as f:
                json.dump(json_data, f, indent=4)
            print(f"Written BTB data to {file_path}")

        return f"{len(json_files)} BTB JSON files written."

    except Exception as e:
        print(f" Error in schedule_today_btb: {e}")
        return f"Failed due to: {str(e)}"

@app.task
def schedule_today_matches():
    matches = cd.live_match_links()
    now = datetime.now(pytz.timezone('Asia/Kolkata'))

    for match in matches:
        if not match["today"]:
            continue

        title = match["title"]
        match_time_str = match["time"]  # e.g., "7:30 PM"
        match_url = match["link"]

        try:
            match_time_obj = datetime.strptime(match_time_str, "%I:%M %p").time()
            match_datetime = datetime.combine(now.date(), match_time_obj).replace(tzinfo=now.tzinfo)

            if match_datetime < now:
                continue

            delay = (match_datetime - now).total_seconds()
            run_match_scraper.apply_async(args=[title, match_url], countdown=delay)

            print(f"Scheduled '{title}' at {match_datetime.strftime('%I:%M %p')}")
        except Exception as e:
            print(f"Failed to schedule {title}: {e}")

@app.task
def test_task():
    test_object = {
        "title": "Royal Challengers Bengaluru vs Punjab Kings",
        "link": "https://www.cricbuzz.com/live-cricket-scores/115174/rcb-vs-pbks-34th-match-indian-premier-league-2025",
        "today": "Today",
        "time": "7:30 PM",
        "stadium": "Bengaluru, M.Chinnaswamy Stadium"
    }

    file_path = "ipl/test_matches.json"

    # Check if file exists and load existing list
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    data = []
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Append the new object and write it back
    for _ in range(5):
        data.append(test_object)

    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

    print(f"[TEST TASK] Match info written to {file_path}")


