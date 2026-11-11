=== TASK A ===
- [Nghiêm trọng] `balance FLOAT` → sai số làm tròn, lệch tiền theo thời gian → dùng `NUMERIC(19,4)` hoặc số nguyên đơn vị nhỏ nhất (đồng), thêm `CHECK (balance >= 0)`.
- [Nghiêm trọng] Webhook đọc rồi ghi (SELECT rồi UPDATE) không có lock → hai webhook hoặc hai request đồng thời bị lost update, mất hoặc sai tiền → dùng một câu lệnh nguyên tử `UPDATE ... SET balance = balance + $1` trong transaction, hoặc `SELECT ... FOR UPDATE`.
- [Nghiêm trọng] Webhook không idempotent (không kiểm tra `txn_id` đã xử lý) → cổng retry thì cộng tiền nhiều lần → ràng buộc `UNIQUE(txn_id)`, bảng giao dịch có state machine (PENDING → SUCCESS/FAILED), cộng tiền cùng transaction với việc đổi trạng thái.
- [Nghiêm trọng] Webhook không xác thực nguồn và tin `amount` từ payload → kẻ tấn công giả webhook để nạp tiền khống → verify chữ ký HMAC của cổng, kiểm tra timestamp chống replay, allowlist IP, và lấy số tiền từ giao dịch đã lưu ở server, không lấy từ payload.
- [Nghiêm trọng] Webhook không kiểm tra `status` → giao dịch thất bại vẫn bị cộng tiền → chỉ cộng khi `status = SUCCESS` và `txn_id` tồn tại, số tiền khớp, trạng thái hiện tại là PENDING.
- [Nghiêm trọng] Timeout 5s thì đánh dấu FAILED → cổng có thể đã trừ tiền thật, user bị mất tiền hoặc nạp lại gây trừ hai lần → để trạng thái PENDING/UNKNOWN, gọi API truy vấn trạng thái của cổng, chạy job đối soát (reconciliation) định kỳ, gửi kèm idempotency key khi gọi cổng.
- [Nghiêm trọng] Client gửi `card_number` và `cvv` qua API của mình → vi phạm PCI DSS, rủi ro rò rỉ thẻ → dùng hosted fields/redirect/tokenization của cổng, server không bao giờ nhận hay lưu PAN/CVV.
- [Nghiêm trọng] Log toàn bộ request body → số thẻ, CVV, token nằm trong log dạng rõ → không log trường nhạy cảm, mask/redact theo allowlist, giới hạn quyền truy cập và thời gian lưu log.
- [Nghiêm trọng] JWT secret hardcode trong `config.js`, yếu và nằm trong source → ai xem được repo cũng giả mạo được token → lấy secret từ secret manager/env, dùng khóa ngẫu nhiên ≥256 bit, có cơ chế rotate (hoặc dùng RS256/ES256), đổi secret đã lộ ngay.
- [Cao] JWT hết hạn 365 ngày, không có revoke → token bị lộ thì dùng được cả năm → access token 5–15 phút kèm refresh token xoay vòng, lưu danh sách revoke/session phía server.
- [Cao] Không có Idempotency-Key và rate limit cho `/topup` → bấm đúp hay retry gây tạo nhiều giao dịch, bị dò thẻ (card testing) → bắt buộc header `Idempotency-Key`, rate limit theo user/IP, phát hiện bất thường.
- [Cao] Không validate `amount` (âm, 0, quá lớn, sai kiểu) → nạp số âm hoặc tràn → kiểm tra min/max, kiểu số, đơn vị tiền tệ ở server.
- [Cao] Chỉ có `wallets.balance`, không có ledger/bảng giao dịch bất biến → không audit hay đối soát được, không tìm ra nguyên nhân khi lệch tiền → bảng `transactions`/ledger append-only (ghi bút toán, số dư trước và sau), balance chỉ là giá trị dẫn xuất hoặc cache.
- [Cao] `GET /transactions` trả toàn bộ lịch sử, không phân trang → user nhiều giao dịch làm quá tải DB/memory, response chậm → phân trang cursor/keyset, giới hạn `limit`, đánh index `(user_id, created_at)`.
- [Cao] Không thấy kiểm tra quyền sở hữu ở `/transactions` và `/topup` → có nguy cơ IDOR (xem hoặc nạp vào ví người khác) → luôn lấy `user_id` từ JWT đã verify, không nhận từ client.
- [Nghiêm trọng] Không backup, chỉ 1 instance PostgreSQL không replica → hỏng đĩa hay xóa nhầm là mất toàn bộ dữ liệu tiền, và DB là SPOF → bật PITR (WAL archiving), backup tự động ra nơi khác, replica/failover, diễn tập restore định kỳ. "MVP chưa cần" không áp dụng cho hệ thống tiền.
- [Trung bình] Redis cache (nếu cache số dư) → số dư cũ hiển thị sai, quyết định dựa trên dữ liệu stale → không cache số dư, hoặc invalidate trong cùng luồng ghi và lấy DB làm nguồn sự thật.
- [Trung bình] Thiếu giám sát, cảnh báo, audit trail, ép TLS, xử lý webhook đồng bộ chậm (cổng timeout rồi retry) → sự cố không ai biết, webhook bị gửi lại → metrics và alert (lỗi webhook, giao dịch PENDING quá lâu, lệch đối soát), ép HTTPS/HSTS, webhook trả 200 nhanh rồi xử lý qua queue.

