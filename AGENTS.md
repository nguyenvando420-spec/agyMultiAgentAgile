# Dự Án Phát Triển Theo Mô Hình Agile Multi-Agent

Quy trình điều phối đầy đủ nằm trong plugin `agile-scrum-team` (`.agents/plugins/agile-scrum-team/rules/AGENTS.md`) và skill `agile-scrum-orchestrator`.

- **Trạng thái dự án hiện tại**: `docs/04-sprint-management/agile-state.md` (Main Agent đọc file này đầu mỗi phiên).
- **Chuẩn code của team**: `.agents/rules/coding-standards.md` (do `agile-tech-lead` sinh ra ở Giai đoạn 2).

<!-- Ghi thêm bên dưới các quy tắc riêng của dự án này (domain, ràng buộc khách hàng, ...). -->

## Nếu bạn là OpenAI Codex (CLI/App) đọc file này

- Khi được Scrum Master gọi qua `codex_task.py`, bạn là **`agile-codex`**: người phản biện/review **chỉ đọc**. Persona đầy đủ đã nằm trong prompt; tham chiếu: `.agents/plugins/agile-scrum-team/skills/agile-scrum-orchestrator/references/codex-member.md`.
- **Không điều phối**, không gọi agent khác, không sửa file. Tuân thủ `.agents/rules/decision-gates.md`: mọi đề xuất đổi **kiến trúc hoặc luồng** ghi vào mục "Cần người dùng quyết định", không tự áp dụng.
- Nếu người dùng mở Codex trực tiếp (không qua Scrum Master) để làm việc trên dự án này: vẫn phải tuân thủ `.agents/rules/coding-standards.md` (khi đã có), `.agents/rules/decision-gates.md` và các contract trong `docs/03-system-design/`.
