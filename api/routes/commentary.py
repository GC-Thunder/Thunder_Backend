from fastapi import APIRouter, HTTPException,Body
from fastapi.responses import StreamingResponse
from openai import OpenAI
import json
from typing import AsyncGenerator

router = APIRouter()
client = OpenAI()

async def classify_intent(text: str) -> str:
    """
    Very simple stub: in prod swap out for your real intent‐classifier/RAG
    """
    # e.g. run a little chat‐completion to classify or use regex
    # Here we just demo: if the word "commentary" is in the query
    return "commentary" if "commentary" in text.lower() else "default"

async def stream_raw_model(user_query: str) -> AsyncGenerator[str, None]:
    stream = client.responses.create(
        model='gpt-4.1',
        input=[{'role': 'user', 'content': user_query}],
        stream=True
    )
    for chunk in stream:
        yield f"data: {json.dumps(chunk.dict())}\n\n"

async def stream_rag_pipeline(user_query: str) -> AsyncGenerator[str, None]:
    """
    Your RAG pipeline async generator; yields dict‐like chunks
    """
    # replace the next lines with your real RAG pipeline call
    # from some_rag_module import rag_stream
    # async for chunk in rag_stream(user_query):
        # yield f"data: {json.dumps(chunk)}\n\n"
    stream = client.responses.create(
        model='gpt-4.1',
        input=[{'role': 'user', 'content': user_query}],
        stream=True
    )
    for chunk in stream:
        yield f"data: {json.dumps(chunk.dict())}\n\n"
    

@router.post('/stream', status_code=201)
async def stream_response(userQuery: str = Body(..., embed=True)   ):
    intent = await classify_intent(userQuery)

    async def event_generator():
        try:
            if intent == "commentary":
                # First send a custom event so client can open a new window
                open_event = {
                    "action": "open_commentary_window",
                    "message": "Starting commentary stream…"
                }
                # note the "event: openWindow" line
                yield f"event: openWindow\ndata: {json.dumps(open_event)}\n\n"

                # now hand off to your RAG pipeline
                async for s in stream_rag_pipeline(userQuery):
                    yield s
            else:
                # fallback to raw model streaming
                async for s in stream_raw_model(userQuery):
                    yield s

        except Exception as e:
            err = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream')
