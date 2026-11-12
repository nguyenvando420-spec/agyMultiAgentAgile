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