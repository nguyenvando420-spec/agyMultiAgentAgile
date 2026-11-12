# Mẫu Gói Ngữ Cảnh Bàn Giao Cho 12 Subagents (Context Packet Templates)

Mỗi Subagent chạy trong phiên ngữ cảnh độc lập. Khi gọi `invoke_subagent` hoặc `swarm`, Scrum Master sử dụng các mẫu Context Packet dưới đây để truyền đủ thông tin đầu vào, ràng buộc và đường dẫn file đầu ra.

---

## 1. Prompt giao việc cho `agile-researcher`

```markdown
### Nhiệm vụ: Khảo sát Hệ thống / Model AI Thực tế Đã Triển khai & Đặc tả Yêu cầu Production-Readiness
- **Ý tưởng & Bối cảnh bài toán từ người dùng**:
  <điền toàn bộ mô tả ý tưởng, đối tượng người dùng, ràng buộc phần cứng CPU/GPU/Edge nếu có>
- **Thư mục dự án**: `<đường dẫn tuyệt đối tới dự án>`
- **Đầu ra bắt buộc trong `docs/01-discovery/`**:
  1. `reference-systems-benchmark.md`: Phân tích 3-5 sản phẩm/dự án Open-Source/kiến trúc hoặc dòng model AI nhỏ nhẹ (SLM/Edge) đầu ngành cùng bài toán; rút ra những điểm tốt nhất nên áp dụng cho MVP và các cạm bẫy thất bại cần tránh.
  2. `production-readiness-requirements.md`: Danh mục các yêu cầu bắt buộc để hệ thống & model AI lên Production an toàn (Security/RBAC, AI Guardrails/Prompt Injection defense, Rate-limiting, Idempotency, Latency/RAM/VRAM budget, Fallback khi model lỗi, Structured Logging/Metrics/Healthchecks).
- **Yêu cầu trả về**: Top 5 tinh hoa học hỏi từ thực tế và Top 5 hạng mục Production sống còn cần đưa vào Backlog.
```

---

## 2. Prompt giao việc cho `agile-po-ba`

```markdown
### Nhiệm vụ: Phân tích Sản phẩm & Xây dựng Product Backlog Chuẩn Production (Phần mềm & AI)
- **Thư mục dự án**: `<đường dẫn tuyệt đối tới dự án>`
- **Ý tưởng gốc từ người dùng**: <mô tả ngắn gọn>
- **Đầu vào bắt buộc đọc trước**:
  - `docs/01-discovery/reference-systems-benchmark.md`
  - `docs/01-discovery/production-readiness-requirements.md`
- **Đầu ra bắt buộc**:
  1. `docs/01-discovery/vision-statement.md` & `project-charter.md`
  2. `docs/02-product-planning/user-personas.md`
  3. `docs/02-product-planning/product-backlog.md` (gồm cả Functional Epics, AI/SLM/Dataset Epics lẫn Production-Readiness Epics; User Stories chuẩn INVEST kèm Acceptance Criteria `Given/When/Then`, ngưỡng chất lượng/độ trễ AI rõ ràng và Story Points ≤ 8).
- **Yêu cầu trả về**: Tóm tắt phạm vi MVP, danh sách Epics/User Stories ưu tiên và câu hỏi mở cho Gate 1.
```

---

## 3. Prompt giao việc cho `agile-tech-lead`

