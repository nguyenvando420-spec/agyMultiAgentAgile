"""Bộ chấm tự động cho benchmark vai trò AI (Task H, I, J, K1).

Dùng: python grade.py <thư mục run chứa output.md>
Chạy được với Python 3.9+, không cần thư viện ngoài.
"""
import copy
import hashlib
import importlib.util
import json
import math
import os
import random
import re
import shutil
import sys
import tempfile
import unicodedata

TASKS = "HIJK"


# ---------------------------------------------------------------- helpers
def split_sections(text):
    secs, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^\s*=+\s*TASK\s+([H-K])\s*=+\s*$", line.strip("*# "))
        if m:
            cur = m.group(1)
            secs[cur] = []
            continue
        if cur:
            secs[cur].append(line)
    return {k: "\n".join(v) for k, v in secs.items()}


def code_block(sec, langs):
    # Ưu tiên rào đóng nằm riêng một dòng: code của Task J có thể chứa ``` bên trong chuỗi.
    for lang in langs:
        m = re.search(r"^[ \t]*```" + lang + r"[^\n]*\n(.*?)^[ \t]*```[ \t]*$", sec, re.S | re.I | re.M)
        if m:
            return m.group(1)
    for lang in langs:
        m = re.search(r"```" + lang + r"[^\n]*\n(.*?)```", sec, re.S | re.I)
        if m:
            return m.group(1)
    m = re.search(r"```[^\n]*\n(.*?)```", sec, re.S)
    return m.group(1) if m else None


def load_module(code, name, workdir):
    # Máy chấm có thể là Python 3.9: hoãn đánh giá annotation để cú pháp `X | None` (3.10+)
    # trong chữ ký hàm không làm hỏng bài đúng. Không đổi logic chạy của bài làm.
    if "from __future__" not in code:
        code = "from __future__ import annotations\n" + code
    path = os.path.join(workdir, name + ".py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    spec = importlib.util.spec_from_file_location(name + "_cand", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_cases(cases):
    ok, fails = 0, []
    for name, fn in cases:
        try:
            good = bool(fn())
        except Exception as e:  # noqa: BLE001 - mọi lỗi của bài làm đều tính là trượt
            good = False
            name = "%s (%s: %s)" % (name, type(e).__name__, str(e)[:60])
        ok += good
        if not good:
            fails.append(name)
    return ok, len(cases), "fail: " + "; ".join(fails[:12])


# ---------------------------------------------------------------- Task H
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:0|\+84)[35789]\d{8}(?!\d)")
KEYS = ("id", "source_id", "text", "label")


def ref_prepare(records):
    if not isinstance(records, list):
        raise TypeError("records")
    out = {"train": [], "val": [], "test": []}
    st = {"input": len(records), "dropped_invalid": 0, "dropped_duplicate": 0, "pii_replaced": 0}
    seen = set()
    for r in records:
        if not isinstance(r, dict) or any(k not in r or not isinstance(r[k], str) for k in KEYS):
            st["dropped_invalid"] += 1
            continue
        t = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", r["text"])).strip()
        if not t:
            st["dropped_invalid"] += 1
            continue
        t, n1 = EMAIL_RE.subn("<EMAIL>", t)
        t, n2 = PHONE_RE.subn("<PHONE>", t)
        key = t.casefold()
        if key in seen:
            st["dropped_duplicate"] += 1
            continue
        seen.add(key)
        st["pii_replaced"] += n1 + n2
        b = int(hashlib.sha256(r["source_id"].encode("utf-8")).hexdigest(), 16) % 10
        split = "test" if b == 0 else "val" if b == 1 else "train"
        out[split].append({"id": r["id"], "source_id": r["source_id"], "text": t, "label": r["label"]})
    out["stats"] = st
    return out


def sid_for(bucket, start=0):
    i = start
    while True:
        s = "src-%d" % i
        if int(hashlib.sha256(s.encode("utf-8")).hexdigest(), 16) % 10 == bucket:
            return s
        i += 1


