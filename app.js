// Auth Interceptor
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    let [resource, config] = args;
    const token = localStorage.getItem('token');
    if (token && typeof resource === 'string' && resource.includes('/api/') && !resource.includes('/api/auth/login') && !resource.includes('/api/auth/register')) {
        config = config || {};
        config.headers = config.headers || {};
        config.headers['Authorization'] = 'Bearer ' + token;
        args[1] = config;
    }
    const response = await originalFetch(...args);
    if (response.status === 401) {
        localStorage.removeItem('is_logged_in');
        localStorage.removeItem('token');
        if(typeof openLoginModal === 'function') {
            document.querySelectorAll('.modern-dialog').forEach(d => { if(d.open) d.close(); });
            openLoginModal();
        } else {
            window.location.href = 'index.html';
        }
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
    if (!container) return alert(message);
    try {
        if (container.matches(':popover-open')) container.hidePopover();
        container.showPopover();
    } catch(e) {}
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    let icon = type === 'error' ? '❌' : (type === 'info' ? 'ℹ️' : '✔️');
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.animation = 'fadeOut 0.3s ease-out forwards'; setTimeout(() => toast.remove(), 300); }, 3000);
}

function initData() {
    if (!localStorage.getItem('hotel_reviews')) {
        localStorage.setItem('hotel_reviews', JSON.stringify([
            { id: 1, customerName: 'Trần Thị B', date: '18/06/2026', stars: 5, content: 'Phòng ốc cực kỳ sạch sẽ, view nhìn ra biển tuyệt đẹp. Dịch vụ buffet sáng đa dạng và ngon miệng.', image: 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80' },
            { id: 2, customerName: 'Lê Văn C', date: '15/06/2026', stars: 4, content: 'Trải nghiệm tuyệt vời. Tiện ích đầy đủ, đưa đón sân bay đúng giờ.', image: 'https://images.unsplash.com/photo-1540518614846-7eded433c457?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80' }
        ]));
    }
    fetch('/api/init')
        .then(res => res.json())
        .then(data => {
            if(data.settings) {
                document.querySelectorAll('.hotel-name-display').forEach(el => el.innerText = data.settings.name);
                window.globalVat = data.settings.vat || 0;
            }
            if(data.rooms && data.services) {
                const roomStat = document.getElementById('stat-rooms-count');
                const serviceStat = document.getElementById('stat-services-count');
                if (roomStat && data.rooms.length) roomStat.dataset.target = data.rooms.length;
                if (serviceStat && data.services.length) serviceStat.dataset.target = data.services.length;
                initCountUp();
            }
        }).catch(e => {
            console.error("Error fetching init data", e);
            window.globalVat = 0;
            initCountUp();
        });
}

async function login() {
    const roleInp = document.getElementById('user-role').value; 
    const userInp = document.getElementById('username').value.trim();
    const passInp = document.getElementById('password').value;

    const submitBtn = document.querySelector('#login-modal .submit-login-btn');
    if (submitBtn) { submitBtn.disabled = true; submitBtn.classList.add('loading'); }

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: userInp, password: passInp })
        });
        
        if (!response.ok) {
            if (submitBtn) { submitBtn.disabled = false; submitBtn.classList.remove('loading'); }
            return showToast("Tài khoản hoặc mật khẩu không chính xác.", "error");
        }
        
        const res = await response.json();
        if (res.role !== roleInp) {
            if (submitBtn) { submitBtn.disabled = false; submitBtn.classList.remove('loading'); }
            return showToast("Bạn không có quyền truy cập vào khu vực này.", "error");
        }
        
        localStorage.setItem('is_logged_in', 'true');
        localStorage.setItem('current_user', res.fullname); 
        localStorage.setItem('current_username', res.username); 
        localStorage.setItem('current_role', res.role);
        localStorage.setItem('token', res.access_token);
        
        closeLoginModal(); 
        if (res.role === 'admin') { window.location.href = 'admin.html'; } 
        else { showHomePage(); updateHeaderUI(); showToast(`Đăng nhập thành công. Chào mừng ${res.fullname}!`, "success"); }
    } catch (e) {
        showToast("Không thể kết nối đến hệ thống. Vui lòng thử lại sau.", "error");
    }
}

function logout() {
    localStorage.removeItem('is_logged_in');
    localStorage.removeItem('current_user');
    localStorage.removeItem('current_username');
    localStorage.removeItem('current_role');
    
    document.getElementById('admin-screen').style.display = 'none';
    document.getElementById('customer-view').style.display = 'block';
    updateHeaderUI(); 
    showHomePage(); 
    showToast("Bạn đã đăng xuất thành công.", "info");
}

async function register() {
    const data = {
        fullname: document.getElementById('reg-fullname').value.trim(),
        username: document.getElementById('reg-username').value.trim(),
        phone: document.getElementById('reg-phone').value.trim(),
        idcard: document.getElementById('reg-idcard').value.trim(),
        address: document.getElementById('reg-address').value.trim(),
        password: document.getElementById('reg-password').value,
    };
    const confirmPass = document.getElementById('reg-confirm-password').value;

    if (!data.fullname || !data.username || !data.password) return showToast("Vui lòng không bỏ trống thông tin bắt buộc!", "error");
    if (data.password !== confirmPass) return showToast("Mật khẩu gõ lại không khớp!", "error");

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showToast("Đăng ký tài khoản thành công! Chào mừng bạn đến với HUCE Hotel.", "success"); 
            switchToLogin();
        } else {
            const err = await response.json();
            showToast(err.detail, "error");
        }
    } catch (e) { showToast("Hệ thống đang bận. Vui lòng thử lại sau.", "error"); }
}

function checkInitialState() {
    if (localStorage.getItem('is_logged_in') === 'true') {
        if (localStorage.getItem('current_role') === 'admin') window.location.href = 'admin.html';
        else { showAboutPage(); updateHeaderUI(); }
    } else { showAboutPage(); updateHeaderUI(); }
}

function updateHeaderUI() {
    const isLoggedIn = localStorage.getItem('is_logged_in');
    const avatar = document.getElementById('user-avatar');
    const loginBtn = document.getElementById('nav-login-btn');
    if (isLoggedIn === 'true') {
        loginBtn.style.display = 'none';
        loginBtn.classList.remove('btn-fade-in');
        avatar.innerHTML = (localStorage.getItem('current_user') || 'U').charAt(0).toUpperCase();
        avatar.style.background = 'linear-gradient(135deg, #b8860b, #d4af37, #f5e09a)';
        avatar.style.color = '#5c3d00';
        avatar.style.display = 'flex';
    } else {
        loginBtn.style.display = 'block';
        void loginBtn.offsetWidth;
        loginBtn.classList.add('btn-fade-in');
        avatar.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="#8b6508" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
        avatar.style.background = 'rgba(180,140,20,0.08)';
        avatar.style.color = '#8b6508';
        avatar.style.display = 'flex';
    }
}

function hideAllScreens() {
    ['profile-screen', 'home-screen', 'review-screen', 'service-screen', 'about-screen'].forEach(id => {
        let el = document.getElementById(id); if (el) el.style.display = 'none';
    });
    let search = document.getElementById('search-bar');
    if (search) { search.style.display = 'none'; search.classList.remove('search-bar--docked'); }
    
    const header = document.querySelector('.header');
    const footer = document.querySelector('.footer-modern');
    if (header) header.style.display = 'flex';
    if (footer) footer.style.display = 'block';
    
    const toggleBtn = document.getElementById('search-bar-toggle-btn');
    if (toggleBtn) toggleBtn.style.display = '';
}

function showHomePage() { hideAllScreens(); document.getElementById('customer-view').style.display = 'block'; document.getElementById('home-screen').style.display = 'block'; const sb = document.getElementById('search-bar'); if (sb) sb.style.display = 'flex'; renderRooms(); }
function scrollToReviewForm() {
    const form = document.querySelector('.rv-form-section');
    if (form) form.scrollIntoView({ behavior: 'smooth' });
}

function showAboutPage() {
    hideAllScreens();
    document.getElementById('customer-view').style.display = 'block';
    
    const header = document.querySelector('.header');
    const footer = document.querySelector('.footer-modern');
    if (header) header.style.display = 'none';
    if (footer) footer.style.display = 'none';

    const aboutScreen = document.getElementById('about-screen');
    if (aboutScreen) aboutScreen.style.display = 'block';
    window.scrollTo(0, 0);
}

function showReviewPage() {
    hideAllScreens();
    document.getElementById('customer-view').style.display = 'block';
    document.getElementById('review-screen').style.display = 'block';
    initReviewForm();
    replayHeroAnimation('#rv-hero');
    renderReviews();
}

