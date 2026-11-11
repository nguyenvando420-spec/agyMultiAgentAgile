=== TASK A ===
- **[Critical]** Dùng kiểu `FLOAT` cho số dư ví → lỗi làm tròn, mất tiền → chuyển sang `NUMERIC(precision, scale)` hoặc `BIGINT` lưu số tiền tính bằng cents.  
- **[Critical]** Không dùng transaction khi cập nhật số dư → race condition, tiền dư sai khi đồng thời nạp → bao quanh SELECT + UPDATE bằng `BEGIN … COMMIT` hoặc `UPDATE … SET balance = balance + amount RETURNING`.  
- **[High]** Không xác thực webhook (thiếu chữ ký/nonce) → bị giả mạo giao dịch → kiểm tra chữ ký HMAC hoặc token bảo mật từ cổng thanh toán.  
- **[High]** Ghi toàn bộ request body (card_number, cvv) vào log → rò rỉ dữ liệu thẻ → loại bỏ hoặc mask dữ liệu nhạy cảm trước khi log.  
- **[High]** JWT secret hard‑coded trong `config.js` → dễ bị lộ, token giả mạo → đưa secret vào biến môi trường và rotate định kỳ.  
- **[High]** Token JWT hết hạn 365 ngày → tăng rủi ro chiếm đoạt tài khoản → giảm thời gian TTL (ví dụ 1‑7 ngày) và hỗ trợ refresh token.  
- **[High]** Không replica cho PostgreSQL → mất khả năng chịu lỗi, downtime → triển khai replica read‑write hoặc failover cluster.  
- **[Medium]** Không có backup dữ liệu → mất dữ liệu khi lỗi ổc → lên lịch backup thường ngày và lưu ở vị trí off‑site.  
- **[Medium]** Không throttle/limit API `/topup` → tấn công DDOS, lạm dụng cổng thanh toán → thêm rate‑limiting và captcha nếu cần.  
- **[Medium]** Không kiểm tra `amount` (âm, quá lớn) → giao dịch không hợp lệ → validate amount > 0 và giới hạn tối đa.  
- **[Medium]** Không có kiểm tra quyền truy cập (authorization) khi GET `/transactions` → rò rỉ giao dịch của người dùng khác → xác thực `user_id` dựa trên JWT.  
- **[Medium]** Timeout 5s cho cổng thanh toán → có thể gây false‑negative khi trả về chậm → tăng timeout hoặc implement retry + async polling.  

=== TASK B ===
```python
def parse_duration(s):
    if not isinstance(s, str):
        raise TypeError("Duration must be a string")
    s = s.strip()
    if not s:
        raise ValueError("Empty duration string")

    # Mapping unit to seconds and order
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    order = ["d", "h", "m", "s"]
    seen = set()
    last_index = -1
    total_seconds = 0

    # Split by spaces (allow multiple)
    parts = [p for p in s.split(" ") if p]

    for part in parts:
        # Find the position where digits end
        i = 0
        while i < len(part) and part[i].isdigit():
            i += 1
        if i == 0 or i == len(part):
            raise ValueError(f"Invalid component: {part}")
        num_str, unit = part[:i], part[i:]
        if unit not in units:
            raise ValueError(f"Unsupported unit: {unit}")
        if unit in seen:
            raise ValueError(f"Duplicate unit: {unit}")
        # Enforce decreasing order
        cur_index = order.index(unit)
        if cur_index <= last_index:
            raise ValueError("Units out of order")
        last_index = cur_index
        seen.add(unit)

        total_seconds += int(num_str) * units[unit]

    if total_seconds > 315_360_000:
        raise OverflowError("Duration exceeds maximum allowed")
    return total_seconds
```

=== TASK C ===
```python
from paginate import paginate
import pytest

@pytest.mark.parametrize(
    "items, page, page_size, expected",
    [
        # normal case
        (list(range(10)), 1, 5, {"items": [0, 1, 2, 3, 4], "total": 10, "total_pages": 2, "has_next": True}),
        (list(range(10)), 2, 5, {"items": [5, 6, 7, 8, 9], "total": 10, "total_pages": 2, "has_next": False}),
        # empty list
        ([], 1, 10, {"items": [], "total": 0, "total_pages": 0, "has_next": False}),
        # page beyond total_pages returns empty items
        (list(range(3)), 5, 2, {"items": [], "total": 3, "total_pages": 2, "has_next": False}),
    ],
)
def test_paginate_success(items, page, page_size, expected):
    assert paginate(items, page, page_size) == expected


@pytest.mark.parametrize(
    "items, page, page_size, exc_type",
    [
        (list(range(5)), 0, 10, ValueError),   # page < 1
        (list(range(5)), -1, 10, ValueError),  # negative page
        (list(range(5)), 1, 0, ValueError),    # page_size < 1
        (list(range(5)), 1, 101, ValueError),  # page_size > 100
        ("not a list", 1, 10, TypeError),      # items not list (if implementation checks)
    ],
)
def test_paginate_invalid_params(items, page, page_size, exc_type):
    with pytest.raises(exc_type):
        paginate(items, page, page_size)
```

