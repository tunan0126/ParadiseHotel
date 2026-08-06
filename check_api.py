from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
response = client.get("/api/rooms")
print("Status:", response.status_code)
print("Data:", response.json()[:1]) # print just the first room
