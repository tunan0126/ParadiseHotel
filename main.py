from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import datetime
import json
import os

SETTINGS_FILE = "settings.json"

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

app = FastAPI(title="HUCE Hotel Toàn Diện API Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_cursor():
    try:
        conn = sqlite3.connect("hotel.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        return conn, conn.cursor()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Không thể kết nối đến SQLite")

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

@app.get("/api/admin/stats/summary")
def get_stats_summary():
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Phong")
        total_rooms = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM DichVu")
        total_services = cursor.fetchone()[0]
        
        return {"total_rooms": total_rooms, "total_services": total_services}
    except Exception as e:
        return {"total_rooms": 0, "total_services": 0}
    finally:
        conn.close()
    
@app.get("/api/admin/rooms/search")
def admin_search_rooms(keyword: str = Query("")):
    conn, cursor = get_db_cursor()
    today_str = str(datetime.date.today())
    tomorrow_str = str(datetime.date.today() + datetime.timedelta(days=1))
    
    query = """
        SELECT p.MaPhong, p.SoPhong, lp.TenLoaiPhong, 
               CASE 
                   WHEN p.MaPhong IN (
                       SELECT ctdp.MaPhong 
                       FROM ChiTietDatPhong ctdp
                       JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP
                       WHERE ddp.TinhTrangDon != 'Đã hủy'
                       AND (ddp.NgayDat < ? AND ddp.NgayTra > ?)
                   ) THEN 'Đang có khách' 
                   WHEN p.TinhTrang != 'Sẵn sàng' THEN p.TinhTrang
                   ELSE 'Sẵn sàng' 
               END as TinhTrang,
               lp.GiaTien, p.MaLoaiPhong
        FROM Phong p
        JOIN LoaiPhong lp ON p.MaLoaiPhong = lp.MaLoaiPhong
    """
    params = [tomorrow_str, today_str]
    if keyword:
        query += " WHERE p.MaPhong LIKE ? OR p.SoPhong LIKE ?"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
        cursor.execute(query, params)
    else:
        cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "roomNumber": r[1], "name": r[2], "status": r[3], "price": float(r[4]), "maLoai": r[5]} for r in rows]
