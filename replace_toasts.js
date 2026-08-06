const fs = require('fs');

function replaceInFile(file, replacements) {
    let content = fs.readFileSync(file, 'utf8');
    for (const [oldStr, newStr] of replacements) {
        content = content.split(oldStr).join(newStr);
    }
    fs.writeFileSync(file, content, 'utf8');
}

const appReplacements = [
    ['"Tài khoản hoặc mật khẩu trong SQL Server không đúng!"', '"Tài khoản hoặc mật khẩu không chính xác."'],
    ['"Tài khoản không sở hữu vai trò truy cập này!"', '"Bạn không có quyền truy cập vào khu vực này."'],
    ['`Đăng nhập thành công! Xin chào ${res.fullname}`', '`Đăng nhập thành công. Chào mừng ${res.fullname}!`'],
    ['"Lỗi kết nối nghiêm trọng đến Server Python main.py!"', '"Không thể kết nối đến hệ thống. Vui lòng thử lại sau."'],
    ['"Đã kết thúc phiên hoạt động an toàn!"', '"Bạn đã đăng xuất thành công."'],
    ['"Đăng ký thành công! Dữ liệu đã đẩy vào bảng TaiKhoan và KhachHang."', '"Đăng ký tài khoản thành công! Chào mừng bạn đến với HUCE Hotel."'],
    ['"Sập kết nối API Server!"', '"Hệ thống đang bận. Vui lòng thử lại sau."'],
    ['"Tuyệt vời! Đánh giá của bạn đã được đăng!"', '"Cảm ơn bạn đã gửi đánh giá! Ý kiến của bạn rất quý giá với chúng tôi."'],
    ['"Lỗi máy chủ! Không thể lưu bài viết."', '"Có lỗi xảy ra khi gửi đánh giá. Vui lòng thử lại."'],
    ['"Mất kết nối với Server!"', '"Hệ thống đang bận. Vui lòng thử lại sau."'],
    ['"Lỗi kết nối bộ lọc Backend"', '"Có lỗi xảy ra khi tải danh sách phòng."'],
    ['`Tuyệt vời! Đơn đã lưu vào CSDL.`', '`Đặt phòng thành công! Cảm ơn quý khách đã tin tưởng HUCE Hotel.`'],
    ['"Lỗi đặt phòng trên Server SQL!"', '"Có lỗi xảy ra trong quá trình xử lý đặt phòng. Vui lòng thử lại."'],
    ['"Không kết nối được Backend!"', '"Hệ thống đang bận. Vui lòng thử lại sau."'],
    ['"Lỗi nạp Profile!"', '"Không thể tải thông tin hồ sơ."'],
    ['"Bảng KhachHang trong SQL Server đã cập nhật!"', '"Cập nhật thông tin cá nhân thành công."'],
    ['"Đổi mật khẩu thành công! Cơ sở dữ liệu đã được cập nhật."', '"Đổi mật khẩu thành công."'],
    ['"Đã làm sạch dữ liệu phiên duyệt web!"', '"Dữ liệu phiên duyệt web đã được làm sạch."'],
    ['"Bảng Phong trong CSDL đã chuyển trạng thái!"', '"Cập nhật trạng thái phòng thành công."'],
    ['"Chức năng lập HD thật đang phát triển"', '"Chức năng lập hóa đơn điện tử đang được cập nhật."'],
    ['"Bảng KhachSan trong SQL Server đã được cập nhật thành công!"', '"Lưu cấu hình hệ thống thành công."'],
    ['"Lỗi kết nối máy chủ API!"', '"Hệ thống đang bận. Vui lòng thử lại sau."']
];

replaceInFile('app.js', appReplacements);

const adminReplacements = [
    ['"Lỗi tìm kiếm phòng"', '"Có lỗi xảy ra khi tìm kiếm phòng."'],
    ['"Đã cập nhật trạng thái phòng!"', '"Cập nhật trạng thái phòng thành công."'],
    ['"Lỗi đổi trạng thái!"', '"Có lỗi xảy ra khi cập nhật trạng thái phòng."'],
    ['"Lỗi tìm kiếm"', '"Có lỗi xảy ra khi tìm kiếm."'],
    ['"Lỗi nạp cấu hình hệ thống!"', '"Có lỗi xảy ra khi tải cấu hình."'],
    ['"Cập nhật thành công."', '"Lưu thay đổi thành công."'],
    ['"Lỗi lưu cấu hình"', '"Có lỗi xảy ra khi lưu cấu hình."'],
    ['\'Chức năng lập HD thật đang phát triển\'', '\'Chức năng xuất hóa đơn điện tử đang được cập nhật.\''],
    ['\'Lập hóa đơn đặt phòng thành công!\'', '\'Khởi tạo đơn đặt phòng thành công!\''],
    ['\'Lỗi kết nối server!\'', '\'Hệ thống đang bận. Vui lòng thử lại sau.\'']
];

replaceInFile('admin.js', adminReplacements);
console.log('Toasts updated!');
