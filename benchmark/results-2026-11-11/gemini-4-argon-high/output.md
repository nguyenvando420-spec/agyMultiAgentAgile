=== TASK A ===
- [CRITICAL] Kiểu dữ liệu `balance FLOAT` cho tiền tệ → Sai số biểu diễn dấu phẩy động (IEEE 754) làm lệch số dư ví của người dùng và sai lệch đối soát kế toán → Đổi sang kiểu `NUMERIC(19, 4)`/`DECIMAL` hoặc lưu số nguyên `BIGINT` ở đơn vị tiền tệ nhỏ nhất.
- [CRITICAL] Race condition (Lost Update) khi cộng tiền do thực hiện `SELECT` rồi `UPDATE` rời rạc không có khóa hay giao dịch → Nhiều webhook hoặc giao dịch chạy đồng thời ghi đè số dư của nhau làm mất tiền khách nạp → Cập nhật nguyên tử bằng `UPDATE wallets SET balance = balance + $1, updated_at = NOW() WHERE user_id = $2` trong DB transaction hoặc khóa dòng bằng `SELECT ... FOR UPDATE`.
- [CRITICAL] Webhook `/webhook/payment` thiếu cơ chế Idempotency và không kiểm tra trạng thái giao dịch → Cổng thanh toán gửi lại (retry) webhook hoặc gửi trạng thái thất bại (`status != 'SUCCESS'`) vẫn bị cộng tiền lặp nhiều lần → Ràng buộc `UNIQUE(txn_id)` trong bảng giao dịch, chỉ cộng tiền khi `status = 'SUCCESS'` và chuyển trạng thái nguyên tử (`WHERE status = 'PENDING'`) trong cùng một DB transaction.
- [CRITICAL] Webhook không xác thực chữ ký (Signature/HMAC) và tin tưởng trực tiếp `amount` từ request body → Kẻ tấn công giả mạo request gọi thẳng vào webhook để tự cộng tiền khống vào ví → Xác thực chữ ký HMAC từ cổng thanh toán, giới hạn IP nguồn và chỉ lấy `amount`, `user_id` từ bản ghi giao dịch gốc trong DB nội bộ dựa theo `txn_id`.
- [CRITICAL] Đánh dấu giao dịch `FAILED` ngay khi gọi cổng thanh toán bị timeout 5s → Giao dịch thực tế vẫn có thể đã trừ tiền thành công ở phía ngân hàng/cổng thanh toán, gây mất tiền của khách hoặc mâu thuẫn dữ liệu khi webhook gọi về sau → Khi timeout phải giữ trạng thái `PENDING`, gửi kèm `idempotency_key` khi gọi cổng thanh toán và dùng webhook hoặc job đối soát (reconciliation) để chốt trạng thái cuối.
- [CRITICAL] Nhận trực tiếp `card_number`, `cvv` tại API `/topup` và ghi toàn bộ request body vào log → Vi phạm chuẩn PCI-DSS, lộ thông tin thẻ và CVV dạng rõ (plaintext) trong hệ thống log dẫn tới rủi ro bị đánh cắp thẻ hàng loạt → Không xử lý dữ liệu thẻ thô trên backend (chuyển sang dùng Tokenization/SDK/Hosted Page của cổng thanh toán) và bắt buộc che (redact/mask) mọi trường nhạy cảm trước khi ghi log.
- [CRITICAL] Không kiểm tra tính hợp lệ của `amount` và thiếu Idempotency ở `POST /topup` → Người dùng truyền `amount <= 0`, `NaN` để trục lợi hoặc bấm nạp nhiều lần (double-submit) gây trừ tiền thẻ trùng lặp → Validate chặt `amount` là số nguyên/thập phân dương trong hạn mức cho phép và bắt buộc client gửi `Idempotency-Key` cho mỗi lần nạp.
- [CRITICAL] Không có bảng lịch sử biến động số dư (Ledger) và không có Backup ở môi trường Production → Khi xảy ra lỗi phần cứng, bug hoặc tấn công sẽ mất trắng dữ liệu tài chính mà không thể khôi phục hay kiểm toán (audit) → Thiết kế sổ cái kế toán kép (append-only ledger) lưu mọi biến động và bật backup tự động hàng ngày kèm WAL archiving (Point-in-Time Recovery).
- [HIGH] JWT dùng secret yếu (`"wallet-secret-2024"`), hardcode trong `config.js`, thời hạn 365 ngày và không có cơ chế thu hồi → Dễ bị lộ qua mã nguồn hoặc dò đoán để giả mạo token của mọi user, và khi lộ token kẻ gian có quyền truy cập suốt 1 năm → Đưa secret mạnh (tối thiểu 256-bit ngẫu nhiên hoặc khóa bất đối xứng RS256/EdDSA) vào Secret Manager/biến môi trường, rút ngắn TTL Access Token xuống 5-15 phút kết hợp Refresh Token có quản lý thu hồi.
- [HIGH] Single Point of Failure do chỉ có 1 instance PostgreSQL không replica → Khi DB gặp sự cố hoặc bảo trì, toàn bộ dịch vụ nạp tiền và nhận webhook bị gián đoạn → Thiết lập PostgreSQL Primary-Standby (Streaming Replication) có auto-failover và đưa webhook vào hàng đợi bền vững (Message Queue) trước khi xử lý.
- [HIGH] Nguy cơ bất nhất dữ liệu giữa Redis cache và PostgreSQL → Đọc số dư từ cache bị cũ (stale data) hoặc không xóa cache sau khi cập nhật DB gây hiển thị sai và lệch logic nghiệp vụ → Mọi thao tác tính toán số dư phải đọc/ghi trực tiếp trên PostgreSQL trong transaction, chỉ dùng Redis cho rate-limit/idempotency hoặc xóa cache ngay sau khi transaction commit.
- [MEDIUM] API `GET /transactions` trả về toàn bộ lịch sử không phân trang → Tài khoản có nhiều giao dịch sẽ gây quá tải bộ nhớ (OOM) cho Node.js và làm nghẽn DB → Bắt buộc phân trang (Cursor-based hoặc Limit/Offset có giới hạn tối đa) và đánh index `(user_id, created_at DESC)`.
- [MEDIUM] Thiếu Rate Limiting trên `/topup` và API xác thực → Kẻ gian lợi dụng API để thử thẻ tín dụng hàng loạt (Carding attack) hoặc làm cạn kiệt kết nối hệ thống → Áp dụng Rate Limiting theo `user_id`/IP trên Redis và khóa tạm thời khi phát hiện tần suất giao dịch lỗi bất thường.

