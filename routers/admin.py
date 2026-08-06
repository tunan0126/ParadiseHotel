from fastapi import APIRouter, HTTPException, Depends, Query
from database import get_db, get_extra_settings, save_extra_settings
from schemas import (
    AdminBookingModel, SettingsUpdateModel, RoomActionModel,
    RoomTypeActionModel, ServiceActionModel
)
import datetime
import time

from security import get_current_user

public_router = APIRouter(prefix="/api/admin", tags=["admin-public"])
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_current_user)])

@router.get("/stats/summary")
async def get_stats_summary():
    db = get_db()
    try:
        total_rooms = await db.rooms.count_documents({})
        total_services = await db.services.count_documents({})
        return {"total_rooms": total_rooms, "total_services": total_services}
    except Exception as e:
        return {"total_rooms": 0, "total_services": 0}
    
@router.get("/rooms/search")
async def admin_search_rooms(keyword: str = Query("")):
    return await admin_get_rooms(keyword)

@router.get("/rooms")
async def admin_get_rooms(keyword: str = Query("")):
    db = get_db()
    today_str = str(datetime.date.today())
    tomorrow_str = str(datetime.date.today() + datetime.timedelta(days=1))
    
    ci_date = datetime.datetime.strptime(today_str, "%Y-%m-%d")
    co_date = datetime.datetime.strptime(tomorrow_str, "%Y-%m-%d")
    
    rooms_filter = {}
    if keyword:
        rooms_filter = {"$or": [
            {"_id": {"$regex": keyword, "$options": "i"}},
            {"SoPhong": {"$regex": keyword, "$options": "i"}}
        ]}
        
    cursor_rooms = db.rooms.find(rooms_filter)
    rooms_data = await cursor_rooms.to_list(length=None)
    
    cursor_rt = db.room_types.find()
    room_types_data = {rt["_id"]: rt for rt in await cursor_rt.to_list(length=None)}
    
    cursor_bookings = db.bookings.find({
        "TinhTrangDon": {"$ne": "Đã hủy"}
    }).sort([("_id", -1)])
    bookings_data = await cursor_bookings.to_list(length=None)
    
    res = []
    for r in rooms_data:
        room_id = r["_id"]
        rt = room_types_data.get(r.get("MaLoaiPhong"), {})
        
        tinh_trang = r.get("TinhTrang", "Sẵn sàng")
        if tinh_trang == "Sẵn sàng":
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
                            tinh_trang = 'Đang có khách'
                            break
                            
        res.append({
            "id": room_id,
            "roomNumber": r.get("SoPhong", ""),
            "name": rt.get("TenLoaiPhong", ""),
            "status": tinh_trang,
            "price": float(rt.get("GiaTien", 0)),
            "maLoai": r.get("MaLoaiPhong", "")
        })
    return res

@router.post("/rooms")
async def admin_add_room(data: RoomActionModel):
    db = get_db()
    existing = await db.rooms.find_one({"SoPhong": data.so_phong})
    if existing:
        raise HTTPException(status_code=400, detail=f"Số phòng {data.so_phong} đã tồn tại trong hệ thống!")

    max_id = 100
    cursor = db.rooms.find({}, {"_id": 1})
    for r in await cursor.to_list(length=None):
        try:
            num = int(r["_id"].replace("P", "").strip())
            if num > max_id:
                max_id = num
        except: pass
        
    ma_phong = "P" + str(max_id + 1)
    await db.rooms.insert_one({
        "_id": ma_phong,
        "SoPhong": data.so_phong,
        "TinhTrang": data.tinh_trang,
        "MaLoaiPhong": data.ma_loai_phong,
        "MaKS": "KS01"
    })
    return {"status": "success"}

@router.put("/rooms/{room_id}")
async def admin_edit_room(room_id: str, data: RoomActionModel):
    db = get_db()
    existing = await db.rooms.find_one({"SoPhong": data.so_phong, "_id": {"$ne": room_id}})
    if existing:
        raise HTTPException(status_code=400, detail=f"Số phòng {data.so_phong} đang được phòng khác sử dụng!")

    await db.rooms.update_one({"_id": room_id}, {"$set": {
        "SoPhong": data.so_phong,
        "MaLoaiPhong": data.ma_loai_phong,
        "TinhTrang": data.tinh_trang
    }})
    return {"status": "success"}

