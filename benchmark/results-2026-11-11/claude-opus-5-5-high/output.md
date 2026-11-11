=== TASK A ===
- [Critical] Webhook không xác thực chữ ký/nguồn gửi → ai cũng có thể gọi `/webhook/payment` để tự cộng tiền → xác minh chữ ký HMAC kèm timestamp chống replay, giới hạn IP (allowlist), và gọi API cổng thanh toán để kiểm tra lại trạng thái trước khi cộng tiền.
- [Critical] Webhook không idempotent → cổng thanh toán retry thì tiền bị cộng 2 lần → đặt UNIQUE cho `txn_id` và dùng state machine PENDING→SUCCESS chỉ chuyển một lần (`UPDATE ... WHERE status='PENDING'`), cập nhật trạng thái và cộng số dư trong cùng một DB transaction.
- [Critical] Cộng số dư kiểu đọc rồi ghi (read-modify-write) không khóa → race condition khiến mất cập nhật, số dư sai → dùng `UPDATE wallets SET balance = balance + $1 WHERE user_id=$2` (atomic) hoặc `SELECT ... FOR UPDATE` trong transaction.
- [Critical] Tin luôn `amount` mà webhook gửi lên → số bị sửa hoặc lệch thì vẫn cộng → đối chiếu với amount/currency của đơn PENDING đã lưu; lệch thì không cộng và phát cảnh báo.
- [Critical] Timeout 5s thì đánh dấu FAILED → thực tế cổng thanh toán có thể đã trừ tiền: user mất tiền mà ví không lên, hoặc webhook đến sau gặp giao dịch FAILED → dùng trạng thái PENDING/UNKNOWN, gửi idempotency key cho cổng, có job đối soát hỏi lại trạng thái, báo user "đang xử lý".
- [Critical] API nhận `card_number` và `cvv` → server rơi vào phạm vi PCI DSS, rò rỉ là lộ thẻ → dùng tokenization/hosted fields/redirect của cổng thanh toán, server không bao giờ chạm vào dữ liệu thẻ.
- [Critical] Log toàn bộ request body → số thẻ, CVV, JWT nằm trong log (vi phạm PCI, rủi ro lộ dữ liệu) → chỉ log theo whitelist field, che (mask) dữ liệu nhạy cảm, log có cấu trúc.
- [Critical] JWT secret yếu, hardcode trong `config.js` (nằm trong git) → bị lộ thì giả mạo được token của bất kỳ user nào → dùng secret ngẫu nhiên ≥256 bit lấy từ secret manager hoặc chuyển sang RS256/ES256; xoay (rotate) ngay vì secret đã lộ.
- [High] Token sống 365 ngày, không có cơ chế thu hồi → token bị đánh cắp dùng được cả năm → access token 5–15 phút, refresh token xoay vòng, có danh sách thu hồi.
- [Critical] Không backup, chỉ 1 instance PostgreSQL → hỏng đĩa là mất dữ liệu tiền, không khôi phục được, downtime kéo dài → backup PITR (WAL archiving), có replica/HA, định kỳ diễn tập restore.
- [High] `balance FLOAT` → sai số làm tròn, tiền lệch dần → dùng `NUMERIC(19,4)` hoặc BIGINT theo đơn vị nhỏ nhất, kèm cột currency.
- [High] Không có sổ cái giao dịch (ledger), chỉ có cột số dư → không audit, không đối soát được, không truy được sai lệch → bảng ledger bút toán kép append-only, số dư phải khớp tổng ledger, đối soát hằng ngày với cổng thanh toán.
- [High] Không validate `amount` (âm, 0, quá lớn, sai kiểu) → bị lạm dụng hoặc lỗi dữ liệu → validate phía server (min/max, số nguyên theo đơn vị nhỏ nhất), dùng CHECK constraint `balance >= 0`.
- [High] Không rate limit hay chống gian lận ở `/topup` → bị dùng để thử thẻ đánh cắp (card testing), dính chargeback → rate limit theo user/IP/thẻ, 3DS, hệ thống chấm điểm gian lận.
- [Medium] Cache số dư trong Redis → hiển thị sai, quyết định dựa trên dữ liệu cũ → DB là nguồn sự thật duy nhất; không cache số dư, hoặc invalidate ngay khi ghi.
- [Medium] `GET /transactions` trả về toàn bộ lịch sử → payload lớn, DB chậm, dễ bị DoS → cursor pagination có limit tối đa, index `(user_id, created_at)`.
- [Medium] Không ràng buộc dữ liệu (`user_id` thiếu UNIQUE, không có FK) và có nguy cơ IDOR nếu lấy user_id từ tham số → thêm UNIQUE/FK, user_id luôn lấy từ token.
- [Medium] Không có monitoring/alerting (webhook lỗi, giao dịch PENDING tồn lâu, lệch đối soát) → sự cố tiền bạc không ai phát hiện → metrics, alert, dashboard đối soát; bắt buộc HTTPS/TLS.