=== TASK B ===
```python
import re

_UNIT_ORDER = {"d": 0, "h": 1, "m": 2, "s": 3}
_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_MAX_SECONDS = 315_360_000
_FULL_PATTERN = re.compile(r"\A[0-9]+[dhms](?: *[0-9]+[dhms])*\Z", re.ASCII)
_PART_PATTERN = re.compile(r"([0-9]+)([dhms])", re.ASCII)


def parse_duration(s: str) -> int:
    if not isinstance(s, str):
        raise TypeError("Duration must be a string")

    trimmed = s.strip()
    if not trimmed:
        raise ValueError("Duration string cannot be empty")

    if not _FULL_PATTERN.match(trimmed):
        raise ValueError(f"Invalid duration format: {s!r}")

    last_order = -1
    total_seconds = 0

    for match in _PART_PATTERN.finditer(trimmed):
        num_str, unit = match.groups()
        order = _UNIT_ORDER[unit]
        if order <= last_order:
            raise ValueError(f"Invalid unit order or duplicate unit: {unit!r}")
        last_order = order
        total_seconds += int(num_str) * _UNIT_SECONDS[unit]

    if total_seconds > _MAX_SECONDS:
        raise OverflowError(f"Total duration exceeds {_MAX_SECONDS} seconds")

    return total_seconds
```

