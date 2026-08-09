import sys

def main():
    # 1. Update admin.py
    with open('routers/admin.py', 'r', encoding='utf-8') as f:
        admin_py = f.read()

    booking_status_model = """class BookingStatusUpdate(BaseModel):
    status: str

"""
    if "class BookingStatusUpdate" not in admin_py:
        admin_py = admin_py.replace("from pydantic import BaseModel", "from pydantic import BaseModel\n" + booking_status_model)
        # If BaseModel is not imported, let's just add it to the top
        if "BookingStatusUpdate" not in admin_py:
            admin_py = "from pydantic import BaseModel\n" + booking_status_model + admin_py

    new_endpoint = """
@router.put("/bookings/{booking_id}/status")
async def admin_update_booking_status(booking_id: str, payload: BookingStatusUpdate):
    db = get_db()
    booking = await db.bookings.find_one({"_id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn")
    
    new_status = payload.status
    await db.bookings.update_one({"_id": booking_id}, {"$set": {"TinhTrangDon": new_status}})
    
    # Logic tự động liên kết: Khi booking cập nhật, cập nhật phòng tương ứng
    if "Phong" in booking and isinstance(booking["Phong"], list) and len(booking["Phong"]) > 0:
        room_id = booking["Phong"][0]
        if new_status == "Đã nhận phòng":
            await db.rooms.update_one({"_id": room_id}, {"$set": {"TinhTrang": "Đang có khách"}})
        elif new_status == "Đã trả phòng":
            await db.rooms.update_one({"_id": room_id}, {"$set": {"TinhTrang": "Đang dọn dẹp"}})
            
    return {"status": "success", "new_status": new_status}
"""
    if "admin_update_booking_status" not in admin_py:
        # insert before @public_router.get("/services")
        admin_py = admin_py.replace('@public_router.get("/services")', new_endpoint + '\n@public_router.get("/services")')
        with open('routers/admin.py', 'w', encoding='utf-8') as f:
            f.write(admin_py)
            print("routers/admin.py updated")

    # 2. Update admin.js to add the UI dropdown and JS function
    with open('admin.js', 'r', encoding='utf-8') as f:
        admin_js = f.read()

    # Find the table row generation for bookings
    old_tr = """                    <td><strong>${b.id}</strong></td><td>${b.customerName}</td><td>${b.checkin} - ${b.checkout}</td><td>${b.totalPrice.toLocaleString()}đ</td><td><span class="badge confirmed">${b.status}</span></td>
                    <td><button class="btn-action-outline" onclick="openInvoiceModal('${b.id}')">📄 In Hóa Đơn</button></td>"""
    
    new_tr = """                    <td><strong>${b.id}</strong></td><td>${b.customerName}</td><td>${b.checkin} - ${b.checkout}</td><td>${b.totalPrice.toLocaleString()}đ</td>
                    <td>
                        <select onchange="changeBookingStatus('${b.id}', this.value)" style="padding: 4px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 13px;">
                            <option value="Đã xác nhận" ${b.status === 'Đã xác nhận' ? 'selected' : ''}>Đã xác nhận</option>
                            <option value="Đã nhận phòng" ${b.status === 'Đã nhận phòng' ? 'selected' : ''}>Đã nhận phòng</option>
                            <option value="Đã trả phòng" ${b.status === 'Đã trả phòng' ? 'selected' : ''}>Đã trả phòng</option>
                            <option value="Đã hủy" ${b.status === 'Đã hủy' ? 'selected' : ''}>Đã hủy</option>
                        </select>
                    </td>
                    <td><button class="btn-action-outline" onclick="openInvoiceModal('${b.id}')">📄 In Hóa Đơn</button></td>"""
                    
    if old_tr in admin_js:
        admin_js = admin_js.replace(old_tr, new_tr)
        
    js_function = """
// Thay đổi trạng thái booking
async function changeBookingStatus(bookingId, newStatus) {
    try {
        const res = await fetch(`/api/admin/bookings/${bookingId}/status`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Cập nhật trạng thái thành công', 'success');
            renderAdminBookings(null, false);
            // Kích hoạt cập nhật chéo (phòng)
            renderAdminRooms(null, false);
            loadRoomMatrix(false);
        } else {
            showToast(data.detail || 'Lỗi cập nhật', 'error');
        }
    } catch(e) {
        showToast('Không thể kết nối máy chủ', 'error');
    }
}
"""
    if "function changeBookingStatus" not in admin_js:
        admin_js += js_function
        with open('admin.js', 'w', encoding='utf-8') as f:
            f.write(admin_js)
            print("admin.js updated")

if __name__ == "__main__":
    main()
