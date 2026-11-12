# Hồ Sơ Phần Cứng & Hạ Tầng Tính Toán AI (Compute Profile)

> **Người dùng chốt ngày 12/11/2026**: Huấn luyện / tinh chỉnh model chỉ dùng **Google Colab** và **Kaggle**. Model sau cùng phải **chạy suy luận được trên tối thiểu RTX 2060 6 GB** (máy của người dùng).
> Mọi vai trò AI (`agile-tech-lead`, `agile-architect`, `agile-ai-data-engineer`, `agile-slm-trainer`, `agile-ai-engineer`, `agile-mlops-eval`, `agile-critic`) **bắt buộc** thiết kế và kiểm chứng trong giới hạn của file này. Đề xuất vượt giới hạn phải ghi rõ là ngoại lệ và chờ người dùng duyệt tại Gate.
>
> Số liệu Colab/Kaggle tra cứu ngày 12/11/2026. Hai nền tảng thay đổi giới hạn không báo trước → kiểm lại khi bắt đầu dự án.

## 1. Ba môi trường

| Môi trường | Vai trò | GPU | VRAM | RAM hệ thống | Giới hạn thời gian | Lưu trữ |
|---|---|---|---|---|---|---|
| **Google Colab (Free)** | Huấn luyện / thử nghiệm | 1× T4 (Turing, sm_75) — *chỉ khi còn GPU trống* | ~15 GB | ~12.7 GB | Tối đa 12 giờ/phiên, **có thể bị ngắt sớm hơn**; ngắt khi bỏ trống (thường ~90 phút); dùng nhiều sẽ bị khóa GPU vài giờ–vài ngày | Đĩa VM **bị xóa khi ngắt phiên** → checkpoint lên **Google Drive** |
| **Kaggle Notebooks** | Huấn luyện chính (ổn định hơn Colab) | 2× T4 *hoặc* 1× P100 (Pascal) | 16 GB mỗi GPU | ~29 GB | **30 giờ GPU/tuần** (dùng chung cho mọi loại GPU); tối đa 12 giờ/phiên; ngắt sau **20 phút** bỏ trống | `/kaggle/working` (~20 GB) được giữ lại khi chạy "Save & Run All"; dữ liệu vào bằng Kaggle Datasets |
| **Máy người dùng — mức sàn triển khai** | Suy luận / đánh giá / demo | RTX 2060 (Turing, sm_75) | **6 GB** | ~16 GB | Không giới hạn | Ổ cục bộ |

## 2. Hệ quả kỹ thuật bắt buộc

### Chung cho cả 3 môi trường (đều là kiến trúc Turing/Pascal)
- **Không có bf16** → dùng `fp16` (mixed precision) hoặc 4-bit. Cấu hình `bf16=True` sẽ lỗi hoặc chạy giả lập rất chậm.
- **Không có FlashAttention-2** (cần Ampere trở lên) → dùng SDPA mặc định của PyTorch hoặc kernel của Unsloth/xformers hỗ trợ Turing.
- **Tránh P100 trên Kaggle cho QLoRA**: Pascal không có Tensor Core, fp16 chậm và nhiều thư viện 4-bit/Unsloth hỗ trợ kém. Ưu tiên chọn **T4** (nếu dùng 2× T4: hoặc DDP, hoặc chỉ dùng 1 GPU cho đơn giản; không giả định NVLink).

### Huấn luyện trên Colab/Kaggle
- **Ngân sách thực tế cho 1 lần huấn luyện**: ≤ ~10 giờ (chừa biên trước mốc 12 giờ). Tổng một Sprint không vượt **30 giờ GPU Kaggle/tuần** + phần Colab không đảm bảo.
- **QLoRA 4-bit** là mặc định. Khả thi trên T4 16 GB: model **≤ 8B** (seq_len vừa phải, batch nhỏ + gradient accumulation + gradient checkpointing). **Full fine-tune** chỉ hợp lý với model ≤ ~0.5B.
- **Chịu được việc bị ngắt phiên**: `save_steps` sao cho mất tối đa ~30 phút công; ghi checkpoint ra Drive / `/kaggle/working`; script phải **resume từ checkpoint mới nhất** (`resume_from_checkpoint`).
- **Tái lập được**: notebook tự cài đúng phiên bản thư viện (pin trong ô đầu tiên), cố định seed, ghi log metrics ra file (không chỉ in ra màn hình).
- **Không làm trò lách luật**: không dùng script giả lập thao tác chuột/bàn phím để tránh bị ngắt phiên (vi phạm điều khoản Colab). Muốn chạy lâu thì dùng "Save & Run All" của Kaggle.

### Triển khai trên RTX 2060 6 GB (mức sàn)
- **Ngân sách VRAM cho suy luận: ≤ 5 GB** (chừa ~1 GB cho driver/desktop), **đã tính KV cache ở độ dài ngữ cảnh mục tiêu**.
- Hướng dẫn chọn cỡ model (định dạng GGUF qua llama.cpp, hoặc AWQ/GPTQ 4-bit):

| Cỡ model | Q4_K_M (ước lượng file) | Vừa 6 GB? |
|---|---|---|
| 0.5B–1.5B | ~0.4–1.0 GB | ✅ Thoải mái, ngữ cảnh dài |
| 3B–4B | ~2.0–2.5 GB | ✅ Khuyến nghị mặc định |
| 7B–8B | ~4.4–4.9 GB | ⚠️ Rất sát: chỉ ngữ cảnh ngắn hoặc phải đẩy bớt layer sang CPU (chậm). **Không chọn làm mặc định.** |
| > 8B | — | ❌ Không đạt |

- Encoder/embedding/reranker (BERT, bge-small/m3, …) và mô hình thị giác nhỏ (YOLO-n/s) chạy song song cũng phải cộng vào ngân sách 5 GB.
- **Python trên máy hiện là 3.9** (quá cũ với thư viện AI mới) → đánh giá cục bộ chạy trong **Docker** (máy đã có Docker) hoặc cài Python ≥ 3.10 trong venv riêng. Không nâng cấp Python hệ thống khi chưa hỏi người dùng.

## 3. Phân công thực thi (ai chạy cái gì, ở đâu)

| Việc | Ai viết | Chạy ở đâu | Ai kiểm chứng |
|---|---|---|---|
| Notebook huấn luyện / chưng cất / lượng tử hóa | `agile-slm-trainer` | Colab / Kaggle | `agile-mlops-eval` + Scrum Master đọc log metrics |
| Notebook sinh dữ liệu tổng hợp nặng (cần GPU) | `agile-ai-data-engineer` | Colab / Kaggle | `agile-mlops-eval` (kiểm rò rỉ dữ liệu) |
| Đánh giá trên Golden Test Set + đo hiệu năng | `agile-mlops-eval` | **RTX 2060 6 GB** (đúng phần cứng đích) | Scrum Master chạy lại lệnh |

- Agent **không tự đăng nhập** Colab. Agent tạo notebook `.ipynb` + hướng dẫn; **người dùng bấm chạy** và trả lại file log/metrics + artifact (Drive/Kaggle output).
- Với Kaggle, có thể chạy tự động qua **Kaggle CLI chính thức** (`kaggle kernels push` / `kaggle kernels output`) **chỉ khi người dùng đã tự cấu hình API token** của họ. Agent không tạo, xin hay đọc token thay người dùng.
- Kết quả huấn luyện chỉ được chấp nhận khi có **file log metrics thật** từ phiên chạy (không chấp nhận số liệu agent tự báo).
