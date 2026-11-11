"""Bộ chấm điểm tự động cho Task B, C, F, G. Dùng: python3 grade.py <thư mục run>"""
import json, re, subprocess, sys, os, tempfile, shutil, textwrap, importlib.util

TASKS = "ABCDEFG"


def split_sections(text):
    secs, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^\s*=+\s*TASK\s+([A-G])\s*=+\s*$", line.strip("*# "))
        if m:
            cur = m.group(1); secs[cur] = []; continue
        if cur:
            secs[cur].append(line)
    return {k: "\n".join(v) for k, v in secs.items()}


def code_block(sec, langs):
    for lang in langs:
        m = re.search(r"```" + lang + r"[^\n]*\n(.*?)```", sec, re.S | re.I)
        if m:
            return m.group(1)
    m = re.search(r"```[^\n]*\n(.*?)```", sec, re.S)
    return m.group(1) if m else None


# ---------------- Task B: hidden tests ----------------
B_CASES = [
    ("1h30m", 5400), ("90s", 90), ("2d", 172800), ("1d 2h 3m 4s", 93784), ("  45m  ", 2700),
    ("05m", 300), ("0s", 0), ("1h0m", 3600), ("90m", 5400), ("1h  30m", 5400), ("\t1h\n", 3600),
    ("0d0h0m0s", 0), ("3650d", 315360000), ("1h30m4s", 5404), ("2d30s", 172830),
    ("", ValueError), ("   ", ValueError), ("h", ValueError), ("90", ValueError), ("1x", ValueError),
    ("1h1h", ValueError), ("30m1h", ValueError), ("1 h", ValueError), ("-5m", ValueError),
    ("+5m", ValueError), ("1H", ValueError), ("1.5h", ValueError), ("1h30", ValueError),
    ("1h,30m", ValueError), ("m5", ValueError), ("１h", ValueError), ("3651d", OverflowError),
    ("315360001s", OverflowError), (None, TypeError), (5, TypeError), (b"1h", TypeError),
]


def grade_B(code, workdir):
    if not code:
        return 0, len(B_CASES), "no code"
    p = os.path.join(workdir, "duration.py"); open(p, "w").write(code)
    spec = importlib.util.spec_from_file_location("duration_mod", p)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        return 0, len(B_CASES), f"import error {e}"
    ok, fails = 0, []
    for inp, exp in B_CASES:
        try:
            r = mod.parse_duration(inp)
            good = (not isinstance(exp, type)) and r == exp and type(r) is int
        except Exception as e:
            good = isinstance(exp, type) and type(e) is exp
        ok += good
        if not good:
            fails.append(repr(inp))
    return ok, len(B_CASES), "fail: " + ", ".join(fails[:12])


# ---------------- Task C: mutation testing ----------------
CORRECT = '''
import math
def paginate(items, page, page_size):
    if page < 1: raise ValueError("page")
    if not (1 <= page_size <= 100): raise ValueError("page_size")
    total = len(items)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    return {"items": items[start:start + page_size], "total": total,
            "total_pages": total_pages, "has_next": page < total_pages}
'''
MUTANTS = {
    "M1 offset": ("start = (page - 1) * page_size", "start = page * page_size"),
    "M2 size100": ("1 <= page_size <= 100", "1 <= page_size < 100"),
    "M3 floor": ("math.ceil(total / page_size)", "(total // page_size)"),
    "M4 has_next": ("page < total_pages}", "page <= total_pages}"),
    "M5 page0": ("if page < 1:", "if page < 0:"),
    "M6 empty_pages": ("if total else 0", "if total else 1"),
    "M7 beyond_raises": ('    start = (page - 1) * page_size\n',
                         '    start = (page - 1) * page_size\n    if total_pages and page > total_pages: raise ValueError("beyond")\n'),
    "M8 size0": ("1 <= page_size", "0 <= page_size"),
}


def run_pytest(d):
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", d],
                       capture_output=True, text=True, timeout=120)
    return r.returncode == 0


def grade_C(code, workdir):
    if not code:
        return 0, len(MUTANTS), "no code"
    d = os.path.join(workdir, "c"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "test_paginate.py"), "w").write(code)
    open(os.path.join(d, "paginate.py"), "w").write(CORRECT)
    if not run_pytest(d):
        return 0, len(MUTANTS), "tests FAIL on correct implementation"
    killed, survived = 0, []
    for name, (a, b) in MUTANTS.items():
        src = CORRECT.replace(a, b)
        assert src != CORRECT, name
        open(os.path.join(d, "paginate.py"), "w").write(src)
        shutil.rmtree(os.path.join(d, "__pycache__"), ignore_errors=True)
        if run_pytest(d):
            survived.append(name)
        else:
            killed += 1
    return killed, len(MUTANTS), "survived: " + ", ".join(survived)


