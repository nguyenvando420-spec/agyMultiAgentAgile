# Model Performance — Đánh Giá Thực Tế Theo Vai Trò

> Scrum Master ghi sau **mỗi lần bàn giao** và tổng hợp tại **mỗi Gate 3**. Cách đánh giá: `model-routing.md` mục 6.
> **Người dùng chọn ngày 12/11/2026**: đây là căn cứ CHÍNH để điều chỉnh model (2 benchmark đều chạm trần, không tách được 5 model mạnh).
> Chỉ ghi số liệu Scrum Master **đã tự kiểm chứng** (mở file, chạy lại lệnh, đọc log thật) — không chép lại lời tự báo của agent.

## Nhật ký bàn giao

| Ngày | Sprint/Gate | Vai trò | Model | Nhiệm vụ | Vòng sửa | Lỗi bị phát hiện (B/H/M) | Báo cáo sai sự thật | Thời gian | Hết quota? | Phản hồi người dùng |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |

## Chỉ số riêng cho vai trò AI (ghi thêm khi vai trò AI bàn giao)

| Ngày | Vai trò | Model | Notebook chạy được trên Colab/Kaggle lần đầu? | Vượt ngân sách (VRAM > 5 GB / phiên > 10 h)? | Rò rỉ dữ liệu bị MLOps-Eval phát hiện? | Số liệu tự báo lệch với số đo lại? | Ghi chú |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

- **Notebook chạy được lần đầu**: Có / Không (lỗi gì: thiếu thư viện, bf16 trên T4, OOM, không resume được…).
- **Số liệu tự báo lệch**: so con số agent báo (accuracy, VRAM, latency) với số `agile-mlops-eval` hoặc Scrum Master đo lại; lệch đáng kể tính là **báo cáo sai sự thật**.

## Nhật ký chuyển model (quota)

| Thời điểm | Vai trò | Từ model | Sang model | Lý do | Quota reset lúc | Đã quay lại model chính? |
|---|---|---|---|---|---|---|
| | | | | | | |

## Tổng hợp tại Gate 3

| Sprint | Vai trò | Model | Tổng vòng sửa | Tổng lỗi B/H | Báo cáo sai | Thời gian TB/bàn giao | Đề xuất (giữ / đổi sang …) | Người dùng duyệt? |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

**Quy tắc đề xuất đổi model** (`model-routing.md` mục 6): ≥ 1 báo cáo sai sự thật, hoặc liên tục phải sửa ≥ 2 vòng, hoặc bị người dùng chê lặp lại. Chất lượng ngang nhau nhưng chậm làm trễ Sprint → được đề xuất đổi sang model nhanh hơn cùng họ (ví dụ Carbon → Argon/Flash cho MLOps-Eval/Critic), kèm số liệu. **Chỉ đổi khi người dùng duyệt.**