function replayHeroAnimation(selector = '.rv-hero') {
    const hero = document.querySelector(selector);
    if (!hero) return;
    hero.classList.remove('rv-play');
    void hero.offsetWidth;
    hero.classList.add('rv-play');
}
function showServicePage() {
    hideAllScreens();
    document.getElementById('customer-view').style.display = 'block';
    document.getElementById('service-screen').style.display = 'block';
    replayHeroAnimation('#svc-hero');
    renderCustomerServices();
}
function showProfilePage() { if (localStorage.getItem('is_logged_in') !== 'true') return openLoginModal(); hideAllScreens(); document.getElementById('customer-view').style.display = 'block'; document.getElementById('profile-screen').style.display = 'block'; switchProfileTab('info'); }

function openLoginModal() { document.getElementById('login-modal').style.display = 'flex'; document.getElementById('register-modal').style.display = 'none'; document.body.style.overflow = 'hidden'; }
function closeLoginModal() { document.getElementById('login-modal').style.display = 'none'; document.body.style.overflow = ''; }
function openRegisterModal() { document.getElementById('register-modal').style.display = 'flex'; document.getElementById('login-modal').style.display = 'none'; document.body.style.overflow = 'hidden'; }
function closeRegisterModal() { document.getElementById('register-modal').style.display = 'none'; document.body.style.overflow = ''; }
function switchToRegister() { openRegisterModal(); }
function switchToLogin() { openLoginModal(); }

async function renderReviews() {
    const container = document.getElementById('review-list'); if (!container) return;
    container.innerHTML = 'Đang tải...';
    try {
        const response = await fetch('/api/reviews');
        const rawReviews = await response.json();

        const reviews = rawReviews.map(r => {
            let extra = {};
            try { extra = JSON.parse(r.content); if (typeof extra !== 'object' || extra === null) extra = { note: r.content }; }
            catch (e) { extra = { note: r.content }; }
            return {
                customerName: r.customerName, date: r.date, stars: r.stars, image: r.image,
                note: extra.note || '', roomType: extra.roomType || '', stayFrom: extra.stayFrom || '', stayTo: extra.stayTo || '',
                roomScore: (typeof extra.roomScore === 'number') ? extra.roomScore : null,
                serviceScore: (typeof extra.serviceScore === 'number') ? extra.serviceScore : null
            };
        });

        const count = reviews.length;
        const avgStars = count ? (reviews.reduce((s, r) => s + (r.stars || 0), 0) / count) : 0;
        const roomScores = reviews.filter(r => r.roomScore !== null).map(r => r.roomScore);
        const serviceScores = reviews.filter(r => r.serviceScore !== null).map(r => r.serviceScore);
        const avgRoom = roomScores.length ? (roomScores.reduce((a, b) => a + b, 0) / roomScores.length) : (avgStars / 5 * 100);
        const avgService = serviceScores.length ? (serviceScores.reduce((a, b) => a + b, 0) / serviceScores.length) : (avgStars / 5 * 100);
        animateReviewStats(count, avgStars, avgRoom, avgService);

        container.innerHTML = '';
        if (count === 0) { container.innerHTML = '<p style="text-align:center; color:#888; padding: 30px 0;">Chưa có đánh giá nào. Hãy là người đầu tiên chia sẻ cảm nhận!</p>'; return; }

        const personIcon = `<svg viewBox="0 0 24 24"><path d="M12 12c2.5 0 4.5-2 4.5-4.5S14.5 3 12 3 7.5 5 7.5 7.5 9.5 12 12 12zm0 1.5c-3 0-9 1.5-9 4.5V21h18v-3c0-3-6-4.5-9-4.5z"/></svg>`;

        container.innerHTML = reviews.map((r, idx) => {
            const starsHTML = '★'.repeat(r.stars) + '☆'.repeat(5 - r.stars);
            const noteId = `rv-note-${idx}`;
            const stayHTML = (r.stayFrom || r.stayTo) ? `<div>Stayed: ${r.stayFrom || '?'} → ${r.stayTo || '?'}</div>` : '';
            const scoresHTML = (r.roomScore !== null || r.serviceScore !== null) ? `
                <div class="rv-item-scores">
                    ${r.roomScore !== null ? `<span>Phòng: <b>${r.roomScore}%</b></span>` : ''}
                    ${r.serviceScore !== null ? `<span>Dịch vụ: <b>${r.serviceScore}%</b></span>` : ''}
                </div>` : '';
            const imgHTML = r.image ? `<img loading="lazy" src="${r.image}" class="rv-item-image" loading="lazy" decoding="async">` : '';
            const noteText = r.note || '';
            const needsExpand = noteText.length > 140;

            return `
                <div class="rv-item">
                    <div class="rv-avatar">${personIcon}</div>
                    <div class="rv-item-body">
                        <div class="rv-item-head">
                            <div>
                                <div class="rv-item-name">${r.customerName ? r.customerName.toUpperCase() : 'KHÁCH'}</div>
                                ${r.roomType ? `<span class="rv-item-roomtype">${r.roomType}</span>` : ''}
                            </div>
                            <div class="rv-item-dates">
                                <div>Posted: ${r.date}</div>
                                ${stayHTML}
                            </div>
                        </div>
                        <div class="rv-item-stars">${starsHTML}</div>
                        <div class="rv-item-category">Cảm nhận trải nghiệm</div>
                        <p class="rv-item-content" id="${noteId}">${noteText}</p>
                        ${needsExpand ? `<button class="rv-see-more" onclick="toggleReviewExpand('${noteId}', this)">Xem thêm</button>` : ''}
                        ${scoresHTML}
                        ${imgHTML}
                    </div>
                </div>`;
        }).join('');

        observeReviewItems();
    } catch (e) { container.innerHTML = '<p style="color:red;">Lỗi tải đánh giá</p>'; }
}

let rvStatsAnimated = false;
function animateReviewStats(count, avgStars, avgRoom, avgService) {
    const statsEl = document.getElementById('rv-stats');
    if (!statsEl) return;
    rvStatsAnimated = false;
    const run = () => {
        if (rvStatsAnimated) return; rvStatsAnimated = true;
        const countEl = document.getElementById('rv-stat-count');
        const start = performance.now(), duration = 900;
        function tick(now) {
            const p = Math.min(1, (now - start) / duration);
            countEl.innerText = Math.round(count * p);
            if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);

        const fullStars = Math.round(avgStars);
        document.getElementById('rv-stat-stars').innerText = '★'.repeat(fullStars) + '☆'.repeat(5 - fullStars);

        document.getElementById('rv-bar-room').style.width = avgRoom.toFixed(1) + '%';
        document.getElementById('rv-pct-room').innerText = avgRoom.toFixed(1) + '%';
        document.getElementById('rv-bar-service').style.width = avgService.toFixed(1) + '%';
        document.getElementById('rv-pct-service').innerText = avgService.toFixed(1) + '%';
    };
    const obs = new IntersectionObserver(entries => { entries.forEach(e => { if (e.isIntersecting) { run(); obs.disconnect(); } }); }, { threshold: 0.3 });
    obs.observe(statsEl);
}

function observeReviewItems() {
    const items = document.querySelectorAll('.rv-item');
    const obs = new IntersectionObserver(entries => {
        entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('rv-visible'); obs.unobserve(e.target); } });
    }, { threshold: 0.15 });
    items.forEach(el => obs.observe(el));
}

function toggleReviewExpand(noteId, btn) {
    const el = document.getElementById(noteId);
    el.classList.toggle('rv-expanded');
    btn.innerText = el.classList.contains('rv-expanded') ? 'Thu lại' : 'Xem thêm';
}