def rec(i, sid, text, label="L"):
    return {"id": str(i), "source_id": sid, "text": text, "label": label}


def grade_H(code, workdir):
    if not code:
        return 0, 17, "no code"
    try:
        mod = load_module(code, "prepare", workdir)
        f = mod.prepare_dataset
    except Exception as e:  # noqa: BLE001
        return 0, 17, "import error %s" % e
    T, V, R = sid_for(0), sid_for(1), sid_for(5)
    R2 = sid_for(7)

    def same(records):
        a = f(copy.deepcopy(records))
        return a == ref_prepare(copy.deepcopy(records))

    def raises_type():
        for bad in [(rec(1, R, "a"),), None, "abc"]:
            try:
                f(bad)
                return False
            except TypeError:
                pass
        return True

    def no_mutation():
        inp = [rec(1, R, "  Gọi 0912345678  "), rec(2, T, "x@y.com"), rec(3, R, "gọi 0987654321")]
        snap = copy.deepcopy(inp)
        out = f(inp)
        if inp != snap:
            return False
        all_out = out["train"] + out["val"] + out["test"]
        return all(o is not i for o in all_out for i in inp)

    rnd = random.Random(20261112)
    words = ["xin", "chào", "đơn", "hàng", "Hủy", "giao", "hàng", "ＡＢＣ", "  ", "\t", "Gọi", "email"]
    pii = ["0912345678", "+84387654321", "0123456789", "a.b@c.vn", "09123456789", "1230912345678"]
    big = []
    for i in range(300):
        parts = [rnd.choice(words) for _ in range(rnd.randint(0, 5))]
        if rnd.random() < 0.4:
            parts.insert(rnd.randint(0, len(parts)), rnd.choice(pii))
        r = rec(i, "src-%d" % rnd.randint(0, 40), " ".join(parts), rnd.choice("ABC"))
        if rnd.random() < 0.05:
            r = {"id": str(i), "text": "thiếu khóa"}
        if rnd.random() < 0.03:
            r["text"] = 123
        big.append(r)

    cases = [
        ("TypeError non-list", raises_type),
        ("basic 3 splits", lambda: same([rec(1, T, "a"), rec(2, V, "b"), rec(3, R, "c")])),
        ("invalid records", lambda: same([rec(1, R, "ok"), "x", {"id": "2", "source_id": R, "text": "t"},
                                          rec(3, R, 5), rec(4, R, " \t\n "), {"id": 9, "source_id": R, "text": "z", "label": "L"}])),
        ("NFKC + whitespace", lambda: f([rec(1, R, "ｈｅｌｌｏ\u00a0\t world\n")])["train"][0]["text"] == "hello world"),
        ("email scrub", lambda: f([rec(1, R, "Liên hệ a.b+c@ex-ample.com.vn nhé")])["train"][0]["text"] == "Liên hệ <EMAIL> nhé"),
        ("phone scrub", lambda: same([rec(1, R, "Gọi 0912345678 hoặc +84387654321")])),
        ("phone non-matches", lambda: same([rec(1, R, "0123456789 09123456789 x12340912345678 +8412345678")])),
        ("email before phone", lambda: same([rec(1, R, "0912345678@gmail.com")])),
        ("dedup casefold/space", lambda: same([rec(1, R, "Hello World"), rec(2, R, "hello   WORLD")])),
        ("dedup after PII + pii count kept only", lambda: same([rec(1, R, "Gọi 0912345678"), rec(2, R, "Gọi 0987654321")])),
        ("dedup across sources", lambda: same([rec(1, T, "trùng"), rec(2, R, "Trùng"), rec(3, V, "TRÙNG ")])),
        ("group split", lambda: same([rec(1, R, "a1"), rec(2, T, "t1"), rec(3, R, "a2"), rec(4, V, "v1"), rec(5, T, "t2")])),
        ("order within split", lambda: [x["id"] for x in f([rec(i, R if i % 2 else R2, "m%d" % i) for i in range(10)])["train"]]
         == [str(i) for i in range(10)]),
        ("no mutation / new dicts", no_mutation),
        ("stats.input counts invalid", lambda: f([rec(1, R, "a"), 5, None])["stats"]["input"] == 3),
        ("extra keys ignored", lambda: same([dict(rec(1, R, "a"), meta="m")])),
        ("random 300 vs reference", lambda: same(big)),
    ]
    return run_cases(cases)


