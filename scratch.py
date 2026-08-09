from pydantic import BaseModel
class BookingStatusUpdate(BaseModel):
    status: str
