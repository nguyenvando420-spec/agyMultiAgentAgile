# Phân Công Model Cho 14 Vai Trò & Tác Vụ Liên Quan (Model Routing)

> Dựa trên khảo sát gốc ngày 11/11/2026 (`benchmark/`), mở rộng 4 vai trò AI/SLM/MLOps ngày 12/11/2026 (`benchmark-ai/`, `benchmark-ai-v2/`), và cập nhật ngày **13/11/2026** cho danh mục **21 models Antigravity (`agy 1.5.7`)** + dải **GPT-6 / 6.1 trên OpenAI Codex CLI (`codex 0.167.2`)**.
>
> ✅ **Người dùng đã duyệt bảng phân công gốc (8 vai trò) ngày 11/11/2026**, **4 vai trò AI + `agile-codex` ngày 12/11/2026**, và **duyệt bản nâng cấp bổ sung `Gemini 4 Hydrogen`, `Orchestrator` & dải `GPT-6/6.1` ngày 13/11/2026**.
>
> ✅ Scrum Master được phép **tự chuyển nóng sang model dự phòng khi hết quota** (mục 5). Mọi thay đổi **model chính** dựa trên đánh giá thực tế (mục 6) phải được người dùng duyệt.

## 1. Bảng phân công chính thức (14 Vai trò + Tác vụ Chuyên biệt)

