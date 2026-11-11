# Tiêu Chí Kiểm Duyệt Tại Các Cổng & Phản Biện (Quality Gates, Critic & DoD Checklists)

Scrum Master sử dụng bảng kiểm này cùng với báo cáo của `agile-critic` để đảm bảo chất lượng trước khi đưa ra xin phê duyệt của người dùng tại mỗi Cổng (Gate).

---

## 🛑 Gate 1 Checklist: Nghiên Cứu Thực Chiến, Production-Readiness & Product Backlog

- [ ] **Nghiên cứu tham chiếu (`agile-researcher`)**:
  - [ ] `docs/01-discovery/reference-systems-benchmark.md` đã phân tích tối thiểu 3 hệ thống thực tế, rút ra các tính năng/mẫu UX tinh hoa và các cạm bẫy cần tránh.
  - [ ] `docs/01-discovery/production-readiness-requirements.md` đã liệt kê rõ yêu cầu Security, Reliability (Idempotency/Rate-limit/Retry), Observability, Data Integrity và Vận hành.
- [ ] **Hoạch định sản phẩm (`agile-po-ba`)**:
  - [ ] `vision-statement.md` & `project-charter.md` xác định rõ phạm vi In-scope (MVP) và Out-of-scope.
  - [ ] `product-backlog.md` chuyển hóa đầy đủ cả tính năng nghiệp vụ lẫn các yêu cầu **Production-Readiness** thành Epics & User Stories chuẩn INVEST (`Given/When/Then`, Story Points ≤ 8).
- [ ] **Phản biện độc lập (`agile-critic`)**:
  - [ ] Đã có `docs/05-quality-assurance/critique-reviews/gate-1-critique.md` đạt trạng thái **`[APPROVED FOR GATE]`** (không còn lỗi `Blocker` / `High Risk` tồn đọng).

---

## 🛑 Gate 2 Checklist: Tech Stack, Code Format Chuẩn Team, Kiến Trúc & Kế Hoạch Sprint

- [ ] **Quyết định công nghệ & Chuẩn hóa Code (`agile-tech-lead`)**:
  - [ ] `docs/03-system-design/tech-stack-decision.md` & ADRs chốt rõ phiên bản ngôn ngữ, framework, DB, thư viện được phép/bị cấm kèm phân tích đánh đổi.
  - [ ] `docs/03-system-design/coding-standards.md` quy định chi tiết chuẩn Code Format, Naming, Error Handling, Structured Logging, Testing & Git.
  - [ ] Đã tạo file rule tự động **`.agents/rules/coding-standards.md`** **mở đầu bằng frontmatter `trigger: always_on`** (thiếu dòng này thì subagent không nhận được rule) và các file cấu hình Formatter/Linter (`.editorconfig`, cấu hình lint/fmt theo ngôn ngữ) kèm lệnh kiểm tra chuẩn.
- [ ] **Thiết kế kiến trúc & Hợp đồng giao tiếp (`agile-architect`)**:
  - [ ] `system-architecture.md` có sơ đồ Mermaid, cấu trúc thư mục rõ ràng và giải quyết đầy đủ các bài toán Production (Idempotency, Concurrency, AuthZ, Observability).
  - [ ] `database-design.md` đặc tả đầy đủ ERD, ràng buộc toàn vẹn, chiến lược Index & Migration.
  - [ ] `api-design.md` khóa chặt Request/Response DTO, Validation & bảng Error Codes thống nhất.
- [ ] **Kế hoạch Sprint & Phản biện độc lập (`agile-critic`)**:
  - [ ] `docs/04-sprint-management/sprint-backlog.md` chia các gói công việc không đụng độ file cho Developer chạy song song.
  - [ ] Đã có `docs/05-quality-assurance/critique-reviews/gate-2-critique.md` đạt **`[APPROVED FOR GATE]`**.

---

## 🛑 Gate 3 & Production Definition of Done (DoD) Checklist

Một Sprint / Bản phát hành chỉ được trình nghiệm thu tại Gate 3 khi **100% tiêu chí sau đạt**:

1. **Nghiệp vụ & Kiến trúc**:
   - [ ] Thỏa mãn 100% Acceptance Criteria của các User Stories trong Sprint và khớp tuyệt đối API/DB Contracts.
2. **Đồng nhất Code Format & Chuẩn Kỹ thuật (`Zero Style Drift`)**:
   - [ ] Toàn bộ mã nguồn vượt qua **100% lệnh Formatter Check & Linter/Typecheck** của `agile-tech-lead` mà không có lỗi hay cảnh báo bị phớt lờ.
   - [ ] Không tự ý cài thư viện ngoài danh mục đã duyệt; không hardcode secrets.
3. **Kiểm thử Độc lập bởi `agile-qa`**:
   - [ ] Đầy đủ Unit Tests + Integration/E2E/Security Tests chạy thực tế qua terminal đạt **100% PASS**.
   - [ ] Không còn tồn đọng Bug `Critical` hoặc `Major` trong `bug-reports.md`.
4. **Đóng gói Vận hành (`agile-devops`) & Phản biện Cuối (`agile-critic`)**:
   - [ ] Có cấu hình đóng gói/CI-CD (cưỡng chế tự động Format/Lint/Test), Healthcheck, Graceful Shutdown và kế hoạch Release/Rollback.
   - [ ] Báo cáo `docs/05-quality-assurance/critique-reviews/sprint-N-critique.md` của `agile-critic` xác nhận **`[APPROVED FOR GATE]`**.
5. **Đánh giá model thực tế**:
   - [ ] Mọi bàn giao trong Sprint đã được Scrum Master tự kiểm chứng và ghi vào `docs/04-sprint-management/model-performance.md`, kể cả các lần chuyển model do hết quota.
   - [ ] Đã có bảng tổng hợp theo vai trò–model và đề xuất giữ/đổi model chính (nếu có) để người dùng quyết định.
