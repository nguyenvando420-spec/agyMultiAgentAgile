# 🚀 agyMultiAgentAgile — Team Agile/Scrum Đa Agent Cho Google Antigravity

Plugin + bộ khung biến **Google Antigravity** (`agy` CLI / IDE / App) thành một **đội phát triển phần mềm Agile/Scrum** gồm **1 Scrum Master + 8 agent chuyên trách**. Quy trình đi từ nghiên cứu ý tưởng đến code sẵn sàng lên Production, có **phản biện độc lập** trước mỗi lần xin duyệt và **3 cổng duyệt (Gate)** do bạn quyết định.

---

## 1. Đội hình

| Vai trò | Agent | Việc chính | Đầu ra |
|---|---|---|---|
| Scrum Master | Main Agent + skill `agile-scrum-orchestrator` | Điều phối, vòng `Tác giả → Critic → Sửa → Gate`, ghi trạng thái | `agile-state.md`, báo cáo Gate |
| Researcher | `agile-researcher` | Khảo sát hệ thống thực tế đã triển khai, yêu cầu để lên Production | `docs/01-discovery/` |
| PO/BA | `agile-po-ba` | Vision, Personas, Epics, User Stories INVEST (Given/When/Then) | `docs/01-discovery/`, `docs/02-product-planning/` |
| Tech Lead | `agile-tech-lead` | Chọn công nghệ (ADR) + **chuẩn code format/linter cho cả team** | `tech-stack-decision.md`, `.agents/rules/coding-standards.md` |
| Architect | `agile-architect` | Kiến trúc C4, DB schema, API contract | `docs/03-system-design/` |
| Critic | `agile-critic` | Phản biện độc lập trước Gate 1, 2, 3 | `docs/05-quality-assurance/critique-reviews/` |
| Developer | `agile-developer` | Code + unit test (chạy song song được) | Mã nguồn |
| QA | `agile-qa` | Integration/E2E/AppSec test, nghiệm thu Definition of Done | `docs/05-quality-assurance/` |
| DevOps | `agile-devops` | Docker, CI/CD, healthcheck, kế hoạch release/rollback | `docs/06-release-deployment/` |

## 2. Quy trình & 3 Gate

1. **Gate 1**: Researcher → PO/BA → Critic → bạn duyệt nghiên cứu + Product Backlog.
2. **Gate 2**: Tech Lead + Architect → Critic → bạn duyệt công nghệ, chuẩn code, thiết kế, kế hoạch Sprint.
3. **Gate 3**: Developer ↔ QA → DevOps → Critic → bạn nghiệm thu Sprint và quyết định release.

## 3. Mỗi vai trò một model

Phân công dựa trên khảo sát 6 model ([benchmark/](benchmark/README.md)), chi tiết trong [model-routing.md](.agents/plugins/agile-scrum-team/skills/agile-scrum-orchestrator/references/model-routing.md):

| Vai trò | Model |
|---|---|
| Researcher, Architect | Claude Opus 5.5 (High) |
| PO/BA, Tech Lead, Developer | Claude Sonnet 5.5 (High) |
| Critic | Gemini 4 Carbon (High), khác họ model với người viết |
| QA | Gemini 4 Argon (High), khác họ với Developer |
| DevOps, Developer cho việc đơn giản | Gemini 3.8 Flash (High) |

- **Hết quota**: Scrum Master tự chuyển sang model dự phòng (giữ nguyên hội thoại) và báo bạn.
- **Đánh giá thực tế**: mỗi lần bàn giao được Scrum Master tự kiểm chứng và ghi vào `model-performance.md`. Tại Gate 3, nếu cần thì đề xuất đổi model kèm số liệu. Chỉ đổi khi bạn duyệt.
- Ghim model cụ thể cho từng vai trò cần dùng **swarm**. `invoke_subagent` chỉ chọn được tier `flash`/`pro`.

## 4. Cài đặt

### Dự án mới
```bash
git clone git@github.com:nguyenvando420-spec/agyMultiAgentAgile.git
./agyMultiAgentAgile/scripts/init-agile-project.sh ../ten-du-an-moi
```
Script sẽ:
- chép `.agents/` và `AGENTS.md` vào dự án;
- tạo cây `docs/01..08`, `agile-state.md` và `model-performance.md`;
- chạy `git init` và tạo commit đầu tiên (cần đã cấu hình `git user.name`/`user.email`).

Nếu đặt thư mục `scrum-project-framework` (bộ biểu mẫu Scrum) cạnh repo này, script tự chép biểu mẫu vào `docs/`. Thêm `--empty-docs` nếu chỉ cần thư mục trống.

### Dự án có sẵn
```bash
cp -R agyMultiAgentAgile/.agents agyMultiAgentAgile/AGENTS.md /duong-dan/du-an/
```

### Kiểm tra
```bash
agy plugin validate .agents/plugins/agile-scrum-team --strict
```

## 5. Bắt đầu
Mở dự án trong Antigravity và nhập:
> Khởi chạy quy trình Agile chuẩn Production cho ý tưởng mới: [mô tả ý tưởng]. Cho Researcher khảo sát hệ thống thực tế trước, lập Backlog, qua Critic và dừng ở Gate 1 để tôi duyệt.

## 6. Lưu ý đã kiểm chứng
- File `.agents/rules/*.md` **phải** mở đầu bằng frontmatter `trigger: always_on` thì subagent mới nhận được.
- Chế độ headless (`agy -p`) tự từ chối quyền ghi file nếu `settings.json` chưa có allow-rule.
- Không tin báo cáo của agent: khi khảo sát đã có model báo ghi file trong khi thực tế không ghi. Scrum Master luôn tự kiểm chứng.

## Cấu trúc repo
```
.agents/plugins/agile-scrum-team/
├── plugin.json
├── rules/AGENTS.md                 # Quy tắc điều phối (phân tách Main Agent / subagent)
├── agents/                         # 8 persona agile-*
└── skills/
    ├── agile-scrum-orchestrator/   # Playbook + references (gate, handoff, model routing, mẫu state/performance)
    └── agile-sprint-runner/        # Chạy Sprint song song, vòng Dev ↔ QA
AGENTS.md                           # Rule gốc chép vào dự án
scripts/init-agile-project.sh       # Khởi tạo dự án mới
benchmark/                          # Bộ đề khảo sát model + kết quả 11/11/2026
```
