# 🏨 HUCE Hotel Management System

Hệ thống quản lý khách sạn được xây dựng bằng **FastAPI (Python)** cho backend và **HTML/CSS/JavaScript** cho frontend.

---

## 📋 Yêu cầu hệ thống

Trước khi cài đặt, đảm bảo máy tính đã có:

| Phần mềm | Phiên bản tối thiểu | Link tải |
|---|---|---|
| Python | 3.8 trở lên | https://www.python.org/downloads |
| SQL Server | 2017 trở lên (Express là đủ) | https://www.microsoft.com/en-us/sql-server/sql-server-downloads |
| SQL Server Management Studio (SSMS) | Bất kỳ | https://aka.ms/ssmsfullsetup |
| ODBC Driver 17 for SQL Server | 17 | https://aka.ms/downloadmsodbcsql |
| Git | Bất kỳ | https://git-scm.com/downloads |

---

## 🚀 Hướng dẫn cài đặt

### Bước 1 — Clone source code về máy

**Cách 1 — Dùng Git (khuyến nghị):**

Mở **Command Prompt** hoặc **PowerShell**, chạy lệnh:

```bash
git clone https://github.com/hwudat/Wed-t-Ph-ng.git
```

Sau khi clone xong, Git sẽ tự tạo thư mục tên `Wed-t-Ph-ng`. Chạy tiếp:

```bash
cd Wed-t-Ph-ng
```

**Cách 2 — Tải file ZIP (không cần cài Git):**

1. Truy cập: https://github.com/hwudat/Wed-t-Ph-ng
2. Nhấn nút **Code** (màu xanh) → chọn **Download ZIP**
3. Giải nén file ZIP vừa tải về
4. Mở **Command Prompt**, dùng lệnh `cd` để vào thư mục vừa giải nén:

```bash
cd đường-dẫn-đến-thư-mục-vừa-giải-nén
```

Ví dụ:
```bash
cd C:\Users\YourName\Downloads\Wed-t-Ph-ng-main
```

---

### Bước 2 — Khôi phục cơ sở dữ liệu từ file backup

1. Mở **SQL Server Management Studio (SSMS)**
2. Kết nối đến SQL Server của máy bạn
3. Chuột phải vào **Databases** → chọn **Restore Database...**

