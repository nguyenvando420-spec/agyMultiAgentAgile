=== TASK A ===
- [Nghiêm trọng] Lưu số dư cột `balance` bằng kiểu `FLOAT` → Sai số dấu phẩy động IEEE 754 gây lệch tiền tích lũy, thất thoát tài chính và lệch đối soát → Đổi sang `BIGINT` (lưu đơn vị tiền nhỏ nhất) hoặc `NUMERIC(19, 4)` kèm ràng buộc `CHECK (balance >= 0)`.
- [Nghiêm trọng] Nhận trực tiếp `card_number` và `cvv` tại `POST /topup` → Vi phạm nghiêm trọng chuẩn PCI-DSS, lộ dữ liệu thẻ thật nếu backend bị xâm nhập → Dùng SDK/Hosted Payment Page của cổng thanh toán để tokenize thẻ trực tiếp từ phía client, server chỉ nhận token.
- [Nghiêm trọng] Ghi toàn bộ request body vào log → Lộ plaintext số thẻ, CVV (PCI-DSS cấm tuyệt đối lưu CVV sau cấp phép) và dữ liệu nhạy cảm ra hệ thống log → Bỏ log raw body, chỉ log các trường an toàn theo whitelist hoặc mask/redact dữ liệu nhạy cảm tại middleware.
- [Nghiêm trọng] Webhook `POST /webhook/payment` không xác thực chữ ký và tin tưởng dữ liệu gửi đến → Kẻ tấn công giả mạo gói tin webhook để tự cộng tiền khống không giới hạn → Xác thực chữ ký số/HMAC kèm timestamp chống replay từ cổng thanh toán và đối chiếu `amount`/`user_id` với bản ghi giao dịch gốc trong DB.
- [Nghiêm trọng] Cộng tiền kiểu đọc-tính-ghi (`SELECT balance` rồi `UPDATE`) tách rời không khóa → Race condition (lost update) khi có nhiều giao dịch đồng thời của cùng user làm mất biến động số dư → Thực hiện trong DB transaction với câu lệnh nguyên tử `UPDATE wallets SET balance = balance + $1 WHERE user_id = $2` hoặc `SELECT ... FOR UPDATE`.
- [Nghiêm trọng] Thiếu cơ chế chống xử lý trùng (Idempotency) ở cả `POST /topup` và webhook → Cổng thanh toán retry webhook làm cộng tiền nhiều lần cho 1 `txn_id`, hoặc client bấm đúp bị trừ thẻ 2 lần → Bắt buộc `Idempotency-Key` ở API nạp, đặt `UNIQUE(txn_id)` và chuyển trạng thái nguyên tử `WHERE txn_id = $1 AND status = 'PENDING'` trong cùng transaction cộng ví.
- [Nghiêm trọng] Đánh dấu giao dịch `FAILED` ngay khi gọi cổng thanh toán bị timeout 5s → Cổng thanh toán vẫn có thể đã trừ tiền thành công phía ngân hàng, gây mất tiền của khách hoặc xung đột khi webhook báo thành công tới sau → Chuyển trạng thái sang `PENDING`/`PROCESSING` khi timeout, chờ webhook và chạy job đối soát chủ động (query status API) với cổng thanh toán.
- [Nghiêm trọng] Hardcode JWT secret yếu (`"wallet-secret-2024"`) trong `config.js` và hạn token 365 ngày không có cơ chế thu hồi → Lộ source code hoặc bị dò secret sẽ bị giả mạo token mọi user, lộ token bị chiếm quyền ví suốt 1 năm → Dùng khóa mạnh (>=256-bit hoặc RS256/ES256) nạp từ Secret Manager, giảm TTL access token xuống 5–15 phút kết hợp Refresh Token rotation và danh sách thu hồi trên Redis.
- [Nghiêm trọng] Chạy 1 instance PostgreSQL không replica và không có backup cho dữ liệu tiền tệ → Hỏng ổ cứng, lỗi vận hành hoặc sự cố hạ tầng gây downtime toàn bộ và mất vĩnh viễn số dư của khách hàng → Thiết lập Primary-Standby replication (synchronous commit), bật backup tự động kèm WAL archiving (PITR) sang vùng lưu trữ độc lập và diễn tập khôi phục định kỳ.
- [Cao] Thiếu bảng giao dịch/sổ cái bất biến (ledger) và khuyết ánh xạ `txn_id` → `user_id` ở luồng webhook → Webhook chỉ nhận `{txn_id, status, amount}` nên không xác định được `user_id` an toàn để cộng tiền và không có lịch sử kiểm toán khi khiếu nại → Tạo bảng `transactions` gắn `txn_id` với `user_id` ngay trước khi gọi cổng thanh toán và ghi sổ cái kép (double-entry ledger) chỉ cho phép `INSERT`.
- [Cao] Không kiểm tra miền giá trị `amount` và quyền sở hữu tài nguyên → Truyền `amount <= 0`, `NaN` hoặc vượt trần gây đảo dấu số dư/rửa tiền; truyền `user_id` ngoài luồng xác thực gây lỗi IDOR → Validate chặt `amount` là số nguyên dương nằm trong hạn mức giao dịch/ngày và chỉ lấy `user_id` từ token đã xác thực.
- [Cao] API `GET /transactions` trả toàn bộ lịch sử không phân trang và thiếu Rate Limiting / Circuit Breaker → User nhiều giao dịch hoặc spam request gây tràn RAM (OOM) Node.js, cạn kiệt DB connection pool (nhất là khi cổng thanh toán treo 5s) làm sập hệ thống → Áp dụng cursor-based pagination có index `(user_id, created_at DESC)`, giới hạn kích thước trang, bật Rate Limit và Circuit Breaker cho lời gọi ra cổng thanh toán.
- [Cao] Không có cơ chế vô hiệu hóa/đồng bộ Redis cache khi cập nhật số dư trong DB → Hiển thị số dư cũ (stale cache) hoặc cho phép chi tiêu lố nếu nghiệp vụ đọc số dư từ cache → Không dùng cache để kiểm tra số dư giao dịch (luôn đọc/khóa từ PostgreSQL) và xóa cache ngay sau khi DB transaction commit.

