=== TASK H ===
```python
import hashlib
import re
import unicodedata

REQUIRED_KEYS = ("id", "source_id", "text", "label")
WHITESPACE_RE = re.compile(r"\s+")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:0|\+84)[35789]\d{8}(?!\d)")


def prepare_dataset(records) -> dict:
    if not isinstance(records, list):
        raise TypeError("records must be a list")

    train = []
    val = []
    test = []
    seen_texts = set()

    dropped_invalid = 0
    dropped_duplicate = 0
    pii_replaced = 0

    for rec in records:
        if not isinstance(rec, dict):
            dropped_invalid += 1
            continue

        if not all(k in rec and isinstance(rec[k], str) for k in REQUIRED_KEYS):
            dropped_invalid += 1
            continue

        norm_text = unicodedata.normalize("NFKC", rec["text"])
        norm_text = WHITESPACE_RE.sub(" ", norm_text).strip()
        if not norm_text:
            dropped_invalid += 1
            continue

        masked_text, email_count = EMAIL_RE.subn("<EMAIL>", norm_text)
        masked_text, phone_count = PHONE_RE.subn("<PHONE>", masked_text)

        dedup_key = masked_text.casefold()
        if dedup_key in seen_texts:
            dropped_duplicate += 1
            continue
        seen_texts.add(dedup_key)

        pii_replaced += email_count + phone_count

        clean_rec = {
            "id": rec["id"],
            "source_id": rec["source_id"],
            "text": masked_text,
            "label": rec["label"],
        }

        bucket = int(hashlib.sha256(rec["source_id"].encode("utf-8")).hexdigest(), 16) % 10
        if bucket == 0:
            test.append(clean_rec)
        elif bucket == 1:
            val.append(clean_rec)
        else:
            train.append(clean_rec)

    return {
        "train": train,
        "val": val,
        "test": test,
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
  "per_device_train_batch_size": 16,
  "gradient_accumulation_steps": 2,
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
  "output_dir": "/kaggle/working/qwen2.5-1.5b-intent",
  "save_interval_minutes": 30,
  "resume_from_checkpoint": true,
  "export_format": "GGUF",
  "quant_type": "Q4_K_M",
  "est_gguf_size_gb": 1.0,
  "kv_cache_fp16_gb_at_4096": 0.11,
  "fits_rtx2060_6gb": true,
  "use_golden_test_for_early_stopping": false,
  "full_ft_7b_bf16_on_t4_feasible": false,
  "notes": "GPU T4 (Turing) không hỗ trợ native bf16 và FlashAttention-2 nên dùng fp16 + SDPA. Lưu định kỳ vào /kaggle/working để chống ngắt phiên. Dùng tập val (không dùng Golden Test) cho early stopping. KV cache fp16 ở 4096 token tốn 112MB (~0.11GB), cùng GGUF Q4_K_M (~1GB) chạy tốt trên RTX 2060 6GB."
}
```

=== TASK J ===
```python
import json
import re

FENCE_RE = re.compile(r"```(?:\s*json\b)?(.*?)```", re.IGNORECASE | re.DOTALL)


def _extract_json_str(text: str) -> str:
    match = FENCE_RE.search(text)
    if match is not None:
        return match.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in model output")
    return text[start : end + 1]


def _is_valid_type(value, expected_type) -> bool:
    if expected_type is bool:
        return isinstance(value, bool)
    if expected_type is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type is str:
        return isinstance(value, str)
    return isinstance(value, expected_type)


def _validate_payload(payload, required: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object (dict), got {type(payload).__name__}")

    result = {}
    for field, expected_type in required.items():
        if field not in payload:
            raise ValueError(f"Missing required field '{field}'")
        val = payload[field]
        if not _is_valid_type(val, expected_type):
            raise ValueError(
                f"Invalid type for field '{field}': expected {expected_type.__name__}, got {type(val).__name__}"
            )
        result[field] = val
    return result


def call_structured(client, prompt, required, max_retries=2, fallback=None) -> dict:
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a str")
    if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries must be a non-negative int")

    total_attempts = 1 + max_retries
    current_prompt = prompt
    last_error = "Unknown error"

    for attempt in range(1, total_attempts + 1):
        try:
            raw_output = client.generate(current_prompt, timeout=10.0)
        except (TimeoutError, ConnectionError) as exc:
            last_error = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
            current_prompt = prompt
            continue

        try:
            if not isinstance(raw_output, str):
                raise ValueError(f"Model output must be str, got {type(raw_output).__name__}")
            json_str = _extract_json_str(raw_output)
            parsed = json.loads(json_str)
            clean_data = _validate_payload(parsed, required)
            return {
                "ok": True,
                "data": clean_data,
                "attempts": attempt,
            }
        except Exception as exc:
            last_error = f"Validation/Parse error: {exc}"
            current_prompt = f"{prompt}\n\n{last_error}"

    return {
        "ok": False,
        "data": fallback,
        "attempts": total_attempts,
        "error": last_error,
    }
```

=== TASK K ===
Phần K1.
```json
{
  "p95_ms": 900,
  "accuracy": 0.85,
  "macro_f1": 0.527,
  "raw_schema_validity": 0.94
}
```

