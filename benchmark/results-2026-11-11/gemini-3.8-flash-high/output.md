=== TASK A ===
- [Nghiêm trọng] Kiểu dữ liệu `FLOAT` cho số dư ví → Sai số làm tròn của số thực dấu phẩy động gây thất thoát tiền tệ và sai lệch sổ sách → Đổi sang `NUMERIC(18, 2)` hoặc lưu số nguyên theo đơn vị tiền nhỏ nhất (`BIGINT`).
- [Nghiêm trọng] Đánh dấu giao dịch `FAILED` ngay khi gọi cổng thanh toán bị timeout 5s → Cổng thanh toán có thể đã trừ tiền của user thành công nhưng ví không được cộng (lệch trạng thái) → Đổi sang trạng thái `PENDING`, chạy cronjob đối soát hoặc gọi API kiểm tra trạng thái (inquiry) từ cổng thanh toán trước khi kết luận.
- [Nghiêm trọng] Webhook cộng tiền bằng `SELECT` rồi `UPDATE` không khóa và thiếu cơ chế Idempotency → Xảy ra Race condition (Lost Update) và nguy cơ cộng tiền trùng lặp khi cổng gửi webhook retry → Sử dụng `UPDATE wallets SET balance = balance + amount`, khóa bi quan (`SELECT ... FOR UPDATE`), đồng thời lưu bảng `processed_transactions(txn_id)` có ràng buộc `UNIQUE` để đảm bảo tính bất biến (idempotent).
- [Nghiêm trọng] Endpoint webhook `POST /webhook/payment` không có xác thực chữ ký số → Kẻ tấn công có thể giả lập request nạp tiền khống vào bất kỳ ví nào → Bắt buộc kiểm tra chữ ký số (HMAC-SHA256 signature với shared secret) do cổng thanh toán cung cấp và cấu hình IP Whitelist.
- [Nghiêm trọng] Ghi toàn bộ request body vào log (chứa `card_number`, `cvv`) → Vi phạm nghiêm trọng chuẩn bảo mật PCI-DSS, lộ thông tin tài chính nhạy cảm khi log bị rò rỉ → Không bao giờ nhận hoặc lưu CVV/số thẻ trực tiếp tại backend (dùng Hosted Fields/SDK Tokenization của cổng) và cấu hình log masking để ẩn các trường dữ liệu nhạy cảm.
- [Cao] Hardcode secret key `"wallet-secret-2024"` trong mã nguồn và JWT có thời hạn 365 ngày → Dễ lộ khóa giải mã/ký giả token và không thể thu hồi khi token bị đánh cắp → Đưa secret ra biến môi trường/Secret Manager, rút ngắn thời hạn access token (15-60 phút), kết hợp refresh token và cơ chế blacklist thu hồi.
- [Nghiêm trọng] Hệ thống tài chính chạy 1 DB PostgreSQL duy nhất, không replica, không backup → Single Point of Failure (SPOF), khi xảy ra sự cố phần cứng hoặc lỗi ổ đĩa sẽ mất trắng dữ liệu ví của khách hàng mà không thể phục hồi → Thiết lập cụm PostgreSQL HA (Primary-Standby Replication với Auto-failover) và cấu hình sao lưu tự động (Daily Snapshot + Continuous WAL Archiving).
- [Trung bình] API `GET /transactions` trả về toàn bộ lịch sử không phân trang → Gây nghẽn mạng, tràn bộ nhớ RAM (OOM) của server và chậm Database khi lượng giao dịch của người dùng tăng lên → Áp dụng phân trang (Pagination theo Keyset/Cursor hoặc Limit/Offset) và giới hạn số bản ghi tối đa trả về trên mỗi trang.

=== TASK B ===
```python
import re

_DURATION_REGEX = re.compile(
    r"^(?:([0-9]+)d)? *(?:([0-9]+)h)? *(?:([0-9]+)m)? *(?:([0-9]+)s)?$"
)
_MAX_SECONDS = 315360000


def parse_duration(s: str) -> int:
    if not isinstance(s, str):
        raise TypeError("Input must be a string")

    s_clean = s.strip()
    if not s_clean:
        raise ValueError("Duration string cannot be empty")

    match = _DURATION_REGEX.fullmatch(s_clean)
    if not match:
        raise ValueError(f"Invalid duration format: {s!r}")

    d_str, h_str, m_str, s_str = match.groups()
    if d_str is None and h_str is None and m_str is None and s_str is None:
        raise ValueError("No duration components found")

    total = (
        (int(d_str) * 86400 if d_str is not None else 0)
        + (int(h_str) * 3600 if h_str is not None else 0)
        + (int(m_str) * 60 if m_str is not None else 0)
        + (int(s_str) if s_str is not None else 0)
    )

    if total > _MAX_SECONDS:
        raise OverflowError(
            f"Total duration ({total}s) exceeds maximum allowed limit of {_MAX_SECONDS}s"
        )

    return total
```

