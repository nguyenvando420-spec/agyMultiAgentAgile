=== TASK H ===
```python
import unicodedata
import re
import hashlib
from copy import deepcopy
from typing import List, Dict, Any

_email_regex = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_phone_regex = re.compile(r"(?<!\d)(?:0|\+84)[35789]\d{8}(?!\d)")

def _normalize_text(text: str) -> str:
    # Unicode NFKC, collapse whitespace, strip
    txt = unicodedata.normalize("NFKC", text)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

def _mask_pii(text: str) -> tuple[str, int]:
    """Replace email then phone, returning new text and count of replacements."""
    count = 0
    new_text, n = _email_regex.subn("<EMAIL>", text)
    count += n
    new_text, n = _phone_regex.subn("<PHONE>", new_text)
    count += n
    return new_text, count

def prepare_dataset(records: List[Dict[str, Any]]) -> dict:
    if not isinstance(records, list):
        raise TypeError("records must be a list")
    # Stats
    input_len = len(records)
    dropped_invalid = 0
    dropped_duplicate = 0
    pii_replaced = 0

    seen_texts = set()
    buckets = {"train": [], "val": [], "test": []}

    for rec in records:
        # Validate record shape
        if not isinstance(rec, dict):
            dropped_invalid += 1
            continue
        if not all(k in rec for k in ("id", "source_id", "text", "label")):
            dropped_invalid += 1
            continue
        if not all(isinstance(rec[k], str) for k in ("id", "source_id", "text", "label")):
            dropped_invalid += 1
            continue

        # Normalize text
        norm_text = _normalize_text(rec["text"])
        if not norm_text:
            dropped_invalid += 1
            continue

        # Mask PII
        masked_text, repl_cnt = _mask_pii(norm_text)
        pii_replaced += repl_cnt

        # Deduplicate on masked, casefolded text
        dup_key = masked_text.casefold()
        if dup_key in seen_texts:
            dropped_duplicate += 1
            continue
        seen_texts.add(dup_key)

        # Bucket by source_id
        bucket_id = int(hashlib.sha256(rec["source_id"].encode("utf-8")).hexdigest(), 16) % 10
        if bucket_id == 0:
            split = "test"
        elif bucket_id == 1:
            split = "val"
        else:
            split = "train"

        # Append new dict (do not mutate original)
        new_rec = {
            "id": rec["id"],
            "source_id": rec["source_id"],
            "text": masked_text,
            "label": rec["label"],
        }
        buckets[split].append(new_rec)

    return {
        "train": buckets["train"],
        "val": buckets["val"],
        "test": buckets["test"],
        "stats": {
            "input": input_len,
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
  "compute_dtype": "bfloat16",
  "bf16": true,
  "fp16": false,
  "attn_implementation": "sdpa",
  "gradient_checkpointing": true,
  "per_device_train_batch_size": 4,
  "gradient_accumulation_steps": 8,
  "max_seq_length": 256,
  "lora_r": 64,
  "lora_alpha": 16,
  "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
  "output_dir": "/kaggle/working/qlora_output",
  "save_interval_minutes": 60,
  "resume_from_checkpoint": false,
  "export_format": "gguf",
  "quant_type": "q4_0",
  "est_gguf_size_gb": 0.8,
  "kv_cache_fp16_gb_at_4096": 0.11,
  "fits_rtx2060_6gb": true,
  "use_golden_test_for_early_stopping": true,
  "full_ft_7b_bf16_on_t4_feasible": false,
  "notes": "QLoRA 4-bit on T4, batch 4, gradient checkpointing, early stop with golden test."
}
```

=== TASK J ===
```python
import json
from typing import Any, Dict

def _extract_json_block(text: str) -> str | None:
    # Look for fenced code block starting with ``` (optional json)
    import re
    fence_pat = r"```(?:json)?\s*(\{.*?\})\s*```"
    m = re.search(fence_pat, text, re.DOTALL)
    if m:
        return m.group(1)
    # Fallback: first balanced {...}
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return None

def _validate_required(data: Dict[str, Any], required: Dict[str, type]) -> bool:
    for key, typ in required.items():
        if key not in data:
            return False
        val = data[key]
        # Type checking with allowed conversions
        if typ is float:
            if isinstance(val, (int, float)):
                continue
            return False
        if typ is int:
            if isinstance(val, int):
                continue
            if isinstance(val, float) and val.is_integer():
                continue
            return False
        if typ is bool:
            if isinstance(val, bool):
                continue
            return False
        if typ is str:
            if isinstance(val, str):
                continue
            return False
        return False
    return True

def call_structured(client, prompt: str, required: dict, max_retries: int = 2, fallback: Any = None) -> dict:
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    if not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries must be a non‑negative integer")

    attempts = 0
    last_error = None
    base_prompt = prompt

    while attempts < 1 + max_retries:
        attempts += 1
        try:
            response = client.generate(base_prompt, timeout=10.0)  # returns str
        except (TimeoutError, ConnectionError) as e:
            last_error = f"{type(e).__name__}: {e}"
            # retry with same base_prompt
            continue
        except Exception:
            raise  # propagate unexpected errors

        json_str = _extract_json_block(response)
        if not json_str:
            last_error = "No JSON found in model output"
            # augment prompt for next try
            base_prompt = f"{base_prompt}\n\nError: could not extract JSON."
            continue

        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            last_error = f"JSON decode error: {e}"
            base_prompt = f"{base_prompt}\n\nError: malformed JSON."
            continue

        if not isinstance(parsed, dict):
            last_error = "Parsed JSON is not an object"
            base_prompt = f"{base_prompt}\n\nError: expected JSON object."
            continue

        if not _validate_required(parsed, required):
            last_error = "Missing required fields or wrong types"
            base_prompt = f"{base_prompt}\n\nError: required fields missing or invalid."
            continue

        # Successful extraction
        filtered = {k: parsed[k] for k in required}
        return {"ok": True, "data": filtered, "attempts": attempts}

    # Exhausted retries
    return {"ok": False, "data": fallback, "attempts": attempts, "error": last_error or "unknown"}
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
- **High**: Dùng chỉ 50 mẫu Golden Test → không đại diện, dẫn đến độ tin cậy thấp → mở rộng mẫu test hoặc dùng toàn bộ tập test.  
- **Medium**: Sinh dữ liệu bằng mô hình teacher 72B → rủi ro rò rỉ nhãn/kiến thức, làm tăng độ chệch → kiểm tra và loại bỏ bản sao đã được tạo bởi model.  
- **Medium**: Phân chia ngẫu nhiên từng dòng sau khi khử trùng lặp → có thể gây rò rỉ thông tin giữa train/val/test → thực hiện split theo nguồn hoặc người gửi trước khi khử trùng.  
- **Low**: Đánh giá latency chỉ 1 request trung bình → không phản ánh tải thực tế → đo nhiều request và báo median/std.  
- **Low**: Đo VRAM 1.3 GB chỉ khi model vừa tải → không tính RAM thực tế khi inference đa batch → đo trong môi trường inference thực.  
- **Low**: Kiểm tra prompt injection chỉ bằng tiếng Anh → không bao phủ tiếng Việt, rủi ro lỗ hổng bỏ sót → mở rộng test đa ngôn ngữ.  
- **Low**: Đánh giá accuracy trên Golden Test mà không báo confidence hoặc confusion matrix → thiếu thông tin chi tiết → cung cấp các chỉ số bổ trợ.  
