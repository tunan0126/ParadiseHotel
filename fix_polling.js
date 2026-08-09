const fs = require('fs');

const content = fs.readFileSync('admin.js', 'utf8');

let newContent = content.replace(
    `    if (window.adminBookingsPolling) {
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
    if (tabId === 'settings') renderAdminSettings();`,
    `    if (window.adminPollingInterval) {
        clearInterval(window.adminPollingInterval);
        window.adminPollingInterval = null;
    }

    if (tabId === 'rooms') {
        renderAdminRooms(null, false);
        window.adminPollingInterval = setInterval(() => renderAdminRooms(null, true), 5000);
    }
    if (tabId === 'matrix') {
        loadRoomMatrix(false);
        window.adminPollingInterval = setInterval(() => loadRoomMatrix(true), 5000);
    }
    if (tabId === 'room-types') {
        renderAdminRoomTypes(null, false);
        window.adminPollingInterval = setInterval(() => renderAdminRoomTypes(null, true), 5000);
    }
    if (tabId === 'bookings') {
        renderAdminBookings(null, false);
        window.adminPollingInterval = setInterval(() => renderAdminBookings(null, true), 5000);
    }
    if (tabId === 'services') {
        renderAdminServices(null, false);
        window.adminPollingInterval = setInterval(() => renderAdminServices(null, true), 5000);
    }
    if (tabId === 'settings') renderAdminSettings();`
);

// renderAdminRooms
newContent = newContent.replace(
    `async function renderAdminRooms(customData = null) {\n    const tbody = document.getElementById('admin-rooms-tbody'); \n    if (!tbody) return;\n    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:24px;">Đang tải...</td></tr>';`,
    `async function renderAdminRooms(customData = null, isPolling = false) {\n    const tbody = document.getElementById('admin-rooms-tbody'); \n    if (!tbody) return;\n    if (!isPolling) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:24px;">Đang tải...</td></tr>';`
);

newContent = newContent.replace(
    `        tbody.innerHTML = '';\n\n        const total = rooms.length;`,
    `        let newHTML = '';\n\n        const total = rooms.length;`
);

newContent = newContent.replace(
    `        if (rooms.length === 0) {\n            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:32px;">Chưa có phòng nào.</td></tr>';\n            return;\n        }`,
    `        if (rooms.length === 0) {\n            newHTML = '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:32px;">Chưa có phòng nào.</td></tr>';\n            if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;\n            return;\n        }`
);

newContent = newContent.replace(
    `        rooms.forEach(room => {\n            let badge = 'status-ready';`,
    `        rooms.forEach(room => {\n            let badge = 'status-ready';`
);

newContent = newContent.replace(
    `            const maLoai = room.maLoai || '';\n\n            tbody.innerHTML += \`<tr>`,
    `            const maLoai = room.maLoai || '';\n\n            newHTML += \`<tr>`
);

newContent = newContent.replace(
    `                </td>\n            </tr>\`;\n        });\n    } catch(e) { tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#ef4444;padding:24px;">Lỗi tải danh sách phòng.</td></tr>'; }`,
    `                </td>\n            </tr>\`;\n        });\n        if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;\n    } catch(e) { if (!isPolling) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#ef4444;padding:24px;">Lỗi tải danh sách phòng.</td></tr>'; }`
);

// loadRoomMatrix
newContent = newContent.replace(
    `async function loadRoomMatrix() {\n    const container = document.getElementById('admin-room-matrix-container');\n    if (!container) return;\n    const daysSelect = document.getElementById('matrix-days-select');\n    const days = daysSelect ? daysSelect.value : 7;\n    \n    container.innerHTML = '<div style="text-align:center; padding:30px; color:#64748b;">Đang tải sơ đồ lịch phòng...</div>';`,
    `async function loadRoomMatrix(isPolling = false) {\n    const container = document.getElementById('admin-room-matrix-container');\n    if (!container) return;\n    const daysSelect = document.getElementById('matrix-days-select');\n    const days = daysSelect ? daysSelect.value : 7;\n    \n    if (!isPolling) container.innerHTML = '<div style="text-align:center; padding:30px; color:#64748b;">Đang tải sơ đồ lịch phòng...</div>';`
);

