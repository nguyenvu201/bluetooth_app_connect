---
description: Implement a complete new feature on the KMP IoT tech stack
---

# New KMP Feature Workflow

Execute the complete feature development workflow using the KMP engineering team agents.

## Workflow Steps

0. **Khởi tạo context** (orchestrator)
   ```bash
   python .claude/skills/kmp-tools/scripts/context_manager.py init <feature-name> "<description>"
   ```

1. **Architecture Design** (kmp-architect)
   - Thiết kế module structure cho feature mới
   - Xác định platform targets (Android/Desktop/iOS/Server)
   - Tạo module dependency diagram
   - Viết ADR cho significant decisions
   - **Output**: `.claude/context/01_architect.json`

2. **Shared Module** (kmp-shared)
   - Domain entities và Repository interfaces
   - Fake implementations cho test + Desktop preview
   - Koin DI modules
   - **Output**: `.claude/context/02_shared.json`

3. **Ktor Backend** (kmp-ktor-backend)
   - API routes cho feature
   - Database schema với Exposed ORM
   - JWT authentication nếu cần
   - WebSocket endpoint cho real-time updates
   - **Output**: `.claude/context/04_ktor.json`

4. **Compose UI** (kmp-compose)
   - Voyager screens (`object : Screen`)
   - ViewModel với StateFlow
   - Koin registration
   - **Output**: `.claude/context/05_compose.json`

5. **Quality Assurance** (kmp-qa)
   - kotlin-test unit tests cho domain/usecase
   - ViewModel tests với runTest
   - Ktor API tests với testApplication
   - **Output**: `.claude/context/07_qa.json`

6. **DevOps** (kmp-devops)
   - Cập nhật Gradle dependencies nếu cần
   - Verify Docker build
   - GitHub Actions CI update
   - **Output**: `.claude/context/06_devops.json`

7. **Generate Documentation** (orchestrator — BẮT BUỘC)
   ```bash
   python .claude/skills/kmp-tools/scripts/doc_generator.py
   git add docs/ CHANGELOG.md
   git commit -m "docs: <feature-name> — update documentation"
   ```
   Creates:
   - `docs/features/<name>.md` — Full tech spec
   - `CHANGELOG.md` — Ghi nhận thay đổi
   - `docs/api/endpoints.md` — API reference
   - `docs/adrs/*.md` — Các architecture decisions

## Required Information

Cung cấp:
- Tên và mô tả feature
- Platform targets (Android only / Android + Desktop / all platforms)
- Có cần backend API không?
- Có cần real-time (WebSocket/MQTT) không?

---

**Orchestrator**: Bắt đầu step 0 để init context, sau đó coordinate các specialists theo dependency order. **Bước 7 là bắt buộc** — không bỏ qua bước generate docs.
