from pymongo import MongoClient
from shared.utils.config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.DB_NAME]
