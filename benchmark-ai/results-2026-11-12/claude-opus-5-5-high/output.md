=== TASK H ===
```python
"""Chuẩn bị dataset: validate, chuẩn hóa, ẩn PII, khử trùng lặp, chia tập theo source_id."""

import hashlib
import re
import unicodedata

_REQUIRED_KEYS = ("id", "source_id", "text", "label")
_WHITESPACE_RE = re.compile(r"\s+")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:0|\+84)[35789]\d{8}(?!\d)")


def _is_valid(record):
    if not isinstance(record, dict):
        return False
    for key in _REQUIRED_KEYS:
        if key not in record or not isinstance(record[key], str):
            return False
    return True


def _normalize(text):
    text = unicodedata.normalize("NFKC", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _redact(text):
    text, n_email = _EMAIL_RE.subn("<EMAIL>", text)
    text, n_phone = _PHONE_RE.subn("<PHONE>", text)
    return text, n_email + n_phone


def _split_for(source_id):
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

    for record in records:
        if not _is_valid(record):
            dropped_invalid += 1
            continue

        text = _normalize(record["text"])
        if not text:
            dropped_invalid += 1
            continue

        text, n_replaced = _redact(text)
        dedup_key = text.casefold()
        if dedup_key in seen:
            dropped_duplicate += 1
            continue
        seen.add(dedup_key)
        pii_replaced += n_replaced

        source_id = record["source_id"]
        result[_split_for(source_id)].append(
            {
                "id": record["id"],
                "source_id": source_id,
                "text": text,
                "label": record["label"],
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
{
  "method": "qlora",
  "load_in_4bit": true,
  "bnb_4bit_quant_type": "nf4",
  "compute_dtype": "float16",
  "bf16": false,
  "fp16": true,
  "attn_implementation": "sdpa",
  "gradient_checkpointing": true,
  "per_device_train_batch_size": 16,
  "gradient_accumulation_steps": 2,
  "max_seq_length": 256,
  "lora_r": 16,
  "lora_alpha": 32,
  "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
  "output_dir": "/kaggle/working/checkpoints",
  "save_interval_minutes": 30,
  "resume_from_checkpoint": true,
  "export_format": "gguf",
  "quant_type": "Q8_0",
  "est_gguf_size_gb": 1.65,
  "kv_cache_fp16_gb_at_4096": 0.117,
  "fits_rtx2060_6gb": true,
  "use_golden_test_for_early_stopping": false,
  "full_ft_7b_bf16_on_t4_feasible": false,
  "notes": "Dùng fp16 vì T4 (Turing) không hỗ trợ bf16 và FlashAttention2. Checkpoint lưu vào /kaggle/working mỗi 30 phút để resume khi phiên bị ngắt. Early stopping theo tập val, Golden Test chỉ dùng để chấm cuối. Merge adapter rồi convert GGUF Q8_0, sau đó chấm lại chính bản GGUF bằng llama.cpp."
}
```

=== TASK J ===
```python
"""Gọi model lấy đầu ra JSON có cấu trúc, có retry kèm phản hồi lỗi và fallback."""

import json
import re

_FENCE_RE = re.compile(r"```[ \t]*(?:json)?[ \t]*\r?\n?(.*?)```", re.DOTALL | re.IGNORECASE)
_RETRYABLE_ERRORS = (TimeoutError, ConnectionError)


def _extract_json(raw):
    if not isinstance(raw, str):
        raise ValueError("model response is not a string")
    match = _FENCE_RE.search(raw)
    if match:
        candidate = match.group(1)
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("no JSON object found in response")
        candidate = raw[start:end + 1]
    obj = json.loads(candidate)
    if not isinstance(obj, dict):
        raise ValueError("parsed JSON is not an object")
    return obj


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


def _validate(obj, required):
    problems = []
    for field, expected in required.items():
        if field not in obj:
            problems.append(f"missing field '{field}'")
        elif not _type_ok(obj[field], expected):
            problems.append(
                f"field '{field}' must be {expected.__name__}, got {type(obj[field]).__name__}"
            )
    return problems


def _feedback(original_prompt, error):
    return (
        original_prompt
        + "\n\n"
        + f"Your previous response was invalid: {error}. "
        + "Reply with a single valid JSON object containing all required fields with correct types."
    )


def call_structured(client, prompt, required, max_retries=2, fallback=None):
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a str")
    if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries must be a non-negative int")

    current_prompt = prompt
    attempts = 0
    last_error = "no attempt made"

    for _ in range(1 + max_retries):
        attempts += 1
        try:
            raw = client.generate(current_prompt, timeout=10.0)
        except _RETRYABLE_ERRORS as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            current_prompt = prompt
            continue

        try:
            obj = _extract_json(raw)
        except ValueError as exc:
            last_error = f"could not parse JSON: {exc}"
            current_prompt = _feedback(prompt, last_error)
            continue

        problems = _validate(obj, required)
        if problems:
            last_error = "schema validation failed: " + "; ".join(problems)
            current_prompt = _feedback(prompt, last_error)
            continue

        return {
            "ok": True,
            "data": {field: obj[field] for field in required},
            "attempts": attempts,
        }

    return {"ok": False, "data": fallback, "attempts": attempts, "error": last_error}
```

