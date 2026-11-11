"""Ẩn danh các bài tự luận A/D/E để chấm mù. Mapping ghi vào blind/.mapping.json (chỉ mở sau khi chấm xong)."""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from grade import split_sections

B = os.path.dirname(os.path.abspath(__file__))
models = sorted(os.listdir(os.path.join(B, "runs")))
labels = [f"M{i}" for i in range(1, len(models) + 1)]
random.SystemRandom().shuffle(labels)
mapping = dict(zip(labels, models))
os.makedirs(os.path.join(B, "blind"), exist_ok=True)
for task in "ADE":
    with open(os.path.join(B, "blind", f"task_{task}.md"), "w") as f:
        for lab in sorted(mapping):
            secs = split_sections(open(os.path.join(B, "runs", mapping[lab], "output.md")).read())
            f.write(f"\n\n######## {lab} ########\n{secs.get(task, '(MISSING)').strip()}\n")
json.dump(mapping, open(os.path.join(B, "blind", ".mapping.json"), "w"))
print("blinded", len(models), "runs")