=== TASK B ===
```python
"""duration.py - Chuyển chuỗi thời lượng dạng '1d 2h3m 4s' thành tổng số giây."""
import re

__all__ = ["parse_duration", "MAX_SECONDS"]

MAX_SECONDS = 315_360_000
_UNIT_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_UNIT_RANK = {"d": 0, "h": 1, "m": 2, "s": 3}
# Dùng [0-9] thay vì \d để chỉ chấp nhận chữ số ASCII.
_COMPONENT = re.compile(r"([0-9]+)([dhms])")


def parse_duration(s) -> int:
    if not isinstance(s, str):
        raise TypeError(f"duration must be str, got {type(s).__name__}")

    text = s.strip()
    if not text:
        raise ValueError("empty duration string")

    # Bước 1: kiểm tra toàn bộ định dạng trước (lỗi định dạng ưu tiên hơn overflow).
    components = []
    pos, n, last_rank = 0, len(text), -1
    while pos < n:
        if components:
            # Giữa các thành phần chỉ cho phép dấu cách ' ' (0 hoặc nhiều).
            while pos < n and text[pos] == " ":
                pos += 1
        match = _COMPONENT.match(text, pos)
        if match is None:
            raise ValueError(f"invalid duration format at position {pos}")
        digits, unit = match.groups()
        rank = _UNIT_RANK[unit]
        if rank <= last_rank:
            raise ValueError(f"unit {unit!r} out of order or repeated")
        last_rank = rank
        components.append((digits, unit))
        pos = match.end()

    # Bước 2: tính tổng; bỏ số 0 đứng đầu để tránh giới hạn chuyển đổi int của chuỗi quá dài.
    total = 0
    for digits, unit in components:
        significant = digits.lstrip("0") or "0"
        if len(significant) > 10:  # >= 10**10 chắc chắn vượt MAX_SECONDS
            raise OverflowError("duration exceeds maximum")
        total += int(significant) * _UNIT_SECONDS[unit]

    if total > MAX_SECONDS:
        raise OverflowError(f"duration {total}s exceeds maximum {MAX_SECONDS}s")
    return total
```

