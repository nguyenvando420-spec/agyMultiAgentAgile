# Mẫu Gói Ngữ Cảnh Bàn Giao Cho 8 Subagents (Context Packet Templates)

Mỗi Subagent chạy trong phiên ngữ cảnh độc lập. Khi gọi `invoke_subagent`, Scrum Master sử dụng các mẫu Context Packet dưới đây để truyền đủ thông tin đầu vào, ràng buộc và đường dẫn file đầu ra.

---

## 1. Prompt giao việc cho `agile-researcher`

```markdown
### Nhiệm vụ: Khảo sát Hệ thống Thực tế Đã Triển khai & Đặc tả Yêu cầu Production-Readiness
- **Ý tưởng & Bối cảnh bài toán từ người dùng**:
  <điền toàn bộ mô tả ý tưởng, đối tượng người dùng, quy mô dự kiến>
- **Thư mục dự án**: `<đường dẫn tuyệt đối tới dự án>`
- **Đầu ra bắt buộc trong `docs/01-discovery/`**:
  1. `reference-systems-benchmark.md`: Phân tích 3-5 sản phẩm/dự án Open-Source/kiến trúc thực tế đầu ngành cùng bài toán; rút ra những điểm tốt nhất nên áp dụng cho MVP và các cạm bẫy thất bại cần tránh.
  2. `production-readiness-requirements.md`: Danh mục các yêu cầu bắt buộc để hệ thống lên Production an toàn (Security/RBAC, Rate-limiting, Idempotency, Retry/Timeout, Data Integrity, Structured Logging/Metrics/Healthchecks, Ops/Admin).
- **Yêu cầu trả về**: Top 5 tinh hoa học hỏi từ thực tế và Top 5 hạng mục Production sống còn cần đưa vào Backlog.
```

---

## 2. Prompt giao việc cho `agile-po-ba`

```markdown
### Nhiệm vụ: Phân tích Sản phẩm & Xây dựng Product Backlog Chuẩn Production
- **Thư mục dự án**: `<đường dẫn tuyệt đối tới dự án>`
- **Ý tưởng gốc từ người dùng**: <mô tả ngắn gọn>
- **Đầu vào bắt buộc đọc trước**:
  - `docs/01-discovery/reference-systems-benchmark.md`
  - `docs/01-discovery/production-readiness-requirements.md`
- **Đầu ra bắt buộc**:
  1. `docs/01-discovery/vision-statement.md` & `project-charter.md`
  2. `docs/02-product-planning/user-personas.md`
  3. `docs/02-product-planning/product-backlog.md` (gồm cả Functional Epics lẫn Production-Readiness Epics; User Stories chuẩn INVEST kèm Acceptance Criteria `Given/When/Then` và Story Points ≤ 8).
- **Yêu cầu trả về**: Tóm tắt phạm vi MVP, danh sách Epics/User Stories ưu tiên và câu hỏi mở cho Gate 1.
```

---

## 3. Prompt giao việc cho `agile-tech-lead`

```markdown
### Nhiệm vụ: Quyết định Công nghệ (Tech Stack) & Thống nhất Code Format Chuẩn Cho Cả Team
- **Thư mục dự án**: `<đường dẫn tuyệt đối tới dự án>`
- **Đầu vào đã duyệt tại Gate 1**:
  - `docs/01-discovery/production-readiness-requirements.md`
  - `docs/02-product-planning/product-backlog.md`
  - Ghi chú/Ưu tiên công nghệ của người dùng (nếu có): <điền thông tin>
- **Đầu ra bắt buộc**:
  1. `docs/03-system-design/tech-stack-decision.md` & `architecture-decision-record.md` (chốt ngôn ngữ, framework, DB, danh mục thư viện được phép/bị cấm).
  2. `docs/03-system-design/coding-standards.md` (chuẩn Code Format, Naming, Error Handling, Logging, Testing & Git).
  3. **Rule tự động cho toàn team**: Ghi file `.agents/rules/coding-standards.md` cô đọng để mọi Developer/QA Subagent tự động tuân thủ. File BẮT BUỘC mở đầu bằng frontmatter `---\ntrigger: always_on\n---`, nếu không sẽ không được nạp.
  4. **Cấu hình công cụ tự động tại gốc dự án**: Tạo `.editorconfig` và file cấu hình Formatter + Linter chuẩn của ngôn ngữ đã chọn; cung cấp chính xác bộ lệnh kiểm tra (`fmt check`, `lint`, `test`).
```

---

## 4. Prompt giao việc cho `agile-architect`