let rvSelectedStars = 5;
let rvFormInitialized = false;
function initReviewForm() {
    const nameInput = document.getElementById('review-fullname-input');
    if (nameInput && !nameInput.value) nameInput.value = localStorage.getItem('current_user') || '';

    if (rvFormInitialized) return;
    rvFormInitialized = true;

    const stars = document.querySelectorAll('#rv-star-picker .rv-star');
    function paintStars(n) { stars.forEach(s => s.classList.toggle('rv-filled', parseInt(s.dataset.value) <= n)); }
    function spawnStarSparkles(starEl) {
        for (let i = 0; i < 5; i++) {
            const sp = document.createElement('span');
            sp.className = 'rv-star-sparkle';
            const angle = Math.random() * Math.PI * 2;
            const dist = 14 + Math.random() * 16;
            sp.style.setProperty('--sx', Math.cos(angle) * dist + 'px');
            sp.style.setProperty('--sy', Math.sin(angle) * dist + 'px');
            starEl.appendChild(sp);
            sp.addEventListener('animationend', () => sp.remove());
        }
    }
    paintStars(rvSelectedStars);
    stars.forEach(s => {
        s.addEventListener('mouseenter', () => paintStars(parseInt(s.dataset.value)));
        s.addEventListener('click', () => {
            rvSelectedStars = parseInt(s.dataset.value);
            paintStars(rvSelectedStars);
            s.classList.remove('rv-pop'); void s.offsetWidth; s.classList.add('rv-pop');
            spawnStarSparkles(s);
        });
    });
    document.getElementById('rv-star-picker').addEventListener('mouseleave', () => paintStars(rvSelectedStars));

    const roomSlider = document.getElementById('rv-room-slider'), roomVal = document.getElementById('rv-room-slider-val');
    const svcSlider = document.getElementById('rv-service-slider'), svcVal = document.getElementById('rv-service-slider-val');
    function updateSliderFill(slider, label) {
        slider.style.setProperty('--rv-progress', slider.value + '%');
        label.innerText = slider.value + '%';
    }
    updateSliderFill(roomSlider, roomVal);
    updateSliderFill(svcSlider, svcVal);
    roomSlider.addEventListener('input', () => updateSliderFill(roomSlider, roomVal));
    svcSlider.addEventListener('input', () => updateSliderFill(svcSlider, svcVal));

    const fileInput = document.getElementById('review-image-input');
    const uploadBox = document.getElementById('rv-upload-box');
    function handleReviewFile(file) {
        const nameSpan = document.getElementById('rv-upload-name');
        const preview = document.getElementById('rv-upload-preview');
        preview.innerHTML = '';
        if (file) {
            nameSpan.innerText = file.name;
            uploadBox.classList.add('rv-has-file');
            const reader = new FileReader();
            reader.onload = () => { preview.innerHTML = `<img loading="lazy" src="${reader.result}">`; };
            reader.readAsDataURL(file);
        } else {
            nameSpan.innerText = 'Kéo & thả ảnh vào đây, hoặc bấm để chọn';
            uploadBox.classList.remove('rv-has-file');
        }
    }
    fileInput.addEventListener('change', () => handleReviewFile(fileInput.files[0] || null));
    ['dragenter', 'dragover'].forEach(evt => uploadBox.addEventListener(evt, e => { e.preventDefault(); uploadBox.classList.add('rv-dragover'); }));
    ['dragleave', 'drop'].forEach(evt => uploadBox.addEventListener(evt, e => { e.preventDefault(); uploadBox.classList.remove('rv-dragover'); }));
    uploadBox.addEventListener('drop', e => {
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            fileInput.files = e.dataTransfer.files;
            handleReviewFile(file);
        } else if (file) {
            showToast("Vui lòng chỉ kéo thả file ảnh!", "error");
        }
    });
}

async function submitReview() {
    if (localStorage.getItem('is_logged_in') !== 'true') {
        showToast("Bạn cần đăng nhập bằng tài khoản Khách hàng trước khi gửi đánh giá!", "error");
        return openLoginModal();
    }

    const fullname = document.getElementById('review-fullname-input').value.trim() || (localStorage.getItem('current_user') || "Khách");
    const roomType = document.getElementById('review-roomtype-input').value;
    const stayFrom = document.getElementById('review-stay-from').value;
    const stayTo = document.getElementById('review-stay-to').value;
    const note = document.getElementById('review-content-input').value.trim();
    const roomScore = parseInt(document.getElementById('rv-room-slider').value);
    const serviceScore = parseInt(document.getElementById('rv-service-slider').value);

    if (!note) return showToast("Vui lòng nhập nội dung đánh giá!", "error");
    if (!roomType) return showToast("Vui lòng chọn loại phòng đã ở!", "error");

    const fileInput = document.getElementById('review-image-input');
    let base64Image = "";
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        if (file.size > 2 * 1024 * 1024) return showToast("Ảnh quá nặng! Vui lòng chọn ảnh dưới 2MB.", "error");
        base64Image = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(file);
        });
    }

    const contentPayload = JSON.stringify({ note, roomType, stayFrom, stayTo, roomScore, serviceScore });

    const reviewData = {
        customer_name: fullname,
        stars: rvSelectedStars,
        content: contentPayload,
        username: localStorage.getItem('current_username') || "",
        image: base64Image
    };

    const submitBtn = document.getElementById('rv-submit-btn');
    submitBtn.classList.add('rv-loading');

    try {
        const response = await fetch('/api/reviews/submit', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(reviewData)
        });
        if (response.ok) {
            showToast("Cảm ơn bạn đã gửi đánh giá! Ý kiến của bạn rất quý giá với chúng tôi.", "success");
            submitBtn.classList.remove('rv-loading');
            submitBtn.classList.add('rv-success');
            setTimeout(() => submitBtn.classList.remove('rv-success'), 1800);
            document.getElementById('review-content-input').value = '';
            document.getElementById('review-image-input').value = '';
            document.getElementById('rv-upload-name').innerText = 'Kéo & thả ảnh vào đây, hoặc bấm để chọn';
            document.getElementById('rv-upload-box').classList.remove('rv-has-file');
            document.getElementById('rv-upload-preview').innerHTML = '';
            renderReviews();
        } else {
            submitBtn.classList.remove('rv-loading');
            showToast("Có lỗi xảy ra khi gửi đánh giá. Vui lòng thử lại.", "error");
        }
    } catch (e) {
        submitBtn.classList.remove('rv-loading');
        showToast("Hệ thống đang bận. Vui lòng thử lại sau.", "error");
    }
}

