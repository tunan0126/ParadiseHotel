from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, rooms, bookings, profile, reviews, admin

app = FastAPI(title="HUCE Hotel Toàn Diện API Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/init")
async def get_init():
    try:
        from routers.rooms import get_rooms
        from routers.admin import admin_get_settings, admin_get_services
        
        rooms_data = await get_rooms()
        settings_data = await admin_get_settings()
        services_data = await admin_get_services()
        
        return {
            "rooms": rooms_data,
            "settings": settings_data,
            "services": services_data
        }
    except Exception as e:
        return {"rooms": [], "settings": {}, "services": []}

from fastapi.staticfiles import StaticFiles

app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(bookings.router)
app.include_router(profile.router)
app.include_router(reviews.router)
app.include_router(admin.public_router)
app.include_router(admin.router)

# Phục vụ files tĩnh của frontend ở thư mục gốc
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)