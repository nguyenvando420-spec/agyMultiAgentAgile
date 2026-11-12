KHÔNG sử dụng bất kỳ công cụ nào (không đọc/ghi file, không chạy lệnh, không tìm web). Trả lời TOÀN BỘ trong MỘT câu trả lời duy nhất.
Phần văn xuôi viết bằng tiếng Việt, ngắn gọn dạng gạch đầu dòng. Mỗi phần BẮT ĐẦU bằng đúng một dòng tiêu đề dạng `=== TASK X ===` (X là H, I, J, K) và theo đúng thứ tự.

=== ĐỀ TASK H (AI Data Engineer - chuẩn bị dataset) ===
Viết module Python `prepare.py` với hàm `prepare_dataset(records) -> dict`. Đặc tả CHÍNH XÁC:
1. Nếu `records` không phải `list` → raise `TypeError`. KHÔNG được sửa đổi (mutate) danh sách đầu vào hay các dict bên trong.
2. Mỗi bản ghi hợp lệ là một `dict` có đủ 4 khóa `id`, `source_id`, `text`, `label`, cả 4 giá trị đều là `str`. Bản ghi không phải dict, thiếu khóa, hoặc có giá trị không phải `str` → BỎ QUA và đếm vào `dropped_invalid`.
3. Chuẩn hóa `text`: `unicodedata.normalize("NFKC", text)`, sau đó thay mọi chuỗi ký tự khoảng trắng liên tiếp (theo `\s` của regex Python) bằng MỘT dấu cách, rồi `strip()`. Nếu rỗng sau chuẩn hóa → bỏ qua, đếm vào `dropped_invalid`.
4. Ẩn PII trên văn bản ĐÃ chuẩn hóa, theo đúng thứ tự: (a) email khớp regex `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` → thay bằng `<EMAIL>`; (b) sau đó số điện thoại khớp regex `(?<!\d)(?:0|\+84)[35789]\d{8}(?!\d)` → thay bằng `<PHONE>`.
5. Khử trùng lặp: khóa trùng = văn bản SAU khi ẩn PII, đem `casefold()`. Giữ bản ghi xuất hiện ĐẦU TIÊN theo thứ tự đầu vào; các bản sau bị bỏ và đếm vào `dropped_duplicate`. Trùng lặp xét trên TOÀN bộ dữ liệu, bất kể `source_id`.
6. Chia tập theo nhóm nguồn (chống rò rỉ): `bucket = int(hashlib.sha256(source_id.encode("utf-8")).hexdigest(), 16) % 10`; `bucket == 0` → `"test"`, `bucket == 1` → `"val"`, còn lại → `"train"`.
7. Trả về `{"train": [...], "val": [...], "test": [...], "stats": {"input": int, "dropped_invalid": int, "dropped_duplicate": int, "pii_replaced": int}}`. Mỗi phần tử trong các tập là dict MỚI `{"id", "source_id", "text", "label"}` với `text` là văn bản đã chuẩn hóa + ẩn PII; giữ thứ tự đầu vào trong từng tập. `input` = `len(records)`. `pii_replaced` = tổng số lần thay thế (email + điện thoại) chỉ tính trên các bản ghi được GIỮ LẠI trong kết quả.
Chỉ đưa ra code trong một khối ```python.

=== ĐỀ TASK I (SLM Trainer - kế hoạch huấn luyện trên phần cứng giới hạn) ===
Bối cảnh: Phân loại ý định tin nhắn CSKH tiếng Việt, 12 lớp, 40.000 mẫu train, mỗi mẫu (prompt + nhãn JSON) ≤ 256 token. Tech Lead đã chốt base model `Qwen2.5-1.5B-Instruct` (1,54 tỷ tham số; 28 layer; 2 KV head; head_dim 128). Huấn luyện trên Kaggle Notebook GPU T4 16 GB (phiên tối đa 12 giờ, có thể bị ngắt, chỉ thư mục `/kaggle/working` được giữ lại). Model cuối chạy bằng llama.cpp trên RTX 2060 6 GB, ngữ cảnh tối đa 4096 token.
Chỉ trả về MỘT khối ```json hợp lệ (không chú thích trong JSON), đúng các khóa sau:
{"method": "qlora"|"lora"|"full", "load_in_4bit": bool, "bnb_4bit_quant_type": string, "compute_dtype": "float16"|"bfloat16"|"float32",
 "bf16": bool, "fp16": bool, "attn_implementation": "sdpa"|"eager"|"flash_attention_2", "gradient_checkpointing": bool,
 "per_device_train_batch_size": int, "gradient_accumulation_steps": int, "max_seq_length": int,
 "lora_r": int, "lora_alpha": int, "target_modules": [string, ...],
 "output_dir": string, "save_interval_minutes": number, "resume_from_checkpoint": bool,
 "export_format": string, "quant_type": string, "est_gguf_size_gb": number,
 "kv_cache_fp16_gb_at_4096": number, "fits_rtx2060_6gb": bool,
 "use_golden_test_for_early_stopping": bool, "full_ft_7b_bf16_on_t4_feasible": bool,
 "notes": string (tối đa 60 từ)}
`kv_cache_fp16_gb_at_4096` là dung lượng KV cache (fp16, batch 1) ở ngữ cảnh 4096 token, tính theo thông số kiến trúc đã cho.