| Vai trò / Tác vụ | Model chính | Dự phòng (hết quota / quá tải — theo thứ tự ưu tiên) | Căn cứ |
|---|---|---|---|
| `agile-scrum-master` *(Dual-mode: Main Agent trực tiếp hoặc Subagent điều phối)* | `claude-opus-5-5-high` *(hoặc theo model người dùng chọn trên UI)* | **`gemini-pro-orchestrator`** → `gemini-4-carbon-high` *(hoặc `claude-sonnet-5-5-high` nếu hạ bậc trong giỏ Claude)* | ✅ Cập nhật 13/11/2026. `Orchestrator` chuyên biệt cho điều phối Swarm/Subagents và khác giỏ quota với Claude |
| `agile-researcher` | `claude-opus-5-5-high` | `claude-sonnet-5-5-high` → **`gemini-4-hydrogen-xhigh`** → `gemini-4-argon-high` | Nghiên cứu 10.5/11; bổ sung dự phòng xuyên giỏ `hydrogen-xhigh` (~40 s, suy luận `xhigh`) |
| `agile-po-ba` | `claude-sonnet-5-5-high` | **`gemini-4-hydrogen-high`** → `gemini-4-carbon-high` | Phân tích nghiệp vụ 14/14; `hydrogen-high` nhanh gấp ~4× Carbon cho đồng bộ Backlog thường quy, `carbon-high` cho nghiệp vụ cực lớn |
| `agile-tech-lead` | `claude-sonnet-5-5-high` | **`gemini-4-hydrogen-xhigh`** → `gemini-4-argon-high` | Định dạng 8/8, phản biện 11/11; dự phòng `hydrogen-xhigh` kiểm soát cấu hình toolchain/linter chặt ở mức `xhigh` |
| `agile-architect` | `claude-opus-5-5-high` | **`gemini-4-hydrogen-xhigh`** → `gemini-4-argon-high` | Thiết kế C4, giao thức mạng, concurrency & AI Pipeline sâu; dự phòng xuyên giỏ `hydrogen-xhigh` |
| `agile-critic` | `gemini-4-carbon-high` | **`gemini-4-hydrogen-xhigh`** → `gemini-4-argon-high` | Phản biện sâu nhất; **khác họ model với tác giả Claude** |
| `agile-developer` *(module lõi / phức tạp: Crypto, Datapath, Async, OS)* | `claude-sonnet-5-5-high` | **`gemini-4-hydrogen-xhigh`** *(lõi khó)* → **`gemini-4-hydrogen-high`** *(chuẩn)* → `gemini-4-argon-high` | Code 36/36; khi chạy dự phòng Gemini vẫn **khác biến thể model với `agile-qa` (`argon`) & `agile-critic` (`carbon`)**, tốc độ nhanh gấp ~2× Argon |
| `agile-developer` *(story đơn giản, đặc tả rõ, CLI / Boilerplate)* | **`gemini-4-hydrogen-high`** | `gemini-3.8-flash-high` → `gemini-4-hydrogen-medium` | ✅ Nâng cấp 13/11/2026. Ngang tốc độ `3.8-flash-high` (~21 s) nhưng thuộc thế hệ **Gemini 4** mới hơn và bắt lỗi biên sâu hơn |
| `agile-ai-data-engineer` | `claude-sonnet-5-5-high` | **`gemini-4-hydrogen-high`** → `gemini-4-argon-high` | Khác họ với `agile-mlops-eval` (`carbon-high`); dự phòng `hydrogen-high` không trùng biến thể với `mlops-eval` |
| `agile-slm-trainer` | `claude-opus-5-5-high` | `claude-sonnet-5-5-high` → **`gemini-4-hydrogen-xhigh`** | Giữ họ Claude để độc lập với `mlops-eval`; bổ sung dự phòng xuyên giỏ `hydrogen-xhigh` khi cả giỏ Claude hết quota tuần |
| `agile-ai-engineer` | `claude-sonnet-5-5-high` | **`gemini-4-hydrogen-high`** → **`gemini-4-hydrogen-xhigh`** → `gemini-4-argon-high` | Nhanh nhất nhóm Claude (75 s); dự phòng `hydrogen-high` (~21 s) tối ưu khi chạy nhiều worker song song |
| `agile-qa` | `gemini-4-argon-high` | `gemini-4-carbon-high` → **`gemini-4-hydrogen-xhigh`** *(chỉ dùng `hydrogen` khi Developer không chạy trên `hydrogen`)* | Mutation test 8/8; **khác họ với Developer (Claude)** và **khác biến thể khi Developer dùng dự phòng `hydrogen`** |
| `agile-mlops-eval` | `gemini-4-carbon-high` | **`gemini-4-hydrogen-xhigh`** → `gemini-4-argon-high` | K1 4/4 + K2 12/12; chốt chặn độc lập sâu nhất khác họ với tác giả AI |
| `agile-devops` | **`gemini-4-hydrogen-high`** | `gemini-3.8-flash-high` → `gemini-4-argon-high` | ✅ Nâng cấp 13/11/2026. Tốc độ ngang `3.8-flash-high` (~21 s), thế hệ Gemini 4 bắt lỗi Dockerfile/systemd/CI/security chặt hơn |
| `agile-codex` *(ngoài Antigravity — OpenAI Codex CLI)* | `gpt-6.1-sol` (`--effort high`) | Xem **Bảng 1b** bên dưới (`gpt-6-astra`, `gpt-6.1-terra`, `gpt-6-luna`; hết quota ChatGPT thì bỏ qua lượt Codex, ghi chú; Critic vẫn chạy) | ✅ Cập nhật 13/11/2026. **Họ model thứ 3 (OpenAI)**, quota ChatGPT riêng, sandbox `read-only` + `--ephemeral`, gọi qua `scripts/codex_task.py` |
| **Tác vụ phụ trợ nhanh** *(Smoke check CLI, tiền kiểm định dạng, tóm tắt log)* | **`gemini-4-hydrogen-low`** | `gemini-3.8-flash-low` | ✅ Bổ sung 13/11/2026. Nhanh nhất toàn hệ thống (`15.52 s`), cực nhẹ quota |

### 1b. Bảng chọn Model & Mức Suy Luận Cho `agile-codex` (`codex-cli 0.167.2`)