=== TASK B ===
```python
import re

MAX_SECONDS = 315_360_000

_UNIT_SECONDS = {
    "d": 86_400,
    "h": 3_600,
    "m": 60,
    "s": 1,
}

_UNIT_ORDER = {
    "d": 0,
    "h": 1,
    "m": 2,
    "s": 3,
}

_COMPONENT_RE = re.compile(r"([0-9]+)([dhms]) *", re.ASCII)


def parse_duration(s: str) -> int:
    if not isinstance(s, str):
        raise TypeError("Input must be a string")

    stripped = s.strip()
    if not stripped:
        raise ValueError("Duration string must not be empty")

    total = 0
    overflow = False
    last_order = -1
    pos = 0
    length = len(stripped)

    while pos < length:
        match = _COMPONENT_RE.match(stripped, pos)
        if match is None:
            raise ValueError(f"Invalid duration format: {s!r}")

        digits, unit = match.group(1), match.group(2)
        order = _UNIT_ORDER[unit]
        if order <= last_order:
            raise ValueError(f"Duplicate or out-of-order unit {unit!r} in {s!r}")
        last_order = order

        if not overflow:
            significant = digits.lstrip("0")
            if len(significant) > 9:
                overflow = True
            elif significant:
                total += int(significant) * _UNIT_SECONDS[unit]
                if total > MAX_SECONDS:
                    overflow = True

        pos = match.end()

    if overflow:
        raise OverflowError(f"Duration exceeds maximum of {MAX_SECONDS} seconds")

    return total
```

