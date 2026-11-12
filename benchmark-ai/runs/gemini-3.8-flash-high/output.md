=== TASK H ===

```python
import hashlib
import re
import unicodedata

EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_REGEX = re.compile(r"(?<!\d)(?:0|\+84)[35789]\d{8}(?!\d)")
WHITESPACE_REGEX = re.compile(r"\s+")


def prepare_dataset(records) -> dict:
  if not isinstance(records, list):
    raise TypeError("records must be a list")

  train_set = []
  val_set = []
  test_set = []

  dropped_invalid = 0
  dropped_duplicate = 0
  pii_replaced = 0

  seen_texts = set()
  required_keys = ("id", "source_id", "text", "label")

  for record in records:
    # 2. Kiểm tra dict và 4 trường bắt buộc kiểu str
    if not isinstance(record, dict):
      dropped_invalid += 1
      continue

    if not all(k in record for k in required_keys):
      dropped_invalid += 1
      continue

    if not all(isinstance(record[k], str) for k in required_keys):
      dropped_invalid += 1
      continue

    # 3. Chuẩn hóa NFKC, gộp khoảng trắng liên tiếp và strip
    raw_text = record["text"]
    norm_text = unicodedata.normalize("NFKC", raw_text)
    norm_text = WHITESPACE_REGEX.sub(" ", norm_text).strip()
    if not norm_text:
      dropped_invalid += 1
      continue

    # 4. Ẩn PII theo thứ tự: Email trước, Số điện thoại sau
    masked_text, email_subs = EMAIL_REGEX.subn("<EMAIL>", norm_text)
    masked_text, phone_subs = PHONE_REGEX.subn("<PHONE>", masked_text)
    record_pii_count = email_subs + phone_subs

    # 5. Khử trùng lặp trên văn bản sau ẩn PII (casefold)
    dedup_key = masked_text.casefold()
    if dedup_key in seen_texts:
      dropped_duplicate += 1
      continue
    seen_texts.add(dedup_key)

    # 6. Phân nhóm chống rò rỉ theo source_id
    source_id = record["source_id"]
    bucket = int(hashlib.sha256(source_id.encode("utf-8")).hexdigest(), 16) % 10

    new_record = {
        "id": record["id"],
        "source_id": source_id,
        "text": masked_text,
        "label": record["label"],
    }

    if bucket == 0:
      test_set.append(new_record)
    elif bucket == 1:
      val_set.append(new_record)
    else:
      train_set.append(new_record)

    pii_replaced += record_pii_count

  return {
      "train": train_set,
      "val": val_set,
      "test": test_set,
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
  "output_dir": "/kaggle/working/qwen2.5-1.5b-cskh",
  "save_interval_minutes": 15,
  "resume_from_checkpoint": true,
  "export_format": "gguf",
  "quant_type": "Q4_K_M",
  "est_gguf_size_gb": 1.0,
  "kv_cache_fp16_gb_at_4096": 0.109,
  "fits_rtx2060_6gb": true,
  "use_golden_test_for_early_stopping": false,
  "full_ft_7b_bf16_on_t4_feasible": false,
  "notes": "Dùng QLoRA hoặc LoRA fp16; T4 thiếu phần cứng bf16 và FA2 nên dùng fp16 kèm sdpa. Checkpoint lưu tại /kaggle/working phòng ngắt phiên. Xuất GGUF Q4_K_M, KV cache 4096 (0.109 GB) cùng model (~1 GB) chạy mượt trên RTX 2060 6 GB."
}
```

=== TASK J ===