| Kịch bản phản biện / review | Tham số `codex_task.py` khuyến nghị | Cửa sổ ngữ cảnh | Lý do |
|---|---|---|---|
| **Mặc định** (Review gói việc chuẩn, thiết kế vừa) | *(mặc định theo `~/.codex/config.toml`: `gpt-6.1-sol`, `effort=high`)* | 500K | Cân bằng tốc độ, chi phí quota ChatGPT và độ chính xác mức byte |
| **Gate 2 / Gate 3 phức tạp, giao thức mật mã, OS kernel/FFI, Race Condition khó** | `--model gpt-6-astra --effort high` *(hoặc `--model gpt-6.1-sol --effort xhigh`)* | 272K (`astra`) / 500K (`6.1-sol`) | `gpt-6-astra` là model đầu bảng (*Frontier intelligence*) của họ OpenAI cho bài toán khó nhất |
| **Review gói việc rất lớn** (nhiều crate/module, cần đọc rộng toàn workspace) | `--model gpt-6.1-terra --effort high` | 500K | Biến thể chuyên sâu Codex với ngữ cảnh 500K |
| **Review gói việc nhỏ / sửa lỗi đơn giản / tiết kiệm quota ChatGPT** | `--model gpt-6-luna --effort high` | 272K | Nhanh và tiết kiệm quota cho thay đổi nhỏ, rõ đặc tả |

**Không khuyến nghị** `gpt-oss-120b-medium` cho vai trò nào: tự bịa yêu cầu không có trong đặc tả (test QA fail cả trên code đúng), đề xuất sửa lỗi sai (bọc BEGIN/COMMIT không chống được lost update), đặt `bf16=true` trên T4 và dùng Golden Test để early-stop.

## 2. Nguyên tắc phân công & Chống đụng độ biến thể

1. **Phản biện khác họ model với tác giả**: tác giả dùng họ Claude, Critic dùng họ Gemini, `agile-codex` dùng họ OpenAI — tạo kiềng 3 chân giảm điểm mù chung.
2. **QA & MLOps-Eval khác họ với người phát triển**:
   - `agile-developer` / `agile-ai-engineer` / `agile-slm-trainer` / `agile-ai-data-engineer` (Claude) ↔ `agile-qa` / `agile-mlops-eval` (Gemini).
3. **Chia đều 3 nguồn quota**:
   - **Giỏ 1 (Antigravity — Claude + GPT-OSS)**: `claude-opus-5-5-*`, `claude-sonnet-5-5-*`, `gpt-oss-120b-medium` dùng chung hạn mức.
   - **Giỏ 2 (Antigravity — Gemini)**: `gemini-4-carbon-*`, `gemini-4-argon-*`, `gemini-4-hydrogen-*`, `gemini-pro-orchestrator`, `gemini-3.8-flash-*` dùng chung hạn mức (reset ngắn hạn nhanh).
   - **Giỏ 3 (OpenAI ChatGPT — Codex CLI)**: `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6.1-terra`, `gpt-6-luna`.
4. **Quy tắc chống tự đụng độ biến thể khi Giỏ 1 (Claude) chạm trần tuần (`0%`)**:
   - Tuyệt đối **không để Tác giả và Người chấm chạy trên cùng một biến thể Gemini**:
     - **Điều phối (`agile-scrum-master`)**: `gemini-pro-orchestrator` (hoặc model người dùng chọn).
     - **Tác giả (`developer`, `tech-lead`, `architect`, `ai-*`)**: dùng nhánh **`gemini-4-hydrogen-{xhigh,high}`**.
     - **Kiểm thử (`agile-qa`)**: cố định ở **`gemini-4-argon-high`**.
     - **Phản biện & AI Eval (`agile-critic`, `agile-mlops-eval`)**: cố định ở **`gemini-4-carbon-high`**.
     - **Đối trọng độc lập họ model thứ 3 (`agile-codex`)**: bắt buộc chạy đầy đủ ở từng Work Package và Gate 2/3 (`gpt-6.1-sol` / `gpt-6-astra`) để bù đắp tính độc lập họ model.