=== TASK C ===
```python
from paginate import paginate
import pytest


def test_paginate_first_page():
    items = [1, 2, 3, 4, 5]
    result = paginate(items, page=1, page_size=2)
    assert result == {
        "items": [1, 2],
        "total": 5,
        "total_pages": 3,
        "has_next": True,
    }
    assert isinstance(result["has_next"], bool)


def test_paginate_middle_page():
    items = [10, 20, 30, 40, 50]
    result = paginate(items, page=2, page_size=2)
    assert result == {
        "items": [30, 40],
        "total": 5,
        "total_pages": 3,
        "has_next": True,
    }


def test_paginate_last_page_partial():
    items = [1, 2, 3, 4, 5]
    result = paginate(items, page=3, page_size=2)
    assert result == {
        "items": [5],
        "total": 5,
        "total_pages": 3,
        "has_next": False,
    }


def test_paginate_last_page_exact_division():
    items = [1, 2, 3, 4]
    result = paginate(items, page=2, page_size=2)
    assert result == {
        "items": [3, 4],
        "total": 4,
        "total_pages": 2,
        "has_next": False,
    }


def test_paginate_ceiling_rounding_small_remainder():
    items = list(range(11))
    result = paginate(items, page=1, page_size=5)
    assert result["total"] == 11
    assert result["total_pages"] == 3
    assert result["has_next"] is True
    assert result["items"] == [0, 1, 2, 3, 4]


def test_paginate_empty_items():
    result = paginate([], page=1, page_size=10)
    assert result == {
        "items": [],
        "total": 0,
        "total_pages": 0,
        "has_next": False,
    }


def test_paginate_empty_items_high_page():
    result = paginate([], page=5, page_size=10)
    assert result == {
        "items": [],
        "total": 0,
        "total_pages": 0,
        "has_next": False,
    }


def test_paginate_page_beyond_total_pages():
    items = ["a", "b", "c"]
    result = paginate(items, page=2, page_size=5)
    assert result == {
        "items": [],
        "total": 3,
        "total_pages": 1,
        "has_next": False,
    }
    result_far = paginate(items, page=999, page_size=2)
    assert result_far == {
        "items": [],
        "total": 3,
        "total_pages": 2,
        "has_next": False,
    }


def test_paginate_page_size_boundaries_valid():
    items = list(range(105))
    res_min = paginate(items, page=1, page_size=1)
    assert res_min == {
        "items": [0],
        "total": 105,
        "total_pages": 105,
        "has_next": True,
    }

    res_max = paginate(items, page=1, page_size=100)
    assert res_max == {
        "items": list(range(100)),
        "total": 105,
        "total_pages": 2,
        "has_next": True,
    }

    res_max_page2 = paginate(items, page=2, page_size=100)
    assert res_max_page2 == {
        "items": [100, 101, 102, 103, 104],
        "total": 105,
        "total_pages": 2,
        "has_next": False,
    }


@pytest.mark.parametrize("invalid_page", [0, -1, -100])
def test_paginate_invalid_page_raises_value_error(invalid_page):
    with pytest.raises(ValueError):
        paginate([1, 2, 3], page=invalid_page, page_size=10)
    with pytest.raises(ValueError):
        paginate([], page=invalid_page, page_size=10)


@pytest.mark.parametrize("invalid_page_size", [0, -1, -50, 101, 102, 1000])
def test_paginate_invalid_page_size_raises_value_error(invalid_page_size):
    with pytest.raises(ValueError):
        paginate([1, 2, 3], page=1, page_size=invalid_page_size)
    with pytest.raises(ValueError):
        paginate([], page=1, page_size=invalid_page_size)


def test_paginate_does_not_mutate_input():
    original = [1, 2, 3, 4, 5]
    copy = list(original)
    result = paginate(original, page=1, page_size=2)
    assert original == copy
    result["items"].append(999)
    assert original == copy
```