```markdown
### Nhiệm vụ: Thiết kế Kiến trúc C4, Cơ sở dữ liệu & Khóa chặt API Contracts
- **Thư mục dự án**: `<đường dẫn tuyệt đối tới dự án>`
- **Đầu vào bắt buộc đọc trước**:
  - `docs/01-discovery/production-readiness-requirements.md`
  - `docs/02-product-planning/product-backlog.md`
  - Quyết định công nghệ & quy chuẩn của Tech Lead tại `docs/03-system-design/tech-stack-decision.md` & `coding-standards.md`
- **Đầu ra bắt buộc trong `docs/03-system-design/`**:
  1. `system-architecture.md` (Sơ đồ Mermaid C4, cấu trúc thư mục mã nguồn, cơ chế Idempotency/Concurrency/Security/Observability).
  2. `database-design.md` (ERD, bảng, ràng buộc toàn vẹn, chiến lược Index & Migration).
  3. `api-design.md` (Request/Response DTO, Validation, AuthZ & bảng Error Codes cho từng User Story).
- **Yêu cầu trả về**: Tóm tắt thiết kế và đề xuất chia các gói công việc độc lập (không đụng độ file) cho Sprint 1.
```

---

## 5. Prompt giao việc cho `agile-critic` (Dùng cho cả 3 Vòng Phản biện)

```markdown
### Nhiệm vụ: Phản biện Độc lập (Devil's Advocate) — Đợt: <Gate 1 | Gate 2 | Sprint N>
- **Thư mục dự án**: `<đường dẫn tuyệt đối tới dự án>`
- **Danh sách tài liệu / mã nguồn cần phản biện chéo**:
  <liệt kê các file đầu ra của giai đoạn hiện tại>
- **Trọng tâm đánh giá**:
  - (Nếu Gate 1): Đối chiếu Backlog với nghiên cứu thực tế & yêu cầu Production; tìm lỗ hổng nghiệp vụ, Scope Creep hoặc thiếu sót vận hành sống còn.
  - (Nếu Gate 2): Tìm điểm nghẽn tải/SPOF, lỗ hổng Race Condition/DB/API Contract, kiểm tra độ chặt của `.agents/rules/coding-standards.md` + cấu hình Formatter/Linter và nguy cơ xung đột khi chạy Developer song song.
  - (Nếu Sprint N / Gate 3): Chạy kiểm chứng thực tế xem code có lệch chuẩn Format/Lint/Kiến trúc không và đã đủ điều kiện lên Production chưa.
- **Đầu ra bắt buộc**:
  - Ghi báo cáo chi tiết vào `docs/05-quality-assurance/critique-reviews/<ten-dot>-critique.md` (phân loại `Blocker`, `High Risk`, `Improvement`, `Strategic Trade-offs`).
  - Kết luận rõ: `[APPROVED FOR GATE]` hoặc `[REVISION REQUIRED]` (nêu rõ Subagent nào cần sửa mục nào).
```

---

## 6. Prompt giao việc cho `agile-developer`

```markdown
### Nhiệm vụ: Lập trình Tính năng & Unit Tests Chuẩn Format Team — Sprint <N>
- **Vai trò & Phạm vi**: `<ví dụ: Backend Developer - Module Order (US-003, US-004)>`
- **Phạm vi thư mục được phép chỉnh sửa**: `<đường dẫn module>`
- **Tài liệu & Quy chuẩn BẮT BUỘC tuân thủ**:
  - Quy chuẩn Code Format & Kỹ thuật: `.agents/rules/coding-standards.md` và `docs/03-system-design/coding-standards.md`
  - Thư viện được phép: `docs/03-system-design/tech-stack-decision.md`
  - Thiết kế & Hợp đồng: `docs/03-system-design/system-architecture.md`, `database-design.md`, `api-design.md`
  - Acceptance Criteria: `docs/02-product-planning/product-backlog.md`
- **Lệnh kiểm định bắt buộc chạy PASS 100% trước khi bàn giao**:
  1. `<lệnh format check từ Tech Lead>`
  2. `<lệnh lint / typecheck từ Tech Lead>`
  3. `<lệnh unit test từ Tech Lead>`
```

---

## 7. Prompt giao việc cho `agile-qa` & `agile-devops`

- **`agile-qa`**: Đối chiếu `product-backlog.md`, `api-design.md`, `coding-standards.md` và `production-readiness-requirements.md`; viết bổ sung Integration/Security tests, chạy toàn bộ Format Check + Lint + Test Suite và xuất `docs/05-quality-assurance/dod-verification.md` (kèm `bug-reports.md` nếu `[FAIL - CẦN SỬA LỖI]`).
- **`agile-devops`**: Dựa trên `tech-stack-decision.md` và `production-readiness-requirements.md`, thiết lập `Dockerfile` chuẩn bảo mật, `docker-compose.yml`, CI Pipeline cưỡng chế tự động Format/Lint/Test, Healthchecks và bộ kế hoạch Release/Rollback trong `docs/06-release-deployment/`.