=== TASK D ===
**1. Các điểm mơ hồ / yêu cầu thiếu (tối đa 12 dòng)**  
- Định dạng và thời gian hiển thị cho lịch bác sĩ (giờ 9‑5, 15‑phút, ngày làm việc).  
- Quy tắc đặt lịch trùng (cùng thời gian cùng bác sĩ).  
- Xác thực bệnh nhân (đăng ký, đăng nhập, xác thực 2FA?).  
- Quy trình hủy / thay đổi lịch, phí hủy.  
- Thông báo xác nhận (email, SMS, push).  
- Hệ thống quản lý lịch cho bác sĩ (độ ưu tiên, nghỉ).  
- Hạn mức số lượt đặt/ngày cho mỗi bệnh nhân.  
- Xử lý lịch khám ngoại tuyến (đặt qua điện thoại).  
- Quyền truy cập dữ liệu (bảo mật thông tin y tế).  
- Tích hợp thanh toán (có trả phí không?).  
- Định danh bác sĩ (ID, chuyên khoa) và cách lựa chọn.  
- Báo cáo lịch sử khám cho bệnh nhân và bác sĩ.

**2. User Story 1 (INVEST)**  
- *Title*: Người bệnh đặt lịch khám với bác sĩ.  
- *As a* bệnh nhân đã đăng nhập,  
- *I want* chọn bác sĩ, ngày giờ khả dụng và nhận xác nhận,  
- *So that* tôi có thời gian khám được bảo đảm.  
- **Acceptance Criteria**  
  - **Given** bệnh nhân đã đăng nhập và đang ở trang đặt lịch,  
  - **When** họ chọn bác sĩ, ngày và khung giờ hợp lệ, và bấm “Đặt lịch”,  
  - **Then** hệ thống tạo một cuộc hẹn, không cho trùng thời gian cùng bác sĩ, và gửi xác nhận qua email/SMS.  
  - **And** nếu thời gian đã bị đặt trước, **Then** hiển thị lỗi “Khung giờ không khả dụng”.  

**User Story 2 (INVEST)**  
- *Title*: Người bệnh hủy hoặc thay đổi lịch khám.  
- *As a* bệnh nhân,  
- *I want* hủy hoặc đổi thời gian lịch đã đặt,  
- *So that* tôi có thể điều chỉnh khi có thay đổi kế hoạch.  
- **Acceptance Criteria**  
  - **Given** bệnh nhân có một lịch khám chưa đến,  
  - **When** họ nhấn “Hủy” và xác nhận,  
  - **Then** hệ thống đánh dấu hẹn là đã hủy, giải phóng khung giờ và gửi thông báo hủy.  
  - **When** họ chọn “Đổi thời gian”, chọn giờ mới hợp lệ và lưu,  
  - **Then** hệ thống cập nhật lịch, kiểm tra trùng và gửi thông báo cập nhật.  
  - **If** thời gian mới không khả dụng, **Then** trả về lỗi “Khung giờ không khả dụng”.  

=== TASK E ===
- **Quá tải đồng thời (spike)** → dùng **Queue (Kafka/RabbitMQ) + async workers** để xếp hàng và xử lý dần.  
- **Đồng thời ghi DB** → triển khai **sharding + read‑replica** và **caching Redis** để giảm tải.  
- **Giới hạn request** → **rate limiting (nginx/Envoy) + CDN** để ngăn lũt traffic.  
- **Đặt hàng trùng lặp** → **idempotent request token** và **optimistic lock** trên DB.  
- **Giải pháp fallback khi dịch vụ thanh toán lỗi** → **circuit breaker (Hystrix/Resilience4j)** và **retry queue**.  
- **Phân phối tải** → **load balancer (HAProxy, ALB)** với **autoscaling** EC2/EKS.  
- **Cache dữ liệu tĩnh (event info)** → **CDN (CloudFront) + edge caching**.  
- **Giữ trạng thái session** → **stateless API + JWT**; nếu cần state, dùng **Redis session store**.  
- **Giám sát & alert** → **Prometheus + Grafana** + **distributed tracing (Jaeger)**.  
- **Deploy zero‑downtime** → **Blue/Green deployment** hoặc **Canary release** trên Kubernetes.

=== TASK F ===
```json
{
  "language": "Python 3.12",
  "formatter": "black",
  "linter": "ruff",
  "type_checker": "mypy",
  "test_framework": "pytest",
  "commands": {
    "format_check": "black --check .",
    "lint": "ruff check .",
    "typecheck": "mypy .",
    "test": "pytest"
  },
  "banned_libraries": ["pylint", "flake8", "autopep8"],
  "rationale": "Ensures consistent style, catches errors early, and avoids duplicated linting tools."
}
```

=== TASK G ===
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (if any) and then Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