=== TASK D ===
- **(1) Các điểm mơ hồ / yêu cầu bị thiếu cần hỏi lại khách hàng:**
- Luồng đặt khám bắt buộc chọn Chuyên khoa trước rồi mới chọn Bác sĩ, hay cho phép đặt theo triệu chứng/khung giờ trống mà không cần chỉ định bác sĩ?
- Thời lượng mỗi ca khám (slot) là cố định (ví dụ 15-30 phút) hay cấu hình riêng theo từng chuyên khoa/bác sĩ, và một khung giờ nhận tối đa một hay nhiều bệnh nhân?
- Bệnh nhân có bắt buộc đăng ký/đăng nhập (xác thực OTP, CCCD, thẻ BHYT) mới được đặt lịch không, và một tài khoản có được đặt lịch hộ người thân không?
- Lịch hẹn được hệ thống xác nhận tự động ngay khi đặt hay phải chờ lễ tân phê duyệt, và gửi xác nhận qua kênh nào (SMS, Zalo ZNS, Email, Push Notification)?
- Có yêu cầu thanh toán trước phí khám hoặc đặt cọc online để giữ lịch không, và quy định hoàn tiền khi hủy lịch như thế nào?
- Quy định thời gian tối thiểu được phép hủy/đổi lịch trước giờ khám là bao lâu, và xử lý thế nào với bệnh nhân đặt trùng giờ hoặc vắng mặt (no-show) nhiều lần?
- Khi nhiều bệnh nhân cùng chọn một slot cuối cùng, hệ thống giữ chỗ tạm thời (hold slot) trong bao lâu hay xác nhận cho người bấm hoàn tất trước?
- Bác sĩ nghỉ đột xuất hoặc thay đổi lịch trực thì quy trình thông báo và chuyển lịch/đổi bác sĩ cho bệnh nhân đã đặt diễn ra như thế nào?
- Hệ thống có cần tích hợp đồng bộ lịch hai chiều với phần mềm quản lý phòng khám (HIS/EMR) hiện có để tránh trùng lịch với khách đến trực tiếp (walk-in) không?
- Phạm vi sản phẩm cần làm gồm những nền tảng nào (Mobile App, Web, Zalo Mini App) và có bao gồm cổng quản trị cho Lễ tân/Bác sĩ không?

- **(2) Hai User Story chuẩn INVEST quan trọng nhất:**
- **User Story 1: Đặt lịch khám theo bác sĩ và khung giờ trống**
  - **Mô tả:** Là một **bệnh nhân**, tôi muốn **xem các khung giờ còn trống của bác sĩ và đặt lịch khám**, để **chủ động thời gian đi khám mà không phải xếp hàng chờ đợi tại phòng khám**.
  - **Acceptance Criteria:**
    - *Trường hợp hợp lệ (Happy Path):* **Given** bệnh nhân đã đăng nhập, chọn một bác sĩ và chọn ngày khám hợp lệ (từ ngày hiện tại trở đi), **When** bệnh nhân chọn một khung giờ đang ở trạng thái "Còn trống", điền triệu chứng tóm tắt và bấm "Xác nhận đặt lịch", **Then** hệ thống chuyển trạng thái khung giờ đó sang "Đã đặt", tạo mã lịch hẹn duy nhất, hiển thị màn hình xác nhận và gửi thông báo xác nhận (SMS/Zalo/App) trong vòng 30 giây.
    - *Trường hợp biên - Xung đột đặt chỗ (Concurrency):* **Given** hai bệnh nhân cùng đang xem một khung giờ trống cuối cùng của bác sĩ, **When** bệnh nhân A bấm "Xác nhận đặt lịch" thành công trước bệnh nhân B tích tắc, **Then** yêu cầu của bệnh nhân B bị từ chối với thông báo "Khung giờ này vừa có người đặt, vui lòng chọn khung giờ khác" và làm mới lại danh sách giờ trống mà không tạo lịch trùng.
    - *Trường hợp lỗi - Đặt trùng lịch của cùng bệnh nhân:* **Given** bệnh nhân đã có một lịch hẹn đang hiệu lực vào khung giờ 09:00 - 09:30 ngày 20/11, **When** bệnh nhân tiếp tục đặt thêm một lịch hẹn khác trùng vào khung giờ 09:00 - 09:30 ngày 20/11, **Then** hệ thống chặn thao tác và báo lỗi "Bạn đã có lịch hẹn khác trong cùng khung giờ này".
    - *Trường hợp biên - Khung giờ đã qua hoặc sát giờ:* **Given** thời gian hiện tại là 08:50, **When** bệnh nhân chọn khung giờ 08:30 cùng ngày hoặc khung giờ cách hiện tại ít hơn thời gian cho phép tối thiểu (ví dụ < 30 phút), **Then** các khung giờ đó bị vô hiệu hóa (disable) hoặc hệ thống từ chối đặt kèm thông báo yêu cầu chọn khung giờ muộn hơn.