# ---------------------------------------------------------------- Task J
class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        r = self.responses.pop(0)
        if isinstance(r, BaseException):
            raise r
        return r


REQ = {"intent": str, "confidence": float}
GOOD = '{"intent": "huy_don", "confidence": 0.9, "extra": 1}'


def grade_J(code, workdir):
    if not code:
        return 0, 19, "no code"
    try:
        mod = load_module(code, "structured", workdir)
        f = mod.call_structured
    except Exception as e:  # noqa: BLE001
        return 0, 19, "import error %s" % e

    def expect_exc(exc, **kw):
        c = FakeClient([GOOD])
        args = dict(client=c, prompt="p", required=REQ)
        args.update(kw)
        try:
            f(**args)
            return False
        except exc:
            return c.calls == []

    def first_try():
        c = FakeClient([GOOD])
        r = f(c, "P", REQ)
        return r == {"ok": True, "data": {"intent": "huy_don", "confidence": 0.9}, "attempts": 1}

    def timeout_kw():
        c = FakeClient([GOOD])
        f(c, "P", REQ)
        args, kw = c.calls[0]
        return args == ("P",) and kw == {"timeout": 10.0}

    def ok_data(resp, expect):
        c = FakeClient([resp])
        r = f(c, "P", REQ)
        return r.get("ok") is True and r.get("data") == expect

    def transient(exc):
        c = FakeClient([exc, GOOD])
        r = f(c, "P", REQ)
        return r["ok"] is True and r["attempts"] == 2 and c.calls[1][0] == ("P",)

    def other_exc():
        c = FakeClient([RuntimeError("boom"), GOOD])
        try:
            f(c, "P", REQ)
            return False
        except RuntimeError:
            return len(c.calls) == 1

    def repair_prompt():
        c = FakeClient(["không phải json", GOOD])
        r = f(c, "PROMPT", REQ)
        p2 = c.calls[1][0][0]
        return r["ok"] is True and r["attempts"] == 2 and p2.startswith("PROMPT") and p2 != "PROMPT"

    def typed(resp, valid):
        c = FakeClient([resp, resp, resp])
        r = f(c, "P", {"n": int, "x": float}, max_retries=0)
        return r["ok"] is valid

    def exhaust():
        fb = object()
        c = FakeClient(["x", "y", "z"])
        r = f(c, "P", REQ, max_retries=2, fallback=fb)
        return (len(c.calls) == 3 and r["ok"] is False and r["data"] is fb and r["attempts"] == 3
                and isinstance(r["error"], str) and r["error"].strip() != "")

    def zero_retries():
        c = FakeClient(["x", GOOD])
        r = f(c, "P", REQ, max_retries=0)
        return len(c.calls) == 1 and r["ok"] is False

    def array_invalid():
        c = FakeClient(["[1, 2]", GOOD])
        r = f(c, "P", REQ)
        return r["ok"] is True and r["attempts"] == 2

    def mixed():
        c = FakeClient([TimeoutError(), "rác", GOOD])
        r = f(c, "P", REQ, max_retries=2)
        p2, p3 = c.calls[1][0][0], c.calls[2][0][0]
        return r["ok"] is True and r["attempts"] == 3 and p2 == "P" and p3.startswith("P") and p3 != "P"

    def timeouts_only():
        c = FakeClient([TimeoutError(), ConnectionError(), TimeoutError()])
        r = f(c, "P", REQ, max_retries=2)
        return r["ok"] is False and r["attempts"] == 3 and r["data"] is None and r["error"].strip() != ""

    def key_sets():
        r1 = f(FakeClient([GOOD]), "P", REQ)
        r2 = f(FakeClient(["x"]), "P", REQ, max_retries=0)
        return set(r1) == {"ok", "data", "attempts"} and set(r2) == {"ok", "data", "attempts", "error"}

    two_fences = 'Đây:\n```json\n{"intent": "a", "confidence": 1}\n```\nhoặc\n```json\n{"intent": "b", "confidence": 0.5}\n```'
    cases = [
        ("TypeError prompt", lambda: expect_exc(TypeError, prompt=123)),
        ("ValueError max_retries", lambda: expect_exc(ValueError, max_retries=-1) and expect_exc(ValueError, max_retries="2")),
        ("first try + filter extra", first_try),
        ("timeout=10.0 keyword", timeout_kw),
        ("```json fence", lambda: ok_data('Kết quả:\n```json\n{"intent": "a", "confidence": 0.5}\n```\nhết', {"intent": "a", "confidence": 0.5})),
        ("bare ``` fence", lambda: ok_data('```\n{"intent": "a", "confidence": 1}\n```', {"intent": "a", "confidence": 1})),
        ("first fence wins", lambda: ok_data(two_fences, {"intent": "a", "confidence": 1})),
        ("no fence, braces in prose", lambda: ok_data('Kết quả: {"intent": "x", "confidence": 0.9} xong', {"intent": "x", "confidence": 0.9})),
        ("TimeoutError retry same prompt", lambda: transient(TimeoutError())),
        ("ConnectionError retry same prompt", lambda: transient(ConnectionError())),
        ("other exception propagates", other_exc),
        ("repair prompt after invalid", repair_prompt),
        ("bool not int", lambda: typed('{"n": true, "x": 1.0}', False)),
        ("int ok for float / bool not float", lambda: typed('{"n": 1, "x": 2}', True) and typed('{"n": 1, "x": false}', False)),
        ("exhaust -> fallback identity", exhaust),
        ("max_retries=0 one call", zero_retries),
        ("top-level array invalid", array_invalid),
        ("mixed timeout/invalid/valid", mixed),
        ("timeouts only", timeouts_only),
    ]
    ok, total, note = run_cases(cases)
    # key_sets gộp vào ghi chú (không cộng điểm riêng để tổng = 19)
    try:
        if not key_sets():
            note += "; result keys not exact"
    except Exception as e:  # noqa: BLE001
        note += "; key_sets error %s" % e
    return ok, total, note


