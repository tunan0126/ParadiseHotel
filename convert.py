import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace pyodbc import and connection logic
connection_logic = """import pyodbc

VALID_CONN_STR = ""

SERVER_CANDIDATES = [
    ".\\\\SQLEXPRESS", 
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
    VALID_CONN_STR = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\\\SQLEXPRESS;DATABASE=QuanLyKhachSanHUCE1;Trusted_Connection=yes;"

def get_db_cursor():
    try:
        conn = pyodbc.connect(VALID_CONN_STR)
        return conn, conn.cursor()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Không thể kết nối đến SQL Server")"""

new_connection_logic = """import sqlite3

def get_db_cursor():
    try:
        conn = sqlite3.connect("hotel.db")
        return conn, conn.cursor()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Không thể kết nối đến SQLite")"""

content = content.replace("import pyodbc", "import sqlite3")

# We just replace the get_db_cursor block and the pyodbc scanning block
# by finding it.
content = re.sub(r'VALID_CONN_STR = "".*?raise HTTPException\(status_code=500, detail="Không thể kết nối đến SQL Server"\)', 
                 """def get_db_cursor():\n    try:\n        conn = sqlite3.connect("hotel.db")\n        return conn, conn.cursor()\n    except Exception as e:\n        raise HTTPException(status_code=500, detail="Không thể kết nối đến SQLite")""", 
                 content, flags=re.DOTALL)

# 2. Replace N'...' with '...'
content = re.sub(r"N'([^']*)'", r"'\1'", content)

# 3. Replace LEN with LENGTH
content = content.replace("LEN(MaKH)", "LENGTH(MaKH)")
content = content.replace("LEN(MaDDP)", "LENGTH(MaDDP)")
content = content.replace("LEN(MaLoaiPhong)", "LENGTH(MaLoaiPhong)")
content = content.replace("LEN(MaDV)", "LENGTH(MaDV)")

# 4. Replace SUBSTRING with SUBSTR
content = content.replace("SUBSTRING", "SUBSTR")

# 5. Replace TOP 1 with LIMIT 1
content = content.replace("SELECT TOP 1 kh.TenDangNhap FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP JOIN KhachHang kh ON ddp.MaKH = kh.MaKH WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC",
                          "SELECT kh.TenDangNhap FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP JOIN KhachHang kh ON ddp.MaKH = kh.MaKH WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC LIMIT 1")
content = content.replace("SELECT TOP 1 ddp.NgayTra FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC",
                          "SELECT ddp.NgayTra FROM ChiTietDatPhong ctdp JOIN DonDatPhong ddp ON ctdp.MaDDP = ddp.MaDDP WHERE ctdp.MaPhong = p.MaPhong ORDER BY ddp.MaDDP DESC LIMIT 1")
content = content.replace("SELECT TOP 1 TenKS, SDT, DiaChi, Email FROM KhachSan", "SELECT TenKS, SDT, DiaChi, Email FROM KhachSan LIMIT 1")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Conversion complete!")
