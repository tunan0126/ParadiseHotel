from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyodbc
import datetime

app = FastAPI(title="HUCE Hotel Toàn Diện API Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_CONN_STR = ""

SERVER_CANDIDATES = [
    ".\\SQLEXPRESS", 
    "(local)", 
    "localhost", 
    ".", 
    "127.0.0.1"
]

print("⏳ Đang dò tìm SQL Server...")
for server in SERVER_CANDIDATES:
    test_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE=QuanLyKhachSanHUCE1;Trusted_Connection=yes;"
    try:
        conn = pyodbc.connect(test_str, timeout=1)
        VALID_CONN_STR = test_str
        conn.close()
        print(f"✅ Đã kết nối thành công CSDL tại máy chủ: {server}")
        break
    except Exception:
        continue

if not VALID_CONN_STR:
    print("❌ CẢNH BÁO: Không tự động tìm thấy SQL Server. Hãy đảm bảo Database đã được bật!")
    VALID_CONN_STR = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE=QuanLyKhachSanHUCE1;Trusted_Connection=yes;"

def get_db_cursor():
    try:
        conn = pyodbc.connect(VALID_CONN_STR)
        return conn, conn.cursor()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Không thể kết nối đến SQL Server")

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

@app.get("/api/rooms")
def get_rooms(username: str = ""):
    """API lấy TOÀN BỘ danh sách phòng, nhận diện chính chủ và TỰ ĐỘNG BÙ NGÀY"""
    conn, cursor = get_db_cursor()
    query = """
        SELECT p.MaPhong, p.SoPhong, lp.TenLoaiPhong, lp.GiaTien, p.TinhTrang, lp.HinhAnh,
               (SELECT TOP 1 kh.TenDangNhap FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP JOIN KhachHang kh ON ddp.MaKH = kh.MaKH WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC) as NguoiDatCuoi,
               (SELECT TOP 1 ddp.NgayTra FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC) as NgayTraDuKien
        FROM Phong p
        JOIN LoaiPhong lp ON p.MaLoaiPhong = lp.MaLoaiPhong
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    import random
    
    rooms = []
    for row in rows:
        status = row[4]
        nguoi_dat = row[6]
        ngay_tra = row[7]
        
        is_my_room = True if (status == 'Đang có khách' and username != "" and nguoi_dat == username) else False
        
        if status == 'Đang có khách' and not ngay_tra:
            ngay_tra = datetime.date.today() + datetime.timedelta(days=random.randint(1, 3))
            
        ngay_tra_str = ngay_tra.strftime('%d/%m/%Y') if ngay_tra else ""
        
        rooms.append({
            "id": row[0],
            "roomNumber": row[1],
            "name": row[2],
            "price": float(row[3]),
            "status": status,
            "image": row[5],
            "isAvailable": True if status == 'Sẵn sàng' else False,
            "isMyRoom": is_my_room,
            "availableFrom": ngay_tra_str
        })
    conn.close()
    return rooms

@app.get("/api/rooms/search")
def search_available_rooms(
    checkin: str = "", checkout: str = "", guests: int = 1, room_type: str = "all",
    min_price: float = 0, max_price: float = 999999999, username: str = ""
):
    """API Lọc phòng thông minh (Check trùng lịch + Giá + Sức chứa + Tự bù ngày)"""
    conn, cursor = get_db_cursor()
    
    ci_date = checkin if checkin else str(datetime.date.today())
    co_date = checkout if checkout else str(datetime.date.today() + datetime.timedelta(days=1))

    query = """
        SELECT p.MaPhong, p.SoPhong, lp.TenLoaiPhong, lp.GiaTien, p.TinhTrang, lp.HinhAnh,
               CASE 
                   WHEN p.MaPhong IN (
                       SELECT ctdp.MaPhong 
                       FROM ChiTietDatPhong ctdp
                       JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP
                       WHERE ddp.TinhTrangDon != N'Đã hủy'
                       AND (ddp.NgayDat < ? AND ddp.NgayTra > ?)
                   ) THEN 0 
                   ELSE 1 
               END as IsAvailableForDates,
               (SELECT TOP 1 kh.TenDangNhap FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP JOIN KhachHang kh ON ddp.MaKH = kh.MaKH WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC) as NguoiDatCuoi,
               (SELECT TOP 1 ddp.NgayTra FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC) as NgayTraDuKien
        FROM Phong p
        JOIN LoaiPhong lp ON p.MaLoaiPhong = lp.MaLoaiPhong
        WHERE lp.SoLuongNguoi >= ? 
          AND lp.GiaTien >= ? 
          AND lp.GiaTien <= ?
    """
    params = [co_date, ci_date, guests, min_price, max_price]

    if room_type != "all":
        query += " AND lp.TenLoaiPhong = ? "
        params.append(room_type)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    import random
    
    rooms = []
    for row in rows:
        is_available = bool(row[6])
        display_status = "Sẵn sàng" if is_available else "Đang có khách"
        nguoi_dat = row[7]
        ngay_tra = row[8]
        
        is_my_room = True if (not is_available and username != "" and nguoi_dat == username) else False
        
        if not is_available and not ngay_tra:
            ngay_tra = datetime.date.today() + datetime.timedelta(days=random.randint(1, 3))
            
        ngay_tra_str = ngay_tra.strftime('%d/%m/%Y') if ngay_tra else ""

        rooms.append({
            "id": row[0],
            "roomNumber": row[1],
            "name": row[2],
            "price": float(row[3]),
            "status": display_status,
            "image": row[5],
            "isAvailable": is_available,
            "isMyRoom": is_my_room,
            "availableFrom": ngay_tra_str
        })
    conn.close()
    return rooms

@app.get("/api/rooms/{room_id}/booked-dates")
def get_booked_dates(room_id: str):
    """API lấy danh sách các ngày đã có khách đặt của 1 phòng cụ thể"""
    conn, cursor = get_db_cursor()
    try:
        query = """
            SELECT d.NgayDat, d.NgayTra 
            FROM DonDatPhong d
            JOIN ChiTietDatPhong c ON d.MaDDP = c.MaDDP
            WHERE c.MaPhong = ? AND d.TinhTrangDon IN (N'Đang ở', N'Đã xác nhận')
        """
        cursor.execute(query, (room_id,))
        rows = cursor.fetchall()
        
        booked_dates = []
        for row in rows:
            start_date = row[0].strftime("%Y-%m-%d") if hasattr(row[0], 'strftime') else str(row[0])[:10]
            end_date = row[1].strftime("%Y-%m-%d") if hasattr(row[1], 'strftime') else str(row[1])[:10]
            
            booked_dates.append({
                "from": start_date,
                "to": end_date
            })
            
        return booked_dates
    except Exception as e:
        print(f"Lỗi truy vấn lịch bận: {e}")
        return []
    finally:
        conn.close()
        
@app.post("/api/login")
def login(data: LoginModel):
    conn, cursor = get_db_cursor()
    cursor.execute("""
        SELECT tk.TenDangNhap, tk.MatKhau, vt.MaVaiTro 
        FROM TaiKhoan tk
        LEFT JOIN TaiKhoan_VaiTro tkvt ON tk.TenDangNhap = tkvt.TenDangNhap
        LEFT JOIN VaiTro vt ON tkvt.MaVaiTro = vt.MaVaiTro
        WHERE tk.TenDangNhap = ? AND tk.MatKhau = ?
    """, (data.username, data.password))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")
    
    fullname = "Người dùng"
    role = "customer"
    if row[2] == "ROLE_ADMIN":
        role = "admin"
        cursor.execute("SELECT TenNV FROM Admin WHERE TenDangNhap = ?", (data.username,))
        admin_row = cursor.fetchone()
        if admin_row: fullname = admin_row[0]
    else:
        cursor.execute("SELECT HoTenKH FROM KhachHang WHERE TenDangNhap = ?", (data.username,))
        kh_row = cursor.fetchone()
        if kh_row: fullname = kh_row[0]
        
    conn.close()
    return {"status": "success", "username": row[0], "fullname": fullname, "role": role}

@app.post("/api/register")
def register(data: RegisterModel):
    conn, cursor = get_db_cursor()
    cursor.execute("SELECT TenDangNhap FROM TaiKhoan WHERE TenDangNhap = ?", (data.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Tài khoản email đã tồn tại")
    try:
        cursor.execute("INSERT INTO TaiKhoan (TenDangNhap, MatKhau) VALUES (?, ?)", (data.username, data.password))
        cursor.execute("INSERT INTO TaiKhoan_VaiTro (TenDangNhap, MaVaiTro) VALUES (?, 'ROLE_CUSTOMER')", (data.username,))
        
        cursor.execute("SELECT COUNT(*) FROM KhachHang")
        ma_kh = "KH" + str(cursor.fetchone()[0] + 101)
        
        cursor.execute(
            "INSERT INTO KhachHang (MaKH, HoTenKH, Email, SDT, DiaChi, CCCD, TenDangNhap) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ma_kh, data.fullname, data.username, data.phone, data.address, data.idcard, data.username)
        )
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/api/bookings")
def create_booking(data: BookingModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("SELECT MaKH FROM KhachHang WHERE TenDangNhap = ?", (data.username,))
        kh_row = cursor.fetchone()
        if not kh_row: raise HTTPException(status_code=404, detail="Không tìm thấy thông tin khách")
        ma_kh = kh_row[0]
        
        cursor.execute("SELECT COUNT(*) FROM DonDatPhong")
        ma_ddp = "DDP" + str(cursor.fetchone()[0] + 101)
        
        try:
            ngay_dat = datetime.datetime.fromisoformat(data.checkin)
            ngay_tra = datetime.datetime.fromisoformat(data.checkout)
        except Exception:
            ngay_dat = datetime.datetime.now()
            ngay_tra = ngay_dat + datetime.timedelta(days=1)

        cursor.execute(
            "INSERT INTO DonDatPhong (MaDDP, NgayDat, NgayTra, TongTien, TinhTrangDon, MaKH) VALUES (?, ?, ?, ?, N'Đã xác nhận', ?)",
            (ma_ddp, ngay_dat, ngay_tra, data.total_price, ma_kh)
        )
        cursor.execute("INSERT INTO ChiTietDatPhong (MaPhong, MaDDP) VALUES (?, ?)", (data.room_id, ma_ddp))
        cursor.execute("UPDATE Phong SET TinhTrang = N'Đang có khách' WHERE MaPhong = ?", (data.room_id,))
        
        for svc_name in data.services:
            cursor.execute("SELECT MaDV FROM DichVu WHERE TenDV = ?", (svc_name,))
            svc_row = cursor.fetchone()
            if svc_row:
                cursor.execute("INSERT INTO ChiTietSuDungDV (MaDV, MaDDP, SoLuong) VALUES (?, ?, 1)", (svc_row[0], ma_ddp))
                
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.get("/api/profile")
def get_profile(username: str):
    conn, cursor = get_db_cursor()
    cursor.execute("SELECT HoTenKH, Email, SDT, DiaChi, CCCD FROM KhachHang WHERE TenDangNhap = ?", (username,))
    r = cursor.fetchone()
    conn.close()
    if not r: raise HTTPException(status_code=404, detail="Không tìm thấy")
    return {"fullname": r[0], "email": r[1], "phone": r[2], "address": r[3], "idcard": r[4] if r[4] else ""}

@app.post("/api/profile/update")
def update_profile(data: ProfileUpdateModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("""
            UPDATE KhachHang 
            SET HoTenKH = ?, SDT = ?, CCCD = ?, DiaChi = ? 
            WHERE TenDangNhap = ?
        """, (data.fullname, data.phone, data.idcard, data.address, data.username))
        conn.commit()
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()
    
@app.post("/api/profile/password")
def update_password(data: PasswordUpdateModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("SELECT MatKhau FROM TaiKhoan WHERE TenDangNhap = ?", (data.username,))
        row = cursor.fetchone()
        if not row or row[0] != data.old_password:
            conn.close()
            raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác!")
        
        cursor.execute("UPDATE TaiKhoan SET MatKhau = ? WHERE TenDangNhap = ?", (data.new_password, data.username))
        conn.commit()
        return {"status": "success", "message": "Đổi mật khẩu thành công!"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/profile/history")
def get_booking_history(username: str):
    conn, cursor = get_db_cursor()
    cursor.execute("""
        SELECT ddp.MaDDP, lp.TenLoaiPhong, ddp.NgayDat, ddp.NgayTra, ddp.TinhTrangDon, ddp.TongTien 
        FROM DonDatPhong ddp
        JOIN KhachHang kh ON ddp.MaKH = kh.MaKH
        JOIN ChiTietDatPhong ctdp ON ddp.MaDDP = ctdp.MaDDP
        JOIN Phong p ON ctdp.MaPhong = p.MaPhong
        JOIN LoaiPhong lp ON p.MaLoaiPhong = lp.MaLoaiPhong
        WHERE kh.TenDangNhap = ?
    """, (username,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "roomName": r[1], "checkin": str(r[2]), "checkout": str(r[3]), "status": r[4], "totalPrice": float(r[5])} for r in rows]

@app.get("/api/profile/services")
def get_used_services(username: str):
    conn, cursor = get_db_cursor()
    cursor.execute("""
        SELECT ctsd.MaDDP, dv.TenDV, ddp.NgayDat, ctsd.SoLuong, (dv.GiaDV * ctsd.SoLuong) as Total
        FROM ChiTietSuDungDV ctsd
        JOIN DichVu dv ON ctsd.MaDV = dv.MaDV
        JOIN DonDatPhong ddp ON ctsd.MaDDP = ddp.MaDDP
        JOIN KhachHang kh ON ddp.MaKH = kh.MaKH
        WHERE kh.TenDangNhap = ?
    """, (username,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "serviceName": r[1], "date": str(r[2]), "quantity": r[3], "total": float(r[4])} for r in rows]

@app.get("/api/reviews")
def get_all_reviews():
    conn, cursor = get_db_cursor()
    cursor.execute("""
        SELECT dg.HoTenKhach, dg.NgayDanhGia, dg.SoSao, dg.NoiDung, dg.HinhAnh,
               kh.HoTenKH, ks.TenKS
        FROM DanhGia dg
        LEFT JOIN KhachHang kh ON dg.MaKH = kh.MaKH
        LEFT JOIN KhachSan ks ON dg.MaKS = ks.MaKS
        ORDER BY dg.MaDG DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    reviews = []
    for r in rows:
        reviews.append({
            "customerName": r[5] if r[5] else r[0],
            "date": str(r[1].strftime('%d/%m/%Y')) if isinstance(r[1], datetime.date) else str(r[1]),
            "stars": r[2],
            "content": r[3],
            "image": r[4] if r[4] else "",
            "hotelName": r[6] if r[6] else ""
        })
    return reviews

@app.post("/api/reviews/submit")
def submit_review(data: ReviewSubmitModel):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Nội dung đánh giá không được để trống")

    conn, cursor = get_db_cursor()
    try:
        ma_kh = None
        if data.username:
            cursor.execute("SELECT MaKH FROM KhachHang WHERE TenDangNhap = ?", (data.username,))
            row = cursor.fetchone()
            if row:
                ma_kh = row[0]

        ngay_hien_tai = datetime.date.today()
        cursor.execute("""
            INSERT INTO DanhGia (HoTenKhach, NgayDanhGia, SoSao, NoiDung, TenDangNhap, HinhAnh, MaKH, MaKS)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data.customer_name, ngay_hien_tai, data.stars, data.content, data.username, data.image, ma_kh, data.ma_ks))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/admin/rooms")
def admin_get_rooms():
    conn, cursor = get_db_cursor()
    cursor.execute("""
        SELECT p.MaPhong, p.SoPhong, lp.TenLoaiPhong, p.TinhTrang, lp.GiaTien, p.MaLoaiPhong
        FROM Phong p
        JOIN LoaiPhong lp ON p.MaLoaiPhong = lp.MaLoaiPhong
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "roomNumber": r[1], "name": r[2], "status": r[3], "price": float(r[4]), "maLoai": r[5]} for r in rows]