=== TASK K ===
**K1**
```json
{"p95_ms": 900.000, "accuracy": 0.850, "macro_f1": 0.527, "raw_schema_validity": 0.940}
```
- P95: sắp tăng dần, hạng ceil(0,95 × 20) = 19 → 900 ms.
- Accuracy: 17/20 = 0,85.
- F1 lớp A = 32/35 ≈ 0,914; F1 lớp B = 2/3 ≈ 0,667; F1 lớp C = 0 → macro-F1 ≈ 0,527.
- Tỷ lệ JSON hợp lệ thô: 188/200 = 0,94.

**K2**
- [Nghiêm trọng] Chia ngẫu nhiên theo từng dòng sau khi diễn đạt lại → các bản diễn đạt của cùng một tin gốc rơi vào cả train lẫn test (rò rỉ dữ liệu) → điểm bị thổi phồng → chia theo nhóm tin gốc (group split theo source_id/khách hàng/hội thoại).
- [Nghiêm trọng] Chỉ khử trùng lặp chính xác → bản diễn đạt lại gần giống nhau vẫn lọt qua các tập → khử gần trùng (MinHash/embedding) trước khi chia, và chia theo nhóm.
- [Nghiêm trọng] Golden Test lấy từ dữ liệu tổng hợp do teacher sinh ra, không phải tin thật có người gán nhãn → không phản ánh phân phối Production → dựng Golden Test riêng từ tin thật, người gán nhãn, khóa cố định, không trùng nguồn với train.
- [Nghiêm trọng] Chọn checkpoint theo điểm trên Golden Test → thiên lệch chọn lọc, quá khớp tập test → chọn theo val, Golden Test chỉ chấm một lần cuối.
- [Nghiêm trọng] Accuracy 96% khi lớp đa số chiếm 87% → baseline đoán toàn lớp đa số đã được ~87%, che giấu các lớp thiểu số đoán sai → báo cáo macro-F1, recall từng lớp, confusion matrix và so với baseline.
- [Cao] Golden Test chỉ 50 mẫu → khoảng tin cậy 95% khoảng ±5–6 điểm %, nhiều lớp gần như không có mẫu → tăng lên hàng trăm/nghìn mẫu, phân tầng theo lớp, kèm khoảng tin cậy bootstrap.
- [Nghiêm trọng] Chấm bản fp16 nhưng triển khai GGUF Q4_K_M → chất lượng sau lượng tử hóa chưa được kiểm chứng → chấm lại chính bản GGUF bằng llama.cpp với đúng tham số triển khai.
- [Cao] Dùng Qwen2.5-72B làm giám khảo, cũng chính là teacher sinh dữ liệu → giám khảo thiên vị văn phong của chính nó, chưa hiệu chỉnh với người → đổi giám khảo khác họ model, đo mức đồng thuận với người chấm (kappa); phần giải thích không thay được chỉ số phân loại.
- [Cao] Tỷ lệ JSON hợp lệ 100% tính sau bước tự sửa → che giấu lỗi đầu ra thô, bước tự sửa có thể đổi nghĩa → báo cáo riêng tỷ lệ thô, tỷ lệ sau sửa, và kiểm tra nhãn sau sửa.
- [Nghiêm trọng] Latency là trung bình của 1 request, ngữ cảnh 256 token, đo trên T4 → không đại diện cho RTX 2060, ngữ cảnh 2048 token, 5 người dùng đồng thời → load test trên phần cứng đích (có warm-up, hàng trăm request, đồng thời 5), báo cáo P50/P95/P99 và throughput.
- [Cao] VRAM đo ngay sau khi nạp model → chưa tính KV cache (2048 token × 5 slot), compute buffer và đỉnh lúc chạy → đo VRAM đỉnh khi load test, kèm biên an toàn so với 6 GB.
- [Cao] Kiểm thử an toàn chỉ có 5 câu prompt injection tiếng Anh → không phủ được tấn công tiếng Việt, jailbreak, rò rỉ PII, đầu vào lỗi → bộ red-team hàng trăm ca (tiếng Việt, không dấu, teencode, injection gián tiếp), báo cáo tỷ lệ tấn công thành công (ASR).
- [Cao] Temperature 0.7, chạy 1 lần → kết quả ngẫu nhiên, không tái lập được → dùng greedy (temperature 0) cho phân loại, hoặc chạy nhiều seed và báo cáo phương sai.
- [Trung bình] Nhãn của dữ liệu diễn đạt lại không được kiểm tra; tin gốc có thể chứa PII → nhãn nhiễu, rủi ro lộ dữ liệu → người duyệt mẫu ngẫu nhiên để đo tỷ lệ nhiễu nhãn, ẩn PII trước khi đưa dữ liệu vào teacher.
- [Trung bình] Không kiểm tra độ bền và dữ liệu ngoài phân phối (OOD: không dấu, sai chính tả, tin dài đến 2048 token, tin ngoài 12 ý định) → hỏng khi gặp dữ liệu thật → thêm các bộ test độ bền/OOD và phát hiện ý định ngoài danh sách.
- [Trung bình] Không có tiêu chí phát hành định trước, không so với v1.1, không ghi version dữ liệu/model/seed, không có kế hoạch rollback → kết luận "đạt chuẩn" mang tính chủ quan → chốt trước ngưỡng chấp nhận, so A/B với bản hiện hành, ghi hash dữ liệu/model, chuẩn bị rollback và giám sát drift.