=== TASK C ===
```python
from paginate import paginate
import pytest


EXPECTED_KEYS = {"items", "total", "total_pages", "has_next"}


def _assert_valid_schema(result: dict) -> None:
    assert isinstance(result, dict)
    assert set(result.keys()) == EXPECTED_KEYS
    assert isinstance(result["items"], list)
    assert type(result["total"]) is int
    assert type(result["total_pages"]) is int
    assert type(result["has_next"]) is bool


@pytest.mark.parametrize("invalid_page", [0, -1, -2, -100])
@pytest.mark.parametrize("sample_items", [[], [1, 2, 3]])
def test_invalid_page_raises_value_error(sample_items, invalid_page):
    with pytest.raises(ValueError):
        paginate(sample_items, page=invalid_page, page_size=10)


@pytest.mark.parametrize("invalid_page_size", [0, -1, -50, 101, 102, 1000])
@pytest.mark.parametrize("sample_items", [[], [1, 2, 3]])
def test_invalid_page_size_raises_value_error(sample_items, invalid_page_size):
    with pytest.raises(ValueError):
        paginate(sample_items, page=1, page_size=invalid_page_size)


@pytest.mark.parametrize("page", [1, 2, 10])
def test_empty_items_returns_zero_pages_and_no_error(page):
    res = paginate([], page=page, page_size=5)
    _assert_valid_schema(res)
    assert res == {
        "items": [],
        "total": 0,
        "total_pages": 0,
        "has_next": False,
    }


def test_page_size_lower_bound_one():
    items = ["a", "b", "c"]
    r1 = paginate(items, page=1, page_size=1)
    r2 = paginate(items, page=2, page_size=1)
    r3 = paginate(items, page=3, page_size=1)
    r4 = paginate(items, page=4, page_size=1)

    for r in (r1, r2, r3, r4):
        _assert_valid_schema(r)

    assert r1 == {"items": ["a"], "total": 3, "total_pages": 3, "has_next": True}
    assert r2 == {"items": ["b"], "total": 3, "total_pages": 3, "has_next": True}
    assert r3 == {"items": ["c"], "total": 3, "total_pages": 3, "has_next": False}
    assert r4 == {"items": [], "total": 3, "total_pages": 3, "has_next": False}


def test_page_size_upper_bound_hundred():
    items = list(range(100))
    res_exact = paginate(items, page=1, page_size=100)
    _assert_valid_schema(res_exact)
    assert res_exact == {
        "items": items,
        "total": 100,
        "total_pages": 1,
        "has_next": False,
    }

    items_101 = list(range(101))
    p1 = paginate(items_101, page=1, page_size=100)
    p2 = paginate(items_101, page=2, page_size=100)
    assert p1["total"] == 101
    assert p1["total_pages"] == 2
    assert p1["has_next"] is True
    assert len(p1["items"]) == 100
    assert p2 == {
        "items": [100],
        "total": 101,
        "total_pages": 2,
        "has_next": False,
    }


def test_exact_multiple_total_and_has_next_on_last_page():
    items = [10, 20, 30, 40, 50, 60]
    p1 = paginate(items, page=1, page_size=3)
    p2 = paginate(items, page=2, page_size=3)
    p3 = paginate(items, page=3, page_size=3)

    _assert_valid_schema(p1)
    _assert_valid_schema(p2)
    _assert_valid_schema(p3)

    assert p1 == {"items": [10, 20, 30], "total": 6, "total_pages": 2, "has_next": True}
    assert p2 == {"items": [40, 50, 60], "total": 6, "total_pages": 2, "has_next": False}
    assert p3 == {"items": [], "total": 6, "total_pages": 2, "has_next": False}


@pytest.mark.parametrize(
    "total,page_size,expected_pages",
    [
        (1, 10, 1),
        (5, 4, 2),   # 1.25 -> must ceil to 2, not round/floor to 1
        (5, 2, 3),   # 2.5 -> must ceil to 3, not banker's round to 2
        (7, 5, 2),   # 1.4 -> must ceil to 2
        (10, 3, 4),
        (99, 100, 1),
        (200, 100, 2),
    ],
)
def test_ceiling_division_for_total_pages(total, page_size, expected_pages):
    items = list(range(total))
    res = paginate(items, page=1, page_size=page_size)
    _assert_valid_schema(res)
    assert res["total"] == total
    assert res["total_pages"] == expected_pages
    assert res["has_next"] is (expected_pages > 1)


def test_full_walkthrough_reconstructs_original_list():
    items = list(range(1, 12))  # 11 items, page_size=4 -> 3 pages (4, 4, 3)
    collected = []
    for p in range(1, 4):
        res = paginate(items, page=p, page_size=4)
        _assert_valid_schema(res)
        assert res["total"] == 11
        assert res["total_pages"] == 3
        assert res["has_next"] is (p < 3)
        collected.extend(res["items"])

    assert collected == items
    assert len(paginate(items, page=3, page_size=4)["items"]) == 3


def test_page_far_beyond_total_pages_returns_empty_without_error():
    items = [1, 2, 3, 4, 5]
    res = paginate(items, page=999, page_size=2)
    _assert_valid_schema(res)
    assert res == {
        "items": [],
        "total": 5,
        "total_pages": 3,
        "has_next": False,
    }


def test_preserves_order_duplicates_and_falsy_elements():
    items = [None, False, 0, "", 0, {"id": 1}, []]
    p1 = paginate(items, page=1, page_size=4)
    p2 = paginate(items, page=2, page_size=4)

    assert p1["items"] == [None, False, 0, ""]
    assert p2["items"] == [0, {"id": 1}, []]
    assert p1["total"] == 7
    assert p2["total"] == 7


def test_does_not_mutate_or_alias_input_list():
    original = [1, 2, 3]
    snapshot = list(original)
    res = paginate(original, page=1, page_size=10)
    assert original == snapshot

    res["items"].append(999)
    assert original == snapshot
```

