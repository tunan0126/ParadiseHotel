import json
import os
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

SETTINGS_FILE = "settings.json"
# Placeholder for Cloud MongoDB URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://tuananh:123@cluster0.btcad6s.mongodb.net/hotel_db?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = "hotel_db"

client = None

def get_extra_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"checkin": "14:00", "checkout": "12:00", "vat": 8}

def save_extra_settings(checkin, checkout, vat):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"checkin": checkin, "checkout": checkout, "vat": vat}, f)
    except: pass

def get_db():
    global client
    import certifi
    try:
        if client is None:
            client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000, tls=True, tlsCAFile=certifi.where())
        db = client[DATABASE_NAME]
        return db
    except Exception as e:
        raise HTTPException(status_code=500, detail="Không thể kết nối đến MongoDB Cloud")