- **User Story 2: Hủy hoặc đổi lịch khám đã đặt**
  - **Mô tả:** Là một **bệnh nhân đã có lịch hẹn**, tôi muốn **đổi sang khung giờ khác hoặc hủy lịch hẹn trực tiếp trên ứng dụng**, để **phòng khám nắm được thông tin, giải phóng khung giờ cho bệnh nhân khác và sắp xếp lại lịch phù hợp khi tôi bận đột xuất**.
  - **Acceptance Criteria:**
    - *Trường hợp hợp lệ - Hủy lịch đúng hạn:* **Given** bệnh nhân có lịch hẹn ở trạng thái "Đã xác nhận" và thời điểm hiện tại còn cách giờ khám trên 4 tiếng (theo quy định phòng khám), **When** bệnh nhân chọn "Hủy lịch", chọn lý do hủy và xác nhận, **Then** lịch hẹn chuyển sang trạng thái "Đã hủy", khung giờ của bác sĩ được mở lại thành "Còn trống" ngay lập tức và hệ thống gửi thông báo xác nhận hủy thành công.
    - *Trường hợp hợp lệ - Đổi lịch khám:* **Given** bệnh nhân có lịch hẹn hợp lệ cách giờ khám trên 4 tiếng, **When** bệnh nhân chọn "Đổi lịch", chọn khung giờ mới còn trống và xác nhận, **Then** hệ thống giữ khung giờ mới, giải phóng khung giờ cũ về trạng thái "Còn trống" trong cùng một giao dịch nguyên tử và gửi thông báo cập nhật mã lịch hẹn.
    - *Trường hợp biên/lỗi - Hủy hoặc đổi quá sát giờ khám:* **Given** lịch hẹn chỉ còn cách thời điểm hiện tại dưới 4 tiếng, **When** bệnh nhân bấm "Hủy lịch" hoặc "Đổi lịch" trên app, **Then** hệ thống từ chối thao tác và hiển thị thông báo "Không thể hủy/đổi lịch trực tuyến khi còn dưới 4 tiếng trước giờ khám, vui lòng liên hệ tổng đài hỗ trợ".
    - *Trường hợp lỗi - Thao tác trên lịch đã hoàn tất hoặc đã hủy:* **Given** lịch hẹn đang ở trạng thái "Đã khám" hoặc "Đã hủy", **When** bệnh nhân mở chi tiết lịch hẹn hoặc gửi yêu cầu hủy/đổi lại, **Then** các nút "Hủy lịch"/"Đổi lịch" không hiển thị và API trả về lỗi từ chối thay đổi trạng thái.

