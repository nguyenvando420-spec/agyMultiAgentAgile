=== TASK H ===
```python
import hashlib, re, unicodedata

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:0|\+84)[35789]\d{8}(?!\d)")
KEYS = ("id", "source_id", "text", "label")


def prepare_dataset(records):
    if not isinstance(records, list):
        raise TypeError("records must be a list")
    out = {"train": [], "val": [], "test": []}
    st = {"input": len(records), "dropped_invalid": 0, "dropped_duplicate": 0, "pii_replaced": 0}
    seen = set()
    for r in records:
        if not isinstance(r, dict) or any(k not in r or not isinstance(r[k], str) for k in KEYS):
            st["dropped_invalid"] += 1
            continue
        t = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", r["text"])).strip()
        if not t:
            st["dropped_invalid"] += 1
            continue
        t, n1 = EMAIL_RE.subn("<EMAIL>", t)
        t, n2 = PHONE_RE.subn("<PHONE>", t)
        key = t.casefold()
        if key in seen:
            st["dropped_duplicate"] += 1
            continue
        seen.add(key)
        st["pii_replaced"] += n1 + n2
        b = int(hashlib.sha256(r["source_id"].encode("utf-8")).hexdigest(), 16) % 10
        split = "test" if b == 0 else "val" if b == 1 else "train"
        out[split].append({"id": r["id"], "source_id": r["source_id"], "text": t, "label": r["label"]})
    out["stats"] = st
    return out
```
=== TASK I ===
```json
{"method": "qlora", "load_in_4bit": true, "bnb_4bit_quant_type": "nf4", "compute_dtype": "float16",
 "bf16": false, "fp16": true, "attn_implementation": "sdpa", "gradient_checkpointing": true,
 "per_device_train_batch_size": 8, "gradient_accumulation_steps": 4, "max_seq_length": 384,
 "lora_r": 16, "lora_alpha": 32, "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
 "output_dir": "/kaggle/working/ckpt", "save_interval_minutes": 20, "resume_from_checkpoint": true,
 "export_format": "gguf", "quant_type": "Q4_K_M", "est_gguf_size_gb": 0.99,
 "kv_cache_fp16_gb_at_4096": 0.11, "fits_rtx2060_6gb": true,
 "use_golden_test_for_early_stopping": false, "full_ft_7b_bf16_on_t4_feasible": false,
 "notes": "T4 không hỗ trợ bf16."}
```
=== TASK J ===
```python
import json, re


def _extract(text):
    m = re.search(r"```[^\n]*\n(.*?)```", text, re.S)
    if m:
        body = m.group(1)
    else:
        a, b = text.find("{"), text.rfind("}")
        if a == -1 or b < a:
            raise ValueError("không tìm thấy JSON")
        body = text[a:b + 1]
    obj = json.loads(body)
    if not isinstance(obj, dict):
        raise ValueError("JSON không phải object")
    return obj


def _ok_type(v, t):
    if t in (int, float) and isinstance(v, bool):
        return False
    if t is float:
        return isinstance(v, (int, float))
    return isinstance(v, t)


def call_structured(client, prompt, required, max_retries=2, fallback=None):
    if not isinstance(prompt, str):
        raise TypeError("prompt")
    if not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries")
    p, err, n = prompt, "", 0
    for _ in range(1 + max_retries):
        n += 1
        try:
            text = client.generate(p, timeout=10.0)
        except (TimeoutError, ConnectionError) as e:
            err, p = "lỗi mạng: %r" % e, prompt
            continue
        try:
            obj = _extract(text)
            bad = [k for k, t in required.items() if k not in obj or not _ok_type(obj[k], t)]
            if bad:
                raise ValueError("sai/thiếu trường: %s" % ", ".join(bad))
        except ValueError as e:
            err = str(e)
            p = prompt + "\n\n" + "Lỗi: " + err + ". Chỉ trả về JSON hợp lệ."
            continue
        return {"ok": True, "data": {k: obj[k] for k in required}, "attempts": n}
    return {"ok": False, "data": fallback, "attempts": n, "error": err}
```
=== TASK K ===
```json
{"p95_ms": 900, "accuracy": 0.85, "macro_f1": 0.527, "raw_schema_validity": 0.94}
```
- (phần K2 chấm tay)
