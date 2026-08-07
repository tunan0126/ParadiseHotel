// === ADMIN JS === //
// Auth Interceptor
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    let [resource, config] = args;
    const token = localStorage.getItem('token');
    if (token && typeof resource === 'string' && resource.includes('/api/') && !resource.includes('/api/login') && !resource.includes('/api/register')) {
        config = config || {};
        config.headers = config.headers || {};
        config.headers['Authorization'] = 'Bearer ' + token;
        args[1] = config;
    }
    const response = await originalFetch(...args);
    if (response.status === 401) {
        localStorage.removeItem('is_logged_in');
        localStorage.removeItem('token');
        window.location.href = 'index.html';
    }
    return response;
};

window.translateRoomName = function(name) {
    if (!name) return name;
    const map = {
        "Standard Single Room": "Phòng Đơn Tiêu Chuẩn",
        "Deluxe Double Room": "Phòng Đôi Cao Cấp",
        "Executive Suite VIP": "Phòng Suite VIP",
        "Standard Single": "Phòng Đơn Tiêu Chuẩn",
        "Deluxe Double": "Phòng Đôi Cao Cấp",
        "Suite VIP": "Phòng Suite VIP"
    };
    return map[name] || name;
};

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    try {
        if (container.matches(':popover-open')) container.hidePopover();
        container.showPopover();
    } catch(e) {}
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : '⚠️'}</span>
        <span class="toast-message">${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => { toast.classList.add('show'); }, 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function formatMoney(amount) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
}

function openAdminModal(id) { const el = document.getElementById(id); if(el) if (!el.open) el.showModal(); }
function closeAdminModal(id) { const el = document.getElementById(id); if(el) el.close(); }

function logoutAdmin() {
    localStorage.removeItem('is_logged_in');
    localStorage.removeItem('current_user');
    localStorage.removeItem('current_username');
    localStorage.removeItem('current_role');
    window.location.href = 'index.html';
}

// Redirect if not admin
document.addEventListener('DOMContentLoaded', () => {
    const role = localStorage.getItem('current_role');
    if (role !== 'admin') {
        window.location.href = 'index.html';
        return;
    }
    // Initialize admin data
    initAdminData();
});

// Listen for sync from customer web
window.addEventListener('storage', function(e) {
    if (e.key === 'sync_trigger') {
        initAdminData();
    }
});

async function initAdminData() {
    await renderAdminRooms();
    await renderAdminRoomTypes();
    await renderAdminBookings();
    await renderAdminServices();
    await renderAdminSettings();
}

