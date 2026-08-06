from fastapi import APIRouter, HTTPException
from database import get_db
from schemas import ReviewSubmitModel
import datetime

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

@router.get("")
async def get_all_reviews():
    db = get_db()
    
    cursor_users = db.users.find()
    users_dict = {u["_id"]: u for u in await cursor_users.to_list(length=None)}
    
    cursor_hotels = db.hotels.find()
    hotels_dict = {h["_id"]: h for h in await cursor_hotels.to_list(length=None)}
    
    cursor_reviews = db.reviews.find().sort([("_id", -1)])
    rows = await cursor_reviews.to_list(length=None)
    
    reviews = []
    for r in rows:
        kh = users_dict.get(r.get("MaKH"), {})
        ks = hotels_dict.get(r.get("MaKS"), {})
        
        # Determine names
        customer_name = kh.get("HoTenKH") if kh.get("HoTenKH") else r.get("HoTenKhach", "")
        hotel_name = ks.get("TenKS", "")
        
        ngay_dg = r.get("NgayDanhGia")
        if isinstance(ngay_dg, datetime.datetime) or isinstance(ngay_dg, datetime.date):
            date_str = ngay_dg.strftime('%d/%m/%Y')
        else:
            date_str = str(ngay_dg)[:10] if ngay_dg else ""
            
        reviews.append({
            "customerName": customer_name,
            "date": date_str,
            "stars": r.get("SoSao", 5),
            "content": r.get("NoiDung", ""),
            "image": r.get("HinhAnh", ""),
            "hotelName": hotel_name
        })
    return reviews

@router.post("/submit")
async def submit_review(data: ReviewSubmitModel):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Nội dung đánh giá không được để trống")

    db = get_db()
    try:
        ma_kh = None
        if data.username:
            user = await db.users.find_one({"_id": data.username})
            if user:
                ma_kh = data.username

        ngay_hien_tai = datetime.datetime.now()
        
        await db.reviews.insert_one({
            "HoTenKhach": data.customer_name,
            "NgayDanhGia": ngay_hien_tai,
            "SoSao": data.stars,
            "NoiDung": data.content,
            "TenDangNhap": data.username,
            "HinhAnh": data.image,
            "MaKH": ma_kh,
            "MaKS": data.ma_ks
        })
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