@router.delete("/rooms/{room_id}")
async def admin_delete_room(room_id: str):
    db = get_db()
    used = await db.bookings.find_one({"Phong": room_id})
    if used:
        raise HTTPException(status_code=500, detail="Không thể xóa do phòng đã có lịch sử đặt.")
    await db.rooms.delete_one({"_id": room_id})
    return {"status": "success"}

@router.post("/rooms/status/{room_id}")
async def admin_change_room_status(room_id: str):
    db = get_db()
    room = await db.rooms.find_one({"_id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Không thấy phòng")
    
    current_status = room.get("TinhTrang")
    if current_status == 'Sẵn sàng': next_status = 'Đang có khách'
    elif current_status == 'Đang có khách': next_status = 'Đang dọn dẹp'
    else: next_status = 'Sẵn sàng'
    
    await db.rooms.update_one({"_id": room_id}, {"$set": {"TinhTrang": next_status}})
    return {"status": "success", "next_status": next_status}

@router.get("/room-types")
async def admin_get_room_types(keyword: str = Query("")):
    db = get_db()
    filter_q = {}
    if keyword:
        filter_q = {"$or": [
            {"_id": {"$regex": keyword, "$options": "i"}},
            {"TenLoaiPhong": {"$regex": keyword, "$options": "i"}}
        ]}
    cursor = db.room_types.find(filter_q)
    rows = await cursor.to_list(length=None)
    return [{"id": r["_id"], "name": r.get("TenLoaiPhong", ""), "moTa": r.get("MoTa", ""), "maxPeople": r.get("SoLuongNguoi", 0), "price": float(r.get("GiaTien", 0)), "beds": r.get("SoGiuong", 1)} for r in rows]

@router.post("/room-types")
async def admin_add_room_type(data: RoomTypeActionModel):
    db = get_db()
    max_id = 100
    cursor = db.room_types.find({}, {"_id": 1})
    for r in await cursor.to_list(length=None):
        try:
            if r["_id"].startswith("LP"):
                num = int(r["_id"][2:])
                if num > max_id: max_id = num
        except: pass
    ma_loai = "LP" + str(max_id + 1)
    
    await db.room_types.insert_one({
        "_id": ma_loai,
        "TenLoaiPhong": data.ten_loai_phong,
        "MoTa": data.mo_ta,
        "SoLuongNguoi": data.so_luong_nguoi,
        "SoGiuong": data.so_giuong,
        "GiaTien": data.gia_tien
    })
    return {"status": "success", "id": ma_loai}

@router.put("/room-types/{type_id}")
async def admin_edit_room_type(type_id: str, data: RoomTypeActionModel):
    db = get_db()
    await db.room_types.update_one({"_id": type_id}, {"$set": {
        "TenLoaiPhong": data.ten_loai_phong,
        "MoTa": data.mo_ta,
        "SoLuongNguoi": data.so_luong_nguoi,
        "SoGiuong": data.so_giuong,
        "GiaTien": data.gia_tien
    }})
    return {"status": "success"}

@router.delete("/room-types/{type_id}")
async def admin_delete_room_type(type_id: str):
    db = get_db()
    used = await db.rooms.find_one({"MaLoaiPhong": type_id})
    if used:
        raise HTTPException(status_code=500, detail="Không thể xóa do vẫn còn phòng thuộc loại này.")
    await db.room_types.delete_one({"_id": type_id})
    return {"status": "success"}

@router.post("/bookings/create")
async def admin_create_booking(data: AdminBookingModel):
    db = get_db()
    try:
        user = await db.users.find_one({"_id": data.username})
        
        if not user:
            unique_username = f"walkin_{int(time.time())}"
            
            max_kh_id = 0
            cursor_users = db.users.find({}, {"MaKH": 1})
            for r in await cursor_users.to_list(length=None):
                try:
                    if r.get("MaKH", "").startswith("KH"):
                        num = int(r["MaKH"][2:])
                        if num > max_kh_id: max_kh_id = num
                except: pass
            
            new_ma_kh = "KH" + str(max_kh_id + 1)
            ten_kh = data.fullname if data.fullname else "Khách vãng lai"
            sdt = data.phone if data.phone else "0000000000"
            cccd = data.idcard if data.idcard else "000000000000"
            
            new_user = {
                "_id": unique_username,
                "MatKhau": unique_username,
                "MaVaiTro": "ROLE_CUSTOMER",
                "MaKH": new_ma_kh,
                "HoTenKH": ten_kh,
                "Email": unique_username,
                "SDT": sdt,
                "DiaChi": "Không",
                "CCCD": cccd
            }
            await db.users.insert_one(new_user)
            ma_kh = unique_username
        else:
            ma_kh = data.username

        max_ddp_id = 100
        cursor_bk = db.bookings.find({}, {"_id": 1})
        for r in await cursor_bk.to_list(length=None):
            try:
                if r["_id"].startswith("DDP"):
                    num = int(r["_id"][3:])
                    if num > max_ddp_id: max_ddp_id = num
            except: pass
        ma_ddp = "DDP" + str(max_ddp_id + 1)
        
        try:
            ngay_dat = datetime.datetime.fromisoformat(data.checkin)
            ngay_tra = datetime.datetime.fromisoformat(data.checkout)
        except Exception:
            ngay_dat = datetime.datetime.now()
            ngay_tra = ngay_dat + datetime.timedelta(days=1)

        dich_vu_list = [{"MaDV": svc_id, "SoLuong": 1} for svc_id in data.services]

        booking = {
            "_id": ma_ddp,
            "NgayDat": ngay_dat,
            "NgayTra": ngay_tra,
            "TongTien": data.total_price,
            "TinhTrangDon": "Đã xác nhận",
            "MaKH": ma_kh,
            "Phong": [data.room_id],
            "DichVu": dich_vu_list
        }
        
        await db.bookings.insert_one(booking)
        await db.rooms.update_one({"_id": data.room_id}, {"$set": {"TinhTrang": "Đang có khách"}})
        
        return {"status": "success", "ma_ddp": ma_ddp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bookings")
async def admin_get_bookings(keyword: str = Query("")):
    db = get_db()
    cursor_u = db.users.find()
    users_dict = {u["_id"]: u for u in await cursor_u.to_list(length=None)}
    
    cursor_b = db.bookings.find()
    bookings = await cursor_b.to_list(length=None)
    res = []
    for b in bookings:
        kh = users_dict.get(b.get("MaKH"), {})
        hoten = kh.get("HoTenKH", "Khách hàng")
        ma_ddp = b["_id"]
        
        if keyword and keyword.lower() not in ma_ddp.lower() and keyword.lower() not in hoten.lower():
            continue
            
        res.append({
            "id": ma_ddp,
            "customerName": hoten,
            "checkin": str(b.get("NgayDat")),
            "checkout": str(b.get("NgayTra")),
            "totalPrice": float(b.get("TongTien", 0)),
            "status": b.get("TinhTrangDon", "")
        })
    return res

@public_router.get("/services")
async def admin_get_services(keyword: str = Query("")):
    db = get_db()
    filter_q = {}
    if keyword:
        filter_q = {"$or": [
            {"_id": {"$regex": keyword, "$options": "i"}},
            {"TenDV": {"$regex": keyword, "$options": "i"}}
        ]}
    cursor = db.services.find(filter_q)
    rows = await cursor.to_list(length=None)
    return [{"id": r["_id"], "name": r.get("TenDV", ""), "category": "Tiện ích", "price": float(r.get("GiaDV", 0)), "status": "Hoạt động"} for r in rows]

@router.post("/services")
async def admin_add_service(data: ServiceActionModel):
    db = get_db()
    max_id = 100
    cursor = db.services.find({}, {"_id": 1})
    for r in await cursor.to_list(length=None):
        try:
            if r["_id"].startswith("DV"):
                num = int(r["_id"][2:])
                if num > max_id: max_id = num
        except: pass
    ma_dv = "DV" + str(max_id + 1)
    
    await db.services.insert_one({
        "_id": ma_dv,
        "TenDV": data.ten_dv,
        "GiaDV": data.gia_dv,
        "MaKS": "KS01"
    })
    return {"status": "success"}

@router.put("/services/{svc_id}")
async def admin_edit_service(svc_id: str, data: ServiceActionModel):
    db = get_db()
    await db.services.update_one({"_id": svc_id}, {"$set": {
        "TenDV": data.ten_dv,
        "GiaDV": data.gia_dv
    }})
    return {"status": "success"}

@router.delete("/services/{svc_id}")
async def admin_delete_service(svc_id: str):
    db = get_db()
    used = await db.bookings.find_one({"DichVu.MaDV": svc_id})
    if used:
        raise HTTPException(status_code=500, detail="Không thể xóa do dịch vụ đã được sử dụng.")
    await db.services.delete_one({"_id": svc_id})
    return {"status": "success"}

@public_router.get("/settings")
async def admin_get_settings():
    try:
        db = get_db()
        r = await db.hotels.find_one({"_id": "KS01"})
        extra = get_extra_settings()
        if r: return {"name": r.get("TenKS", ""), "phone": r.get("SDT", ""), "address": r.get("DiaChi", ""), "checkin": extra["checkin"], "checkout": extra["checkout"], "vat": extra["vat"]}
        return {"name": "HUCE HOTEL", "phone": "1900 1234", "address": "55 Giải Phóng", "checkin": extra["checkin"], "checkout": extra["checkout"], "vat": extra["vat"]}
    except Exception as e:
        return {"LOI_CUA_MAY_MOI_LA": str(e)}

@router.post("/settings")
async def admin_save_settings(data: SettingsUpdateModel):
    db = get_db()
    try:
        count = await db.hotels.count_documents({})
        if count == 0:
            await db.hotels.insert_one({"_id": "KS01", "TenKS": data.name, "DiaChi": data.address, "SDT": data.phone, "Email": data.address})
        else:
            await db.hotels.update_one({"_id": "KS01"}, {"$set": {"TenKS": data.name, "DiaChi": data.address, "SDT": data.phone}})
        save_extra_settings(data.checkin, data.checkout, data.vat)
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@public_router.get("/room-matrix")
async def get_room_matrix(days: int = Query(7)):
    db = get_db()
    try:
        today = datetime.date.today()
        dates = [(today + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
        
        cursor_rooms = db.rooms.find().sort("SoPhong", 1)
        rooms_rows = await cursor_rooms.to_list(length=None)
        
        cursor_rt = db.room_types.find()
        room_types_data = {rt["_id"]: rt for rt in await cursor_rt.to_list(length=None)}
        
        cursor_bk = db.bookings.find({"TinhTrangDon": {"$ne": "Đã hủy"}})
        booking_rows = await cursor_bk.to_list(length=None)
        
        cursor_u = db.users.find()
        users_dict = {u["_id"]: u for u in await cursor_u.to_list(length=None)}
        
        rooms = []
        for r in rooms_rows:
            r_id = r["_id"]
            r_num = r.get("SoPhong", "")
            r_type = room_types_data.get(r.get("MaLoaiPhong"), {}).get("TenLoaiPhong", "")
            r_status = r.get("TinhTrang", "Sẵn sàng")
            
            schedule = {}
            for d in dates:
                d_obj = datetime.datetime.strptime(d, "%Y-%m-%d").date()
                found_b = None
                for b in booking_rows:
                    if r_id in b.get("Phong", []):
                        b_in = b.get("NgayDat")
                        b_out = b.get("NgayTra")
                        
                        in_date = b_in if isinstance(b_in, datetime.date) else datetime.datetime.strptime(str(b_in)[:10], "%Y-%m-%d").date()
                        out_date = b_out if isinstance(b_out, datetime.date) else datetime.datetime.strptime(str(b_out)[:10], "%Y-%m-%d").date()
                        
                        if in_date <= d_obj < out_date:
                            b_status = b.get("TinhTrangDon")
                            b_guest_id = b.get("MaKH")
                            b_guest = users_dict.get(b_guest_id, {}).get("HoTenKH", "Khách")
                            
                            found_b = {"status": "occupied" if b_status in ['Đang ở', 'Đã xác nhận'] else "booked", "guest": b_guest, "booking_id": b["_id"]}
                            break
                if found_b:
                    schedule[d] = found_b
                else:
                    schedule[d] = {"status": "cleaning" if r_status == 'Đang dọn dẹp' else "available"}
            
            rooms.append({
                "id": r_id,
                "number": r_num,
                "type": r_type,
                "base_status": r_status,
                "schedule": schedule
            })
            
        return {"dates": dates, "rooms": rooms}
    except Exception as e:
        return {"dates": [], "rooms": [], "error": str(e)}