=== TASK B ===
```python
import re

_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_ORDER = "dhms"
_COMPONENT = re.compile(r"([0-9]+)([dhms])")
_LIMIT = 315360000


def parse_duration(s) -> int:
    if not isinstance(s, str):
        raise TypeError("s must be a str")

    text = s.strip()
    if not text:
        raise ValueError("empty duration")

    pos = 0
    length = len(text)
    last_index = -1
    total = 0

    while pos < length:
        match = _COMPONENT.match(text, pos)
        if match is None:
            raise ValueError("invalid duration format")

        digits, unit = match.group(1), match.group(2)
        index = _ORDER.index(unit)
        if index <= last_index:
            raise ValueError("units must be in strictly descending order")
        last_index = index

        stripped = digits.lstrip("0")
        if len(stripped) > 15:
            # Quá lớn chắc chắn vượt giới hạn; tránh int() trên chuỗi khổng lồ.
            # Vẫn tiếp tục duyệt để ưu tiên ValueError nếu phần sau sai định dạng.
            total += _LIMIT + 1
        elif stripped:
            total += int(stripped) * _UNIT_SECONDS[unit]

        pos = match.end()
        while pos < length and text[pos] == " ":
            pos += 1

    if total > _LIMIT:
        raise OverflowError("duration exceeds 315360000 seconds")
    return total
```

