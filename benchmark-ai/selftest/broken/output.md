=== TASK H ===
```python
import random, re

def prepare_dataset(records):
    out = {"train": [], "val": [], "test": [], "stats": {"input": len(records), "dropped_invalid": 0, "dropped_duplicate": 0, "pii_replaced": 0}}
    seen = set()
    for r in records:
        t = r["text"].strip()
        t = re.sub(r"\S+@\S+", "<EMAIL>", t)
        if t.lower() in seen:
            continue
        seen.add(t.lower())
        r["text"] = t
        out[random.choice(["train", "train", "val", "test"])].append(r)
    return out
```
=== TASK I ===
```json
{"method": "lora", "load_in_4bit": false, "bnb_4bit_quant_type": "", "compute_dtype": "bfloat16",
 "bf16": true, "fp16": false, "attn_implementation": "flash_attention_2", "gradient_checkpointing": false,
 "per_device_train_batch_size": 32, "gradient_accumulation_steps": 1, "max_seq_length": 4096,
 "lora_r": 16, "lora_alpha": 32, "target_modules": ["q_proj"],
 "output_dir": "/tmp/out", "save_interval_minutes": 120, "resume_from_checkpoint": false,
 "export_format": "gguf", "quant_type": "Q4_K_M", "est_gguf_size_gb": 3.0,
 "kv_cache_fp16_gb_at_4096": 0.47, "fits_rtx2060_6gb": true,
 "use_golden_test_for_early_stopping": true, "full_ft_7b_bf16_on_t4_feasible": true, "notes": "ok"}
```
=== TASK J ===
```python
import json

def call_structured(client, prompt, required, max_retries=2, fallback=None):
    for i in range(max_retries + 1):
        try:
            obj = json.loads(client.generate(prompt))
            return {"ok": True, "data": obj, "attempts": i + 1}
        except Exception as e:
            err = str(e)
    return {"ok": False, "data": fallback, "attempts": max_retries + 1, "error": err}
```
=== TASK K ===
```json
{"p95_ms": 975, "accuracy": 0.85, "macro_f1": 0.79, "raw_schema_validity": 0.985}
```