## 3. Cách ghim model & Tính năng Điều phối Mới (`agy 1.5.7`)

| Cách | Chọn được model cụ thể? | Ghi file? | Dùng khi |
|---|---|---|---|
| **A. Swarm** (`swarm add` với `model`) | ✅ Cả **21 model** | ✅ Theo quyền bình thường của phiên | **Cách chính** khi chạy đa model & thực thi song song |
| **B. `agy --model <id> [--effort <lvl>] -p "..."`** (qua terminal) | ✅ Cả **21 model** + `--effort` + `--json-schema` | ❌ Headless tự từ chối ghi ngoài vùng cho phép, trừ khi cấu hình allow-rule | Vai trò chỉ trả về văn bản, smoke check, hoặc script chấm tự động |
| **C. `invoke_subagent`** / frontmatter `model:` | ❌ Chỉ nhận tier `flash_lite`/`flash`/`pro`/`inherit` | ✅ | Khi không cần ghim biến thể model cụ thể |

### A. Swarm & Schedule (`agy 1.5.7` — Khuyến nghị)
- Lưu ý thực nghiệm (`agy 1.5.7`): công cụ `swarm` được gắn sẵn trong phiên **Main Agent mặc định** (không truyền `--agent`) hoặc khi khởi tạo qua `/swarm <task>`; còn khi chạy `--agent agile-scrum-master` thì có đủ `schedule`, `ask_question`, `invoke_subagent`, `define_subagent`, `manage_subagents` (lúc đó nếu cần ghim biến thể model cụ thể có thể khởi động `/swarm` hoặc gọi `agy --agent agile-<role> --model <id>`).
- Mỗi vai trò là một worker, ghim model theo bảng ở mục 1:
  `swarm{action:"add", name:"dev-crypto", model:"claude-sonnet-5-5-high", workspace:"share", brief:"..."}`
- Khi chia nhiều gói việc độc lập cùng vai trò, có thể dùng `tasks: ["WP-01 ...", "WP-02 ..."]` để tạo nhóm `<name>-1..<name>-k` trên `workspace:"share"` (giữ nguyên cả staged/unstaged/untracked changes), hoặc `fork:"<member>"` khi cần tách nhánh kế thừa ngữ cảnh.
- Worker bắt đầu từ đầu (trừ khi `fork`), nên `brief` phải có đủ: (1) persona `.agents/plugins/agile-scrum-team/agents/agile-<vai trò>.md`, (2) Context Packet theo [handoff-prompts.md](./handoff-prompts.md) kèm Gate đã duyệt, (3) báo kết quả cho `@coordinator`.
- **Không bao giờ dùng `sleep` trong shell để canh tiến trình**: dùng công cụ built-in `schedule` (`DurationSeconds` kèm `TimerCondition: "<senderId>"` hoặc `"any"` để tự hủy timer ngay khi worker/task báo xong).

## 4. Giới hạn của khảo sát
- Benchmark 1 lượt bị "chạm trần" ở nhóm model mạnh (95–100%). Khác biệt rõ nhất đo được là **tốc độ** và khả năng giữ kỷ luật qua nhiều bước dùng công cụ trên codebase thật.
- Vì vậy bảng ở mục 1 là cấu hình chuẩn xuất phát; dữ liệu thực tế từ dự án (mục 6) là căn cứ chính để tinh chỉnh tiếp.

## 5. Chuyển Model Khi Hết Quota (Người dùng đã cho phép tự làm)

1. **Kiểm tra trước khi giao việc lớn**: gọi `swarm{action:"models", all:true}` để xem `quota_remaining` và `quota_resets` của cả 21 model.
2. **Khi nào chuyển**:
   - Worker báo lỗi hết quota (`429 RESOURCE_EXHAUSTED`) hoặc tự tạm dừng do `[quota]`.
   - Hoặc `quota_remaining < 10%` trước một việc lớn (viết code cả Sprint, huấn luyện/tối ưu model, phản biện toàn bộ thiết kế).