=== TASK C ===
```python
from paginate import paginate
import pytest


def test_invalid_page():
    with pytest.raises(ValueError):
        paginate([1, 2, 3], page=0, page_size=10)
    with pytest.raises(ValueError):
        paginate([1, 2, 3], page=-1, page_size=10)


@pytest.mark.parametrize("invalid_size", [-1, 0, 101, 1000])
def test_invalid_page_size(invalid_size):
    with pytest.raises(ValueError):
        paginate([1, 2, 3], page=1, page_size=invalid_size)


def test_empty_items():
    result = paginate([], page=1, page_size=10)
    assert result == {
        "items": [],
        "total": 0,
        "total_pages": 0,
        "has_next": False,
    }


def test_empty_items_large_page():
    result = paginate([], page=5, page_size=10)
    assert result == {
        "items": [],
        "total": 0,
        "total_pages": 0,
        "has_next": False,
    }


def test_exact_page_division():
    items = list(range(20))
    res1 = paginate(items, page=1, page_size=5)
    assert res1 == {
        "items": [0, 1, 2, 3, 4],
        "total": 20,
        "total_pages": 4,
        "has_next": True,
    }

    res4 = paginate(items, page=4, page_size=5)
    assert res4 == {
        "items": [15, 16, 17, 18, 19],
        "total": 20,
        "total_pages": 4,
        "has_next": False,
    }


def test_round_up_division_and_partial_page():
    items = list(range(7))
    res1 = paginate(items, page=1, page_size=3)
    assert res1 == {
        "items": [0, 1, 2],
        "total": 7,
        "total_pages": 3,
        "has_next": True,
    }

    res2 = paginate(items, page=2, page_size=3)
    assert res2 == {
        "items": [3, 4, 5],
        "total": 7,
        "total_pages": 3,
        "has_next": True,
    }

    res3 = paginate(items, page=3, page_size=3)
    assert res3 == {
        "items": [6],
        "total": 7,
        "total_pages": 3,
        "has_next": False,
    }


def test_page_exceeding_total_pages_returns_empty_list():
    items = [1, 2, 3]
    result = paginate(items, page=3, page_size=2)
    assert result == {
        "items": [],
        "total": 3,
        "total_pages": 2,
        "has_next": False,
    }

    result_far = paginate(items, page=100, page_size=2)
    assert result_far == {
        "items": [],
        "total": 3,
        "total_pages": 2,
        "has_next": False,
    }


def test_boundary_page_size_one():
    items = ["a", "b"]
    res1 = paginate(items, page=1, page_size=1)
    assert res1 == {
        "items": ["a"],
        "total": 2,
        "total_pages": 2,
        "has_next": True,
    }
    res2 = paginate(items, page=2, page_size=1)
    assert res2 == {
        "items": ["b"],
        "total": 2,
        "total_pages": 2,
        "has_next": False,
    }


def test_boundary_page_size_hundred():
    items = list(range(105))
    res1 = paginate(items, page=1, page_size=100)
    assert len(res1["items"]) == 100
    assert res1["total"] == 105
    assert res1["total_pages"] == 2
    assert res1["has_next"] is True

    res2 = paginate(items, page=2, page_size=100)
    assert res2["items"] == list(range(100, 105))
    assert res2["total"] == 105
    assert res2["total_pages"] == 2
    assert res2["has_next"] is False


def test_does_not_mutate_original_list():
    original = [1, 2, 3, 4, 5]
    backup = original.copy()
    paginate(original, page=1, page_size=2)
    assert original == backup
```

