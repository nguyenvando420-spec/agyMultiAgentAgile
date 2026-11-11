# Thang chấm cho các bài tự luận (chốt TRƯỚC khi đọc bài, chấm mù)

Mỗi mục: 1 = nêu đúng vấn đề + cách sửa hợp lý; 0.5 = có nhắc nhưng mơ hồ/sửa sai; 0 = không có.

## Task A — Phản biện thiết kế ví điện tử (11 điểm)
A1 balance FLOAT → tiền sai số (dùng BIGINT đơn vị nhỏ nhất / NUMERIC)
A2 Server nhận card_number + CVV → vi phạm PCI-DSS (tokenize phía client / hosted page)
A3 Log toàn bộ request body → lộ PAN/CVV/PII
A4 Webhook không xác thực chữ ký → giả mạo cộng tiền
A5 Đọc-tính-ghi không khóa → lost update (UPDATE balance = balance + x / FOR UPDATE / transaction)
A6 Webhook không idempotent → cổng retry cộng tiền nhiều lần (UNIQUE txn_id, state machine)
A7 Timeout → FAILED là sai: trạng thái không xác định, tiền có thể đã trừ (PENDING + truy vấn trạng thái/đối soát)
A8 JWT secret hardcode trong code + hạn 365 ngày, không thu hồi
A9 GET /transactions không phân trang
A10 1 PostgreSQL không replica + không backup → SPOF / mất dữ liệu tiền
A11 Webhook không đối chiếu amount/txn với giao dịch gốc (payload không có user_id, phải tra theo txn_id; amount có thể bị sửa)

## Task D — Phân tích nghiệp vụ đặt lịch khám (14 điểm)
D1 Trùng lịch / tranh chấp slot đồng thời
D2 Chính sách hủy / đổi lịch (thời hạn)
D3 No-show, đặt cọc / thanh toán / hoàn tiền
D4 Quản lý lịch bác sĩ: độ dài slot, bác sĩ nghỉ đột xuất → xử lý lịch đã đặt
D5 Kênh thông báo & nhắc lịch (SMS/Zalo/email)
D6 Danh tính: tài khoản/OTP, đặt hộ người thân/trẻ em, khách vãng lai
D7 Bảo mật dữ liệu y tế / đồng ý / pháp lý (VD Nghị định 13/2023)
D8 Tích hợp HIS/hệ thống phòng khám hiện có, BHYT/bảo hiểm
D9 Chọn theo chuyên khoa/triệu chứng vs chọn bác sĩ; phối hợp khách walk-in
D10 Giờ làm/ngày lễ, cửa sổ đặt trước bao xa, giới hạn số lịch/người (chống spam)
D11 Nền tảng (web/app) & cổng quản trị cho lễ tân/admin, báo cáo
D12 Xác nhận tức thì hay chờ phòng khám duyệt
D13 User Story 1 có AC Given/When/Then gồm ≥1 trường hợp lỗi/biên đúng nghĩa
D14 User Story 2 như trên

## Task E — Nghiên cứu hệ thống bán vé flash sale (11 điểm)
E1 Phòng chờ ảo / hàng đợi (Queue-it, Ticketmaster Smart Queue)
E2 Giữ chỗ tạm có TTL và tự nhả
E3 Chống bán vượt: trừ tồn kho nguyên tử (Redis Lua/DECR, conditional UPDATE, lock)
E4 Chống bot/phe vé (Verified Fan, CAPTCHA, rate limit, fingerprint)
E5 Thanh toán idempotent / tách bất đồng bộ, state machine đơn hàng
E6 CDN / cache trang sự kiện, giảm tải đọc
E7 Backpressure / load shedding / graceful degradation / pre-scale
E8 Hot partition: chia nhỏ theo khu ghế / sharding sơ đồ ghế
E9 Load test & capacity planning trước giờ mở bán
E10 Giám sát, kill switch, đối soát thanh toán & giữ chỗ
E11 (thưởng) Dẫn chứng hệ thống thực tế có tên + cơ chế cụ thể, chính xác

## Trừ điểm
- Thông tin sai sự thật / bịa (hallucination) rõ ràng: −0.5 mỗi lỗi, ghi chú lại.
