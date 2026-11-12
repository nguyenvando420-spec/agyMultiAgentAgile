"""Chạy benchmark v2 trên nhiều model song song qua `agy -p`, mỗi model chạy N lần để đo độ dao động.

Dùng: python run_bench.py --reps 2 <model> [<model> ...]
Mỗi lần chạy trong thư mục tạm NGOÀI workspace; output ghi vào runs/<model>__r<k>/.
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


def run(model, rep):
    d = os.path.join(B, "runs", "%s__r%d" % (model, rep))
    os.makedirs(d, exist_ok=True)
    cwd = tempfile.mkdtemp(prefix="bench-v2-")
    start = time.time()
    with open(os.path.join(d, "output.md"), "wb") as out, open(os.path.join(d, "stderr.log"), "wb") as err:
        try:
            code = subprocess.run([AGY, "-p", PROMPT, "--model", model, "--print-timeout", "1800s"],
                                  stdout=out, stderr=err, cwd=cwd, timeout=2000).returncode
        except subprocess.TimeoutExpired:
            code = -1
    meta = {"model": model, "rep": rep, "exit": code, "seconds": round(time.time() - start)}
    with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)
    shutil.rmtree(cwd, ignore_errors=True)
    print(json.dumps(meta), flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    reps = 1
    if args[:1] == ["--reps"]:
        reps, args = int(args[1]), args[2:]
    threads = [threading.Thread(target=run, args=(m, k)) for m in args for k in range(1, reps + 1)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("ALL DONE", flush=True)
