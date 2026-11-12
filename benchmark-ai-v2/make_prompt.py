"""Sinh prompt.md cho benchmark v2 từ các file trong repo/ (để đề và repo luôn khớp nhau)."""
import os

B = os.path.dirname(os.path.abspath(__file__))
FILES = ["mlkit/data_prep.py", "mlkit/train_plan.py", "mlkit/llm_call.py", "mlkit/eval_metrics.py", "tests/test_public.py"]

HEAD = """KHÔNG sử dụng bất kỳ công cụ nào (không đọc/ghi file, không chạy lệnh, không tìm web). Trả lời TOÀN BỘ trong MỘT câu trả lời duy nhất. Văn xuôi bằng tiếng Việt, ngắn gọn.

Bạn là kỹ sư AI cấp cao, rà soát repo `mlkit` trước khi lên Production. Repo phục vụ một model phân loại ý định CSKH tiếng Việt:
- Huấn luyện QLoRA trên Google Colab / Kaggle (GPU T4, có lúc P100); phiên tối đa 12 giờ, có thể bị ngắt.
- Triển khai suy luận bằng llama.cpp trên RTX 2060 6 GB.
- Docstring đầu module và docstring từng hàm là HỢP ĐỒNG đã được duyệt.

NHIỆM VỤ: tìm và sửa MỌI lỗi khiến code vi phạm hợp đồng hoặc gây rủi ro thật cho hệ thống AI này (rò rỉ dữ liệu, sai phần cứng, sai chỉ số đánh giá, lỗ hổng an toàn...).
- KHÔNG sửa những gì đã đúng: mỗi thay đổi làm hỏng một hành vi đang đúng đều bị trừ điểm.
- Giữ nguyên tên module, tên hàm, tham số, giá trị mặc định và kiểu trả về. Chỉ dùng thư viện chuẩn Python 3.9.
- `tests/test_public.py` chỉ là vài test mẫu, không bao phủ các lỗi.

ĐỊNH DẠNG ĐẦU RA (bắt buộc):
1. Một dòng `=== FINDINGS ===`, sau đó mỗi lỗi một dòng: `file:hàm → vấn đề → cách sửa`.
2. Một dòng `=== FILES ===`, sau đó TOÀN BỘ nội dung MỚI của từng file trong `mlkit/` mà bạn sửa. Mỗi file một khối, mở bằng đúng dòng ```python file=mlkit/<tên_file>.py và đóng bằng một dòng chỉ có ```. File không sửa thì không in.

=== REPO ===
"""


def main():
    parts = [HEAD]
    for rel in FILES:
        with open(os.path.join(B, "repo", rel), encoding="utf-8") as f:
            parts.append("--- FILE: %s ---\n```python\n%s```\n" % (rel, f.read()))
    with open(os.path.join(B, "prompt.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("prompt.md written")


if __name__ == "__main__":
    main()
