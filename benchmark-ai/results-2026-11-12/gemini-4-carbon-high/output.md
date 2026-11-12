=== TASK H ===
```python
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

_REQUIRED_KEYS = ("id", "source_id", "text", "label")
_WHITESPACE_RE = re.compile(r"\s+")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:0|\+84)[35789]\d{8}(?!\d)")


def prepare_dataset(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(records, list):
        raise TypeError("records must be a list")

    splits: dict[str, list[dict[str, str]]] = {
        "train": [],
        "val": [],
        "test": [],
    }
    seen_keys: set[str] = set()

    dropped_invalid = 0
    dropped_duplicate = 0
    pii_replaced = 0

    for record in records:
        if not isinstance(record, dict) or not all(
            key in record and isinstance(record[key], str) for key in _REQUIRED_KEYS
        ):
            dropped_invalid += 1
            continue

        normalized_text = unicodedata.normalize("NFKC", record["text"])
        normalized_text = _WHITESPACE_RE.sub(" ", normalized_text).strip()
        if not normalized_text:
            dropped_invalid += 1
            continue

        masked_text, email_count = _EMAIL_RE.subn("<EMAIL>", normalized_text)
        masked_text, phone_count = _PHONE_RE.subn("<PHONE>", masked_text)

        dedup_key = masked_text.casefold()
        if dedup_key in seen_keys:
            dropped_duplicate += 1
            continue
        seen_keys.add(dedup_key)

        pii_replaced += email_count + phone_count

        source_id = record["source_id"]
        bucket = int(hashlib.sha256(source_id.encode("utf-8")).hexdigest(), 16) % 10
        if bucket == 0:
            target_split = "test"
        elif bucket == 1:
            target_split = "val"
        else:
            target_split = "train"

        splits[target_split].append(
            {
                "id": record["id"],
                "source_id": source_id,
                "text": masked_text,
                "label": record["label"],
            }
        )

    return {
        "train": splits["train"],
        "val": splits["val"],
        "test": splits["test"],
        "stats": {
            "input": len(records),
            "dropped_invalid": dropped_invalid,
            "dropped_duplicate": dropped_duplicate,
            "pii_replaced": pii_replaced,
        },
    }
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
  "per_device_train_batch_size": 8,
  "gradient_accumulation_steps": 4,
  "max_seq_length": 256,
  "lora_r": 16,
  "lora_alpha": 32,
  "target_modules": [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj"
  ],
  "output_dir": "/kaggle/working/checkpoints",
  "save_interval_minutes": 15,
  "resume_from_checkpoint": true,
  "export_format": "gguf",
  "quant_type": "Q4_K_M",
  "est_gguf_size_gb": 1.05,
  "kv_cache_fp16_gb_at_4096": 0.11,
  "fits_rtx2060_6gb": true,
  "use_golden_test_for_early_stopping": false,
  "full_ft_7b_bf16_on_t4_feasible": false,
  "notes": "T4 không hỗ trợ native bf16 hay FlashAttention2 nên dùng QLoRA NF4 với fp16 và SDPA. Lưu định kỳ tại /kaggle/working để resume khi ngắt phiên. Merge base FP16 rồi lượng tử GGUF Q4_K_M. Early stopping chỉ dùng tập val."
}
```