const SVC_IMAGE_RULES = [
    { keys: ['spa', 'massage', 'xông hơi', 'thư giãn'], img: 'https://images.unsplash.com/photo-1540555700478-4be289fbecef?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['đón', 'sân bay', 'taxi', 'xe', 'đưa'], img: 'https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['sáng', 'buffet', 'ăn', 'nhà hàng', 'tối', 'ẩm thực'], img: 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['giặt', 'ủi', 'là'], img: 'https://images.unsplash.com/photo-1545173168-9f1947eebb7f?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['bơi', 'pool'], img: 'https://images.unsplash.com/photo-1572331165267-854da2b10ccf?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['gym', 'tập', 'thể dục', 'fitness'], img: 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['họp', 'hội nghị', 'hội trường', 'sự kiện'], img: 'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['trẻ', 'em bé', 'thiếu nhi'], img: 'https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['karaoke', 'giải trí'], img: 'https://images.unsplash.com/photo-1598387993441-a364f854c3e1?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['wifi', 'internet', 'mạng'], img: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['bar', 'minibar', 'đồ uống', 'cocktail'], img: 'https://images.unsplash.com/photo-1551024601-bec78aea704b?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['dọn phòng', 'vệ sinh'], img: 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
    { keys: ['tour', 'tham quan', 'du lịch'], img: 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70' },
];
const SVC_FALLBACK_IMAGES = [
    'https://images.unsplash.com/photo-1564501049412-61c2a3083791?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70',
    'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70',
    'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70',
    'https://images.unsplash.com/photo-1519449556851-5720b33024e7?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&q=70',
];
function getServiceImage(name, idx) {
    const lower = (name || '').toLowerCase();
    const rule = SVC_IMAGE_RULES.find(r => r.keys.some(k => lower.includes(k)));
    return rule ? rule.img : SVC_FALLBACK_IMAGES[idx % SVC_FALLBACK_IMAGES.length];
}

async function renderCustomerServices() {
    const container = document.getElementById('service-list'); if (!container) return;
    container.innerHTML = `<div class="room-skeleton"></div><div class="room-skeleton"></div><div class="room-skeleton"></div>`;
    try {
        const response = await fetch('/api/admin/services');
        const services = await response.json();

        if (!services.length) {
            container.innerHTML = `
                <div style="grid-column:1/-1; text-align:center; padding: 80px 20px; color: #8a7550;">
                    <div style="font-size:32px; margin-bottom:16px; opacity:0.4;">◈</div>
                    <p style="font-size:14px; letter-spacing:1px;">Hiện chưa có dịch vụ nào trong hệ thống</p>
                </div>`;
            return;
        }

        container.innerHTML = services.map((s, idx) => `
            <div class="room-card">
                <div class="room-card-img-wrap">
                    <span class="status-badge status-category">${s.category || 'Tiện ích'}</span>
                    <span class="room-card-num">HUCE Hotel</span>
                    <img loading="lazy" src="${getServiceImage(s.name, idx)}" alt="${s.name}" loading="lazy">
                </div>
                <div class="room-card-body">
                    <p class="room-card-type">Dịch vụ cao cấp</p>
                    <h3 class="room-card-name">${s.name}</h3>
                    <div class="room-card-divider"></div>
                    <div class="room-card-price-row">
                        <span class="room-card-price">${s.price.toLocaleString('vi-VN')}</span>
                        <span class="room-card-unit">VND</span>
                    </div>
                    <div class="svc-note">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>
                        Có thể chọn thêm ngay khi đặt phòng
                    </div>
                </div>
            </div>
        `).join('');

        container.querySelectorAll('.room-card').forEach((card, i) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(24px)';
            setTimeout(() => {
                card.style.transition = 'opacity 0.5s ease, transform 0.5s cubic-bezier(0.22,1,0.36,1), box-shadow 0.4s, border-color 0.3s';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, i * 90 + 80);
        });

    } catch (e) {
        container.innerHTML = `
            <div style="grid-column:1/-1; text-align:center; padding:60px 20px; color:#c0392b;">
                <p style="font-size:14px;">Không tải được dịch vụ từ Server. Vui lòng kiểm tra main.py / SQL Server.</p>
            </div>`;
    }
}

async function renderRooms(roomsToRender = null) {
    const container = document.getElementById("room-container");
    if(!container) return;

    container.innerHTML = `
        <div class="room-skeleton"></div>
        <div class="room-skeleton"></div>
        <div class="room-skeleton"></div>
    `;
    
    try {
        let displayRooms = roomsToRender;
        if (!displayRooms) {
            const username = localStorage.getItem('current_username') || '';
            const response = await fetch(`/api/rooms?username=${username}`);
            displayRooms = await response.json();
        }
        
        displayRooms.forEach(r => { if(r.name) r.name = window.translateRoomName(r.name); });
        
        container.innerHTML = ""; 
        if (displayRooms.length === 0) return container.innerHTML = `
            <div style="grid-column:1/-1; text-align:center; padding: 80px 20px; color: #8a7550;">
                <div style="font-size:32px; margin-bottom:16px; opacity:0.4;">◈</div>
                <p style="font-size:14px; letter-spacing:1px;">Không tìm thấy phòng nào phù hợp với bộ lọc</p>
            </div>`;
        
        const fragment = document.createDocumentFragment();
        const tempDiv = document.createElement('div');

        const luxuryImages = [
            "https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=1200&q=80"
        ];
        const bentoClasses = ['bento-large', 'bento-tall', 'bento-small', 'bento-wide', 'bento-small', 'bento-small'];

        displayRooms.forEach((room, idx) => {
            let badgeHTML = '';
            let buttonHTML = '';
            let cardExtraStyle = '';

           if (room.isMyRoom) {
            badgeHTML = `<span class="status-badge status-mine">Phòng của bạn</span>`;
            buttonHTML = `<button class="book-btn btn-mine" onclick="showToast('Bạn đang sử dụng phòng này. Xem chi tiết ở mục Cá nhân!','info')">Đang sử dụng</button>`;
            cardExtraStyle = 'border-color: rgba(14,165,233,0.4); box-shadow: 0 8px 28px rgba(14,165,233,0.12);';
        } else {
            if (room.isAvailable) {
                badgeHTML = `<span class="status-badge status-ready">Còn trống</span>`;
            } else {
                badgeHTML = `<span class="status-badge status-occupied">Đang có khách</span>`;
                cardExtraStyle = 'opacity: 0.9;';
            }
            buttonHTML = `<button class="book-btn" onclick="attemptToBook('${room.id}', '${room.name}', ${room.price})">Chọn ngày đặt</button>`;
        }

            const typeLabel = (room.name.includes('Suite') || room.name.includes('VIP')) ? 'Suite · Hạng sang' 
                            : (room.name.includes('Deluxe') || room.name.includes('Cao Cấp')) ? 'Deluxe · Cao cấp'
                            : 'Standard · Tiêu chuẩn';
                            
            const imageSrc = luxuryImages[idx % luxuryImages.length];

            tempDiv.innerHTML = `
                <div class="room-card" style="${cardExtraStyle}">
                    <div class="room-card-img-wrap">
                        ${badgeHTML}
                        <span class="room-card-num">Phòng ${room.roomNumber}</span>
                        <img loading="lazy" src="${imageSrc}" alt="${room.name}" loading="lazy" decoding="async">
                    </div>
                    <div class="room-card-body">
                        <p class="room-card-type">${typeLabel}</p>
                        <h3 class="room-card-name">${room.name}</h3>
                        <div class="room-card-divider"></div>
                        <div class="room-card-price-row">
                            <span class="room-card-price">${room.price.toLocaleString('vi-VN')}</span>
                            <span class="room-card-unit">VND / đêm</span>
                        </div>
                        ${buttonHTML}
                    </div>
                </div>`;
            fragment.appendChild(tempDiv.firstElementChild);
        });
        container.appendChild(fragment);

        container.querySelectorAll('.room-card').forEach((card, i) => {
            const imgWrap = card.querySelector('.room-card-img-wrap');
            if (imgWrap && displayRooms[i]) {
                imgWrap.addEventListener('click', () => openRoomDetail(displayRooms[i]));
            }
            card.style.opacity = '0';
            card.style.transform = 'translateY(24px)';
            setTimeout(() => {
                card.style.transition = 'opacity 0.5s ease, transform 0.5s cubic-bezier(0.22,1,0.36,1), box-shadow 0.4s, border-color 0.3s';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, i * 90 + 80);
        });

    } catch (error) { 
        container.innerHTML = `
            <div style="grid-column:1/-1; text-align:center; padding:60px 20px; color:#c0392b;">
                <p style="font-size:13px;">⚠ Lỗi kết nối CSDL — Kiểm tra file <code>main.py</code> và SQL Server</p>
            </div>`;
    }
}

let detailRoom = null;

function getRoomTypeLabel(name) {
    if (name.includes('Suite') || name.includes('VIP')) return 'Suite · Hạng sang';
    if (name.includes('Deluxe') || name.includes('Cao Cấp')) return 'Deluxe · Cao cấp';
    return 'Standard · Tiêu chuẩn';
}

function openRoomDetail(room) {
    detailRoom = room;
    const fallbackImg = 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=900&q=80';
    const imgEl = document.getElementById('detail-room-img');
    imgEl.src = room.image || fallbackImg;
    imgEl.onerror = function() { this.onerror = null; this.src = fallbackImg; };

    document.getElementById('detail-room-type').textContent = getRoomTypeLabel(room.name);
    document.getElementById('detail-room-name').textContent = room.name;
    document.getElementById('detail-room-number').textContent = room.roomNumber;
    document.getElementById('detail-room-beds').textContent = room.beds ?? 1;
    document.getElementById('detail-room-max').textContent = room.maxPeople ?? 1;
    document.getElementById('detail-room-desc').textContent =
        'Phòng được trang bị đầy đủ tiện nghi hiện đại, không gian rộng rãi và thoáng mát.';
    document.getElementById('detail-room-price').textContent = Number(room.price).toLocaleString('vi-VN');

    const badge = document.getElementById('detail-room-status-badge');
    const bookBtn = document.getElementById('detail-book-btn');
    const unavailableMsg = document.getElementById('detail-unavailable-msg');
    const availableDiv = document.getElementById('detail-room-available');

    if (room.isMyRoom) {
        badge.textContent = '● PHÒNG CỦA BẠN';
        badge.className = 'room-detail-badge status-mine-detail';
        bookBtn.style.display = 'none';
        unavailableMsg.style.display = 'block';
        unavailableMsg.textContent = 'Bạn đang sử dụng phòng này. Xem chi tiết ở mục Cá nhân!';
        availableDiv.textContent = '';
    } else if (room.isAvailable) {
        badge.textContent = '● SẴN SÀNG';
        badge.className = 'room-detail-badge status-ready-detail';
        bookBtn.style.display = 'block';
        unavailableMsg.style.display = 'none';
        availableDiv.innerHTML = `<span style="display:flex;align-items:center;gap:6px;color:#22c55e;font-weight:500;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>Phòng đang sẵn sàng đón khách</span>`;
    } else {
        badge.textContent = '● ĐANG CÓ KHÁCH';
        badge.className = 'room-detail-badge status-occupied-detail';
        bookBtn.style.display = 'none';
        unavailableMsg.style.display = 'block';
        unavailableMsg.textContent = 'Phòng hiện đang có khách lưu trú';
        availableDiv.innerHTML = room.availableFrom
            ? `<span style="display:flex;align-items:center;gap:6px;color:#f59e0b;font-weight:500;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>Dự kiến trống từ: ${room.availableFrom}</span>`
            : '';
    }

    document.getElementById('modal-room-detail').showModal();
}

function closeRoomDetail() {
    document.getElementById('modal-room-detail').close();
}

function bookFromDetail() {
    closeRoomDetail();
    if (detailRoom) attemptToBook(detailRoom.id, detailRoom.name, detailRoom.price);
}

async function searchRooms() {
    const selectedType = document.getElementById('room-type-search').value;
    const priceRange = document.getElementById('room-price-search').value;
    const [minPrice, maxPrice] = priceRange.split('-').map(Number);
    const username = localStorage.getItem('current_username') || '';

    let checkin = '';
    let checkout = '';
    const dateRangeStr = document.getElementById('search-date-range') ? document.getElementById('search-date-range').value : '';
    if (dateRangeStr.includes(' to ')) {
        const parts = dateRangeStr.split(' to ');
        const parseDate = (d) => {
            const [day, month, year] = d.split('/');
            return `${year}-${month.padStart(2,'0')}-${day.padStart(2,'0')}`;
        };
        checkin = parseDate(parts[0]);
        checkout = parseDate(parts[1]);
    }

    const totalGuests = guestCounts.adults + guestCounts.children;

    try {
        const params = new URLSearchParams({
            checkin: checkin || '',
            checkout: checkout || '',
            guests: totalGuests,
            room_type: selectedType,
            min_price: priceRange !== '0-999999999' ? minPrice : 0,
            max_price: priceRange !== '0-999999999' ? maxPrice : 999999999,
            username
        });
        const response = await fetch(`/api/rooms/search?${params}`);
        const allRooms = await response.json();
        
        renderRooms(allRooms);
        document.querySelector('.room-section').scrollIntoView({ behavior: 'smooth' });
    } catch (error) { 
        showToast("Có lỗi xảy ra khi tải danh sách phòng.", "error"); 
        console.error(error);
    }
}

let currentBookingRoom = null;
let bookingNights = 1;

async function attemptToBook(roomId, roomName, price) {
    if (localStorage.getItem('is_logged_in') !== 'true') { 
        showToast("Vui lòng đăng nhập trước khi đặt phòng!", "error"); 
        return openLoginModal(); 
    }
    
    currentBookingRoom = { id: roomId, name: roomName, price: price };
    
    const ciInput = document.getElementById('booking-checkin-input');
    const coInput = document.getElementById('booking-checkout-input');
    if (ciInput) ciInput.type = 'text';
    if (coInput) coInput.type = 'text';
    
    document.getElementById('booking-room-name').innerText = roomName;
    document.getElementById('booking-guest-name').innerText = localStorage.getItem('current_user') || "Khách hàng";
    
    ciInput.value = '';
    coInput.value = '';
    document.getElementById('booking-nights-badge').innerText = '0 đêm';
    document.getElementById('invoice-nights').innerText = '0';
    updateBookingTotal();
    
    // destroy old flatpickr instances to recreate them with new disabled dates
    if(window.bookingCheckinPicker) window.bookingCheckinPicker.destroy();
    if(window.bookingCheckoutPicker) window.bookingCheckoutPicker.destroy();
    let disabledDates = [];
    try {
        const res = await fetch(`/api/rooms/${roomId}/booked-dates`);
        if (res.ok) disabledDates = await res.json(); 
    } catch(e) { console.log("Không tải được lịch kẹt của phòng này."); }

    const modalElem = document.getElementById('booking-modal');
    
    function createModalFlatpickr(selector, opts) {
        return flatpickr(selector, {
            ...opts,
            appendTo: modalElem,
            onReady: function(sDates, dStr, instance) {
                instance.positionCalendar = function() {
                    if (!instance.calendarContainer || !instance.isOpen) return;
                    const inputRect = instance.element.getBoundingClientRect();
                    const modalRect = modalElem.getBoundingClientRect();
                    const calWidth = instance.calendarContainer.offsetWidth || 307;
                    const inputCenter = inputRect.left + (inputRect.width / 2);
                    let idealLeft = inputCenter - (calWidth / 2) - modalRect.left;
                    
                    const minLeft = 10;
                    const maxLeft = modalRect.width - calWidth - 10;
                    if (idealLeft < minLeft) idealLeft = minLeft;
                    if (idealLeft > maxLeft) idealLeft = maxLeft;

                    instance.calendarContainer.style.position = 'absolute';
                    instance.calendarContainer.style.top = (inputRect.bottom - modalRect.top + 6) + 'px';
                    instance.calendarContainer.style.left = idealLeft + 'px';
                    instance.calendarContainer.style.zIndex = '99999';
                };
                if (opts.onReady) opts.onReady(sDates, dStr, instance);
            },
            onOpen: function(sDates, dStr, instance) {
                const reposition = () => { if (instance.positionCalendar) instance.positionCalendar(); };
                reposition();
                requestAnimationFrame(reposition);
                setTimeout(reposition, 10);
                setTimeout(reposition, 50);
                setTimeout(reposition, 150);
                if (opts.onOpen) opts.onOpen(sDates, dStr, instance);
            }
        });
    }

    const checkoutPicker = createModalFlatpickr("#booking-checkout-input", {
        minDate: "today",
        disable: disabledDates,
        dateFormat: "Y-m-d",
        onChange: function() { recalculateBooking(); }
    });
    window.bookingCheckoutPicker = checkoutPicker;

    const checkinPicker = createModalFlatpickr("#booking-checkin-input", {
        minDate: "today",
        disable: disabledDates,
        dateFormat: "Y-m-d",
        onChange: function(selectedDates, dateStr) {
            if (selectedDates[0]) {
                let nextDay = new Date(selectedDates[0]);
                nextDay.setDate(nextDay.getDate() + 1);
                checkoutPicker.set('minDate', nextDay);
            }
            recalculateBooking();
        }
    });
    window.bookingCheckinPicker = checkinPicker;

    ['#booking-checkin-input', '#booking-checkout-input'].forEach(sel => {
        const inp = document.querySelector(sel);
        if (inp) {
            inp.onclick = function() {
                if (this._flatpickr) {
                    this._flatpickr.open();
                    if (this._flatpickr.positionCalendar) {
                        this._flatpickr.positionCalendar();
                        setTimeout(() => { if (this._flatpickr && this._flatpickr.positionCalendar) this._flatpickr.positionCalendar(); }, 20);
                    }
                }
            };
        }
    });
    
    const contentLayout = modalElem.querySelector('.booking-content-layout');
    if (contentLayout) {
        contentLayout.onscroll = function() {
            if (window.bookingCheckinPicker && window.bookingCheckinPicker.isOpen) window.bookingCheckinPicker.positionCalendar();
            if (window.bookingCheckoutPicker && window.bookingCheckoutPicker.isOpen) window.bookingCheckoutPicker.positionCalendar();
        };
    }
    
    const sList = document.getElementById('booking-services-list'); 
    sList.innerHTML = '<p style="font-size:13px; color:#666;">Đang tải danh sách dịch vụ...</p>';
    try {
        const response = await fetch('/api/admin/services');
        const activeServices = await response.json(); 
        sList.innerHTML = '';
        activeServices.forEach(s => {
            sList.innerHTML += `
                <label class="service-item-card">
                    <input type="checkbox" class="booking-service-cb hidden-cb" value="${s.price}" data-name="${s.name}" onchange="updateBookingTotal()">
                    <div class="svc-card-content">
                        <div class="svc-left">
                            <div class="svc-checkbox-custom"></div>
                            <span class="svc-name">${s.name}</span>
                        </div>
                        <span class="svc-price">+${s.price.toLocaleString('vi-VN')} đ</span>
                    </div>
                </label>
            `;
        });
        updateBookingTotal();
        document.getElementById('booking-modal').showModal();
    } catch(e) { showToast("Không tải được dịch vụ!", "error"); }
}
function recalculateBooking() {
    let ciVal = document.getElementById('booking-checkin-input').value;
    let coVal = document.getElementById('booking-checkout-input').value;
    if(!ciVal || !coVal) return;

    let ciDate = new Date(ciVal);
    let coDate = new Date(coVal);

    if(coDate <= ciDate) {
        coDate = new Date(ciDate.getTime() + 24 * 60 * 60 * 1000);
        const formatForInput = (d) => { return d.getFullYear() + '-' + (d.getMonth() + 1).toString().padStart(2, '0') + '-' + d.getDate().toString().padStart(2, '0'); };
        document.getElementById('booking-checkout-input').value = formatForInput(coDate);
    }

    let diffHours = Math.ceil((coDate - ciDate) / (1000 * 60 * 60));
    let calculatedNights = Math.ceil(diffHours / 24);
    if (calculatedNights <= 0) calculatedNights = 1;

    bookingNights = calculatedNights;

    let timeText = diffHours < 24 ? `${diffHours} giờ` : `${bookingNights} đêm`;
    let invoiceText = diffHours < 24 ? diffHours : bookingNights;
    document.getElementById('booking-nights-badge').innerText = timeText;
    document.getElementById('invoice-nights').innerText = invoiceText;

    updateBookingTotal();
}

async function submitBooking() {
    let svcs = []; 
    document.querySelectorAll('.booking-service-cb:checked').forEach(cb => { svcs.push(cb.getAttribute('data-name')); });
    
    let totalStr = document.getElementById('booking-total-price').innerText.replace(/\D/g,'');

    const bookingData = {
        username: localStorage.getItem('current_username'), 
        room_id: currentBookingRoom.id, 
        checkin: document.getElementById('booking-checkin-input').value,
        checkout: document.getElementById('booking-checkout-input').value,
        total_price: parseFloat(totalStr), 
        services: svcs
    };

    try {
        const response = await fetch('/api/bookings', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(bookingData)
        });
        if (response.ok) {
            showToast(`Đặt phòng thành công! Cảm ơn quý khách đã tin tưởng HUCE Hotel.`, "success"); 
            closeBookingModal(); 
            renderRooms(); 
        } else { showToast("Có lỗi xảy ra trong quá trình xử lý đặt phòng. Vui lòng thử lại.", "error"); }
    } catch (e) { showToast("Hệ thống đang bận. Vui lòng thử lại sau.", "error"); }
}

function updateBookingTotal() {
    let roomTotal = currentBookingRoom.price * bookingNights;
    document.getElementById('booking-room-total-price').innerText = roomTotal.toLocaleString('vi-VN') + ' đ';
    
    let servicesTotal = 0;
    document.querySelectorAll('.booking-service-cb:checked').forEach(cb => { 
        servicesTotal += parseInt(cb.value); 
    });
    document.getElementById('booking-services-total-price').innerText = servicesTotal.toLocaleString('vi-VN') + ' đ';
    
    let subTotal = roomTotal + servicesTotal;
    let vatPercent = window.globalVat || 0;
    let vatAmount = Math.round(subTotal * (vatPercent / 100));
    
    const vatPercentEl = document.getElementById('booking-vat-percent');
    if (vatPercentEl) vatPercentEl.innerText = vatPercent;
    const vatPriceEl = document.getElementById('booking-vat-price');
    if (vatPriceEl) vatPriceEl.innerText = '+' + vatAmount.toLocaleString('vi-VN') + ' đ';
    
    let grandTotal = subTotal + vatAmount;
    document.getElementById('booking-total-price').innerText = grandTotal.toLocaleString('vi-VN') + ' VND';
}

function closeBookingModal() { document.getElementById('booking-modal').close(); }

function switchProfileTab(tabName) {
    document.querySelectorAll('.tab-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.getElementById(`tab-menu-${tabName}`).classList.add('active');
    document.getElementById(`tab-content-${tabName}`).style.display = 'block';
    
    if (window.customerHistoryPolling) {
        clearInterval(window.customerHistoryPolling);
        window.customerHistoryPolling = null;
    }
    
    if (tabName === 'info') loadProfileData();
    if (tabName === 'history') {
        loadBookingHistory(false);
        window.customerHistoryPolling = setInterval(() => loadBookingHistory(true), 5000);
    }
    if (tabName === 'services') loadUsedServices();
}

async function loadProfileData() {
    let username = localStorage.getItem('current_username');
    try {
        const res = await fetch(`/api/profile?username=${username}`);
        const user = await res.json();
        document.getElementById('profile-avatar-large').innerText = user.fullname.charAt(0).toUpperCase();
        document.getElementById('profile-name-display').innerText = user.fullname;
        document.getElementById('prof-fullname').value = user.fullname;
        document.getElementById('prof-email').value = user.email; 
        document.getElementById('prof-phone').value = user.phone;
        document.getElementById('prof-idcard').value = user.idcard;
        document.getElementById('prof-address').value = user.address;
    } catch(e) { showToast("Không thể tải thông tin hồ sơ.", "error"); }
}

async function updateProfile() {
    const data = {
        username: localStorage.getItem('current_username'),
        fullname: document.getElementById('prof-fullname').value.trim(),
        phone: document.getElementById('prof-phone').value.trim(),
        idcard: document.getElementById('prof-idcard').value.trim(),
        address: document.getElementById('prof-address').value.trim()
    };
    try {
        const response = await fetch('/api/profile/update', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
        });
        if(response.ok) {
            localStorage.setItem('current_user', data.fullname); updateHeaderUI();
            showToast("Cập nhật thông tin cá nhân thành công.", "success");
        }
    } catch(e) { showToast("Lỗi kết nối", "error"); }
}

async function loadBookingHistory(isPolling = false) {
    let username = localStorage.getItem('current_username');
    const tbody = document.getElementById('history-tbody'); 
    if (!isPolling) tbody.innerHTML = 'Đang truy vấn...';
    try {
        const res = await fetch(`/api/profile/history?username=${username}`);
        const history = await res.json(); 
        
        let newHTML = '';
        if(history.length === 0) newHTML = `<tr><td colspan="5">Chưa có đơn đặt phòng nào.</td></tr>`;
        else {
            history.forEach(b => {
                newHTML += `<tr><td><strong>${b.id}</strong></td><td>${b.roomName}</td><td>${b.checkin} - ${b.checkout}</td><td><span class="badge confirmed">${b.status}</span></td><td>${b.totalPrice.toLocaleString()}đ</td></tr>`;
            });
        }
        
        if (tbody.innerHTML !== newHTML) tbody.innerHTML = newHTML;
    } catch(e) { if (!isPolling) tbody.innerHTML = 'Lỗi kết nối.'; }
}

async function loadUsedServices() {
    let username = localStorage.getItem('current_username');
    const tbody = document.getElementById('services-tbody'); if(!tbody) return; tbody.innerHTML = 'Đang truy vấn...';
    try {
        const res = await fetch(`/api/profile/services?username=${username}`);
        const svcs = await res.json(); tbody.innerHTML = '';
        if(svcs.length === 0) return tbody.innerHTML = `<tr><td colspan="5">Bạn chưa sử dụng dịch vụ đi kèm nào.</td></tr>`;
        svcs.forEach(s => {
            tbody.innerHTML += `<tr><td><strong>${s.id}</strong></td><td>${s.serviceName}</td><td>${s.date}</td><td>${s.quantity}</td><td>${s.total.toLocaleString()}đ</td></tr>`;
        });
    } catch(e) { tbody.innerHTML = 'Lỗi kết nối.'; }
}

async function changePassword() {
    const oldPass = document.getElementById('old-password').value;
    const newPass = document.getElementById('new-password').value;
    const confirmPass = document.getElementById('confirm-new-password').value;
    
    if (!oldPass || !newPass || !confirmPass) return showToast("Vui lòng điền đầy đủ các ô mật khẩu!", "error");
    if (newPass !== confirmPass) return showToast("Mật khẩu mới gõ lại không khớp!", "error");
    if (oldPass === newPass) return showToast("Mật khẩu mới phải khác mật khẩu hiện tại!", "error");
    
    const data = {
        username: localStorage.getItem('current_username'),
        old_password: oldPass,
        new_password: newPass
    };
    
    try {
        const res = await fetch('/api/profile/password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (res.ok) {
            showToast("Đổi mật khẩu thành công.", "success");
            document.getElementById('old-password').value = '';
            document.getElementById('new-password').value = '';
            document.getElementById('confirm-new-password').value = '';
        } else {
            const err = await res.json();
            showToast(err.detail, "error");
        }
    } catch (e) {
        showToast("Hệ thống đang bận. Vui lòng thử lại sau.", "error");
    }
}
function resetData() { localStorage.clear(); initData(); showHomePage(); showToast("Dữ liệu phiên duyệt web đã được làm sạch.", "info"); }

function showAdminPage() {
    hideAllScreens();
    document.getElementById('customer-view').style.display = 'none'; 
    document.getElementById('admin-screen').style.display = 'flex';
    switchAdminTab('rooms');
}

function switchAdminTab(tabId) {
    document.querySelectorAll('.admin-nav-menu li').forEach(li => li.classList.remove('active'));
    let navEl = document.getElementById('nav-admin-' + tabId); if (navEl) navEl.classList.add('active');
    document.querySelectorAll('.admin-tab-content').forEach(content => content.style.display = 'none');
    let tabEl = document.getElementById('admin-tab-' + tabId); if (tabEl) tabEl.style.display = 'block';

    if (tabId === 'rooms') renderAdminRooms();
    if (tabId === 'room-types') renderAdminRoomTypes();
    if (tabId === 'bookings') renderAdminBookings();
    if (tabId === 'services') renderAdminServices();
    if (tabId === 'settings') renderAdminSettings();
}

async function renderAdminRooms() {
    const tbody = document.getElementById('admin-rooms-tbody'); 
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:24px;">Đang tải...</td></tr>';
    try {
        const res = await fetch('/api/admin/rooms');
        const rooms = await res.json(); 
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

            const roomEmoji = room.name && room.name.toLowerCase().includes('suite') ? '🛎️' : room.name && room.name.toLowerCase().includes('deluxe') ? '🛏️' : '🏠';
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
                    <button class="btn-action" onclick="mockUpdateStatus('${room.id}')">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                        Đổi trạng thái
                    </button>
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

async function mockUpdateStatus(roomId) {
    try {
        const res = await fetch(`/api/admin/rooms/status/${roomId}`, { method: 'POST' });
        if (res.ok) { 
            showToast("Cập nhật trạng thái phòng thành công.", "success"); 
            renderAdminRooms(); 
            
            localStorage.setItem('sync_trigger', Date.now());
        }
    } catch(e) { showToast("Lỗi đổi trạng thái!", "error"); }
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
        const typeEmojis = ['🏠', '🛏️', '🛎️', '👑', '🌟'];
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
    } catch(e) { showToast("Lỗi tìm kiếm", "error"); }
}

async function renderAdminBookings(customData = null) {
    const tbody = document.getElementById('admin-bookings-tbody'); tbody.innerHTML = 'Đang lấy dữ liệu...';
    try {
        let bookings = customData;
        if (!bookings) {
            const res = await fetch('/api/admin/bookings');
            bookings = await res.json();
        }
        tbody.innerHTML = '';
        if(bookings.length === 0) tbody.innerHTML = '<tr><td colspan="6">Không thấy đơn đặt phòng nào.</td></tr>';
        bookings.forEach(b => {
            tbody.innerHTML += `<tr>
                <td><strong>${b.id}</strong></td><td>${b.customerName}</td><td>${b.checkin} - ${b.checkout}</td><td>${b.totalPrice.toLocaleString()}đ</td><td><span class="badge confirmed">${b.status}</span></td>
                <td><button class="btn-action-outline" onclick="showToast('Chức năng lập HD thật đang phát triển','info')">Lập HD</button></td>
            </tr>`;
        });
    } catch(e) { tbody.innerHTML = 'Lỗi nạp đơn hàng.'; }
}

async function searchAdminBookings() {
    let kw = document.getElementById('admin-search-booking-input').value.trim();
    try {
        const res = await fetch(`/api/admin/bookings?keyword=${encodeURIComponent(kw)}`);
        const data = await res.json(); renderAdminBookings(data);
    } catch(e) { showToast("Lỗi tìm kiếm", "error"); }
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
    } catch(e) { showToast("Lỗi tìm kiếm", "error"); }
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
    } catch(e) { showToast("Lỗi nạp cấu hình hệ thống!", "error"); }
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
            showToast("Lưu cấu hình hệ thống thành công.", "success");
            
            localStorage.setItem('sync_trigger', Date.now());
        }
    } catch(e) { showToast("Lỗi lưu cấu hình", "error"); }
}

