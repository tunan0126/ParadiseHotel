import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import certifi

MONGO_URI = "mongodb+srv://adminhotel:AdminHotel12345@cluster0.btcad6s.mongodb.net/hotel_db?retryWrites=true&w=majority&appName=Cluster0"

async def test_db():
    print("Testing connection...")
    try:
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000, tls=True, tlsCAFile=certifi.where())
        db = client["hotel_db"]
        
        rooms = await db.rooms.count_documents({})
        room_types = await db.room_types.count_documents({})
        users = await db.users.count_documents({})
        
        print(f"Rooms: {rooms}")
        print(f"Room Types: {room_types}")
        print(f"Users: {users}")
    except Exception as e:
        print("Error:", e)

asyncio.run(test_db())
