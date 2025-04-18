import json
import pandas as pd
import os
import getpass
import os

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("OPENAI_API_KEY")

from langchain_openai.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
  
# THE OVER SUMMARIES FOR EACH IPL MATCH

def load_json_folder_to_dataframe(folder_path):
    data = []
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    content = json.load(f)
                    data.append(content)
                except json.JSONDecodeError:
                    print(f"Error decoding {file_path}")

    return data


folder_path = r'pipeline/retriever/data/ipl_json'
data = load_json_folder_to_dataframe(folder_path)




rows = []

for match in data:
    match_information= match.get("info", {})
    date=match_information.get("dates","NULL")
    teams= match_information.get("teams", [])
    venue= match_information.get("venue", "NULL")
    winner= match_information.get("outcome", "NULL")
    winner=winner.get("winner", "NULL")

    for innings_index,innings in enumerate(match["innings"],start=1):
        team=innings["team"]
        for over_data in innings["overs"]:
            over_number=over_data["over"]
            for ball_index,delivery in enumerate(over_data["deliveries"]):
                row = {
                    "teams":f"{teams[0]} vs {teams[1]}",
                    "date": date,
                    "venue": venue,
                    "winner": winner,
                    "inning": innings_index,
                    "team": team,
                    "over": over_number,
                    "ball": ball_index + 1,
                    "batsman": delivery.get("batter"),
                    "non_striker": delivery.get("non_striker"),
                    "bowler": delivery.get("bowler"),
                    "runs_batter": delivery.get("runs", {}).get("batter", 0),
                    "runs_extras": delivery.get("runs", {}).get("extras", 0),
                    "runs_total": delivery.get("runs", {}).get("total", 0),
                    "wickets":1 if delivery.get("wickets") else 0,
                    

                    "wicket_type": delivery.get("wickets", [{}])[0].get("kind") if "wickets" in delivery else None,
                    "player_out": delivery.get("wickets", [{}])[0].get("player_out") if "wickets" in delivery else None,
                    "match_winner": winner
                }
                rows.append(row)



'''
for innings_index, inning in enumerate(data["innings"], start=1):
    team = inning["team"]
    
    for over_data in inning["overs"]:
        over_number = over_data["over"]
        
        for ball_index, delivery in enumerate(over_data["deliveries"]):
            row = {
                "match_id": data.get("meta", {}).get("match_id", "335982"),
                "inning": innings_index,
                "team": team,
                "over": over_number,
                "ball": ball_index + 1,
                "batsman": delivery.get("batter"),
                "non_striker": delivery.get("non_striker"),
                "bowler": delivery.get("bowler"),
                "runs_batter": delivery.get("runs", {}).get("batter", 0),
                "runs_extras": delivery.get("runs", {}).get("extras", 0),
                "runs_total": delivery.get("runs", {}).get("total", 0),
                

                "wicket_type": delivery.get("wickets", [{}])[0].get("kind") if "wickets" in delivery else None,
                "player_out": delivery.get("wickets", [{}])[0].get("player_out") if "wickets" in delivery else None
            }
            rows.append(row)

'''

df = pd.DataFrame(rows)

#print(df.head())

from datetime import datetime

def convert_date_str_to_unix(date_str: str) -> int:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return int(dt.timestamp())


df["over_id"] = df["date"].astype(str) + "_" +df["teams"]+"_" +df["inning"].astype(str) + "_" + df["over"].astype(str)


grouped = df.groupby("over_id")


over_summaries = []

for over_id, group in grouped:
    
    date= group["date"].iloc[0]
    match_winner = group["match_winner"].iloc[0]
    venue = group["venue"].iloc[0]
    teams = group["teams"].iloc[0]
    inning = group["inning"].iloc[0]
    over = group["over"].iloc[0]+1
    team = group["team"].iloc[0]
    bowler = group["bowler"].iloc[0]
    total_runs = group["runs_total"].sum()
    wickets = group["wicket_type"].notna().sum()
    sixes = (group["runs_batter"] == 6).sum()
    fours = (group["runs_batter"] == 4).sum()
    extras = group["runs_extras"].sum()
    
    

    
    batter_runs = group.groupby("batsman")["runs_batter"].sum().to_dict()

    
    batter_fours_count = group[group["runs_batter"] == 4].groupby("batsman").size().to_dict()
    batter_sixes_count = group[group["runs_batter"] == 6].groupby("batsman").size().to_dict()

    batter_text = ', '.join([
    f"{b}: {batter_runs[b]} run(s), {batter_fours_count.get(b, 0)} four(s), {batter_sixes_count.get(b, 0)} six(es)"
    for b in batter_runs
    ] )
    bowler_wicket_counts = group[group["wicket_type"].notna()].groupby("bowler").size().to_dict()
    bowler_text = ', '.join([f"{b}: {w} wicket(s)" for b, w in bowler_wicket_counts.items()])


    text = (
        f"date {date},between {teams}, played at {venue} , Inning {inning}, Over {over} by {bowler} to {', '.join(batter_runs.keys())}: "
        f"{total_runs} total runs, {wickets} wicket(s), {fours} four(s), {sixes} six(es), {extras} extras. "
        f"Runs per batter - {batter_text} , wickets by bowler - {bowler_text} , {match_winner} emerged as the winner of this match."
    )

    
    over_summaries.append({
        "id": over_id,
        "text": text,
        "metadata": {
            "date": convert_date_str_to_unix(date[0]),
            "teams": teams,
            "match_winner": match_winner,
            "venue": venue,
            "inning": inning,
            "over": over,
            "team": team,
            "batsmen": (batter_runs.keys()),
            "batter_sixes_count": batter_sixes_count,
            "batter_fours_count": batter_fours_count,
            "bowler_wickets": bowler_wicket_counts,

            "batter_runs": batter_runs, 
            "bowler": bowler,
            "total_runs": total_runs,
            "wickets": wickets,
            "fours": fours,
            "sixes": sixes,
            "over_score": total_runs,
            "extras":extras  
        }
    })