function showAdminPage() {
    if (typeof hideAllScreens === 'function') hideAllScreens();
    const cv = document.getElementById('customer-view');
    if (cv) cv.style.display = 'none'; 
    const adminScreen = document.getElementById('admin-screen');
    if (adminScreen) adminScreen.style.display = 'flex';
    switchAdminTab('rooms');
}
function switchAdminTab(tabId) {
    document.querySelectorAll('.admin-nav-menu li').forEach(li => li.classList.remove('active'));
    let navEl = document.getElementById('nav-admin-' + tabId); if (navEl) navEl.classList.add('active');
    document.querySelectorAll('.admin-tab-content').forEach(content => content.style.display = 'none');
    let tabEl = document.getElementById('admin-tab-' + tabId); if (tabEl) tabEl.style.display = 'block';

    if (window.adminBookingsPolling) {
        clearInterval(window.adminBookingsPolling);
        window.adminBookingsPolling = null;
    }

    if (tabId === 'rooms') renderAdminRooms();
    if (tabId === 'matrix') loadRoomMatrix();
    if (tabId === 'room-types') renderAdminRoomTypes();
    if (tabId === 'bookings') {
        renderAdminBookings(null, false);
        window.adminBookingsPolling = setInterval(() => renderAdminBookings(null, true), 5000);
    }
    if (tabId === 'services') renderAdminServices();
    if (tabId === 'settings') renderAdminSettings();
}
async function renderAdminRooms(customData = null) {
    const tbody = document.getElementById('admin-rooms-tbody'); 
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:24px;">Đang tải...</td></tr>';
    try {
        // Ưu tiên dùng dữ liệu tìm kiếm nếu có
        let rooms = customData;
        if (!rooms) {
            const res = await fetch('/api/admin/rooms');
            rooms = await res.json(); 
        }
        
        rooms.forEach(r => { if(r.name) r.name = window.translateRoomName(r.name); });
        
        tbody.innerHTML = '';

        const total = rooms.length;
        const ready = rooms.filter(r => r.status === 'Sẵn sàng' || r.status === 'Còn trống').length;
        const occupied = rooms.filter(r => r.status === 'Đang có khách').length;
        const cleaning = rooms.filter(r => r.status === 'Đang dọn dẹp').length;
        const statTotal = document.getElementById('stat-total-rooms');
        const statReady = document.getElementById('stat-ready-rooms');
        const statOccupied = document.getElementById('stat-occupied-rooms');
        const statCleaning = document.getElementById('stat-cleaning-rooms');
        if (statTotal) statTotal.textContent = total;
        if (statReady) statReady.textContent = ready;
        if (statOccupied) statOccupied.textContent = occupied;
        if (statCleaning) statCleaning.textContent = cleaning;

        if (rooms.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:32px;">Chưa có phòng nào.</td></tr>';
            return;
        }
        rooms.forEach(room => {
            let badge = 'status-ready';
            let statusText = room.status;
            if (room.status === 'Đang có khách') badge = 'status-occupied';
            if (room.status === 'Đang dọn dẹp') badge = 'status-cleaning';

            const suiteSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>';
            const deluxeSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v9"/></svg>';
            const standardSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>';
            
            const roomNameLower = (room.name || '').toLowerCase();
            const roomEmoji = (roomNameLower.includes('suite') || roomNameLower.includes('vip')) ? suiteSvg : (roomNameLower.includes('deluxe') || roomNameLower.includes('cao cấp')) ? deluxeSvg : standardSvg;
            const maLoai = room.maLoai || '';

            tbody.innerHTML += `<tr>
                <td>
                    <div class="room-cell">
                        <div class="room-cell-img-placeholder">${roomEmoji}</div>
                        <div class="room-cell-info">
                            <span class="room-cell-id">${room.id} · Phòng ${room.roomNumber}</span>
                            <span class="room-cell-type">${room.name}</span>
                        </div>
                    </div>
                </td>
                <td style="font-weight:600;color:#334155;">${room.price ? room.price.toLocaleString() + 'đ' : '—'}</td>
                <td><span class="status-badge ${badge}">${statusText}</span></td>
                <td>
                    <button class="btn-edit" onclick="editRoom('${room.id}', '${room.roomNumber}', '${maLoai}', '${room.status}')">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                        Sửa phòng
                    </button>
                    <button class="btn-delete" onclick="deleteRoom('${room.id}', '${room.roomNumber}')">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
                        Xóa
                    </button>
                </td>
            </tr>`;
        });
    } catch(e) { tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#ef4444;padding:24px;">Lỗi tải danh sách phòng.</td></tr>'; }
}
async function searchAdminRooms() {
    let kw = document.getElementById('admin-search-room-input').value.trim();
    try {
        const res = await fetch(`/api/admin/rooms?keyword=${encodeURIComponent(kw)}`);
        const data = await res.json();
        renderAdminRooms(data); // Cập nhật lại bảng với dữ liệu đã lọc
    } catch(e) { 
        showToast("Có lỗi xảy ra khi tìm kiếm phòng.", "error"); 
    }
}
async function mockUpdateStatus(roomId) {
    try {
        const res = await fetch(`/api/admin/rooms/status/${roomId}`, { method: 'POST' });
        if (res.ok) {
            showToast("Cập nhật trạng thái phòng thành công.", "success");
            renderAdminRooms();
            localStorage.setItem('sync_trigger', Date.now());
        }
    } catch(e) { showToast("Có lỗi xảy ra khi cập nhật trạng thái phòng.", "error"); }
}
async function renderAdminRoomTypes(customData = null) {
    const tbody = document.getElementById('admin-room-types-tbody');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:24px;">Đang tải...</td></tr>';
    try {
        let types = customData;
        if (!types) {
            const res = await fetch('/api/admin/room-types');
            types = await res.json();
        }
        
        types.forEach(t => { if(t.name) t.name = window.translateRoomName(t.name); });
        
        tbody.innerHTML = '';

        const total = types.length;
        const prices = types.map(t => t.price).filter(p => p > 0);
        const minPrice = prices.length ? Math.min(...prices) : 0;
        const maxPrice = prices.length ? Math.max(...prices) : 0;
        const elTotal = document.getElementById('stat-total-types');
        const elActive = document.getElementById('stat-active-types');
        const elMin = document.getElementById('stat-min-price');
        const elMax = document.getElementById('stat-max-price');
        if (elTotal) elTotal.textContent = total;
        if (elActive) elActive.textContent = total;
        if (elMin) elMin.textContent = minPrice ? (minPrice/1000).toFixed(0) + 'K' : '0';
        if (elMax) elMax.textContent = maxPrice ? (maxPrice/1000).toFixed(0) + 'K' : '0';

        if (types.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:32px;">Chưa có loại phòng nào.</td></tr>';
            return;
        }
        const svgIcon1 = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>';
        const svgIcon2 = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v9"/></svg>';
        const svgIcon3 = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>';
        const svgIcon4 = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12l5.25 5 2.625-9.167L12.5 17l5.25-5"/></svg>';
        const svgIcon5 = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/></svg>';

        const typeEmojis = [svgIcon1, svgIcon2, svgIcon3, svgIcon4, svgIcon5];
        types.forEach((type, i) => {
            const soNguoi = typeof type.maxPeople === 'string' ? type.maxPeople.replace(' Người','') : type.maxPeople;
            tbody.innerHTML += `<tr>
                <td>
                    <div class="type-cell">
                        <div class="type-cell-badge">${typeEmojis[i % typeEmojis.length]}</div>
                        <div class="type-cell-info">
                            <div class="type-name">${type.name}</div>
                            <div class="type-sub">Mã: ${type.id}</div>
                        </div>
                    </div>
                </td>
                <td>${type.beds} giường</td>
                <td>${soNguoi} người</td>
                <td style="font-weight:600;color:#334155;">${type.price.toLocaleString()}đ</td>
                <td>
                    <button class="btn-edit" onclick="editRoomType('${type.id}', \`${type.name}\`, \`${type.moTa||''}\`, ${type.beds}, ${soNguoi}, ${type.price})">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                        Sửa
                    </button>
                    <button class="btn-delete" onclick="deleteRoomType('${type.id}', \`${type.name}\`)">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
                        Xóa
                    </button>
                </td>
            </tr>`;
        });
    } catch(e) { tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:24px;">Lỗi kết nối</td></tr>'; }
}
async function searchAdminRoomTypes() {
    let kw = document.getElementById('admin-search-type-input').value.trim();
    try {
        const res = await fetch(`/api/admin/room-types?keyword=${encodeURIComponent(kw)}`);
        const data = await res.json(); renderAdminRoomTypes(data);
    } catch(e) { showToast("Có lỗi xảy ra khi tìm kiếm.", "error"); }
}
async function renderAdminBookings(customData = null, isPolling = false) {
    const tbody = document.getElementById('admin-bookings-tbody'); 
    if (!isPolling) tbody.innerHTML = 'Đang lấy dữ liệu...';
    try {
        let bookings = customData;
        if (!bookings) {
            const res = await fetch('/api/admin/bookings');
            bookings = await res.json();
        }
        
        let newHTML = '';
        if(bookings.length === 0) newHTML = '<tr><td colspan="6">Không thấy đơn đặt phòng nào.</td></tr>';
        else {
            bookings.forEach(b => {
                newHTML += `<tr>
                    <td><strong>${b.id}</strong></td><td>${b.customerName}</td><td>${b.checkin} - ${b.checkout}</td><td>${b.totalPrice.toLocaleString()}đ</td><td><span class="badge confirmed">${b.status}</span></td>
                    <td><button class="btn-action-outline" onclick="openInvoiceModal('${b.id}')">📄 In Hóa Đơn</button></td>
                </tr>`;
            });
        }
        
        if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;
    } catch(e) { if (!isPolling) tbody.innerHTML = 'Lỗi nạp đơn hàng.'; }
}
async function searchAdminBookings() {
    let kw = document.getElementById('admin-search-booking-input').value.trim();
    try {
        const res = await fetch(`/api/admin/bookings?keyword=${encodeURIComponent(kw)}`);
        const data = await res.json(); renderAdminBookings(data);
    } catch(e) { showToast("Có lỗi xảy ra khi tìm kiếm.", "error"); }
}
async function renderAdminServices(customData = null) {
    const tbody = document.getElementById('admin-services-tbody');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:24px;">Đang tải...</td></tr>';
    try {
        let services = customData;
        if (!services) {
            const res = await fetch('/api/admin/services');
            services = await res.json();
        }
        tbody.innerHTML = '';

        const total = services.length;
        const active = services.filter(s => s.status === 'Hoạt động' || s.status === 'active').length;
        const inactive = total - active;
        const categories = [...new Set(services.map(s => s.category))].length;
        const elTotal = document.getElementById('stat-total-services');
        const elActive = document.getElementById('stat-active-services');
        const elInactive = document.getElementById('stat-inactive-services');
        const elCats = document.getElementById('stat-service-categories');
        if (elTotal) elTotal.textContent = total;
        if (elActive) elActive.textContent = active;
        if (elInactive) elInactive.textContent = inactive;
        if (elCats) elCats.textContent = categories;

        if (services.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:32px;">Chưa có dịch vụ nào.</td></tr>';
            return;
        }
        const catEmoji = { 'Spa': '💆', 'Ăn uống': '🍽️', 'Vận chuyển': '🚗', 'Giặt ủi': '👕', 'Thể thao': '🏊', 'Tiện ích': '✨' };
        services.forEach(s => {
            const emoji = catEmoji[s.category] || '⭐';
            const badgeClass = (s.status === 'Hoạt động' || s.status === 'active') ? 'status-active' : 'status-inactive';
            tbody.innerHTML += `<tr>
                <td>
                    <div class="service-cell">
                        <div class="service-cell-icon">${emoji}</div>
                        <div class="service-cell-info">
                            <div class="service-name">${s.name}</div>
                            <div class="service-desc">Mã: ${s.id}</div>
                        </div>
                    </div>
                </td>
                <td><span style="background:#f1f5f9;color:#475569;padding:4px 10px;border-radius:6px;font-size:12px;font-weight:600;">${s.category}</span></td>
                <td style="font-weight:600;color:#334155;">${s.price.toLocaleString()}đ</td>
                <td><span class="status-badge ${badgeClass}">${s.status}</span></td>
                <td>
                    <button class="btn-edit" onclick="editService('${s.id}', \`${s.name}\`, ${s.price})">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                        Sửa
                    </button>
                    <button class="btn-delete" onclick="deleteService('${s.id}', \`${s.name}\`)">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
                        Xóa
                    </button>
                </td>
            </tr>`;
        });
    } catch(e) { tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:24px;">Lỗi nạp dịch vụ.</td></tr>'; }
}
async function searchAdminServices() {
    let kw = document.getElementById('admin-search-service-input').value.trim();
    try {
        const res = await fetch(`/api/admin/services?keyword=${encodeURIComponent(kw)}`);
        const data = await res.json(); renderAdminServices(data);
    } catch(e) { showToast("Có lỗi xảy ra khi tìm kiếm.", "error"); }
}
async function renderAdminSettings() {
    try {
        const res = await fetch('/api/admin/settings');
        const settings = await res.json();
        document.getElementById('set-hotel-name').value = settings.name;
        document.getElementById('set-hotel-phone').value = settings.phone;
        document.getElementById('set-hotel-address').value = settings.address;
        document.getElementById('set-checkin-time').value = settings.checkin;
        document.getElementById('set-checkout-time').value = settings.checkout;
        document.getElementById('set-vat').value = settings.vat;
    } catch(e) { showToast("Có lỗi xảy ra khi tải cấu hình.", "error"); }
}
async function saveAdminSettings() {
    const data = {
        name: document.getElementById('set-hotel-name').value,
        phone: document.getElementById('set-hotel-phone').value,
        address: document.getElementById('set-hotel-address').value,
        checkin: document.getElementById('set-checkin-time').value,
        checkout: document.getElementById('set-checkout-time').value,
        vat: parseInt(document.getElementById('set-vat').value)
    };
    try {
        const res = await fetch('/api/admin/settings', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        });
        if(res.ok) {
            document.querySelectorAll('.hotel-name-display').forEach(el => el.innerText = data.name);
            showToast("Lưu thay đổi thành công.", "success");
            
            localStorage.setItem('sync_trigger', Date.now());
        }
    } catch(e) { showToast("Có lỗi xảy ra khi lưu cấu hình.", "error"); }
}
async function addRoom() {
    document.getElementById('modal-room-title').textContent = 'Thêm phòng mới';
    document.getElementById('room-edit-id').value = '';
    document.getElementById('room-so-phong').value = '';
    document.getElementById('room-tinh-trang').value = 'Sẵn sàng';
    await loadRoomTypeOptions('room-ma-loai', '');
    openAdminModal('modal-room');
}
async function editRoom(roomId, soPhong, maLoai, tinhTrang) {
    document.getElementById('modal-room-title').textContent = 'Sửa phòng';
    document.getElementById('room-edit-id').value = roomId;
    document.getElementById('room-so-phong').value = soPhong;
    document.getElementById('room-tinh-trang').value = tinhTrang || 'Sẵn sàng';
    await loadRoomTypeOptions('room-ma-loai', maLoai);
    openAdminModal('modal-room');
}
async function loadRoomTypeOptions(selectId, selectedValue) {
    const sel = document.getElementById(selectId);
    sel.innerHTML = '<option value="">-- Đang tải... --</option>';
    try {
        const res = await fetch('/api/admin/room-types');
        const types = await res.json();
        
        types.forEach(t => { if(t.name) t.name = window.translateRoomName(t.name); });
        
        sel.innerHTML = '<option value="">-- Chọn loại phòng --</option>';
        types.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = `${t.id} - ${t.name}`;
            if (t.id === selectedValue) opt.selected = true;
            sel.appendChild(opt);
        });
    } catch(e) { sel.innerHTML = '<option value="">-- Lỗi tải loại phòng --</option>'; }
}
async function saveRoom() {
    const id = document.getElementById('room-edit-id').value;
    const soPhong = document.getElementById('room-so-phong').value.trim();
    const maLoai = document.getElementById('room-ma-loai').value;
    const tinhTrang = document.getElementById('room-tinh-trang').value;

    if (!soPhong) { showToast('Vui lòng nhập số phòng!', 'error'); return; }
    if (!maLoai) { showToast('Vui lòng chọn loại phòng!', 'error'); return; }

    const body = { so_phong: soPhong, ma_loai_phong: maLoai, tinh_trang: tinhTrang };
    const url = id ? `/api/admin/rooms/${id}` : '/api/admin/rooms';
    const method = id ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
        if (res.ok) {
            closeAdminModal('modal-room');
            renderAdminRooms();
            localStorage.setItem('sync_trigger', Date.now());
            showToast(id ? 'Đã cập nhật phòng!' : 'Đã thêm phòng mới!', 'success');
        } else {
            const err = await res.json();
            showToast('Lỗi: ' + (err.detail || 'Không thể lưu'), 'error');
        }
    } catch(e) { showToast('Hệ thống đang bận. Vui lòng thử lại sau.', 'error'); }
}
function deleteRoom(roomId, soPhong) {
    document.getElementById('modal-delete-msg').textContent = `Bạn có chắc muốn xóa phòng số ${soPhong} (${roomId})? Hành động này không thể hoàn tác.`;
    document.getElementById('modal-delete-confirm-btn').onclick = async () => {
        try {
            const res = await fetch(`/api/admin/rooms/${roomId}`, { method: 'DELETE' });
            if (res.ok) {
                closeAdminModal('modal-confirm-delete');
                renderAdminRooms();
                localStorage.setItem('sync_trigger', Date.now());
                showToast('Đã xóa phòng!', 'success');
            } else {
                const err = await res.json();
                showToast('Lỗi: ' + (err.detail || 'Không thể xóa'), 'error');
                closeAdminModal('modal-confirm-delete');
            }
        } catch(e) { showToast('Hệ thống đang bận. Vui lòng thử lại sau.', 'error'); }
    };
    openAdminModal('modal-confirm-delete');
}
function addRoomType() {
    document.getElementById('modal-room-type-title').textContent = 'Thêm loại phòng mới';
    document.getElementById('room-type-edit-id').value = '';
    document.getElementById('rt-ten').value = '';
    document.getElementById('rt-mo-ta').value = '';
    document.getElementById('rt-so-giuong').value = '1';
    document.getElementById('rt-so-nguoi').value = '2';
    document.getElementById('rt-gia').value = '';
    openAdminModal('modal-room-type');
}
function editRoomType(id, ten, moTa, soGiuong, soNguoi, gia) {
    document.getElementById('modal-room-type-title').textContent = 'Sửa loại phòng';
    document.getElementById('room-type-edit-id').value = id;
    document.getElementById('rt-ten').value = ten;
    document.getElementById('rt-mo-ta').value = moTa || '';
    document.getElementById('rt-so-giuong').value = soGiuong;
    document.getElementById('rt-so-nguoi').value = soNguoi;
    document.getElementById('rt-gia').value = gia;
    openAdminModal('modal-room-type');
}
async function saveRoomType() {
    const id = document.getElementById('room-type-edit-id').value;
    const ten = document.getElementById('rt-ten').value.trim();
    const moTa = document.getElementById('rt-mo-ta').value.trim();
    const soGiuong = parseInt(document.getElementById('rt-so-giuong').value);
    const soNguoi = parseInt(document.getElementById('rt-so-nguoi').value);
    const gia = parseFloat(document.getElementById('rt-gia').value);

    if (!ten) { showToast('Vui lòng nhập tên loại phòng!', 'error'); return; }
    if (!gia || gia <= 0) { showToast('Vui lòng nhập giá tiền hợp lệ!', 'error'); return; }

    const body = { ten_loai_phong: ten, mo_ta: moTa, so_giuong: soGiuong, so_luong_nguoi: soNguoi, gia_tien: gia };
    const url = id ? `/api/admin/room-types/${id}` : '/api/admin/room-types';
    const method = id ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
        if (res.ok) {
            closeAdminModal('modal-room-type');
            renderAdminRoomTypes();
            localStorage.setItem('sync_trigger', Date.now());
            showToast(id ? 'Đã cập nhật loại phòng!' : 'Đã thêm loại phòng mới!', 'success');
        } else {
            const err = await res.json();
            showToast('Lỗi: ' + (err.detail || 'Không thể lưu'), 'error');
        }
    } catch(e) { showToast('Hệ thống đang bận. Vui lòng thử lại sau.', 'error'); }
}
function deleteRoomType(id, ten) {
    document.getElementById('modal-delete-msg').textContent = `Bạn có chắc muốn xóa loại phòng "${ten}" (${id})? Chỉ xóa được nếu không có phòng nào thuộc loại này.`;
    document.getElementById('modal-delete-confirm-btn').onclick = async () => {
        try {
            const res = await fetch(`/api/admin/room-types/${id}`, { method: 'DELETE' });
            if (res.ok) {
                closeAdminModal('modal-confirm-delete');
                renderAdminRoomTypes();
                localStorage.setItem('sync_trigger', Date.now());
                showToast('Đã xóa loại phòng!', 'success');
            } else {
                const err = await res.json();
                showToast('Lỗi: ' + (err.detail || 'Không thể xóa'), 'error');
                closeAdminModal('modal-confirm-delete');
            }
        } catch(e) { showToast('Hệ thống đang bận. Vui lòng thử lại sau.', 'error'); }
    };
    openAdminModal('modal-confirm-delete');
}
function addService() {
    document.getElementById('modal-service-title').textContent = 'Thêm dịch vụ mới';
    document.getElementById('service-edit-id').value = '';
    document.getElementById('svc-ten').value = '';
    document.getElementById('svc-gia').value = '';
    openAdminModal('modal-service');
}
function editService(id, ten, gia) {
    document.getElementById('modal-service-title').textContent = 'Sửa dịch vụ';
    document.getElementById('service-edit-id').value = id;
    document.getElementById('svc-ten').value = ten;
    document.getElementById('svc-gia').value = gia;
    openAdminModal('modal-service');
}
async function saveService() {
    const id = document.getElementById('service-edit-id').value;
    const ten = document.getElementById('svc-ten').value.trim();
    const gia = parseFloat(document.getElementById('svc-gia').value);

    if (!ten) { showToast('Vui lòng nhập tên dịch vụ!', 'error'); return; }
    if (!gia || gia <= 0) { showToast('Vui lòng nhập giá hợp lệ!', 'error'); return; }

    const body = { ten_dv: ten, gia_dv: gia };
    const url = id ? `/api/admin/services/${id}` : '/api/admin/services';
    const method = id ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
        if (res.ok) {
            closeAdminModal('modal-service');
            renderAdminServices();
            localStorage.setItem('sync_trigger', Date.now());
            showToast(id ? 'Đã cập nhật dịch vụ!' : 'Đã thêm dịch vụ mới!', 'success');
        } else {
            const err = await res.json();
            showToast('Lỗi: ' + (err.detail || 'Không thể lưu'), 'error');
        }
    } catch(e) { showToast('Hệ thống đang bận. Vui lòng thử lại sau.', 'error'); }
}
function deleteService(id, ten) {
    document.getElementById('modal-delete-msg').textContent = `Bạn có chắc muốn xóa dịch vụ "${ten}" (${id})?`;
    document.getElementById('modal-delete-confirm-btn').onclick = async () => {
        try {
            const res = await fetch(`/api/admin/services/${id}`, { method: 'DELETE' });
            if (res.ok) {
                closeAdminModal('modal-confirm-delete');
                renderAdminServices();
                localStorage.setItem('sync_trigger', Date.now());
                showToast('Đã xóa dịch vụ!', 'success');
            } else {
                const err = await res.json();
                showToast('Lỗi: ' + (err.detail || 'Không thể xóa'), 'error');
                closeAdminModal('modal-confirm-delete');
            }
        } catch(e) { showToast('Hệ thống đang bận. Vui lòng thử lại sau.', 'error'); }
    };
    openAdminModal('modal-confirm-delete');
}

