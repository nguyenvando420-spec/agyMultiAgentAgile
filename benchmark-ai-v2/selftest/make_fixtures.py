"""Tạo đầu ra giả cho tự kiểm tra bộ chấm v2: out_ref (bản sửa tham chiếu) và out_empty (không sửa gì)."""
import os
import pathlib

B = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
FENCE = "`" * 3
parts = ["=== FINDINGS ===", "- (tham chiếu)", "=== FILES ==="]
for n in ["data_prep.py", "train_plan.py", "llm_call.py", "eval_metrics.py"]:
    body = (B / "fixed" / "mlkit" / n).read_text(encoding="utf-8")
    parts.append("%spython file=mlkit/%s\n%s%s" % (FENCE, n, body, FENCE))
(B / "out_ref").mkdir(exist_ok=True)
(B / "out_empty").mkdir(exist_ok=True)
(B / "out_ref" / "output.md").write_text("\n".join(parts) + "\n", encoding="utf-8")
(B / "out_empty" / "output.md").write_text("=== FINDINGS ===\n- không thấy lỗi\n=== FILES ===\n", encoding="utf-8")
print("fixtures written")
