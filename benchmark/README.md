# Benchmark Model Cho Team Agile

Bộ đề 7 bài, mỗi bài ứng với một vai trò:

| Bài | Vai trò | Chấm |
|---|---|---|
| A. Phản biện thiết kế ví điện tử (11 lỗi cài sẵn) | Critic, Architect | Chấm mù theo `rubric.md` |
| B. Viết `parse_duration` theo đặc tả | Developer | Tự động: 36 test ẩn |
| C. Viết test cho `paginate` | QA | Tự động: test phải pass trên code đúng và bắt được 8 bản lỗi (mutation testing) |
| D. Phân tích yêu cầu đặt lịch khám | PO/BA | Chấm mù theo `rubric.md` |
| E. Bài toán bán vé flash sale trong thực tế | Researcher, Architect | Chấm mù theo `rubric.md` |
| F. Chốt công cụ + xuất JSON đúng schema | Tech Lead | Tự động |
| G. Dockerfile production | DevOps | Tự động: 8 tiêu chí |

## Chạy lại
```bash
cd benchmark
python3 -m venv .venv && .venv/bin/pip install pytest
./run.sh claude-opus-5-5-high gemini-4-carbon-high ...   # danh sách model: agy models
.venv/bin/python grade.py runs/<model>                    # chấm B, C, F, G
.venv/bin/python blind.py                                 # ẩn tên để chấm mù A, D, E
```
Chấm A/D/E theo `rubric.md` trên `blind/task_*.md`, ghi điểm rồi mới mở `blind/.mapping.json`.

Kết quả lần chạy 11/11/2026: `results-2026-11-11/` (`scores.json` là điểm mù; `.mapping.json` là bảng nhãn M1..M6 → tên model).
