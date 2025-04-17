import motor.motor_asyncio
import os
from dotenv import load_dotenv

# Load environment variables if not already loaded
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client.local  # Using the same DB name as before

# Export the database client and db instance
__all__ = ["client", "db"]