=== TASK D ===
- **(1) Các điểm mơ hồ / yêu cầu bị thiếu cần hỏi lại khách hàng:**
- Phạm vi nền tảng & phân hệ: Làm Mobile App (iOS/Android), Web hay Zalo Mini App; có bao gồm cổng cho lễ tân/bác sĩ quản lý lịch hay tích hợp phần mềm quản lý phòng khám (HIS) sẵn có không?
- Tài khoản & đặt hộ: Bệnh nhân đăng nhập bằng SĐT (OTP) hay đặt nhanh không cần tài khoản; một tài khoản có được tạo nhiều hồ sơ để đặt lịch hộ người thân (trẻ em, người lớn tuổi) và khai báo BHYT không?
- Cách chọn bác sĩ/chuyên khoa: Nếu bệnh nhân chưa biết chọn bác sĩ nào, hệ thống có cho phép đặt theo chuyên khoa/triệu chứng để phòng khám tự phân bổ bác sĩ phù hợp không?
- Quy tắc khung giờ (Slot): Thời lượng mỗi slot là bao nhiêu phút, mỗi slot nhận tối đa 1 hay nhiều bệnh nhân, và giới hạn đặt trước tối thiểu/tối đa bao lâu (ví dụ trước 2 giờ, tối đa 30 ngày)?
- Thanh toán & phí khám: Đặt lịch miễn phí trả tiền tại quầy hay bắt buộc thanh toán trước/đặt cọc online (VietQR, thẻ, ví điện tử), và chính sách hoàn tiền khi hủy lịch ra sao?
- Quy trình xác nhận & kênh thông báo: Lịch hẹn được xác nhận tự động ngay khi đặt hay cần lễ tân duyệt thủ công; gửi thông báo xác nhận/nhắc lịch qua kênh nào (Zalo ZNS, SMS, Email, Push Notification)?
- Chính sách đổi/hủy & vắng mặt (No-show): Bệnh nhân được tự đổi/hủy lịch trước giờ khám bao lâu, và có khóa tính năng đặt online nếu bỏ hẹn liên tiếp nhiều lần không?
- Xử lý sự cố từ phía bác sĩ: Khi bác sĩ nghỉ đột xuất, hội chẩn khẩn hoặc trễ ca, quy trình dời lịch/chuyển bác sĩ thay thế và thông báo cho bệnh nhân thực hiện thế nào?
- Tiếp đón thực tế tại phòng khám: Bệnh nhân đến nơi check-in bằng mã QR hay đọc SĐT tại quầy, và thứ tự ưu tiên giữa khách đặt online với khách vãng lai (walk-in) được xử lý ra sao?
- Yêu cầu phi chức năng & pháp lý: Lượng đặt lịch dự kiến/ngày là bao nhiêu và quy định lưu trữ/bảo vệ dữ liệu sức khỏe cá nhân (theo Nghị định 13/2023/NĐ-CP) cần đáp ứng ở mức nào?

