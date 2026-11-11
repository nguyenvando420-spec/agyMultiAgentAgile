#!/usr/bin/env bash
set -euo pipefail

# Script khởi tạo dự án mới tích hợp sẵn Đội ngũ 8 Subagents Agile Production-Ready + Scrum Project Framework
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SCRUM_TEMPLATES_DIR="$(cd "${FRAMEWORK_ROOT}/.." && pwd)/scrum-project-framework"

usage() {
  cat <<EOF
Cách dùng:
  $(basename "$0") <duong-dan-du-an-moi> [--empty-docs]

Tham số:
  <duong-dan-du-an-moi>   Đường dẫn thư mục dự án muốn khởi tạo (tương đối hoặc tuyệt đối)
  --empty-docs            Chỉ tạo cây thư mục docs/ trống thay vì chép sẵn mẫu từ scrum-project-framework

Ví dụ:
  ./scripts/init-agile-project.sh ../my-production-app
EOF
}

if [[ $# -lt 1 ]] || [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

TARGET_DIR="$1"
COPY_TEMPLATES=true
if [[ "${2:-}" == "--empty-docs" ]]; then
  COPY_TEMPLATES=false
fi

mkdir -p "${TARGET_DIR}"
TARGET_ABS="$(cd "${TARGET_DIR}" && pwd)"

echo "🚀 Đang khởi tạo dự án Enterprise Agile Multi-Agent tại: ${TARGET_ABS}"

# 1. Sao chép cấu hình .agents/ (bao gồm thư mục .agents/rules/ cho Tech Lead ghi chuẩn code format) và AGENTS.md
mkdir -p "${TARGET_ABS}/.agents/rules"
cp -R "${FRAMEWORK_ROOT}/.agents/"* "${TARGET_ABS}/.agents/"
cp "${FRAMEWORK_ROOT}/AGENTS.md" "${TARGET_ABS}/AGENTS.md"

# 2. Khởi tạo hệ thống thư mục tài liệu Scrum chuẩn + thư mục lưu biên bản Phản biện (critique-reviews)
mkdir -p "${TARGET_ABS}/docs"
if [[ "${COPY_TEMPLATES}" == true ]] && [[ -d "${SCRUM_TEMPLATES_DIR}" ]]; then
  echo "📋 Đang chép bộ biểu mẫu chuẩn từ scrum-project-framework vào docs/..."
  for phase_dir in \
    01-discovery \
    02-product-planning \
    03-system-design \
    04-sprint-management \
    05-quality-assurance \
    06-release-deployment \
    07-monitoring-improvement \
    08-project-closure; do
    if [[ -d "${SCRUM_TEMPLATES_DIR}/${phase_dir}" ]]; then
      cp -R "${SCRUM_TEMPLATES_DIR}/${phase_dir}" "${TARGET_ABS}/docs/"
    else
      mkdir -p "${TARGET_ABS}/docs/${phase_dir}"
    fi
  done
else
  for phase_dir in \
    01-discovery \
    02-product-planning \
    03-system-design \
    04-sprint-management \
    05-quality-assurance \
    06-release-deployment \
    07-monitoring-improvement \
    08-project-closure; do
    mkdir -p "${TARGET_ABS}/docs/${phase_dir}"
  done
fi

mkdir -p "${TARGET_ABS}/docs/05-quality-assurance/critique-reviews"

# 2b. File trạng thái điều phối (giúp Scrum Master khôi phục sau khi server restart)
STATE_TEMPLATE="${FRAMEWORK_ROOT}/.agents/plugins/agile-scrum-team/skills/agile-scrum-orchestrator/references/agile-state-template.md"
mkdir -p "${TARGET_ABS}/docs/04-sprint-management"
if [[ ! -f "${TARGET_ABS}/docs/04-sprint-management/agile-state.md" ]] && [[ -f "${STATE_TEMPLATE}" ]]; then
  cp "${STATE_TEMPLATE}" "${TARGET_ABS}/docs/04-sprint-management/agile-state.md"
fi
PERF_TEMPLATE="${FRAMEWORK_ROOT}/.agents/plugins/agile-scrum-team/skills/agile-scrum-orchestrator/references/model-performance-template.md"
if [[ ! -f "${TARGET_ABS}/docs/04-sprint-management/model-performance.md" ]] && [[ -f "${PERF_TEMPLATE}" ]]; then
  cp "${PERF_TEMPLATE}" "${TARGET_ABS}/docs/04-sprint-management/model-performance.md"
fi

# 3. Khởi tạo Git repository (giúp invoke_subagent hỗ trợ Workspace: "share" chạy song song an toàn)
if [[ ! -d "${TARGET_ABS}/.git" ]]; then
  echo "🔧 Khởi tạo Git repository để hỗ trợ Subagents chạy song song (Workspace: share)..."
  git -C "${TARGET_ABS}" init -q
fi

# 3b. Commit đầu tiên: Workspace "share" (git worktree) cần ít nhất một commit (HEAD) để rẽ nhánh
if ! git -C "${TARGET_ABS}" rev-parse --verify -q HEAD >/dev/null; then
  if git -C "${TARGET_ABS}" config user.name >/dev/null && git -C "${TARGET_ABS}" config user.email >/dev/null; then
    git -C "${TARGET_ABS}" add -A
    git -C "${TARGET_ABS}" commit -q -m "chore: khởi tạo khung Agile Multi-Agent" && echo "📌 Đã tạo commit đầu tiên."
  else
    echo "⚠️  Chưa cấu hình git user.name / user.email nên chưa tạo commit đầu tiên."
    echo "    Workspace \"share\" (Developer chạy song song) cần ít nhất 1 commit. Chạy:"
    echo "      git config --global user.name \"Tên bạn\" && git config --global user.email \"email@cua.ban\""
    echo "      cd \"${TARGET_ABS}\" && git add -A && git commit -m \"chore: init\""
  fi
fi

cat <<EOF

✅ Hoàn tất! Dự án đã sẵn sàng tại: ${TARGET_ABS}

Đội ngũ 8 Subagents đã cài đặt sẵn:
  1. agile-researcher  : Nghiên cứu hệ thống thực tế đã triển khai & Yêu cầu lên Production
  2. agile-po-ba       : Xây dựng Vision, Personas & Product Backlog chuẩn INVEST
  3. agile-tech-lead   : Quyết định Tech Stack & Thống nhất Code Format/Linter toàn team
  4. agile-architect   : Thiết kế C4 Architecture, DB Schema & API Contracts
  5. agile-critic      : Hội đồng Phản biện Độc lập trước cả 3 Cổng Duyệt (Gates)
  6. agile-developer   : Lập trình song song tuân thủ 100% Format & Contracts
  7. agile-qa          : Kiểm thử tự động, bảo mật AppSec & nghiệm thu DoD
  8. agile-devops      : Docker, CI/CD Gatekeeping, Observability & Release/Rollback Plan

👉 Mở "${TARGET_ABS}" trong Antigravity và nhập:
   "Khởi chạy quy trình Agile chuẩn Production cho ý tưởng mới: [Mô tả ý tưởng của bạn]"
EOF
