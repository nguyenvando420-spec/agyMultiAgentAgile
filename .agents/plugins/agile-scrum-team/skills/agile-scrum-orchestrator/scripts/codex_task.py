"""Gọi OpenAI Codex CLI làm thành viên `agile-codex` (phản biện / review chỉ-đọc).

Dùng (từ gốc dự án):
  python .agents/plugins/agile-scrum-team/skills/agile-scrum-orchestrator/scripts/codex_task.py \
      --mode review-code --packet packet.md --cd . --diff-uncommitted \
      --out docs/05-quality-assurance/codex-reviews/WP-01.md

  python .agents/plugins/agile-scrum-team/skills/agile-scrum-orchestrator/scripts/codex_task.py \
      --mode review-design --model gpt-6-astra --effort high --packet packet.md --cd . \
      --out docs/05-quality-assurance/critique-reviews/gate-2-codex.md

- Prompt = persona (lấy từ references/codex-member.md) + Context Packet (+ Git diff chỉ-đọc nếu bật --diff-*),
  gửi qua STDIN (`codex exec ... -`) để tránh lỗi dấu nháy trên Windows/PowerShell và giữ trọn Persona + nhãn kết luận.
- Luôn chạy sandbox `read-only` và mặc định bật `--ephemeral` (không rác file session).
- Không bao giờ dùng cờ bỏ qua sandbox/phê duyệt.
- In ra một dòng JSON: {"exit", "seconds", "verdict", "model", "effort", "diff_scope", "out", "log"}.
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
    "review-design": (
        "PHẢN BIỆN THIẾT KẾ (trước Gate 2): kiến trúc, DB/API contract, AI/ML stack, "
        "giới hạn phần cứng, kế hoạch Sprint."
    ),
    "review-code": (
        "REVIEW CODE / ĐỘ SẴN SÀNG PRODUCTION: đúng contract, đúng chuẩn code, lỗi logic, "
        "bảo mật, rò rỉ dữ liệu, sai phần cứng."
    ),
}
EFFORTS = ("low", "medium", "high", "xhigh", "max", "ultra")
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


def run_git_readonly(repo_dir, git_args, timeout=30):
    git_bin = shutil.which("git")
    if not git_bin:
        return None
    try:
        proc = subprocess.run(
            [git_bin, "-C", repo_dir] + list(git_args),
            capture_output=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", errors="replace").strip()


def collect_git_diff_section(repo_dir, args):
    if not is_git_repo(repo_dir):
        return None, "no-git-repo"

    if args.diff_uncommitted:
        scope = "uncommitted"
        status = run_git_readonly(repo_dir, ["status", "--short"]) or "(clean)"
        stat = run_git_readonly(repo_dir, ["diff", "HEAD", "--stat"]) or ""
        if not stat:
            stat = run_git_readonly(repo_dir, ["diff", "--stat"]) or "(no tracked diff)"
        patch = run_git_readonly(repo_dir, ["diff", "HEAD"])
        if patch is None:
            patch = run_git_readonly(repo_dir, ["diff"]) or ""
        header = "### Trạng thái Git (`git status --short`)\n```text\n%s\n```\n\n### Thống kê Diff\n```text\n%s\n```" % (
            status,
            stat,
        )
    elif args.diff_base:
        scope = "base:%s" % args.diff_base
        rng = "%s...HEAD" % args.diff_base
        stat = run_git_readonly(repo_dir, ["diff", rng, "--stat"]) or "(no diff)"
        patch = run_git_readonly(repo_dir, ["diff", rng]) or ""
        header = "### Thống kê Diff so với `%s`\n```text\n%s\n```" % (args.diff_base, stat)
    elif args.diff_commit:
        scope = "commit:%s" % args.diff_commit
        stat = run_git_readonly(repo_dir, ["show", "--stat", "--format=oneline", args.diff_commit]) or "(not found)"
        patch = run_git_readonly(repo_dir, ["show", "--format=", "--patch", args.diff_commit]) or ""
        header = "### Thông tin Commit `%s`\n```text\n%s\n```" % (args.diff_commit, stat)
    else:
        return None, None

    encoded = patch.encode("utf-8")
    if len(encoded) > args.max_diff_bytes:
        clipped = encoded[: args.max_diff_bytes].decode("utf-8", errors="ignore")
        patch_block = (
            "```diff\n%s\n```\n\n"
            "> Lưu ý: Bản diff dài %d bytes, đã cắt ở ngưỡng %d bytes. "
            "Hãy trực tiếp đọc thêm các file liên quan trong repo để kiểm chứng đầy đủ."
            % (clipped, len(encoded), args.max_diff_bytes)
        )
    elif patch:
        patch_block = "```diff\n%s\n```" % patch
    else:
        patch_block = "_(Không có patch tracked diff — kiểm tra danh sách untracked hoặc các file chỉ định trong Context Packet.)_"

    section = "## Git Diff Tự Động Trích Xuất (%s)\n%s\n\n### Chi tiết Patch\n%s" % (scope, header, patch_block)
    return section, scope


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", required=True, choices=sorted(MODES))
    ap.add_argument("--packet", required=True, help="File Markdown chứa Context Packet")
    ap.add_argument("--cd", default=".", help="Thư mục gốc dự án cho Codex")
    ap.add_argument("--out", required=True, help="File ghi báo cáo cuối của Codex")
    ap.add_argument(
        "--model",
        default=None,
        help="Ghi đè model (vd: gpt-6.1-sol, gpt-6-astra, gpt-6.1-terra, gpt-6-luna; mặc định theo ~/.codex/config.toml)",
    )
    ap.add_argument(
        "--effort",
        default=None,
        choices=EFFORTS,
        help="Ghi đè model_reasoning_effort (low|medium|high|xhigh|max|ultra)",
    )
    diff_group = ap.add_mutually_exclusive_group()
    diff_group.add_argument(
        "--diff-uncommitted",
        action="store_true",
        help="Đính kèm git status + git diff chưa commit vào prompt review",
    )
    diff_group.add_argument("--diff-base", default=None, metavar="BRANCH", help="Đính kèm git diff <BRANCH>...HEAD")
    diff_group.add_argument("--diff-commit", default=None, metavar="SHA", help="Đính kèm git show của commit <SHA>")
    ap.add_argument("--max-diff-bytes", type=int, default=120000, help="Giới hạn kích thước patch đính kèm (mặc định 120000)")
    ap.add_argument(
        "--persist-session",
        action="store_true",
        help="Giữ lại file session của Codex (mặc định dùng --ephemeral để không rác đĩa)",
    )
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()

    codex = shutil.which("codex")
    if not codex:
        sys.exit("Không tìm thấy lệnh `codex` trong PATH")
    repo_dir = os.path.abspath(args.cd)
    with open(args.packet, encoding="utf-8") as f:
        packet = f.read()

    diff_section, diff_scope = collect_git_diff_section(repo_dir, args)
    parts = [
        load_persona(),
        "## Chế độ: %s\n%s" % (args.mode, MODES[args.mode]),
        "## Context Packet từ Scrum Master\n%s" % packet,
    ]
    if diff_section:
        parts.append(diff_section)
    prompt = "\n\n".join(parts) + "\n"

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    log = out + ".log.jsonl"
    cmd = [
        codex,
        "exec",
        "-s",
        "read-only",
        "-C",
        repo_dir,
        "-o",
        out,
        "--json",
        "--color",
        "never",
        "-c",
        "shell_environment_policy.inherit=all",
    ]
    if not args.persist_session:
        cmd.append("--ephemeral")
    if not is_git_repo(repo_dir):
        cmd.append("--skip-git-repo-check")
    if args.model:
        cmd += ["-m", args.model]
    if args.effort:
        cmd += ["-c", 'model_reasoning_effort="%s"' % args.effort]
    cmd.append("-")

    start = time.time()
    with open(log, "wb") as lf:
        try:
            code = subprocess.run(
                cmd,
                input=prompt.encode("utf-8"),
                stdout=lf,
                stderr=subprocess.STDOUT,
                timeout=args.timeout,
            ).returncode
        except subprocess.TimeoutExpired:
            code = -1
    verdict = None
    if os.path.exists(out):
        with open(out, encoding="utf-8", errors="replace") as f:
            found = VERDICT_RE.findall(f.read())
        verdict = found[-1] if found else None
    print(
        json.dumps(
            {
                "exit": code,
                "seconds": round(time.time() - start),
                "verdict": verdict,
                "model": args.model or "config-default",
                "effort": args.effort or "config-default",
                "diff_scope": diff_scope,
                "out": out,
                "log": log,
            },
            ensure_ascii=False,
        )
    )
    sys.exit(0 if code == 0 else 1)


if __name__ == "__main__":
    main()
