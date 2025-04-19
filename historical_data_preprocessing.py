import os
import json
import pandas as pd
from datetime import datetime
from langchain_core.documents import Document
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import OpenAI
from langchain_community.vectorstores import Qdrant
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from tqdm import tqdm
import getpass
from langchain_openai.embeddings import OpenAIEmbeddings

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("OPENAI_API_KEY")



embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
  



class create_collection:
    def __init__(self,collection_name:str,url, vector_size:int=3072)->None:
        self.client = QdrantClient(url)
        self.collection_name = collection_name
        self.vector_size = vector_size
        
    def create_collection(self):
        self.client.create_collection(
        collection_name=self.collection_name,
        vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
        )


class IPLOverDataProcessor:
    def __init__(self, folder_path: str,url:str,collection_name:str):
        self.collection_name = collection_name
        self.folder_path = folder_path
        self.data = []
        self.df = pd.DataFrame()
        self.over_df1 = pd.DataFrame()
        self.url=url
        self.vector_store = None

    def load_json_files(self):
        for filename in os.listdir(self.folder_path):
            if filename.endswith('.json'):
                file_path = os.path.join(self.folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        content = json.load(f)
                        self.data.append(content)
                    except json.JSONDecodeError:
                        print(f"Error decoding {file_path}")

    

    def parse_ball_data(self):
        rows = []
        for match in self.data:
            info = match.get("info", {})
            date = info.get("dates", ["NULL"])[0]
            teams = info.get("teams", [])
            venue = info.get("venue", "NULL")
            winner = info.get("outcome", {}).get("winner", "NULL")

            for innings_index, innings in enumerate(match["innings"], start=1):
                team = innings["team"]
                for over_data in innings["overs"]:
                    over_number = over_data["over"]
                    for ball_index, delivery in enumerate(over_data["deliveries"]):
                        row = {
                            "teams": f"{teams[0]} vs {teams[1]}",
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
                            "wickets": 1 if delivery.get("wickets") else 0,
                            "wicket_type": delivery.get("wickets", [{}])[0].get("kind") if "wickets" in delivery else None,
                            "player_out": delivery.get("wickets", [{}])[0].get("player_out") if "wickets" in delivery else None,
                            "match_winner": winner
                        }
                        rows.append(row)

        self.df = pd.DataFrame(rows)

    

    def generate_over_summaries(self):
        self.df["over_id"] = self.df["date"].astype(str) + "_" + self.df["teams"] + "_" + \
                             self.df["inning"].astype(str) + "_" + self.df["over"].astype(str)

        grouped = self.df.groupby("over_id")
        summaries = []

        for over_id, group in grouped:
            date = group["date"].iloc[0]
            match_winner = group["match_winner"].iloc[0]
            venue = group["venue"].iloc[0]
            teams = group["teams"].iloc[0]
            inning = group["inning"].iloc[0]
            over = group["over"].iloc[0] + 1
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
            bowler_wicket_counts = group[group["wicket_type"].notna()].groupby("bowler").size().to_dict()

            batter_text = ', '.join([
                f"{b}: {batter_runs[b]} run(s), {batter_fours_count.get(b, 0)} four(s), {batter_sixes_count.get(b, 0)} six(es)"
                for b in batter_runs
            ])
            bowler_text = ', '.join([f"{b}: {w} wicket(s)" for b, w in bowler_wicket_counts.items()])

            text = (
                f"date {date}, between {teams}, played at {venue}, Inning {inning}, Over {over} by {bowler} to {', '.join(batter_runs.keys())}: "
                f"{total_runs} total runs, {wickets} wicket(s), {fours} four(s), {sixes} six(es), {extras} extras. "
                f"Runs per batter - {batter_text}, wickets by bowler - {bowler_text}, {match_winner} emerged as the winner of this match."
            )

            summaries.append({
                "id": over_id,
                "text": text,
                "metadata": {
                    "date": date,
                    "teams": teams,
                    "match_winner": match_winner,
                    "venue": venue,
                    "inning": inning,
                    "over": over,
                    "team": team,
                    "batsmen": list(batter_runs.keys()),
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
                    "extras": extras
                }
            })

        self.over_df = pd.DataFrame(summaries)

    
    def convert_metadata(self,meta):
        import numpy as np
        for k, v in meta.items():
            if isinstance(v, type({}.keys())):
                meta[k] = list(v)
        
            elif isinstance(v, (np.integer, np.floating, np.bool_)):
                meta[k] = v.item()
        
            elif isinstance(v, dict):
                meta[k] = self.convert_metadata(v)
        
        
        return meta
    

    def push_to_qdrant(self,):
        client = QdrantClient(self.url)
        self.vector_store = QdrantVectorStore(
        client=client,
        collection_name=self.collection_name,
        embedding=embeddings,
        )
        batch_size = 1000
        batch = []

        for content, meta in tqdm(zip(self.over_df["text"], self.over_df["metadata"]), total=len(self.over_df)):
            safe_meta = self.convert_metadata(meta)
            doc = Document(page_content=content, metadata=safe_meta)
            
    
            batch.append(doc)

            if len(batch) >= batch_size:
                self.vector_store.add_documents(batch)
                batch = []

        
        if batch:
            self.vector_store.add_documents(batch)



    def run_pipeline(self) -> pd.DataFrame:
        self.load_json_files()
        self.parse_ball_data()
        self.generate_over_summaries()
        self.push_to_qdrant()
        print("Pushed to Qdrant successfully")






# FOR SCORECARDS OF EACH IPL MATCH
class IPLScorecardProcesser:
    def __init__(self,folder_path:str):
        self.folder_path = folder_path
        self.all_scorecards = []
        self.page_content0 = []
        self.metadata0 = []
        self.all_squads = []

    def json_to_dataframe(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file == "scorecard.json":
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)
                            self.scorecards.append(data)
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")

    def convert_to_iso(self,date_str):
        try:
            dt = datetime.strptime(date_str, "%d %B %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None
        
    def extract_date(self,text):
        import re
        match = re.match(r"(\d{1,2} \w+ \d{4})", text)
        if match:
            return match.group(1)
        else:
            return None
    
    def generate_match_summaries(self):
        for all_scorecard in self.all_scorecards:
            for match in all_scorecard:
                details = match['scorecard']['match_details']
                venue = details.get('Stadium name', '')
                date1 = self.extract_date(details.get('Match days', ''))
                date= self.convert_to_iso(date1)
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
                
                        self.page_content0.append(content)
                        self.metadata0.append(metadata_entry)

            
                    extras_content = f"Extras: {inning['Extras']['total']}, Total Runs: {inning['Total']['score']}"
                    extras_metadata = {
                        "extras": int(inning["Extras"]["total"]),
                        "total_runs": int(inning["Total"]["score"].split("/")[0]) if inning["Total"]["score"] else 0,
                        "venue": venue,
                        "date": date,
                        "teams": teams,
                    }

                    self.page_content0.append(extras_content)
                    self.metadata0.append(extras_metadata)

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
                    self.page_content0.append(bowling_content)
                    self.metadata0.append(bowling_metadata)
    def convert_metadata(self,meta):
        import numpy as np
        for k, v in meta.items():
            if isinstance(v, type({}.keys())):
                meta[k] = list(v)
        
            elif isinstance(v, (np.integer, np.floating, np.bool_)):
                meta[k] = v.item()
        
            elif isinstance(v, dict):
                meta[k] = self.convert_metadata(v)
        
        
        return meta  
    def push_to_qdrant(self, collection_name: str,url):
        client = QdrantClient(url)
        self.vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
        )
        batch_size = 1000
        batch = []

        for content, meta in tqdm(zip(self.page_content0, self.metadata0), total=len(self.page_content0)):
            safe_meta = self.convert_metadata(meta)
            doc = Document(page_content=content, metadata=safe_meta)
            
    
            batch.append(doc)

            if len(batch) >= batch_size:
                self.vector_store.add_documents(batch)
                batch = []

        
        if batch:
            self.vector_store.add_documents(batch)   
    def run_pipeline(self) -> pd.DataFrame:
        self.json_to_dataframe()
        self.generate_match_summaries()
        
        self.push_to_qdrant()
        print("Pushed to Qdrant successfully")










class F1RaceDataProcessor:
    def __init__(self, folder_path: str,collection_name:str,url:str):
        self.collection_name = collection_name
        self.url=url
        self.folder_path = folder_path
        self.data = []
        self.page_content1 = []
        self.metadata1 = []

    def load_json_files(self):
        for filename in os.listdir(self.folder_path):
            if filename.endswith('.json'):
                file_path = os.path.join(self.folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        content = json.load(f)
                        self.data.append(content)
                    except json.JSONDecodeError:
                        print(f"Error decoding {file_path}")
    def json_to_dataframe(self):
        for data in self.data:
            for comp in data:
                race=comp["Race"]
                for points in comp["Results"]:
                    content=f"In the race {race} the driver {points["Driver"]} from {points["Country"]} representing {points["Team"]} had won the {points["Position"]} position completing the race in {points["Absolute Race Time (s)"]} seconds"
                    row1={
                        "position":points["Position"],
                        "driver":points["Driver"],
                        "country":points["Country"],
                        "team":points["Team"],
                        "race_time":points["Absolute Race Time (s)"],
                        "race":race

                    }
                    self.page_content1.append(content)
                    self.metadata1.append(row1)

    def convert_metadata(self,meta):
        import numpy as np
        for k, v in meta.items():
            if isinstance(v, type({}.keys())):
                meta[k] = list(v)
        
            elif isinstance(v, (np.integer, np.floating, np.bool_)):
                meta[k] = v.item()
        
            elif isinstance(v, dict):
                meta[k] = self.convert_metadata(v)
        
        
        return meta
    
    def push_to_qdrant(self):
        client = QdrantClient(self.url)
        self.vector_store = QdrantVectorStore(
        client=client,
        collection_name=self.collection_name,
        embedding=embeddings,
        )
        batch_size = 1000
        batch = []

        for content, meta in tqdm(zip(self.page_content1, self.metadata1), total=len(self.page_content1)):
            safe_meta = self.convert_metadata(meta)
            doc = Document(page_content=content, metadata=safe_meta)
            
    
            batch.append(doc)

            if len(batch) >= batch_size:
                self.vector_store.add_documents(batch)
                batch = []

        
        if batch:
            self.vector_store.add_documents(batch)
    
    
    def run_pipeline(self)->pd.DataFrame:
        self.load_json_files()
        self.json_to_dataframe()
        self.push_to_qdrant()
        print("Pushed to Qdrant successfully")






class IPLSquads():
    def __init__(self, folder_path: str,url:str,collection_name:str):
        self.collection_name = collection_name
        self.url=url
        self.folder_path = folder_path
        self.all_squads = []
        self.page_content2 = []
        self.metadata2 = []

    def load_json_files(self):
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file == "squads.json":
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)
                            self.all_squads.append(data)
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
    
    def convert_metadata(self,meta):
        import numpy as np
        for k, v in meta.items():
            if isinstance(v, type({}.keys())):
                meta[k] = list(v)
        
            elif isinstance(v, (np.integer, np.floating, np.bool_)):
                meta[k] = v.item()
        
            elif isinstance(v, dict):
                meta[k] = self.convert_metadata(v)
        
        
        return meta
    def generate_squad_details(self):
        for teams in self.all_squads:
            for team in teams:
                team_name = team["name"]
                year = team["year"]
               
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
            
            
                self.page_content2.append(content)
                self.metadata2.append(row)

    def push_to_qdrant(self):
        client = QdrantClient(self.url)
        self.vector_store = QdrantVectorStore(
        client=client,
        collection_name=self.collection_name,
        embedding=embeddings,
        )
        batch_size = 1000
        batch = []

        for content, meta in tqdm(zip(self.page_content2, self.metadata2), total=len(self.page_content2)):
            safe_meta = self.convert_metadata(meta)
            doc = Document(page_content=content, metadata=safe_meta)
            
    
            batch.append(doc)

            if len(batch) >= batch_size:
                self.vector_store.add_documents(batch)
                batch = []

        
        if batch:
            self.vector_store.add_documents(batch)   
    
    def run_pipeline(self) -> pd.DataFrame:
        self.load_json_files()
        self.generate_squad_details()
        self.push_to_qdrant()
        print("Pushed to Qdrant successfully")




''' create a collection first before creating other instancess of the classes'''
















