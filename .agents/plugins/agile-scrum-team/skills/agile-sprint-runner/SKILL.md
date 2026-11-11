---
name: agile-sprint-runner
description: >-
  Thực thi chi tiết một Sprint phát triển phần mềm bằng các Subagents: dựng nền tảng chuẩn hóa
  Formatter/Linter (Foundation), chạy lập trình song song nhiều agile-developer đồng nhất 100% code format,
  kiểm thử độc lập với agile-qa, đóng gói với agile-devops và phản biện Production với agile-critic.
---

# Agile Sprint Runner Playbook (Zero-Drift & Production-Ready)

Sử dụng skill này sau khi người dùng đã duyệt thiết kế, Tech Stack, chuẩn Code Format và kế hoạch Sprint tại **Gate 2**, hoặc khi chạy các Sprint tiếp theo.

---

## Bước 1: Khởi Tạo Khung Dự Án & Khóa Công Cụ Code Format (Foundation Step)

Trước khi tách nhiều Developer Subagents chạy song song (đặc biệt ở Sprint 1 hoặc khi cập nhật hạ tầng dùng chung):
1. Gọi **1 `agile-developer` duy nhất** (`Role: "Lead Developer - Foundation"`, `Workspace: "inherit"`) để:
   - Khởi tạo manifest dự án (`Cargo.toml` / `package.json` / `pyproject.toml` / `go.mod`), cấu trúc thư mục gốc, shared error types, structured logger và DB migration cơ sở theo đúng `docs/03-system-design/`.
   - Kích hoạt và kiểm chứng thực tế bộ công cụ **Formatter + Linter + Test Runner** mà `agile-tech-lead` đã quy định để đảm bảo lệnh kiểm tra chuẩn chạy thành công từ vạch xuất phát.
2. Tạo commit mốc nền tảng trên Git trước khi rẽ nhánh song song.

---

## Bước 2: Lập Trình Tính Năng Song Song Đồng Nhất Chuẩn Format (`agile-developer`)

1. Dựa trên `docs/04-sprint-management/sprint-backlog.md`, gọi đồng thời nhiều `agile-developer` subagents (sử dụng `Workspace: "share"` hoặc phân vùng cứng theo module/tầng).
2. Mọi `agile-developer` tự động nhận rule `.agents/rules/coding-standards.md` và bắt buộc phải chứng minh đã chạy xanh cả **3 lệnh: `Format Check` + `Linter/Typecheck` + `Unit Tests`** trong báo cáo bàn giao.
3. Scrum Master tích hợp (merge) các nhánh công việc về workspace chính và chạy kiểm tra build tổng thể.

---

## Bước 3: Kiểm Thử Độc Lập & Vòng Lặp Sửa Lỗi (`agile-qa` ↔ `agile-developer`)

1. Gọi `agile-qa` kiểm tra toàn bộ:
   - Tuân thủ Code Format & Linter trên toàn dự án sau tích hợp.
   - Integration / E2E / Concurrency / AppSec tests đối chiếu với Acceptance Criteria, API Contracts và yêu cầu Production-Readiness.
2. Nếu `agile-qa` trả về **`[FAIL - CẦN SỬA LỖI]`**:
   - Dùng `send_message` gửi danh sách lỗi từ `bug-reports.md` về đúng `conversationId` của `agile-developer` phụ trách để sửa và chạy lại Format + Lint + Test.
   - Gọi lại `agile-qa` kiểm tra hồi quy (tối đa 3 vòng lặp tự động).

---

## Bước 4: Đóng Gói DevOps, Phản Biện Cuối (`agile-critic`) & Đóng Sprint

1. Khi `agile-qa` xác nhận **`[PASS - ĐẠT DoD]`**, gọi `agile-devops` cập nhật cấu hình đóng gói Docker, CI Pipeline (cưỡng chế Format/Lint/Test) và tài liệu Release/Rollback (nếu có thay đổi hạ tầng hoặc chuẩn bị phát hành).
2. Gọi **`agile-critic`** thực hiện **Phản biện Vòng 3** (`docs/05-quality-assurance/critique-reviews/sprint-N-critique.md`) để rà soát lần cuối hiện tượng lệch kiến trúc (Architecture Drift), lệch chuẩn code hoặc thiếu sót vận hành Production.
   - Nếu `agile-critic` phát hiện lỗi `Blocker` / `High Risk`, điều phối `agile-developer` hoặc `agile-devops` xử lý dứt điểm và nhờ `agile-qa` / `agile-critic` xác nhận lại.
3. Cập nhật `docs/04-sprint-management/sprint-review.md` & `sprint-retrospective.md`.
4. **Đánh giá model của Sprint**: tổng hợp `docs/04-sprint-management/model-performance.md` theo vai trò–model (vòng sửa, lỗi bị phát hiện, báo cáo sai sự thật, lần hết quota). Nếu có vai trò cần đổi model chính, đưa đề xuất kèm số liệu vào báo cáo Gate 3 để người dùng quyết định.
5. Trình bày báo cáo **Gate 3** cho người dùng.
