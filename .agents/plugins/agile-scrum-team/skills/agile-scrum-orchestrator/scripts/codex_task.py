"""Gọi OpenAI Codex CLI làm thành viên `agile-codex` (phản biện / review chỉ-đọc).

Dùng (từ gốc dự án):
  python .agents/plugins/agile-scrum-team/skills/agile-scrum-orchestrator/scripts/codex_task.py \
      --mode review-code --packet packet.md --cd . --out docs/05-quality-assurance/codex-reviews/WP-01.md

- Prompt = persona (lấy từ references/codex-member.md) + Context Packet, gửi qua STDIN (`codex exec ... -`)
  để tránh lỗi dấu nháy khi truyền đối số trên Windows/PowerShell.
- Luôn chạy sandbox `read-only`. Không bao giờ dùng cờ bỏ qua sandbox/phê duyệt.
- In ra một dòng JSON: {"exit", "seconds", "verdict", "out", "log"}.
Python >= 3.9, chỉ dùng thư viện chuẩn.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MEMBER_DOC = os.path.join(HERE, "..", "references", "codex-member.md")
MODES = {
    "review-design": "PHẢN BIỆN THIẾT KẾ (trước Gate 2): kiến trúc, DB/API contract, AI/ML stack, giới hạn phần cứng, kế hoạch Sprint.",
    "review-code": "REVIEW CODE / ĐỘ SẴN SÀNG PRODUCTION: đúng contract, đúng chuẩn code, lỗi logic, bảo mật, rò rỉ dữ liệu, sai phần cứng.",
}
VERDICT_RE = re.compile(r"\[(APPROVED FOR GATE|REVISION REQUIRED|PASS|CHANGES REQUESTED)\]")


def load_persona():
    with open(MEMBER_DOC, encoding="utf-8") as f:
        doc = f.read()
    m = re.search(r"<!-- PERSONA-START -->(.*?)<!-- PERSONA-END -->", doc, re.S)
    if not m:
        sys.exit("Không tìm thấy persona trong %s" % MEMBER_DOC)
    return m.group(1).strip()


def is_git_repo(path):
    cur = os.path.abspath(path)
    while True:
        if os.path.exists(os.path.join(cur, ".git")):
            return True
        parent = os.path.dirname(cur)
        if parent == cur:
            return False
        cur = parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", required=True, choices=sorted(MODES))
    ap.add_argument("--packet", required=True, help="File Markdown chứa Context Packet")
    ap.add_argument("--cd", default=".", help="Thư mục gốc dự án cho Codex")
    ap.add_argument("--out", required=True, help="File ghi báo cáo cuối của Codex")
    ap.add_argument("--model", default=None, help="Ghi đè model (mặc định theo ~/.codex/config.toml)")
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()

    codex = shutil.which("codex")
    if not codex:
        sys.exit("Không tìm thấy lệnh `codex` trong PATH")
    with open(args.packet, encoding="utf-8") as f:
        packet = f.read()
    prompt = "%s\n\n## Chế độ: %s\n%s\n\n## Context Packet từ Scrum Master\n%s\n" % (
        load_persona(), args.mode, MODES[args.mode], packet)

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    log = out + ".log.jsonl"
    cmd = [codex, "exec", "-s", "read-only", "-C", os.path.abspath(args.cd), "-o", out, "--json",
           "--color", "never", "-c", "shell_environment_policy.inherit=all"]
    if not is_git_repo(args.cd):
        cmd.append("--skip-git-repo-check")
    if args.model:
        cmd += ["-m", args.model]
    cmd.append("-")

    start = time.time()
    with open(log, "wb") as lf:
        try:
            code = subprocess.run(cmd, input=prompt.encode("utf-8"), stdout=lf, stderr=subprocess.STDOUT,
                                  timeout=args.timeout).returncode
        except subprocess.TimeoutExpired:
            code = -1
    verdict = None
    if os.path.exists(out):
        with open(out, encoding="utf-8", errors="replace") as f:
            found = VERDICT_RE.findall(f.read())
        verdict = found[-1] if found else None
    print(json.dumps({"exit": code, "seconds": round(time.time() - start), "verdict": verdict,
                      "out": out, "log": log}, ensure_ascii=False))
    sys.exit(0 if code == 0 else 1)


if __name__ == "__main__":
    main()
