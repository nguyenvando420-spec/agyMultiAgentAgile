# 🚀 agyMultiAgentAgile — Team Agile/Scrum & AI/SLM Đa Agent Cho Google Antigravity

Plugin + bộ khung biến **Google Antigravity** (`agy` CLI / IDE / App) thành một **đội phát triển phần mềm & AI/SLM chuẩn Enterprise Agile/Scrum** gồm **14 mắt xích** (**1 Scrum Master Dual-mode + 12 Subagents chuyên trách + 1 thành viên phản biện độc lập thứ 13 ngoài Antigravity là `agile-codex`**). Quy trình đi từ nghiên cứu ý tưởng đến sản phẩm sẵn sàng lên Production, có **kiểm định chéo 3 họ model (Claude – Gemini – OpenAI)** và **3 cổng duyệt (Gate)** do bạn quyết định.

---

## 1. Đội hình (14 Vai trò)

### Điều phối trung tâm (Dual-mode)
| Vai trò | Agent | Việc chính | Đầu ra |
|---|---|---|---|
| Scrum Master | `agile-scrum-master` *(Main Agent trực tiếp hoặc gọi riêng qua `--agent` / subagent)* | Điều phối toàn trình, lập Sprint Backlog, đóng gói Context Packet, kiểm chứng bàn giao, quản lý vòng `Tác giả → Critic/Codex → Sửa → QA/MLOps-Eval → Gate` | `agile-state.md`, `sprint-backlog.md`, `model-performance.md` |

### Nhóm Sản phẩm, Kiến trúc, Phần mềm & Vận hành (8 Subagents)
| Vai trò | Agent | Việc chính | Đầu ra |
|---|---|---|---|
| Researcher | `agile-researcher` | Khảo sát hệ thống & kiến trúc model AI/SLM thực tế đã triển khai, yêu cầu bắt buộc để lên Production | `docs/01-discovery/` |
| PO/BA | `agile-po-ba` | Vision, Personas, Epics, User Stories INVEST (cả phần mềm, AI/SLM & NFRs) | `docs/01-discovery/`, `docs/02-product-planning/` |
| Tech Lead | `agile-tech-lead` | Chọn Tech Stack, Base Model, Quantization/Serving (ADR) + **chuẩn code format/linter cho cả team** | `tech-stack-decision.md`, `.agents/rules/coding-standards.md` |
| Architect | `agile-architect` | Kiến trúc C4, AI/RAG pipeline, ngân sách VRAM, DB/Vector schema, API & Structured Output contracts | `docs/03-system-design/` |
| Critic | `agile-critic` | Phản biện độc lập trước Gate 1, 2, 3 (cả phần mềm, dữ liệu/model AI & giới hạn phần cứng) | `docs/05-quality-assurance/critique-reviews/` |
| Developer | `agile-developer` | Code phần mềm + unit test (chạy song song được) tuân thủ 100% Contract & Format | Mã nguồn + Unit Tests |
| QA | `agile-qa` | Integration/E2E/AppSec test phần mềm, nghiệm thu Definition of Done | `docs/05-quality-assurance/` |
| DevOps | `agile-devops` | **Người dựng hạ tầng**: Docker, Model Serving container, CI/CD gatekeeping, healthcheck, release/rollback | `docs/06-release-deployment/` |

### Nhóm Chuyên sâu Dữ liệu AI, Model AI Nhỏ Nhẹ (SLM) & MLOps (4 Subagents)
| Vai trò | Agent | Việc chính | Đầu ra |
|---|---|---|---|
| AI Data Engineer | `agile-ai-data-engineer` | Làm sạch, khử trùng lặp, ẩn danh PII, sinh dữ liệu tổng hợp (Synthetic/Distillation), chia `Train/Val/Golden Test` theo nhóm (0% Data Leakage) & nạp/chunk/embed RAG **offline** | `docs/03-system-design/ai-dataset-spec.md`, scripts dữ liệu |
| SLM Trainer | `agile-slm-trainer` | Viết notebook/script trên **Google Colab / Kaggle** để fine-tune (QLoRA/LoRA/DPO), chưng cất tri thức, cắt tỉa & lượng tử hóa (`GGUF`, `ONNX`, `AWQ`) chạy vừa **RTX 2060 6 GB** (≤ 5 GB VRAM) | `docs/03-system-design/slm-training-compression-report.md`, notebooks |
| AI Engineer | `agile-ai-engineer` | Phát triển tầng ứng dụng AI **lúc chạy (query-time)**: Prompt-as-Code, Structured Outputs, RAG/Hybrid Search/Reranking, Function Calling, Agentic Workflow, Caching, Fallback/Guardrails | Mã nguồn tầng AI + Prompt/RAG tests |
| MLOps & AI Eval | `agile-mlops-eval` | **Người chấm độc lập (không dựng)**: đánh giá model sau lượng tử hóa trên Golden Test Set, rà soát rò rỉ dữ liệu, đo Latency P95 & Peak VRAM trên RTX 2060 6 GB, red-team an toàn AI & kiểm chứng cơ chế rollback do DevOps dựng | `docs/05-quality-assurance/ai-evaluation-report.md`, `ai-safety-redteam-report.md` |

