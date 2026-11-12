---
trigger: always_on
---

# Điểm Quyết Định Bắt Buộc Hỏi Người Dùng (áp dụng cho MỌI agent, subagent và Codex)

- **Lệnh terminal**: được chạy tự động. Không được lách danh sách lệnh phá hủy bị chặn (xóa đệ quy, format ổ đĩa, `git push --force`, `git reset --hard`, `git clean -fdx`, tắt máy, sửa registry); cần làm thật thì hỏi.
- **Kiến trúc** (Tech Stack, thư viện ngoài danh mục, ranh giới module, C4, DB schema, API/Model contract, base model, cách huấn luyện/lượng tử hóa, runtime suy luận, hạ tầng, ngân sách phần cứng) và **Luồng** (thứ tự giai đoạn/Gate, vai trò, phân công model, phạm vi Sprint/Backlog đã duyệt, quy trình review/QA/release): **KHÔNG tự quyết**.
  - Main Agent (Scrum Master): dừng và hỏi người dùng bằng `ask_question`.
  - Subagent / Codex: dừng phần việc đó, ghi rõ vào báo cáo mục **"Cần người dùng quyết định"** để Scrum Master trình người dùng.
- Hiện thực đúng thiết kế đã duyệt, sửa lỗi trong phạm vi contract, chạy test/lint/build/eval: **không cần hỏi**.
- Không chắc thì coi là quyết định kiến trúc/luồng và hỏi.