=== TASK D ===
**(1) Các điểm mơ hồ / yêu cầu bị thiếu cần làm rõ:**
- Quy tắc chia ca và thời lượng khám: Mỗi ca khám cố định bao nhiêu phút (15p, 30p) hay tùy theo chuyên khoa, và có thời gian nghỉ đệm giữa các ca không?
- Giới hạn đặt trước: Cho phép bệnh nhân đặt lịch trước tối đa bao nhiêu ngày (VD: 30 ngày) và tối thiểu trước giờ khám bao lâu (VD: trước 2 tiếng)?
- Chính sách quản lý lịch bác sĩ: Bác sĩ có lịch làm việc cố định hay xoay ca theo tuần; quy trình xử lý khi bác sĩ có lịch mổ/nghỉ đột xuất thế nào?
- Thanh toán & Giữ chỗ: Phòng khám thu phí khám trước (online qua thẻ/VNPAY/Momo) hay bệnh nhân đến khám mới thanh toán tại quầy?
- Định danh và hồ sơ người khám: Bệnh nhân có bắt buộc đăng ký tài khoản không; một tài khoản có được đặt lịch hộ cho người thân (vợ/chồng, con) không?
- Kênh và quy cách xác nhận: Xác nhận và nhắc hẹn gửi qua SMS Brandname, Email, Zalo ZNS hay Push notification trên app; có tự động nhắc hẹn trước T-24h không?
- Chính sách hủy và dời lịch: Bệnh nhân được tự hủy/đổi lịch trước bao lâu; có giới hạn số lần hủy trong tháng để chống spam không?
- Xử lý No-show và trễ giờ: Bệnh nhân đến trễ quá bao nhiêu phút thì lịch bị tự động hủy; bệnh nhân không đến khám có bị đưa vào danh sách hạn chế không?
- Tích hợp hệ thống phòng khám (HIS/EMR): Ứng dụng chạy độc lập hay phải đồng bộ lịch hẹn hai chiều theo thời gian thực với hệ thống HIS có sẵn của phòng khám?
- Luồng chọn chuyên khoa: Bệnh nhân tự chọn bác sĩ trực tiếp hay cần có bước sàng lọc triệu chứng bệnh lý ban đầu để gợi ý chuyên khoa phù hợp?

**(2) Hai User Story chuẩn INVEST:**

**User Story 1: Xem và chọn khung giờ khám theo bác sĩ**
- *Mô tả:* Là một bệnh nhân, tôi muốn xem danh sách các khung giờ khám còn trống của một bác sĩ theo ngày đã chọn, để tôi có thể chọn thời gian khám phù hợp nhất với thời gian biểu của mình.
- *Acceptance Criteria:*
  - **Given** bệnh nhân đã chọn Bác sĩ A và chọn một ngày hợp lệ trong tương lai; **When** ngày đó bác sĩ còn ca khám trống; **Then** hệ thống hiển thị danh sách các khung giờ còn khả dụng (dạng nút bấm/màu xanh) kèm thời lượng khám của từng ca.
  - **Given** bệnh nhân chọn một ngày mà tất cả các khung giờ của Bác sĩ A đã có người đặt hoặc bác sĩ nghỉ; **When** hệ thống tải dữ liệu lịch; **Then** hiển thị thông báo "Bác sĩ đã kín lịch vào ngày này", làm mờ các khung giờ và gợi ý ngày khám gần nhất còn trống.
  - **Given** bệnh nhân đang xem lịch nhưng kết nối mạng bị gián đoạn; **When** bệnh nhân chuyển sang chọn ngày khác; **Then** hiển thị thông báo "Không thể tải lịch khám, vui lòng kiểm tra kết nối" và nút "Thử lại".

**User Story 2: Đặt lịch khám và nhận mã xác nhận**
- *Mô tả:* Là một bệnh nhân, tôi muốn nhập thông tin người khám và xác nhận đặt lịch cho khung giờ đã chọn, để lịch hẹn của tôi được hệ thống phòng khám ghi nhận thành công.
- *Acceptance Criteria:*
  - **Given** bệnh nhân đã chọn khung giờ 09:00 - 09:30 ngày 20/10 của Bác sĩ B và điền đầy đủ họ tên, số điện thoại hợp lệ; **When** bệnh nhân bấm nút "Xác nhận đặt lịch"; **Then** hệ thống khóa ca khám, tạo lịch hẹn mới, hiển thị màn hình thành công với Mã đặt lịch (VD: `MED-8921`), đồng thời gửi tin nhắn SMS xác nhận về số điện thoại đã đăng ký.
  - **Given** khung giờ 09:00 chỉ còn 1 chỗ trống và vừa có bệnh nhân khác đặt thành công trước đó 1 giây; **When** bệnh nhân bấm "Xác nhận đặt lịch"; **Then** hệ thống từ chối tạo lịch, hiển thị cảnh báo "Khung giờ này vừa có người đặt, vui lòng chọn giờ khác", và tự động làm mới danh sách khung giờ trống.
  - **Given** bệnh nhân để trống trường Số điện thoại hoặc nhập sai định dạng (chứa ký tự chữ cái hoặc không đủ 10 số); **When** bệnh nhân bấm nút "Xác nhận đặt lịch"; **Then** hệ thống chặn gửi yêu cầu, viền đỏ ô nhập liệu và hiển thị lỗi "Số điện thoại không hợp lệ".