// Lập Hóa Đơn (Admin Bookings)
async function openAddBookingModal() {
    document.getElementById('booking-username').value = '';
    document.getElementById('booking-fullname').value = '';
    document.getElementById('booking-phone').value = '';
    document.getElementById('booking-price').value = '';
    
    const now = new Date();
    const tomorrow = new Date(now.getTime() + 86400000);
    const toLocalISO = (d) => new Date(d.getTime() - (d.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
    document.getElementById('booking-checkin').value = toLocalISO(now);
    document.getElementById('booking-checkout').value = toLocalISO(tomorrow);
    
    const sel = document.getElementById('booking-room-id');
    sel.innerHTML = '<option value="">-- Đang tải phòng trống... --</option>';
    
    try {
        const settingsRes = await fetch('/api/admin/settings');
        const settings = await settingsRes.json();
        window.adminVatPercent = settings.vat || 0;

        const res = await fetch('/api/admin/rooms');
        const rooms = await res.json();
        const availableRooms = rooms.filter(r => r.status === 'Sẵn sàng' || r.status === 'S\u1eb5n s\u00e0ng');
        
        sel.innerHTML = '<option value="">-- Chọn phòng --</option>';
        availableRooms.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.id;
            opt.dataset.price = r.price;
            opt.textContent = `${r.id} - ${r.name} - ${r.price.toLocaleString()}đ`;
            sel.appendChild(opt);
        });
        
        const svcRes = await fetch('/api/admin/services');
        const svcs = await svcRes.json();
        const svcList = document.getElementById('booking-services-list');
        svcList.innerHTML = '';
        svcs.forEach(s => {
            if (s.status === 'Hoạt động' || s.status === 'Ho\u1ea1t \u0111\u1ed9ng' || s.status === 'active') {
                svcList.innerHTML += `<label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
                    <input type="checkbox" name="booking_services" value="${s.id}" data-price="${s.price}" onchange="calculateAdminBookingPrice()">
                    <span>${s.name} - ${s.price.toLocaleString()}đ</span>
                </label>`;
            }
        });

        sel.onchange = calculateAdminBookingPrice;
        document.getElementById('booking-checkin').onchange = calculateAdminBookingPrice;
        document.getElementById('booking-checkout').onchange = calculateAdminBookingPrice;
    } catch(e) {
        sel.innerHTML = '<option value="">-- Lỗi tải dữ liệu --</option>';
    }
    
    openAdminModal('modal-booking');
}