=== TASK C ===
```python
from paginate import paginate

import math
import pytest


def reference(items, page, page_size):
    total = len(items)
    total_pages = math.ceil(total / page_size) if total else 0
    return {
        "items": items[(page - 1) * page_size: page * page_size],
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
    }


# ---------- validation ----------

@pytest.mark.parametrize("page", [0, -1, -100])
def test_page_less_than_one_raises(page):
    with pytest.raises(ValueError):
        paginate([1, 2, 3], page, 10)


@pytest.mark.parametrize("page_size", [0, -1, 101, 1000])
def test_page_size_out_of_range_raises(page_size):
    with pytest.raises(ValueError):
        paginate([1, 2, 3], 1, page_size)


@pytest.mark.parametrize("page_size", [1, 2, 50, 99, 100])
def test_page_size_valid_bounds_do_not_raise(page_size):
    result = paginate(list(range(10)), 1, page_size)
    assert result["total"] == 10


def test_validation_applies_even_with_empty_items():
    with pytest.raises(ValueError):
        paginate([], 0, 10)
    with pytest.raises(ValueError):
        paginate([], 1, 0)
    with pytest.raises(ValueError):
        paginate([], 1, 101)


def test_validation_applies_when_page_beyond_range():
    with pytest.raises(ValueError):
        paginate([1], 5, 101)
    with pytest.raises(ValueError):
        paginate([1], 0, 100)


# ---------- basic behaviour ----------

def test_empty_items():
    r = paginate([], 1, 10)
    assert r == {"items": [], "total": 0, "total_pages": 0, "has_next": False}


def test_empty_items_page_beyond():
    r = paginate([], 5, 10)
    assert r == {"items": [], "total": 0, "total_pages": 0, "has_next": False}


def test_result_keys_exact():
    r = paginate([1, 2, 3], 1, 2)
    assert set(r.keys()) == {"items", "total", "total_pages", "has_next"}


def test_result_types():
    r = paginate([1, 2, 3], 1, 2)
    assert isinstance(r["items"], list)
    assert type(r["total"]) is int
    assert type(r["total_pages"]) is int
    assert type(r["has_next"]) is bool


def test_exact_multiple_first_page():
    r = paginate(list(range(20)), 1, 10)
    assert r["items"] == list(range(10))
    assert r["total"] == 20
    assert r["total_pages"] == 2
    assert r["has_next"] is True


def test_exact_multiple_last_page():
    r = paginate(list(range(20)), 2, 10)
    assert r["items"] == list(range(10, 20))
    assert r["total_pages"] == 2
    assert r["has_next"] is False


def test_partial_last_page():
    r = paginate(list(range(25)), 3, 10)
    assert r["items"] == [20, 21, 22, 23, 24]
    assert r["total_pages"] == 3
    assert r["has_next"] is False


def test_partial_middle_page():
    r = paginate(list(range(25)), 2, 10)
    assert r["items"] == list(range(10, 20))
    assert r["has_next"] is True


def test_one_more_than_multiple_ceil():
    r = paginate(list(range(21)), 1, 10)
    assert r["total_pages"] == 3
    assert r["has_next"] is True
    r = paginate(list(range(21)), 3, 10)
    assert r["items"] == [20]
    assert r["has_next"] is False


def test_one_less_than_multiple_ceil():
    r = paginate(list(range(19)), 2, 10)
    assert r["total_pages"] == 2
    assert r["items"] == list(range(10, 19))
    assert r["has_next"] is False


def test_single_item():
    r = paginate(["a"], 1, 1)
    assert r == {"items": ["a"], "total": 1, "total_pages": 1, "has_next": False}


def test_page_size_larger_than_items():
    r = paginate([1, 2, 3], 1, 100)
    assert r == {"items": [1, 2, 3], "total": 3, "total_pages": 1, "has_next": False}


def test_page_size_one_pagination():
    items = ["a", "b", "c"]
    r1 = paginate(items, 1, 1)
    r2 = paginate(items, 2, 1)
    r3 = paginate(items, 3, 1)
    assert r1["items"] == ["a"] and r1["has_next"] is True
    assert r2["items"] == ["b"] and r2["has_next"] is True
    assert r3["items"] == ["c"] and r3["has_next"] is False
    assert r1["total_pages"] == r2["total_pages"] == r3["total_pages"] == 3


def test_page_size_100_boundary():
    items = list(range(250))
    r = paginate(items, 1, 100)
    assert r["items"] == list(range(100))
    assert r["total_pages"] == 3
    assert r["has_next"] is True
    r = paginate(items, 3, 100)
    assert r["items"] == list(range(200, 250))
    assert r["has_next"] is False


def test_exactly_100_items_page_size_100():
    r = paginate(list(range(100)), 1, 100)
    assert r["total_pages"] == 1
    assert r["has_next"] is False
    assert len(r["items"]) == 100


def test_101_items_page_size_100():
    r = paginate(list(range(101)), 2, 100)
    assert r["items"] == [100]
    assert r["total_pages"] == 2
    assert r["has_next"] is False


# ---------- page beyond range ----------

def test_page_just_beyond_total_pages():
    r = paginate(list(range(20)), 3, 10)
    assert r["items"] == []
    assert r["total"] == 20
    assert r["total_pages"] == 2
    assert r["has_next"] is False


def test_page_far_beyond_total_pages():
    r = paginate(list(range(5)), 10**6, 10)
    assert r["items"] == []
    assert r["total"] == 5
    assert r["total_pages"] == 1
    assert r["has_next"] is False


# ---------- items handling ----------

def test_does_not_mutate_input():
    items = list(range(15))
    copy = list(items)
    paginate(items, 2, 10)
    assert items == copy


def test_preserves_order_and_duplicates():
    items = [3, 1, 3, 2, 1, 1, 3]
    r = paginate(items, 2, 3)
    assert r["items"] == [2, 1, 1]
    r = paginate(items, 1, 3)
    assert r["items"] == [3, 1, 3]


def test_items_of_various_types():
    items = [None, "x", 1, (1, 2), {"a": 1}]
    r = paginate(items, 1, 5)
    assert r["items"] == items
    assert r["total"] == 5


def test_pages_cover_all_items_without_overlap():
    items = list(range(47))
    collected = []
    page = 1
    while True:
        r = paginate(items, page, 10)
        collected.extend(r["items"])
        if not r["has_next"]:
            break
        page += 1
    assert collected == items
    assert page == 5


def test_returned_items_not_aliasing_mutation_safe():
    items = [1, 2, 3, 4]
    r = paginate(items, 1, 2)
    r["items"].append(99)
    assert items == [1, 2, 3, 4]


# ---------- exhaustive comparison against reference ----------

@pytest.mark.parametrize("n", list(range(0, 31)) + [99, 100, 101, 199, 200, 201, 250])
@pytest.mark.parametrize("page_size", [1, 2, 3, 7, 10, 50, 99, 100])
def test_matches_reference(n, page_size):
    items = list(range(n))
    total_pages = math.ceil(n / page_size) if n else 0
    for page in range(1, total_pages + 3):
        assert paginate(items, page, page_size) == reference(items, page, page_size)


@pytest.mark.parametrize("n", [0, 1, 9, 10, 11, 100])
def test_has_next_flag_consistency(n):
    items = list(range(n))
    for page_size in (1, 3, 10, 100):
        total_pages = math.ceil(n / page_size) if n else 0
        for page in range(1, total_pages + 3):
            r = paginate(items, page, page_size)
            assert r["has_next"] is (page < total_pages)
            assert r["total_pages"] == total_pages
            assert r["total"] == n
```

