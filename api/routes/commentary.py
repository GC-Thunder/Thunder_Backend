from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from openai import OpenAI
import json
from typing import AsyncGenerator
from pydantic import BaseModel, Field
from typing import Literal
from loguru import logger
from pydantic import BaseModel, Field
from typing import Type
import asyncio
from pipeline.llm import SportsChatbot
import time
import redis.asyncio as redis


REDIS_URL = "redis://localhost:6379/0"

router = APIRouter()
client = OpenAI()

class IntentSchema(BaseModel):
    live_commentary: Literal["yes", "no"]
    message: str

class UserIntentionJson():
    def __init__(self, model:str = "gpt-4o"):
        self.model = model
        
    def get_structured_intention_response(
        self, 
        system_prompt: str, 
        user_input: str, 
        schema: Type[BaseModel]
    ) -> dict:
        try:
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": system_prompt}]
                    },
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_input}]
                    }
                ],
                response_format=schema
            )
            structured_output = response.choices[0].message.parsed
            return structured_output.model_dump()

        except Exception as e:
            logger.error(f"Failed to get structured response: {e}")
            return {}

    
chatbot_prompt = """
    You are an assistant whose only task is to detect whether the user is asking for live IPL commentary for the following match:

    Match Details:
    {
    "live_commentary": "yes",
    "message": "The IPL clash between Royal Challengers Bengaluru and Punjab Kings kicks off today at 7:30 PM IST at the iconic M.Chinnaswamy Stadium in Bengaluru. Stay tuned for ball-by-ball commentary once the match begins—you can follow live updates at the provided link."
    }

    If the user's input is related to IPL but outside live commentary windows (e.g. asking for past scores or schedules), respond with exactly:

    {
    "live_commentary": "no",
    "message": "The IPL match is scheduled at 7:30 PM today at Bengaluru, M.Chinnaswamy Stadium. Live commentary will be available only during match hours."
    }

    If the user's input is completely unrelated to IPL live commentary, respond with exactly:

    {
    "live_commentary": "no",
    "message": "Only live commentary of IPL is provided."
    }

    """

class IntentSchema(BaseModel):
    live_commentary: Literal["yes", "no"]
    message: str

async def classify_intent(text: str) -> bool:
    """
    Very simple stub: in prod swap out for your real intent‐classifier/RAG
    """
    user_intention = UserIntentionJson()
    response_data = user_intention.get_structured_intention_response(chatbot_prompt, text, IntentSchema)
    if response_data.get("live_commentary") == "yes":
        return True
    return False
    

async def stream_raw_model(user_query: str) -> AsyncGenerator[str, None]:
    chat_bot=  SportsChatbot()
    time.sleep(3)
    print('user query',user_query)
    message = chat_bot.answer_query(user_query)
    print(message)

    response_id = f"resp_{hash(user_query)}"
    created_event = {
        "type": "response.created",
        "response": {
            "id": response_id
        }
    }
    yield f"data: {json.dumps(created_event)}\n\n"
    
    # Stream the message character by character to simulate typing
    # For smoother streaming, you can adjust the chunk size
    chunk_size = 3
    for i in range(0, len(message), chunk_size):
        text_chunk = message[i:i+chunk_size]
        delta_event = {
            "type": "response.output_text.delta",
            "delta": text_chunk
        }
        yield f"data: {json.dumps(delta_event)}\n\n"
        
        # Optional: Add a small delay for more natural typing effect
        await asyncio.sleep(0.05)
    
    # Send completed event at the end
    completed_event = {
        "type": "response.completed"
    }
    yield f"data: {json.dumps(completed_event)}\n\n"

async def stream_rag_pipeline(user_query: str) -> AsyncGenerator[str, None]:
    """
    Your RAG pipeline async generator that yields chunks matching the format
    expected by the frontend
    """
    # chat_bot=  SportsChatbot()
    # message = chat_bot.answer_query(user_query)
    # user_intent = UserIntentionJson()
    # response_data = user_intent.get_structured_intention_response(chatbot_prompt, user_query, IntentSchema)
    # message = response_data.get("message", "No commentary available at the moment.")
    message = user_query
    
    # Generate a unique response ID
    response_id = f"resp_{hash(user_query)}"
    
    # Send response.created event to match what frontend expects
    created_event = {
        "type": "response.created",
        "response": {
            "id": response_id
        }
    }
    yield f"data: {json.dumps(created_event)}\n\n"
    
    # Stream the message character by character to simulate typing
    # For smoother streaming, you can adjust the chunk size
    chunk_size = 3
    for i in range(0, len(message), chunk_size):
        text_chunk = message[i:i+chunk_size]
        delta_event = {
            "type": "response.output_text.delta",
            "delta": text_chunk
        }
        yield f"data: {json.dumps(delta_event)}\n\n"
        
        # Optional: Add a small delay for more natural typing effect
        await asyncio.sleep(0.05)
    
    # Send completed event at the end
    completed_event = {
        "type": "response.completed"
    }
    yield f"data: {json.dumps(completed_event)}\n\n"



@router.post('/stream', status_code=201)
async def stream_response(userQuery: str = Body(..., embed=True)):
    intent = await classify_intent(userQuery)

    async def event_generator():
        try:
            if intent:
                open_event = {
                    "action": "open_commentary_window",
                    "message": "Starting commentary stream…"
                }
                yield f"event: openWindow\ndata: {json.dumps(open_event)}\n\n"

                # Connect to Redis (with specified db)
                r = redis.Redis.from_url(REDIS_URL)
                pubsub = r.pubsub()
                await pubsub.subscribe("commentary_channel")

                try:
                    async for message in pubsub.listen():
                        if message is None or message["type"] != "message":
                            continue
                        data = json.loads(message["data"])
                        print(json.dumps(data,indent=4))
                        async for s in stream_rag_pipeline(json.dumps(data)):
                            yield s
                finally:
                    await pubsub.unsubscribe("commentary_channel")
                    await pubsub.close()
            else:
                async for s in stream_raw_model(userQuery):
                    yield s

        except Exception as e:
            err = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream')