@app.post("/api/admin/rooms/status/{room_id}")
def admin_change_room_status(room_id: str):
    conn, cursor = get_db_cursor()
    cursor.execute("SELECT TinhTrang FROM Phong WHERE MaPhong = ?", (room_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Không thấy phòng")
    
    current_status = row[0]
    if current_status == 'Sẵn sàng': next_status = 'Đang có khách'
    elif current_status == 'Đang có khách': next_status = 'Đang dọn dẹp'
    else: next_status = 'Sẵn sàng'
    
    cursor.execute("UPDATE Phong SET TinhTrang = ? WHERE MaPhong = ?", (next_status, room_id))
    conn.commit()
    conn.close()
    return {"status": "success", "next_status": next_status}

@app.get("/api/admin/room-types")
def admin_get_room_types(keyword: str = Query("")):
    conn, cursor = get_db_cursor()
    query = "SELECT MaLoaiPhong, TenLoaiPhong, MoTa, SoLuongNguoi, GiaTien, SoGiuong FROM LoaiPhong"
    if keyword:
        query += " WHERE MaLoaiPhong LIKE ? OR TenLoaiPhong LIKE ?"
        cursor.execute(query, (f"%{keyword}%", f"%{keyword}%"))
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "moTa": r[2] or "", "maxPeople": r[3], "price": float(r[4]), "beds": r[5] if r[5] else 1} for r in rows]

