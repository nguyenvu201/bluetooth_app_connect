---
role: kmp-pr
description: Tạo Pull Request tự động bằng GitHub CLI sau khi nhánh feature/fix được tạo.
---

# Agent: kmp-pr

**Purpose**: Khi một nhánh `feat/<ticket>` hoặc `fix/<ticket>` đã được push, tự động mở Pull Request tới `main` bằng lệnh `gh pr create`.

## Workflow Steps
1. **Determine branch name** – nhận từ Orchestrator (ví dụ `feat/BT-123`).
2. **Run GitHub CLI command**:
   ```bash
   gh pr create \
     --title "[${BRANCH}] Feature ${ticket}" \
     --body "Auto‑generated PR for ${BRANCH}." \
     --base main \
     --head ${BRANCH} \
     --label ${LABEL}
   ```
   - `${LABEL}` = `feature` nếu branch bắt đầu bằng `feat/`, ngược lại `bug`.
3. **Capture PR URL** và trả về cho Orchestrator.
4. **Optional**: Gắn tag `delegate` nếu người dùng không merge ngay (Orchestrator sẽ thực hiện khi nhận được tín hiệu).

## Tool Calls
- `run_command` – thực thi lệnh `gh pr create` (đánh dấu `SafeToAutoRun: true`).

## Expected Output
```
Pull request created: https://github.com/nguyenvu201/bluetooth_app_connect/pull/XX
```

> Yêu cầu: GitHub CLI (`gh`) phải được cài đặt và người dùng đã đăng nhập (`gh auth login`).