=== TASK J ===
```python
from __future__ import annotations

import json
import re
from typing import Any

_FENCE_RE = re.compile(
    r"```(?:[ \t]*json(?![A-Za-z0-9_]))?(.*?)```",
    re.IGNORECASE | re.DOTALL,
)


def _extract_json_str(raw: str) -> str:
    fence_match = _FENCE_RE.search(raw)
    if fence_match is not None:
        return fence_match.group(1).strip()

    first_brace = raw.find("{")
    last_brace = raw.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
        raise ValueError("No JSON object or code fence found in response.")
    return raw[first_brace : last_brace + 1]


def _matches_type(value: Any, expected_type: type) -> bool:
    if expected_type is bool:
        return isinstance(value, bool)
    if expected_type is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type is str:
        return isinstance(value, str)
    return False


def _validate_payload(payload: Any, required: dict[str, type]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object (dict), got {type(payload).__name__}.")

    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}.")

    invalid_types: list[str] = []
    for field, expected_type in required.items():
        val = payload[field]
        if not _matches_type(val, expected_type):
            invalid_types.append(
                f"field '{field}' expected {expected_type.__name__}, got {type(val).__name__}"
            )
    if invalid_types:
        raise ValueError("Invalid field type(s): " + "; ".join(invalid_types) + ".")

    return {field: payload[field] for field in required}


def call_structured(
    client: Any,
    prompt: str,
    required: dict[str, type],
    max_retries: int = 2,
    fallback: Any = None,
) -> dict[str, Any]:
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a str.")
    if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries must be a non-negative int.")

    max_attempts = 1 + max_retries
    current_prompt = prompt
    last_error = ""

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.generate(current_prompt, timeout=10.0)
        except (TimeoutError, ConnectionError) as exc:
            last_error = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
            current_prompt = prompt
            continue

        if not isinstance(response, str):
            last_error = (
                f"Expected str response from client.generate, got {type(response).__name__}."
            )
            current_prompt = f"{prompt}\n\nValidation error: {last_error}"
            continue

        try:
            json_text = _extract_json_str(response)
            parsed = json.loads(json_text)
            validated = _validate_payload(parsed, required)
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = f"{type(exc).__name__}: {exc}" if str(exc) else "Invalid JSON output."
            current_prompt = f"{prompt}\n\nValidation error: {last_error}"
            continue

        return {
            "ok": True,
            "data": validated,
            "attempts": attempt,
        }

    return {
        "ok": False,
        "data": fallback,
        "attempts": max_attempts,
        "error": last_error,
    }
```

=== TASK K ===
```json
{
  "p95_ms": 900,
  "accuracy": 0.85,
  "macro_f1": 0.527,
  "raw_schema_validity": 0.94
}
```