=== TASK D ===
**(1) Điểm mơ hồ/thiếu cần hỏi lại**
- Đối tượng người dùng và vai trò: ngoài bệnh nhân còn có lễ tân, bác sĩ, admin không? Ai quản lý lịch làm việc của bác sĩ?
- Bệnh nhân có phải đăng ký tài khoản không (OTP SĐT/email, khách vãng lai)? Có đặt hộ người thân không? Hồ sơ bệnh nhân lưu những gì?
- Lịch bác sĩ: ca làm việc, độ dài một slot (cố định hay theo chuyên khoa/loại khám), nghỉ phép, đổi lịch đột xuất, khám nhiều phòng/cơ sở?
- Chọn bác sĩ theo tiêu chí nào (chuyên khoa, triệu chứng, tên)? Có cho "không chọn bác sĩ, hệ thống tự gán" không?
- Chống đặt trùng: giữ slot tạm trong bao lâu khi đang đặt? Một bệnh nhân được đặt tối đa bao nhiêu lịch, có chống đặt chồng giờ không?
- Hủy/đổi lịch: hạn chót, ai được hủy, bác sĩ hủy thì xử lý thế nào, có phạt no-show/blacklist không?
- "Xác nhận" là gì: tự động ngay hay cần lễ tân duyệt? Kênh nào (SMS, email, Zalo, push)? Có nhắc lịch trước giờ khám không?
- Thanh toán: có đặt cọc/thanh toán online, hoàn tiền, xuất hóa đơn không? Hay chỉ thanh toán tại quầy?
- Tích hợp hệ thống hiện có: phần mềm quản lý phòng khám/HIS, hồ sơ bệnh án, BHYT — có cần đồng bộ hai chiều không?
- Tuân thủ và bảo mật: dữ liệu sức khỏe là dữ liệu nhạy cảm (Nghị định 13/2023 về bảo vệ dữ liệu cá nhân), lưu ở đâu, ai được xem, thời gian lưu?
- Nền tảng và phi chức năng: mobile app native, web hay cả hai; ngôn ngữ; số người dùng đồng thời, giờ cao điểm; SLA; ngân sách, deadline?
- Tiêu chí thành công và phạm vi MVP: các tính năng nào ngoài phạm vi (khám từ xa/video, kê đơn, kết quả xét nghiệm), KPI đo (giảm no-show, giảm tải tổng đài)?