- **(2) Hai User Story chuẩn INVEST quan trọng nhất:**
- **User Story 1 — Tra cứu bác sĩ và khung giờ khám còn trống**
  - **Mô tả:** Là một **bệnh nhân**, tôi muốn **lọc bác sĩ theo chuyên khoa và xem các khung giờ còn trống theo ngày**, để **chọn được bác sĩ và thời gian khám phù hợp với nhu cầu cá nhân**.
  - **AC1 (Luồng chính - Còn chỗ trống):** **Given** bệnh nhân chọn một chuyên khoa, một bác sĩ đang làm việc và một ngày hợp lệ trong khoảng cho phép đặt trước (từ hôm nay đến +30 ngày), **When** màn hình chọn giờ tải xong, **Then** hệ thống hiển thị danh sách khung giờ làm việc của bác sĩ đó, chỉ cho phép chọn các khung giờ còn suất trống và cách thời điểm hiện tại tối thiểu 60 phút.
  - **AC2 (Biên - Bác sĩ kín lịch hoặc nghỉ phép):** **Given** bác sĩ đã kín toàn bộ suất khám hoặc có lịch nghỉ trong ngày được chọn, **When** bệnh nhân chọn ngày đó, **Then** các khung giờ đã đầy được hiển thị trạng thái "Hết chỗ" (vô hiệu hóa nút chọn) và hệ thống thông báo gợi ý ngày làm việc gần nhất còn chỗ trống.
  - **AC3 (Lỗi/Biên - Chọn ngày ngoài phạm vi cho phép):** **Given** bệnh nhân cố chọn ngày trong quá khứ hoặc vượt quá giới hạn 30 ngày đặt trước, **When** thao tác chọn ngày diễn ra, **Then** hệ thống chặn thao tác và hiển thị thông báo rõ giới hạn khoảng ngày được phép đặt lịch.
- **User Story 2 — Đặt lịch khám và nhận xác nhận lịch hẹn**
  - **Mô tả:** Là một **bệnh nhân đã chọn bác sĩ và khung giờ trống**, tôi muốn **xác nhận thông tin đặt lịch và nhận mã hẹn ngay sau khi đặt**, để **chắc chắn giữ được suất khám và dùng mã này khi đến phòng khám**.
  - **AC1 (Luồng chính - Đặt lịch thành công):** **Given** bệnh nhân đã đăng nhập/xác thực SĐT, chọn một khung giờ đang còn chỗ và điền hợp lệ thông tin hồ sơ khám, **When** bệnh nhân nhấn "Xác nhận đặt lịch", **Then** hệ thống ghi nhận lịch hẹn với mã đặt lịch duy nhất, giảm số chỗ trống của khung giờ đó đi 1, hiển thị màn hình xác nhận chi tiết (bác sĩ, chuyên khoa, ngày giờ, địa điểm, mã QR) và gửi thông báo xác nhận qua Zalo ZNS/SMS trong vòng 30 giây.
  - **AC2 (Lỗi tranh chấp đồng thời - Hết chỗ ở giây cuối):** **Given** khung giờ chỉ còn 1 suất trống cuối cùng và một bệnh nhân khác vừa hoàn tất đặt suất đó trước vài mili-giây, **When** bệnh nhân nhấn "Xác nhận đặt lịch", **Then** hệ thống từ chối tạo lịch vượt quá sức chứa, thông báo "Khung giờ bạn chọn vừa hết chỗ, vui lòng chọn khung giờ khác" và tự động làm mới danh sách khung giờ trống.
  - **AC3 (Biên - Bệnh nhân đặt trùng khung giờ với chính mình):** **Given** hồ sơ bệnh nhân đã có một lịch hẹn đang ở trạng thái "Đã xác nhận" trùng ngày và giao thoa khung giờ, **When** bệnh nhân nhấn "Xác nhận đặt lịch" cho ca khám mới, **Then** hệ thống chặn tạo lịch mới và cảnh báo bệnh nhân đang có lịch hẹn trùng giờ kèm liên kết xem lịch đã đặt.
  - **AC4 (Lỗi hệ thống bên ngoài - Cổng SMS/ZNS gián đoạn):** **Given** suất khám hợp lệ và lịch hẹn đã được lưu thành công trong cơ sở dữ liệu nhưng dịch vụ gửi ZNS/SMS tạm thời lỗi/timeout, **When** quá trình đặt lịch hoàn tất, **Then** bệnh nhân vẫn thấy mã xác nhận và chi tiết lịch hẹn ngay trên ứng dụng, đồng thời hệ thống đưa tin nhắn vào hàng đợi retry tự động để gửi bù mà không làm thất bại giao dịch đặt lịch.