=== TASK E ===
- Quá tải tầng mạng và sập server do lượng request ập vào đồng thời hàng triệu kết nối → Triển khai phòng chờ ảo tại tầng CDN/Edge (Virtual Waiting Room như Cloudflare Waiting Room, Queue-it) để xếp hàng người dùng và điều tiết lượng truy cập theo hạn mức xử lý của backend.
- Tranh chấp giữ chỗ đồng thời (Race condition) khi nhiều người cùng chọn một ghế → Sử dụng Distributed Lock qua Redis với Lua Script nguyên tử kèm thời gian hết hạn (TTL Hold khoảng 5-10 phút) để tạm giữ ghế mà không gây nghẽn Database.
- Tình trạng đầu cơ, vét vé hàng loạt bằng tool/bot tự động → Áp dụng giải pháp nhận diện bot nâng cao (Akamai Bot Manager, Cloudflare Turnstile, phân tích hành vi thiết bị) kết hợp chính sách vé định danh bắt buộc xác minh danh tính (Identity Verification).
- Nghẽn cổ chai I/O Database do hàng triệu lượt đọc sơ đồ ghế cùng lúc → Tách biệt kiến trúc đọc/ghi (CQRS), chuyển toàn bộ dữ liệu trạng thái sơ đồ ghế sang static snapshot in-memory trên Redis Cluster và phân phối qua CDN.
- Ghế ảo bị giữ liên tục rồi bỏ rơi làm cạn kiệt kho vé (Inventory Hoarding) → Sử dụng cơ chế hàng đợi trễ (Delay Queue qua RabbitMQ DLX hoặc Redis Keyspace Expiration) để tự động trả lại trạng thái ghế trống ngay khi hết hạn giữ chỗ mà không cần quét toàn bộ DB.
- Cổng thanh toán bên thứ ba bị quá tải hoặc phản hồi chậm gây treo luồng xử lý → Tách quy trình thanh toán thành luồng bất đồng bộ qua Message Queue (Apache Kafka / AWS SQS) kết hợp mẫu Circuit Breaker để tránh sụp đổ dây chuyền (Cascading Failure).
- Vé bị làm giả, sao chép hoặc chụp màn hình bán lại chợ đen → Sử dụng mã vé điện tử động (Dynamic Rolling Barcode / Rotating QR Code kiểu Ticketmaster SafeTix) thay đổi mã sau mỗi 15 giây và vô hiệu hóa chức năng chụp màn hình trên app.
- Nghẽn hệ thống gửi email/SMS thông báo khi có hàng chục nghìn đơn hàng thành công liên tục → Đưa tác vụ xuất vé PDF và gửi thông báo vào background worker pool để xử lý theo đợt (batch processing), tách biệt hoàn toàn với luồng mua vé chính.

=== TASK F ===
```json
{
  "language": "Python 3.12",
  "formatter": "ruff",
  "linter": "ruff",
  "type_checker": "mypy",
  "test_framework": "pytest",
  "commands": {
    "format_check": "ruff format --check .",
    "lint": "ruff check .",
    "typecheck": "mypy .",
    "test": "pytest"
  },
  "banned_libraries": [
    "requests",
    "black",
    "flake8",
    "isort",
    "pylint"
  ],
  "rationale": "Ruff tối ưu tốc độ format và lint, Mypy kiểm soát chặt kiểu dữ liệu, Pytest chuẩn hóa kiểm thử; cấm thư viện đồng bộ như requests và công cụ cũ để giữ codebase async nhất quán, đạt hiệu năng cao."
}
```

=== TASK G ===
```dockerfile
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production runtime
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

USER appuser

COPY --chown=appuser:appuser . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
