import json
import os
import asyncio

COMMENTARY_PATH = "commentary.json"

class CommentaryTracker:
    def __init__(self):
        self.last_index = 0
        self.running = False

    async def start(self, send_callback):
        self.running = True
        while self.running:
            new_data = self.load_new_commentary()
            if new_data:
                await send_callback(new_data)
            await asyncio.sleep(60)

    def stop(self):
        self.running = False

    def load_new_commentary(self):
        if not os.path.exists(COMMENTARY_PATH):
            return []

        with open(COMMENTARY_PATH, "r") as f:
            data = json.load(f)

        new_entries = data[self.last_index:]
        self.last_index = len(data)
        return new_entries



# from fastapi import APIRouter, Request, BackgroundTasks
# from rag_engine.dynamic_commentary import CommentaryTracker

# router = APIRouter()
# trackers = {}  # match_id -> tracker

# @router.post("/live-commentary/")
# async def live_commentary_handler(request: Request, background_tasks: BackgroundTasks):
#     body = await request.json()
#     match_id = body.get("match_id")
#     user_intent = body.get("intent")  # extracted via LLM output
#     show_live = user_intent == "live_commentary"

#     def match_is_live(match_id):
#         # implement check with your scorecard or live_model
#         return True

#     async def send_to_frontend(data):
#         # this should send data through SSE or queue to frontend
#         print("Sending:", data)

#     if show_live and match_is_live(match_id):
#         tracker = CommentaryTracker()
#         trackers[match_id] = tracker
#         background_tasks.add_task(tracker.start, send_to_frontend)
#         return {"status": "tracking started"}

#     return {"status": "not tracking"}

# @router.post("/stop-commentary/")
# async def stop_live_commentary(request: Request):
#     body = await request.json()
#     match_id = body.get("match_id")

#     tracker = trackers.get(match_id)
#     if tracker:
#         tracker.stop()
#         return {"status": "tracking stopped"}
#     return {"status": "no tracker found"}