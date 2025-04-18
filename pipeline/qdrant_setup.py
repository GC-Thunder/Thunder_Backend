import os
from langchain_core.documents import Document
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import OpenAI
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OpenAIEmbeddings  
from langchain.schema import Document
from tqdm import tqdm  # for progress bar
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_openai.embeddings import OpenAIEmbeddings
import qdrant_client
import pandas as pd
client = qdrant_client.QdrantClient("http://localhost:6333")
import numpy as np

import numpy as np
from historical_data_filtering import over_df, page_content0,metadata0,page_content1,metadata1,page_content2,metadata2
load_dotenv()  # this loads variables from .env

api_key = os.getenv("OPENAI_API_KEY")
#print("API Key:", api_key)



embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

client = QdrantClient("http://localhost:6333")

client.create_collection(
    collection_name="ipl",
    vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
)

vector_store = QdrantVectorStore(
    client=client,
    collection_name="ipl",
    embedding=embeddings,
)





def convert_metadata(meta):
    for k, v in meta.items():
        
        if isinstance(v, type({}.keys())):
            meta[k] = list(v)
        
        elif isinstance(v, (np.integer, np.floating, np.bool_)):
            meta[k] = v.item()
        
        elif isinstance(v, dict):
            meta[k] = convert_metadata(v)
    return meta






batch_size = 5000
batch = []

for content, meta in tqdm(zip(over_df["text"], over_df["metadata"]), total=len(over_df)):
    safe_meta = convert_metadata(meta)
    doc = Document(page_content=content, metadata=safe_meta)
    
    
    batch.append(doc)

    if len(batch) >= batch_size:
        vector_store.add_documents(batch)
        batch = []

# Insert remaining documents
if batch:
    vector_store.add_documents(batch)

for content, meta in tqdm(zip(page_content0,metadata0),total=len(metadata0)):
    safe_meta=convert_metadata(meta)
    doc=Document(page_content=content,metadata=safe_meta)
    batch.append(doc)
    if(len(batch)>=batch_size):
        vector_store.add_documents(batch)
        batch=[]

if batch:
    vector_store.add_documents(batch)

for content, meta in tqdm(zip(page_content1,metadata1),total=len(metadata1)):
    safe_meta=convert_metadata(meta)
    doc=Document(page_content=content,metadata=safe_meta)
    batch.append(doc)
    if(len(batch)>=batch_size):
        vector_store.add_documents(batch)
        batch=[]

if batch:
    vector_store.add_documents(batch)    

for content, meta in tqdm(zip(page_content2,metadata2),total=len(metadata2)):
    safe_meta=convert_metadata(meta)
    doc=Document(page_content=content,metadata=safe_meta)
    batch.append(doc)
    if(len(batch)>=batch_size):
        vector_store.add_documents(batch)
        batch=[]

if batch:
    vector_store.add_documents(batch) 