over_df = pd.DataFrame(over_summaries)

# FOR SCORECARDS OF EACH IPL MATCH


import os
import json

def read_scorecards(root_folder):
    scorecards = []

    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file == "scorecard.json":
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        scorecards.append(data)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return scorecards

# Usage
folder_path = r"pipeline/retriever/data/ipl"  # Replace with your actual path
all_scorecards = read_scorecards(folder_path)

import pandas as pd
import re

from datetime import datetime

def convert_to_iso(date_str):
    try:
        dt = datetime.strptime(date_str, "%d %B %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def extract_date(text):
    match = re.match(r"(\d{1,2} \w+ \d{4})", text)
    if match:
        return match.group(1)
    else:
        return None


page_content0 = []
metadata0 = []

for all_scorecard in all_scorecards:
    for match in all_scorecard:
        details = match['scorecard']['match_details']
        venue = details.get('Stadium name', '')
        date = extract_date(details.get('Match days', ''))
        teams = details.get('Points', '')

        for inning in match['scorecard']['innings']:
            for player in inning["Batting"]:
                
                content = f"Batsman: { player['Player']}, Runs: {player['Runs']}, Balls: {player['Balls']}, Fours: {player['4s']}, Sixes: {player['6s']}, Strike Rate: {player['SR']}, Dismissal: {player['Dismissal']} on {date} at {venue} between {teams}."
                
                
                metadata_entry = {
                    "batsmen": player["Player"],
                    "runs": int(player["Runs"]) if player["Runs"] != "-" else 0,
                    "balls": int(player["Balls"]) if player["Balls"] != "-" else 0,
                    "fours": int(player["4s"]) if player["4s"] != "-" else 0,
                    "sixes": int(player["6s"]) if player["6s"] != "-" else 0,
                    "strike_rate": float(player["SR"]) if player["SR"] != "-" else 0.0,
                    "dismissal": player["Dismissal"],
                    "venue": venue,
                    "date": date,
                    "teams": teams,
                }
                
                page_content0.append(content)
                metadata0.append(metadata_entry)

            
            extras_content = f"Extras: {inning['Extras']['total']}, Total Runs: {inning['Total']['score']}"
            extras_metadata = {
                "extras": int(inning["Extras"]["total"]),
                "total_runs": int(inning["Total"]["score"].split("/")[0]) if inning["Total"]["score"] else 0,
                "venue": venue,
                "date": date,
                "teams": teams,
            }

            page_content0.append(extras_content)
            metadata0.append(extras_metadata)

            for player in inning["Bowling"]:
                bowling_content = f"Bowler: {player['Bowler']}, Overs: {player['Overs']}, Runs: {player['Runs']}, Wickets: {player['Wickets']}, Economy: {player['Econ']}, Maidens: {player['Maidens']}, 4s: {player['4s']}, 6s: {player['6s']}, Wides: {player['WD']}, No Balls: {player['NB']}, Dots: {player['Dots']}"
                
                bowling_metadata = {
                    "bowler": player["Bowler"],
                    "overs": float(player["Overs"]),
                    "runs_conceded": int(player["Runs"]),
                    "wickets": int(player["Wickets"]),
                    "economy": float(player["Econ"]),
                    "maiden": int(player["Maidens"]),
                    "fours_conceded": int(player["4s"]),
                    "sixes_conceded": int(player["6s"]),
                    "wides": int(player["WD"]),
                    "no_balls": int(player["NB"]),
                    "dot": int(player["Dots"]),
                    "venue": venue,
                    "date": date,
                    "teams": teams,
                }
            page_content0.append(bowling_content)
            metadata0.append(bowling_metadata)

                

# F1 RACE DATA LOADING

def load_json_folder_to_dataframe(folder_path):
    data = []
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    content = json.load(f)
                    data.append(content)
                except json.JSONDecodeError:
                    print(f"Error decoding {file_path}")

    return data


folder_path = r'pipeline/retriever/data/f1_race_results'
data = load_json_folder_to_dataframe(folder_path)

page_content1=[]
metadata1=[]
for data in data:
    for comp in data:
        race=comp["Race"]
        for points in comp["Results"]:
            content = f"In the race {race} the driver {points['Driver']} from {points['Country']} representing {points['Team']} had won the {points['Position']} position completing the race in {points['Absolute Race Time (s)']} seconds"

            row1={
                "position":points["Position"],
                "driver":points["Driver"],
                "country":points["Country"],
                "team":points["Team"],
                "race_time":points["Absolute Race Time (s)"],
                "race":race

            }
            page_content1.append(content)
            metadata1.append(row1)



# IPL TEAM SQUAD DATA OF ALL THE YEARS

def read_squads(root_folder):
    squads = []

    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file == "squads.json":
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        squads.append(data)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return squads


folder_path = r"pipeline/retriever/data/ipl"  
all_squads = read_squads(folder_path)

page_content2=[]
metadata2=[]
row={}
for teams in all_squads:
    for team in teams:
        team_name = team["name"]
        year = team["year"]
        players = team["players"]
        content=f"In the year {year}, the team {team_name} had the following players: "
        row={
            "team_name":team_name,
            "year":year,
            "squad":" "
        }
        for player in team["players"]:
            if(player['role']):
                t=f"{ player['title']}  ({player['role']}), "
                content+=f"{ player['title']} who plays as {player['role']}, "
                row["squad"]+=t
            
            
        page_content2.append(content)
        metadata2.append(row)






