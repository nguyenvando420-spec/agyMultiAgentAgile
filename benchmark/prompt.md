KHÔNG sử dụng bất kỳ công cụ nào (không đọc/ghi file, không chạy lệnh, không tìm web). Trả lời TOÀN BỘ trong MỘT câu trả lời duy nhất.
Phần văn xuôi viết bằng tiếng Việt, ngắn gọn dạng gạch đầu dòng. Mỗi phần BẮT ĐẦU bằng đúng một dòng tiêu đề dạng `=== TASK X ===` (X là A, B, C, D, E, F, G) và theo đúng thứ tự.

=== ĐỀ TASK A (Phản biện thiết kế) ===
Dưới đây là thiết kế "Ví điện tử - Nạp tiền" của một team. Liệt kê TẤT CẢ lỗi/rủi ro nghiêm trọng khi chạy Production, mỗi lỗi 1 dòng: [mức độ] vấn đề → hậu quả → cách sửa. Không cần khen.

```
- Stack: Node.js API, 1 instance PostgreSQL (không replica), Redis cache.
- Bảng wallets(id, user_id, balance FLOAT, updated_at).
- Luồng nạp: client gọi POST /topup {amount, card_number, cvv} → API gọi cổng thanh toán (timeout 5s).
  Nếu timeout → đánh dấu giao dịch FAILED và báo lỗi cho user.
- Cổng thanh toán gọi webhook POST /webhook/payment {txn_id, status, amount}. API xử lý:
  wallet = SELECT balance FROM wallets WHERE user_id=?; newBalance = wallet.balance + amount;
  UPDATE wallets SET balance = newBalance WHERE user_id=?
- Logging: ghi toàn bộ request body vào log để dễ debug.
- Auth: JWT ký HS256, secret "wallet-secret-2024" đặt trong config.js, token hết hạn sau 365 ngày.
- API GET /transactions trả về toàn bộ lịch sử giao dịch của user.
- Backup: chưa cần ở giai đoạn MVP.
```

=== ĐỀ TASK B (Lập trình) ===
Viết module Python `duration.py` với hàm `parse_duration(s) -> int` trả về tổng số giây. Đặc tả CHÍNH XÁC:
1. Nếu `s` không phải `str` → raise `TypeError`.
2. Bỏ qua khoảng trắng (whitespace) ở đầu và cuối chuỗi. Chuỗi rỗng sau khi bỏ → `ValueError`.
3. Chuỗi gồm 1 hoặc nhiều thành phần `<số><đơn vị>`; `<số>` là chuỗi chữ số ASCII 0-9 (cho phép số 0 đứng đầu như "05", không dấu +/-, không thập phân); `<đơn vị>` là một trong `d` (86400s), `h` (3600s), `m` (60s), `s` (1s), CHỈ chữ thường.
4. Giữa các thành phần có thể có 0 hoặc nhiều dấu cách (space). Không được có khoảng trắng giữa số và đơn vị.
5. Các đơn vị phải xuất hiện theo thứ tự giảm dần d → h → m → s, mỗi đơn vị tối đa 1 lần (bỏ qua đơn vị nào cũng được). Sai thứ tự hoặc lặp → `ValueError`.
6. Số trong một thành phần không giới hạn theo đơn vị (ví dụ "90m" hợp lệ = 5400).
7. Nếu tổng số giây > 315360000 → raise `OverflowError`. (Bằng đúng 315360000 thì hợp lệ.)
8. Mọi dạng sai khác → `ValueError`.
Chỉ đưa ra code trong một khối ```python.

=== ĐỀ TASK C (Kiểm thử QA) ===
Hàm sau đã có trong module `paginate.py` (bạn KHÔNG viết lại hàm, chỉ viết test):
```
def paginate(items: list, page: int, page_size: int) -> dict
- page tính từ 1; page < 1 → ValueError
- page_size phải trong khoảng 1..100 (bao gồm 2 đầu), ngoài khoảng → ValueError
- total = len(items); total_pages = làm tròn LÊN total/page_size (bằng 0 nếu items rỗng)
- items của trang = items[(page-1)*page_size : page*page_size]; page vượt quá total_pages trả về danh sách rỗng (KHÔNG lỗi)
- has_next = page < total_pages
- trả về {"items": [...], "total": int, "total_pages": int, "has_next": bool}
```
Viết file pytest `test_paginate.py` (dòng đầu `from paginate import paginate`) sao cho test PASS với cài đặt đúng và bắt được càng nhiều cài đặt sai càng tốt. Chỉ đưa ra code trong một khối ```python.

=== ĐỀ TASK D (Phân tích nghiệp vụ - PO/BA) ===
Khách hàng yêu cầu: "Làm app đặt lịch khám bệnh online cho phòng khám đa khoa: bệnh nhân chọn bác sĩ, chọn giờ, đặt lịch, nhận xác nhận."
(1) Liệt kê các điểm mơ hồ / yêu cầu bị thiếu quan trọng nhất cần hỏi lại khách hàng (tối đa 12 dòng).
(2) Viết 2 User Story chuẩn INVEST quan trọng nhất, mỗi story có Acceptance Criteria dạng Given/When/Then gồm cả trường hợp lỗi/biên.

=== ĐỀ TASK E (Nghiên cứu hệ thống thực tế & Kiến trúc) ===
Hệ thống bán vé sự kiện chịu tải đột biến (flash sale, kiểu Ticketmaster): liệt kê các vấn đề then chốt khi lên Production và cách các hệ thống thực tế đã giải quyết (tối đa 10 dòng, mỗi dòng: vấn đề → giải pháp cụ thể đã được dùng trong thực tế).

=== ĐỀ TASK F (Tech Lead - quyết định & tuân thủ định dạng) ===
Cho một service Python 3.12 + FastAPI. Chỉ trả về MỘT khối ```json hợp lệ (không chú thích bên trong JSON) đúng schema:
{"language": string, "formatter": string, "linter": string, "type_checker": string, "test_framework": string,
 "commands": {"format_check": string, "lint": string, "typecheck": string, "test": string},
 "banned_libraries": [string, ...], "rationale": string (tối đa 40 từ)}
Các lệnh phải là lệnh CLI thật, chạy được, và format_check KHÔNG được sửa file.

=== ĐỀ TASK G (DevOps) ===
Viết Dockerfile production cho app FastAPI: code ở thư mục hiện tại, phụ thuộc trong requirements.txt, chạy `uvicorn main:app` cổng 8000, có endpoint GET /health. Chỉ đưa ra một khối ```dockerfile.
