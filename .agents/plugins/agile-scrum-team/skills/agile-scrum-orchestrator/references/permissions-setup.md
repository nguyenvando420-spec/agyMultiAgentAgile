# Cấu Hình Quyền: Tự Chạy Lệnh, Chặn Lệnh Phá Hủy (người dùng tự áp dụng)

> Người dùng chọn ngày 12/11/2026: **chạy mọi lệnh không hỏi, nhưng chặn lệnh phá hủy**. Kiến trúc & luồng vẫn phải hỏi — phần đó do rule `.agents/rules/decision-gates.md` đảm nhiệm, không phải do cấu hình quyền.
> File cấu hình quyền nằm trong vùng bảo vệ hệ thống: **agent không được đọc/sửa**. Người dùng tự áp dụng theo một trong hai cách dưới đây.

## Cách 1 — Dùng trình quản lý quyền (khuyến nghị)
Trong `agy` gõ `/permissions`, rồi thêm:
- **Allow**: `command(*)`
- **Deny**: từng dòng trong mục "Danh sách chặn" bên dưới.

## Cách 2 — Sửa `~/.gemini/antigravity-cli/settings.json`
Thêm (hoặc gộp vào) khối `permissions`:

```json
{
  "permissions": {
    "allow": [
      "command(*)"
    ],
    "deny": [
      "command(regex:(?i).*\\b(rm|del|erase|rd|rmdir)\\b.*\\s(-rf|-fr|-r|/s)\\b.*)",
      "command(regex:(?i).*\\b(rm|ri|del|rd|rmdir|Remove-Item)\\b.*-Rec.*)",
      "command(regex:(?i).*\\b(Format-Volume|Clear-Disk|Initialize-Disk|diskpart|mkfs)\\b.*)",
      "command(regex:(?i).*\\bformat\\s+[a-z]:.*)",
      "command(regex:(?i).*\\bgit\\s+push\\b.*(--force|\\s-f\\b).*)",
      "command(regex:(?i).*\\bgit\\s+reset\\s+--hard.*)",
      "command(regex:(?i).*\\bgit\\s+clean\\s+-[a-z]*f.*)",
      "command(regex:(?i).*\\b(shutdown|Stop-Computer|Restart-Computer)\\b.*)",
      "command(regex:(?i).*\\breg\\s+delete\\b.*)",
      "command(regex:(?i).*\\b(takeown|cipher\\s+/w)\\b.*)",
      "command(regex:(?i).*--dangerously.*)"
    ]
  }
}
```

**Ý nghĩa danh sách chặn**: xóa đệ quy (`rm -rf`, `rd /s`, `Remove-Item -Recurse`), format/phân vùng ổ đĩa, `git push --force`, `git reset --hard`, `git clean -f…`, tắt/khởi động lại máy, xóa registry, chiếm quyền/xóa trắng ổ, và **mọi cờ `--dangerously…`** (để không agent nào tự mở phiên `agy`/`codex` bỏ qua quyền).

- Thứ tự ưu tiên của Antigravity: **Deny > Ask > Allow** → lệnh khớp danh sách chặn luôn bị chặn dù đã `allow command(*)`.
- Các lớp bảo vệ cứng của hệ thống vẫn hoạt động, không bị cấu hình này ghi đè.
- Danh sách chặn chỉ là lớp phòng vệ cơ bản (khớp chuỗi lệnh). Rule `decision-gates.md` cấm agent lách bằng cú pháp khác hay script trung gian.

## Kiểm tra sau khi áp dụng (an toàn, không xóa gì)
Nhờ Scrum Master chạy hai lệnh:
1. `Write-Output "hello"` → phải **tự chạy, không hỏi**.
2. `Write-Output "git reset --hard"` → chỉ in ra một chuỗi (vô hại), nhưng chuỗi lệnh khớp mẫu chặn nên phải **bị từ chối**. Nếu lệnh này vẫn chạy được thì danh sách chặn chưa có hiệu lực (sai cú pháp hoặc sai file) → báo lại để điều chỉnh.

## Codex
Codex chạy với sandbox `read-only` do `codex_task.py` đặt → không thể ghi file hay chạy lệnh làm thay đổi trạng thái, bất kể cấu hình trên. Không dùng `--dangerously-bypass-approvals-and-sandbox`.
