import os
import sys
import time
from crewai import Agent, Crew, Process, Task, LLM

# Sửa lỗi in emoji (🚀) trên Windows Terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 1. CẤU HÌNH CÁC BỘ NÃO AI (ĐA NỀN TẢNG: CLOUD + LOCAL)
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "")
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

# 1. Groq Cloud (Mô hình 8B để tránh bị giới hạn Token)
llm_groq = LLM(model="groq/llama-3.1-8b-instant", api_key=os.environ["GROQ_API_KEY"], temperature=0.1, timeout=120)

# 2. Google Cloud (Rất thông minh, cho phép 1 Triệu Token/phút)
llm_gemini = LLM(model="gemini/gemini-2.0-flash", api_key=os.environ["GEMINI_API_KEY"], temperature=0.1, timeout=120)

# 3. Local AI (Chạy trên máy bạn, miễn phí trọn đời)
llm_local = LLM(
    model="ollama/llama3.1",
    base_url="http://localhost:11434",
    temperature=0.7,
    timeout=300
)

# 2. KHAI BÁO AGENTS PHÂN CÔNG CHO TỪNG AI
dev_agent = Agent(
    role="Senior Frontend Developer",
    goal="Viết mã CSS chuẩn xác theo yêu cầu thiết kế Responsive cho màn hình Mobile. Sửa triệt để các lỗi do QA báo.",
    backstory="Bạn là chuyên gia UI/UX. Bạn viết mã CSS sạch, dùng đúng class và tuân thủ yêu cầu responsive.",
    llm=llm_local, 
    verbose=True,
    max_iter=15,
    max_retry_limit=5
)

tester_agent = Agent(
    role="Strict CSS QA Tester",
    goal="Soi mã CSS cực kỳ khắt khe để xem có đúng yêu cầu của Phase hiện tại không.",
    backstory="""Nhận code CSS từ Dev và test.
    Bạn phải ĐỌC KỸ MÔ TẢ NHIỆM VỤ (Task Description) để biết Phase hiện tại yêu cầu những gì.
    - Nếu THIẾU hoặc SAI: Trả về dòng đầu là 'STATUS: FAILED' kèm chi tiết lỗi yêu cầu Dev làm lại.
    - Nếu ĐÚNG 100% tất cả checklist: Trả về dòng đầu là 'STATUS: PASSED'.""",
    llm=llm_local, 
    verbose=True,
    max_iter=15,
    max_retry_limit=5
)

ux_agent = Agent(
    role="CSS Formatter",
    goal="Định dạng lại mã CSS cho đẹp, thêm comment rõ ràng.",
    backstory="Chuyên gia làm sạch code CSS.",
    verbose=True,
    llm=llm_local 
)

packager_agent = Agent(
    role="Code Packager",
    goal="Đóng gói đoạn code sạch đã qua kiểm thử.",
    backstory="Kỹ sư xuất file code chuẩn chỉnh.",
    verbose=True,
    llm=llm_local 
)

