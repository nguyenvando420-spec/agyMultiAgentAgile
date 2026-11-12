# Benchmark v2 — Vai Trò AI (khó hơn, chấm tự động 100%)

v1 (`benchmark-ai/`) bị "chạm trần": 5 model mạnh đều đạt tối đa. v2 được thiết kế để tách được chúng:

- **Một repo nhỏ 4 module** (`repo/mlkit/`), mỗi module ứng với một vai trò AI, có **19 lỗi tinh vi** cài sẵn và **8 bẫy** (code trông đáng ngờ nhưng đúng).
- Đề **không chỉ ra lỗi**: model phải tự đối chiếu code với docstring (hợp đồng) và kiến thức thực tế (Turing không có bf16, GQA, nearest-rank, Wilson, prompt injection, rò rỉ do augment...).
- **Sửa nhầm bị trừ điểm**: điểm = số lỗi sửa đúng − số bẫy bị sửa hỏng. Đo cả độ kỹ lẫn sự kiềm chế.
- **Chấm hoàn toàn tự động** bằng test ẩn (`hidden/hidden_tests.py`) → không có thiên vị người chấm.
- Mỗi model chạy **2 lần** để thấy độ dao động.

| Module | Vai trò | Lỗi (B) | Bẫy (D) |
|---|---|---|---|
| `data_prep.py` | AI Data Engineer | B01 chia tập bằng `hash()` (đổi theo PYTHONHASHSEED); B02 augment cả val/test; B03 biến thể đổi `source_id` → rò rỉ nhóm; B04 thiếu định dạng số điện thoại; B05 khử trùng trước khi ẩn PII | D01 email xử lý trước số điện thoại; D02 giữ bản đầu tiên |
| `train_plan.py` | SLM Trainer | B06 bật bf16/FA2 trên Turing; B07 tính step lưu checkpoint sai (nhân thay vì chia); B08 bỏ quên biên an toàn phiên; B09 KV cache dùng số head Q thay vì KV (GQA) | D03 grad_accum làm tròn lên; D04 so sánh `<=` ngân sách |
| `llm_call.py` | AI Engineer | B10 retry cả lỗi không tạm thời; B11 regex tham lam lấy sai JSON; B12 `bool` lọt qua kiểu số; B13 backoff sai số mũ + không chặn trần; B14 prompt injection qua thẻ `<user_input>` | D05 `timeout=` dạng keyword; D06 retry khi JSON sai rồi trả fallback |
| `eval_metrics.py` | MLOps-Eval | B15 percentile lệch 1; B16 macro-F1 bỏ lớp không được dự đoán; B17 kiểm tra rò rỉ chỉ so trùng chính xác; B18 tỷ lệ JSON tính sau khi sửa; B19 dùng xấp xỉ chuẩn thay vì Wilson | D07 accuracy chặn danh sách rỗng; D08 chia 0 → 0 |

## Chạy lại
```powershell
cd benchmark-ai-v2
python make_prompt.py                       # sinh prompt.md từ repo/
python selftest\make_fixtures.py            # tự kiểm tra bộ chấm:
python grade.py selftest\out_ref selftest\out_empty   # phải ra 19/19 và 0/19, bẫy nguyên vẹn
python run_bench.py --reps 2 claude-opus-5-5-high gemini-4-carbon-high ...
python grade.py --all
```

## Kết quả 12/11/2026
Cả 5 model (Opus, Sonnet, Carbon, Argon, Flash) × 2 lần chạy đều **19/19 lỗi, 0 bẫy bị hỏng** → v2 cũng chạm trần. Thời gian: Sonnet ~100 s, Opus ~165 s, Flash ~190 s, Argon ~350 s, Carbon ~670 s. Chi tiết: `results-2026-11-12/results.json`, mục 7b của `model-routing.md`.

## Giới hạn
- Chế độ headless của `agy` tự từ chối gọi công cụ, nên repo được đưa thẳng vào đề (một lượt trả lời). Muốn đo đúng kiểu "agent tự mở file, tự chạy test" thì người dùng cần tự thêm allow-rule trong `settings.json`.
- Mỗi model 2 lần chạy; vẫn là mẫu nhỏ.
- Các lỗi do Scrum Master (Claude Opus 5.5) thiết kế: có thể vô tình hợp "khẩu vị" của họ Claude. Bù lại, việc chấm là tự động hoàn toàn.
