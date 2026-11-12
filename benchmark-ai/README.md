# Benchmark Model Cho 4 Vai Trò AI

Bộ đề riêng cho các vai trò AI (người dùng yêu cầu ngày 12/11/2026), bổ sung cho `benchmark/` gốc (8 vai trò phần mềm).
Đề bài gắn với ràng buộc thật của người dùng: **huấn luyện trên Colab/Kaggle, triển khai trên RTX 2060 6 GB**.

| Bài | Vai trò | Chấm |
|---|---|---|
| H. Chuẩn bị dataset: chuẩn hóa, ẩn PII, khử trùng, chia theo nhóm chống rò rỉ | `agile-ai-data-engineer` | Tự động: 17 test ẩn so với cài đặt mẫu |
| I. Kế hoạch QLoRA trên Kaggle T4 → GGUF chạy RTX 2060 (JSON) | `agile-slm-trainer` | Tự động: 16 tiêu chí (fp16 không bf16, không FA2, checkpoint + resume, cỡ GGUF, KV cache, không early-stop trên test, …) |
| J. Gọi model có cấu trúc: trích JSON, kiểm kiểu, retry, prompt sửa lỗi, fallback | `agile-ai-engineer` | Tự động: 19 test ẩn với client giả |
| K1. Tính P95 nearest-rank, accuracy, macro-F1, tỷ lệ JSON thô | `agile-mlops-eval` | Tự động: 4 con số |
| K2. Phản biện báo cáo đánh giá model (12 lỗi cài sẵn) | `agile-mlops-eval` (+ `agile-critic` phần AI) | Chấm mù theo `rubric.md` |

## Chạy lại (Windows / Python ≥ 3.9, không cần thư viện ngoài)
```powershell
cd benchmark-ai
python grade.py selftest\reference     # kiểm tra bộ chấm: phải đạt điểm tối đa
python run_bench.py claude-opus-5-5-high gemini-4-carbon-high ...   # danh sách model: agy models
python grade.py runs\<model>            # chấm H, I, J, K1
python blind.py                         # ẩn tên để chấm mù K2
```
Chấm K2 theo `rubric.md` trên `blind/task_K.md`, ghi điểm rồi mới mở `blind/.mapping.json`.

## Kết quả 12/11/2026
Chi tiết: `results-2026-11-12/` và mục 7 của `model-routing.md`. Tóm tắt: 5 model mạnh (Opus, Sonnet, Carbon, Argon, Flash) đều đạt tối đa mọi bài → **đề bị chạm trần**, không tách được 5 model. GPT-OSS: H 15/17, I 9/16, J 17/19, K1 4/4, K2 4/12.

Lưu ý bộ chấm: máy chấm dùng Python 3.9, nên `grade.py` tự thêm `from __future__ import annotations` để bài dùng cú pháp `X | None` (3.10+) trong chữ ký hàm không bị chấm oan.

## Giới hạn
- Mỗi model chạy 1 lần. Bài tự động có thể "chạm trần" như benchmark gốc.
- Người chấm K2 là Scrum Master (Claude Opus 5.5) → có thể thiên vị họ Claude dù chấm mù. Thang điểm chốt trước khi chạy.
- Chỉ đo trả lời một lượt, không đo làm việc nhiều bước với công cụ, không chạy notebook thật trên Colab/Kaggle.
