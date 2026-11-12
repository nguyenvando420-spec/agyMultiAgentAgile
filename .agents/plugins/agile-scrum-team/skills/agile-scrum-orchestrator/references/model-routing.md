# Phân Công Model Cho 12 Vai Trò (Model Routing)

> Dựa trên khảo sát ngày 11/11/2026 (bộ đề trong `benchmark/` của framework) và mở rộng cho 4 vai trò chuyên sâu về AI / SLM / MLOps. Khi danh sách model thay đổi, chạy lại benchmark và cập nhật bảng này.
>
> ✅ **Người dùng đã duyệt bảng phân công gốc (8 vai trò) ngày 11/11/2026** và cho phép Scrum Master **tự chuyển sang model dự phòng khi hết quota** (xem mục 5). Mọi thay đổi model **chính** dựa trên đánh giá thực tế (mục 6) phải được người dùng duyệt tại Gate.
>
> ✅ **4 vai trò AI được người dùng duyệt ngày 12/11/2026** sau benchmark riêng (`benchmark-ai/`, kết quả ở mục 7). Người dùng cũng yêu cầu làm benchmark v2 khó hơn để tách 5 model mạnh; nếu v2 cho kết quả khác, đề xuất đổi sẽ trình lại người dùng.

## 1. Bảng phân công khuyến nghị (14 Vai trò: Scrum Master + 12 Subagents + Codex)

| Vai trò | Model chính | Dự phòng (hết quota / chậm) | Căn cứ |
|---|---|---|---|
| `agile-scrum-master` (Dual-mode: Main Agent trực tiếp hoặc Subagent điều phối) | `claude-opus-5-5-high` | `claude-sonnet-5-5-high` | Là model người dùng chọn trong UI (hoặc ghim khi gọi riêng). Cần phán đoán, lập Sprint Backlog, đóng gói Context Packet & kiểm chứng bàn giao |
| `agile-researcher` | `claude-opus-5-5-high` | `claude-sonnet-5-5-high` | Nghiên cứu: dẫn chứng hệ thống & kiến trúc AI thực tế chính xác nhất (10.5/11) |
| `agile-po-ba` | `claude-sonnet-5-5-high` | `gemini-4-carbon-high` | Phân tích nghiệp vụ 14/14, nhanh |
| `agile-tech-lead` | `claude-sonnet-5-5-high` | `gemini-4-argon-high` | Tuân thủ định dạng 8/8, phản biện 11/11, chọn stack & chuẩn code nhanh |
| `agile-architect` | `claude-opus-5-5-high` | `gemini-4-argon-high` | Phản biện 11/11 + nghiên cứu 10.5/11, thiết kế C4 & AI Pipeline sâu |
| `agile-critic` | `gemini-4-carbon-high` | `gemini-4-argon-high` | Phản biện 11/11, phát hiện sâu nhất; **khác họ model với tác giả** |
| `agile-developer` | `claude-sonnet-5-5-high` | `gemini-4-argon-high` | Code 36/36, nhanh nhất trong nhóm mạnh |
| `agile-developer` (story đơn giản, đặc tả rõ) | `gemini-3.8-flash-high` | `claude-sonnet-5-5-medium` | Code 36/36, nhanh, rẻ; yếu hơn ở suy luận mở |
| `agile-ai-data-engineer` | `claude-sonnet-5-5-high` | `gemini-4-argon-high` | ✅ Duyệt 12/11/2026. Benchmark AI: 5 model hòa điểm tối đa → chọn theo nguyên tắc: MLOps-Eval (Gemini) kiểm tra lại rò rỉ dữ liệu của vai trò này nên tác giả phải khác họ (xem mục 7) |
| `agile-slm-trainer` | `claude-opus-5-5-high` | `claude-sonnet-5-5-high` | ✅ Duyệt 12/11/2026. Benchmark AI: I 16/16 (5 model hòa); giữ Claude để khác họ với MLOps-Eval |
| `agile-ai-engineer` | `claude-sonnet-5-5-high` | `gemini-4-argon-high` | ✅ Duyệt 12/11/2026. Benchmark AI: J 19/19 (5 model hòa), nhanh nhất nhóm đạt tối đa (75 s) |
| `agile-qa` | `gemini-4-argon-high` | `gemini-4-carbon-high` | Mutation test 8/8; **khác họ với Developer** để kiểm thử độc lập |
| `agile-mlops-eval` | `gemini-4-carbon-high` | `gemini-4-argon-high` | ✅ Duyệt 12/11/2026. Benchmark AI: K1 4/4 + K2 12/12 (5 model hòa); Gemini để khác họ với mọi tác giả AI (Claude) |
| `agile-devops` | `gemini-3.8-flash-high` | `gemini-4-argon-high` | Dockerfile & CI/CD 8/8, nhanh |
| `agile-codex` (ngoài Antigravity) | `gpt-6.1-sol` qua Codex CLI (theo `~/.codex/config.toml`) | — (hết quota ChatGPT thì bỏ qua lượt Codex, ghi chú; Critic vẫn chạy) | ✅ Người dùng thêm 12/11/2026. **Họ model thứ 3** (OpenAI) khác cả tác giả (Claude) và Critic/QA (Gemini). Quota riêng. Chỉ đọc. Gọi qua `scripts/codex_task.py`, không qua swarm/`invoke_subagent` |