```python
import json
import re


def _is_valid_type(val, expected_type):
  if expected_type is bool:
    return isinstance(val, bool)
  if expected_type is int:
    return isinstance(val, int) and not isinstance(val, bool)
  if expected_type is float:
    return (isinstance(val, float) or isinstance(val, int)) and not isinstance(
        val, bool
    )
  if expected_type is str:
    return isinstance(val, str)
  return False


def call_structured(
    client, prompt: str, required: dict, max_retries: int = 2, fallback=None
) -> dict:
  if not isinstance(prompt, str):
    raise TypeError("prompt must be a str")
  if type(max_retries) is not int or max_retries < 0:
    raise ValueError("max_retries must be a non-negative int")

  max_attempts = 1 + max_retries
  attempts = 0
  current_prompt = prompt
  last_error = ""

  fence_pattern = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)

  while attempts < max_attempts:
    attempts += 1
    try:
      response_text = client.generate(current_prompt, timeout=10.0)
    except (TimeoutError, ConnectionError) as e:
      last_error = str(e) or type(e).__name__
      current_prompt = prompt  # Gọi lại bằng đúng prompt gốc
      continue

    # Trích xuất chuỗi JSON
    candidate = None
    fence_match = fence_pattern.search(response_text)
    if fence_match:
      candidate = fence_match.group(1).strip()
    else:
      start = response_text.find("{")
      end = response_text.rfind("}")
      if start != -1 and end != -1 and end > start:
        candidate = response_text[start : end + 1]

    if candidate is None:
      last_error = "Could not extract JSON from response"
      current_prompt = f"{prompt}\n\nError: {last_error}"
      continue

    # Parse JSON
    try:
      parsed_json = json.loads(candidate)
    except Exception as e:
      last_error = f"JSON parse error: {e}"
      current_prompt = f"{prompt}\n\nError: {last_error}"
      continue

    if not isinstance(parsed_json, dict):
      last_error = "Parsed JSON is not a dictionary"
      current_prompt = f"{prompt}\n\nError: {last_error}"
      continue

    # Kiểm tra schema theo required
    validation_error = None
    for field_name, expected_type in required.items():
      if field_name not in parsed_json:
        validation_error = f"Missing required field: {field_name}"
        break
      val = parsed_json[field_name]
      if not _is_valid_type(val, expected_type):
        validation_error = (
            f"Field '{field_name}' invalid type. Expected"
            f" {expected_type.__name__}, got {type(val).__name__}"
        )
        break

    if validation_error is not None:
      last_error = validation_error
      current_prompt = f"{prompt}\n\nError: {last_error}"
      continue

    # Thành công
    return {
        "ok": True,
        "data": {k: parsed_json[k] for k in required},
        "attempts": attempts,
    }

  # Hết lượt gọi
  return {
      "ok": False,
      "data": fallback,
      "attempts": attempts,
      "error": last_error,
  }
```

=== TASK K ===

```json
{
  "p95_ms": 900.0,
  "accuracy": 0.85,
  "macro_f1": 0.527,
  "raw_schema_validity": 0.94
}
```