@app.post("/api/admin/room-types")
def admin_add_room_type(data: RoomTypeActionModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM LoaiPhong")
        ma_loai = "LP" + str(cursor.fetchone()[0] + 101)
        cursor.execute(
            "INSERT INTO LoaiPhong (MaLoaiPhong, TenLoaiPhong, MoTa, SoLuongNguoi, SoGiuong, GiaTien, MaKS) VALUES (?, ?, ?, ?, ?, ?, 'KS01')",
            (ma_loai, data.ten_loai_phong, data.mo_ta, data.so_luong_nguoi, data.so_giuong, data.gia_tien)
        )
        conn.commit()
        return {"status": "success", "id": ma_loai}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/api/admin/room-types/{type_id}")
def admin_edit_room_type(type_id: str, data: RoomTypeActionModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute(
            "UPDATE LoaiPhong SET TenLoaiPhong = ?, MoTa = ?, SoLuongNguoi = ?, SoGiuong = ?, GiaTien = ? WHERE MaLoaiPhong = ?",
            (data.ten_loai_phong, data.mo_ta, data.so_luong_nguoi, data.so_giuong, data.gia_tien, type_id)
        )
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.delete("/api/admin/room-types/{type_id}")
def admin_delete_room_type(type_id: str):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("DELETE FROM LoaiPhong WHERE MaLoaiPhong = ?", (type_id,))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Không thể xóa do vẫn còn phòng thuộc loại này (ràng buộc khóa ngoại).")
    finally: conn.close()

@app.get("/api/admin/bookings")
def admin_get_bookings(keyword: str = Query("")):
    conn, cursor = get_db_cursor()
    query = """
        SELECT ddp.MaDDP, kh.HoTenKH, ddp.NgayDat, ddp.NgayTra, ddp.TongTien, ddp.TinhTrangDon
        FROM DonDatPhong ddp
        JOIN KhachHang kh ON ddp.MaKH = kh.MaKH
    """
    if keyword:
        query += " WHERE ddp.MaDDP LIKE ? OR kh.HoTenKH LIKE ?"
        cursor.execute(query, (f"%{keyword}%", f"%{keyword}%"))
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "customerName": r[1], "checkin": str(r[2]), "checkout": str(r[3]), "totalPrice": float(r[4]), "status": r[5]} for r in rows]

