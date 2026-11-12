---
name: agile-sprint-runner
description: >-
  Thực thi chi tiết một Sprint phát triển phần mềm & AI/SLM bằng các Subagents: dựng nền tảng chuẩn hóa
  Formatter/Linter (Foundation), chuẩn bị dữ liệu AI & huấn luyện/nén model AI nhỏ nhẹ (agile-ai-data-engineer +
  agile-slm-trainer), chạy lập trình song song nhiều agile-developer và agile-ai-engineer đồng nhất 100% code format,
  kiểm thử độc lập với agile-qa + agile-mlops-eval, đóng gói với agile-devops và phản biện Production với agile-critic.
---

# Agile & AI/SLM Sprint Runner Playbook (Zero-Drift & Production-Ready)

Sử dụng skill này sau khi người dùng đã duyệt thiết kế, Tech Stack / Base Model, chuẩn Code Format và kế hoạch Sprint tại **Gate 2**, hoặc khi chạy các Sprint tiếp theo.

---

## Bước 1: Khởi Tạo Khung Dự Án & Khóa Công Cụ Code Format (Foundation Step)

Trước khi tách nhiều Developer / AI Subagents chạy song song (đặc biệt ở Sprint 1 hoặc khi cập nhật hạ tầng dùng chung):
1. Gọi **1 `agile-developer` duy nhất** (`Role: "Lead Developer - Foundation"`, `Workspace: "inherit"`) để:
   - Khởi tạo manifest dự án (`Cargo.toml` / `package.json` / `pyproject.toml` / `go.mod`), cấu trúc thư mục gốc (bao gồm cả thư mục cho AI/Model/Dataset nếu có), shared error types, structured logger và DB migration cơ sở theo đúng `docs/03-system-design/`.
   - Kích hoạt và kiểm chứng thực tế bộ công cụ **Formatter + Linter + Test Runner** mà `agile-tech-lead` đã quy định để đảm bảo lệnh kiểm tra chuẩn chạy thành công từ vạch xuất phát.
2. Tạo commit mốc nền tảng trên Git trước khi rẽ nhánh song song.

---

## Bước 2: Thực Thi Dữ Liệu AI, Model AI Nhỏ Nhẹ (SLM) & Lập Trình Tính Năng Song Song

Dựa trên `docs/04-sprint-management/sprint-backlog.md`, điều phối các luồng công việc độc lập:

1. **Luồng Dữ liệu & Huấn luyện/Tối ưu Model AI Nhỏ Nhẹ (Nếu Sprint có hạng mục AI/SLM)**:
   - Giao `agile-ai-data-engineer` thu thập, làm sạch, ẩn danh PII, sinh dữ liệu tổng hợp/chưng cất (Synthetic/Distillation data), tách tập `Train / Val / Golden Test` (đảm bảo 0% Data Leakage) hoặc xây dựng pipeline dữ liệu/chunking cho RAG.
   - Giao `agile-slm-trainer` huấn luyện/fine-tune (LoRA/QLoRA/DPO), chưng cất tri thức (Distillation), cắt tỉa (Pruning) và lượng tử hóa (Quantization: `GGUF`, `ONNX`, `AWQ`, `INT8/INT4`) các **model AI nhỏ nhẹ**, kèm bảng đo đối chứng Kích thước, RAM/VRAM, Latency và Validation Accuracy.
2. **Luồng Phát triển Ứng dụng AI & Phần mềm Song song (`agile-ai-engineer` + `agile-developer`)**:
   - Gọi đồng thời các `agile-developer` (phát triển Backend/Frontend/Core modules) và `agile-ai-engineer` (phát triển Prompt-as-Code, Structured Outputs, RAG/Hybrid Search, Agentic Workflows, tích hợp SLM/LLM kèm Fallback/Guardrails) với `Workspace: "share"` hoặc phân vùng cứng theo module.
   - Mọi Subagent tự động nhận rule `.agents/rules/coding-standards.md` và bắt buộc phải chứng minh đã chạy xanh cả **3 lệnh: `Format Check` + `Linter/Typecheck` + `Unit Tests`** trong báo cáo bàn giao.
3. Scrum Master tích hợp (merge) các nhánh công việc về workspace chính và chạy kiểm tra build tổng thể.

---

## Bước 2.5: Codex Review Từng Gói Việc Trước Khi Chuyển QA (`agile-codex`, chỉ đọc)

1. Với mỗi gói việc vừa bàn giao (sau khi Scrum Master đã tự chạy lại Format + Lint + Test), viết Context Packet theo `handoff-prompts.md` mục 10 rồi chạy:
   `python .agents/plugins/agile-scrum-team/skills/agile-scrum-orchestrator/scripts/codex_task.py --mode review-code --packet <packet> --cd . --out docs/05-quality-assurance/codex-reviews/<WP-id>.md`
   Có thể chạy song song cho nhiều gói việc (Codex dùng quota riêng).
