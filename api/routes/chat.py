from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any
from bson import ObjectId
from datetime import datetime

# Import database modules
from db.collections import chat_collection
from db.models import serialize_doc, validate_object_id

router = APIRouter()

@router.get("/chats/")
async def get_chats(userId: str = Query(..., description="User ID")):
    if not userId:
        raise HTTPException(status_code=400, detail="user ID is required")
    
    chats = await chat_collection.find({"userId": userId}).to_list(length=100)
    serialized_chats = serialize_doc(chats)
    return {"success": True, "data": serialized_chats}

@router.post("/chats/", status_code=201)
async def create_chat(chat_data: Dict[str, Any]):
    chat_data["createdAt"] = datetime.now()
    chat_data["updatedAt"] = datetime.now()
    
    result = await chat_collection.insert_one(chat_data)
    created_chat = await chat_collection.find_one({"_id": result.inserted_id})
    
    return {"success": True, "data": serialize_doc(created_chat)}

@router.get("/chats/{id}")
async def get_chat(id: ObjectId = Depends(validate_object_id)):
    chat = await chat_collection.find_one({"_id": ObjectId(id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {"success": True, "data": serialize_doc(chat)}

@router.put("/chats/{id}")
async def update_chat(chat_update: Dict[str, Any], id: ObjectId = Depends(validate_object_id)):
    chat_update["updatedAt"] = datetime.now()
    
    result = await chat_collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": chat_update},
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {"success": True, "data": serialize_doc(result)}

@router.delete("/chats/{id}")
async def delete_chat(id: ObjectId = Depends(validate_object_id)):
    result = await chat_collection.find_one_and_delete({"_id": ObjectId(id)})
    
    if not result:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {"success": True, "message": "Chat deleted successfully"}

@router.post("/chats/{id}/messages")
async def add_message(message: Dict[str, Any], id: ObjectId = Depends(validate_object_id)):
    chat = await chat_collection.find_one({"_id": ObjectId(id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    message["timestamp"] = datetime.now()
    
    result = await chat_collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {
            "$push": {"messages": message},
            "$set": {"updatedAt": datetime.now()}
        },
        return_document=True
    )
    
    return {"success": True, "data": serialize_doc(result)}