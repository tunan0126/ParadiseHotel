from fastapi import APIRouter, HTTPException
from database import get_db
import datetime
import random

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

@router.get("")
async def get_rooms(username: str = ""):
    db = get_db()
    
    today = datetime.datetime.now()
    today_str = str(datetime.date.today())
    tomorrow_str = str(datetime.date.today() + datetime.timedelta(days=1))
    
    ci_date = datetime.datetime.strptime(today_str, "%Y-%m-%d")
    co_date = datetime.datetime.strptime(tomorrow_str, "%Y-%m-%d")

    cursor = db.rooms.find()
    rooms_data = await cursor.to_list(length=None)
    
    rt_cursor = db.room_types.find()
    room_types_data = {rt["_id"]: rt for rt in await rt_cursor.to_list(length=None)}
    
    # Active bookings
    bookings_cursor = db.bookings.find({
        "TinhTrangDon": {"$ne": "Đã hủy"}
    }).sort([("_id", -1)])
    bookings_data = await bookings_cursor.to_list(length=None)
    
    rooms = []
    for r in rooms_data:
        room_id = r["_id"]
        rt = room_types_data.get(r["MaLoaiPhong"], {})
        
        # Determine if booked
        is_available = True
        nguoi_dat = None
        ngay_tra = None
        
        for b in bookings_data:
            if room_id in b.get("Phong", []):
                b_start = b.get("NgayDat")
                b_end = b.get("NgayTra")
                
                if isinstance(b_start, str):
                    try: b_start = datetime.datetime.fromisoformat(b_start)
                    except: pass
                if isinstance(b_end, str):
                    try: b_end = datetime.datetime.fromisoformat(b_end)
                    except: pass
                
                if b_start and b_end:
                    # Check overlap
                    if b_start < co_date and b_end > ci_date:
                        is_available = False
                        
                if not nguoi_dat:
                    nguoi_dat = b.get("MaKH")
                if not ngay_tra:
                    ngay_tra = b_end
                    
        if r.get("TinhTrang") != 'Sẵn sàng':
            is_available = False
            
        status = 'Sẵn sàng' if is_available else 'Đang có khách'
        is_my_room = True if (not is_available and username != "" and nguoi_dat == username) else False
        
        if not is_available and not ngay_tra:
            ngay_tra = today + datetime.timedelta(days=random.randint(1, 3))
            
        if isinstance(ngay_tra, datetime.datetime):
            ngay_tra_str = ngay_tra.strftime('%d/%m/%Y')
        else:
            ngay_tra_str = str(ngay_tra)[:10] if ngay_tra else ""
            
        rooms.append({
            "id": room_id,
            "roomNumber": r.get("SoPhong", ""),
            "name": rt.get("TenLoaiPhong", ""),
            "price": float(rt.get("GiaTien", 0)),
            "status": status,
            "image": rt.get("HinhAnh", ""),
            "isAvailable": is_available,
            "isMyRoom": is_my_room,
            "availableFrom": ngay_tra_str,
            "maxPeople": rt.get("SoLuongNguoi", 0),
            "beds": rt.get("SoGiuong", 0)
        })
    return rooms

@router.get("/search")
async def search_available_rooms(
    checkin: str = "", checkout: str = "", guests: int = 1, room_type: str = "all",
    min_price: float = 0, max_price: float = 999999999, username: str = ""
):
    db = get_db()
    
    ci_str = checkin if checkin else str(datetime.date.today())
    co_str = checkout if checkout else str(datetime.date.today() + datetime.timedelta(days=1))
    
    try:
        ci_date = datetime.datetime.strptime(ci_str, "%Y-%m-%d")
        co_date = datetime.datetime.strptime(co_str, "%Y-%m-%d")
    except:
        ci_date = datetime.datetime.now()
        co_date = ci_date + datetime.timedelta(days=1)

    cursor = db.rooms.find()
    rooms_data = await cursor.to_list(length=None)
    
    rt_cursor = db.room_types.find()
    room_types_data = {rt["_id"]: rt for rt in await rt_cursor.to_list(length=None)}
    
    bookings_cursor = db.bookings.find({
        "TinhTrangDon": {"$ne": "Đã hủy"}
    }).sort([("_id", -1)])
    bookings_data = await bookings_cursor.to_list(length=None)
    
    rooms = []
    for r in rooms_data:
        room_id = r["_id"]
        rt = room_types_data.get(r["MaLoaiPhong"], {})
        
        # Apply filters
        if rt.get("SoLuongNguoi", 0) < guests:
            continue
        price = float(rt.get("GiaTien", 0))
        if price < min_price or price > max_price:
            continue
        if room_type != "all" and rt.get("TenLoaiPhong") != room_type:
            continue
            
        is_available = True
        nguoi_dat = None
        ngay_tra = None
        
        for b in bookings_data:
            if room_id in b.get("Phong", []):
                b_start = b.get("NgayDat")
                b_end = b.get("NgayTra")
                
                if isinstance(b_start, str):
                    try: b_start = datetime.datetime.fromisoformat(b_start)
                    except: pass
                if isinstance(b_end, str):
                    try: b_end = datetime.datetime.fromisoformat(b_end)
                    except: pass
                
                if b_start and b_end:
                    if b_start < co_date and b_end > ci_date:
                        is_available = False
                        
                if not nguoi_dat:
                    nguoi_dat = b.get("MaKH")
                if not ngay_tra:
                    ngay_tra = b_end
                    
        if r.get("TinhTrang") != 'Sẵn sàng':
            is_available = False
            
        status = 'Sẵn sàng' if is_available else 'Đang có khách'
        is_my_room = True if (not is_available and username != "" and nguoi_dat == username) else False
        
        if not is_available and not ngay_tra:
            ngay_tra = datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 3))
            
        if isinstance(ngay_tra, datetime.datetime):
            ngay_tra_str = ngay_tra.strftime('%d/%m/%Y')
        else:
            ngay_tra_str = str(ngay_tra)[:10] if ngay_tra else ""

        rooms.append({
            "id": room_id,
            "roomNumber": r.get("SoPhong", ""),
            "name": rt.get("TenLoaiPhong", ""),
            "price": price,
            "status": status,
            "image": rt.get("HinhAnh", ""),
            "isAvailable": is_available,
            "isMyRoom": is_my_room,
            "availableFrom": ngay_tra_str,
            "maxPeople": rt.get("SoLuongNguoi", 0),
            "beds": rt.get("SoGiuong", 0)
        })
    return rooms

@router.get("/{room_id}/booked-dates")
async def get_booked_dates(room_id: str):
    db = get_db()
    try:
        cursor = db.bookings.find({
            "Phong": room_id,
            "TinhTrangDon": {"$in": ["Đang ở", "Đã xác nhận"]}
        })
        bookings = await cursor.to_list(length=None)
        
        booked_dates = []
        for b in bookings:
            start_date = b.get("NgayDat")
            end_date = b.get("NgayTra")
            
            if isinstance(start_date, datetime.datetime):
                s_str = start_date.strftime("%Y-%m-%d")
            else:
                s_str = str(start_date)[:10]
                
            if isinstance(end_date, datetime.datetime):
                e_str = end_date.strftime("%Y-%m-%d")
            else:
                e_str = str(end_date)[:10]
                
            booked_dates.append({
                "from": s_str,
                "to": e_str
            })
            
        return booked_dates
    except Exception as e:
        print(f"Lỗi truy vấn lịch bận: {e}")
        return []