=== TASK C ===
```python
from paginate import paginate

import copy
import math

import pytest


def _expected(items, page, page_size):
    total = len(items)
    total_pages = math.ceil(total / page_size) if total else 0
    return {
        "items": items[(page - 1) * page_size : page * page_size],
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
    }


TEN = list(range(1, 11))


@pytest.mark.parametrize(
    "page, exp_items, exp_has_next",
    [
        (1, [1, 2, 3], True),
        (2, [4, 5, 6], True),
        (3, [7, 8, 9], True),
        (4, [10], False),  # trang cuối không đầy
        (5, [], False),  # vượt total_pages -> rỗng, không lỗi
        (10**6, [], False),
    ],
)
def test_basic_pages(page, exp_items, exp_has_next):
    assert paginate(TEN, page, 3) == {
        "items": exp_items,
        "total": 10,
        "total_pages": 4,
        "has_next": exp_has_next,
    }


def test_exact_division():
    items = list(range(9))
    assert paginate(items, 3, 3) == {
        "items": [6, 7, 8],
        "total": 9,
        "total_pages": 3,
        "has_next": False,
    }
    assert paginate(items, 2, 3)["has_next"] is True
    assert paginate(items, 4, 3)["items"] == []


@pytest.mark.parametrize("page", [1, 2, 50])
def test_empty_items(page):
    assert paginate([], page, 10) == {
        "items": [],
        "total": 0,
        "total_pages": 0,
        "has_next": False,
    }


def test_page_size_one():
    items = ["a", "b", "c", "d", "e"]
    assert paginate(items, 1, 1) == {"items": ["a"], "total": 5, "total_pages": 5, "has_next": True}
    assert paginate(items, 4, 1)["has_next"] is True
    assert paginate(items, 5, 1) == {"items": ["e"], "total": 5, "total_pages": 5, "has_next": False}
    assert paginate(items, 6, 1)["items"] == []


def test_page_size_hundred():
    items = list(range(250))
    r = paginate(items, 3, 100)
    assert r == {"items": list(range(200, 250)), "total": 250, "total_pages": 3, "has_next": False}
    assert paginate(items, 1, 100)["items"] == list(range(100))
    assert paginate(list(range(100)), 1, 100)["total_pages"] == 1
    assert paginate(list(range(100)), 1, 100)["has_next"] is False
    assert paginate(list(range(101)), 1, 100)["total_pages"] == 2
    assert paginate(list(range(101)), 1, 100)["has_next"] is True
    assert paginate(list(range(101)), 2, 100)["items"] == [100]


def test_page_size_larger_than_total():
    assert paginate([1, 2, 3], 1, 10) == {"items": [1, 2, 3], "total": 3, "total_pages": 1, "has_next": False}
    assert paginate([1, 2, 3], 2, 10)["items"] == []


def test_single_item():
    assert paginate(["x"], 1, 100) == {"items": ["x"], "total": 1, "total_pages": 1, "has_next": False}


@pytest.mark.parametrize("page", [0, -1, -100])
@pytest.mark.parametrize("items", [[], TEN])
def test_invalid_page(page, items):
    with pytest.raises(ValueError):
        paginate(items, page, 10)


@pytest.mark.parametrize("page_size", [0, -1, 101, 1000])
@pytest.mark.parametrize("items", [[], TEN])
def test_invalid_page_size(page_size, items):
    with pytest.raises(ValueError):
        paginate(items, 1, page_size)


@pytest.mark.parametrize("page_size", [1, 2, 99, 100])
def test_valid_page_size_boundaries(page_size):
    r = paginate(TEN, 1, page_size)
    assert r == _expected(TEN, 1, page_size)


def test_both_invalid_raises_value_error():
    with pytest.raises(ValueError):
        paginate(TEN, 0, 0)


def test_return_shape_and_types():
    r = paginate(TEN, 2, 3)
    assert isinstance(r, dict)
    assert set(r.keys()) == {"items", "total", "total_pages", "has_next"}
    assert type(r["items"]) is list
    assert type(r["total"]) is int
    assert type(r["total_pages"]) is int
    assert type(r["has_next"]) is bool
    assert type(paginate(TEN, 4, 3)["has_next"]) is bool
    assert type(paginate([], 1, 3)["has_next"]) is bool


def test_does_not_mutate_input():
    items = [{"id": i} for i in range(7)]
    snapshot = copy.deepcopy(items)
    paginate(items, 2, 3)
    paginate(items, 99, 3)
    assert items == snapshot


def test_result_list_is_new_and_preserves_identity_and_order():
    objs = [object() for _ in range(5)]
    r = paginate(objs, 1, 100)
    assert r["items"] is not objs
    assert len(r["items"]) == 5
    assert all(a is b for a, b in zip(r["items"], objs))
    r["items"].append("extra")
    assert len(objs) == 5


def test_heterogeneous_items_preserved():
    items = [None, 0, "", False, [], {"k": 1}, 3.5]
    assert paginate(items, 1, 4)["items"] == [None, 0, "", False]
    assert paginate(items, 2, 4)["items"] == [[], {"k": 1}, 3.5]


@pytest.mark.parametrize("n", range(0, 24))
@pytest.mark.parametrize("page_size", [1, 2, 3, 4, 5, 7, 10, 22, 23, 99, 100])
def test_matches_reference_exhaustive(n, page_size):
    items = list(range(n))
    last = (n // page_size) + 3
    for page in range(1, last + 1):
        assert paginate(items, page, page_size) == _expected(items, page, page_size), (n, page_size, page)
```

