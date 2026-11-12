"""Chạy bộ đề benchmark-ai trên nhiều model song song qua `agy -p`, ghi output + thời gian.

Dùng: python run_bench.py <model> [<model> ...]      (danh sách model: agy models)
Viết bằng Python thay vì PowerShell/bash: PowerShell 5.1 làm mất dấu " khi truyền đối số
cho chương trình ngoài, còn đề bài có JSON. subprocess (list args) escape đúng trên Windows.
Mỗi model chạy trong thư mục tạm NGOÀI workspace để không nạp rule/plugin của dự án.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

B = os.path.dirname(os.path.abspath(__file__))
PROMPT = open(os.path.join(B, "prompt.md"), encoding="utf-8").read()
AGY = shutil.which("agy") or "agy"


def run(model):
    d = os.path.join(B, "runs", model)
    os.makedirs(d, exist_ok=True)
    cwd = tempfile.mkdtemp(prefix="bench-ai-")
    start = time.time()
    with open(os.path.join(d, "output.md"), "wb") as out, open(os.path.join(d, "stderr.log"), "wb") as err:
        try:
            code = subprocess.run([AGY, "-p", PROMPT, "--model", model, "--print-timeout", "1500s"],
                                  stdout=out, stderr=err, cwd=cwd, timeout=1700).returncode
        except subprocess.TimeoutExpired:
            code = -1
    meta = {"model": model, "exit": code, "seconds": round(time.time() - start)}
    with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)
    shutil.rmtree(cwd, ignore_errors=True)
    print(json.dumps(meta), flush=True)


if __name__ == "__main__":
    threads = [threading.Thread(target=run, args=(m,)) for m in sys.argv[1:]]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("ALL DONE", flush=True)