@app.get("/api/admin/services")
def admin_get_services(keyword: str = Query("")):
    conn, cursor = get_db_cursor()
    query = "SELECT MaDV, TenDV, GiaDV, MaKS FROM DichVu"
    if keyword:
        query += " WHERE MaDV LIKE ? OR TenDV LIKE ?"
        cursor.execute(query, (f"%{keyword}%", f"%{keyword}%"))
    else:
        cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "category": "Tiện ích", "price": float(r[2]), "status": "Hoạt động"} for r in rows]

@app.get("/api/admin/settings")
def admin_get_settings():
    try:
        conn, cursor = get_db_cursor()
        cursor.execute("SELECT TOP 1 TenKS, SDT, DiaChi, Email FROM KhachSan")
        r = cursor.fetchone()
        conn.close()
        if r: return {"name": r[0], "phone": r[1], "address": r[2], "checkin": "14:00", "checkout": "12:00", "vat": 8}
        return {"name": "HUCE HOTEL", "phone": "1900 1234", "address": "55 Giải Phóng", "checkin": "14:00", "checkout": "12:00", "vat": 8}
    except Exception as e:
        return {"LOI_CUA_MAY_MOI_LA": str(e)}

@app.post("/api/admin/settings")
def admin_save_settings(data: SettingsUpdateModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM KhachSan")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO KhachSan (MaKS, TenKS, DiaChi, SDT, Email) VALUES ('KS01', ?, ?, ?, ?)", (data.name, data.address, data.phone, data.address))
        else:
            cursor.execute("UPDATE KhachSan SET TenKS = ?, DiaChi = ?, SDT = ? WHERE MaKS = 'KS01'", (data.name, data.address, data.phone))
        conn.commit()
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

