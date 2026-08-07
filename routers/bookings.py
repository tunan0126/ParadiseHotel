from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from schemas import BookingModel, CancelBookingModel, PaymentModel
import datetime

from security import get_current_user

router = APIRouter(prefix="/api/bookings", tags=["bookings"], dependencies=[Depends(get_current_user)])

@router.post("")
async def create_booking(data: BookingModel):
    db = get_db()
    try:
        user = await db.users.find_one({"_id": data.username})
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông tin khách")
        
        # Get next booking ID
        cursor = db.bookings.find().sort([("_id", -1)]).limit(1)
        last_booking_list = await cursor.to_list(length=1)
        max_id = 100
        if last_booking_list and "_id" in last_booking_list[0]:
            try:
                ma_ddp_str = last_booking_list[0]["_id"]
                if ma_ddp_str.startswith("DDP"):
                    max_id = int(ma_ddp_str[3:])
            except: pass
            
        ma_ddp = "DDP" + str(max_id + 1)
        
        if not data.checkin or not data.checkin.strip() or not data.checkout or not data.checkout.strip():
            raise HTTPException(status_code=400, detail="Vui lòng chọn ngày nhận phòng và ngày trả phòng")
        
        try:
            ngay_dat = datetime.datetime.fromisoformat(data.checkin)
            ngay_tra = datetime.datetime.fromisoformat(data.checkout)
        except Exception:
            raise HTTPException(status_code=400, detail="Ngày nhận phòng hoặc ngày trả phòng không hợp lệ")
        
        if ngay_tra <= ngay_dat:
            raise HTTPException(status_code=400, detail="Ngày trả phòng phải sau ngày nhận phòng")


        dich_vu_list = []
        for svc_name in data.services:
            svc = await db.services.find_one({"TenDV": svc_name})
            if svc:
                dich_vu_list.append({"MaDV": svc["_id"], "SoLuong": 1})

        booking = {
            "_id": ma_ddp,
            "NgayDat": ngay_dat,
            "NgayTra": ngay_tra,
            "TongTien": data.total_price,
            "TinhTrangDon": "Đã xác nhận",
            "MaKH": data.username,
            "Phong": [data.room_id],
            "DichVu": dich_vu_list
        }
        
        await db.bookings.insert_one(booking)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel")
async def cancel_booking(data: CancelBookingModel):
    db = get_db()
    try:
        booking = await db.bookings.find_one({"_id": data.ma_ddp, "MaKH": data.username})
        if not booking:
            raise HTTPException(status_code=403, detail="Không tìm thấy đơn hoặc bạn không có quyền hủy đơn này")
            
        tinh_trang = booking.get("TinhTrangDon")
        ngay_dat = booking.get("NgayDat")
        
        if isinstance(ngay_dat, str):
            try: ngay_dat = datetime.datetime.fromisoformat(ngay_dat)
            except: pass
            
        if isinstance(ngay_dat, datetime.datetime) or hasattr(ngay_dat, 'timestamp'):
            if (ngay_dat - datetime.datetime.now()).total_seconds() < 24 * 3600:
                raise HTTPException(status_code=400, detail="Không thể hủy phòng trong vòng 24h trước giờ nhận phòng. Vui lòng gọi lễ tân!")

        if tinh_trang != 'Đã xác nhận':
            raise HTTPException(status_code=400, detail=f"Không thể hủy đơn đang ở trạng thái '{tinh_trang}'")
            
        await db.bookings.update_one({"_id": data.ma_ddp}, {"$set": {"TinhTrangDon": "Đã hủy"}})
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payment")
async def payment_booking(data: PaymentModel):
    db = get_db()
    try:
        booking = await db.bookings.find_one({"_id": data.ma_ddp, "MaKH": data.username})
        if not booking:
            raise HTTPException(status_code=403, detail="Không tìm thấy đơn hoặc bạn không có quyền thanh toán đơn này")
            
        if booking.get("TinhTrangDon") != 'Đã xác nhận':
            raise HTTPException(status_code=400, detail=f"Không thể thanh toán đơn đang ở trạng thái '{booking.get('TinhTrangDon')}'")
            
        await db.bookings.update_one({"_id": data.ma_ddp}, {"$set": {"TinhTrangDon": "Đã thanh toán"}})
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