Phần K2.
- [NGHIÊM TRỌNG] Rò rỉ dữ liệu (Data Leakage) do sinh paraphrase 3 lần trước rồi mới chia ngẫu nhiên từng dòng 80/10/10 và chỉ khử trùng lặp chính xác → các câu diễn đạt lại của cùng một tin nhắn gốc nằm ở cả tập train, val và test khiến điểm đánh giá cao giả tạo do học vẹt → chia train/val/test theo cụm `source_id` của 5.000 tin gốc TRƯỚC khi paraphrase và bổ sung khử trùng lặp gần đúng (MinHash/embedding).
- [NGHIÊM TRỌNG] Dùng Golden Test để chọn checkpoint tốt nhất (Test Set Leakage) → làm mất tính độc lập của tập kiểm thử cuối và gây overfitting trực tiếp lên Golden Test → chỉ dùng tập `val` để chọn checkpoint/early stopping, khóa kín Golden Test và chỉ chấm một lần duy nhất trước khi phát hành.
- [NGHIÊM TRỌNG] Cỡ mẫu Golden Test quá nhỏ (50 mẫu) và lấy ngẫu nhiên trên dữ liệu 12 lớp mất cân bằng nặng (lớp chính chiếm 87%) → 11 lớp thiểu số chỉ có tổng cộng khoảng 6–7 mẫu (nhiều lớp có 0 mẫu), dẫn đến phương sai thống kê cực lớn và mù thông tin ở các ý định quan trọng → thiết lập Golden Test cố định đủ lớn (≥ 500–1.000 mẫu) lấy mẫu phân tầng (stratified) tối thiểu 30–50 mẫu/lớp do con người gán nhãn.
- [NGHIÊM TRỌNG] Chỉ báo cáo Accuracy (96%) trên tập dữ liệu mất cân bằng (1 lớp chiếm 87%) → che khuất hoàn toàn lỗi phân loại sai ở 11 lớp nghiệp vụ quan trọng còn lại (model đoán toàn lớp đa số đã đạt 87%) → bắt buộc báo cáo Macro-F1, Per-class Precision/Recall/F1 và Confusion Matrix.
- [NGHIÊM TRỌNG] Sai lệch phiên bản đánh giá và triển khai (chấm điểm trên checkpoint `fp16` nhưng phát hành bản lượng tử hóa `GGUF Q4_K_M`) → quá trình nén 4-bit có thể làm tụt F1 các lớp khó và tăng lỗi cú pháp JSON mà không được phát hiện → chạy toàn bộ bài kiểm định chất lượng và an toàn trực tiếp trên bản `GGUF Q4_K_M` qua `llama.cpp`.
- [CAO] Thiên kiến tự chấm (Self-Bias) khi dùng chính `Qwen2.5-72B` (model teacher đã sinh dữ liệu) làm giám khảo chấm phần giải thích → giám khảo thiên vị văn phong và lỗi suy luận của chính nó, làm điểm đánh giá bị thổi phồng → dùng model giám khảo độc lập khác họ hoặc đối chiếu định량 (Cohen's Kappa) với tập mẫu do chuyên gia con người chấm.
- [CAO] Chỉ báo cáo tỷ lệ JSON hợp lệ sau bước tự sửa (100%) mà ẩn tỷ lệ hợp lệ thô (`raw_schema_validity`) → che giấu việc model tuân thủ schema kém, làm tăng độ trễ retry/repair hoặc rủi ro bộ sửa JSON làm sai lệch nội dung → đo và đặt ngưỡng bắt buộc cho cả `raw_schema_validity` trước khi sửa lẫn tỷ lệ sau khi sửa.
- [CAO] Đo latency sai phần cứng, sai tải và sai chỉ số (đo trung bình 1 request đơn lẻ, 256 token trên Kaggle T4 thay vì RTX 2060, 2048 token, 5 người dùng đồng thời) → trung bình 1 mẫu không có ý nghĩa thống kê, bỏ qua độ trễ hàng đợi (queuing) và tail latency khi chạy ngữ cảnh dài nhiều luồng → benchmark trên đúng RTX 2060 6 GB với tải đồng thời 5 CCU, ngữ cảnh tới 2048 token trên hàng trăm request và báo cáo P50/P95/P99 cùng throughput.
- [CAO] Đo VRAM (1,3 GB) ngay khi vừa nạp model ở trạng thái tĩnh → bỏ qua bộ nhớ KV cache và activation buffer tăng vọt khi xử lý 5 request song song ở ngữ cảnh 2048 token, dễ gây tràn VRAM (OOM) trên RTX 2060 6 GB → đo Peak VRAM dưới tải đồng thời tối đa với ngữ cảnh dài nhất.
- [CAO] Kiểm thử an toàn chỉ với 5 câu prompt injection tiếng Anh cho bài toán CSKH tiếng Việt → số lượng mẫu quá ít và lệch ngôn ngữ thực tế, bỏ lọt tấn công tiếng Việt, teencode, trộn ngôn ngữ và rò rỉ PII → xây dựng bộ red-team tiếng Việt + đa ngôn ngữ (≥ 100–200 mẫu bao gồm direct/indirect injection, jailbreak, PII leak) để kiểm thử tự động.
- [TRUNG BÌNH] Cấu hình giải mã `temperature = 0.7` và chỉ chạy 1 lần cho bài toán phân loại xuất JSON → đầu ra ngẫu nhiên, thiếu tính tất định (non-deterministic), dễ phát sinh lỗi JSON và không tái lập được kết quả → đặt `temperature = 0.0` (greedy decoding) kết hợp ép khuôn GBNF/JSON Schema trên `llama.cpp` (hoặc chạy nhiều seed để đo độ lệch chuẩn nếu bắt buộc dùng sampling).