# ---------------------------------------------------------------- Task I
I_KEYS = {"method", "load_in_4bit", "bnb_4bit_quant_type", "compute_dtype", "bf16", "fp16", "attn_implementation",
          "gradient_checkpointing", "per_device_train_batch_size", "gradient_accumulation_steps", "max_seq_length",
          "lora_r", "lora_alpha", "target_modules", "output_dir", "save_interval_minutes", "resume_from_checkpoint",
          "export_format", "quant_type", "est_gguf_size_gb", "kv_cache_fp16_gb_at_4096", "fits_rtx2060_6gb",
          "use_golden_test_for_early_stopping", "full_ft_7b_bf16_on_t4_feasible", "notes"}
GGUF_RANGES = {"Q4_K_M": (0.85, 1.15), "Q5_K_M": (1.0, 1.35), "Q6_K": (1.15, 1.5), "Q8_0": (1.45, 1.9)}
# KV cache = 2 (K,V) * 28 layer * 2 head * 128 dim * 4096 token * 2 byte = 117.4 MB = 0.109 GiB
KV_RANGE = (0.095, 0.135)


def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def grade_I(sec):
    code = code_block(sec, ["json"])
    try:
        j = json.loads(code)
    except Exception:  # noqa: BLE001
        return 0, 16, "invalid JSON"
    pts, notes = 0, []

    def chk(cond, label):
        nonlocal pts
        if cond:
            pts += 1
        else:
            notes.append(label)

    chk(set(j) == I_KEYS, "keys %s" % sorted(set(j) ^ I_KEYS))
    chk(j.get("method") == "qlora" and j.get("load_in_4bit") is True and str(j.get("bnb_4bit_quant_type", "")).lower() == "nf4",
        "qlora/4bit/nf4")
    chk(j.get("compute_dtype") == "float16", "compute_dtype=%s" % j.get("compute_dtype"))
    chk(j.get("bf16") is False and j.get("fp16") is True, "bf16/fp16")
    chk(j.get("attn_implementation") in ("sdpa", "eager"), "attn=%s" % j.get("attn_implementation"))
    chk(j.get("gradient_checkpointing") is True, "grad ckpt")
    chk(str(j.get("output_dir", "")).startswith("/kaggle/working") and j.get("resume_from_checkpoint") is True,
        "output_dir/resume")
    s = j.get("save_interval_minutes")
    chk(num(s) and 0 < s <= 30, "save_interval=%s" % s)
    q = str(j.get("quant_type", "")).upper()
    chk(str(j.get("export_format", "")).lower() == "gguf" and q in GGUF_RANGES, "export %s %s" % (j.get("export_format"), q))
    g = j.get("est_gguf_size_gb")
    lo, hi = GGUF_RANGES.get(q, (0, -1))
    chk(num(g) and lo <= g <= hi, "gguf_size=%s for %s" % (g, q))
    k = j.get("kv_cache_fp16_gb_at_4096")
    chk(num(k) and KV_RANGE[0] <= k <= KV_RANGE[1], "kv=%s" % k)
    chk(j.get("fits_rtx2060_6gb") is True, "fits")
    chk(j.get("use_golden_test_for_early_stopping") is False, "golden early stop")
    chk(j.get("full_ft_7b_bf16_on_t4_feasible") is False, "7b full ft")
    m = j.get("max_seq_length")
    chk(isinstance(m, int) and 256 <= m <= 512, "max_seq=%s" % m)
    bs, ga = j.get("per_device_train_batch_size"), j.get("gradient_accumulation_steps")
    chk(isinstance(bs, int) and isinstance(ga, int) and 1 <= bs <= 16 and 8 <= bs * ga <= 128, "batch %s x %s" % (bs, ga))
    if len(str(j.get("notes", "")).split()) > 60:
        notes.append("notes > 60 words")
    extra = re.sub(r"```json.*?```", "", sec, flags=re.S).strip()
    if extra:
        notes.append("prose outside JSON (%d chars)" % len(extra))
    return pts, 16, "; ".join(notes)


