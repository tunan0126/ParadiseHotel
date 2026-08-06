import datetime
from pymongo import MongoClient
import os

import asyncio

from database import get_db, MONGO_URI
from security import hash_password

async def init_db():
    print(f"Connecting to MongoDB at: {MONGO_URI}...")
    db = get_db()
    
    print("Clearing old collections...")
    await db.users.drop()
    await db.hotels.drop()
    await db.room_types.drop()
    await db.rooms.drop()
    await db.services.drop()
    await db.bookings.drop()
    await db.reviews.drop()

    print("Inserting Users (TaiKhoan & KhachHang)...")
    await db.users.insert_many([
        {
            "_id": "admin",
            "MatKhau": hash_password("123"),
            "MaVaiTro": "ROLE_ADMIN",
            "MaKH": None,
            "HoTenKH": "Quản trị viên",
            "Email": "admin@example.com",
            "SDT": "0000000000",
            "DiaChi": "",
            "CCCD": ""
        },
        {
            "_id": "khach1",
            "MatKhau": hash_password("123"),
            "MaVaiTro": "ROLE_CUSTOMER",
            "MaKH": "KH01",
            "HoTenKH": "Nguyễn Văn A",
            "Email": "a@example.com",
            "SDT": "0123456789",
            "DiaChi": "Hà Nội",
            "CCCD": "001010101010"
        }
    ])

    print("Inserting Hotel (KhachSan)...")
    await db.hotels.insert_one({
        "_id": "KS01",
        "TenKS": "HUCE HOTEL",
        "DiaChi": "55 Giải Phóng",
        "SDT": "1900 1234",
        "Email": "contact@hucehotel.com"
    })

    print("Inserting Room Types (LoaiPhong)...")
    await db.room_types.insert_many([
        {
            "_id": "LP01",
            "TenLoaiPhong": "Phòng Đơn",
            "MoTa": "Phòng 1 giường cho 1-2 người",
            "SoLuongNguoi": 2,
            "SoGiuong": 1,
            "GiaTien": 500000
        },
        {
            "_id": "LP02",
            "TenLoaiPhong": "Phòng Đôi",
            "MoTa": "Phòng 2 giường cho 2-4 người",
            "SoLuongNguoi": 4,
            "SoGiuong": 2,
            "GiaTien": 800000
        }
    ])

    print("Inserting Rooms (Phong)...")
    await db.rooms.insert_many([
        {"_id": "P01", "SoPhong": "101", "TinhTrang": "Sẵn sàng", "MaLoaiPhong": "LP01", "MaKS": "KS01"},
        {"_id": "P02", "SoPhong": "102", "TinhTrang": "Sẵn sàng", "MaLoaiPhong": "LP01", "MaKS": "KS01"},
        {"_id": "P03", "SoPhong": "201", "TinhTrang": "Sẵn sàng", "MaLoaiPhong": "LP02", "MaKS": "KS01"}
    ])

    print("Inserting Services (DichVu)...")
    await db.services.insert_many([
        {"_id": "DV01", "TenDV": "Giặt ủi", "GiaDV": 50000, "MaKS": "KS01"},
        {"_id": "DV02", "TenDV": "Đưa đón sân bay", "GiaDV": 200000, "MaKS": "KS01"},
        {"_id": "DV03", "TenDV": "Ăn sáng", "GiaDV": 100000, "MaKS": "KS01"}
    ])

    print("Inserting Bookings (DonDatPhong)...")
    await db.bookings.insert_many([
        {
            "_id": "DDP01",
            "NgayDat": datetime.datetime.now() - datetime.timedelta(days=2),
            "NgayTra": datetime.datetime.now() + datetime.timedelta(days=1),
            "TongTien": 1100000,
            "TinhTrangDon": "Đã xác nhận",
            "MaKH": "khach1",
            "Phong": ["P01"],
            "DichVu": [{"MaDV": "DV03", "SoLuong": 2}]
        }
    ])

    # Cập nhật trạng thái phòng có khách
    await db.rooms.update_one({"_id": "P01"}, {"$set": {"TinhTrang": "Đang có khách"}})

    print("Inserting Reviews (DanhGia)...")
    await db.reviews.insert_many([
        {
            "HoTenKhach": "Nguyễn Văn A",
            "NgayDanhGia": datetime.datetime.now(),
            "SoSao": 5,
            "NoiDung": "Khách sạn rất tuyệt vời",
            "TenDangNhap": "khach1",
            "HinhAnh": "",
            "MaKH": "khach1",
            "MaKS": "KS01"
        }
    ])

    print("Database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
