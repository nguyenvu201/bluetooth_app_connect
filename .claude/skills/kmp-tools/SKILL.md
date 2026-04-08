---
name: kmp-tools
description: Automation tooling cho Kotlin Multiplatform IoT project (caonguyen.vu). Scripts chạy được ngay để analyze, scaffold, và CI/CD pipeline cho KMP project với Voyager, HiveMQ MQTT, Ktor, Exposed, Koin.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# KMP Engineering Tools

> ✅ = Script đã implement, chạy ngay  
> 📋 = Planned stub (tạo khi cần)

## Stack thực tế của dự án

| Layer | Technology |
|-------|-----------|
| Package | `caonguyen.vu` |
| Navigation | Voyager (không phải Navigation Compose) |
| MQTT | HiveMQ Client (không phải Eclipse Paho) |
| Testing | `kotlin-test` + `kotlinx-coroutines-test` |
| DB ORM | Exposed + PostgreSQL |
| DI | Koin |
| RS485 | jSerialComm |

---

## 🏗 Architecture

### ✅ Module Dependency Analyzer
Scan toàn bộ `.kt` files, map vào KMP modules, detect circular deps, generate Mermaid diagram.
```bash
python .claude/skills/kmp-tools/scripts/architecture/module_analyzer.py .
python .claude/skills/kmp-tools/scripts/architecture/module_analyzer.py . --output docs/architecture
python .claude/skills/kmp-tools/scripts/architecture/module_analyzer.py . --json
```

---

## 📦 Shared Module Scaffolding

### ✅ Repository Scaffolder
Tạo: Domain model + Repository interface + Fake implementation + Unit tests (kotlin-test).
```bash
python .claude/skills/kmp-tools/scripts/shared/repository_scaffolder.py Device
python .claude/skills/kmp-tools/scripts/shared/repository_scaffolder.py SensorReading --dry-run
```
Output:
- `shared/.../models/Device.kt`
- `shared/.../repository/DeviceRepository.kt`
- `shared/.../repository/FakeDeviceRepository.kt`
- `shared/.../repository/FakeDeviceRepositoryTest.kt`
- `shared/.../repository/DeviceModule_HINT.txt` (Koin registration guide)

### 📋 UseCase Scaffolder (planned)
```bash
# Chưa có file — AI sẽ viết khi cần
python .claude/skills/kmp-tools/scripts/shared/usecase_scaffolder.py GetDevices Device
```

---

## 🎨 Compose Screen Generation

### ✅ Screen Generator (Voyager)
Tạo: Voyager Screen object + ViewModel + State + Event.
```bash
python .claude/skills/kmp-tools/scripts/compose/screen_generator.py Dashboard
python .claude/skills/kmp-tools/scripts/compose/screen_generator.py DeviceList --with-list
python .claude/skills/kmp-tools/scripts/compose/screen_generator.py SensorDetail --dry-run
```
Output:
- `composeApp/.../ui/{name}/{Name}State.kt`
- `composeApp/.../ui/{name}/{Name}ViewModel.kt`
- `composeApp/.../ui/{name}/{Name}Screen.kt` (Voyager `object : Screen`)

### 📋 Component Generator (planned)
```bash
python .claude/skills/kmp-tools/scripts/compose/component_generator.py DeviceCard
```

---

## 🖥️ Ktor Backend Scaffolding

### ✅ Route Scaffolder
Tạo: Exposed Table + DAO + Service + Ktor Route handler + Test.
```bash
python .claude/skills/kmp-tools/scripts/ktor/route_scaffolder.py Device
python .claude/skills/kmp-tools/scripts/ktor/route_scaffolder.py SensorReading --dry-run
```
Output:
- `server/.../database/{Name}Table.kt` (Exposed DSL)
- `server/.../database/{Name}Dao.kt`
- `server/.../service/{Name}Service.kt`
- `server/.../routes/{Name}Routes.kt`
- `server/src/test/.../{Name}RoutesTest.kt`

---

## 🚀 CI/CD

### ✅ GitHub Actions Generator
Tạo GitHub Actions CI (test + build) và CD (Docker deploy) workflows.
```bash
# Xem trước (dry run)
python .claude/skills/kmp-tools/scripts/cicd/cicd_generator.py --dry-run --all

# Tạo CI workflow (.github/workflows/ci.yml)
python .claude/skills/kmp-tools/scripts/cicd/cicd_generator.py --ci-only

# Tạo CD workflow + secrets checklist
python .claude/skills/kmp-tools/scripts/cicd/cicd_generator.py --cd-only

# Tất cả + cài git pre-commit hook
python .claude/skills/kmp-tools/scripts/cicd/cicd_generator.py --all
```

**CI workflow includes:**
- Test `:shared:jvmTest` + `:shared:allTests`  
- Test `:server:test` với PostgreSQL service container  
- Build Android debug APK  
- Build Desktop distribution  

**CD workflow includes:**
- Build multi-stage Docker image cho Ktor server  
- Push to GHCR (GitHub Container Registry)  
- Deploy to staging via SSH  
- Deploy to production (manual approval required)  