**(2) User Story (INVEST)**

**Story 1 – Đặt lịch khám với bác sĩ**
- Là bệnh nhân, tôi muốn chọn bác sĩ và một khung giờ còn trống để đặt lịch khám, để tôi không phải gọi điện hay đến phòng khám xếp hàng.
- Độc lập: chỉ cần danh sách bác sĩ và lịch trống. Có thể đàm phán: thứ tự chọn (bác sĩ trước hay giờ trước), cách giữ slot. Ước lượng được: khoảng 5–8 điểm. Kiểm thử được: theo AC dưới đây.
- AC1 (thành công): Given bác sĩ A có slot 09:00 ngày mai còn trống, When bệnh nhân đã xác thực chọn slot đó và gửi thông tin hợp lệ, Then hệ thống tạo lịch trạng thái "Đã xác nhận", slot chuyển sang "Đã đặt", và hiển thị mã lịch hẹn.
- AC2 (tranh chấp): Given hai bệnh nhân cùng chọn slot cuối của bác sĩ A, When cả hai gửi đặt lịch gần như đồng thời, Then chỉ một người thành công; người còn lại nhận thông báo "Khung giờ vừa được đặt" kèm gợi ý các slot gần nhất, và không có lịch trùng nào được tạo.
- AC3 (giữ slot tạm): Given bệnh nhân đang ở bước xác nhận, When quá 5 phút không hoàn tất, Then slot được nhả lại và bệnh nhân được báo phiên đã hết hạn.
- AC4 (biên thời gian): Given slot nằm trong quá khứ hoặc ít hơn 2 giờ nữa (quy định tối thiểu, cần khách hàng xác nhận), When bệnh nhân cố đặt, Then hệ thống từ chối với thông báo rõ lý do.
- AC5 (chống chồng giờ): Given bệnh nhân đã có lịch lúc 09:00 ngày mai, When họ đặt thêm lịch khác cùng khung giờ với bác sĩ khác, Then hệ thống cảnh báo và chặn đặt.
- AC6 (lỗi dữ liệu/hệ thống): Given thiếu họ tên hoặc số điện thoại sai định dạng, When gửi, Then hiện lỗi theo từng trường và không tạo lịch. Given lỗi hệ thống khi lưu, Then slot không bị khóa và bệnh nhân được báo thử lại.

**Story 2 – Nhận xác nhận lịch khám**
- Là bệnh nhân, tôi muốn nhận xác nhận (và nhắc lịch) qua kênh tôi chọn ngay sau khi đặt lịch, để tôi biết chắc lịch đã được ghi nhận và đến đúng giờ.
- Độc lập: chỉ cần sự kiện "lịch đã tạo". Có thể đàm phán: kênh (SMS/email/Zalo), thời điểm nhắc. Ước lượng được: khoảng 3–5 điểm. Kiểm thử được: theo AC dưới đây.
- AC1 (thành công): Given lịch vừa được xác nhận, When hệ thống xử lý xong, Then trong vòng 1 phút bệnh nhân nhận tin nhắn gồm tên bác sĩ, ngày giờ, địa điểm/phòng và mã lịch.
- AC2 (nhắc lịch): Given lịch hẹn còn 24 giờ nữa và trạng thái "Đã xác nhận", When đến mốc nhắc, Then gửi đúng một tin nhắc; nếu lịch đã hủy thì không gửi.
- AC3 (gửi lỗi): Given nhà cung cấp SMS/email trả lỗi, When gửi thất bại, Then hệ thống thử lại tối đa 3 lần (backoff), nếu vẫn lỗi thì đánh dấu "chưa gửi", đồng thời vẫn hiển thị xác nhận trong app, và lễ tân thấy danh sách cần liên hệ.
- AC4 (liên hệ sai/biên): Given số điện thoại hoặc email không hợp lệ/không tồn tại, When gửi bị bounce, Then ghi nhận bounce và yêu cầu bệnh nhân cập nhật liên hệ khi mở app.
- AC5 (đổi/hủy): Given lịch bị đổi giờ hoặc hủy (bởi bệnh nhân hay bác sĩ), When thay đổi được lưu, Then gửi thông báo cập nhật ngay, không gửi trùng khi sự kiện bị xử lý lại (idempotent).

