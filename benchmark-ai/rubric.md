# Thang chấm bài tự luận — Benchmark vai trò AI (chốt TRƯỚC khi chạy model, chấm mù)

> Chốt ngày 12/11/2026, trước khi gửi đề cho bất kỳ model nào.
> Mỗi mục: 1 = nêu đúng vấn đề + cách sửa hợp lý; 0.5 = có nhắc nhưng mơ hồ/sửa sai; 0 = không có.

## Task K2 — Phản biện báo cáo đánh giá model (12 điểm)
K2.1 Rò rỉ do diễn đạt lại: tăng cường dữ liệu TRƯỚC khi chia + chia ngẫu nhiên từng dòng → bản diễn đạt lại của cùng 1 tin gốc nằm ở cả train và test (khử trùng chính xác không bắt được) → chia theo nhóm tin gốc trước khi tăng cường, kiểm tra gần trùng
K2.2 Chọn checkpoint theo điểm trên Golden Test → test bị "nhìn thấy", điểm bị thổi phồng → chọn trên val, test chỉ chấm 1 lần
K2.3 Chấm bản fp16 trong khi triển khai GGUF Q4_K_M → không phản ánh suy giảm do lượng tử hóa → chấm đúng bản triển khai
K2.4 Golden Test 50 mẫu quá nhỏ, không có khoảng tin cậy → kết luận 96% không chắc chắn → tăng cỡ mẫu (theo lớp), báo khoảng tin cậy
K2.5 Lệch lớp (87% một lớp) → accuracy đánh lừa (đoán toàn lớp đa số đã ~87%) → macro-F1, chỉ số theo từng lớp, ma trận nhầm lẫn
K2.6 Teacher (Qwen2.5-72B) đồng thời làm giám khảo → thiên vị tự ưu tiên / cùng điểm mù → giám khảo khác họ model + người chấm kiểm tra mẫu
K2.7 Tỷ lệ JSON hợp lệ tính sau khi tự sửa → che giấu tỷ lệ lỗi thô → báo tỷ lệ thô trước khi sửa (và tỷ lệ sửa được)
K2.8 Latency: dùng trung bình, đo 1 request, không có tải đồng thời → không biết đuôi trễ → P95/P99 với 5 người dùng đồng thời
K2.9 Đo trên Kaggle T4 + ngữ cảnh 256 trong khi triển khai RTX 2060 + ngữ cảnh 2048 → sai phần cứng/điều kiện → đo trên phần cứng đích với ngữ cảnh thật
K2.10 VRAM đo lúc vừa nạp model → bỏ qua KV cache khi ngữ cảnh dài/đồng thời → đo Peak VRAM dưới tải và ngữ cảnh tối đa
K2.11 An toàn: chỉ 5 câu tiếng Anh, chỉ injection trực tiếp → quá ít, sai ngôn ngữ, thiếu injection gián tiếp/jailbreak → bộ test lớn hơn, tiếng Việt, gián tiếp
K2.12 Temperature 0.7 chạy 1 lần → kết quả ngẫu nhiên, không tái lập → cố định cấu hình giải mã/seed hoặc chạy lặp và báo độ lệch

## Trừ điểm
- Thông tin sai sự thật / bịa (hallucination) rõ ràng: −0.5 mỗi lỗi, ghi chú lại.

## Các bài chấm tự động (grade.py)
| Bài | Vai trò | Cách chấm |
|---|---|---|
| H | AI Data Engineer | Test ẩn so với cài đặt mẫu (chuẩn hóa, ẩn PII, khử trùng, chia theo nhóm, thống kê, không mutate) |
| I | SLM Trainer | Kiểm tra từng tiêu chí của JSON (QLoRA fp16 trên T4, không bf16/FA2, checkpoint + resume, GGUF hợp kích thước, KV cache tính đúng, không dùng test để early-stop, …) |
| J | AI Engineer | Test ẩn với client giả (retry đúng loại lỗi, prompt sửa lỗi, trích JSON, kiểm kiểu, fallback, số lần gọi) |
| K1 | MLOps-Eval | 4 con số: P95 nearest-rank, accuracy, macro-F1, tỷ lệ JSON thô |