![Restore Database](https://i.imgur.com/placeholder.png)

4. Trong cửa sổ Restore Database:
   - Chọn **Device** → nhấn nút `...` bên phải
   - Nhấn **Add** → tìm đến file `QuanLyKhachSanHUCE1.bak` trong thư mục dự án
   - Nhấn **OK**

5. Kiểm tra ô **Restore** đã được tick ✅
6. Nhấn **OK** để khôi phục

7. Khi thành công sẽ hiện thông báo:
   > *"The restore of database 'QuanLyKhachSanHUCE1' completed successfully."*

> ⚠️ **Lưu ý:** Tên database phải là `QuanLyKhachSanHUCE1` đúng như vậy, không được đổi tên.

---

### Bước 3 — Cài đặt các thư viện Python

Mở **Command Prompt** tại thư mục dự án, chạy lần lượt:

```bash
python -m pip install fastapi uvicorn
```

```bash
python -m pip install pyodbc
```

> 💡 Nếu lệnh `python` không nhận, thử dùng `python3` thay thế.

---

### Bước 4 — Khởi động server backend

Vẫn trong **Command Prompt** tại thư mục dự án, chạy:

```bash
python main.py
```

Nếu thành công, terminal sẽ hiển thị:

```
⏳ Đang dò tìm SQL Server...
✅ Đã kết nối thành công CSDL tại máy chủ: .\SQLEXPRESS
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

> ❌ Nếu thấy dòng `CẢNH BÁO: Không tự động tìm thấy SQL Server`, hãy xem phần **Xử lý lỗi** bên dưới.

---

### Bước 5 — Mở giao diện web

Tìm file `index.html` trong thư mục dự án và **mở bằng trình duyệt** (Chrome hoặc Edge được khuyến nghị):

- Kéo thả file `index.html` vào cửa sổ trình duyệt, hoặc
- Nhấn đúp chuột vào file `index.html`

Hệ thống sẽ hoạt động tại địa chỉ dạng: `file:///C:/...../index.html`

---

## 🗂️ Cấu trúc thư mục dự án

```
📁 HUCE-Hotel/
├── 📄 index.html       ← Giao diện chính (mở file này để dùng)
├── 🎨 style.css        ← CSS giao diện
├── ⚙️  app.js           ← Logic frontend JavaScript
├── 🐍 main.py          ← Backend API (FastAPI)
├── 🗃️  QuanLyKhachSanHUCE1.bak  ← File backup database SQL Server
└── 📖 README.md        ← File hướng dẫn này
```

---

## 👤 Tài khoản mặc định

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Admin | `admin` | `admin123` |
| Khách hàng | Tự đăng ký | — |

---

## ✨ Chức năng chính

**Dành cho khách hàng:**
- Đăng ký / Đăng nhập tài khoản
- Xem danh sách phòng và tình trạng
- Tìm kiếm và lọc phòng theo ngày, loại phòng, giá
- Đặt phòng và chọn dịch vụ kèm theo
- Xem lịch sử đặt phòng
- Đánh giá khách sạn

**Dành cho quản trị viên (Admin):**
- Quản lý danh sách phòng (thêm, sửa, xóa, đổi trạng thái)
- Quản lý loại phòng và giá tiền
- Quản lý dịch vụ tiện ích
- Xem danh sách đặt phòng
- Cài đặt thông tin khách sạn

---

## 🔧 Xử lý lỗi thường gặp

### ❌ Lỗi: "Không tự động tìm thấy SQL Server"

Nguyên nhân: SQL Server chưa chạy hoặc tên instance khác.

**Cách xử lý:**
1. Mở **Services** (nhấn `Win + R`, gõ `services.msc`)
2. Tìm dịch vụ `SQL Server (SQLEXPRESS)` hoặc `SQL Server (MSSQLSERVER)`
3. Đảm bảo trạng thái là **Running** — nếu không thì nhấn chuột phải → **Start**

Hoặc kiểm tra tên server trong SSMS (góc trên cửa sổ kết nối), sau đó mở file `main.py` và thêm tên đó vào danh sách `SERVER_CANDIDATES`:

```python
SERVER_CANDIDATES = [
    ".\\SQLEXPRESS",
    "TÊN_SERVER_CỦA_BẠN",   ← thêm vào đây
    ...
]
```

---

### ❌ Lỗi: "pip không được nhận dạng"

Chạy lệnh sau thay thế:

```bash
python -m ensurepip --upgrade
python -m pip install fastapi uvicorn pyodbc
```

---

### ❌ Lỗi: "ODBC Driver 17 for SQL Server not found"

Tải và cài đặt driver tại:
https://aka.ms/downloadmsodbcsql

Sau khi cài xong, khởi động lại máy và chạy lại `python main.py`.

---

### ❌ Giao diện web không lấy được dữ liệu (trang trắng / không hiện phòng)

Kiểm tra:
1. Terminal đang chạy `python main.py` chưa bị tắt
2. Địa chỉ `http://127.0.0.1:8000` có hoạt động không — mở trình duyệt và truy cập địa chỉ đó, nếu thấy `{"detail":"Not Found"}` là server đang chạy bình thường
3. Thử tắt tường lửa Windows tạm thời để kiểm tra

---

## 📡 Danh sách API

Server chạy tại `http://127.0.0.1:8000`. Một số endpoint chính:

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/rooms` | Lấy danh sách tất cả phòng |
| GET | `/api/rooms/search` | Tìm kiếm phòng theo tiêu chí |
| POST | `/api/login` | Đăng nhập |
| POST | `/api/register` | Đăng ký tài khoản |
| POST | `/api/booking` | Tạo đơn đặt phòng |
| GET | `/api/admin/rooms` | [Admin] Danh sách phòng |
| POST | `/api/admin/rooms` | [Admin] Thêm phòng |
| PUT | `/api/admin/rooms/{id}` | [Admin] Sửa phòng |
| DELETE | `/api/admin/rooms/{id}` | [Admin] Xóa phòng |
| GET | `/api/admin/room-types` | [Admin] Danh sách loại phòng |
| POST | `/api/admin/room-types` | [Admin] Thêm loại phòng |
| PUT | `/api/admin/room-types/{id}` | [Admin] Sửa loại phòng |
| DELETE | `/api/admin/room-types/{id}` | [Admin] Xóa loại phòng |
| GET | `/api/admin/services` | [Admin] Danh sách dịch vụ |
| POST | `/api/admin/services` | [Admin] Thêm dịch vụ |
| PUT | `/api/admin/services/{id}` | [Admin] Sửa dịch vụ |
| DELETE | `/api/admin/services/{id}` | [Admin] Xóa dịch vụ |

Xem toàn bộ API tại: `http://127.0.0.1:8000/docs` (Swagger UI tự động)

---

## 🛑 Tắt server

Quay lại cửa sổ terminal đang chạy `python main.py` và nhấn:

```
Ctrl + C
```

---

