import re

def main():
    with open('admin.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update switchAdminTab
    old_switch = """    if (window.adminBookingsPolling) {
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
    if (tabId === 'settings') renderAdminSettings();"""
    new_switch = """    if (window.adminPollingInterval) {
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
    if (tabId === 'settings') renderAdminSettings();"""
    content = content.replace(old_switch, new_switch)

    # 2. Update renderAdminRooms
    old_rooms_1 = "async function renderAdminRooms(customData = null) {\n    const tbody = document.getElementById('admin-rooms-tbody'); \n    if (!tbody) return;\n    tbody.innerHTML = '<tr><td colspan=\"4\" style=\"text-align:center;color:#94a3b8;padding:24px;\">Đang tải...</td></tr>';"
    new_rooms_1 = "async function renderAdminRooms(customData = null, isPolling = false) {\n    const tbody = document.getElementById('admin-rooms-tbody'); \n    if (!tbody) return;\n    if (!isPolling) tbody.innerHTML = '<tr><td colspan=\"4\" style=\"text-align:center;color:#94a3b8;padding:24px;\">Đang tải...</td></tr>';"
    content = content.replace(old_rooms_1, new_rooms_1)
    
    # In renderAdminRooms, change tbody.innerHTML assignment to buffer
    old_rooms_2 = """        tbody.innerHTML = '';

        const total = rooms.length;"""
    new_rooms_2 = """        let newHTML = '';

        const total = rooms.length;"""
    content = content.replace(old_rooms_2, new_rooms_2)
    
    old_rooms_3 = "        if (rooms.length === 0) {\n            tbody.innerHTML = '<tr><td colspan=\"4\" style=\"text-align:center;color:#94a3b8;padding:32px;\">Chưa có phòng nào.</td></tr>';\n            return;\n        }"
    new_rooms_3 = "        if (rooms.length === 0) {\n            newHTML = '<tr><td colspan=\"4\" style=\"text-align:center;color:#94a3b8;padding:32px;\">Chưa có phòng nào.</td></tr>';\n            if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;\n            return;\n        }"
    content = content.replace(old_rooms_3, new_rooms_3)
    
    old_rooms_4 = "            tbody.innerHTML += `<tr>"
    new_rooms_4 = "            newHTML += `<tr>"
    content = content.replace(old_rooms_4, new_rooms_4)

    # We need to add the final assignment for renderAdminRooms
    # We find the end of the rooms.forEach(room => { ... }) block
    old_rooms_5 = """                </td>
            </tr>`;
        });
    } catch(e) { tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#ef4444;padding:24px;">Lỗi kết nối</td></tr>'; }"""
    new_rooms_5 = """                </td>
            </tr>`;
        });
        if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;
    } catch(e) { if (!isPolling) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#ef4444;padding:24px;">Lỗi kết nối</td></tr>'; }"""
    content = content.replace(old_rooms_5, new_rooms_5)

    # 3. Update loadRoomMatrix
    old_matrix_1 = "async function loadRoomMatrix() {\n    const container = document.getElementById('admin-room-matrix-container');\n    if (!container) return;\n    const daysSelect = document.getElementById('matrix-days-select');\n    const days = daysSelect ? daysSelect.value : 7;\n    \n    container.innerHTML = '<div style=\"text-align:center; padding:30px; color:#64748b;\">Đang tải sơ đồ lịch phòng...</div>';"
    new_matrix_1 = "async function loadRoomMatrix(isPolling = false) {\n    const container = document.getElementById('admin-room-matrix-container');\n    if (!container) return;\n    const daysSelect = document.getElementById('matrix-days-select');\n    const days = daysSelect ? daysSelect.value : 7;\n    \n    if (!isPolling) container.innerHTML = '<div style=\"text-align:center; padding:30px; color:#64748b;\">Đang tải sơ đồ lịch phòng...</div>';"
    content = content.replace(old_matrix_1, new_matrix_1)

    old_matrix_2 = "        if (!data.rooms || data.rooms.length === 0) {\n            container.innerHTML = '<div style=\"text-align:center; padding:30px; color:#64748b;\">Chưa có dữ liệu phòng.</div>';\n            return;\n        }"
    new_matrix_2 = "        if (!data.rooms || data.rooms.length === 0) {\n            const newHTML = '<div style=\"text-align:center; padding:30px; color:#64748b;\">Chưa có dữ liệu phòng.</div>';\n            if (container.innerHTML !== newHTML) container.innerHTML = newHTML;\n            return;\n        }"
    content = content.replace(old_matrix_2, new_matrix_2)

    old_matrix_3 = "        html += '</tbody></table>';\n        container.innerHTML = html;\n    } catch(e) {\n        container.innerHTML = '<div style=\"text-align:center; padding:30px; color:#ef4444;\">Lỗi nạp sơ đồ.</div>';\n    }"
    new_matrix_3 = "        html += '</tbody></table>';\n        if (container.innerHTML !== html) container.innerHTML = html;\n    } catch(e) {\n        if (!isPolling) container.innerHTML = '<div style=\"text-align:center; padding:30px; color:#ef4444;\">Lỗi nạp sơ đồ.</div>';\n    }"
    content = content.replace(old_matrix_3, new_matrix_3)

    # 4. Update renderAdminRoomTypes
    old_types_1 = "async function renderAdminRoomTypes(customData = null) {\n    const tbody = document.getElementById('admin-room-types-tbody');\n    tbody.innerHTML = '<tr><td colspan=\"5\" style=\"text-align:center;color:#94a3b8;padding:24px;\">Đang tải...</td></tr>';"
    new_types_1 = "async function renderAdminRoomTypes(customData = null, isPolling = false) {\n    const tbody = document.getElementById('admin-room-types-tbody');\n    if (!isPolling) tbody.innerHTML = '<tr><td colspan=\"5\" style=\"text-align:center;color:#94a3b8;padding:24px;\">Đang tải...</td></tr>';"
    content = content.replace(old_types_1, new_types_1)

    old_types_2 = "        tbody.innerHTML = '';\n\n        const total = types.length;"
    new_types_2 = "        let newHTML = '';\n\n        const total = types.length;"
    content = content.replace(old_types_2, new_types_2)

    old_types_3 = "        if (types.length === 0) {\n            tbody.innerHTML = '<tr><td colspan=\"5\" style=\"text-align:center;color:#94a3b8;padding:32px;\">Chưa có loại phòng nào.</td></tr>';\n            return;\n        }"
    new_types_3 = "        if (types.length === 0) {\n            newHTML = '<tr><td colspan=\"5\" style=\"text-align:center;color:#94a3b8;padding:32px;\">Chưa có loại phòng nào.</td></tr>';\n            if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;\n            return;\n        }"
    content = content.replace(old_types_3, new_types_3)

    old_types_4 = "            tbody.innerHTML += `<tr>"
    new_types_4 = "            newHTML += `<tr>"
    content = content.replace(old_types_4, new_types_4)

    old_types_5 = """                </td>
            </tr>`;
        });
    } catch(e) { tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:24px;">Lỗi kết nối</td></tr>'; }"""
    new_types_5 = """                </td>
            </tr>`;
        });
        if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;
    } catch(e) { if (!isPolling) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:24px;">Lỗi kết nối</td></tr>'; }"""
    content = content.replace(old_types_5, new_types_5)

    # 5. Update renderAdminServices
    old_srv_1 = "async function renderAdminServices(customData = null) {\n    const tbody = document.getElementById('admin-services-tbody');\n    if (!tbody) return;\n    tbody.innerHTML = '<tr><td colspan=\"5\" style=\"text-align:center;color:#94a3b8;padding:24px;\">Đang tải...</td></tr>';"
    new_srv_1 = "async function renderAdminServices(customData = null, isPolling = false) {\n    const tbody = document.getElementById('admin-services-tbody');\n    if (!tbody) return;\n    if (!isPolling) tbody.innerHTML = '<tr><td colspan=\"5\" style=\"text-align:center;color:#94a3b8;padding:24px;\">Đang tải...</td></tr>';"
    content = content.replace(old_srv_1, new_srv_1)

    old_srv_2 = "        tbody.innerHTML = '';\n\n        const total = services.length;"
    new_srv_2 = "        let newHTML = '';\n\n        const total = services.length;"
    content = content.replace(old_srv_2, new_srv_2)

    old_srv_3 = "        if (services.length === 0) {\n            tbody.innerHTML = '<tr><td colspan=\"5\" style=\"text-align:center;color:#94a3b8;padding:32px;\">Chưa có dịch vụ nào.</td></tr>';\n            return;\n        }"
    new_srv_3 = "        if (services.length === 0) {\n            newHTML = '<tr><td colspan=\"5\" style=\"text-align:center;color:#94a3b8;padding:32px;\">Chưa có dịch vụ nào.</td></tr>';\n            if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;\n            return;\n        }"
    content = content.replace(old_srv_3, new_srv_3)

    old_srv_4 = "            tbody.innerHTML += `<tr>"
    new_srv_4 = "            newHTML += `<tr>"
    content = content.replace(old_srv_4, new_srv_4)

    old_srv_5 = """                </td>
            </tr>`;
        });
    } catch(e) { tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:24px;">Lỗi kết nối</td></tr>'; }"""
    new_srv_5 = """                </td>
            </tr>`;
        });
        if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;
    } catch(e) { if (!isPolling) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#ef4444;padding:24px;">Lỗi kết nối</td></tr>'; }"""
    content = content.replace(old_srv_5, new_srv_5)


    with open('admin.js', 'w', encoding='utf-8') as f:
        f.write(content)
        print("admin.js updated!")

if __name__ == '__main__':
    main()
