from fastapi import APIRouter, HTTPException, Depends
from schemas import LoginModel, RegisterModel
from security import hash_password, verify_password, create_jwt_token, get_current_user
from database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
async def login(data: LoginModel):
    db = get_db()
    try:
        user = await db.users.find_one({"_id": data.username})
        
        if not user or not verify_password(data.password, user.get("MatKhau", "")):
            raise HTTPException(status_code=400, detail="Sai tên đăng nhập hoặc mật khẩu")
        
        role = user.get("MaVaiTro", "ROLE_CUSTOMER")
        
        access_token = create_jwt_token(payload={"sub": user["_id"], "role": role})
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "role": role,
            "username": user["_id"],
            "fullname": user.get("HoTenKH", user.get("TenNV", "User"))
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register")
async def register(data: RegisterModel):
    db = get_db()
    try:
        existing_user = await db.users.find_one({"_id": data.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
        
        hashed_password = hash_password(data.password)
        
        # Tạo mã khách hàng ngẫu nhiên, hoặc có thể lấy số cuối rồi cộng thêm
        max_id = 100
        cursor = db.users.find({}, {"MaKH": 1})
        for r in await cursor.to_list(length=None):
            try:
                ma_kh = r.get("MaKH", "")
                if ma_kh and ma_kh.startswith("KH"):
                    num = int(ma_kh[2:])
                    if num > max_id:
                        max_id = num
            except: pass
            
        new_ma_kh = "KH" + str(max_id + 1)
        
        new_user = {
            "_id": data.username,
            "MatKhau": hashed_password,
            "MaVaiTro": "ROLE_CUSTOMER",
            "MaKH": new_ma_kh,
            "HoTenKH": data.fullname,
            "Email": data.email,
            "SDT": data.phone,
            "DiaChi": "",
            "CCCD": ""
        }
        
        await db.users.insert_one(new_user)
        return {"status": "success", "message": "Đăng ký thành công"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
async def get_profile(current_user: str = Depends(get_current_user)):
    return {"username": current_user}