=== ĐỀ TASK J (AI Engineer - gọi model có cấu trúc, retry, fallback) ===
Viết module Python `structured.py` với hàm `call_structured(client, prompt, required, max_retries=2, fallback=None) -> dict`. Đặc tả CHÍNH XÁC:
1. `prompt` không phải `str` → `TypeError`. `max_retries` không phải `int` hoặc < 0 → `ValueError`. Kiểm tra trước khi gọi model.
2. Gọi model bằng `client.generate(p, timeout=10.0)` (luôn truyền `timeout=10.0` dạng keyword), trả về `str`. Tổng số lần gọi tối đa = `1 + max_retries`. Không gọi `time.sleep`.
3. Nếu `generate` raise `TimeoutError` hoặc `ConnectionError` → tính là một lần thất bại, lần gọi kế tiếp dùng LẠI ĐÚNG `prompt` gốc. Mọi exception khác → để lan ra ngoài ngay (không bắt, không retry).
4. Trích JSON từ chuỗi trả về: nếu có khối rào ``` (có hoặc không có chữ `json` sau dấu rào) thì lấy nội dung của khối rào ĐẦU TIÊN; nếu không có khối rào thì lấy chuỗi con từ ký tự `{` đầu tiên đến ký tự `}` cuối cùng. Parse bằng `json.loads`; kết quả phải là `dict`.
5. `required` là dict `tên_trường -> kiểu` với kiểu thuộc {`str`, `int`, `float`, `bool`}. Hợp lệ khi đủ mọi trường và đúng kiểu, với quy tắc: `bool` KHÔNG được chấp nhận cho `int`/`float`; `int` ĐƯỢC chấp nhận cho `float`.
6. Nếu chuỗi trả về không trích/parse được hoặc không hợp lệ theo `required` → lần thất bại; lần gọi kế tiếp dùng prompt = prompt gốc + `"\n\n"` + một thông báo lỗi ngắn mô tả vì sao không hợp lệ (prompt mới phải BẮT ĐẦU bằng prompt gốc và khác prompt gốc).
7. Thành công → trả `{"ok": True, "data": <dict chỉ gồm các trường trong required>, "attempts": <số lần đã gọi>}`. Hết lượt → trả `{"ok": False, "data": fallback, "attempts": <số lần đã gọi>, "error": <chuỗi mô tả lỗi cuối cùng>}`.
Chỉ đưa ra code trong một khối ```python.

=== ĐỀ TASK K (MLOps-Eval - tính chỉ số & phản biện báo cáo đánh giá) ===
Phần K1. Chỉ trả về MỘT khối ```json gồm đúng 4 khóa `{"p95_ms": number, "accuracy": number, "macro_f1": number, "raw_schema_validity": number}` (số thập phân làm tròn 3 chữ số), tính từ dữ liệu sau:
- Latency (ms) của 20 request: 120, 95, 130, 110, 105, 2400, 140, 98, 101, 115, 125, 99, 160, 108, 112, 900, 118, 103, 97, 135. Tính P95 theo phương pháp **nearest-rank** (hạng = ceil(0.95 × N), đánh số từ 1 trên dãy đã sắp tăng dần).
- Phân loại 20 mẫu, 3 lớp A/B/C. Nhãn đúng: 16 mẫu A, 2 mẫu B, 2 mẫu C. Dự đoán: cả 16 mẫu A đều đoán A; 2 mẫu B: 1 đoán B, 1 đoán A; 2 mẫu C: cả 2 đoán A. Tính accuracy và macro-F1 (trung bình không trọng số F1 của 3 lớp; precision/recall chia cho 0 thì lấy 0).
- Có 200 đầu ra; 188 đầu ra đúng JSON Schema ngay từ đầu; thêm 9 đầu ra hợp lệ sau bước tự sửa JSON. `raw_schema_validity` = tỷ lệ hợp lệ của đầu ra thô (trước khi tự sửa).

Phần K2. Dưới đây là báo cáo đánh giá của một team. Liệt kê TẤT CẢ lỗi phương pháp/rủi ro khiến kết luận không đáng tin, mỗi lỗi 1 dòng: [mức độ] vấn đề → hậu quả → cách sửa. Không cần khen.
```
Báo cáo đánh giá model phân loại ý định CSKH v1.2 — đề xuất phát hành
- Dữ liệu: 5.000 tin nhắn gốc. Dùng Qwen2.5-72B (teacher) diễn đạt lại mỗi tin 3 lần → 20.000 mẫu.
  Khử trùng lặp chính xác, rồi chia ngẫu nhiên từng dòng 80/10/10 (train/val/test).
- Golden Test: lấy ngẫu nhiên 50 mẫu từ tập test để chấm cho nhanh.
- Kết quả: Accuracy 96% trên Golden Test. (Thống kê thực tế: 87% tin nhắn thuộc lớp "hỏi thông tin chung".)
- Model được chấm: checkpoint fp16 tốt nhất, chọn theo điểm trên Golden Test. Bản sẽ triển khai: GGUF Q4_K_M.
- Phần giải thích lý do của model được chấm bởi Qwen2.5-72B làm giám khảo.
- Tỷ lệ JSON hợp lệ: 100% (tính sau bước tự sửa JSON).
- Hiệu năng: latency trung bình 180 ms, đo 1 request, ngữ cảnh 256 token, trên Kaggle T4.
  (Production: RTX 2060 6 GB, ngữ cảnh đến 2048 token, 5 người dùng đồng thời.)
- VRAM: 1,3 GB, đo ngay sau khi nạp model.
- An toàn: thử 5 câu prompt injection tiếng Anh, chặn được 5/5.
- Giải mã: temperature 0.7, chạy 1 lần.
- Kết luận: Đạt chuẩn phát hành.
```