=== TASK D ===
**(1) Điểm mơ hồ / yêu cầu còn thiếu cần hỏi lại**
- Vai trò người dùng: ngoài bệnh nhân còn lễ tân, bác sĩ, admin không? Ai tạo/sửa lịch làm việc của bác sĩ?
- Nền tảng: app mobile (iOS/Android), web hay cả hai? Có cần đa ngôn ngữ?
- Định danh: đăng ký bằng OTP số điện thoại hay tài khoản? Có cho đặt hộ người thân/trẻ em? Có thu thập BHYT/CCCD?
- Lịch bác sĩ: dữ liệu lấy từ đâu (đã có HIS chưa)? Mỗi slot dài bao lâu, nhận bao nhiêu bệnh nhân? Xử lý ngày nghỉ, ca trực, nhiều chi nhánh thế nào?
- Cách chọn: theo chuyên khoa/triệu chứng hay chỉ theo bác sĩ? Có lựa chọn "bác sĩ nào cũng được"?
- Xác nhận: tự động ngay hay lễ tân duyệt? Gửi qua kênh nào (SMS/Zalo/email/push)? Có nhắc lịch không, trước bao lâu?
- Thanh toán: có thu trước phí khám hoặc đặt cọc không? Chính sách hoàn tiền?
- Hủy/đổi lịch: hạn chót, số lần được đổi; xử lý no-show (khóa tài khoản, mất cọc)?
- Giới hạn: được đặt trước tối đa bao nhiêu ngày, mỗi người giữ tối đa bao nhiêu lịch đang chờ, chống giữ chỗ ảo ra sao?
- Tại phòng khám: có check-in, cấp số thứ tự, tích hợp HIS/EMR không? Bác sĩ đến trễ hoặc hủy thì xử lý thế nào?
- Pháp lý/bảo mật: dữ liệu sức khỏe là dữ liệu nhạy cảm (Nghị định 13/2023/NĐ-CP): cần đồng ý, lưu trữ ở đâu, ai được xem?
- Phạm vi & phi chức năng: có khám từ xa không, quy mô người dùng, SLA, deadline, ngân sách, KPI thành công?

**(2) User Story**

*US1 – Đặt lịch theo khung giờ trống*
- Là bệnh nhân đã đăng nhập, tôi muốn xem các khung giờ còn trống của một bác sĩ và đặt một khung giờ, để có lịch khám chắc chắn mà không phải xếp hàng chờ.
- AC1: Given bác sĩ A còn trống slot 09:00 ngày D, When tôi chọn slot đó và bấm "Xác nhận đặt", Then lịch hẹn được tạo với trạng thái "Đã đặt" và mã lịch hẹn, đồng thời slot không còn hiển thị là trống với người khác.
- AC2 (tranh chấp): Given slot 09:00 chỉ còn 1 chỗ, When hai bệnh nhân gửi yêu cầu đặt gần như đồng thời, Then chỉ một người thành công; người kia nhận thông báo "Khung giờ vừa có người đặt, vui lòng chọn giờ khác" và danh sách slot được làm mới.
- AC3 (biên thời gian): Given một slot đã qua, hoặc bắt đầu trong vòng < X giờ, hoặc nằm ngoài khoảng đặt trước tối đa N ngày (X, N chờ khách hàng chốt), When tôi xem lịch, Then slot đó không hiển thị và API từ chối nếu vẫn bị gọi.
- AC4 (trùng lịch): Given tôi đã có một lịch hẹn chồng giờ với slot định đặt, hoặc đã đạt giới hạn số lịch đang chờ, When tôi đặt, Then hệ thống từ chối và nêu rõ lý do.
- AC5 (không có slot): Given bác sĩ A không còn slot trống trong N ngày tới, When tôi mở lịch của bác sĩ, Then hiển thị "Chưa có lịch trống" và gợi ý bác sĩ cùng chuyên khoa.
- AC6 (retry): Given mạng chập chờn khiến tôi bấm gửi lại, When server nhận 2 request cùng idempotency key, Then chỉ một lịch hẹn được tạo.

*US2 – Nhận xác nhận và nhắc lịch*
- Là bệnh nhân vừa đặt lịch, tôi muốn nhận tin xác nhận và tin nhắc lịch, để có bằng chứng lịch hẹn và không quên đi khám.
- AC1: Given đặt lịch thành công, When lịch hẹn được tạo, Then trong ≤ 1 phút tôi nhận SMS/push gồm mã lịch, bác sĩ, chuyên khoa, ngày giờ, địa chỉ và link hủy/đổi lịch; lịch hẹn cũng hiện trong mục "Lịch của tôi".
- AC2: Given lịch hẹn còn hiệu lực, When còn 24h đến giờ khám, Then hệ thống gửi đúng 1 tin nhắc.
- AC3 (đã hủy): Given lịch hẹn đã bị hủy, When đến mốc nhắc lịch, Then không gửi tin nhắc.
- AC4 (gửi lỗi): Given nhà cung cấp SMS lỗi, When gửi tin xác nhận thất bại, Then hệ thống retry tối đa 3 lần có backoff; nếu vẫn lỗi thì ghi log và đánh dấu để lễ tân liên hệ; lịch hẹn KHÔNG bị hủy hay rollback.
- AC5: Given đặt lịch thất bại, When kết thúc request, Then không gửi bất kỳ tin xác nhận nào.
- AC6: Given phòng khám hủy hoặc đổi lịch của bác sĩ, When thay đổi được lưu, Then bệnh nhân bị ảnh hưởng được thông báo trong ≤ 15 phút.

