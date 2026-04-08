---
description: Workflow for fixing a bug (fix-bug)
---

# fix-bug Workflow

This workflow automates the process for addressing a bug collaboratively across multiple agents.

## Steps
1. **Create Bug Branch** – The Orchestrator invokes the `kmp-branch` agent with the ticket identifier.
   ```bash
   # Orchestrator calls kmp-branch with ticket e.g. BUG-456
   ```
2. **Context & Analysis** – Analytical agents (e.g., `kmp-architect` or `Orchestrator`) investigate the bug reports, understand the root cause, and propose a code-level fix. They **MUST** document this analysis in `docs/context/` (e.g., `docs/context/fix_<ticket>.md`) including the root cause and proposed resolution.
3. **Core Implementation** – The appropriate Dev agents (such as `kmp-compose`, `kmp-iot`, or `kmp-ktor-backend`) apply the code fix within the branch.
4. **Regression Testing** – The `kmp-qa` agent writes failing tests capturing the bug's behavior, runs them against the fix, and verifies the resolution locally.
5. **Security Verification** – The `kmp-security` agent ensures the patch does not introduce security risks or bypasses.
6. **Changelog & Doc Update** – The Orchestrator ensures `CHANGELOG.md` is updated with bug fix details before the branch is pushed.
7. **Push Branch** – The `kmp-branch` agent pushes the final commit to `origin` and sets upstream.
8. **Open Pull Request** – The `kmp-pr` agent is invoked to create a PR via GitHub CLI.
   ```bash
   gh pr create --title "[fix/BUG-456] Bug FIX-456" \
       --body "Auto‑generated PR for bug FIX-456" \
       --base main --head fix/BUG-456 --label bug
   ```
8. **Code Review** – The `reviewer_logic` and `reviewer_style` agents execute a final review against the PR's code structure.
9. **FDA Gate Check** – Orchestrator validates FDA compliance JSON files.
10. **Merge or Delegate** – If all checks pass, the Orchestrator merges the PR; otherwise, it assigns the `delegate` tag for manual review.

> **Note:** The orchestrator bridges tasks between all these specialized agents to maintain state.