function calculateAdminBookingPrice() {
    const sel = document.getElementById('booking-room-id');
    const checkin = new Date(document.getElementById('booking-checkin').value);
    const checkout = new Date(document.getElementById('booking-checkout').value);
    const priceInput = document.getElementById('booking-price');

    if (!sel.value || isNaN(checkin) || isNaN(checkout)) {
        priceInput.value = '';
        return;
    }

    const msPerDay = 1000 * 60 * 60 * 24;
    let days = Math.ceil((checkout - checkin) / msPerDay);
    if (days < 1) days = 1;

    const opt = sel.options[sel.selectedIndex];
    const roomPrice = parseFloat(opt.dataset.price) || 0;
    
    let totalServices = 0;
    document.querySelectorAll('input[name="booking_services"]:checked').forEach(cb => {
        totalServices += parseFloat(cb.dataset.price) || 0;
    });

    let subTotal = (roomPrice * days) + totalServices;
    let vatAmount = Math.round(subTotal * ((window.adminVatPercent || 0) / 100));
    priceInput.value = subTotal + vatAmount;
}

async function saveBookingAdmin() {
    let username = document.getElementById('booking-username').value.trim();
    const fullname = document.getElementById('booking-fullname').value.trim();
    const phone = document.getElementById('booking-phone').value.trim();
    const roomId = document.getElementById('booking-room-id').value;
    const checkin = document.getElementById('booking-checkin').value;
    const checkout = document.getElementById('booking-checkout').value;
    const price = document.getElementById('booking-price').value;

    if (!username && !fullname) { showToast('Vui lòng nhập Username hoặc Họ tên khách!', 'error'); return; }
    if (!roomId) { showToast('Vui lòng chọn phòng!', 'error'); return; }
    if (!checkin || !checkout) { showToast('Vui lòng chọn ngày đến và đi!', 'error'); return; }
    if (!price) { showToast('Vui lòng nhập giá!', 'error'); return; }

    const selectedServices = Array.from(document.querySelectorAll('input[name="booking_services"]:checked')).map(cb => cb.value);

    const body = {
        username: username,
        fullname: fullname,
        phone: phone,
        idcard: '',
        room_id: roomId,
        checkin: new Date(checkin).toISOString(),
        checkout: new Date(checkout).toISOString(),
        total_price: parseFloat(price),
        services: selectedServices
    };

    try {
        const res = await fetch('/api/admin/bookings/create', { 
            method: 'POST', 
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify(body) 
        });
        if (res.ok) {
            closeAdminModal('modal-booking');
            renderAdminBookings();
            showToast('Khởi tạo đơn đặt phòng thành công!', 'success');
        } else {
            const err = await res.json();
            showToast('Lỗi: ' + (err.detail || 'Không thể lưu'), 'error');
        }
    } catch(e) { 
        showToast('Hệ thống đang bận. Vui lòng thử lại sau.', 'error'); 
    }
}