=== TASK E ===
- Hàng triệu người vào cùng lúc làm sập backend → hàng đợi ảo (virtual waiting room) như Ticketmaster Queue-it/Smart Queue: người dùng được xếp hàng và cho vào theo tốc độ hệ thống chịu được.
- Bot/scalper chiếm vé → Verified Fan (đăng ký xét duyệt trước), CAPTCHA/challenge, giới hạn số vé mỗi tài khoản/thẻ/thiết bị, bot management của Cloudflare/Akamai.
- Oversell cùng một ghế → giữ chỗ tạm (hold) có TTL 5–10 phút và khóa nguyên tử: Redis `SET NX EX`/Lua, hoặc `SELECT ... FOR UPDATE SKIP LOCKED`/optimistic locking trong DB; trạng thái ghế qua state machine available → held → sold.
- Hot-key và hot-row (một sự kiện hot) → chia shard theo event/section, cache đọc trên CDN/Redis, tách đường ghi nóng (inventory) khỏi đường đọc (catalog, mô tả).
- Thundering herd khi mở bán và cache stampede → mở bán lệch theo cohort từ hàng đợi, request coalescing, TTL ngẫu nhiên (jitter), cache trang tĩnh ở CDN/edge.
- Thanh toán chậm, lỗi một phần (đã trừ tiền nhưng chưa có vé) → saga + idempotency key; hết TTL giữ chỗ mới nhả ghế; đối soát với cổng thanh toán, có trạng thái pending để xử lý lại bất đồng bộ.
- Quá tải kéo sập dịch vụ phụ thuộc → backpressure, rate limit, load shedding, circuit breaker, bulkhead; ưu tiên đường checkout hơn browsing.
- Ghi đồng bộ làm nghẽn → hàng đợi (Kafka/SQS) cho việc không nằm trên đường chính (email vé, analytics, QR); ghi vào DB chính dùng event sourcing/CQRS hoặc ghi tuần tự theo partition.
- Chuẩn bị khả năng chịu tải → pre-warm autoscaling, load test với kịch bản flash sale (k6, Gatling), game day/chaos test, đa AZ/đa vùng, feature flag để tắt chức năng không thiết yếu.
- Công bằng, gian lận và sự cố → randomization trong hàng đợi thay vì first-come (lottery như Verified Fan), chuyển vé có kiểm soát (vé động/SafeTix), dashboard thời gian thực và runbook rollback.

=== TASK F ===
```json
{"language": "Python 3.12", "formatter": "ruff format", "linter": "ruff", "type_checker": "mypy", "test_framework": "pytest", "commands": {"format_check": "ruff format --check .", "lint": "ruff check .", "typecheck": "mypy .", "test": "pytest -q"}, "banned_libraries": ["requests", "flask", "pylint", "flake8", "black", "isort"], "rationale": "Ruff gộp format và lint nhanh, một công cụ duy nhất. Mypy kiểm tra kiểu tĩnh, pytest chuẩn kiểm thử. Cấm requests vì chặn event loop; dùng httpx. Cấm công cụ trùng ruff."}
```

=== TASK G ===
```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app . .

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
