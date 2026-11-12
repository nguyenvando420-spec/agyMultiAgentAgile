=== TASK H ===
```python
import hashlib
import re
import unicodedata

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:0|\+84)[35789]\d{8}(?!\d)")
_WS_RE = re.compile(r"\s+")
_KEYS = ("id", "source_id", "text", "label")


def _split_of(source_id):
    bucket = int(hashlib.sha256(source_id.encode("utf-8")).hexdigest(), 16) % 10
    if bucket == 0:
        return "test"
    if bucket == 1:
        return "val"
    return "train"


def prepare_dataset(records):
    if not isinstance(records, list):
        raise TypeError("records must be a list")

    result = {"train": [], "val": [], "test": []}
    dropped_invalid = 0
    dropped_duplicate = 0
    pii_replaced = 0
    seen = set()

    for rec in records:
        if not isinstance(rec, dict) or any(
            k not in rec or not isinstance(rec[k], str) for k in _KEYS
        ):
            dropped_invalid += 1
            continue

        text = unicodedata.normalize("NFKC", rec["text"])
        text = _WS_RE.sub(" ", text).strip()
        if not text:
            dropped_invalid += 1
            continue

        text, n_email = _EMAIL_RE.subn("<EMAIL>", text)
        text, n_phone = _PHONE_RE.subn("<PHONE>", text)

        key = text.casefold()
        if key in seen:
            dropped_duplicate += 1
            continue
        seen.add(key)

        pii_replaced += n_email + n_phone
        result[_split_of(rec["source_id"])].append(
            {
                "id": rec["id"],
                "source_id": rec["source_id"],
                "text": text,
                "label": rec["label"],
            }
        )

    result["stats"] = {
        "input": len(records),
        "dropped_invalid": dropped_invalid,
        "dropped_duplicate": dropped_duplicate,
        "pii_replaced": pii_replaced,
    }
    return result
```

=== TASK I ===
```json
{"method": "qlora", "load_in_4bit": true, "bnb_4bit_quant_type": "nf4", "compute_dtype": "float16",
 "bf16": false, "fp16": true, "attn_implementation": "sdpa", "gradient_checkpointing": true,
 "per_device_train_batch_size": 8, "gradient_accumulation_steps": 4, "max_seq_length": 256,
 "lora_r": 16, "lora_alpha": 32, "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
 "output_dir": "/kaggle/working/checkpoints", "save_interval_minutes": 20, "resume_from_checkpoint": true,
 "export_format": "gguf", "quant_type": "Q4_K_M", "est_gguf_size_gb": 1.0,
 "kv_cache_fp16_gb_at_4096": 0.11, "fits_rtx2060_6gb": true,
 "use_golden_test_for_early_stopping": false, "full_ft_7b_bf16_on_t4_feasible": false,
 "notes": "T4 không hỗ trợ bf16 và flash-attention-2 nên dùng fp16 và sdpa. Checkpoint lưu trong /kaggle/working để resume khi phiên bị ngắt. Early stopping dùng tập val, không dùng Golden Test. KV cache bằng 2×28×2×128×2 byte×4096, xấp xỉ 117 MB."}
```

