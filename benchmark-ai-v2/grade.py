"""Chấm benchmark v2: áp các file model trả về lên bản sao sạch của repo/ rồi chạy test ẩn.

Dùng: python grade.py <thư mục run chứa output.md>     (hoặc --all để chấm mọi thư mục trong runs/)
Điểm mỗi vai trò = số lỗi đã sửa (B) − số bẫy bị sửa hỏng (D), tối thiểu 0.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

B = os.path.dirname(os.path.abspath(__file__))
ALLOWED = {"mlkit/data_prep.py", "mlkit/train_plan.py", "mlkit/llm_call.py", "mlkit/eval_metrics.py"}
ROLES = {
    "data (AI Data Engineer)": ("B01", "B02", "B03", "B04", "B05", "D01", "D02"),
    "train (SLM Trainer)": ("B06", "B07", "B08", "B09", "D03", "D04"),
    "llm (AI Engineer)": ("B10", "B11", "B12", "B13", "B14", "D05", "D06"),
    "eval (MLOps-Eval)": ("B15", "B16", "B17", "B18", "B19", "D07", "D08"),
}
FILE_RE = re.compile(r"^[ \t]*```python[ \t]+file=(\S+)[ \t]*\n(.*?)^[ \t]*```[ \t]*$", re.S | re.M)


def extract_files(text):
    files = {}
    for path, body in FILE_RE.findall(text):
        path = path.strip().replace("\\", "/").lstrip("./")
        if path in ALLOWED:
            files[path] = body  # khối sau cùng của cùng một file sẽ thắng
    return files


def run_hidden(files):
    work = tempfile.mkdtemp(prefix="v2grade-")
    try:
        shutil.copytree(os.path.join(B, "repo", "mlkit"), os.path.join(work, "mlkit"))
        for path, body in files.items():
            if "from __future__" not in body:
                body = "from __future__ import annotations\n" + body  # máy chấm Python 3.9
            with open(os.path.join(work, path), "w", encoding="utf-8") as f:
                f.write(body)
        r = subprocess.run([sys.executable, os.path.join(B, "hidden", "hidden_tests.py")], cwd=work,
                           capture_output=True, text=True, encoding="utf-8", timeout=300)
        return json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        shutil.rmtree(work, ignore_errors=True)


def score(res):
    out, tot_fix, tot_bug, tot_broken = {}, 0, 0, 0
    for role, ids in ROLES.items():
        bugs = [k for k in res if not k.endswith("__err") and k[:3] in ids and k.startswith("B")]
        decs = [k for k in res if not k.endswith("__err") and k[:3] in ids and k.startswith("D")]
        fixed = sum(res[k] for k in bugs)
        broken = sum(not res[k] for k in decs)
        out[role] = {"fixed": fixed, "bugs": len(bugs), "decoys_broken": broken, "net": max(0, fixed - broken),
                     "missed": [k for k in bugs if not res[k]], "broken": [k for k in decs if not res[k]]}
        tot_fix += fixed
        tot_bug += len(bugs)
        tot_broken += broken
    out["TOTAL"] = {"fixed": tot_fix, "bugs": tot_bug, "decoys_broken": tot_broken, "net": max(0, tot_fix - tot_broken)}
    return out


def grade(run_dir):
    with open(os.path.join(run_dir, "output.md"), encoding="utf-8", errors="replace") as f:
        text = f.read()
    files = extract_files(text)
    res = run_hidden(files)
    s = score(res)
    s["files_returned"] = sorted(files)
    s["errors"] = {k: v for k, v in res.items() if k.endswith("__err")}
    return s


if __name__ == "__main__":
    targets = sys.argv[1:]
    if targets == ["--all"]:
        targets = [os.path.join(B, "runs", d) for d in sorted(os.listdir(os.path.join(B, "runs")))]
    allres = {}
    for t in targets:
        allres[os.path.basename(t.rstrip("\\/"))] = grade(t)
    print(json.dumps(allres, ensure_ascii=False, indent=1))