function initHeroParticles() {
    const canvas = document.getElementById('hero-particles');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, particles = [], rafId = null, isVisible = true;

    function resize() {
        W = canvas.width  = canvas.offsetWidth;
        H = canvas.height = canvas.offsetHeight;
    }
    resize();
    let resizeTimer;
    window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(resize, 200); });

    const COLORS = ['rgba(212,175,55,', 'rgba(245,217,122,', 'rgba(180,134,11,'];

    for (let i = 0; i < 30; i++) {
        particles.push({
            x: Math.random() * W,
            y: Math.random() * H,
            r: Math.random() * 1.8 + 0.4,
            alpha: Math.random() * 0.5 + 0.1,
            vx: (Math.random() - 0.5) * 0.3,
            vy: -(Math.random() * 0.4 + 0.1),
            color: COLORS[Math.floor(Math.random() * COLORS.length)],
            twinkleSpeed: Math.random() * 0.02 + 0.005,
            twinkleDir: 1,
        });
    }

    function draw() {
        if (!isVisible) { rafId = null; return; }
        ctx.clearRect(0, 0, W, H);
        particles.forEach(p => {
            p.alpha += p.twinkleSpeed * p.twinkleDir;
            if (p.alpha >= 0.65 || p.alpha <= 0.05) p.twinkleDir *= -1;
            p.x += p.vx; p.y += p.vy;
            if (p.y < -4) { p.y = H + 4; p.x = Math.random() * W; }
            if (p.x < -4) p.x = W + 4;
            if (p.x > W + 4) p.x = -4;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = p.color + p.alpha + ')';
            ctx.fill();
        });
        rafId = requestAnimationFrame(draw);
    }

    const visObs = new IntersectionObserver(entries => {
        isVisible = entries[0].isIntersecting;
        if (isVisible && !rafId) draw();
    }, { threshold: 0 });
    visObs.observe(canvas);

    draw();
}

