import sqlite3
from security import hash_password

def migrate():
    conn = sqlite3.connect("hotel.db")
    cursor = conn.cursor()
    cursor.execute("SELECT TenDangNhap, MatKhau FROM TaiKhoan")
    users = cursor.fetchall()
    
    for username, password in users:
        # If the password is not already a hex string of length 64 (sha256 length), hash it.
        # This prevents double hashing if the script is run multiple times.
        if len(password) != 64:
            hashed_pwd = hash_password(password)
            cursor.execute("UPDATE TaiKhoan SET MatKhau = ? WHERE TenDangNhap = ?", (hashed_pwd, username))
            print(f"Migrated password for {username}")
    
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
