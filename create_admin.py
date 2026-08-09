import asyncio
from database import get_db
from security import hash_password

async def create_new_admin():
    db = get_db()
    # Create or update a new admin account
    admin_id = "admin_new"
    password = "123"
    
    user_data = {
        "_id": admin_id,
        "MatKhau": hash_password(password),
        "MaVaiTro": "ROLE_ADMIN",
        "MaKH": None,
        "HoTenKH": "Super Admin",
        "Email": "admin_new@example.com",
        "SDT": "0999999999",
        "DiaChi": "Admin HQ",
        "CCCD": "123456789012"
    }
    
    # Use update_one with upsert=True to insert or update
    await db.users.update_one(
        {"_id": admin_id},
        {"$set": user_data},
        upsert=True
    )
    
    print(f"Created/Updated admin account! Username: {admin_id}, Password: {password}")

if __name__ == "__main__":
    asyncio.run(create_new_admin())