```markdown
### Nhiệm vụ: Quyết định Công nghệ (Tech Stack + AI/SLM Stack) & Thống nhất Code Format Chuẩn Cho Cả Team
- **Thư mục dự án**: `<đường dẫn tuyệt đối tới dự án>`
- **Đầu vào đã duyệt tại Gate 1**:
  - `docs/01-discovery/production-readiness-requirements.md`
  - `docs/02-product-planning/product-backlog.md`
  - Ghi chú/Ưu tiên công nghệ & phần cứng của người dùng (nếu có): <điền thông tin>
- **Đầu ra bắt buộc**:
  1. `docs/03-system-design/tech-stack-decision.md` & `architecture-decision-record.md` (chốt ngôn ngữ, framework, DB/Vector DB, Base Model nhỏ nhẹ, phương pháp Fine-tune/Distillation, chuẩn Quantization GGUF/ONNX/AWQ, Inference Engine và danh mục thư viện được phép/bị cấm).
  2. `docs/03-system-design/coding-standards.md` (chuẩn Code Format, Naming, Error Handling, Logging, Reproducible Seed cho AI, Testing & Git).
  3. **Rule tự động cho toàn team**: Ghi file `.agents/rules/coding-standards.md` cô đọng để mọi Developer/AI/QA Subagent tự động tuân thủ. File BẮT BUỘC mở đầu bằng frontmatter `---\ntrigger: always_on\n---`, nếu không sẽ không được nạp.
  4. **Cấu hình công cụ tự động tại gốc dự án**: Tạo `.editorconfig` và file cấu hình Formatter + Linter chuẩn của ngôn ngữ đã chọn; cung cấp chính xác bộ lệnh kiểm tra (`fmt check`, `lint`, `test`).
```

---

## 4. Prompt giao việc cho `agile-architect`

```markdown
### Nhiệm vụ: Thiết kế Kiến trúc C4, AI/Inference Pipeline, Cơ sở dữ liệu & Khóa chặt API Contracts
- **Thư mục dự án**: `<đường dẫn tuyệt đối tới dự án>`
- **Đầu vào bắt buộc đọc trước**:
  - `docs/01-discovery/production-readiness-requirements.md`
  - `docs/02-product-planning/product-backlog.md`
  - Quyết định công nghệ & quy chuẩn của Tech Lead tại `docs/03-system-design/tech-stack-decision.md` & `coding-standards.md`
- **Đầu ra bắt buộc trong `docs/03-system-design/`**:
  1. `system-architecture.md` (Sơ đồ Mermaid C4, AI/RAG/SLM Serving Pipeline, cấu trúc thư mục mã nguồn, cơ chế Idempotency/Concurrency/Fallback/Guardrails/Observability).
  2. `database-design.md` (ERD, bảng, Vector Index/Embedding schema nếu có, ràng buộc toàn vẹn & Migration).
  3. `api-design.md` (Request/Response DTO, Structured Output JSON Schemas cho AI, Validation, AuthZ & bảng Error Codes cho từng User Story).
- **Yêu cầu trả về**: Tóm tắt thiết kế và đề xuất chia các gói công việc độc lập (không đụng độ file) cho Sprint 1.
```

---

## 5. Prompt giao việc cho `agile-critic` (Dùng cho cả 3 Vòng Phản biện)

```markdown
### Nhiệm vụ: Phản biện Độc lập (Devil's Advocate) — Đợt: <Gate 1 | Gate 2 | Sprint N>
- **Thư mục dự án**: `<đường dẫn tuyệt đối tới dự án>`
- **Danh sách tài liệu / mã nguồn / báo cáo AI cần phản biện chéo**:
  <liệt kê các file đầu ra của giai đoạn hiện tại>
- **Trọng tâm đánh giá**:
  - (Nếu Gate 1): Đối chiếu Backlog với nghiên cứu thực tế & yêu cầu Production; tìm lỗ hổng nghiệp vụ, thiếu sót về dữ liệu/đánh giá AI, Scope Creep hoặc thiếu sót vận hành sống còn.
  - (Nếu Gate 2): Tìm điểm nghẽn tải/SPOF, rủi ro tràn RAM/VRAM hoặc độ trễ cao của model AI, lỗ hổng Race Condition/DB/API Contract, kiểm tra độ chặt của `.agents/rules/coding-standards.md` + cấu hình Formatter/Linter và nguy cơ xung đột khi chạy song song.
  - (Nếu Sprint N / Gate 3): Chạy kiểm chứng thực tế xem code có lệch chuẩn Format/Lint/Kiến trúc không, model AI có bị Data Leakage/Hallucination/Prompt Injection không và đã đủ điều kiện lên Production chưa.
- **Đầu ra bắt buộc**:
  - Ghi báo cáo chi tiết vào `docs/05-quality-assurance/critique-reviews/<ten-dot>-critique.md` (phân loại `Blocker`, `High Risk`, `Improvement`, `Strategic Trade-offs`).
  - Kết luận rõ: `[APPROVED FOR GATE]` hoặc `[REVISION REQUIRED]` (nêu rõ Subagent nào cần sửa mục nào).
```

