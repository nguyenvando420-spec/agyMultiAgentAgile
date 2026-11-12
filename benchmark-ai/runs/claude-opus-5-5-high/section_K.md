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