2. `[CHANGES REQUESTED]` → Scrum Master **tự kiểm chứng** từng phát hiện, rồi `send_message` các lỗi đúng về tác giả (tối đa 2 vòng/gói việc); phát hiện sai ghi vào `model-performance.md` (vai trò `agile-codex`).
3. Phát hiện thuộc **kiến trúc/luồng** → không giao sửa ngay; trình người dùng (`ask_question`).
4. `[PASS]` (hoặc đã xử lý xong) → chuyển sang Bước 3.

---

## Bước 3: Kiểm Thử Độc Lập Phần Mềm & Đánh Giá AI (`agile-qa` + `agile-mlops-eval`)

1. **Kiểm thử phần mềm & bảo mật (`agile-qa`)**:
   - Kiểm tra tuân thủ Code Format & Linter trên toàn dự án sau tích hợp.
   - Chạy Integration / E2E / Concurrency / AppSec tests đối chiếu với Acceptance Criteria, API Contracts và yêu cầu Production-Readiness.
2. **Đánh giá định lượng Model AI & Kiểm thử An toàn AI (`agile-mlops-eval` — nếu Sprint có AI/SLM)**:
   - Đánh giá độc lập trên tập **Golden Test Set** (Accuracy/F1/Faithfulness, 100% Structured Output Schema Validity).
   - Đo benchmark suy luận thực tế (Latency P50/P95, TTFT, Throughput, Peak RAM/VRAM) đảm bảo model nhỏ nhẹ chạy mượt trong giới hạn phần cứng.
   - Chạy bộ test Red-Teaming chống **Prompt Injection, Jailbreak, PII Leak** và xuất `docs/05-quality-assurance/ai-evaluation-report.md`.
3. **Vòng lặp sửa lỗi tự động**:
   - Nếu `agile-qa` trả về **`[FAIL - CẦN SỬA LỖI]`** hoặc `agile-mlops-eval` trả về **`[AI FAIL - CẦN TINH CHỈNH MODEL/PROMPT]`**:
     - Dùng `send_message` gửi danh sách lỗi cụ thể về đúng `conversationId` của `agile-developer`, `agile-ai-engineer` hoặc `agile-slm-trainer` phụ trách để sửa và chạy lại Format + Lint + Test/Eval.
     - Gọi lại `agile-qa` / `agile-mlops-eval` kiểm tra hồi quy (tối đa 3 vòng lặp tự động).

---

## Bước 4: Đóng Gói DevOps/MLOps, Phản Biện Cuối (`agile-critic`) & Đóng Sprint

1. Khi cả `agile-qa` (**`[PASS - ĐẠT DoD]`**) và `agile-mlops-eval` (**`[AI PASS - ĐẠT CHUẨN PRODUCTION]`**) đã xác nhận đạt chuẩn, gọi `agile-devops` **dựng/cập nhật** cấu hình đóng gói Docker, Model Serving container, CI Pipeline (cưỡng chế Format/Lint/Test/Eval) và tài liệu Release/Rollback (bao gồm cả kịch bản Rollback phiên bản model/prompt); sau đó `agile-mlops-eval` **kiểm chứng độc lập** healthcheck, warm-up và thử rollback model thật.
2. Gọi **`agile-critic`** thực hiện **Phản biện Vòng 3** (`docs/05-quality-assurance/critique-reviews/sprint-N-critique.md`), **song song** chạy Codex chế độ `review-code` toàn Sprint (`sprint-N-codex.md`), để rà soát lần cuối hiện tượng lệch kiến trúc (Architecture Drift), lệch chuẩn code, rủi ro chất lượng/an toàn AI hoặc thiếu sót vận hành Production.
   - Nếu `agile-critic` phát hiện lỗi `Blocker` / `High Risk`, điều phối xử lý dứt điểm và nhờ `agile-qa` / `agile-mlops-eval` / `agile-critic` xác nhận lại.
3. Cập nhật `docs/04-sprint-management/sprint-review.md` & `sprint-retrospective.md`.
4. **Đánh giá model của Sprint**: tổng hợp `docs/04-sprint-management/model-performance.md` theo vai trò–model (vòng sửa, lỗi bị phát hiện, báo cáo sai sự thật, lần hết quota). Nếu có vai trò cần đổi model chính, đưa đề xuất kèm số liệu vào báo cáo Gate 3 để người dùng quyết định.
5. Trình bày báo cáo **Gate 3** cho người dùng.
