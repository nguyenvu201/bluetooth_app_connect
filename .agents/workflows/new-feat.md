---
description: Workflow for creating a new feature (new-feat)
---

# new-feat Workflow

This workflow automates the end‑to‑end process for implementing a new feature through collaborative effort across multiple specialized agents.

## Steps
1. **Create Feature Branch** – The Orchestrator invokes the `kmp-branch` agent using the ticket identifier.
   ```bash
   # Orchestrator calls kmp-branch with ticket e.g. BT-123
   ```
2. **Context & Architecture Documentation** – The `kmp-architect` (or acting BA agent) analyzes requirements, defines tasks, and **MUST** explicitly create or update a context document in `docs/context/` (e.g., `docs/context/feat_<ticket>.md`) detailing the architecture, requirements, APIs, and UI changes.
3. **Core Development** – Task delegation to specialized dev agents (e.g. `kmp-compose` for UI, `kmp-ktor-backend` for server, `kmp-iot` for logic/hardware). Agents independently commit code to the feature branch.
4. **Local QA & Testing** – The `kmp-qa` agent locally evaluates the implementation, writes and executes necessary unit tests, and adds tests to cover edge cases.
5. **Local Security Scan** – The `kmp-security` agent scans the local branch implementation for any security vulnerabilities.
6. **Changelog & Doc Update** – The Orchestrator ensures `CHANGELOG.md` and any other relevant root documentation are updated with the new changes before the branch is pushed.
7. **Push Branch** – The `kmp-branch` agent pushes the finalized branch to `origin` and sets upstream.
8. **Open Pull Request** – The Orchestrator invokes the `kmp-pr` agent to create a PR via GitHub CLI.
   ```bash
   gh pr create --title "[feat/BT-123] Feature BT-123" \
       --body "Auto‑generated PR for feature BT-123" \
       --base main --head feat/BT-123 --label feature
   ```
8. **Code Review** – The `reviewer_logic` and `reviewer_style` agents execute a final review against the opened PR.
9. **FDA Gate Check** – Orchestrator validates FDA compliance JSON files.
10. **Merge or Delegate** – If all checks pass, the Orchestrator merges the PR; otherwise, it tags it with `delegate` for manual intervention.

> **Note:** The orchestrator manages the hand-offs between these different agents, ensuring FDA traceability steps are completed between phases.
