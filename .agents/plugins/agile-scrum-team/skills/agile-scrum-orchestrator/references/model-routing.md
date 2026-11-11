# Phân Công Model Cho Từng Vai Trò (Model Routing)

> Dựa trên khảo sát ngày 11/11/2026 (bộ đề trong `benchmark/` của framework). Khi danh sách model thay đổi, chạy lại benchmark và cập nhật bảng này.
>
> ✅ **Người dùng đã duyệt bảng phân công này ngày 11/11/2026** và cho phép Scrum Master **tự chuyển sang model dự phòng khi hết quota** (xem mục 5). Mọi thay đổi model **chính** dựa trên đánh giá thực tế (mục 6) phải được người dùng duyệt tại Gate.

## 1. Bảng phân công khuyến nghị

| Vai trò | Model chính | Dự phòng (hết quota / chậm) | Căn cứ |
|---|---|---|---|
| Scrum Master (Main Agent) | `claude-opus-5-5-high` | `claude-sonnet-5-5-high` | Là model người dùng chọn trong UI. Cần phán đoán & điều phối |
| `agile-researcher` | `claude-opus-5-5-high` | `claude-sonnet-5-5-high` | Nghiên cứu: dẫn chứng hệ thống thực tế chính xác nhất (10.5/11) |
| `agile-po-ba` | `claude-sonnet-5-5-high` | `gemini-4-carbon-high` | Phân tích nghiệp vụ 14/14, nhanh |
| `agile-tech-lead` | `claude-sonnet-5-5-high` | `gemini-4-argon-high` | Tuân thủ định dạng 8/8, phản biện 11/11, nhanh |
| `agile-architect` | `claude-opus-5-5-high` | `gemini-4-argon-high` | Phản biện 11/11 + nghiên cứu 10.5/11 |
| `agile-critic` | `gemini-4-carbon-high` | `gemini-4-argon-high` | Phản biện 11/11, phát hiện sâu nhất; **khác họ model với tác giả** |
| `agile-developer` | `claude-sonnet-5-5-high` | `gemini-4-argon-high` | Code 36/36, nhanh nhất trong nhóm mạnh |
| `agile-developer` (story đơn giản, đặc tả rõ) | `gemini-3.8-flash-high` | `claude-sonnet-5-5-medium` | Code 36/36, nhanh, rẻ; yếu hơn ở suy luận mở |
| `agile-qa` | `gemini-4-argon-high` | `gemini-4-carbon-high` | Mutation test 8/8; **khác họ với Developer** để kiểm thử độc lập |
| `agile-devops` | `gemini-3.8-flash-high` | `gemini-4-argon-high` | Dockerfile 8/8, nhanh |

**Không khuyến nghị** `gpt-oss-120b-medium` cho vai trò nào: tự bịa yêu cầu không có trong đặc tả (test QA fail cả trên code đúng), đề xuất sửa lỗi sai (bọc BEGIN/COMMIT không chống được lost update).

## 2. Nguyên tắc phân công

1. **Phản biện khác họ model với tác giả**: tác giả Gate 1 & 2 dùng Claude, Critic dùng Gemini. Tránh hai model cùng họ có chung điểm mù.
2. **QA khác họ với Developer**: Developer Claude ↔ QA Gemini.
3. **Chia đều 2 nhóm quota**: Claude + GPT-OSS dùng chung một nhóm quota, Gemini dùng nhóm còn lại. Bảng trên chia việc ra cả hai nhóm.
4. **Đổi sang dự phòng khi hết quota**, không đổi vai trò. Ghi lại model thực tế đã dùng vào `agile-state.md`.

## 3. Cách ghim model cho vai trò trong Antigravity (đã kiểm chứng)

| Cách | Chọn được model cụ thể? | Ghi file? | Dùng khi |
|---|---|---|---|
| **A. Swarm** (`swarm add` với `model`) | ✅ Cả 16 model | ✅ Theo quyền bình thường của phiên | **Cách chính** khi người dùng muốn mỗi vai trò một model |
| **B. `agy -p --agent <vai trò> --model <id>`** (chạy qua terminal) | ✅ | ❌ Chế độ headless tự từ chối quyền ghi, trừ khi người dùng thêm allow-rule trong `settings.json` | Vai trò chỉ cần trả về văn bản: Researcher, Critic. Scrum Master tự ghi kết quả ra file |
| **C. `invoke_subagent`** / frontmatter `model:` | ❌ Chỉ nhận tier `flash_lite`/`flash`/`pro`/`inherit` (khi thử, cả 3 tier đều tự báo là Gemini 3.8 Flash) | ✅ | Khi không cần chọn model cụ thể |

### A. Swarm (khuyến nghị)
- Mỗi vai trò là một worker, đặt tên theo vai trò, ghim model theo bảng ở mục 1:
  `swarm{action:"add", name:"critic", model:"gemini-4-carbon-high", brief:"..."}`
- Worker bắt đầu từ đầu, không thấy cuộc trò chuyện, nên brief phải có:
  1. "Bạn là `agile-<vai trò>`. Đọc và tuân thủ `.agents/plugins/agile-scrum-team/agents/agile-<vai trò>.md`."
  2. Context Packet theo [handoff-prompts.md](./handoff-prompts.md), ghi rõ Gate nào đã được duyệt.
  3. Báo kết quả cho ai (`@coordinator` hoặc vai trò kế tiếp).
