import sqlite3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
import sys
import datetime
from database import MONGO_URI, DATABASE_NAME
from security import hash_password

sys.stdout.reconfigure(encoding='utf-8')

async def migrate_data():
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000, tls=True, tlsCAFile=certifi.where())
    db = client[DATABASE_NAME]
    
    print("Connecting to SQLite...")
    conn = sqlite3.connect('hotel.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Clearing old collections in MongoDB...")
    await db.users.drop()
    await db.hotels.drop()
    await db.room_types.drop()
    await db.rooms.drop()
    await db.services.drop()
    await db.bookings.drop()
    await db.reviews.drop()

    # 1. Hotels
    cursor.execute("SELECT * FROM KhachSan")
    hotels = [dict(row) for row in cursor.fetchall()]
    for h in hotels:
        h["_id"] = h.pop("MaKS")
    if hotels:
        await db.hotels.insert_many(hotels)
        print(f"Migrated {len(hotels)} hotels.")

    # 2. Room Types
    cursor.execute("SELECT * FROM LoaiPhong")
    room_types = [dict(row) for row in cursor.fetchall()]
    for rt in room_types:
        rt["_id"] = rt.pop("MaLoaiPhong")
    if room_types:
        await db.room_types.insert_many(room_types)
        print(f"Migrated {len(room_types)} room types.")

    # 3. Rooms
    cursor.execute("SELECT * FROM Phong")
    rooms = [dict(row) for row in cursor.fetchall()]
    for r in rooms:
        r["_id"] = r.pop("MaPhong")
    if rooms:
        await db.rooms.insert_many(rooms)
        print(f"Migrated {len(rooms)} rooms.")

    # 4. Services
    cursor.execute("SELECT * FROM DichVu")
    services = [dict(row) for row in cursor.fetchall()]
    for s in services:
        s["_id"] = s.pop("MaDV")
    if services:
        await db.services.insert_many(services)
        print(f"Migrated {len(services)} services.")

    # 5. Users (TaiKhoan + KhachHang + Admin)
    # Get all accounts
    cursor.execute("SELECT * FROM TaiKhoan")
    accounts = {row['TenDangNhap']: dict(row) for row in cursor.fetchall()}
    
    # Map roles
    cursor.execute("SELECT * FROM TaiKhoan_VaiTro")
    for row in cursor.fetchall():
        if row['TenDangNhap'] in accounts:
            accounts[row['TenDangNhap']]['MaVaiTro'] = row['MaVaiTro']

    # Get KhachHang
    cursor.execute("SELECT * FROM KhachHang")
    customers = {row['TenDangNhap']: dict(row) for row in cursor.fetchall()}
    
    # Combine
    users_to_insert = []
    for username, acc in accounts.items():
        user_doc = {
            "_id": username,
            "MatKhau": hash_password("123"), # Default pass if raw is missing, wait let's just keep raw or rehash? 
            # In old system they might have plain text or MD5. Since fastAPI expects bcrypt, let's reset to "123" 
            # or keep old password if it's already bcrypt. We will just rehash their plain text if they had plain text.
            "MaVaiTro": acc.get('MaVaiTro', 'ROLE_CUSTOMER'),
            "MaKH": None,
            "HoTenKH": None,
            "Email": None,
            "SDT": None,
            "DiaChi": None,
            "CCCD": None
        }
        
        # In TaiKhoan table, MatKhau is usually stored. Let's just use hash_password("123") for all migrated users to be safe,
        # or hash whatever they had. Let's hash their old password.
        old_pass = acc.get('MatKhau', '123')
        if not old_pass.startswith('$2b$'):
            user_doc['MatKhau'] = hash_password(old_pass)
        else:
            user_doc['MatKhau'] = old_pass
            
        if username in customers:
            cust = customers[username]
            user_doc["MaKH"] = cust.get("MaKH")
            user_doc["HoTenKH"] = cust.get("HoTenKH")
            user_doc["Email"] = cust.get("Email")
            user_doc["SDT"] = cust.get("SDT")
            user_doc["DiaChi"] = cust.get("DiaChi")
            user_doc["CCCD"] = cust.get("CCCD")
        
        users_to_insert.append(user_doc)
        
    if users_to_insert:
        await db.users.insert_many(users_to_insert)
        print(f"Migrated {len(users_to_insert)} users.")

    # 6. Bookings (DonDatPhong + ChiTietDatPhong + ChiTietSuDungDV)
    cursor.execute("SELECT * FROM DonDatPhong")
    bookings = {row['MaDDP']: dict(row) for row in cursor.fetchall()}
    
    cursor.execute("SELECT * FROM ChiTietDatPhong")
    for row in cursor.fetchall():
        maddp = row['MaDDP']
        if maddp in bookings:
            if "Phong" not in bookings[maddp]:
                bookings[maddp]["Phong"] = []
            bookings[maddp]["Phong"].append(row['MaPhong'])

    cursor.execute("SELECT * FROM ChiTietSuDungDV")
    for row in cursor.fetchall():
        maddp = row['MaDDP']
        if maddp in bookings:
            if "DichVu" not in bookings[maddp]:
                bookings[maddp]["DichVu"] = []
            bookings[maddp]["DichVu"].append({"MaDV": row['MaDV'], "SoLuong": row['SoLuong']})
            
    bookings_to_insert = []
    for maddp, b in bookings.items():
        # parse dates
        ngay_dat = b.get("NgayDat")
        ngay_tra = b.get("NgayTra")
        if isinstance(ngay_dat, str):
            try: ngay_dat = datetime.datetime.fromisoformat(ngay_dat.replace("Z", ""))
            except: pass
        if isinstance(ngay_tra, str):
            try: ngay_tra = datetime.datetime.fromisoformat(ngay_tra.replace("Z", ""))
            except: pass
            
        bookings_to_insert.append({
            "_id": maddp,
            "NgayDat": ngay_dat,
            "NgayTra": ngay_tra,
            "TongTien": b.get("TongTien", 0),
            "TinhTrangDon": b.get("TinhTrangDon", ""),
            "MaKH": b.get("MaKH", ""),
            "Phong": b.get("Phong", []),
            "DichVu": b.get("DichVu", [])
        })
        
    if bookings_to_insert:
        await db.bookings.insert_many(bookings_to_insert)
        print(f"Migrated {len(bookings_to_insert)} bookings.")
        
    # 7. Reviews
    cursor.execute("SELECT * FROM DanhGia")
    reviews = []
    for row in cursor.fetchall():
        rev = dict(row)
        ngay = rev.get("NgayDanhGia")
        if isinstance(ngay, str):
            try: ngay = datetime.datetime.fromisoformat(ngay.replace("Z", ""))
            except: pass
        rev["NgayDanhGia"] = ngay
        reviews.append(rev)
        
    if reviews:
        await db.reviews.insert_many(reviews)
        print(f"Migrated {len(reviews)} reviews.")

    print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_data())