=== TASK J ===
```python
import json
import re

_FENCE_RE = re.compile(r"```(?:json)?[ \t]*\r?\n?(.*?)```", re.DOTALL | re.IGNORECASE)


def _type_ok(value, expected):
    if expected is bool:
        return isinstance(value, bool)
    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected is str:
        return isinstance(value, str)
    return isinstance(value, expected)


def _extract_and_validate(raw, required):
    """Return (data, None) if valid, otherwise (None, error_message)."""
    if not isinstance(raw, str):
        return None, "response is not a string"

    fence = _FENCE_RE.search(raw)
    if fence:
        candidate = fence.group(1)
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end < start:
            return None, "no JSON object found in response"
        candidate = raw[start:end + 1]

    try:
        obj = json.loads(candidate.strip())
    except (ValueError, TypeError) as exc:
        return None, "invalid JSON: %s" % exc

    if not isinstance(obj, dict):
        return None, "JSON is not an object"

    data = {}
    for name, expected in required.items():
        if name not in obj:
            return None, "missing field '%s'" % name
        value = obj[name]
        if not _type_ok(value, expected):
            tname = getattr(expected, "__name__", str(expected))
            return None, "field '%s' must be of type %s" % (name, tname)
        data[name] = value
    return data, None


def call_structured(client, prompt, required, max_retries=2, fallback=None):
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a str")
    if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries must be an int >= 0")

    current = prompt
    last_error = ""
    attempts = 0

    for _ in range(1 + max_retries):
        attempts += 1
        try:
            raw = client.generate(current, timeout=10.0)
        except (TimeoutError, ConnectionError) as exc:
            last_error = "%s: %s" % (type(exc).__name__, exc)
            current = prompt
            continue

        data, error = _extract_and_validate(raw, required)
        if error is None:
            return {"ok": True, "data": data, "attempts": attempts}

        last_error = error
        current = (
            prompt
            + "\n\n"
            + "Previous response was invalid: %s. Reply with only a valid JSON object." % error
        )

    return {"ok": False, "data": fallback, "attempts": attempts, "error": last_error}
```

=== TASK K ===
**K1**
```json
{"p95_ms": 900.0, "accuracy": 0.85, "macro_f1": 0.527, "raw_schema_validity": 0.94}
```
- P95: N=20, hạng = ceil(19) = 19, nên giá trị thứ 19 trong dãy sắp tăng là 900 ms.
- Accuracy = 17/20 = 0.85.
- F1 của A = 32/35 ≈ 0.914.
- F1 của B = 2/3 ≈ 0.667.
- F1 của C = 0.
- Macro-F1 = (0.914 + 0.667 + 0) / 3 ≈ 0.527.
- Raw validity = 188/200 = 0.94. Con số 197/200 tính cả bước tự sửa nên không dùng.