### Thành viên thứ 13 ngoài Antigravity (Họ Model thứ 3 — OpenAI)
| Vai trò | Công cụ | Việc chính | Đầu ra |
|---|---|---|---|
| Codex Reviewer | `agile-codex` *(OpenAI Codex CLI `gpt-6.1-sol`, sandbox `read-only`)* | (1) Phản biện song song với `agile-critic` trước Gate 2 & Gate 3; (2) Review code từng gói việc trước khi chuyển sang QA | `gate-2-codex.md`, `gate-3-codex.md`, `docs/05-quality-assurance/codex-reviews/<WP-id>.md` |

---

## 2. Quy trình & 3 Gate

1. **Gate 1**: Researcher → PO/BA → Critic → bạn duyệt nghiên cứu + Product Backlog.
2. **Gate 2**: Tech Lead + Architect → Scrum Master lập Sprint Backlog → Critic + Codex (song song) → bạn duyệt công nghệ, model, chuẩn code, thiết kế, kế hoạch Sprint.
3. **Gate 3**: (AI Data Engineer → SLM Trainer) + (Developer + AI Engineer) → Codex review từng gói việc → QA + MLOps-Eval → DevOps (MLOps-Eval kiểm chứng) → Critic + Codex (song song) → bạn nghiệm thu Sprint và quyết định release.

---

## 3. Mỗi vai trò một model (Kiểm định chéo 3 họ Model)

Phân công dựa trên khảo sát thực nghiệm ([benchmark/](benchmark/README.md), [benchmark-ai/](benchmark-ai/README.md), [benchmark-ai-v2/](benchmark-ai-v2/prompt.md)), chi tiết trong [model-routing.md](.agents/plugins/agile-scrum-team/skills/agile-scrum-orchestrator/references/model-routing.md):

| Nhóm / Vai trò | Model chính | Dự phòng |
|---|---|---|
| `agile-scrum-master`, `agile-researcher`, `agile-architect`, `agile-slm-trainer` | `claude-opus-5-5-high` | `claude-sonnet-5-5-high` / `gemini-4-argon-high` |
| `agile-po-ba`, `agile-tech-lead`, `agile-developer`, `agile-ai-data-engineer`, `agile-ai-engineer` | `claude-sonnet-5-5-high` | `gemini-4-argon-high` / `gemini-4-carbon-high` |
| `agile-critic`, `agile-mlops-eval` *(Kiểm định độc lập khác họ với tác giả Claude)* | `gemini-4-carbon-high` | `gemini-4-argon-high` |
| `agile-qa` *(Kiểm thử phần mềm độc lập khác họ với Developer)* | `gemini-4-argon-high` | `gemini-4-carbon-high` |
| `agile-devops`, `agile-developer` (story đơn giản) | `gemini-3.8-flash-high` | `gemini-4-argon-high` / `claude-sonnet-5-5-medium` |
| `agile-codex` *(Phản biện độc lập họ model thứ 3 — OpenAI)* | `gpt-6.1-sol` (Codex CLI) | — |

---

## 4. Cài đặt

### Dự án mới
```bash
git clone git@github.com:nguyenvando420-spec/agyMultiAgentAgile.git
./agyMultiAgentAgile/scripts/init-agile-project.sh ../ten-du-an-moi
```

### Dự án có sẵn
```bash
cp -R agyMultiAgentAgile/.agents agyMultiAgentAgile/AGENTS.md /duong-dan/du-an/
```

### Kiểm tra
```bash
agy plugin validate .agents/plugins/agile-scrum-team --strict
```

---

## 5. Cấu trúc repo
```text
.agents/
├── rules/decision-gates.md         # Quy tắc bắt buộc hỏi người dùng khi đổi Kiến trúc / Luồng
└── plugins/agile-scrum-team/
    ├── plugin.json                 # Manifest v2.3.0 (13 agents + 2 skills + 1 rule)
    ├── rules/AGENTS.md             # Quy tắc điều phối toàn đội
    ├── agents/                     # 13 persona agile-* (agile-scrum-master + 12 subagents chuyên trách)
    └── skills/
        ├── agile-scrum-orchestrator/
        │   ├── SKILL.md
        │   ├── scripts/codex_task.py
        │   └── references/         # compute-profile, model-routing, codex-member, permissions-setup, ...
        └── agile-sprint-runner/
AGENTS.md                           # Rule gốc chép vào dự án
scripts/init-agile-project.sh       # Khởi tạo dự án mới
benchmark/                          # Benchmark 8 vai trò gốc (11/11/2026)
benchmark-ai/                       # Benchmark 4 vai trò AI v1 (12/11/2026)
benchmark-ai-v2/                    # Benchmark 4 vai trò AI v2 nâng cao (12/11/2026)
```