- Developer chạy song song dùng `workspace:"share"`. Researcher, Critic, QA để `inherit`.
- Chỉ thêm worker khi tới lượt vai trò đó. Worker chờ không tốn quota, nhưng mỗi tin nhắn trên board đều được đọc. Thêm Developer theo số gói việc độc lập.
- Swarm đang ở bản Preview và tốn quota hơn subagent thường.

### B. Headless qua terminal
```bash
agy -p "<Context Packet>" --agent agile-critic --model gemini-4-carbon-high --print-timeout 900s > /tmp/critic.md
```
Chạy nền, đọc output, Scrum Master tự ghi vào `docs/05-quality-assurance/critique-reviews/`. Không dùng `--dangerously-skip-permissions` nếu người dùng chưa đồng ý rõ ràng.

## 4. Giới hạn của khảo sát
- Mỗi model chỉ chạy 1 lần, ở mức effort High (GPT-OSS chỉ có Medium). Chưa đo Low/Medium.
- Bài khách quan (code, test, JSON, Dockerfile) bị "chạm trần": 4 model mạnh đều gần tối đa. Chênh lệch giữa 4 model đầu (95–100%) nằm trong sai số chấm.
- Chỉ đo trả lời một lượt, chưa đo khả năng làm việc nhiều bước với công cụ trên codebase thật.
- Người chấm bài tự luận là một model Claude. Đã chấm mù theo thang chốt trước, nhưng vẫn có thể còn thiên vị.

→ Vì vậy bảng ở mục 1 chỉ là **điểm xuất phát**. Dữ liệu thực tế từ dự án (mục 6) có giá trị hơn benchmark.

## 5. Chuyển Model Khi Hết Quota (Người dùng đã cho phép tự làm)

1. **Kiểm tra trước khi giao việc lớn**: gọi `swarm{action:"models"}` để xem `quota_remaining` và `quota_resets` của model sắp dùng.
2. **Khi nào chuyển**:
   - Lượt làm việc của worker lỗi do hết quota, hoặc worker nhận cảnh báo `[quota]`.
   - Hoặc `quota_remaining` của model < 10% trước một việc lớn (viết code cả Sprint, phản biện toàn bộ thiết kế).
3. **Chuyển sang đâu**: model dự phòng của đúng vai trò đó trong bảng mục 1. Nếu dự phòng cũng thấp, chọn model mạnh nhất còn quota **trong họ model khác với tác giả** (giữ nguyên tắc Critic/QA độc lập). Nếu không còn lựa chọn nào, để worker chạy trên model của Scrum Master và ghi chú "mất tính độc lập họ model".
4. **Cách chuyển**: `swarm{action:"model", name:"<worker>", model:"<model dự phòng>"}`. Worker **giữ nguyên hội thoại**, không `kill` rồi `add` lại. Chỉ chuyển được khi worker đang `waiting`.
5. **Báo người dùng** ngay trong câu trả lời kế tiếp: model nào hết quota, đã chuyển vai trò nào sang model nào, thời điểm quota reset.
6. **Ghi lại** vào `agile-state.md` (cột Model) và `model-performance.md` (mục Nhật ký chuyển model).
7. **Quay lại model chính** sau thời điểm `quota_resets`, nhưng chỉ ở ranh giới nhiệm vụ (giữa 2 việc), không chuyển giữa chừng một việc.

## 6. Đánh Giá Thực Tế Trong Dự Án

Ghi vào `docs/04-sprint-management/model-performance.md` (mẫu: [model-performance-template.md](./model-performance-template.md)):

1. **Sau mỗi lần một vai trò bàn giao**, Scrum Master ghi 1 dòng gồm vai trò, model, nhiệm vụ và các chỉ số khách quan:
   - **Số vòng phải sửa** theo yêu cầu của Critic / QA.
   - **Lỗi Critic/QA phát hiện** trong sản phẩm của vai trò đó (theo mức Blocker/High/Medium).
   - **Báo cáo sai sự thật**: agent nói đã làm (ghi file, test pass) nhưng kiểm tra lại thì không đúng. **Chỉ số này quan trọng nhất.** Scrum Master phải tự kiểm chứng (mở file, chạy lại test) trước khi chấp nhận bàn giao.
   - **Thời gian** hoàn thành và **có bị hết quota** hay không.
   - **Phản hồi của người dùng tại Gate** về sản phẩm của vai trò đó.
2. **Tại mỗi Gate 3 (Sprint Review)**, tổng hợp theo vai trò–model. Nếu một vai trò có ≥ 1 báo cáo sai sự thật, hoặc liên tục phải sửa ≥ 2 vòng, hoặc bị người dùng chê lặp lại, thì **đề xuất đổi model chính**, kèm số liệu và model thay thế.
3. **Chỉ đổi model chính khi người dùng duyệt.** Khi người dùng duyệt, cập nhật bảng mục 1 của file này (ghi ngày + lý do) để các dự án sau dùng lại.
