from bson import ObjectId
from datetime import datetime
import json
from fastapi import HTTPException

# JSON Encoder for ObjectId and datetime
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Helper function to convert MongoDB documents to JSON-serializable dictionaries
def serialize_doc(doc):
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id":
                result["id"] = str(value)
            else:
                result[key] = serialize_doc(value)
        return result
    
    if isinstance(doc, ObjectId):
        return str(doc)
    
    if isinstance(doc, datetime):
        return doc.isoformat()
    
    return doc

def validate_object_id(id: str) -> ObjectId:
    try:
        print(f"Validating ObjectId: {id}")
        return ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

# You can define Pydantic models here for request/response validation
# Example:
# from pydantic import BaseModel
# class ChatCreate(BaseModel):
#     userId: str
#     title: str
#     messages: list = []