**K2 – Các lỗi phương pháp/rủi ro**
- [Nghiêm trọng] Chia ngẫu nhiên từng dòng trong khi mỗi tin gốc có 3 bản diễn đạt lại → rò rỉ train/test, điểm bị thổi phồng → chia theo nhóm `source_id` của tin gốc (group split).
- [Nghiêm trọng] Chọn checkpoint theo điểm Golden Test rồi báo cáo luôn điểm đó → lạc quan do chọn lọc, test không còn độc lập → chọn checkpoint trên val, giữ một test set khóa chặt, chỉ chấm một lần.
- [Nghiêm trọng] 96% accuracy trong khi lớp đa số chiếm 87% (baseline đoán lớp đa số đạt 87%) → accuracy không phản ánh chất lượng, lớp hiếm bị che khuất → báo macro-F1, precision/recall từng lớp, ma trận nhầm lẫn, so với baseline.
- [Nghiêm trọng] Chấm model fp16 nhưng triển khai GGUF Q4_K_M → chất lượng thật của bản triển khai chưa được kiểm chứng, lượng tử hóa có thể làm tụt điểm → đánh giá lại chính artifact Q4_K_M, trên cùng test set và cùng runtime llama.cpp.
- [Nghiêm trọng] "Golden Test" chỉ 50 mẫu, lấy ngẫu nhiên từ test tổng hợp, chưa người thật gán nhãn → khoảng tin cậy rất rộng (48/50 có Wilson 95% CI khoảng 87–99%), lớp hiếm gần như vắng mặt (chỉ khoảng 6–7 mẫu không thuộc lớp đa số) → dùng tập golden do người gán nhãn, phân tầng theo lớp, cỡ vài trăm mẫu trở lên, kèm khoảng tin cậy.
- [Cao] Dữ liệu là bản diễn đạt lại bởi LLM (teacher), cả test cũng tổng hợp → không đại diện cho tin nhắn thật (lỗi chính tả, tiếng Việt không dấu, tiếng lóng), nhãn có thể lệch khi diễn đạt lại → test bằng tin nhắn thật do người gán nhãn, kiểm tra mẫu nhãn sau khi diễn đạt lại, chạy shadow test trên traffic thật.
- [Cao] Chỉ khử trùng lặp chính xác → các bản diễn đạt gần giống vẫn còn, làm rò rỉ ngữ nghĩa và phình dữ liệu → dùng near-dup (MinHash/embedding similarity) và khử trùng lặp theo nhóm.
- [Cao] Giám khảo giải thích là Qwen2.5-72B, cùng họ với teacher tạo dữ liệu → thiên vị tự ưu tiên, chưa hiệu chỉnh với người → dùng giám khảo khác họ, có rubric, đối chiếu mẫu chấm tay và đo độ đồng thuận.
- [Cao] JSON hợp lệ 100% chỉ tính sau bước tự sửa → che giấu tỷ lệ lỗi thô, và hợp lệ schema không đồng nghĩa đúng nghĩa → báo raw validity (trước sửa), tỷ lệ phải sửa và độ trễ của bước sửa, kiểm tra thêm tính đúng nội dung.
- [Cao] Latency chỉ báo trung bình, đo 1 request, ngữ cảnh 256, trên T4, trong khi production là RTX 2060, ngữ cảnh đến 2048, 5 người dùng đồng thời → không đại diện cho production, đuôi trễ (p95/p99) bị bỏ qua → đo p50/p95/p99, TTFT và tokens/s trên RTX 2060 với GGUF Q4_K_M, ngữ cảnh 2048, 5 luồng đồng thời, với số request đủ lớn.
- [Cao] VRAM 1,3 GB chỉ đo ngay sau khi nạp model → bỏ qua KV cache, compute buffer và 5 luồng đồng thời, rủi ro OOM trên card 6 GB → đo VRAM đỉnh dưới tải thật (ngữ cảnh 2048 × 5 luồng), chừa headroom cho hệ điều hành/hiển thị.
- [Cao] An toàn: chỉ 5 prompt injection bằng tiếng Anh, 5/5 → quá ít, sai ngôn ngữ (người dùng nói tiếng Việt), khoảng tin cậy rất rộng, thiếu jailbreak/rò rỉ PII/injection gián tiếp → dùng bộ test tiếng Việt và đa ngôn ngữ, hàng trăm mẫu, đa dạng tấn công, báo tỷ lệ tấn công thành công kèm CI, rà soát rò rỉ PII.
- [Trung bình] Giải mã temperature 0.7, chạy 1 lần → kết quả ngẫu nhiên, không biết phương sai, và có thể khác cấu hình production → chạy nhiều seed hoặc dùng greedy/temperature thấp như production, báo trung bình ± độ lệch chuẩn.
- [Trung bình] Không có baseline, không so với phiên bản trước, không có ngưỡng chấp nhận đặt từ trước → "Đạt chuẩn" không có căn cứ, dễ quyết định theo cảm tính → đặt tiêu chí phát hành định lượng từ trước (macro-F1, recall từng lớp, p95, VRAM, safety) và so với baseline/v1.1.
- [Trung bình] Thiếu phân tích lỗi, kiểm thử độ bền (typo, không dấu, tin nhắn dài/ngắn, ngoài phân phối) và kế hoạch giám sát/rollback → rủi ro lỗi khi chạy thật mà không phát hiện được → thêm error analysis, test robustness, theo dõi drift và kế hoạch rollback.
- [Thấp] Báo cáo không nêu phiên bản dữ liệu/seed/commit, nên khó tái lập → ghi version dữ liệu, seed, cấu hình và commit.
- [Kết luận] Kết luận "Đạt chuẩn phát hành" chưa được các bằng chứng trên hỗ trợ → chưa phát hành, đánh giá lại theo các mục trên.
