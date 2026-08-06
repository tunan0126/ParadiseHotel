from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from schemas import ProfileUpdateModel, PasswordUpdateModel

from security import get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/profile", tags=["profile"], dependencies=[Depends(get_current_user)])

@router.get("")
async def get_profile(username: str):
    db = get_db()
    r = await db.users.find_one({"_id": username})
    if not r: raise HTTPException(status_code=404, detail="Không tìm thấy")
    return {"fullname": r.get("HoTenKH", ""), "email": r.get("Email", ""), "phone": r.get("SDT", ""), "address": r.get("DiaChi", ""), "idcard": r.get("CCCD", "")}

@router.post("/update")
async def update_profile(data: ProfileUpdateModel):
    db = get_db()
    try:
        await db.users.update_one({"_id": data.username}, {"$set": {
            "HoTenKH": data.fullname,
            "SDT": data.phone,
            "CCCD": data.idcard,
            "DiaChi": data.address
        }})
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/password")
async def update_password(data: PasswordUpdateModel):
    db = get_db()
    try:
        user = await db.users.find_one({"_id": data.username})
        
        if not user or (not verify_password(data.old_password, user.get("MatKhau", "")) and data.old_password != user.get("MatKhau")):
            raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác!")
        
        hashed_new_password = hash_password(data.new_password)
        await db.users.update_one({"_id": data.username}, {"$set": {"MatKhau": hashed_new_password}})
        return {"status": "success", "message": "Đổi mật khẩu thành công!"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_booking_history(username: str):
    db = get_db()
    
    cursor_rooms = db.rooms.find()
    rooms_dict = {r["_id"]: r for r in await cursor_rooms.to_list(length=None)}
    
    cursor_rt = db.room_types.find()
    room_types_dict = {rt["_id"]: rt for rt in await cursor_rt.to_list(length=None)}
    
    cursor_bk = db.bookings.find({"MaKH": username})
    bookings = await cursor_bk.to_list(length=None)
    
    res = []
    for b in bookings:
        room_ids = b.get("Phong", [])
        room_name = ""
        if room_ids:
            room = rooms_dict.get(room_ids[0])
            if room:
                rt = room_types_dict.get(room.get("MaLoaiPhong"))
                if rt:
                    room_name = rt.get("TenLoaiPhong", "")
                    
        res.append({
            "id": b["_id"],
            "roomName": room_name,
            "checkin": str(b.get("NgayDat")),
            "checkout": str(b.get("NgayTra")),
            "status": b.get("TinhTrangDon", ""),
            "totalPrice": float(b.get("TongTien", 0))
        })
    return res

@router.get("/services")
async def get_used_services(username: str):
    db = get_db()
    cursor_svc = db.services.find()
    services_dict = {s["_id"]: s for s in await cursor_svc.to_list(length=None)}
    
    cursor_bk = db.bookings.find({"MaKH": username})
    bookings = await cursor_bk.to_list(length=None)
    
    res = []
    for b in bookings:
        for d in b.get("DichVu", []):
            svc_id = d.get("MaDV")
            svc = services_dict.get(svc_id, {})
            svc_name = svc.get("TenDV", "")
            svc_price = svc.get("GiaDV", 0)
            qty = d.get("SoLuong", 1)
            
            res.append({
                "id": b["_id"],
                "serviceName": svc_name,
                "date": str(b.get("NgayDat")),
                "quantity": qty,
                "total": float(svc_price * qty)
            })
    return res