=== TASK E ===
- Bão lưu lượng đột biến (Thundering Herd) tại đúng giây mở bán làm sập API và DB → Chặn ngay từ biên bằng phòng chờ ảo (Ticketmaster Smart Queue / Queue-it / Cloudflare Waiting Room), cấp token thứ tự có chữ ký và điều tiết lượng user vào trang chọn vé theo tốc độ cố định (admission control).
- Bán trùng hoặc lố số lượng ghế (Overselling / Double-booking) dưới hàng vạn request đồng thời → Thực thi cấp phát nguyên tử trong bộ nhớ bằng Redis Lua script, DynamoDB conditional write trên từng `seat_id` hoặc kiến trúc Single-Writer phân vùng theo sự kiện kèm ràng buộc `UNIQUE(event_id, seat_id)` ở tầng lưu trữ bền vững.
- Đầu cơ giữ chỗ ảo trên giỏ hàng làm "đóng băng" kho vé mà không thanh toán (Inventory Hoarding) → Áp dụng cơ chế giữ ghế tạm thời có thời hạn (Seat Reservation Lease / TTL 5–10 phút như Ticketmaster) kèm đồng hồ đếm ngược, tự động thu hồi trả ghế về kho trống ngay khi hết hạn.
- Bot tự động (Scalper Bots) cào sơ đồ ghế và mua sạch vé trong vài mili-giây → Kết hợp đăng ký xét duyệt định danh trước giờ mở bán (mô hình Ticketmaster Verified Fan / lottery), giới hạn số vé trên mỗi tài khoản/thẻ thanh toán và chặn bot theo hành vi ở tầng WAF/Edge (Akamai Bot Manager, DataDome).
- Nghẽn khóa trên một dòng đếm duy nhất (Hot-row Lock Contention) với loại vé đứng/không số ghế (General Admission) → Chia nhỏ quỹ vé thành nhiều phân vùng bộ đếm độc lập (Sharded Counters / Slot Buckets trên Redis hoặc DB) hoặc tuần tự hóa qua các partition của Kafka thay vì `UPDATE` khóa một bản ghi duy nhất.
- Lưu lượng xem sơ đồ ghế (Seat Map) lớn gấp hàng trăm lần lưu lượng đặt vé làm nghẽn cơ sở dữ liệu giao dịch → Tách luồng đọc-ghi (CQRS): cache sơ đồ tĩnh trên CDN, phục vụ trạng thái ghế từ bản sao in-memory/edge cache TTL ngắn (1–3 giây) hoặc đẩy delta qua WebSocket/SSE, chỉ kiểm tra nguyên tử tại nguồn chính khi bấm giữ ghế.
- Cổng thanh toán bên thứ ba phản hồi chậm hoặc timeout lúc cao điểm gây treo kết nối và lệch trạng thái đơn → Tách bước giữ ghế khỏi bước thu tiền theo Saga pattern + Transactional Outbox, gia hạn lease ngắn khi đã chuyển sang cổng thanh toán, bắt buộc `Idempotency-Key` và đối soát qua webhook/worker.
- Một sự kiện "cháy vé" hút cạn tài nguyên làm sập lây toàn bộ các sự kiện khác và gây bão retry (Retry Storm) → Cô lập tài nguyên theo từng sự kiện nóng bằng Bulkhead/Cell-based architecture, chủ động cắt tải sớm (Load Shedding 429/503), bật Circuit Breaker và bắt buộc Exponential Backoff có Jitter ở phía client.
- Vé chợ đen giả mạo qua ảnh chụp màn hình và nghẽn mạng tại cổng soát vé sân vận động khi hàng vạn người vào cùng lúc → Dùng mã vé động đổi mới mỗi 15–30 giây dựa trên khóa mật mã TOTP (như Ticketmaster SafeTix) và đồng bộ trước khóa xác thực xuống máy quét tại cổng để xác thực offline tức thời.

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
    "typecheck": "mypy --strict .",
    "test": "pytest"
  },
  "banned_libraries": [
    "requests",
    "urllib3",
    "pytz",
    "nose"
  ],
  "rationale": "Ruff thống nhất format và lint cực nhanh, mypy --strict đảm bảo an toàn kiểu tĩnh, pytest chuẩn hóa kiểm thử async; cấm requests/urllib3 vì chặn event loop FastAPI và cấm pytz vì Python 3.12 đã có zoneinfo."
}
```

=== TASK G ===
```dockerfile
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN groupadd --system --gid 10001 appgroup && \
    useradd --system --uid 10001 --gid appgroup --no-create-home --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
```
