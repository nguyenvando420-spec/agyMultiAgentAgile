**K1**
```json
{"p95_ms": 900.0, "accuracy": 0.85, "macro_f1": 0.527, "raw_schema_validity": 0.94}
```
- P95: N=20, hạng = ceil(19) = 19, nên giá trị thứ 19 trong dãy sắp tăng là 900 ms.
- Accuracy = 17/20 = 0.85.
- F1 của A = 32/35 ≈ 0.914.
- F1 của B = 2/3 ≈ 0.667.
- F1 của C = 0.
- Macro-F1 = (0.914 + 0.667 + 0) / 3 ≈ 0.527.
- Raw validity = 188/200 = 0.94. Con số 197/200 tính cả bước tự sửa nên không dùng.

**K2 – Các lỗi phương pháp/rủi ro**
- [Nghiêm trọng] Chia ngẫu nhiên từng dòng trong khi mỗi tin gốc có 3 bản diễn đạt lại → rò rỉ train/test, điểm bị thổi phồng → chia theo nhóm `source_id` của tin gốc (group split).
- [Nghiêm trọng] Chọn checkpoint theo điểm Golden Test rồi báo cáo luôn điểm đó → lạc quan do chọn lọc, test không còn độc lập → chọn checkpoint trên val, giữ một test set khóa chặt, chỉ chấm một lần.
- [Nghiêm trọng] 96% accuracy trong khi lớp đa số chiếm 87% (baseline đoán lớp đa số đạt 87%) → accuracy không phản ánh chất lượng, lớp hiếm bị che khuất → báo macro-F1, precision/recall từng lớp, ma trận nhầm lẫn, so với baseline.
- [Nghiêm trọng] Chấm model fp16 nhưng triển khai GGUF Q4_K_M → chất lượng thật của bản triển khai chưa được kiểm chứng, lượng tử hóa có thể làm tụt điểm → đánh giá lại chính artifact Q4_K_M, trên cùng test set và cùng runtime llama.cpp.
- [Nghiêm trọng] "Golden Test" chỉ 50 mẫu, lấy ngẫu nhiên từ test tổng hợp, chưa người thật gán nhãn → khoảng tin cậy rất rộng (48/50 có Wilson 95% CI khoảng 87–99%), lớp hiếm gần như vắng mặt (chỉ khoảng 6–7 mẫu không thuộc lớp đa số) → dùng tập golden do người gán nhãn, phân tầng theo lớp, cỡ vài trăm mẫu trở lên, kèm khoảng tin cậy.
- [Cao] Dữ liệu là bản diễn đạt lại bởi LLM (teacher), cả test cũng tổng hợp → không đại diện cho tin nhắn thật (lỗi chính tả, tiếng Việt không dấu, tiếng lóng), nhãn có thể lệch khi diễn đạt lại → test bằng tin nhắn thật do người gán nhãn, kiểm tra mẫu nhãn sau khi diễn đạt lại, chạy shadow test trên traffic thật.
- [Cao] Chỉ khử trùng lặp chính xác → các bản diễn đạt gần giống vẫn còn, làm rò rỉ ngữ nghĩa và phình dữ liệu → dùng near-dup (MinHash/embedding similarity) và khử trùng lặp theo nhóm.
- [Cao] Giám khảo giải thích là Qwen2.5-72B, cùng họ với teacher tạo dữ liệu → thiên vị tự ưu tiên, chưa hiệu chỉnh với người → dùng giám khảo khác họ, có rubric, đối chiếu mẫu chấm tay và đo độ đồng thuận.
- [Cao] JSON hợp lệ 100% chỉ tính sau bước tự sửa → che giấu tỷ lệ lỗi thô, và hợp lệ schema không đồng nghĩa đúng nghĩa → báo raw validity (trước sửa), tỷ lệ phải sửa và độ trễ của bước sửa, kiểm tra thêm tính đúng nội dung.
- [Cao] Latency chỉ báo trung bình, đo 1 request, ngữ cảnh 256, trên T4, trong khi production là RTX 2060, ngữ cảnh đến 2048, 5 người dùng đồng thời → không đại diện cho production, đuôi trễ (p95/p99) bị bỏ qua → đo p50/p95/p99, TTFT và tokens/s trên RTX 2060 với GGUF Q4_K_M, ngữ cảnh 2048, 5 luồng đồng thời, với số request đủ lớn.
- [Cao] VRAM 1,3 GB chỉ đo ngay sau khi nạp model → bỏ qua KV cache, compute buffer và 5 luồng đồng thời, rủi ro OOM trên card 6 GB → đo VRAM đỉnh dưới tải thật (ngữ cảnh 2048 × 5 luồng), chừa headroom cho hệ điều hành/hiển thị.
- [Cao] An toàn: chỉ 5 prompt injection bằng tiếng Anh, 5/5 → quá ít, sai ngôn ngữ (người dùng nói tiếng Việt), khoảng tin cậy rất rộng, thiếu jailbreak/rò rỉ PII/injection gián tiếp → dùng bộ test tiếng Việt và đa ngôn ngữ, hàng trăm mẫu, đa dạng tấn công, báo tỷ lệ tấn công thành công kèm CI, rà soát rò rỉ PII.
- [Trung bình] Giải mã temperature 0.7, chạy 1 lần → kết quả ngẫu nhiên, không biết phương sai, và có thể khác cấu hình production → chạy nhiều seed hoặc dùng greedy/temperature thấp như production, báo trung bình ± độ lệch chuẩn.
- [Trung bình] Không có baseline, không so với phiên bản trước, không có ngưỡng chấp nhận đặt từ trước → "Đạt chuẩn" không có căn cứ, dễ quyết định theo cảm tính → đặt tiêu chí phát hành định lượng từ trước (macro-F1, recall từng lớp, p95, VRAM, safety) và so với baseline/v1.1.
- [Trung bình] Thiếu phân tích lỗi, kiểm thử độ bền (typo, không dấu, tin nhắn dài/ngắn, ngoài phân phối) và kế hoạch giám sát/rollback → rủi ro lỗi khi chạy thật mà không phát hiện được → thêm error analysis, test robustness, theo dõi drift và kế hoạch rollback.
- [Thấp] Báo cáo không nêu phiên bản dữ liệu/seed/commit, nên khó tái lập → ghi version dữ liệu, seed, cấu hình và commit.
- [Kết luận] Kết luận "Đạt chuẩn phát hành" chưa được các bằng chứng trên hỗ trợ → chưa phát hành, đánh giá lại theo các mục trên.