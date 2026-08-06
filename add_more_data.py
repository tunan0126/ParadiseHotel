import sqlite3
import random

conn = sqlite3.connect("hotel.db")
cursor = conn.cursor()

# 1. Thêm nhiều dịch vụ hơn
services = [
    ('DV104', 'Dịch vụ giặt ủi', 150000),
    ('DV105', 'Ăn tối tại phòng', 450000),
    ('DV106', 'Thuê xe máy', 200000),
    ('DV107', 'Thuê ô tô tự lái', 1200000),
    ('DV108', 'Tour lặn ngắm san hô', 850000),
    ('DV109', 'Vé công viên giải trí', 550000),
    ('DV110', 'Dịch vụ trông trẻ', 300000)
]
for svc in services:
    try:
        cursor.execute("INSERT INTO DichVu (MaDV, TenDV, GiaDV, MaKS) VALUES (?, ?, ?, 'KS01')", svc)
    except:
        pass # ignore if already exists

# 2. Thêm nhiều phòng hơn (Sinh tự động cho đủ 50 phòng)
loai_phongs = ['LP101', 'LP102', 'LP103']
tinh_trangs = ['Sẵn sàng', 'Đang dọn dẹp', 'Đang bảo trì']

for floor in range(1, 9): # Tầng 1 đến 8
    for room_num in range(1, 11): # Mỗi tầng 10 phòng
        if floor <= 3:
            ma_loai = 'LP101' # Standard
        elif floor <= 6:
            ma_loai = 'LP102' # Deluxe
        else:
            ma_loai = 'LP103' # Suite
            
        so_phong = f"{floor}{room_num:02d}"
        ma_phong = f"P{so_phong}"
        tinh_trang = random.choice(['Sẵn sàng', 'Sẵn sàng', 'Sẵn sàng', 'Đang dọn dẹp'])
        
        try:
            cursor.execute("INSERT INTO Phong (MaPhong, SoPhong, TinhTrang, MaLoaiPhong, MaKS) VALUES (?, ?, ?, ?, 'KS01')", 
                          (ma_phong, so_phong, tinh_trang, ma_loai))
        except:
            pass

conn.commit()
conn.close()
print("Đã thêm hàng loạt dịch vụ và 80 phòng vào Database!")
