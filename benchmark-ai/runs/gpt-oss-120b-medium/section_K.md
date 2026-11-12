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