3. **Chuyển sang đâu**: theo đúng chuỗi dự phòng của vai trò đó ở mục 1 và tuân thủ **quy tắc chống đụng độ biến thể** (mục 2.4). Lưu ý: vì `claude-opus-5-5` và `claude-sonnet-5-5` dùng chung Giỏ 1, khi Giỏ 1 về `0%` thì bỏ qua dự phòng nội bộ Claude và chuyển thẳng sang tầng dự phòng Gemini 4 (`gemini-pro-orchestrator` / `gemini-4-hydrogen-xhigh` / `gemini-4-hydrogen-high`).
4. **Cách chuyển**: `swarm{action:"model", name:"<worker>", model:"<model dự phòng>"}` (hoặc bỏ trống `name` để chuyển model cho chính coordinator). Worker **giữ nguyên hội thoại**, không `kill` rồi `add` lại. Chỉ chuyển khi worker đang `waiting`.
5. **Báo người dùng** ngay trong câu trả lời kế tiếp: giỏ model nào hết quota, đã chuyển vai trò nào sang model nào, thời điểm `quota_resets`.
6. **Ghi lại** vào `agile-state.md` (cột Model) và `model-performance.md` (mục Nhật ký chuyển model).
7. **Quay lại model chính** sau thời điểm `quota_resets`, nhưng chỉ ở ranh giới giữa 2 nhiệm vụ, không đổi giữa chừng.

## 6. Đánh Giá Thực Tế Trong Dự Án

Ghi vào `docs/04-sprint-management/model-performance.md` (mẫu: [model-performance-template.md](./model-performance-template.md)):

1. **Sau mỗi lần một vai trò bàn giao**, Scrum Master tự kiểm chứng (mở file, chạy lại lệnh test/lint/eval) rồi ghi 1 dòng gồm: vai trò, model, nhiệm vụ, số vòng phải sửa, lỗi Critic/Codex/QA/MLOps-Eval phát hiện (`B/H/M`), **báo cáo sai sự thật** (chỉ số quan trọng nhất), thời gian hoàn thành, tình trạng quota và phản hồi người dùng.
2. **Tại mỗi Gate 3 (Sprint Review)**, tổng hợp theo vai trò–model. Nếu một vai trò có ≥ 1 báo cáo sai sự thật, hoặc liên tục phải sửa ≥ 2 vòng, thì đề xuất đổi model chính kèm số liệu.
3. **Chỉ đổi model chính khi người dùng duyệt.** Khi duyệt, cập nhật mục 1 của file này (ghi ngày + lý do).

## 7. Kết Quả Benchmark Vai Trò AI (12/11/2026)

Bộ đề: `benchmark-ai/` ở gốc framework (H: Data Engineer, I: SLM Trainer, J: AI Engineer, K: MLOps-Eval), gắn với phần cứng Colab/Kaggle T4 → RTX 2060 6 GB.

| Model | H /17 | I /16 | J /19 | K1 /4 | K2 /12 (mù) | Thời gian |
|---|---|---|---|---|---|---|
| `claude-opus-5-5-high` | 17 | 16 | 19 | 4 | 12 | 92 s |
| `claude-sonnet-5-5-high` | 17 | 16 | 19 | 4 | 12 | 75 s |
| `gemini-4-carbon-high` | 17 | 16 | 19 | 4 | 12 | 436 s |
| `gemini-4-argon-high` | 17 | 16 | 19 | 4 | 12 | 203 s |
| `gemini-3.8-flash-high` | 17 | 16 | 19 | 4 | 12 | 132 s |
| `gpt-oss-120b-medium` | 15 | 9 | 17 | 4 | 4 | 40 s |

### 7b. Benchmark v2 — khó hơn, chấm tự động 100% (12/11/2026)