# ---------------------------------------------------------------- Task K1
def grade_K1(sec):
    code = code_block(sec, ["json"])
    try:
        j = json.loads(code)
    except Exception:  # noqa: BLE001
        return 0, 4, "invalid JSON"
    pts, notes = 0, []
    expect = {"p95_ms": (900, 0.5), "accuracy": (0.85, 0.0015), "macro_f1": (0.527, 0.0015), "raw_schema_validity": (0.94, 0.0015)}
    for key, (val, tol) in expect.items():
        v = j.get(key)
        if num(v) and abs(v - val) <= tol:
            pts += 1
        else:
            notes.append("%s=%s (expect %s)" % (key, v, val))
    return pts, 4, "; ".join(notes)


# ---------------------------------------------------------------- main
def main(run_dir):
    with open(os.path.join(run_dir, "output.md"), encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    secs = split_sections(text)
    work = tempfile.mkdtemp()
    sys.path.insert(0, work)
    res = {"sections_found": "".join(sorted(secs)), "order_ok": list(secs) == list(TASKS)}
    res["H"] = grade_H(code_block(secs.get("H", ""), ["python", "py"]), work)
    res["I"] = grade_I(secs.get("I", ""))
    res["J"] = grade_J(code_block(secs.get("J", ""), ["python", "py"]), work)
    res["K1"] = grade_K1(secs.get("K", ""))
    with open(os.path.join(run_dir, "section_K.md"), "w", encoding="utf-8") as fh:
        fh.write(secs.get("K", "(MISSING)"))
    shutil.rmtree(work, ignore_errors=True)
    print(json.dumps(res, ensure_ascii=False))
    return res


if __name__ == "__main__":
    main(sys.argv[1])
