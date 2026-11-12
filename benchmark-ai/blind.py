"""Ẩn danh phần K2 (tự luận) để chấm mù. Mapping ghi vào blind/.mapping.json — chỉ mở SAU khi chấm xong."""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade import split_sections  # noqa: E402

B = os.path.dirname(os.path.abspath(__file__))
models = sorted(os.listdir(os.path.join(B, "runs")))
labels = ["M%d" % i for i in range(1, len(models) + 1)]
random.SystemRandom().shuffle(labels)
mapping = dict(zip(labels, models))
os.makedirs(os.path.join(B, "blind"), exist_ok=True)
with open(os.path.join(B, "blind", "task_K.md"), "w", encoding="utf-8") as f:
    for lab in sorted(mapping):
        with open(os.path.join(B, "runs", mapping[lab], "output.md"), encoding="utf-8", errors="replace") as fh:
            secs = split_sections(fh.read())
        f.write("\n\n######## %s ########\n%s\n" % (lab, secs.get("K", "(MISSING)").strip()))
with open(os.path.join(B, "blind", ".mapping.json"), "w", encoding="utf-8") as f:
    json.dump(mapping, f)
print("blinded", len(models), "runs")