newContent = newContent.replace(
    `        if (!data.rooms || data.rooms.length === 0) {\n            container.innerHTML = '<div style="text-align:center; padding:30px; color:#64748b;">Chưa có dữ liệu phòng.</div>';\n            return;\n        }`,
    `        if (!data.rooms || data.rooms.length === 0) {\n            const newHTML = '<div style="text-align:center; padding:30px; color:#64748b;">Chưa có dữ liệu phòng.</div>';\n            if (container.innerHTML !== newHTML) container.innerHTML = newHTML;\n            return;\n        }`
);

newContent = newContent.replace(
    `        html += '</tbody></table>';\n        container.innerHTML = html;\n    } catch(e) {\n        container.innerHTML = '<div style="text-align:center; padding:30px; color:#ef4444;">Lỗi nạp sơ đồ.</div>';\n    }`,
    `        html += '</tbody></table>';\n        if (container.innerHTML !== html) container.innerHTML = html;\n    } catch(e) {\n        if (!isPolling) container.innerHTML = '<div style="text-align:center; padding:30px; color:#ef4444;">Lỗi nạp sơ đồ.</div>';\n    }`
);


// renderAdminRoomTypes
newContent = newContent.replace(
    `async function renderAdminRoomTypes(customData = null) {\n    const tbody = document.getElementById('admin-room-types-tbody');\n    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:24px;">Đang tải...</td></tr>';`,
    `async function renderAdminRoomTypes(customData = null, isPolling = false) {\n    const tbody = document.getElementById('admin-room-types-tbody');\n    if (!isPolling) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:24px;">Đang tải...</td></tr>';`
);

newContent = newContent.replace(
    `        tbody.innerHTML = '';\n\n        const total = types.length;`,
    `        let newHTML = '';\n\n        const total = types.length;`
);

newContent = newContent.replace(
    `        if (types.length === 0) {\n            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:32px;">Chưa có loại phòng nào.</td></tr>';\n            return;\n        }`,
    `        if (types.length === 0) {\n            newHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:32px;">Chưa có loại phòng nào.</td></tr>';\n            if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;\n            return;\n        }`
);

newContent = newContent.replace(
    `            const soNguoi = typeof type.maxPeople === 'string' ? type.maxPeople.replace(' Người','') : type.maxPeople;\n            tbody.innerHTML += \`<tr>`,
    `            const soNguoi = typeof type.maxPeople === 'string' ? type.maxPeople.replace(' Người','') : type.maxPeople;\n            newHTML += \`<tr>`
);

newContent = newContent.replace(
    `                </td>\n            </tr>\`;\n        });\n    } catch(e) { tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:24px;">Lỗi kết nối</td></tr>'; }`,
    `                </td>\n            </tr>\`;\n        });\n        if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;\n    } catch(e) { if (!isPolling) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:24px;">Lỗi kết nối</td></tr>'; }`
);

// renderAdminServices
newContent = newContent.replace(
    `async function renderAdminServices(customData = null) {\n    const tbody = document.getElementById('admin-services-tbody');\n    if (!tbody) return;\n    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:24px;">Đang tải...</td></tr>';`,
    `async function renderAdminServices(customData = null, isPolling = false) {\n    const tbody = document.getElementById('admin-services-tbody');\n    if (!tbody) return;\n    if (!isPolling) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:24px;">Đang tải...</td></tr>';`
);

newContent = newContent.replace(
    `        tbody.innerHTML = '';\n\n        const total = services.length;`,
    `        let newHTML = '';\n\n        const total = services.length;`
);

newContent = newContent.replace(
    `        if (services.length === 0) {\n            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:32px;">Chưa có dịch vụ nào.</td></tr>';\n            return;\n        }`,
    `        if (services.length === 0) {\n            newHTML = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:32px;">Chưa có dịch vụ nào.</td></tr>';\n            if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;\n            return;\n        }`
);

newContent = newContent.replace(
    `            const statusText = service.status || 'Sẵn sàng';\n            tbody.innerHTML += \`<tr>`,
    `            const statusText = service.status || 'Sẵn sàng';\n            newHTML += \`<tr>`
);

newContent = newContent.replace(
    `                </td>\n            </tr>\`;\n        });\n    } catch(e) { tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:24px;">Lỗi nạp dịch vụ.</td></tr>'; }`,
    `                </td>\n            </tr>\`;\n        });\n        if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;\n    } catch(e) { if (!isPolling) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:24px;">Lỗi nạp dịch vụ.</td></tr>'; }`
);

fs.writeFileSync('admin.js', newContent, 'utf8');
console.log('Fixed successfully with NodeJS');