---

## 6. Prompt giao việc cho `agile-ai-data-engineer`

```markdown
### Nhiệm vụ: Xây dựng Dataset Huấn luyện/Đánh giá AI & Pipeline Dữ liệu Chuẩn Production — Sprint <N>
- **Vai trò & Phạm vi**: `<ví dụ: AI Data Engineer - Dataset Curation & Golden Test Set (US-005)>`
- **Phạm vi thư mục được phép chỉnh sửa**: `<đường dẫn module data / datasets>`
- **Tài liệu & Quy chuẩn BẮT BUỘC tuân thủ**:
  - `.agents/rules/coding-standards.md` và `docs/03-system-design/tech-stack-decision.md`
  - `docs/03-system-design/system-architecture.md` & `database-design.md`
- **Yêu cầu kỹ thuật bắt buộc**:
  1. Làm sạch, khử trùng lặp, ẩn danh PII và chuẩn hóa định dạng dữ liệu (`Train / Val / Golden Test`) hoặc pipeline chunking/embedding cho RAG.
  2. Kiểm chứng **0% Data Leakage** giữa tập `Train/Val` và `Golden Test Set`.
  3. Chạy PASS 100% `Format Check + Lint/Typecheck + Unit Tests` trước khi bàn giao.
```

---

## 7. Prompt giao việc cho `agile-slm-trainer`

```markdown
### Nhiệm vụ: Phát triển, Tinh chỉnh & Nén/Lượng tử hóa Model AI Nhỏ Nhẹ (SLM / Edge AI) — Sprint <N>
- **Vai trò & Phạm vi**: `<ví dụ: SLM Trainer - Fine-tune & Quantization GGUF/ONNX (US-006)>`
- **Phạm vi thư mục được phép chỉnh sửa**: `<đường dẫn module training / models>`
- **Tài liệu & Quy chuẩn BẮT BUỘC tuân thủ**:
  - `.agents/rules/coding-standards.md` và `docs/03-system-design/tech-stack-decision.md`
  - Dataset từ `agile-ai-data-engineer`: `<đường dẫn train/val>` (TUYỆT ĐỐI không dùng Golden Test Set để train/tune)
- **Yêu cầu kỹ thuật bắt buộc**:
  0. Đọc `.agents/plugins/agile-scrum-team/skills/agile-scrum-orchestrator/references/compute-profile.md`: huấn luyện trên **Colab/Kaggle** (fp16, không bf16, ≤ ~10 giờ/lần, checkpoint + resume), model cuối **≤ 5 GB VRAM trên RTX 2060 6 GB**.
  1. Viết **notebook Colab/Kaggle** thực hiện Fine-tuning (QLoRA/LoRA/DPO) hoặc Knowledge Distillation, rồi merge + lượng tử hóa (`GGUF` mặc định, `ONNX` cho encoder) theo thiết kế. Người dùng chạy notebook và trả lại log metrics + artifact.
  2. Cung cấp bảng đo đối chứng trước & sau khi nén: **Kích thước file (MB/GB), Peak RAM/VRAM, Latency/Throughput và Validation Accuracy/Loss**.
  3. Chạy PASS 100% `Format Check + Lint/Typecheck + Unit Tests` và xuất `Model Card` + Inference snippet.
```

---

## 8. Prompt giao việc cho `agile-ai-engineer` & `agile-developer`