# 3. DANH SÁCH 11 PHASE (KỊCH BẢN TỰ LÁI)
PHASES = [
    {
        "id": "Phase 1",
        "name": "Cấu trúc Layout & Thanh Điều hướng (Sidebar)",
        "req": "Thực hiện Phase 1 cho màn hình < 768px: 1. .admin-layout ngừng dùng flex-direction: row. 2. Sidebar đổi transform thành left: -300px để ẩn triệt để. (Bọc trong @media max-width: 768px)",
        "qa": "Nếu vẫn còn dùng flex-direction: row cho .admin-layout, hoặc Sidebar thiếu left: -300px, hoặc không có @media -> Trả về STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "admin-mobile-phase1.css"
    },
    {
        "id": "Phase 2",
        "name": "Khung chứa & Padding (Main Content)",
        "req": "Thực hiện Phase 2 cho màn hình < 768px: 1. Thu nhỏ padding của .admin-main-content xuống 15px. 2. Tiêu đề .admin-page-header xếp dọc (flex-direction: column). (Bọc trong @media)",
        "qa": "Nếu .admin-main-content không có padding: 15px, hoặc .admin-page-header không xếp dọc -> STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "admin-mobile-phase2.css"
    },
    {
        "id": "Phase 3",
        "name": "Thanh Tìm kiếm & Nút hành động",
        "req": "Thực hiện Phase 3 cho màn hình < 768px: 1. Ô tìm kiếm .admin-search-wrap mở rộng 100% chiều ngang. 2. Các nút hành động dãn 100% chiều rộng. (Bọc trong @media)",
        "qa": "Nếu .admin-search-wrap hoặc các nút hành động không có width 100% -> STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "admin-mobile-phase3.css"
    },
    {
        "id": "Phase 4",
        "name": "Thẻ Thống kê (Stats Cards)",
        "req": "Thực hiện Phase 4 cho màn hình < 768px: 1. .admin-stats-grid thành lưới 2 cột (grid-template-columns: repeat(2, 1fr)). 2. Giảm font-size cho tiêu đề/số liệu xuống 14px. (Bọc trong @media)",
        "qa": "Nếu thiếu lưới 2 cột (repeat(2, 1fr) hoặc 50%), hoặc thiếu giảm font-size -> STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "admin-mobile-phase4.css"
    },
    {
        "id": "Phase 5",
        "name": "Bảng Dữ liệu (Data Tables)",
        "req": "Thực hiện Phase 5 cho màn hình < 768px: 1. .admin-table-container thêm overflow-x: auto. 2. Ô dữ liệu thêm white-space: nowrap để chặn bẻ dòng. (Bọc trong @media)",
        "qa": "Nếu thiếu overflow-x: auto hoặc white-space: nowrap -> STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "admin-mobile-phase5.css"
    },
    {
        "id": "Phase 6",
        "name": "Cửa sổ bật lên (Admin Modals)",
        "req": "Thực hiện Phase 6 cho màn hình < 768px: 1. .admin-modal-box chiếm 95% màn hình (width: 95%). (Bọc trong @media)",
        "qa": "Nếu .admin-modal-box không có width: 95% -> STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "admin-mobile-phase6.css"
    },
    {
        "id": "Phase 7",
        "name": "Header & Menu Điều hướng Public",
        "req": "Thực hiện Phase 7 cho màn hình < 768px: 1. Tinh chỉnh Header chiều cao 60px. 2. Tinh chỉnh khoảng cách nút bấm Đăng nhập/Đăng ký margin 5px. (Bọc trong @media)",
        "qa": "Nếu không có chiều cao 60px hoặc thiếu căn chỉnh nút -> STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "public-mobile-phase7.css"
    },
    {
        "id": "Phase 8",
        "name": "Hero Banner & Số liệu Public",
        "req": "Thực hiện Phase 8 cho màn hình < 768px: 1. Đưa dải số liệu vào lưới 2 cột (grid-template-columns: repeat(2, 1fr)). 2. Tối ưu kích thước chữ tiêu đề chính xuống 24px. (Bọc trong @media)",
        "qa": "Nếu không có lưới 2 cột cho số liệu hoặc tiêu đề không giảm size -> STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "public-mobile-phase8.css"
    },
    {
        "id": "Phase 9",
        "name": "Cụm Tìm kiếm (Search Bar) Public",
        "req": "Thực hiện Phase 9 cho màn hình < 768px: 1. Khối tìm kiếm đổi thành khối dọc (flex-direction: column). 2. Các trường width: 100%. (Bọc trong @media)",
        "qa": "Nếu thiếu flex-direction: column hoặc width: 100% -> STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "public-mobile-phase9.css"
    },
    {
        "id": "Phase 10",
        "name": "Thẻ Phòng, Đánh giá Public",
        "req": "Thực hiện Phase 10 cho màn hình < 768px: 1. Danh sách phòng chuyển về 1 cột (grid-template-columns: 1fr). 2. Cố định height: 200px cho ảnh bìa phòng. (Bọc trong @media)",
        "qa": "Nếu thiếu 1 cột (1fr) hoặc không có height 200px cho ảnh -> STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "public-mobile-phase10.css"
    },
    {
        "id": "Phase 11",
        "name": "Footer & Modals Khách hàng",
        "req": "Thực hiện Phase 11 cho màn hình < 768px: 1. Footer căn giữa (text-align: center) và xếp dọc các liên kết (flex-direction: column). (Bọc trong @media)",
        "qa": "Nếu không có text-align: center hoặc flex-direction: column ở Footer -> STATUS: FAILED. Nếu đúng -> STATUS: PASSED.",
        "out": "public-mobile-phase11.css"
    }
]

