

######## M1 ########
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


######## M2 ########
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


######## M3 ########
```json
{
  "p95_ms": 900,
  "accuracy": 0.85,
  "macro_f1": 0.527,
  "raw_schema_validity": 0.94
}
```

- [Nghiêm trọng] Sinh 3 bản diễn đạt lại cho mỗi tin gốc rồi mới chia ngẫu nhiên từng dòng 80/10/10 → các biến thể cùng một tin gốc nằm ở cả train, val và test gây rò rỉ dữ liệu (data leakage), làm điểm đánh giá cao giả tạo → Chia tập theo nhóm `source_id` của 5.000 tin gốc trước, sau đó chỉ sinh dữ liệu tổng hợp trên tập train.
- [Cao] Tập test/Golden Test chứa tới ~75% mẫu do Qwen2.5-72B sinh ra và chỉ khử trùng lặp chính xác (exact match) → không loại được các tin gần trùng ngữ nghĩa (near-duplicates) và chấm điểm trên phân phối nhân tạo thay vì ngôn ngữ khách hàng thật → Áp dụng near-deduplication (MinHash/embedding) và xây dựng tập val/Golden Test 100% từ tin nhắn CSKH thực tế được gán nhãn chuẩn bởi người.
- [Nghiêm trọng] Golden Test chỉ lấy ngẫu nhiên 50 mẫu không phân tầng cho bài toán 12 lớp mất cân bằng nặng → sai số thống kê rất lớn và nhiều lớp thiểu số có 0 mẫu trong tập chấm → Tăng quy mô Golden Test (ví dụ ≥ 1.000 mẫu) và lấy mẫu phân tầng (stratified) đảm bảo đủ số lượng mẫu tối thiểu cho mỗi lớp.
- [Nghiêm trọng] Chỉ dùng Accuracy (96%) khi lớp đa số chiếm tới 87% lưu lượng thực tế → che khuất hoàn toàn khả năng model đoán sai hoặc bỏ sót 11 lớp thiểu số quan trọng (khiếu nại, hủy đơn, sự cố) → Bắt buộc đo Macro-F1, Precision/Recall/F1 từng lớp và ma trận nhầm lẫn (Confusion Matrix).
- [Nghiêm trọng] Chọn checkpoint tốt nhất dựa trực tiếp trên điểm Golden Test → rò rỉ tập kiểm định vào bước chọn mô hình (selection bias/overfitting lên 50 mẫu test), làm mất tính khách quan của cổng nghiệm thu → Chỉ dùng tập `val` cho early stopping và chọn checkpoint, giữ Golden Test độc lập chỉ chấm một lần trước phát hành.
- [Nghiêm trọng] Chấm điểm trên bản FP16 nhưng triển khai thực tế bản lượng tử hóa `GGUF Q4_K_M` → không phát hiện được suy giảm độ chính xác, lệch chat template/tokenizer hoặc tăng lỗi JSON do nén 4-bit và khác engine suy luận → Chạy toàn bộ bài kiểm định chất lượng, schema và an toàn trực tiếp trên file `GGUF Q4_K_M` chạy qua `llama.cpp`.
- [Cao] Dùng cùng Qwen2.5-72B vừa làm teacher sinh dữ liệu vừa làm giám khảo chấm phần giải thích → thiên kiến tự ưa thích văn phong của chính mình (self-preference/circular bias) và không phát hiện được ảo giác sai nghiệp vụ → Dùng giám khảo độc lập khác họ model kèm rubric chặt chẽ và hiệu chuẩn độ đồng thuận (Cohen's Kappa) với tập chấm tay của chuyên gia.
- [Cao] Báo cáo tỷ lệ JSON hợp lệ 100% sau bước tự sửa JSON mà ẩn tỷ lệ hợp lệ thô → che giấu lỗi cú pháp thực của model, tăng độ trễ xử lý và có nguy cơ bộ sửa cơ học làm biến dạng giá trị trường/nhãn → Đo riêng `raw_schema_validity` trước khi sửa, kiểm tra chặt JSON Schema cùng danh mục 12 nhãn hợp lệ và bật grammar constraint trong `llama.cpp`.
- [Nghiêm trọng] Đo hiệu năng trên Kaggle T4 ở ngữ cảnh 256 token với 1 request đơn lẻ trong khi Production dùng RTX 2060 6 GB, ngữ cảnh 2048 token và 5 người dùng đồng thời → sai lệch hoàn toàn về năng lực phần cứng, chi phí prefill ngữ cảnh dài và độ trễ xếp hàng khi chạy song song → Benchmark trực tiếp trên RTX 2060 6 GB với `llama.cpp` ở tải thực 5 kết nối đồng thời và ngữ cảnh lên tới 2048 token.
- [Cao] Đo latency trên đúng 1 request và gọi là "trung bình 180 ms" → cỡ mẫu N=1 vô nghĩa thống kê và giá trị trung bình che giấu độ trễ đuôi (tail latency) gây nghẽn trải nghiệm khách hàng → Chạy bước warm-up rồi đo trên hàng trăm–nghìn request để báo cáo P50, P95, P99, TTFT và throughput.
- [Nghiêm trọng] Chỉ đo VRAM (1,3 GB) ngay sau khi nạp model ở trạng thái nghỉ → bỏ qua dung lượng KV cache cho 5 phiên đồng thời × 2048 token, compute buffers và VRAM hệ điều hành, dẫn tới nguy cơ tràn bộ nhớ (OOM) khi chịu tải thật trên thẻ 6 GB → Đo Peak VRAM dưới tải đồng thời tối đa (5 slots × 2048 tokens) chạy liên tục.
- [Cao] Kiểm thử an toàn chỉ với 5 câu prompt injection tiếng Anh cho hệ thống CSKH tiếng Việt → cỡ mẫu quá nhỏ và bỏ lọt tấn công tiếng Việt, không dấu/teencode, trộn ngôn ngữ, rò rỉ PII hoặc ép xuất sai JSON → Xây dựng bộ Red-Teaming tiếng Việt và đa ngữ hàng trăm mẫu bao phủ prompt injection, jailbreak, PII leak và tấn công cấu trúc đầu ra.
- [Trung bình] Đặt `temperature = 0.7` và chỉ chạy đánh giá 1 lần cho tác vụ phân loại có cấu trúc → đầu ra ngẫu nhiên thiếu ổn định giữa các lần gọi, tăng nguy cơ lỗi JSON và kết quả trên 50 mẫu dao động may rủi → Chuyển sang giải mã tất định (`temperature = 0`) cho tác vụ phân loại xuất JSON và kiểm chứng tính tái lập.


######## M4 ########
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


######## M5 ########
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


######## M6 ########
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
