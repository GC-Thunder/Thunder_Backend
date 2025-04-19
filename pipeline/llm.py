import os
import json
import re
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAI
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
#from qdrant_setup import vector_store  # Assumes you have this ready
from openai import OpenAI as OpenAIClient

load_dotenv()

client = QdrantClient("http://localhost:6333")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

vector_store = QdrantVectorStore(
    client=client,
    collection_name="ipl",
    embedding=embeddings,
)

class SportsChatbot:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = OpenAI(temperature=0)
        self.client = OpenAIClient(api_key=self.api_key)
        #self.memory=[]

        self.document_content_description = "a brief description of ipl and the formula 1 racing data."
        self.metadata_field_info = [
            AttributeInfo(name="batsmen", description="names of batsmen who played in the over.", type="list[string]"),
            AttributeInfo(name="bowler", description="The bowler who bowled the delivery.", type="string"),
            AttributeInfo(name="over", description="The over number.", type="integer"),
            AttributeInfo(name="inning", description="The inning number.", type="integer"),
            AttributeInfo(name="date", description="The date of the match.", type="string"),
            AttributeInfo(name="teams", description="The teams playing in the match.", type="string"),
            AttributeInfo(name="venue", description="The venue of the match.", type="string"),
            AttributeInfo(name="match_winner", description="The winner of the match.", type="string"),
            AttributeInfo(name="Driver", description="the driver of the car", type="string"),
            AttributeInfo(name="team", description="the team the driver and the car belonged to", type="string"),
            AttributeInfo(name="year", description="the year the respective ipl edition took place", type="integer"),
            AttributeInfo(name="country", description="the country of the driving team", type="string")
        ]

        self.retriever = SelfQueryRetriever.from_llm(
            self.llm,
            vector_store,
            self.document_content_description,
            self.metadata_field_info,
            verbose=True,
            enable_limit=True
        )

    def prompt_generator(self, user_prompt: str) -> str:
        system_prompt = """You are a helpful assistant that converts user IPL cricket questions into a structured prompt for a SelfQueryRetriever.
Your output must be a JSON with:
"query": A concise version of the user query
"filter": A dictionary that includes "must": a list of filter conditions in Qdrant-compatible format
Each filter should look like: { "key": "<field>", "match": { "value": "<value>" } } Or for ranges: { "key": "<field>", "range": { "gte": 6 } }
Available fields: batsman, bowler, over, inning, match_id, teams, date, venue, runs_batter, runs_extras, runs_total, wickets, extras, over_score, match_winner
Powerplay is said to be the first 6 overs of the innings, so set the range accordingly.
Do not include any other information or explanations in your response.
Important: Do not add or infer details that are not explicitly mentioned in the user query.
if any date is involved in the query, convert it to unix timestamp and use it in the filter as range . for example if given in the year 2023 it means the range is 2023-01-01 to 2023-12-31.
"""
        response = self.client.responses.create(
            model="gpt-4o",
            instructions=system_prompt,
            input=user_prompt,
        )
        raw_output = response.output_text
        json_str = re.sub(r"```json|```", "", raw_output).strip()
        return json.loads(json_str)
    

            
        

    def answer_query(self, user_prompt: str) -> str:
        # Use retriever
        documents = self.retriever.get_relevant_documents(user_prompt)

        # Format system prompt for response generation
        system_prompt = f'''You are a chat bot that helps users improve their sports viewing experience. From the given retrieved data, answer the query in a descriptive way which should contain the answer to the question and be engaging.
        also remember that you shoud give only the relevent information that you got from the retrieval. . 
Original query: "{user_prompt}"
Answer the question by carefully going through the input data.
'''
        


        
        response = self.client.responses.create(
            model="gpt-4o",
            instructions=system_prompt,
            input=f"Input data: {documents}",
            )
        return response.output_text

        
    

    

'''chatbot = SportsChatbot()
result = chatbot.answer_query("how many races were won by team ferrari in total , give 20 records")

print(result)'''