from pydantic import BaseModel

class LoginModel(BaseModel):
    username: str
    password: str

class RegisterModel(BaseModel):
    fullname: str
    username: str
    phone: str
    idcard: str
    address: str
    password: str

class BookingModel(BaseModel):
    username: str
    room_id: str
    checkin: str
    checkout: str
    total_price: float
    services: list

class AdminBookingModel(BaseModel):
    username: str = ""
    fullname: str = ""
    phone: str = ""
    idcard: str = ""
    room_id: str
    checkin: str
    checkout: str
    total_price: float
    services: list = []

class ProfileUpdateModel(BaseModel):
    username: str
    fullname: str
    phone: str
    idcard: str
    address: str

class SettingsUpdateModel(BaseModel):
    name: str
    phone: str
    address: str
    checkin: str
    checkout: str
    vat: int

class PasswordUpdateModel(BaseModel):
    username: str
    old_password: str
    new_password: str

class ReviewSubmitModel(BaseModel):
    customer_name: str
    stars: int
    content: str
    username: str = ""
    image: str = ""
    ma_ks: str = "KS01"

class RoomActionModel(BaseModel):
    so_phong: str
    ma_loai_phong: str
    tinh_trang: str = "Sẵn sàng"

class RoomTypeActionModel(BaseModel):
    ten_loai_phong: str
    mo_ta: str
    so_luong_nguoi: int
    so_giuong: int
    gia_tien: float

class ServiceActionModel(BaseModel):
    ten_dv: str
    gia_dv: float

class CancelBookingModel(BaseModel):
    ma_ddp: str
    username: str

class PaymentModel(BaseModel):
    ma_ddp: str
    phuong_thuc: str
    username: str