**Không khuyến nghị** `gpt-oss-120b-medium` cho vai trò nào: tự bịa yêu cầu không có trong đặc tả (test QA fail cả trên code đúng), đề xuất sửa lỗi sai (bọc BEGIN/COMMIT không chống được lost update).

## 2. Nguyên tắc phân công

1. **Phản biện khác họ model với tác giả**: tác giả Gate 1 & 2 dùng Claude, Critic dùng Gemini. Tránh hai model cùng họ có chung điểm mù.
2. **QA & MLOps-Eval khác họ với người phát triển**:
   - `agile-developer` / `agile-ai-engineer` / `agile-slm-trainer` / `agile-ai-data-engineer` (họ Claude) ↔ `agile-qa` / `agile-mlops-eval` (họ Gemini).
3. **Chia đều 2 nhóm quota**: Claude + GPT-OSS dùng chung một nhóm quota, Gemini dùng nhóm còn lại. Bảng trên chia việc ra cả hai nhóm.
4. **Đổi sang dự phòng khi hết quota**, không đổi vai trò. Ghi lại model thực tế đã dùng vào `agile-state.md`.

## 3. Cách ghim model cho vai trò trong Antigravity (đã kiểm chứng)

| Cách | Chọn được model cụ thể? | Ghi file? | Dùng khi |
|---|---|---|---|
| **A. Swarm** (`swarm add` với `model`) | ✅ Cả 16 model | ✅ Theo quyền bình thường của phiên | **Cách chính** khi người dùng muốn mỗi vai trò một model |
| **B. `agy -p --agent <vai trò> --model <id>`** (chạy qua terminal) | ✅ | ❌ Chế độ headless tự từ chối quyền ghi, trừ khi người dùng thêm allow-rule trong `settings.json` | Vai trò chỉ cần trả về văn bản: Researcher, Critic. Scrum Master tự ghi kết quả ra file |
| **C. `invoke_subagent`** / frontmatter `model:` | ❌ Chỉ nhận tier `flash_lite`/`flash`/`pro`/`inherit` | ✅ | Khi không cần chọn model cụ thể |

### A. Swarm (khuyến nghị)
- Mỗi vai trò là một worker, đặt tên theo vai trò, ghim model theo bảng ở mục 1:
  `swarm{action:"add", name:"slm-trainer", model:"claude-opus-5-5-high", brief:"..."}`
- Worker bắt đầu từ đầu, không thấy cuộc trò chuyện, nên brief phải có:
  1. "Bạn là `agile-<vai trò>`. Đọc và tuân thủ `.agents/plugins/agile-scrum-team/agents/agile-<vai trò>.md`."
  2. Context Packet theo [handoff-prompts.md](./handoff-prompts.md), ghi rõ Gate nào đã được duyệt.
  3. Báo kết quả cho ai (`@coordinator` hoặc vai trò kế tiếp).
- Developer, AI Engineer, AI Data Engineer, SLM Trainer chạy song song dùng `workspace:"share"`. Researcher, Critic, QA, MLOps-Eval để `inherit`.
- Chỉ thêm worker khi tới lượt vai trò đó. Worker chờ không tốn quota, nhưng mỗi tin nhắn trên board đều được đọc.

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
   - Hoặc `quota_remaining` của model < 10% trước một việc lớn (viết code cả Sprint, huấn luyện/tối ưu model, phản biện toàn bộ thiết kế).