@app.get("/api/rooms")
def get_rooms(username: str = ""):
    """API lấy TOÀN BỘ danh sách phòng, tự động tính toán kẹt lịch cho HÔM NAY"""
    conn, cursor = get_db_cursor()
    
    # Lấy ngày hôm nay và ngày mai để đối chiếu lịch
    today_str = str(datetime.date.today())
    tomorrow_str = str(datetime.date.today() + datetime.timedelta(days=1))
    
    query = """
        SELECT p.MaPhong, p.SoPhong, lp.TenLoaiPhong, lp.GiaTien, p.TinhTrang, lp.HinhAnh,
               (SELECT kh.TenDangNhap FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP JOIN KhachHang kh ON ddp.MaKH = kh.MaKH WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC LIMIT 1) as NguoiDatCuoi,
               (SELECT ddp.NgayTra FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC LIMIT 1) as NgayTraDuKien,
               lp.SoLuongNguoi, lp.SoGiuong,
               -- LOGIC MỚI: Quét bảng lịch đặt để xem hôm nay có khách không
               CASE 
                   WHEN p.MaPhong IN (
                       SELECT ctdp.MaPhong 
                       FROM ChiTietDatPhong ctdp
                       JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP
                       WHERE ddp.TinhTrangDon != 'Đã hủy'
                       AND (ddp.NgayDat < ? AND ddp.NgayTra > ?)
                   ) THEN 0 
                   WHEN p.TinhTrang != 'Sẵn sàng' THEN 0
                   ELSE 1 
               END as IsReallyAvailable
        FROM Phong p
        JOIN LoaiPhong lp ON p.MaLoaiPhong = lp.MaLoaiPhong
    """
    
    cursor.execute(query, (tomorrow_str, today_str))
    rows = cursor.fetchall()
    
    import random
    
    rooms = []
    for row in rows:
        # Sử dụng trạng thái thật (thay vì trạng thái ảo trong DB)
        is_available = bool(row[10])
        status = 'Sẵn sàng' if is_available else 'Đang có khách'
        
        nguoi_dat = row[6]
        ngay_tra = row[7]
        
        is_my_room = True if (not is_available and username != "" and nguoi_dat == username) else False
        
        if not is_available and not ngay_tra:
            ngay_tra = datetime.date.today() + datetime.timedelta(days=random.randint(1, 3))
            
        ngay_tra_str = ngay_tra.strftime('%d/%m/%Y') if ngay_tra else ""
        
        rooms.append({
            "id": row[0],
            "roomNumber": row[1],
            "name": row[2],
            "price": float(row[3]),
            "status": status,
            "image": row[5],
            "isAvailable": is_available,
            "isMyRoom": is_my_room,
            "availableFrom": ngay_tra_str,
            "maxPeople": row[8],
            "beds": row[9]
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
                       WHERE ddp.TinhTrangDon != 'Đã hủy'
                       AND (ddp.NgayDat < ? AND ddp.NgayTra > ?)
                   ) THEN 0 
                   WHEN p.TinhTrang != 'Sẵn sàng' THEN 0
                   ELSE 1 
               END as IsAvailableForDates,
               (SELECT kh.TenDangNhap FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP JOIN KhachHang kh ON ddp.MaKH = kh.MaKH WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC LIMIT 1) as NguoiDatCuoi,
               (SELECT ddp.NgayTra FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC LIMIT 1) as NgayTraDuKien,
               lp.SoLuongNguoi, lp.SoGiuong
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
            "availableFrom": ngay_tra_str,
            "maxPeople": row[9],
            "beds": row[10]
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
            WHERE c.MaPhong = ? AND d.TinhTrangDon IN ('Đang ở', 'Đã xác nhận')
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
        
        cursor.execute("SELECT MAX(CAST(SUBSTR(MaKH, 3, LENGTH(MaKH)) AS INT)) FROM KhachHang WHERE MaKH LIKE 'KH%'")
        max_id = cursor.fetchone()[0]
        ma_kh = "KH" + str((max_id if max_id is not None else 100) + 1)
        
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
        
        cursor.execute("SELECT MAX(CAST(SUBSTR(MaDDP, 4, LENGTH(MaDDP)) AS INT)) FROM DonDatPhong WHERE MaDDP LIKE 'DDP%'")
        max_id = cursor.fetchone()[0]
        ma_ddp = "DDP" + str((max_id if max_id is not None else 100) + 1)
        
        try:
            ngay_dat = datetime.datetime.fromisoformat(data.checkin)
            ngay_tra = datetime.datetime.fromisoformat(data.checkout)
        except Exception:
            ngay_dat = datetime.datetime.now()
            ngay_tra = ngay_dat + datetime.timedelta(days=1)

        cursor.execute(
            "INSERT INTO DonDatPhong (MaDDP, NgayDat, NgayTra, TongTien, TinhTrangDon, MaKH) VALUES (?, ?, ?, ?, 'Đã xác nhận', ?)",
            (ma_ddp, ngay_dat, ngay_tra, data.total_price, ma_kh)
        )
        cursor.execute("INSERT INTO ChiTietDatPhong (MaPhong, MaDDP) VALUES (?, ?)", (data.room_id, ma_ddp))
        
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
def admin_get_rooms(keyword: str = Query("")):
    conn, cursor = get_db_cursor()
    today_str = str(datetime.date.today())
    tomorrow_str = str(datetime.date.today() + datetime.timedelta(days=1))
    query = """
        SELECT p.MaPhong, p.SoPhong, lp.TenLoaiPhong, 
               CASE 
                   WHEN p.MaPhong IN (
                       SELECT ctdp.MaPhong 
                       FROM ChiTietDatPhong ctdp
                       JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP
                       WHERE ddp.TinhTrangDon != 'Đã hủy'
                       AND (ddp.NgayDat < ? AND ddp.NgayTra > ?)
                   ) THEN 'Đang có khách' 
                   WHEN p.TinhTrang != 'Sẵn sàng' THEN p.TinhTrang
                   ELSE 'Sẵn sàng' 
               END as TinhTrang, 
               lp.GiaTien, p.MaLoaiPhong
        FROM Phong p
        JOIN LoaiPhong lp ON p.MaLoaiPhong = lp.MaLoaiPhong
    """
    params = [tomorrow_str, today_str]
    if keyword:
        query += " WHERE p.MaPhong LIKE ? OR p.SoPhong LIKE ?"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
        cursor.execute(query, params)
    else:
        cursor.execute(query, params)
        
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
       
        cursor.execute("SELECT MAX(CAST(SUBSTR(MaLoaiPhong, 3, LENGTH(MaLoaiPhong)) AS INT)) FROM LoaiPhong WHERE MaLoaiPhong LIKE 'LP%'")
        max_id = cursor.fetchone()[0]
        ma_loai = "LP" + str((max_id if max_id is not None else 100) + 1)
        
     
        cursor.execute(
            "INSERT INTO LoaiPhong (MaLoaiPhong, TenLoaiPhong, MoTa, SoLuongNguoi, SoGiuong, GiaTien) VALUES (?, ?, ?, ?, ?, ?)",
            (ma_loai, data.ten_loai_phong, data.mo_ta, data.so_luong_nguoi, data.so_giuong, data.gia_tien)
        )
        
        conn.commit()
        return {"status": "success", "id": ma_loai}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: 
        conn.close()

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
        raise HTTPException(status_code=500, detail="Không thể xóa do vẫn còn phòng thuộc loại này.")
    finally: conn.close()

@app.post("/api/admin/bookings/create")
def admin_create_booking(data: AdminBookingModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("SELECT MaKH FROM KhachHang WHERE TenDangNhap = ?", (data.username,))
        kh_row = cursor.fetchone()
        
        if not kh_row:
            import time
            unique_username = f"walkin_{int(time.time())}"
            cursor.execute("INSERT INTO TaiKhoan (TenDangNhap, MatKhau) VALUES (?, ?)", (unique_username, unique_username))
            cursor.execute("INSERT INTO TaiKhoan_VaiTro (TenDangNhap, MaVaiTro) VALUES (?, 'ROLE_CUSTOMER')", (unique_username,))
            
            cursor.execute("SELECT MAX(CAST(SUBSTR(MaKH, 3, LENGTH(MaKH)) AS INT)) FROM KhachHang WHERE MaKH LIKE 'KH%'")
            max_kh_id = cursor.fetchone()[0]
            new_ma_kh = "KH" + str((max_kh_id if max_kh_id is not None else 0) + 1)
            
            ten_kh = data.fullname if data.fullname else "Khách vãng lai"
            sdt = data.phone if data.phone else "0000000000"
            cccd = data.idcard if data.idcard else "000000000000"
            
            cursor.execute(
                "INSERT INTO KhachHang (MaKH, HoTenKH, Email, SDT, DiaChi, CCCD, TenDangNhap) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (new_ma_kh, ten_kh, unique_username, sdt, 'Không', cccd, unique_username)
            )
            ma_kh = new_ma_kh
        else:
            ma_kh = kh_row[0]

        cursor.execute("SELECT MAX(CAST(SUBSTR(MaDDP, 4, LENGTH(MaDDP)) AS INT)) FROM DonDatPhong WHERE MaDDP LIKE 'DDP%'")
        max_id = cursor.fetchone()[0]
        ma_ddp = "DDP" + str((max_id if max_id is not None else 100) + 1)
        
        try:
            ngay_dat = datetime.datetime.fromisoformat(data.checkin)
            ngay_tra = datetime.datetime.fromisoformat(data.checkout)
        except Exception:
            ngay_dat = datetime.datetime.now()
            ngay_tra = ngay_dat + datetime.timedelta(days=1)

        cursor.execute(
            "INSERT INTO DonDatPhong (MaDDP, NgayDat, NgayTra, TongTien, TinhTrangDon, MaKH) VALUES (?, ?, ?, ?, 'Đã xác nhận', ?)",
            (ma_ddp, ngay_dat, ngay_tra, data.total_price, ma_kh)
        )
        cursor.execute("INSERT INTO ChiTietDatPhong (MaPhong, MaDDP) VALUES (?, ?)", (data.room_id, ma_ddp))
        cursor.execute("UPDATE Phong SET TinhTrang = 'Đang có khách' WHERE MaPhong = ?", (data.room_id,))
        
        for svc_id in data.services:
            cursor.execute("INSERT INTO ChiTietSuDungDV (MaDV, MaDDP, SoLuong) VALUES (?, ?, 1)", (svc_id, ma_ddp))
                
        conn.commit()
        return {"status": "success", "ma_ddp": ma_ddp}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
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
        cursor.execute("SELECT TenKS, SDT, DiaChi, Email FROM KhachSan LIMIT 1")
        r = cursor.fetchone()
        conn.close()
        extra = get_extra_settings()
        if r: return {"name": r[0], "phone": r[1], "address": r[2], "checkin": extra["checkin"], "checkout": extra["checkout"], "vat": extra["vat"]}
        return {"name": "HUCE HOTEL", "phone": "1900 1234", "address": "55 Giải Phóng", "checkin": extra["checkin"], "checkout": extra["checkout"], "vat": extra["vat"]}
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
        save_extra_settings(data.checkin, data.checkout, data.vat)
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
        # 1. KIỂM TRA TRÙNG SỐ PHÒNG
        cursor.execute("SELECT SoPhong FROM Phong WHERE SoPhong = ?", (data.so_phong,))
        if cursor.fetchone():
            # Trả về lỗi 400 để app.js bắt và hiện thông báo màu đỏ
            raise HTTPException(status_code=400, detail=f"Số phòng {data.so_phong} đã tồn tại trong hệ thống!")

        # 2. TẠO MÃ PHÒNG THÔNG MINH (Không dùng COUNT nữa để tránh trùng khi xóa)
        cursor.execute("SELECT MaPhong FROM Phong")
        max_id = 100
        for r in cursor.fetchall():
            try:
                num = int(r[0].replace("P", "").strip())
                if num > max_id:
                    max_id = num
            except:
                pass
        ma_phong = "P" + str(max_id + 1)
        
        # 3. THÊM VÀO DATABASE
        cursor.execute(
            "INSERT INTO Phong (MaPhong, SoPhong, TinhTrang, MaLoaiPhong, MaKS) VALUES (?, ?, ?, ?, 'KS01')",
            (ma_phong, data.so_phong, data.tinh_trang, data.ma_loai_phong)
        )
        conn.commit()
        return {"status": "success"}
    
    except HTTPException:
        raise # Giữ nguyên lỗi 400 nếu bị trùng số phòng
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: 
        conn.close()
@app.put("/api/admin/rooms/{room_id}")
def admin_edit_room(room_id: str, data: RoomActionModel):
    conn, cursor = get_db_cursor()
    try:
        # Kiểm tra xem số phòng mới nhập vào có bị trùng với phòng KHÁC không
        cursor.execute("SELECT MaPhong FROM Phong WHERE SoPhong = ? AND MaPhong != ?", (data.so_phong, room_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Số phòng {data.so_phong} đang được phòng khác sử dụng!")

        cursor.execute(
            "UPDATE Phong SET SoPhong = ?, MaLoaiPhong = ?, TinhTrang = ? WHERE MaPhong = ?",
            (data.so_phong, data.ma_loai_phong, data.tinh_trang, room_id)
        )
        conn.commit()
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: 
        conn.close()
@app.delete("/api/admin/rooms/{room_id}")
def admin_delete_room(room_id: str):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("DELETE FROM Phong WHERE MaPhong = ?", (room_id,))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Không thể xóa do phòng đã có lịch sử đặt.")
    finally: conn.close()

@app.post("/api/admin/services")
def admin_add_service(data: ServiceActionModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("SELECT MAX(CAST(SUBSTR(MaDV, 3, LENGTH(MaDV)) AS INT)) FROM DichVu WHERE MaDV LIKE 'DV%'")
        max_id = cursor.fetchone()[0]
        ma_dv = "DV" + str((max_id if max_id is not None else 100) + 1)
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

class CancelBookingModel(BaseModel):
    ma_ddp: str
    username: str

class PaymentModel(BaseModel):
    ma_ddp: str
    phuong_thuc: str
    username: str

@app.post("/api/bookings/cancel")
def cancel_booking(data: CancelBookingModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("""
            SELECT ddp.TinhTrangDon, ctdp.MaPhong, ddp.NgayDat
            FROM DonDatPhong ddp
            JOIN KhachHang kh ON ddp.MaKH = kh.MaKH
            JOIN ChiTietDatPhong ctdp ON ddp.MaDDP = ctdp.MaDDP
            WHERE ddp.MaDDP = ? AND kh.TenDangNhap = ?
        """, (data.ma_ddp, data.username))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=403, detail="Không tìm thấy đơn hoặc bạn không có quyền hủy đơn này")
        tinh_trang, ma_phong, ngay_dat = row
        
        if type(ngay_dat) == str:
            try: ngay_dat = datetime.datetime.fromisoformat(ngay_dat)
            except: pass
            
        if isinstance(ngay_dat, datetime.datetime) or hasattr(ngay_dat, 'timestamp'):
            if (ngay_dat - datetime.datetime.now()).total_seconds() < 24 * 3600:
                raise HTTPException(status_code=400, detail="Không thể hủy phòng trong vòng 24h trước giờ nhận phòng. Vui lòng gọi lễ tân!")

        if tinh_trang != 'Đã xác nhận':
            raise HTTPException(status_code=400, detail=f"Không thể hủy đơn đang ở trạng thái '{tinh_trang}'")
        cursor.execute("UPDATE DonDatPhong SET TinhTrangDon = 'Đã hủy' WHERE MaDDP = ?", (data.ma_ddp,))
        conn.commit()
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()

@app.post("/api/bookings/payment")
def payment_booking(data: PaymentModel):
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("""
            SELECT ddp.TinhTrangDon
            FROM DonDatPhong ddp
            JOIN KhachHang kh ON ddp.MaKH = kh.MaKH
            WHERE ddp.MaDDP = ? AND kh.TenDangNhap = ?
        """, (data.ma_ddp, data.username))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=403, detail="Không tìm thấy đơn hoặc bạn không có quyền thanh toán đơn này")
        if row[0] != 'Đã xác nhận':
            raise HTTPException(status_code=400, detail=f"Không thể thanh toán đơn đang ở trạng thái '{row[0]}'")
        cursor.execute("UPDATE DonDatPhong SET TinhTrangDon = 'Đã thanh toán' WHERE MaDDP = ?", (data.ma_ddp,))
        conn.commit()
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally: conn.close()