=== TASK E ===
- Lượng truy cập tăng đột biến vượt năng lực hệ thống → phòng chờ ảo (virtual waiting room) đứng trước luồng mua: Ticketmaster Smart Queue, Queue-it, Cloudflare Waiting Room; cho người vào theo tốc độ backend chịu được, kèm access token có chữ ký.
- Bot/scalper vét vé → Ticketmaster Verified Fan (đăng ký trước, nhận mã mời), bot management (Akamai, Cloudflare), CAPTCHA, device fingerprint, giới hạn số vé theo tài khoản/thẻ/địa chỉ.
- Bán vượt số ghế (oversell) khi nhiều người tranh cùng ghế → giữ chỗ tạm có TTL (vài phút) bằng thao tác atomic: Redis `SET NX EX`/Lua script, hoặc conditional update `UPDATE seats SET status='HELD' WHERE id=? AND status='AVAILABLE'`; hết hạn thì tự nhả ghế.
- Hot row/hot partition (cả triệu request dồn vào 1 sự kiện) → chia tồn kho thành nhiều shard/bucket theo khu vực và trừ kho trong bộ nhớ (cách của flash sale Alibaba 11.11 và 12306 Trung Quốc), ghi xuống DB bất đồng bộ.
- Lượng đọc khổng lồ (trang sự kiện, sơ đồ ghế) → CDN/edge cache, sơ đồ ghế render sẵn, tình trạng ghế cập nhật kiểu eventual consistency; chỉ kiểm tra chính xác ở bước giữ chỗ.
- Cổng thanh toán chậm hoặc quá tải → tách bước giữ chỗ khỏi bước thanh toán, xử lý đơn qua hàng đợi (Kafka/SQS), dùng idempotency key (mô hình của Stripe), có job đối soát.
- Autoscaling phản ứng không kịp → biết trước giờ mở bán nên pre-scale/pre-warm, load test ở quy mô thật, tổ chức game day; bài học Taylor Swift Eras Tour (11/2022): khoảng 3,5 tỷ request vượt xa dự kiến, Ticketmaster phải hủy đợt bán công khai.
- Một thành phần lỗi kéo sập cả hệ thống → rate limit nhiều tầng, circuit breaker, bulkhead, load shedding (trả 503 hoặc đẩy về hàng đợi), tạm tắt tính năng phụ.
- Công bằng: người vào sớm hay script lợi thế hơn → xếp những ai vào trước giờ mở bán theo thứ tự ngẫu nhiên (pre-queue randomization của Queue-it/Ticketmaster), hiển thị vị trí và ETA trong hàng đợi.
- Vé giả và phe vé bán lại → vé động có mã xoay vòng (Ticketmaster SafeTix), sàn bán lại chính thức có trần giá, vé gắn với danh tính người mua.

=== TASK F ===
```json
{
  "language": "Python 3.12",
  "formatter": "ruff format",
  "linter": "ruff",
  "type_checker": "mypy",
  "test_framework": "pytest",
  "commands": {
    "format_check": "ruff format --check --diff .",
    "lint": "ruff check .",
    "typecheck": "mypy --strict .",
    "test": "pytest -q"
  },
  "banned_libraries": ["requests", "pycrypto", "pickle", "nose"],
  "rationale": "Ruff gộp format và lint, rất nhanh; mypy bắt lỗi kiểu; pytest chuẩn. Cấm requests (chặn event loop, dùng httpx), pycrypto (bỏ bảo trì), pickle (RCE), nose (ngừng phát triển)."
}
```

=== TASK G ===
```dockerfile
# syntax=docker/dockerfile:1
# Lưu ý: nên có .dockerignore (.git, .venv, __pycache__, .env, tests...) để không đưa rác/secret vào image.

########## Stage 1: build dependencies ##########
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
# Copy requirements trước để tận dụng layer cache
COPY requirements.txt .
# Nếu có package cần biên dịch, cài thêm build-essential ở stage này (không ảnh hưởng image cuối)
RUN pip install --no-cache-dir -r requirements.txt

########## Stage 2: runtime ##########
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# User không phải root
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
# Code thuộc root (chỉ đọc với user app) để tránh bị sửa lúc runtime
COPY . .

USER app

EXPOSE 8000

# Image slim không có curl: dùng Python stdlib để healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"]

# Exec form để uvicorn là PID 1 và nhận SIGTERM, shutdown êm
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--timeout-graceful-shutdown", "20"]
```