3. **Chuyển sang đâu**: model dự phòng của đúng vai trò đó trong bảng mục 1. Nếu dự phòng cũng thấp, chọn model mạnh nhất còn quota **trong họ model khác với tác giả** (giữ nguyên tắc Critic/QA/MLOps-Eval độc lập).
4. **Cách chuyển**: `swarm{action:"model", name:"<worker>", model:"<model dự phòng>"}`. Worker **giữ nguyên hội thoại**, không `kill` rồi `add` lại. Chỉ chuyển được khi worker đang `waiting`.
5. **Báo người dùng** ngay trong câu trả lời kế tiếp: model nào hết quota, đã chuyển vai trò nào sang model nào, thời điểm quota reset.
6. **Ghi lại** vào `agile-state.md` (cột Model) và `model-performance.md` (mục Nhật ký chuyển model).
7. **Quay lại model chính** sau thời điểm `quota_resets`, nhưng chỉ ở ranh giới nhiệm vụ (giữa 2 việc), không chuyển giữa chừng một việc.

## 6. Đánh Giá Thực Tế Trong Dự Án

Ghi vào `docs/04-sprint-management/model-performance.md` (mẫu: [model-performance-template.md](./model-performance-template.md)):

1. **Sau mỗi lần một vai trò bàn giao**, Scrum Master ghi 1 dòng gồm vai trò, model, nhiệm vụ và các chỉ số khách quan:
   - **Số vòng phải sửa** theo yêu cầu của Critic / QA / MLOps-Eval.
   - **Lỗi Critic/QA/MLOps-Eval phát hiện** trong sản phẩm của vai trò đó (theo mức Blocker/High/Medium).
   - **Báo cáo sai sự thật**: agent nói đã làm (ghi file, test pass, benchmark model đạt) nhưng kiểm tra lại thì không đúng. **Chỉ số này quan trọng nhất.** Scrum Master phải tự kiểm chứng (mở file, chạy lại test/eval) trước khi chấp nhận bàn giao.
   - **Thời gian** hoàn thành và **có bị hết quota** hay không.
   - **Phản hồi của người dùng tại Gate** về sản phẩm của vai trò đó.
2. **Tại mỗi Gate 3 (Sprint Review)**, tổng hợp theo vai trò–model. Nếu một vai trò có ≥ 1 báo cáo sai sự thật, hoặc liên tục phải sửa ≥ 2 vòng, hoặc bị người dùng chê lặp lại, thì **đề xuất đổi model chính**, kèm số liệu và model thay thế.
3. **Chỉ đổi model chính khi người dùng duyệt.** Khi người dùng duyệt, cập nhật bảng mục 1 của file này (ghi ngày + lý do) để các dự án sau dùng lại.

## 7. Kết Quả Benchmark Vai Trò AI (12/11/2026)

Bộ đề: `benchmark-ai/` ở gốc framework (H: Data Engineer, I: SLM Trainer, J: AI Engineer, K: MLOps-Eval). Gắn với phần cứng thật của người dùng (Colab/Kaggle T4 → RTX 2060 6 GB). Bộ chấm tự động đã tự kiểm tra (bài mẫu đúng đạt tối đa, bài cố tình sai bị trừ). K2 chấm mù, ghi điểm trước khi mở bảng tên.

| Model | H /17 | I /16 | J /19 | K1 /4 | K2 /12 (mù) | Thời gian |
|---|---|---|---|---|---|---|
| `claude-opus-5-5-high` | 17 | 16 | 19 | 4 | 12 | 92 s |
| `claude-sonnet-5-5-high` | 17 | 16 | 19 | 4 | 12 | 75 s |
| `gemini-4-carbon-high` | 17 | 16 | 19 | 4 | 12 | 436 s |
| `gemini-4-argon-high` | 17 | 16 | 19 | 4 | 12 | 203 s |
| `gemini-3.8-flash-high` | 17 | 16 | 19 | 4 | 12 | 132 s |
| `gpt-oss-120b-medium` | 15 | 9 | 17 | 4 | 4 | 40 s |