Bộ đề: `benchmark-ai-v2/` — repo 4 module, **19 lỗi tinh vi + 8 bẫy** (sửa nhầm bị trừ điểm), mỗi model chạy 2 lần:

| Model | Data /5 | SLM /4 | AI Eng /5 | Eval /5 | Bẫy bị hỏng | Thời gian (2 lần) |
|---|---|---|---|---|---|---|
| `claude-sonnet-5-5-high` | 5, 5 | 4, 4 | 5, 5 | 5, 5 | 0, 0 | 97 s, 108 s |
| `claude-opus-5-5-high` | 5, 5 | 4, 4 | 5, 5 | 5, 5 | 0, 0 | 172 s, 156 s |
| `gemini-3.8-flash-high` | 5, 5 | 4, 4 | 5, 5 | 5, 5 | 0, 0 | 186 s, 194 s |
| `gemini-4-argon-high` | 5, 5 | 4, 4 | 5, 5 | 5, 5 | 0, 0 | 387 s, 307 s |
| `gemini-4-carbon-high` | 5, 5 | 4, 4 | 5, 5 | 5, 5 | 0, 0 | 656 s, 686 s |

## 8. Kiểm Chứng Thực Nghiệm Nhóm Model Mới `Gemini 4 Hydrogen` & `Orchestrator` (13/11/2026)

Đối chứng song song trên cùng bài toán bắt lỗi hàm bất đồng bộ Rust (`std::sync::MutexGuard` giữ qua `.await` làm hỏng `Send`/deadlock, so sánh MAC không hằng thời gian rò rỉ timing channel, `unwrap()` poison panic, Head-of-Line blocking trên `mpsc::Sender::send().await`, hủy sớm vòng lặp broadcast bởi `?` và cấp phát dư `pkt.clone()`):

| Model | Thời gian phản hồi | Lỗi bắt được | Vị trí phân công được người dùng duyệt (13/11/2026) |
|---|---:|---|---|
| `gemini-4-hydrogen-low` | **15.52 s** | Đủ 5/5 nhóm lỗi + tối ưu move cuối vòng lặp | Tác vụ phụ trợ nhanh, smoke check CLI, tiền kiểm định dạng |
| `gemini-3.8-flash-high` *(mốc cũ)* | 20.39 s | Đủ 5/5 nhóm lỗi | Chuyển xuống làm dự phòng cho `gemini-4-hydrogen-high` |
| `gemini-4-hydrogen-high` | **20.98 s** | Đủ 5/5 nhóm lỗi + phát hiện rò rỉ sender chết | **Model chính** cho `agile-devops` & `agile-developer` (story đơn giản); **Dự phòng nhanh** cho `po-ba`, `developer`, `ai-data-engineer`, `ai-engineer` |
| `gemini-4-hydrogen-xhigh` | **39.53 s** | Đủ 5/5 nhóm lỗi + phân tích sâu mức `xhigh` | **Dự phòng xuyên giỏ (`xhigh`)** cho `researcher`, `tech-lead`, `architect`, `developer` (lõi khó), `slm-trainer`, `critic`, `mlops-eval` |
| `gemini-4-argon-high` *(mốc cũ)* | 40.67 s | Đủ 5/5 nhóm lỗi + liên hệ `SEC-05` | Giữ làm **Model chính** cho `agile-qa` (tách biệt với nhánh `hydrogen`) |
| `gemini-pro-orchestrator` | **67.35 s** | Đủ 5/5 nhóm lỗi + cảnh báo lộ chi tiết lỗi auth `"bad mac"` | **Dự phòng số 1 chuyên biệt** cho `agile-scrum-master` khi điều phối Swarm/Subagents |
| `gemini-4-carbon-high` *(mốc cũ)* | 83.03 s | Đủ 5/5 nhóm lỗi + phân tích sâu DoS stale-peer | Giữ làm **Model chính** cho `agile-critic` & `agile-mlops-eval` |