- [Nghiêm trọng] Rò rỉ dữ liệu qua phân chia ngẫu nhiên (Data Leakage): 5.000 tin gốc được sinh thành 20.000 mẫu bằng diễn đạt lại rồi chia ngẫu nhiên 80/10/10 → Các biến thể của cùng một câu gốc xuất hiện ở cả train và test, gây overfit và thổi phồng độ chính xác đánh giá → Phân chia tập theo nhóm nguồn (Group Split theo ID câu gốc) trước khi augment hoặc chia 5.000 tin gốc trước rồi mới augment độc lập từng tập.
- [Nghiêm trọng] Rò rỉ dữ liệu khi chọn checkpoint trên Golden Test (Data Contamination): Chọn checkpoint fp16 tốt nhất dựa trên điểm số của Golden Test → Golden Test bị mất tính khách quan độc lập, model bị overfit vào tập đánh giá → Chỉ dùng tập validation (`val`) để chọn checkpoint và dừng sớm, giữ Golden Test nguyên vẹn cho đánh giá nghiệm thu cuối cùng.
- [Nghiêm trọng] Sai lệch giữa model đánh giá và model triển khai (Train-Serving Discrepancy): Đánh giá trên checkpoint fp16 nhưng phát hành bản lượng tử hóa GGUF Q4_K_M → Bỏ qua hiện tượng suy hao độ chính xác và lỗi suy luận do lượng tử hóa 4-bit gây ra → Đánh giá trực tiếp trên file GGUF Q4_K_M chạy qua runtime llama.cpp.
- [Cao] Kích thước Golden Test quá nhỏ và thiếu đại diện: Chỉ lấy ngẫu nhiên 50 mẫu cho 12 lớp phân loại → Nhiều lớp thiểu số chỉ có 0-2 mẫu, kết quả có phương sai rất lớn và không có ý nghĩa thống kê → Mở rộng Golden Test lên tối thiểu 500–1.000 mẫu và dùng lấy mẫu phân tầng (Stratified Sampling) để đảm bảo mọi lớp đều đủ mẫu kiểm định.
- [Cao] Đánh giá sai lệch trên dữ liệu mất cân bằng nghiêm trọng (Accuracy Paradox): Dùng Accuracy (96%) làm thước đo chính khi lớp đa số chiếm tới 87% → Model chỉ cần đoán toàn bộ về lớp đa số đã đạt 87% accuracy, che giấu việc nhận diện kém ở các lớp thiểu số → Bắt buộc đánh giá bằng Macro-F1, Balanced Accuracy, Precision/Recall từng lớp và Confusion Matrix.
- [Cao] Sai lệch tự thiên vị từ giám khảo LLM (Self-Enhancement Bias): Dùng Qwen2.5-72B chấm phần giải thích của học sinh vốn học từ dữ liệu do chính Qwen2.5-72B sinh ra → Giám khảo thiên vị phong cách và lỗi của chính nó, bỏ qua các lỗi logic hoặc ảo giác ngầm → Dùng chuyên gia con người thẩm định hoặc dùng model giám khảo độc lập từ họ khác (như GPT-4o, Claude 3.5 Sonnet) với rubric chấm điểm chặt chẽ.
- [Cao] Môi trường đo kiểm hiệu năng không tương thích thực tế (Benchmark Mismatch): Đo latency trung bình 180 ms trên 1 request, ngữ cảnh 256 token trên Kaggle T4, trong khi thực tế chạy RTX 2060 6 GB, ngữ cảnh 2048 token với 5 user đồng thời → Bỏ qua độ trễ hàng đợi, KV cache phình to và hiện tượng nghẽn tài nguyên trên phần cứng production yếu hơn → Đo kiểm tải thực tế trên RTX 2060 với 5 concurrency ở ngữ cảnh 2048 token, báo cáo P50/P95/P99 latency và throughput.
- [Cao] Đo dung lượng VRAM sai thời điểm (Incomplete VRAM Profiling): Đo VRAM 1,3 GB ngay sau khi nạp model → Chưa tính bộ nhớ cấp phát cho KV cache (5 user × 2048 token), CUDA context và activation khi suy luận, dễ tràn VRAM (OOM) trên GPU 6 GB → Đo Peak VRAM (bộ nhớ đỉnh) trong điều kiện tải tối đa của hệ thống.
- [Cao] Báo cáo tỷ lệ JSON hợp lệ gây hiểu nhầm: Báo cáo 100% JSON hợp lệ sau khi đã qua bước tự sửa (self-healing) → Che giấu tỷ lệ sinh JSON sai nguyên bản của model, làm tăng latency và rủi ro sửa sai lệch ngữ nghĩa dữ liệu ở production → Báo cáo cả tỷ lệ hợp lệ thô (Raw Validity) và tỷ lệ sau khi sửa kèm chi phí tài nguyên/thời gian tự sửa.
- [Trung bình] Đánh giá an toàn hời hợt và lệch ngôn ngữ: Chỉ thử 5 câu prompt injection bằng tiếng Anh cho chatbot CSKH tiếng Việt → Số lượng mẫu quá ít, không bao quát được tấn công bằng tiếng Việt, jailbreak hay rò rỉ dữ liệu PI → Xây dựng bộ test an toàn tiếng Việt chuẩn hóa (tối thiểu 100+ kịch bản) gồm Prompt Injection, Jailbreak và rò rỉ System Prompt/PII.
- [Trung bình] Tham số giải mã không phù hợp cho tác vụ phân loại: Dùng temperature 0.7 và chỉ chạy 1 lần cho phân loại nhãn → Khiến kết quả đầu ra ngẫu nhiên, không thể tái lập và tăng tỷ lệ lỗi định dạng JSON → Đặt temperature = 0.0 (greedy decoding) cho tác vụ phân loại hoặc chạy lặp lại nhiều lần để đo độ lệch chuẩn.