**Kết luận trung thực:**
- **Bộ đề bị "chạm trần"**: 5 model mạnh đều đạt tối đa mọi bài, kể cả bài tự luận. Benchmark **không phân biệt được chất lượng** giữa 5 model này. Phân công ở mục 1 vì vậy dựa trên **nguyên tắc** (khác họ model giữa tác giả và người chấm, chia quota, tốc độ), không dựa trên chênh lệch điểm.
- **GPT-OSS tiếp tục không khuyến nghị**, có lỗi cụ thể đúng vào rủi ro của người dùng: đặt `bf16=true` trên T4 (không hỗ trợ), **dùng Golden Test để early-stop** (rò rỉ test), checkpoint không ghi vào `/kaggle/working`/không resume; bỏ sót khử trùng sau khi ẩn PII; K2 bỏ sót 8/12 lỗi phương pháp.
- **Thông tin định tính** (không tính điểm vì không có trong thang chốt trước): Opus và Sonnet nêu thêm nhiều lỗi hợp lệ ngoài thang (thiếu baseline/ngưỡng phát hành, ẩn PII trước khi đưa vào teacher, OOD, rollback).
- Giới hạn: mỗi model chạy 1 lần; người chấm K2 là Claude Opus 5.5 (có thể thiên vị họ Claude dù chấm mù); không đo làm việc nhiều bước hay chạy notebook thật.
- → Dữ liệu thực tế từ dự án (mục 6) sẽ là căn cứ chính để điều chỉnh. Lần sau cần đề khó hơn (nhiều bước, có bẫy tinh vi hơn) mới tách được 5 model.

**Lý do đổi đề xuất cho `agile-ai-data-engineer` (Gemini → Claude Sonnet):** `agile-mlops-eval` (Gemini) phải tự kiểm tra lại rò rỉ dữ liệu của Data Engineer. Nếu cả hai cùng họ Gemini thì mất tính độc lập (mục 2.2). Đổi lại, nhóm quota Claude gánh thêm một vai trò; khi Claude hết quota thì dự phòng `gemini-4-argon-high` sẽ tạm mất tính độc lập họ model → ghi chú vào `agile-state.md`.

### 7b. Benchmark v2 — khó hơn, chấm tự động 100% (12/11/2026)

Bộ đề: `benchmark-ai-v2/` — repo 4 module (mỗi module một vai trò AI), **19 lỗi tinh vi + 8 bẫy** (code đúng, sửa nhầm bị trừ điểm), không chỉ ra lỗi trong đề. Bộ chấm đã tự kiểm tra (bản sửa mẫu 19/19, bài trống 0/19, bản "sửa quá tay" làm hỏng 8/8 bẫy). Mỗi model chạy 2 lần.

| Model | Data /5 | SLM /4 | AI Eng /5 | Eval /5 | Bẫy bị hỏng | Thời gian (2 lần) |
|---|---|---|---|---|---|---|
| `claude-sonnet-5-5-high` | 5, 5 | 4, 4 | 5, 5 | 5, 5 | 0, 0 | 97 s, 108 s |
| `claude-opus-5-5-high` | 5, 5 | 4, 4 | 5, 5 | 5, 5 | 0, 0 | 172 s, 156 s |
| `gemini-3.8-flash-high` | 5, 5 | 4, 4 | 5, 5 | 5, 5 | 0, 0 | 186 s, 194 s |
| `gemini-4-argon-high` | 5, 5 | 4, 4 | 5, 5 | 5, 5 | 0, 0 | 387 s, 307 s |
| `gemini-4-carbon-high` | 5, 5 | 4, 4 | 5, 5 | 5, 5 | 0, 0 | 656 s, 686 s |

**Kết luận:** v2 cũng chạm trần — cả 10 lần chạy đều sửa đủ 19 lỗi và không làm hỏng bẫy nào. Với dạng bài **một lượt, ngữ cảnh ≤ ~14 nghìn ký tự, có hợp đồng rõ ràng**, 5 model mạnh ngang nhau về chất lượng. Khác biệt đo được duy nhất là **tốc độ** (Sonnet nhanh nhất, Carbon chậm hơn ~6 lần).
- → **Giữ nguyên bảng đã duyệt** ở mục 1 (không có bằng chứng để đổi).
- ✅ **Người dùng quyết định ngày 12/11/2026: không làm thêm benchmark; dùng số liệu thực tế từ dự án (mục 6) làm căn cứ chính** để giữ/đổi model. Ghi vào `docs/04-sprint-management/model-performance.md`, kể cả bảng chỉ số riêng cho vai trò AI. Được đề xuất đổi sang model nhanh hơn cùng họ nếu chất lượng ngang nhau mà tốc độ làm trễ Sprint (chỉ đổi khi người dùng duyệt).
- Muốn tách được 5 model cần bài **nhiều bước có dùng công cụ** trên repo lớn (agent tự đọc file, tự chạy test, sửa qua nhiều vòng). Chế độ headless của `agy` tự từ chối công cụ, nên cần **người dùng tự thêm allow-rule** trong `settings.json` thì mới chạy được dạng bài này. Hoặc dựa vào số liệu thực tế từ dự án (mục 6) — đây là nguồn đáng tin nhất.
