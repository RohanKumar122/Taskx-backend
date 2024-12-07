from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
import os
from passlib.context import CryptContext


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set. Please check your .env file.")

DB_NAME = "task_manager"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
tasks_collection = db.tasks

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
user_collection = db["users"]

tasks_collection.create_index([("created_at", ASCENDING)])
tasks_collection.create_index([("due_date", ASCENDING)])
