from db import db

# Define your collections here
chat_collection = db.chatInstances

# Export collections
__all__ = ["chat_collection"]