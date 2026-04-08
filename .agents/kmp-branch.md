---
role: kmp-branch
description: Tạo nhánh Git cho mỗi feature hoặc bug và push lên remote.
---

# Agent: kmp-branch

**Purpose**: Automate the creation of a new Git branch following the naming convention `feat/<ticket>` (or `fix/<ticket>`), checkout the branch, and push the initial commit to `origin`.

## Workflow Steps
1. **Receive ticket identifier** (e.g., `BT-123`).
2. **Determine branch prefix** – if the ticket type is `feature` use `feat/`, otherwise `fix/`.
3. **Run command** to create and checkout the branch:
   ```bash
   git checkout -b feat/<ticket>
   ```
4. **Push the branch** to remote and set upstream:
   ```bash
   git push -u origin feat/<ticket>
   ```
5. **Report** the new branch name back to the Orchestrator.

## Tool Calls
- `run_command` – to execute the Git commands (marked as safe to auto‑run).

## Expected Output
```
Branch 'feat/<ticket>' created and pushed to origin.
```

> The agent assumes the repository is already initialized and the user has push permissions.