# ---------------- Task F: JSON compliance ----------------
def grade_F(sec):
    pts, notes = 0, []
    code = code_block(sec, ["json"])
    try:
        j = json.loads(code); pts += 2
    except Exception:
        return 0, 8, "invalid JSON"
    keys = {"language", "formatter", "linter", "type_checker", "test_framework", "commands", "banned_libraries", "rationale"}
    if set(j) == keys: pts += 1
    else: notes.append(f"keys {sorted(set(j) ^ keys)}")
    c = j.get("commands", {})
    if set(c) == {"format_check", "lint", "typecheck", "test"}: pts += 1
    fc = c.get("format_check", "")
    if re.search(r"--check|--diff", fc) and not re.search(r"--fix\b", fc): pts += 1
    else: notes.append(f"format_check='{fc}'")
    known = re.compile(r"\b(ruff|black|flake8|pylint|mypy|pyright|pytest|isort)\b")
    if all(known.search(c.get(k, "")) for k in ("lint", "typecheck", "test")): pts += 1
    if isinstance(j.get("banned_libraries"), list) and j["banned_libraries"]: pts += 1
    if len(str(j.get("rationale", "")).split()) <= 40: pts += 1
    else: notes.append("rationale >40 words")
    extra = re.sub(r"```json.*?```", "", sec, flags=re.S).strip()
    if extra: notes.append(f"prose outside JSON ({len(extra)} chars)")
    return pts, 8, "; ".join(notes)


# ---------------- Task G: Dockerfile checklist ----------------
def _deps_before_code(code):
    lines = [l.strip() for l in code.splitlines()]
    req = next((i for i, l in enumerate(lines) if re.match(r"COPY\b", l, re.I) and "requirements" in l), None)
    src = next((i for i, l in enumerate(lines) if re.match(r"COPY\b(?!.*--from)", l, re.I)
                and re.search(r"\s\.\s+\S+\s*$|\s\.\s*$", l) and "requirements" not in l), None)
    return req is not None and src is not None and req < src

def grade_G(sec):
    code = code_block(sec, ["dockerfile", "docker"]) or ""
    froms = re.findall(r"^\s*FROM\s+(\S+)", code, re.M | re.I)
    checks = {
        "multi-stage": len(froms) >= 2,
        "pinned base (no latest)": bool(froms) and all(":" in f and not f.endswith(":latest") for f in froms if not re.match(r"^[a-z]+$", f)),
        "non-root USER": bool(re.search(r"^\s*USER\s+(?!root\b|0\b)\S+", code, re.M | re.I)),
        "HEALTHCHECK": "HEALTHCHECK" in code.upper(),
        "exec-form CMD/ENTRYPOINT": bool(re.search(r"^\s*(CMD|ENTRYPOINT)\s*\[", code, re.M)),
        "pip no-cache": "--no-cache-dir" in code or "PIP_NO_CACHE_DIR" in code,
        "deps layer before code": _deps_before_code(code),
        "PYTHONUNBUFFERED/DONTWRITEBYTECODE": "PYTHONUNBUFFERED" in code or "PYTHONDONTWRITEBYTECODE" in code,
    }
    failed = [k for k, v in checks.items() if not v]
    return sum(checks.values()), len(checks), "missing: " + ", ".join(failed)


def main(run_dir):
    text = open(os.path.join(run_dir, "output.md"), encoding="utf-8", errors="replace").read()
    secs = split_sections(text)
    work = tempfile.mkdtemp()
    res = {"sections_found": "".join(sorted(secs)), "order_ok": list(secs) == list(TASKS)}
    res["B"] = grade_B(code_block(secs.get("B", ""), ["python", "py"]), work)
    res["C"] = grade_C(code_block(secs.get("C", ""), ["python", "py"]), work)
    res["F"] = grade_F(secs.get("F", ""))
    res["G"] = grade_G(secs.get("G", ""))
    for k in "ADE":
        open(os.path.join(run_dir, f"section_{k}.md"), "w").write(secs.get(k, "(MISSING)"))
    shutil.rmtree(work, ignore_errors=True)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