// ROOM MATRIX TIMELINE
async function loadRoomMatrix() {
    const container = document.getElementById('admin-room-matrix-container');
    if (!container) return;
    const daysSelect = document.getElementById('matrix-days-select');
    const days = daysSelect ? daysSelect.value : 7;
    
    container.innerHTML = '<div style="text-align:center; padding:30px; color:#64748b;">Đang tải sơ đồ lịch phòng...</div>';
    try {
        const res = await fetch(`/api/admin/room-matrix?days=${days}`);
        const data = await res.json();
        
        if (!data.rooms || data.rooms.length === 0) {
            container.innerHTML = '<div style="text-align:center; padding:30px; color:#64748b;">Chưa có dữ liệu phòng.</div>';
            return;
        }
        
        let html = '<table class="matrix-table"><thead><tr><th class="matrix-room-info">Phòng / Ngày</th>';
        data.dates.forEach(d => {
            const dateParts = d.split('-');
            html += `<th>${dateParts[2]}/${dateParts[1]}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        data.rooms.forEach(r => {
            html += `<tr><td class="matrix-room-info"><strong>Phòng ${r.number}</strong><br><span style="font-size:11px; color:#64748b; font-weight:normal;">${r.type}</span></td>`;
            data.dates.forEach(d => {
                const item = r.schedule[d] || { status: 'available' };
                if (item.status === 'occupied') {
                    html += `<td class="matrix-cell cell-occupied" title="${item.guest} (${item.booking_id})">🔴 ${item.guest}</td>`;
                } else if (item.status === 'cleaning') {
                    html += `<td class="matrix-cell cell-cleaning">🟡 Dọn dẹp</td>`;
                } else {
                    html += `<td class="matrix-cell cell-available">🟢 Sẵn sàng</td>`;
                }
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch(e) {
        container.innerHTML = '<div style="text-align:center; padding:30px; color:#ef4444;">Không thể tải sơ đồ phòng.</div>';
    }
}

// INVOICE PRINTING
async function openInvoiceModal(bookingId) {
    try {
        const res = await fetch('/api/admin/bookings');
        const bookings = await res.json();
        const b = bookings.find(item => item.id === bookingId);
        
        if (!b) {
            showToast('Không tìm thấy thông tin đơn đặt phòng.', 'error');
            return;
        }

        document.getElementById('inv-booking-id').innerText = b.id;
        document.getElementById('inv-guest-name').innerText = b.customerName || 'Khách lẻ';
        document.getElementById('inv-print-date').innerText = new Date().toLocaleDateString('vi-VN');
        document.getElementById('inv-room-number').innerText = b.roomNumber || b.roomName || '---';

        const tbody = document.getElementById('inv-items-tbody');
        let itemsHTML = '';
        
        // Room item
        itemsHTML += `
            <tr style="border-bottom:1px solid #f1f5f9;">
                <td style="padding:10px;">Tiền phòng (${b.roomName || 'Phòng tiêu chuẩn'})</td>
                <td style="padding:10px; text-align:center;">1</td>
                <td style="padding:10px; text-align:right;">${b.totalPrice.toLocaleString()} đ</td>
                <td style="padding:10px; text-align:right;">${b.totalPrice.toLocaleString()} đ</td>
            </tr>
        `;

        tbody.innerHTML = itemsHTML;

        const vat = Math.round(b.totalPrice * 0.1);
        const grandTotal = b.totalPrice + vat;

        document.getElementById('inv-subtotal').innerText = b.totalPrice.toLocaleString() + ' đ';
        document.getElementById('inv-vat').innerText = vat.toLocaleString() + ' đ';
        document.getElementById('inv-grand-total').innerText = grandTotal.toLocaleString() + ' đ';

        openAdminModal('modal-invoice');
    } catch(e) {
        showToast('Có lỗi xảy ra khi tạo hóa đơn.', 'error');
    }
}

// EXPORT BOOKINGS TO CSV
async function exportBookingsCSV() {
    try {
        const res = await fetch('/api/admin/bookings');
        const bookings = await res.json();
        
        if (!bookings || bookings.length === 0) {
            showToast('Chưa có dữ liệu đơn để xuất file.', 'warning');
            return;
        }

        let csvContent = "\uFEFFMã Đơn,Tên Khách Hàng,Thời Gian Nhận Phòng,Thời Gian Trả Phòng,Tổng Tiền,Trạng Thái\n";
        bookings.forEach(b => {
            csvContent += `"${b.id}","${b.customerName || ''}","${b.checkin || ''}","${b.checkout || ''}","${b.totalPrice || 0}","${b.status || ''}"\n`;
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `danh-sach-dat-phong-${new Date().toISOString().slice(0,10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast('Xuất file Excel (CSV) thành công!', 'success');
    } catch(e) {
        showToast('Không thể xuất file CSV.', 'error');
    }
}
function toggleAdminSidebar() {
    const sidebar = document.querySelector('.admin-sidebar-nav');
    sidebar.classList.toggle('mobile-active');
}