print("🚀 KHỞI ĐỘNG CỖ MÁY AUTO-PILOT (11 PHASES)...")

# Khởi tạo file chung (Ghi đè trắng file cũ trước khi chạy vòng lặp mới)
with open("admin-mobile-final.css", "w", encoding="utf-8") as f:
    f.write("/* ADMIN MOBILE FINAL CSS - AUTO GENERATED (11 PHASES) */\n")

for phase in PHASES:
    print(f"\n=======================================================")
    print(f"🌟 ĐANG CHẠY {phase['id']}: {phase['name']}")
    print(f"=======================================================")
    
    feedback = ""
    is_passed = False
    max_attempts = 4
    attempt = 0
    
    while not is_passed and attempt < max_attempts:
        attempt += 1
        print(f"\n🔄 --- {phase['id']} - LẦN THỬ THỨ {attempt}/{max_attempts} ---")
        
        dev_prompt = f"Yêu cầu bài toán:\n{phase['req']}\n"
        if feedback:
            dev_prompt += f"\n⚠️ [CẢNH BÁO LỖI TỪ QA]:\n{feedback}\n👉 Hãy sửa lại code!"

        task_dev = Task(description=dev_prompt, expected_output="Đoạn code CSS", agent=dev_agent)
        
        qa_prompt = f"Test code CSS Dev vừa viết. \n{phase['qa']}"
        task_qa = Task(
            description=qa_prompt,
            expected_output="STATUS: PASSED hoặc FAILED",
            agent=tester_agent
        )
        
        dev_qa_crew = Crew(
            agents=[dev_agent, tester_agent],
            tasks=[task_dev, task_qa],
            process=Process.sequential,
            verbose=True,
            max_rpm=10
        )
        
        try:
            qa_result = str(dev_qa_crew.kickoff())
        except Exception as e:
            print(f"\n⚠️ LỖI API (Rate Limit/Timeout): {str(e)[:80]}...")
            print("⏳ Hệ thống tự động ngủ đông 60s để phục hồi...")
            time.sleep(60)
            attempt -= 1
            continue
        
        if "STATUS: PASSED" in qa_result:
            print(f"\n✅ QA ĐÃ DUYỆT PASS CHO {phase['id']}!")
            is_passed = True
        else:
            print(f"\n❌ QA BÁO FAILED! Đang chuyển phản hồi cho Dev sửa...")
            feedback = qa_result
            if attempt < max_attempts:
                print(f"⏳ Nghỉ 20 giây để hệ thống ổn định...")
                time.sleep(20)

    # ĐÓNG GÓI VÀ NỐI VÀO FILE CHUNG
    if is_passed:
        print(f"\n🎨 Đang tối ưu định dạng CSS và NỐI GỘP file cho {phase['id']}...")
        task_ux = Task(description="Rà soát và format lại mã CSS cho đẹp mắt.", expected_output="Code CSS đã chuẩn hóa.", agent=ux_agent)
        task_final = Task(description=f"Đóng gói code CSS cuối cùng cho {phase['id']}.", expected_output="File code.", agent=packager_agent) # Đã bỏ output_file
        
        try:
            final_result = Crew(agents=[ux_agent, packager_agent], tasks=[task_ux, task_final], process=Process.sequential, verbose=True).kickoff()
            
            # Ghi nối tiếp (Append) vào file chung
            with open("admin-mobile-final.css", "a", encoding="utf-8") as f:
                f.write(f"\n\n/* ==================== {phase['id'].upper()} ==================== */\n")
                f.write(str(final_result))
                f.write("\n")
                
            print(f"\n🎉 XONG! {phase['id']} đã được NỐI THÊM thành công vào: admin-mobile-final.css")
        except Exception as e:
            print(f"\n⚠️ Lỗi đóng gói: {str(e)[:100]}")
    else:
        print(f"\n🛑 Thất bại sau 4 lần thử tại {phase['id']}. HỆ THỐNG SẼ TỰ ĐỘNG BỎ QUA VÀ CHẠY PHASE TIẾP THEO!")
        time.sleep(5)
        
print("\n🏆 QUÁ TRÌNH AUTO-PILOT ĐÃ HOÀN TẤT 11 PHASES! HÃY KIỂM TRA FILE: admin-mobile-final.css")