**Pre-commit script** (local):
```bash
# Cài vào git hook
cp .claude/skills/kmp-tools/scripts/cicd/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
# Sẽ chạy tự động trước mỗi git commit:
# - :shared:jvmTest
# - :server:test
# - quality_analyzer.py (score check)
```

---

## 🧪 QA / Testing

### ✅ Quality Analyzer
Phân tích Kotlin file stats, test ratio, Gradle health, coverage reports.
```bash
python .claude/skills/kmp-tools/scripts/qa/quality_analyzer.py .
python .claude/skills/kmp-tools/scripts/qa/quality_analyzer.py . --json
```

### ✅ Test Generator
Tạo kotlin-test specs cho Repository, ViewModel, UseCase, Service.
```bash
# Auto-detect type và module
python .claude/skills/kmp-tools/scripts/qa/test_generator.py --class DeviceRepository
python .claude/skills/kmp-tools/scripts/qa/test_generator.py --class DashboardViewModel
python .claude/skills/kmp-tools/scripts/qa/test_generator.py --class MqttGateway --module server

# Explicit type
python .claude/skills/kmp-tools/scripts/qa/test_generator.py --class DeviceRepository --type repository
python .claude/skills/kmp-tools/scripts/qa/test_generator.py --class ApplicationTest --type service --module server

# Preview
python .claude/skills/kmp-tools/scripts/qa/test_generator.py --class Device --dry-run
```

Chạy tests:
```bash
./gradlew :shared:jvmTest          # Fast — only JVM
./gradlew :shared:allTests         # All platforms
./gradlew :server:test             # Ktor server tests
./gradlew allTests                 # Everything
```

---

## ⚙️ DevOps / Build

### ✅ Build Health Check
Kiểm tra Gradle properties, version catalog, compatibility, Docker setup.
```bash
python .claude/skills/kmp-tools/scripts/devops/build_health_check.py
python .claude/skills/kmp-tools/scripts/devops/build_health_check.py --fix       # Auto-apply safe fixes
python .claude/skills/kmp-tools/scripts/devops/build_health_check.py --fix --dry-run
```

**Checks:**
- `org.gradle.caching=true` ✅
- Parallel builds, incremental Kotlin
- JVM heap size adequacy
- Version catalog presence + library compatibility
- All KMP module build files present
- Dockerfile + docker-compose presence

### 📋 Build Analyzer (planned)
```bash
python .claude/skills/kmp-tools/scripts/devops/build_analyzer.py --profile
```

---

## 📋 Common Options (tất cả scripts)

```bash
--dry-run    # Xem output mà không tạo file
--json       # Print JSON output to stdout (scripts có hỗ trợ)
```

---

## Summary — Scripts đã implement ✅

| Script | Chạy | Mục đích |
|--------|------|---------|
| `architecture/module_analyzer.py` | ✅ | Kotlin module deps + Mermaid |
| `shared/repository_scaffolder.py` | ✅ | Repository + Fake + Test |
| `compose/screen_generator.py` | ✅ | Voyager Screen + VM + State |
| `ktor/route_scaffolder.py` | ✅ | Table + DAO + Service + Route + Test |
| `cicd/cicd_generator.py` | ✅ | GitHub Actions CI/CD + pre-commit |
| `qa/quality_analyzer.py` | ✅ | KMP quality score + recs |
| `qa/test_generator.py` | ✅ | kotlin-test spec generator |
| `devops/build_health_check.py` | ✅ | Gradle / version health |
| `context_manager.py` | ✅ | Agent workflow state management |
| `doc_generator.py` | ✅ | Auto-generate docs từ workflow context |

## 📄 doc_generator.py — Documentation Generator

Tự động generate / cập nhật toàn bộ `docs/` từ các workflow context files.
**Chạy bắt buộc sau khi hoàn thành bất kỳ workflow nào.**

```bash
# Generate tất cả (sau khi workflow xong)
python .claude/skills/kmp-tools/scripts/doc_generator.py

# Từng phần
python .claude/skills/kmp-tools/scripts/doc_generator.py --changelog     # CHANGELOG.md
python .claude/skills/kmp-tools/scripts/doc_generator.py --feature       # docs/features/<name>.md
python .claude/skills/kmp-tools/scripts/doc_generator.py --architecture  # docs/architecture/
python .claude/skills/kmp-tools/scripts/doc_generator.py --api           # docs/api/endpoints.md
python .claude/skills/kmp-tools/scripts/doc_generator.py --adrs          # docs/adrs/
python .claude/skills/kmp-tools/scripts/doc_generator.py --dry-run       # Preview
```

**Output:**

```
docs/
├── README.md              # Docs index (auto-generated)
├── features/
│   └── <workflow-name>.md # Full tech spec của feature
├── api/
│   └── endpoints.md       # REST + WebSocket + MQTT reference
├── architecture/
│   └── overview.md        # Tech stack, module structure, principles
├── adrs/
│   └── adr_001_*.md       # Architecture Decision Records
└── guides/
    └── dev-setup.md       # Getting started guide
```