function initHeroSpotlight() {
    const hero   = document.getElementById('hero-banner');
    const spot   = document.getElementById('hero-spotlight');
    if (!hero || !spot) return;

    hero.addEventListener('mousemove', e => {
        const rect = hero.getBoundingClientRect();
        spot.style.left = (e.clientX - rect.left) + 'px';
        spot.style.top  = (e.clientY - rect.top)  + 'px';
        spot.style.opacity = '1';
    });
    hero.addEventListener('mouseleave', () => { spot.style.opacity = '0'; });
}

function initHeroParallax() {
    const hero = document.getElementById('hero-banner');
    if (!hero) return;
    
    // Scroll Parallax
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(() => {
            const y = window.scrollY;
            if (y < hero.offsetHeight) {
                hero.style.setProperty('--parallax-y', (y * 0.3) + 'px');
            }
            ticking = false;
        });
    }, { passive: true });

    // 3D Tilt Effect on mousemove
    const inner = hero.querySelector('.hero-inner');
    if (inner) {
        hero.addEventListener('mousemove', (e) => {
            const rect = hero.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = ((y - centerY) / centerY) * -12; // Max 12 deg tilt
            const rotateY = ((x - centerX) / centerX) * 12;
            
            inner.style.transition = 'none'; // remove transition for smooth tracking
            inner.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
        
        hero.addEventListener('mouseleave', () => {
            inner.style.transition = 'transform 0.6s cubic-bezier(0.23, 1, 0.32, 1)';
            inner.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg)`;
        });
    }
}

function initCountUp() {
    const nums = document.querySelectorAll('.hero-stat-num');
    if (!nums.length) return;

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el = entry.target;
            const target = parseInt(el.dataset.target);
            const duration = target > 100 ? 1600 : 900;
            const start = performance.now();

            function update(now) {
                const elapsed = now - start;
                const progress = Math.min(elapsed / duration, 1);
                const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
                el.textContent = Math.floor(ease * target).toLocaleString('vi-VN');
                if (progress < 1) requestAnimationFrame(update);
                else el.textContent = target.toLocaleString('vi-VN');
            }
            requestAnimationFrame(update);
            observer.unobserve(el);
        });
    }, { threshold: 0.6 });

    nums.forEach(n => observer.observe(n));
}

function initScrollReveal() {
    const targets = [
        '.section-label', '.section-title-main', '.section-desc', '.section-rule'
    ];
    targets.forEach((sel, i) => {
        document.querySelectorAll(sel).forEach(el => {
            el.classList.add('reveal', `reveal-delay-${i}`);
        });
    });

    const observer = new IntersectionObserver(entries => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                e.target.classList.add('visible');
                observer.unobserve(e.target);
            }
        });
    }, { threshold: 0.15 });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

function addRippleEffect() {
    document.addEventListener('click', e => {
        const btn = e.target.closest('.book-btn');
        if (!btn || btn.disabled) return;

        const rect = btn.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * 1.5;
        const ripple = document.createElement('span');
        ripple.className = 'ripple';
        ripple.style.cssText = `
            width:${size}px; height:${size}px;
            left:${e.clientX - rect.left - size/2}px;
            top:${e.clientY - rect.top - size/2}px;
        `;
        btn.appendChild(ripple);
        ripple.addEventListener('animationend', () => ripple.remove());
    });
}

function initHomeAnimations() {
    initHeroParticles();
    initHeroSpotlight();
    initHeroParallax();
    initScrollReveal();
    addRippleEffect();
}

let guestCounts = { adults: 1, children: 0 };

function initSearchFields() {
    if (document.getElementById('search-date-range')) {
        flatpickr("#search-date-range", {
            mode: "range",
            dateFormat: "d/m/Y",
            minDate: "today",
            static: true,
            monthSelectorType: "static"
        });
    }

    const guestInput = document.getElementById('search-guests-display');
    const guestPopover = document.getElementById('guest-popover');
    
    if (guestInput && guestPopover) {
        guestInput.addEventListener('click', (e) => {
            e.stopPropagation();
            guestPopover.classList.toggle('show');
        });
        guestPopover.addEventListener('click', (e) => e.stopPropagation());
        document.addEventListener('click', () => {
            guestPopover.classList.remove('show');
        });

        function updateGuestDisplay() {
            document.getElementById('adult-count').textContent = guestCounts.adults;
            document.getElementById('child-count').textContent = guestCounts.children;
            let text = `${guestCounts.adults} Người lớn`;
            if (guestCounts.children > 0) text += `, ${guestCounts.children} Trẻ em`;
            guestInput.value = text;
        }

        document.getElementById('adult-minus').addEventListener('click', () => {
            if (guestCounts.adults > 1) { guestCounts.adults--; updateGuestDisplay(); }
        });
        document.getElementById('adult-plus').addEventListener('click', () => {
            if (guestCounts.adults < 10) { guestCounts.adults++; updateGuestDisplay(); }
        });
        document.getElementById('child-minus').addEventListener('click', () => {
            if (guestCounts.children > 0) { guestCounts.children--; updateGuestDisplay(); }
        });
        document.getElementById('child-plus').addEventListener('click', () => {
            if (guestCounts.children < 10) { guestCounts.children++; updateGuestDisplay(); }
        });
    }
}

function initSearchChoices() {
    const typeEl = document.getElementById('room-type-search');
    const priceEl = document.getElementById('room-price-search');
    
    if (typeEl && !typeEl.dataset.choicesInit) {
        new Choices(typeEl, { searchEnabled: false, itemSelectText: '', shouldSort: false, position: 'top' });
        typeEl.dataset.choicesInit = 'true';
    }
    if (priceEl && !priceEl.dataset.choicesInit) {
        new Choices(priceEl, { searchEnabled: false, itemSelectText: '', shouldSort: false, position: 'top' });
        priceEl.dataset.choicesInit = 'true';
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initHomeAnimations();
        initSearchChoices();
        initSearchFields();
    });
} else {
    initHomeAnimations();
    initSearchChoices();
    initSearchFields();
}

initData(); 
renderRooms(); 
checkInitialState();

window.addEventListener('load', function() {
    function initReviewDatePickers() {
        if (document.getElementById('review-stay-from')._flatpickr) return;
        const fpFrom = flatpickr("#review-stay-from", {
            locale: "vn", dateFormat: "d/m/Y",
            disableMobile: true,
            onChange: function(selectedDates) {
                if (selectedDates[0]) fpTo.set('minDate', selectedDates[0]);
            }
        });
        const fpTo = flatpickr("#review-stay-to", {
            locale: "vn", dateFormat: "d/m/Y",
            disableMobile: true,
            onChange: function(selectedDates) {
                if (selectedDates[0]) fpFrom.set('maxDate', selectedDates[0]);
            }
        });
    }

    function initReviewChoices() {
        const el = document.getElementById('review-roomtype-input');
        if (el && !el.dataset.choicesInit) {
            new Choices(el, {
                searchEnabled: false,
                itemSelectText: '',
                shouldSort: false,
            });
            el.dataset.choicesInit = 'true';
        }
    }

    const _origShowReviewPage = showReviewPage;
    showReviewPage = function() {
        _origShowReviewPage();
        setTimeout(() => { initReviewDatePickers(); initReviewChoices(); }, 50);
    };

    (function() {
        const searchBar = document.getElementById('search-bar');
        const roomAnchor = document.getElementById('room-anchor');
        if (!searchBar || !roomAnchor) return;

        let lastScrollY = window.scrollY;
        let ticking = false;
        let manuallyOpened = false;
        const threshold = 5;

        function setHidden(hidden) {
            searchBar.classList.toggle('search-bar-hidden', hidden);
        }

        function onScroll() {
            const currentScrollY = window.scrollY;
            const anchorTop = roomAnchor.getBoundingClientRect().top + window.scrollY;
            const pastAnchor = currentScrollY >= anchorTop - 80;

            if (!pastAnchor) {
                setHidden(true);
                lastScrollY = currentScrollY;
                manuallyOpened = false;
                ticking = false;
                return;
            }

            const diff = currentScrollY - lastScrollY;
            if (Math.abs(diff) > threshold) {
                if (diff > 0 && !manuallyOpened) {
                    setHidden(true);
                } else if (diff < 0) {
                    setHidden(false);
                    manuallyOpened = false;
                }
                lastScrollY = currentScrollY;
            }
            ticking = false;
        }

        window.addEventListener('scroll', function() {
            if (!ticking) {
                window.requestAnimationFrame(onScroll);
                ticking = true;
            }
        }, { passive: true });

        if (toggleBtn) {
            toggleBtn.addEventListener('click', function() {
                setHidden(false);
                manuallyOpened = true;
                lastScrollY = window.scrollY;
            });
        }

        onScroll();
    })();
});

window.addEventListener('storage', function(e) {
    if (e.key === 'sync_trigger') {
        
        initData();
        
        const homeScreen = document.getElementById('home-screen');
        if (homeScreen && homeScreen.style.display !== 'none') {
            renderRooms(); 
        }
        
        const serviceScreen = document.getElementById('service-screen');
        if (serviceScreen && serviceScreen.style.display !== 'none') {
            renderCustomerServices();
        }
    }
});

function openAdminModal(id) { document.getElementById(id).classList.add('open'); }
function closeAdminModal(id) { document.getElementById(id).classList.remove('open'); }

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
            showToast(id ? 'Đã cập nhật phòng!' : 'Đã thêm phòng mới!', 'success');
        } else {
            const err = await res.json();
            showToast('Lỗi: ' + (err.detail || 'Không thể lưu'), 'error');
        }
    } catch(e) { showToast('Lỗi kết nối server!', 'error'); }
}

function deleteRoom(roomId, soPhong) {
    document.getElementById('modal-delete-msg').textContent = `Bạn có chắc muốn xóa phòng số ${soPhong} (${roomId})? Hành động này không thể hoàn tác.`;
    document.getElementById('modal-delete-confirm-btn').onclick = async () => {
        try {
            const res = await fetch(`/api/admin/rooms/${roomId}`, { method: 'DELETE' });
            if (res.ok) {
                closeAdminModal('modal-confirm-delete');
                renderAdminRooms();
                showToast('Đã xóa phòng!', 'success');
            } else {
                const err = await res.json();
                showToast('Lỗi: ' + (err.detail || 'Không thể xóa'), 'error');
                closeAdminModal('modal-confirm-delete');
            }
        } catch(e) { showToast('Lỗi kết nối server!', 'error'); }
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
            showToast(id ? 'Đã cập nhật loại phòng!' : 'Đã thêm loại phòng mới!', 'success');
        } else {
            const err = await res.json();
            showToast('Lỗi: ' + (err.detail || 'Không thể lưu'), 'error');
        }
    } catch(e) { showToast('Lỗi kết nối server!', 'error'); }
}

function deleteRoomType(id, ten) {
    document.getElementById('modal-delete-msg').textContent = `Bạn có chắc muốn xóa loại phòng "${ten}" (${id})? Chỉ xóa được nếu không có phòng nào thuộc loại này.`;
    document.getElementById('modal-delete-confirm-btn').onclick = async () => {
        try {
            const res = await fetch(`/api/admin/room-types/${id}`, { method: 'DELETE' });
            if (res.ok) {
                closeAdminModal('modal-confirm-delete');
                renderAdminRoomTypes();
                showToast('Đã xóa loại phòng!', 'success');
            } else {
                const err = await res.json();
                showToast('Lỗi: ' + (err.detail || 'Không thể xóa'), 'error');
                closeAdminModal('modal-confirm-delete');
            }
        } catch(e) { showToast('Lỗi kết nối server!', 'error'); }
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
            showToast(id ? 'Đã cập nhật dịch vụ!' : 'Đã thêm dịch vụ mới!', 'success');
        } else {
            const err = await res.json();
            showToast('Lỗi: ' + (err.detail || 'Không thể lưu'), 'error');
        }
    } catch(e) { showToast('Lỗi kết nối server!', 'error'); }
}

function deleteService(id, ten) {
    document.getElementById('modal-delete-msg').textContent = `Bạn có chắc muốn xóa dịch vụ "${ten}" (${id})?`;
    document.getElementById('modal-delete-confirm-btn').onclick = async () => {
        try {
            const res = await fetch(`/api/admin/services/${id}`, { method: 'DELETE' });
            if (res.ok) {
                closeAdminModal('modal-confirm-delete');
                renderAdminServices();
                showToast('Đã xóa dịch vụ!', 'success');
            } else {
                const err = await res.json();
                showToast('Lỗi: ' + (err.detail || 'Không thể xóa'), 'error');
                closeAdminModal('modal-confirm-delete');
            }
        } catch(e) { showToast('Lỗi kết nối server!', 'error'); }
    };
    openAdminModal('modal-confirm-delete');
}

function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    navMenu.classList.toggle('mobile-active');
}

window.addEventListener('click', function(e) {
    if (e.target.id === 'login-modal') closeLoginModal();
    if (e.target.id === 'register-modal') closeRegisterModal();
    if (e.target.id === 'modal-room-detail') closeRoomDetail();
});

// Smart header logic (hide on scroll down, show on scroll up)
let lastScrollY = window.scrollY;
window.addEventListener('scroll', () => {
    const header = document.querySelector('.header');
    if (!header) return;
    const currentScrollY = window.scrollY;
    
    // Only apply logic if scrolled past header height
    if (currentScrollY > 74) {
        if (currentScrollY > lastScrollY) {
            // Scrolling down
            header.classList.add('header-hidden');
        } else {
            // Scrolling up
            header.classList.remove('header-hidden');
        }
    } else {
        // At the top of the page
        header.classList.remove('header-hidden');
    }
    
    lastScrollY = currentScrollY;
});