- [Nghiêm trọng] Sinh 3 bản diễn đạt lại cho mỗi tin gốc rồi mới chia ngẫu nhiên từng dòng 80/10/10 → các biến thể cùng một tin gốc nằm ở cả train, val và test gây rò rỉ dữ liệu (data leakage), làm điểm đánh giá cao giả tạo → Chia tập theo nhóm `source_id` của 5.000 tin gốc trước, sau đó chỉ sinh dữ liệu tổng hợp trên tập train.
- [Cao] Tập test/Golden Test chứa tới ~75% mẫu do Qwen2.5-72B sinh ra và chỉ khử trùng lặp chính xác (exact match) → không loại được các tin gần trùng ngữ nghĩa (near-duplicates) và chấm điểm trên phân phối nhân tạo thay vì ngôn ngữ khách hàng thật → Áp dụng near-deduplication (MinHash/embedding) và xây dựng tập val/Golden Test 100% từ tin nhắn CSKH thực tế được gán nhãn chuẩn bởi người.
- [Nghiêm trọng] Golden Test chỉ lấy ngẫu nhiên 50 mẫu không phân tầng cho bài toán 12 lớp mất cân bằng nặng → sai số thống kê rất lớn và nhiều lớp thiểu số có 0 mẫu trong tập chấm → Tăng quy mô Golden Test (ví dụ ≥ 1.000 mẫu) và lấy mẫu phân tầng (stratified) đảm bảo đủ số lượng mẫu tối thiểu cho mỗi lớp.
- [Nghiêm trọng] Chỉ dùng Accuracy (96%) khi lớp đa số chiếm tới 87% lưu lượng thực tế → che khuất hoàn toàn khả năng model đoán sai hoặc bỏ sót 11 lớp thiểu số quan trọng (khiếu nại, hủy đơn, sự cố) → Bắt buộc đo Macro-F1, Precision/Recall/F1 từng lớp và ma trận nhầm lẫn (Confusion Matrix).
- [Nghiêm trọng] Chọn checkpoint tốt nhất dựa trực tiếp trên điểm Golden Test → rò rỉ tập kiểm định vào bước chọn mô hình (selection bias/overfitting lên 50 mẫu test), làm mất tính khách quan của cổng nghiệm thu → Chỉ dùng tập `val` cho early stopping và chọn checkpoint, giữ Golden Test độc lập chỉ chấm một lần trước phát hành.
- [Nghiêm trọng] Chấm điểm trên bản FP16 nhưng triển khai thực tế bản lượng tử hóa `GGUF Q4_K_M` → không phát hiện được suy giảm độ chính xác, lệch chat template/tokenizer hoặc tăng lỗi JSON do nén 4-bit và khác engine suy luận → Chạy toàn bộ bài kiểm định chất lượng, schema và an toàn trực tiếp trên file `GGUF Q4_K_M` chạy qua `llama.cpp`.
- [Cao] Dùng cùng Qwen2.5-72B vừa làm teacher sinh dữ liệu vừa làm giám khảo chấm phần giải thích → thiên kiến tự ưa thích văn phong của chính mình (self-preference/circular bias) và không phát hiện được ảo giác sai nghiệp vụ → Dùng giám khảo độc lập khác họ model kèm rubric chặt chẽ và hiệu chuẩn độ đồng thuận (Cohen's Kappa) với tập chấm tay của chuyên gia.
- [Cao] Báo cáo tỷ lệ JSON hợp lệ 100% sau bước tự sửa JSON mà ẩn tỷ lệ hợp lệ thô → che giấu lỗi cú pháp thực của model, tăng độ trễ xử lý và có nguy cơ bộ sửa cơ học làm biến dạng giá trị trường/nhãn → Đo riêng `raw_schema_validity` trước khi sửa, kiểm tra chặt JSON Schema cùng danh mục 12 nhãn hợp lệ và bật grammar constraint trong `llama.cpp`.
- [Nghiêm trọng] Đo hiệu năng trên Kaggle T4 ở ngữ cảnh 256 token với 1 request đơn lẻ trong khi Production dùng RTX 2060 6 GB, ngữ cảnh 2048 token và 5 người dùng đồng thời → sai lệch hoàn toàn về năng lực phần cứng, chi phí prefill ngữ cảnh dài và độ trễ xếp hàng khi chạy song song → Benchmark trực tiếp trên RTX 2060 6 GB với `llama.cpp` ở tải thực 5 kết nối đồng thời và ngữ cảnh lên tới 2048 token.
- [Cao] Đo latency trên đúng 1 request và gọi là "trung bình 180 ms" → cỡ mẫu N=1 vô nghĩa thống kê và giá trị trung bình che giấu độ trễ đuôi (tail latency) gây nghẽn trải nghiệm khách hàng → Chạy bước warm-up rồi đo trên hàng trăm–nghìn request để báo cáo P50, P95, P99, TTFT và throughput.
- [Nghiêm trọng] Chỉ đo VRAM (1,3 GB) ngay sau khi nạp model ở trạng thái nghỉ → bỏ qua dung lượng KV cache cho 5 phiên đồng thời × 2048 token, compute buffers và VRAM hệ điều hành, dẫn tới nguy cơ tràn bộ nhớ (OOM) khi chịu tải thật trên thẻ 6 GB → Đo Peak VRAM dưới tải đồng thời tối đa (5 slots × 2048 tokens) chạy liên tục.
- [Cao] Kiểm thử an toàn chỉ với 5 câu prompt injection tiếng Anh cho hệ thống CSKH tiếng Việt → cỡ mẫu quá nhỏ và bỏ lọt tấn công tiếng Việt, không dấu/teencode, trộn ngôn ngữ, rò rỉ PII hoặc ép xuất sai JSON → Xây dựng bộ Red-Teaming tiếng Việt và đa ngữ hàng trăm mẫu bao phủ prompt injection, jailbreak, PII leak và tấn công cấu trúc đầu ra.
- [Trung bình] Đặt `temperature = 0.7` và chỉ chạy đánh giá 1 lần cho tác vụ phân loại có cấu trúc → đầu ra ngẫu nhiên thiếu ổn định giữa các lần gọi, tăng nguy cơ lỗi JSON và kết quả trên 50 mẫu dao động may rủi → Chuyển sang giải mã tất định (`temperature = 0`) cho tác vụ phân loại xuất JSON và kiểm chứng tính tái lập.
