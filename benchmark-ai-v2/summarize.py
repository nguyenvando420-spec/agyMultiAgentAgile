"""Tổng hợp kết quả v2: chấm mọi run, ghi results.json + in bảng theo model (trung bình 2 lần chạy)."""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade import B, ROLES, grade  # noqa: E402

runs = sorted(os.listdir(os.path.join(B, "runs")))
res = {r: grade(os.path.join(B, "runs", r)) for r in runs}
for r in runs:
    with open(os.path.join(B, "runs", r, "meta.json"), encoding="utf-8") as f:
        res[r]["seconds"] = json.load(f)["seconds"]
with open(os.path.join(B, "results.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)

short = [k.split(" ")[0] for k in ROLES]
print("%-34s %s | %-14s | files | sec" % ("run", " | ".join("%-8s" % s for s in short), "TOTAL fix/brk/net"))
for r in runs:
    v = res[r]
    cells = ["%d/%d -%d " % (v[k]["fixed"], v[k]["bugs"], v[k]["decoys_broken"]) for k in ROLES]
    t = v["TOTAL"]
    print("%-34s %s | %2d / %d / %2d     | %d     | %d" % (r, " | ".join("%-8s" % c for c in cells), t["fixed"], t["decoys_broken"], t["net"],
                                                      len(v["files_returned"]), v["seconds"]))
print()
for r in runs:
    v = res[r]
    missed = sum((v[k]["missed"] for k in ROLES), [])
    broken = sum((v[k]["broken"] for k in ROLES), [])
    print("%-34s missed=%s broken=%s errors=%s" % (r, [m[:3] for m in missed], [b[:3] for b in broken], list(v["errors"])))

agg = defaultdict(lambda: defaultdict(list))
for r in runs:
    model = r.split("__r")[0]
    for k in list(ROLES) + ["TOTAL"]:
        agg[model][k].append(res[r][k]["net"])
print("\nTrung bình net theo model (2 lần chạy):")
for model, d in sorted(agg.items(), key=lambda kv: -sum(kv[1]["TOTAL"])):
    print("%-26s %s | TOTAL %s" % (model, " | ".join("%s %s" % (s, d[k]) for s, k in zip(short, ROLES)), d["TOTAL"]))