```markdown
### Nhiệm vụ: Lập trình Tính năng Phần mềm / Ứng dụng AI & Unit Tests Chuẩn Format Team — Sprint <N>
- **Vai trò & Phạm vi**: `<ví dụ: Applied AI Engineer - RAG & Structured Output Pipeline (US-007) | Backend Developer (US-003)>`
- **Phạm vi thư mục được phép chỉnh sửa**: `<đường dẫn module>`
- **Tài liệu & Quy chuẩn BẮT BUỘC tuân thủ**:
  - Quy chuẩn Code Format & Kỹ thuật: `.agents/rules/coding-standards.md` và `docs/03-system-design/coding-standards.md`
  - Thư viện & Model được phép: `docs/03-system-design/tech-stack-decision.md`
  - Thiết kế & Hợp đồng: `docs/03-system-design/system-architecture.md`, `database-design.md`, `api-design.md`
  - Acceptance Criteria: `docs/02-product-planning/product-backlog.md`
- **Yêu cầu riêng cho `agile-ai-engineer`**:
  - Quản lý Prompt-as-Code, cưỡng chế Structured Outputs khớp 100% DTO, cài đặt đầy đủ Timeout/Retry/Fallback/Guardrails và kiểm soát Token/Latency.
- **Lệnh kiểm định bắt buộc chạy PASS 100% trước khi bàn giao**:
  1. `<lệnh format check từ Tech Lead>`
  2. `<lệnh lint / typecheck từ Tech Lead>`
  3. `<lệnh unit test từ Tech Lead>`
```

---

## 9. Prompt giao việc cho `agile-qa`, `agile-mlops-eval` & `agile-devops`

- **`agile-qa`**: Đối chiếu `product-backlog.md`, `api-design.md`, `coding-standards.md` và `production-readiness-requirements.md`; viết bổ sung Integration/Security tests, chạy toàn bộ Format Check + Lint + Test Suite và xuất `docs/05-quality-assurance/dod-verification.md` (kèm `bug-reports.md` nếu `[FAIL - CẦN SỬA LỖI]`).
- **`agile-mlops-eval`**: Chạy đánh giá độc lập model/pipeline AI trên tập **Golden Test Set** (đo Accuracy/F1/Faithfulness, Schema Validity Rate, Latency P50/P95, RAM/VRAM), thực hiện kiểm thử Red-Teaming chống **Prompt Injection / Jailbreak / PII Leak**, kiểm chứng đóng gói Inference Server & kịch bản Model Rollback; xuất báo cáo `docs/05-quality-assurance/ai-evaluation-report.md` với kết luận `[AI PASS - ĐẠT CHUẨN PRODUCTION]` hoặc `[AI FAIL - CẦN TINH CHỈNH MODEL/PROMPT]`.
- **`agile-devops`**: Dựa trên `tech-stack-decision.md` và `production-readiness-requirements.md`, thiết lập `Dockerfile` chuẩn bảo mật (bao gồm cả container cho ứng dụng & AI Inference Server), `docker-compose.yml`, CI Pipeline cưỡng chế tự động Format/Lint/Test/Eval, Healthchecks và bộ kế hoạch Release/Rollback trong `docs/06-release-deployment/`.

---

## 10. Context Packet cho `agile-codex` (ghi ra file rồi truyền vào `codex_task.py --packet`)

```markdown
### <Phản biện thiết kế Gate 2 | Review gói việc WP-xx | Phản biện Sprint N trước Gate 3>
- **Gate đã được người dùng duyệt**: <Gate 1 ngày ...; Gate 2 ngày ...>
- **Phạm vi cần đọc**: <danh sách file/thư mục; với gói việc: các file đã tạo/sửa>
- **Tài liệu đối chiếu**: `docs/02-product-planning/product-backlog.md` (US-xx), `docs/03-system-design/*`, `.agents/rules/coding-standards.md`, `compute-profile.md`
- **Kết quả kiểm tra Scrum Master đã chạy lại**: <lệnh format/lint/test + kết quả>
- **Trọng tâm**: <ví dụ: đúng API contract US-07, rò rỉ dữ liệu, VRAM ≤ 5 GB, prompt injection>
- **Đầu ra**: báo cáo theo persona; dòng cuối là nhãn kết luận.
```
Chế độ: `--mode review-design` (Gate 2) hoặc `--mode review-code` (gói việc, Gate 3); trong Sprint có Git ưu tiên kèm `--diff-uncommitted` / `--diff-commit <sha>` / `--diff-base <branch>`, và chọn `--model gpt-6-astra --effort high` (hoặc `gpt-6.1-sol --effort xhigh`) cho Gate 2/3 hoặc gói việc mật mã/FFI/async khó, `--model gpt-6.1-terra` cho gói lớn nhiều crate, `--model gpt-6-luna` cho gói nhỏ.