=== TASK E ===
- **Lượng truy cập đột biến (Thundering Herd) làm sập hệ thống ngay giờ mở bán** → Dùng phòng chờ ảo (Virtual Waiting Room như Queue-it hoặc tầng Edge CloudFront + Lambda@Edge/DynamoDB tại Ticketmaster) để xếp hàng, cấp token định danh và chỉ xả người dùng vào luồng mua vé theo đúng tốc độ xử lý của backend (Admission Control).
- **Bán vượt số lượng ghế (Overselling) và Race Condition khi hàng vạn người bấm chọn cùng một ghế** → Giữ chỗ nguyên tử (Atomic Seat Hold) trên Redis Cluster bằng Lua script hoặc khóa theo đúng `seat_id` kèm TTL ngắn (5–10 phút), kết hợp kiểm tra điều kiện nguyên tử (`WHERE status = 'AVAILABLE'`) khi ghi nhận.
- **Nghẽn cổ chai Database do tranh chấp khóa (Lock Contention / Hot Spotting) trên cùng một sự kiện** → Phân mảnh dữ liệu (Sharding/Partitioning) theo từng sự kiện và khu vực khán đài (Section), xử lý trạng thái ghế trên bộ nhớ (In-Memory Grid) và đẩy sự kiện qua Apache Kafka để ghi xuống DB bất đồng bộ theo mô hình CQRS / Event Sourcing.
- **Bot tự động đầu cơ gom sạch vé (Scalper Bots) và tấn công cào dữ liệu** → Triển khai chương trình định danh người mua trước giờ mở bán (như Ticketmaster Verified Fan cấp mã truy cập riêng), kết hợp WAF/Bot Management ở CDN, Device Fingerprinting, giới hạn số vé mỗi tài khoản/thẻ thanh toán.
- **Cổng thanh toán phản hồi chậm hoặc lỗi mạng làm treo giao dịch và giam ghế** → Tách rời bước giữ ghế (Reservation) và thanh toán (Checkout) bất đồng bộ qua Message Queue kèm Idempotency Key; dùng tiến trình nền (Expiration/Reconciliation Worker) tự động thu hồi ghế về kho khi hết hạn TTL mà chưa thanh toán.
- **Quá tải truy vấn đọc sơ đồ ghế (Seat Map) liên tục được làm mới bởi hàng triệu người dùng** → Hiển thị khả năng còn vé theo phân khu (Zone/Section) trước khi chọn ghế chi tiết, cache trạng thái sơ đồ ghế tại CDN/Edge với TTL rất ngắn (1–2 giây, Stale-While-Revalidate) và đẩy thay đổi qua WebSocket/SSE.
- **Người dùng bị văng khỏi hàng đợi hoặc mất ghế đang giữ khi rớt mạng/F5 trình duyệt** → Cấp Queue Token có chữ ký số và lưu trạng thái phiên giữ ghế (Session/Cart State) tập trung trên Redis gắn với `user_id`, cho phép người dùng tải lại trang vẫn giữ nguyên vị trí hàng đợi và ghế đang giữ trong thời hạn TTL.
- **Auto-scaling phản ứng quá chậm so với tốc độ tăng tải dựng đứng trong vài giây đầu** → Thực hiện Pre-warming hạ tầng (chủ động nhân bản Pod Kubernetes, mở sẵn DB Connection Pool và nâng công suất Load Balancer trước giờ mở bán) kết hợp Circuit Breaker và Graceful Degradation (tắt các tính năng phụ như gợi ý, lịch sử).

=== TASK F ===
```json
{
  "language": "python",
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
    "urllib3",
    "black",
    "flake8",
    "isort"
  ],
  "rationale": "Ruff hợp nhất formatter và linter với tốc độ cực nhanh; mypy đảm bảo an toàn kiểu tĩnh cho FastAPI; pytest chuẩn hóa kiểm thử; cấm thư viện HTTP đồng bộ như requests để tránh chặn async event loop."
}
```

=== TASK G ===
```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
