import re
import shutil
import sys

def split_js(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define admin function names
    admin_funcs = [
        "showAdminPage",
        "switchAdminTab",
        "renderAdminRooms",
        "searchAdminRooms",
        "mockUpdateStatus",
        "renderAdminRoomTypes",
        "searchAdminRoomTypes",
        "renderAdminBookings",
        "searchAdminBookings",
        "renderAdminServices",
        "searchAdminServices",
        "renderAdminSettings",
        "saveAdminSettings",
        "addRoom",
        "editRoom",
        "loadRoomTypeOptions",
        "saveRoom",
        "deleteRoom",
        "addRoomType",
        "editRoomType",
        "saveRoomType",
        "deleteRoomType",
        "addService",
        "editService",
        "saveService",
        "deleteService",
        "logoutAdmin" # To be added
    ]

    admin_code = []
    
    # We will use regex to extract the functions. 
    # Since regex for nested brackets is hard, we can iterate over lines.
    lines = content.split('\n')
    
    app_lines = []
    admin_lines = []
    
    in_admin_func = False
    brace_count = 0
    current_func_lines = []
    
    # Common vars and event listeners to keep in both or move
    # admin.js will need basic things like showToast, formatMoney, initData (maybe?)
    # For now, we will extract just the admin specific functions into admin_lines.
    
    for line in lines:
        if not in_admin_func:
            # Check if line starts an admin function
            is_admin_start = False
            for func in admin_funcs:
                if re.match(r'^(async\s+)?function\s+' + func + r'\s*\(', line):
                    is_admin_start = True
                    break
            
            if is_admin_start:
                in_admin_func = True
                brace_count = line.count('{') - line.count('}')
                current_func_lines.append(line)
                if brace_count == 0 and '{' in line:
                    # Single line function like function openAdminModal(id) { ... }
                    admin_lines.extend(current_func_lines)
                    current_func_lines = []
                    in_admin_func = False
            else:
                app_lines.append(line)
        else:
            brace_count += line.count('{') - line.count('}')
            current_func_lines.append(line)
            if brace_count <= 0:
                admin_lines.extend(current_func_lines)
                current_func_lines = []
                in_admin_func = False

    # Write app.js
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(app_lines))
        
    # Write admin.js - We will copy some base utility functions too
    with open('admin.js', 'w', encoding='utf-8') as f:
        # Give admin.js basic utilities
        f.write('''// === ADMIN JS === //
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
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

function openAdminModal(id) { const el = document.getElementById(id); if(el) el.classList.add('open'); }
function closeAdminModal(id) { const el = document.getElementById(id); if(el) el.classList.remove('open'); }

function logoutAdmin() {
    localStorage.removeItem('token');
    localStorage.removeItem('userRole');
    localStorage.removeItem('username');
    window.location.href = 'index.html';
}

// Redirect if not admin
document.addEventListener('DOMContentLoaded', () => {
    const role = localStorage.getItem('userRole');
    if (role !== 'admin') {
        window.location.href = 'index.html';
        return;
    }
    // Initialize admin data
    initAdminData();
});

async function initAdminData() {
    await renderAdminRooms();
    await renderAdminRoomTypes();
    await renderAdminBookings();
    await renderAdminServices();
    await renderAdminSettings();
}

''')
        f.write('\n'.join(admin_lines))

if __name__ == '__main__':
    split_js('app.js')