@app.post("/api/admin/rooms")
def admin_add_room(data: RoomActionModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Phong")
        ma_phong = "P" + str(cursor.fetchone()[0] + 101)
        
        cursor.execute(
            "INSERT INTO Phong (MaPhong, SoPhong, TinhTrang, MaLoaiPhong, MaKS) VALUES (?, ?, ?, ?, 'KS01')",
            (ma_phong, data.so_phong, data.tinh_trang, data.ma_loai_phong)
        )
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/api/admin/rooms/{room_id}")
def admin_edit_room(room_id: str, data: RoomActionModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute(
            "UPDATE Phong SET SoPhong = ?, MaLoaiPhong = ?, TinhTrang = ? WHERE MaPhong = ?",
            (data.so_phong, data.ma_loai_phong, data.tinh_trang, room_id)
        )
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.delete("/api/admin/rooms/{room_id}")
def admin_delete_room(room_id: str):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("DELETE FROM Phong WHERE MaPhong = ?", (room_id,))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Không thể xóa do phòng đã có lịch sử đặt (ràng buộc khóa ngoại).")
    finally: conn.close()

@app.post("/api/admin/services")
def admin_add_service(data: ServiceActionModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM DichVu")
        ma_dv = "DV" + str(cursor.fetchone()[0] + 101)
        cursor.execute(
            "INSERT INTO DichVu (MaDV, TenDV, GiaDV, MaKS) VALUES (?, ?, ?, 'KS01')",
            (ma_dv, data.ten_dv, data.gia_dv)
        )
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.put("/api/admin/services/{svc_id}")
def admin_edit_service(svc_id: str, data: ServiceActionModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("UPDATE DichVu SET TenDV = ?, GiaDV = ? WHERE MaDV = ?", (data.ten_dv, data.gia_dv, svc_id))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.delete("/api/admin/services/{svc_id}")
def admin_delete_service(svc_id: str):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("DELETE FROM DichVu WHERE MaDV = ?", (svc_id,))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Không thể xóa do dịch vụ đã được sử dụng.")
    finally: conn.close()