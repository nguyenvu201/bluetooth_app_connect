#!/usr/bin/env python3
"""
KMP Documentation Generator
Tự động tạo / cập nhật documents từ context files sau khi hoàn thành workflow.

Đọc .claude/context/NN_agent.json → sinh ra markdown docs trong docs/

Usage:
  python doc_generator.py                  # Generate từ workflow hiện tại
  python doc_generator.py --feature        # Feature docs only
  python doc_generator.py --architecture   # Architecture docs only
  python doc_generator.py --api            # API reference only
  python doc_generator.py --all            # Tất cả (mặc định)
  python doc_generator.py --dry-run        # Preview
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

# ─── Path setup ──────────────────────────────────────────────────────────────
def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir() and (parent / ".claude" / "agents").is_dir():
            return parent
    return current.parents[5]

PROJECT_ROOT = _find_project_root()
CONTEXT_DIR  = PROJECT_ROOT / ".claude/context"
DOCS_DIR     = PROJECT_ROOT / "docs"


# ─── Context helpers ──────────────────────────────────────────────────────────
def read_ctx(fname: str) -> dict:
    p = CONTEXT_DIR / fname
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def write_doc(path: Path, content: str, dry_run: bool):
    if dry_run:
        print(f"  [DRY RUN] {path.relative_to(PROJECT_ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✅ {path.relative_to(PROJECT_ROOT)}")


# ─── 1. CHANGELOG ─────────────────────────────────────────────────────────────
def generate_changelog(dry_run: bool):
    """Append new entry to CHANGELOG.md from workflow context."""
    wf   = read_ctx("00_workflow.json")
    arch = read_ctx("01_architect.json")
    sh   = read_ctx("02_shared.json")
    kt   = read_ctx("04_ktor.json")
    cp   = read_ctx("05_compose.json")
    qa   = read_ctx("07_qa.json")
    sec  = read_ctx("08_security.json")

    if not wf:
        print("  ⏭️  No workflow context — skipping CHANGELOG")
        return

    feature   = wf.get("workflow", {}).get("feature", "Unknown feature")
    ts        = wf.get("workflow", {}).get("started_at", now_str())[:10]
    wf_name   = wf.get("workflow", {}).get("name", "unnamed")

    # Collect what changed
    models    = [m["name"] for m in sh.get("outputs", {}).get("domain_models", [])]
    repos     = [r["interface"] for r in sh.get("outputs", {}).get("repositories", [])]
    routes    = [f"{r['method']} {r['path']}" for r in kt.get("outputs", {}).get("routes", [])]
    screens   = [s["name"] for s in cp.get("outputs", {}).get("screens", [])]
    adrs      = [a["id"] + ": " + a["title"] for a in arch.get("outputs", {}).get("adrs", [])]
    tests_ok  = qa.get("outputs", {}).get("all_tests_pass", None)
    crit_sec  = sec.get("outputs", {}).get("critical_issues", [])

    entry = f"\n## [{ts}] {feature}\n\n"
    entry += f"> Feature ID: `{wf_name}`\n\n"

    if models:
        entry += "### 🆕 Domain Models\n"
        for m in models:
            entry += f"- `{m}`\n"
        entry += "\n"

    if repos:
        entry += "### 📦 Repositories\n"
        for r in repos:
            entry += f"- `{r}`\n"
        entry += "\n"

    if routes:
        entry += "### 🖥️ API Endpoints\n"
        for r in routes:
            entry += f"- `{r}`\n"
        entry += "\n"

    if screens:
        entry += "### 🎨 UI Screens\n"
        for s in screens:
            entry += f"- `{s}`\n"
        entry += "\n"

    if adrs:
        entry += "### 🏛️ Architecture Decisions\n"
        for a in adrs:
            entry += f"- {a}\n"
        entry += "\n"

    if tests_ok is True:
        entry += "### ✅ Testing\n- All tests pass\n\n"
    elif tests_ok is False:
        entry += "### ⚠️ Testing\n- Tests failing — see `07_qa.json`\n\n"

    if crit_sec:
        entry += "### 🔒 Security Issues\n"
        for issue in crit_sec:
            entry += f"- ⚠️ {issue}\n"
        entry += "\n"

    entry += "---\n"

    changelog_path = PROJECT_ROOT / "CHANGELOG.md"
    if changelog_path.exists():
        existing = changelog_path.read_text(encoding="utf-8")
        # Insert after header line
        lines = existing.split("\n")
        header_end = next((i for i, l in enumerate(lines) if l.startswith("## ")), 1)
        new_content = "\n".join(lines[:header_end]) + "\n" + entry + "\n".join(lines[header_end:])
    else:
        new_content = (
            "# Changelog\n\n"
            "Tất cả thay đổi quan trọng của dự án được ghi lại tại đây theo feature.\n\n"
            "Format: `[YYYY-MM-DD] Feature description`\n\n"
            "---\n" + entry
        )

    write_doc(changelog_path, new_content, dry_run)


# ─── 2. FEATURE DOC ───────────────────────────────────────────────────────────
def generate_feature_doc(dry_run: bool):
    """Create docs/features/<name>.md for the completed feature."""
    wf   = read_ctx("00_workflow.json")
    arch = read_ctx("01_architect.json")
    sh   = read_ctx("02_shared.json")
    iot  = read_ctx("03_iot.json")
    kt   = read_ctx("04_ktor.json")
    cp   = read_ctx("05_compose.json")
    qa   = read_ctx("07_qa.json")
    sec  = read_ctx("08_security.json")

    if not wf:
        print("  ⏭️  No workflow context — skipping feature doc")
        return

    wf_data   = wf.get("workflow", {})
    feature   = wf_data.get("feature", "Unknown")
    wf_name   = wf_data.get("name", "unnamed")
    platforms = wf_data.get("platforms", [])
    ts        = now_str()

    doc = f"# {feature}\n\n"
    doc += f"> **Feature ID**: `{wf_name}`  \n"
    doc += f"> **Updated**: {ts}  \n"
    doc += f"> **Platforms**: {', '.join(platforms) if platforms else 'All'}\n\n"

    # Overview
    doc += "## Overview\n\n"
    doc += f"{feature}.\n\n"

    # Architecture Decisions
    adrs = arch.get("outputs", {}).get("adrs", [])
    if adrs:
        doc += "## Architecture Decisions\n\n"
        doc += "| ADR | Decision | Status |\n|-----|----------|--------|\n"
        for adr in adrs:
            doc += f"| {adr.get('id','')} | {adr.get('title', '')} | {adr.get('status', '')} |\n"
        doc += "\n"

    # Data Models
    models = sh.get("outputs", {}).get("domain_models", [])
    if models:
        doc += "## Domain Models\n\n"
        for m in models:
            doc += f"### `{m['name']}`\n\n"
            if "file" in m:
                doc += f"**File**: `{m['file']}`\n\n"
            if "fields" in m:
                doc += "```kotlin\ndata class " + m["name"] + "(\n"
                for f in m["fields"]:
                    doc += f"    val {f},\n"
                doc += ")\n```\n\n"

    # Repositories
    repos = sh.get("outputs", {}).get("repositories", [])
    if repos:
        doc += "## Repositories\n\n"
        for r in repos:
            doc += f"- **`{r.get('interface', '')}`** → `{r.get('fake_impl', '')}`\n"
            if "file" in r:
                doc += f"  - File: `{r['file']}`\n"
        doc += "\n"

    # IoT
    iot_outputs = iot.get("outputs", {})
    if iot_outputs:
        doc += "## IoT Integration\n\n"
        devices = iot_outputs.get("devices", [])
        if devices:
            doc += "### Devices\n\n"
            doc += "| ID Prefix | Type | Sensors | Actuators |\n|-----------|------|---------|----------|\n"
            for d in devices:
                sensors = ", ".join(d.get("sensors", []))
                actors  = ", ".join(d.get("actuators", []))
                doc += f"| `{d.get('id_prefix','')}` | {d.get('type','')} | {sensors} | {actors} |\n"
            doc += "\n"

        mqtt = iot_outputs.get("mqtt_topics", {})
        if mqtt:
            doc += "### MQTT Topics\n\n"
            doc += "**Subscribe** (server listens):\n"
            for t in mqtt.get("subscribe", []):
                doc += f"- `{t}`\n"
            doc += "\n**Publish** (server sends):\n"
            for t in mqtt.get("publish", []):
                doc += f"- `{t}`\n"
            doc += "\n"

        flow = iot_outputs.get("data_flow", "")
        if flow:
            doc += f"### Data Flow\n\n`{flow}`\n\n"

    # API Endpoints
    routes = kt.get("outputs", {}).get("routes", [])
    ws     = kt.get("outputs", {}).get("websocket_endpoints", [])
    if routes or ws:
        doc += "## API Reference\n\n"
        if routes:
            doc += "### REST Endpoints\n\n"
            doc += "| Method | Path | Auth | Handler |\n|--------|------|------|--------|\n"
            for r in routes:
                auth = r.get("auth", "none")
                handler = r.get("handler", "").split("/")[-1] if r.get("handler") else "-"
                doc += f"| `{r['method']}` | `{r['path']}` | {auth} | `{handler}` |\n"
            doc += "\n"
        if ws:
            doc += "### WebSocket Endpoints\n\n"
            for w in ws:
                doc += f"- `{w}`\n"
            doc += "\n"

    # UI Screens
    screens = cp.get("outputs", {}).get("screens", [])
    if screens:
        doc += "## UI Screens\n\n"
        for s in screens:
            doc += f"### `{s['name']}`\n\n"
            if "file" in s:
                doc += f"**File**: `{s['file']}`  \n"
            if "viewmodel" in s:
                doc += f"**ViewModel**: `{s['viewmodel']}`  \n"
            if "navigator" in s:
                doc += f"**Navigator**: {s['navigator']}  \n"
            state = s.get("state_fields", [])
            if state:
                doc += "\n**State fields**:\n"
                for sf in state:
                    doc += f"- `{sf}`\n"
            doc += "\n"

    # Testing
    qa_out = qa.get("outputs", {})
    tests  = qa_out.get("tests_created", [])
    cov    = qa_out.get("coverage", {})
    if tests or cov:
        doc += "## Testing\n\n"
        if cov:
            doc += "### Coverage\n\n"
            doc += "| Layer | Coverage |\n|-------|----------|\n"
            for k, v in cov.items():
                label = k.replace("_pct", "").replace("_", " ").title()
                doc += f"| {label} | {v}% |\n"
            doc += "\n"
        if tests:
            doc += "### Test Files\n\n"
            for t in tests:
                doc += f"- `{t.get('file', '')}` — {t.get('type', '')} ({t.get('count', '?')} tests)\n"
            doc += "\n"
        run_cmd = qa_out.get("run_command", "./gradlew allTests")
        doc += f"```bash\n{run_cmd}\n```\n\n"

    # Security
    sec_out = sec.get("outputs", {})
    high    = sec_out.get("high_issues", [])
    crit    = sec_out.get("critical_issues", [])
    if crit or high:
        doc += "## Security Notes\n\n"
        for i in crit:
            doc += f"- 🔴 **CRITICAL**: {i}\n"
        for i in high:
            doc += f"- 🟠 **HIGH**: {i}\n"
        doc += "\n"

    # Koin registrations
    koin = cp.get("outputs", {}).get("koin_registrations", [])
    km   = sh.get("outputs", {}).get("koin_module", {}).get("bindings", [])
    if koin or km:
        doc += "## Koin DI Registrations\n\n```kotlin\n"
        for k in km:
            doc += f"// shared: {k}\n"
        for k in koin:
            doc += f"// composeApp: {k}\n"
        doc += "```\n\n"

    out_path = DOCS_DIR / "features" / f"{wf_name}.md"
    write_doc(out_path, doc, dry_run)


# ─── 3. ARCHITECTURE DOC ──────────────────────────────────────────────────────
def generate_architecture_doc(dry_run: bool):
    """Update docs/architecture/overview.md từ module analyzer output + context."""
    # Run module analyzer to get fresh data
    import subprocess
    result = subprocess.run(
        ["python3", ".claude/skills/kmp-tools/scripts/architecture/module_analyzer.py",
         ".", "--json"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )

    arch_ctx = read_ctx("01_architect.json")
    adrs     = arch_ctx.get("outputs", {}).get("adrs", [])

    doc = f"# Architecture Overview\n\n"
    doc += f"> **Updated**: {now_str()}\n\n"

    doc += "## Module Structure\n\n"
    doc += "```\n"
    doc += "KMPRoadMap/\n"
    doc += "├── shared/          # KMP shared business logic (commonMain)\n"
    doc += "│   ├── models/      # Domain data classes\n"
    doc += "│   ├── repository/  # Repository interfaces + Fake implementations\n"
    doc += "│   ├── network/     # MQTT client interface\n"
    doc += "│   └── di/          # Koin shared module\n"
    doc += "├── composeApp/      # Compose Multiplatform UI\n"
    doc += "│   └── ui/          # Screens + ViewModels (Voyager)\n"
    doc += "├── server/          # Ktor backend (JVM)\n"
    doc += "│   ├── database/    # Exposed ORM tables + DAOs\n"
    doc += "│   ├── routes/      # Ktor REST route handlers\n"
    doc += "│   ├── service/     # Business services\n"
    doc += "│   └── mqtt/        # HiveMQ/MQTT gateway\n"
    doc += "└── iosApp/          # iOS wrapper\n"
    doc += "```\n\n"

    doc += "## Tech Stack\n\n"
    doc += "| Layer | Technology | Version |\n"
    doc += "|-------|-----------|--------|\n"
    doc += "| Language | Kotlin Multiplatform | 2.3.0 |\n"
    doc += "| UI | Compose Multiplatform | 1.10.0 |\n"
    doc += "| Navigation | Voyager | 1.1.0-beta03 |\n"
    doc += "| Backend | Ktor (Netty) | 3.3.3 |\n"
    doc += "| Database | Exposed + PostgreSQL | 0.49.0 |\n"
    doc += "| DI | Koin | 3.6.0 |\n"
    doc += "| MQTT Client | HiveMQ | 1.3.3 |\n"
    doc += "| RS485 | jSerialComm | 2.10.4 |\n"
    doc += "| Testing | kotlin-test + coroutines-test | 2.3.0 |\n"
    doc += "| Auth | Ktor JWT | 3.3.3 |\n"
    doc += "\n"

    doc += "## Module Dependencies\n\n"
    doc += "```mermaid\ngraph TD\n"
    doc += "    composeApp[\"📱 composeApp\\nCompose Multiplatform UI\"]\n"
    doc += "    shared[\"🔷 shared\\nKMP Domain Logic\"]\n"
    doc += "    server[\"🖥️ server\\nKtor Backend\"]\n"
    doc += "    composeApp --> shared\n"
    doc += "    server --> shared\n"
    doc += "```\n\n"

    doc += "## Architecture Principles\n\n"
    doc += "1. **KMP-first**: Tối đa code trong `commonMain`, tối thiểu platform-specific\n"
    doc += "2. **Repository pattern**: Interface ở `shared/`, Fake impl cho tests và Desktop preview\n"
    doc += "3. **Unidirectional Data Flow**: ViewModel → StateFlow → Compose UI\n"
    doc += "4. **IoT Data Flow**: `ESP8266 → MQTT(HiveMQ) → Ktor → WebSocket → Compose`\n"
    doc += "5. **Coroutine Safety**: Không dùng GlobalScope, tất cả qua structured concurrency\n\n"

    if adrs:
        doc += "## Architecture Decision Records\n\n"
        doc += "| ID | Title | Status |\n|----|-------|--------|\n"
        for adr in adrs:
            doc += f"| {adr.get('id','')} | {adr.get('title','')} | {adr.get('status','?')} |\n"
        doc += "\n> See `docs/adrs/` for full ADR documents.\n\n"

    write_doc(DOCS_DIR / "architecture" / "overview.md", doc, dry_run)


# ─── 4. API REFERENCE ─────────────────────────────────────────────────────────
def generate_api_reference(dry_run: bool):
    """Generate / update docs/api/endpoints.md from ktor context."""
    kt  = read_ctx("04_ktor.json")
    iot = read_ctx("03_iot.json")

    if not kt:
        print("  ⏭️  No ktor context — skipping API reference")
        return

    kt_out = kt.get("outputs", {})
    routes = kt_out.get("routes", [])
    ws     = kt_out.get("websocket_endpoints", [])
    jwt    = kt_out.get("jwt_config", {})
    health = kt_out.get("health_endpoint", "/health")

    doc = f"# API Reference\n\n"
    doc += f"> **Updated**: {now_str()}\n\n"
    doc += f"**Base URL**: `http://localhost:8085`  \n"
    doc += f"**Health**: `GET {health}`\n\n"

    doc += "## Authentication\n\n"
    doc += "JWT Bearer token required for protected endpoints.\n\n"
    doc += "```http\nAuthorization: Bearer <token>\n```\n\n"
    if jwt:
        doc += f"- **Issuer**: `{jwt.get('issuer', 'iot-server')}`\n"
        doc += f"- **Expiry**: {jwt.get('expiry_hours', 1)} hour(s)\n\n"

    doc += "### Login\n\n"
    doc += "```http\nPOST /api/auth/login\nContent-Type: application/json\n\n"
    doc += '{"email": "admin@iot.local", "password": "..."}\n```\n\n'

    if routes:
        doc += "## REST Endpoints\n\n"
        # Group by resource
        groups: dict = {}
        for r in routes:
            path  = r.get("path", "/")
            parts = path.strip("/").split("/")
            group = parts[1] if len(parts) > 1 else "misc"
            groups.setdefault(group, []).append(r)

        for group, group_routes in sorted(groups.items()):
            doc += f"### `/{group}`\n\n"
            doc += "| Method | Path | Auth | Description |\n|--------|------|------|-------------|\n"
            for r in group_routes:
                auth = "🔒 JWT" if r.get("auth") and r.get("auth") != "none" else "Public"
                doc += f"| `{r['method']}` | `{r['path']}` | {auth} | |\n"
            doc += "\n"

    if ws:
        doc += "## WebSocket Endpoints\n\n"
        doc += "| Endpoint | Description |\n|----------|-------------|\n"
        for w in ws:
            doc += f"| `{w}` | Real-time data stream |\n"
        doc += "\n"

    # MQTT
    iot_out = iot.get("outputs", {})
    mqtt = iot_out.get("mqtt_topics", {})
    schemas = iot_out.get("payload_schemas", {})
    if mqtt:
        doc += "## MQTT Topics (HiveMQ)\n\n"
        doc += f"**Broker**: `tcp://localhost:1883`\n\n"
        doc += "### Subscribe (server → listens)\n\n"
        for t in mqtt.get("subscribe", []):
            doc += f"- `{t}`\n"
        doc += "\n### Publish (server → device)\n\n"
        for t in mqtt.get("publish", []):
            doc += f"- `{t}`\n"
        doc += "\n"

        if schemas:
            doc += "### Payload Schemas\n\n"
            for name, schema in schemas.items():
                doc += f"**`{name}`**:\n```json\n{{\n"
                for k, v in schema.items():
                    doc += f'  "{k}": {v}\n'
                doc += "}\n```\n\n"

    doc += "## Error Responses\n\n"
    doc += "```json\n{\"error\": \"message\", \"code\": \"ERROR_CODE\"}\n```\n\n"
    doc += "| HTTP Code | Meaning |\n|-----------|--------|\n"
    doc += "| 200 | OK |\n"
    doc += "| 201 | Created |\n"
    doc += "| 400 | Bad request (validation failed) |\n"
    doc += "| 401 | Unauthorized (missing/invalid JWT) |\n"
    doc += "| 404 | Not found |\n"
    doc += "| 500 | Internal server error |\n"

    write_doc(DOCS_DIR / "api" / "endpoints.md", doc, dry_run)


# ─── 5. ADR DOC ───────────────────────────────────────────────────────────────
def generate_adrs(dry_run: bool):
    """Create individual ADR files in docs/adrs/."""
    arch = read_ctx("01_architect.json")
    adrs = arch.get("outputs", {}).get("adrs", [])

    if not adrs:
        return

    wf      = read_ctx("00_workflow.json")
    feature = wf.get("workflow", {}).get("feature", "")
    ts      = now_str()

    for adr in adrs:
        adr_id   = adr.get("id", "ADR-000")
        title    = adr.get("title", "Untitled")
        decision = adr.get("decision", "")
        status   = adr.get("status", "proposed")

        slug = adr_id.lower().replace("-", "_") + "_" + re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        out_path = DOCS_DIR / "adrs" / f"{slug}.md"

        if out_path.exists() and not dry_run:
            # Update status only
            content = out_path.read_text(encoding="utf-8")
            content = re.sub(r"Trạng thái: .+", f"Trạng thái: **{status}**", content)
            out_path.write_text(content, encoding="utf-8")
            print(f"  🔄 Updated: {out_path.relative_to(PROJECT_ROOT)}")
            continue

        doc = f"# {adr_id}: {title}\n\n"
        doc += f"> **Trạng thái**: **{status}**  \n"
        doc += f"> **Ngày tạo**: {ts}  \n"
        doc += f"> **Feature**: {feature}\n\n"
        doc += "## Context\n\n_Mô tả vấn đề tại sao cần quyết định này._\n\n"
        doc += "## Decision\n\n"
        doc += f"{decision}\n\n"
        doc += "## Consequences\n\n"
        doc += "**Tích cực:**\n- _Liệt kê ở đây_\n\n"
        doc += "**Tiêu cực:**\n- _Liệt kê ở đây_\n\n"
        doc += "## Alternatives Considered\n\n_Các phương án khác đã xem xét._\n"

        write_doc(out_path, doc, dry_run)


# ─── 6. DEV SETUP / README ────────────────────────────────────────────────────
def generate_dev_setup(dry_run: bool):
    """Create docs/guides/dev-setup.md — getting started guide."""
    out_path = DOCS_DIR / "guides" / "dev-setup.md"
    if out_path.exists():
        print(f"  ⏭️  Exists (manual edit recommended): {out_path.relative_to(PROJECT_ROOT)}")
        return

    doc = """# Developer Setup Guide

> **Updated**: {ts}

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| JDK | 17+ | `brew install temurin@17` |
| Android Studio | Hedgehog+ | [developer.android.com](https://developer.android.com/studio) |
| Docker | 24.0+ | [docker.com](https://docker.com) |
| Python | 3.11+ | `brew install python` |
| IntelliJ IDEA | 2024.1+ | For server development |

## Quick Start

```bash
# 1. Clone project
git clone <repo-url>
cd KMPRoadMap

# 2. Start backend services (PostgreSQL + MQTT + Ktor)
docker-compose up -d

# 3. Run Android app
./gradlew :composeApp:installDebug

# 4. Run Desktop app
./gradlew :composeApp:run

# 5. Run Server locally (without Docker)
./gradlew :server:run
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
JWT_SECRET=<min-32-char-random-string>
DB_PASSWORD=<postgres-password>
MQTT_USERNAME=ktor-server
MQTT_PASSWORD=<mqtt-password>
DATABASE_URL=jdbc:postgresql://localhost:5432/iotdb
```

Generate JWT secret:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Project Structure

```
KMPRoadMap/
├── shared/          # KMP shared module (domain logic)
├── composeApp/      # Android + Desktop UI
├── server/          # Ktor backend
├── iosApp/          # iOS wrapper
├── docs/            # Project documentation ← you are here
│   ├── features/    # Feature-level docs
│   ├── api/         # API reference
│   ├── architecture/ # Architecture overview
│   ├── adrs/        # Architecture Decision Records
│   └── guides/      # Developer guides
└── .claude/         # AI agent configuration
    ├── agents/      # Specialized agents
    ├── commands/    # Workflow commands
    └── skills/      # Automation scripts
```

## AI Agent Workflow

```bash
# Khởi tạo workflow mới
python .claude/skills/kmp-tools/scripts/context_manager.py init <feature-name> "<description>"

# Xem trạng thái
python .claude/skills/kmp-tools/scripts/context_manager.py status

# Generate docs sau khi xong
python .claude/skills/kmp-tools/scripts/doc_generator.py --all
```

## Running Tests

```bash
# Tất cả tests
./gradlew allTests

# Chỉ shared module (nhanh hơn)
./gradlew :shared:jvmTest

# Server tests (cần PostgreSQL running)
./gradlew :server:test
```

## Code Style

- Kotlin: follow [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html)
- Package: `caonguyen.vu.*`
- SharedMain first: implement logic trong `commonMain` trước, platform-specific sau
""".format(ts=now_str())

    write_doc(out_path, doc, dry_run)


# ─── 7. UPDATE docs/README (index) ────────────────────────────────────────────
def generate_docs_index(dry_run: bool):
    """Generate/update docs/README.md as the main docs index."""
    features_dir = DOCS_DIR / "features"
    feature_files = sorted(features_dir.glob("*.md")) if features_dir.exists() else []

    adrs_dir  = DOCS_DIR / "adrs"
    adr_files = sorted(adrs_dir.glob("*.md")) if adrs_dir.exists() else []

    doc = "# KMP IoT — Documentation\n\n"
    doc += f"> Last updated: {now_str()}\n\n"

    doc += "## 📁 Structure\n\n"
    doc += "| Directory | Content |\n|-----------|---------|\n"
    doc += "| `features/` | Feature-level docs (1 file per feature) |\n"
    doc += "| `api/` | REST + WebSocket + MQTT API reference |\n"
    doc += "| `architecture/` | Module structure, tech stack, module deps |\n"
    doc += "| `adrs/` | Architecture Decision Records |\n"
    doc += "| `guides/` | Developer setup, deployment, troubleshooting |\n"
    doc += "\n"

    doc += "## 🚀 Features\n\n"
    if feature_files:
        for f in feature_files:
            name = f.stem.replace("-", " ").replace("_", " ").title()
            doc += f"- [{name}](features/{f.name})\n"
    else:
        doc += "_No features documented yet. Run `doc_generator.py` after completing a workflow._\n"
    doc += "\n"

    doc += "## 🏛️ Architecture\n\n"
    doc += "- [Overview](architecture/overview.md)\n"
    doc += "- [Module Dependency Analysis](architecture/kmp-dependency-analysis.md)\n\n"

    doc += "## 📖 API\n\n"
    doc += "- [Endpoints](api/endpoints.md)\n\n"

    if adr_files:
        doc += "## ⚖️ Architecture Decisions (ADR)\n\n"
        for f in adr_files:
            name = f.stem.replace("_", " ").title()
            doc += f"- [{name}](adrs/{f.name})\n"
        doc += "\n"

    doc += "## 🛠️ Guides\n\n"
    doc += "- [Developer Setup](guides/dev-setup.md)\n\n"

    doc += "---\n\n"
    doc += "_Generated automatically by `.claude/skills/kmp-tools/scripts/doc_generator.py`_\n"

    write_doc(DOCS_DIR / "README.md", doc, dry_run)


# ─── FDA-8: SRS Addendum ──────────────────────────────────────────────────────
def generate_srs(dry_run: bool):
    """Generate docs/SRS/SRS-NNN_<feature>.md from architect + shared context."""
    wf   = read_ctx("00_workflow.json")
    arch = read_ctx("01_architect.json")
    sh   = read_ctx("02_shared.json")
    iot  = read_ctx("03_iot.json")
    kt   = read_ctx("04_ktor.json")
    cp   = read_ctx("05_compose.json")

    if not wf:
        print("  ⏭️  No workflow context — skipping SRS")
        return

    wf_data  = wf.get("workflow", {})
    feature  = wf_data.get("feature", "Unknown")
    wf_name  = wf_data.get("name", "unnamed")
    ts       = now_str()

    # Determine next SRS doc number
    srs_dir = DOCS_DIR / "SRS"
    existing = sorted(srs_dir.glob("SRS-*.md")) if srs_dir.exists() else []
    next_num = len(existing) + 1  # SRS-001 is master, features start at 002
    doc_id   = f"SRS-{next_num:03d}"
    slug     = re.sub(r"[^a-z0-9]+", "-", wf_name.lower()).strip("-")
    out_path = srs_dir / f"{doc_id}_{slug}.md"

    # Collect requirements from _fda blocks
    arch_reqs = arch.get("_fda", {}).get("requirements_implemented", [])
    sh_reqs   = sh.get("_fda", {}).get("requirements_implemented", [])
    iot_reqs  = iot.get("_fda", {}).get("requirements_implemented", [])
    kt_reqs   = kt.get("_fda", {}).get("requirements_implemented", [])
    cp_reqs   = cp.get("_fda", {}).get("requirements_implemented", [])

    all_parent_reqs = sorted(set(arch_reqs + sh_reqs + iot_reqs + kt_reqs + cp_reqs))

    # Collect new domain models as functional requirements
    models  = sh.get("outputs", {}).get("domain_models", [])
    routes  = kt.get("outputs", {}).get("routes", [])
    screens = cp.get("outputs", {}).get("screens", [])
    devices = iot.get("outputs", {}).get("devices", [])
    mqtt    = iot.get("outputs", {}).get("mqtt_topics", {})
    adrs    = arch.get("outputs", {}).get("adrs", [])

    doc  = f"# {doc_id}: Software Requirements — {feature}\n\n"
    doc += f"| Field | Value |\n|-------|-------|\n"
    doc += f"| **Document ID** | {doc_id} |\n"
    doc += f"| **Version** | 1.0.0 |\n"
    doc += f"| **Status** | DRAFT |\n"
    doc += f"| **Author** | kmp-architect |\n"
    doc += f"| **Created** | {ts[:10]} |\n"
    doc += f"| **Feature ID** | `{wf_name}` |\n"
    doc += f"| **Parent SRS** | SRS-001 |\n"
    doc += f"| **Standard** | IEC 62304 §5.2 |\n\n---\n\n"

    doc += "## 1. Feature Overview\n\n"
    doc += f"{feature}.\n\n"

    # Parent requirements satisfied
    if all_parent_reqs:
        doc += "## 2. Parent Requirements Addressed\n\n"
        doc += "This feature contributes to the following system-level requirements (SRS-001):\n\n"
        for r in all_parent_reqs:
            doc += f"- `{r}`\n"
        doc += "\n"

    # Architecture decisions
    if adrs:
        doc += "## 3. Architecture Decisions\n\n"
        doc += "| ADR ID | Title | Status |\n|--------|-------|--------|\n"
        for a in adrs:
            doc += f"| `{a.get('id','')}` | {a.get('title','')} | {a.get('status','')} |\n"
        doc += "\n"

    # Functional requirements derived from outputs
    req_counter = 1
    feature_prefix = re.sub(r"[^A-Z0-9]", "", wf_name.upper())[:4] or "FT"

    doc += "## 4. Feature-Specific Requirements\n\n"
    doc += "> IDs below are feature-scoped. Format: `REQ-<FEATURE>-<NNN>`\n\n"

    if models:
        doc += "### 4.1 Domain Model Requirements\n\n"
        for m in models:
            rid = f"REQ-{feature_prefix}-{req_counter:03d}"
            req_counter += 1
            doc += f"**{rid}** — The system SHALL provide a `{m['name']}` domain model"
            if m.get("fields"):
                doc += f" with fields: {', '.join(f'`{f}`' for f in m['fields'][:5])}"
            doc += ".\n\n"

    if routes:
        doc += "### 4.2 API Requirements\n\n"
        for r in routes:
            rid = f"REQ-{feature_prefix}-{req_counter:03d}"
            req_counter += 1
            auth_note = " with JWT auth" if r.get("auth") and r.get("auth") != "none" else ""
            doc += f"**{rid}** — The server SHALL expose `{r['method']} {r['path']}`{auth_note}.\n\n"

    if devices or mqtt.get("subscribe") or mqtt.get("publish"):
        doc += "### 4.3 IoT / MQTT Requirements\n\n"
        for t in mqtt.get("subscribe", []):
            rid = f"REQ-{feature_prefix}-{req_counter:03d}"
            req_counter += 1
            doc += f"**{rid}** — The server SHALL subscribe to MQTT topic `{t}`.\n\n"
        for t in mqtt.get("publish", []):
            rid = f"REQ-{feature_prefix}-{req_counter:03d}"
            req_counter += 1
            doc += f"**{rid}** — The server SHALL publish to MQTT topic `{t}`.\n\n"

    if screens:
        doc += "### 4.4 UI Requirements\n\n"
        for s in screens:
            rid = f"REQ-{feature_prefix}-{req_counter:03d}"
            req_counter += 1
            doc += f"**{rid}** — The client SHALL provide a `{s['name']}` screen"
            if s.get("state_fields"):
                doc += f" displaying: {', '.join(f'`{f}`' for f in s['state_fields'][:4])}"
            doc += ".\n\n"

    doc += "## 5. Non-Functional Requirements\n\n"
    doc += "| Requirement | Inherited From |\n|------------|---------------|\n"
    doc += "| Performance: UI updates ≤ 2s latency | REQ-S002 |\n"
    doc += "| Security: JWT auth for write ops | REQ-S004 |\n"
    doc += "| Reliability: No GlobalScope coroutines | REQ-A004 |\n"
    doc += "| Testability: ≥ 80% coverage on domain | REQ-Q001 |\n\n"

    doc += "## 6. Traceability\n\n"
    doc += f"| Requirement | SDD Ref | TST Ref |\n|------------|---------|--------|\n"
    doc += f"| (see §4 above) | SDD-{next_num:03d}_{slug}.md | VVR-{next_num:03d}_{slug}_results.md |\n\n"
    doc += f"*Full traceability: [TM-001](../TM/TM-001_traceability.md)*\n\n"
    doc += f"---\n*Document: {doc_id} | Standard: IEC 62304 §5.2*\n"

    write_doc(out_path, doc, dry_run)


# ─── FDA-9: SDD per Feature ───────────────────────────────────────────────────
def generate_sdd(dry_run: bool):
    """Generate docs/SDD/SDD-NNN_<feature>.md from all agent contexts."""
    wf   = read_ctx("00_workflow.json")
    arch = read_ctx("01_architect.json")
    sh   = read_ctx("02_shared.json")
    iot  = read_ctx("03_iot.json")
    kt   = read_ctx("04_ktor.json")
    cp   = read_ctx("05_compose.json")

    if not wf:
        print("  ⏭️  No workflow context — skipping SDD")
        return

    wf_data = wf.get("workflow", {})
    wf_name = wf_data.get("name", "unnamed")
    feature = wf_data.get("feature", "Unknown")
    ts      = now_str()

    sdd_dir  = DOCS_DIR / "SDD"
    existing = sorted(sdd_dir.glob("SDD-*.md")) if sdd_dir.exists() else []
    next_num = len(existing) + 1
    doc_id   = f"SDD-{next_num:03d}"
    slug     = re.sub(r"[^a-z0-9]+", "-", wf_name.lower()).strip("-")
    out_path = sdd_dir / f"{doc_id}_{slug}.md"

    doc  = f"# {doc_id}: Software Design — {feature}\n\n"
    doc += f"| Field | Value |\n|-------|-------|\n"
    doc += f"| **Document ID** | {doc_id} |\n"
    doc += f"| **Version** | 1.0.0 |\n"
    doc += f"| **Status** | DRAFT |\n"
    doc += f"| **Feature ID** | `{wf_name}` |\n"
    doc += f"| **Created** | {ts[:10]} |\n"
    doc += f"| **Parent SDD** | SDD-001 |\n"
    doc += f"| **Standard** | IEC 62304 §5.4 |\n\n---\n\n"

    # Shared / Domain
    models = sh.get("outputs", {}).get("domain_models", [])
    repos  = sh.get("outputs", {}).get("repositories", [])
    if models or repos:
        doc += "## 1. Shared Module Design\n\n"
        if models:
            doc += "### 1.1 Domain Models\n\n"
            for m in models:
                doc += f"**`{m['name']}`** — `{m.get('file','')}`\n\n"
                if m.get("fields"):
                    doc += "```kotlin\ndata class " + m['name'] + "(\n"
                    for f in m["fields"]:
                        doc += f"    val {f},\n"
                    doc += ")\n```\n\n"
        if repos:
            doc += "### 1.2 Repository Interfaces\n\n"
            doc += "| Interface | Fake Impl | File |\n|-----------|----------|------|\n"
            for r in repos:
                doc += f"| `{r.get('interface','')}` | `{r.get('fake_impl','')}` | `{r.get('file','')}` |\n"
            doc += "\n"
        # SOUP used
        soups = sh.get("_fda", {}).get("soups_used", [])
        if soups:
            doc += "### 1.3 SOUP Dependencies\n\n"
            for s in soups:
                doc += f"- {s}\n"
            doc += "\n"

    # IoT Design
    iot_out = iot.get("outputs", {})
    if iot_out:
        doc += "## 2. IoT / MQTT Design\n\n"
        devices = iot_out.get("devices", [])
        if devices:
            doc += "### 2.1 Devices\n\n"
            doc += "| ID Prefix | Type | Sensors | Actuators |\n|-----------|------|---------|-----------|\n"
            for d in devices:
                doc += f"| `{d.get('id_prefix','')}` | {d.get('type','')} | {', '.join(d.get('sensors',[]))} | {', '.join(d.get('actuators',[]))} |\n"
            doc += "\n"
        mqtt = iot_out.get("mqtt_topics", {})
        if mqtt:
            doc += "### 2.2 MQTT Topics\n\n"
            doc += "**Subscribe**: " + ", ".join(f"`{t}`" for t in mqtt.get("subscribe", [])) + "\n\n"
            doc += "**Publish**: " + ", ".join(f"`{t}`" for t in mqtt.get("publish", [])) + "\n\n"
        flow = iot_out.get("data_flow", "")
        if flow:
            doc += f"### 2.3 Data Flow\n\n`{flow}`\n\n"

    # Backend Design
    kt_out = kt.get("outputs", {})
    routes = kt_out.get("routes", [])
    ws     = kt_out.get("websocket_endpoints", [])
    if routes or ws:
        doc += "## 3. Backend Design (Ktor)\n\n"
        if routes:
            doc += "### 3.1 REST Routes\n\n"
            doc += "| Method | Path | Handler | Auth |\n|--------|------|---------|------|\n"
            for r in routes:
                h = r.get("handler","").split("/")[-1] if r.get("handler") else "-"
                doc += f"| `{r['method']}` | `{r['path']}` | `{h}` | {r.get('auth','none')} |\n"
            doc += "\n"
        if ws:
            doc += "### 3.2 WebSocket Endpoints\n\n"
            for w in ws:
                doc += f"- `{w}`\n"
            doc += "\n"
        db = kt_out.get("db_tables", [])
        if db:
            doc += "### 3.3 Database Tables\n\n"
            for t in db:
                doc += f"- `{t}`\n"
            doc += "\n"

    # Compose Design
    cp_out  = cp.get("outputs", {})
    screens = cp_out.get("screens", [])
    vms     = cp_out.get("viewmodels", [])
    if screens:
        doc += "## 4. UI Design (Compose)\n\n"
        doc += "### 4.1 Screens\n\n"
        for s in screens:
            doc += f"**`{s['name']}`** (Voyager Screen)\n\n"
            doc += f"- File: `{s.get('file','')}`\n"
            doc += f"- ViewModel: `{s.get('viewmodel','')}`\n"
            if s.get("state_fields"):
                doc += f"- State: {', '.join(f'`{f}`' for f in s['state_fields'])}\n"
            doc += "\n"
        nav = cp_out.get("navigation_added_to", "")
        if nav:
            doc += f"Navigation registered in: `{nav}`\n\n"

    doc += f"## 5. SOUP Components Used\n\n"
    all_soups = (
        arch.get("_fda", {}).get("soups_introduced", []) +
        [{"name": s} for s in sh.get("_fda", {}).get("soups_used", [])] +
        [{"name": s} for s in iot.get("_fda", {}).get("soups_used", [])] +
        [{"name": s} for s in kt.get("_fda", {}).get("soups_used", [])]
    )
    if all_soups:
        for s in all_soups:
            if isinstance(s, dict) and "soup_id" in s:
                doc += f"- `{s['soup_id']}` {s['name']} {s.get('version','')} — {s.get('purpose','')}\n"
            else:
                name = s.get("name","") if isinstance(s,dict) else str(s)
                doc += f"- {name}\n"
    else:
        doc += "_No new SOUP introduced. See SOUP-001 for base inventory._\n"
    doc += "\n"

    doc += f"---\n*Document: {doc_id} | Standard: IEC 62304 §5.4 | Feature: {wf_name}*\n"
    write_doc(out_path, doc, dry_run)


# ─── FDA-10: VVR ──────────────────────────────────────────────────────────────
def generate_vvr(dry_run: bool):
    """Generate docs/VVR/VVR-NNN_<feature>_results.md from QA context."""
    wf = read_ctx("00_workflow.json")
    qa = read_ctx("07_qa.json")
    sh = read_ctx("02_shared.json")
    kt = read_ctx("04_ktor.json")
    cp = read_ctx("05_compose.json")

    if not wf or not qa:
        print("  ⏭️  No QA context (07_qa.json) — skipping VVR")
        return

    wf_data = wf.get("workflow", {})
    wf_name = wf_data.get("name", "unnamed")
    feature = wf_data.get("feature", "Unknown")
    ts      = now_str()
    qa_out  = qa.get("outputs", {})
    qa_fda  = qa.get("_fda", {})

    vvr_dir  = DOCS_DIR / "VVR"
    existing = sorted(vvr_dir.glob("VVR-*.md")) if vvr_dir.exists() else []
    next_num = len(existing) + 1
    doc_id   = f"VVR-{next_num:03d}"
    slug     = re.sub(r"[^a-z0-9]+", "-", wf_name.lower()).strip("-")
    out_path = vvr_dir / f"{doc_id}_{slug}_results.md"

    all_pass   = qa_out.get("all_tests_pass", False)
    status_str = "✅ PASS" if all_pass else "❌ FAIL"
    run_cmd    = qa_out.get("run_command", "./gradlew allTests")

    doc  = f"# {doc_id}: V&V Results — {feature}\n\n"
    doc += f"| Field | Value |\n|-------|-------|\n"
    doc += f"| **Document ID** | {doc_id} |\n"
    doc += f"| **Version** | 1.0.0 |\n"
    doc += f"| **Status** | {'APPROVED' if all_pass else 'REJECTED'} |\n"
    doc += f"| **Feature ID** | `{wf_name}` |\n"
    doc += f"| **Executed** | {ts[:10]} |\n"
    doc += f"| **V&V Plan** | VVP-001 |\n"
    doc += f"| **Overall Result** | {status_str} |\n"
    doc += f"| **Standard** | IEC 62304 §5.7 |\n\n---\n\n"

    # Test execution summary
    doc += "## 1. Test Execution Summary\n\n"
    doc += f"```bash\n{run_cmd}\n```\n\n"
    doc += f"**Result: {status_str}**\n\n"

    # Coverage
    cov = qa_out.get("coverage", {})
    if cov:
        doc += "## 2. Coverage Report\n\n"
        doc += "| Layer | Coverage | Threshold | Status |\n|-------|----------|-----------|--------|\n"
        thresholds = {"shared_domain_pct": 80, "server_routes_pct": 70, "compose_viewmodel_pct": 80}
        for k, v in cov.items():
            threshold = thresholds.get(k, 70)
            label = k.replace("_pct","").replace("_"," ").title()
            status = "✅ PASS" if v >= threshold else "❌ FAIL"
            doc += f"| {label} | {v}% | {threshold}% | {status} |\n"
        doc += "\n"

    # Test cases from _fda block
    tests = qa_fda.get("tests", [])
    if tests:
        doc += "## 3. Test Case Results\n\n"
        doc += "| TST-ID | REQ-ID | Description | Result | Date | Notes |\n"
        doc += "|--------|--------|-------------|--------|------|-------|\n"
        for t in tests:
            doc += (f"| `{t.get('tst_id','—')}` | `{t.get('req_ref','—')}` "
                    f"| | {t.get('result','PENDING')} | {t.get('date','')[:10]} "
                    f"| {t.get('notes','')} |\n")
        doc += "\n"

    # Test files created
    test_files = qa_out.get("tests_created", [])
    if test_files:
        doc += "## 4. Test Files\n\n"
        for t in test_files:
            doc += f"- `{t.get('file','')}` — {t.get('type','')} ({t.get('count','?')} tests)\n"
        doc += "\n"

    # Risks verified
    risks_ver = qa_fda.get("risks_verified", [])
    if risks_ver:
        doc += "## 5. Risk Verification\n\n"
        for r in risks_ver:
            doc += f"- `{r}` — test evidence provided (see §3)\n"
        doc += "\n"

    # Conclusion
    doc += "## 6. Conclusion\n\n"
    if all_pass:
        doc += f"All verification activities for **{feature}** have been completed successfully. "
        doc += "The feature meets the requirements defined in the corresponding SRS addendum.\n\n"
        doc += "**Recommendation**: Approved for integration and release.\n\n"
    else:
        doc += f"⚠️ Verification for **{feature}** has FAILED. See failing tests above.\n\n"
        doc += "**Action required**: Fix failing tests before release. Create CM entry.\n\n"

    doc += f"---\n*Document: {doc_id} | Standard: IEC 62304 §5.7 | Feature: {wf_name}*\n"
    write_doc(out_path, doc, dry_run)


# ─── FDA-11: Risk Register Update ─────────────────────────────────────────────
def generate_risk_update(dry_run: bool):
    """Append new risk items to RM-001 from architect + security context."""
    arch = read_ctx("01_architect.json")
    sec  = read_ctx("08_security.json")
    wf   = read_ctx("00_workflow.json")

    new_risks = arch.get("_fda", {}).get("risks", [])
    if not new_risks:
        print("  ⏭️  No new risks in 01_architect._fda — skipping RM update")
        return

    wf_name = wf.get("workflow", {}).get("name", "unnamed")
    ts      = now_str()
    rm_path = DOCS_DIR / "RM" / "RM-001_risk-analysis.md"

    # Build new risk entries
    entries = ""
    for risk in new_risks:
        rid       = risk.get("risk_id", "RISK-NEW")
        hazard    = risk.get("hazard", "")
        severity  = risk.get("severity", "Medium")
        likelihood= risk.get("likelihood", "Possible")
        control   = risk.get("control", "")
        req_ref   = risk.get("req_ref", "")
        entries += f"\n### {rid} — (Feature: {wf_name})\n\n"
        entries += f"| Field | Value |\n|-------|-------|\n"
        entries += f"| **Risk ID** | {rid} |\n"
        entries += f"| **Hazard** | {hazard} |\n"
        entries += f"| **Severity** | {severity} |\n"
        entries += f"| **Likelihood** | {likelihood} |\n"
        entries += f"| **Control** | {control} |\n"
        entries += f"| **REQ Ref** | {req_ref} |\n"
        entries += f"| **Status** | Open |\n\n---\n"

    if dry_run:
        print(f"  [DRY RUN] docs/RM/RM-001_risk-analysis.md (append {len(new_risks)} risks)")
        return

    if rm_path.exists():
        content = rm_path.read_text(encoding="utf-8")
        # Append before the risk update log section
        insert_before = "## 5. Risk Update Log"
        if insert_before in content:
            content = content.replace(insert_before, entries + "\n" + insert_before)
        else:
            content += "\n" + entries

        # Update log
        log_line = f"| {ts[:10]} | New risks from `{wf_name}` | kmp-architect |\n"
        content += log_line if "| Date |" in content else ""
        rm_path.write_text(content, encoding="utf-8")
        print(f"  ✅ docs/RM/RM-001_risk-analysis.md (+{len(new_risks)} risks)")
    else:
        print(f"  ⚠️  RM-001 not found — run generate_risk_update after creating base docs")


# ─── FDA-12: Traceability Matrix Update ───────────────────────────────────────
def generate_tm_update(dry_run: bool):
    """Append new feature rows to TM-001 from all agent + _fda contexts."""
    wf   = read_ctx("00_workflow.json")
    arch = read_ctx("01_architect.json")
    sh   = read_ctx("02_shared.json")
    iot  = read_ctx("03_iot.json")
    kt   = read_ctx("04_ktor.json")
    cp   = read_ctx("05_compose.json")
    qa   = read_ctx("07_qa.json")

    if not wf:
        print("  ⏭️  No workflow — skipping TM update")
        return

    wf_name = wf.get("workflow", {}).get("name", "unnamed")
    ts      = now_str()
    tm_path = DOCS_DIR / "TM" / "TM-001_traceability.md"

    # Gather all implemented REQs from _fda blocks
    all_reqs: list[dict] = []
    for ctx, agent in [(arch,"kmp-architect"),(sh,"kmp-shared"),(iot,"kmp-iot"),(kt,"kmp-ktor"),(cp,"kmp-compose")]:
        for req in ctx.get("_fda", {}).get("requirements_implemented", []):
            all_reqs.append({"req_id": req, "agent": agent})

    qa_fda = qa.get("_fda", {})
    tests  = qa_fda.get("tests", [])
    test_map: dict = {t["req_ref"]: t["tst_id"] for t in tests if "req_ref" in t and "tst_id" in t}

    srs_num = len(sorted((DOCS_DIR / "SRS").glob("SRS-*.md"))) if (DOCS_DIR / "SRS").exists() else 2
    vvr_ref = f"VVR-{srs_num:03d}"

    slug = re.sub(r"[^a-z0-9]+", "-", wf_name.lower()).strip("-")

    new_rows = ""
    for r in all_reqs:
        req_id = r["req_id"]
        tst_id = test_map.get(req_id, "—")
        result = "PENDING"
        for t in tests:
            if t.get("req_ref") == req_id:
                result = t.get("result", "PENDING")
        new_rows += f"| `{req_id}` | | (feature: {wf_name}) | | `{tst_id}` | {result} | {vvr_ref} |\n"

    if not new_rows:
        print(f"  ⏭️  No _fda.requirements_implemented found — skipping TM update")
        return

    if dry_run:
        print(f"  [DRY RUN] docs/TM/TM-001_traceability.md (+{len(all_reqs)} rows for {wf_name})")
        return

    if tm_path.exists():
        content = tm_path.read_text(encoding="utf-8")
        # Find the feature addendum table and append
        marker = "| *(system base)* |"
        if marker in content:
            srs_tag = f"SRS-{srs_num:03d}"
            feature_row = f"| {wf_name} | {srs_tag} | SDD-{srs_num:03d} | {vvr_ref} | In Progress |\n"
            content = content.replace(marker, feature_row + marker)
        content += f"\n\n### {wf_name} — Added {ts[:10]}\n\n"
        content += "| REQ-ID | Description | SDD Ref | Implementation | TST-ID | Result | VVR Ref |\n"
        content += "|--------|-------------|---------|----------------|--------|--------|--------|\n"
        content += new_rows
        tm_path.write_text(content, encoding="utf-8")
        print(f"  ✅ docs/TM/TM-001_traceability.md (+{len(all_reqs)} rows)")
    else:
        print("  ⚠️  TM-001 not found — create base docs first")


# ─── FDA-13: SOUP Update ──────────────────────────────────────────────────────
def generate_soup_update(dry_run: bool):
    """Append new SOUP entries to SOUP-001 from architect + iot context _fda blocks."""
    arch = read_ctx("01_architect.json")
    iot  = read_ctx("03_iot.json")
    wf   = read_ctx("00_workflow.json")

    new_soups = arch.get("_fda", {}).get("soups_introduced", [])
    if not new_soups:
        print("  ⏭️  No new SOUP in 01_architect._fda.soups_introduced — skipping")
        return

    wf_name   = wf.get("workflow", {}).get("name", "unnamed")
    ts        = now_str()
    soup_path = DOCS_DIR / "SOUP" / "SOUP-001_ots-inventory.md"

    rows = ""
    for s in new_soups:
        soup_id = s.get("soup_id", "SOUP-NEW")
        name    = s.get("name", "")
        version = s.get("version", "?")
        purpose = s.get("purpose", "")
        risk    = s.get("risk_level", "Low")
        rows += f"| {soup_id} | {name} | {version} | Feature: {wf_name} | {purpose} | {risk} — Added by AI agent |\n"

    if dry_run:
        print(f"  [DRY RUN] docs/SOUP/SOUP-001_ots-inventory.md (+{len(new_soups)} entries)")
        return

    if soup_path.exists():
        content = soup_path.read_text(encoding="utf-8")
        # Append to update log and add note
        log_entry = f"| {ts[:10]} | Added {len(new_soups)} SOUP(s) from `{wf_name}` | kmp-architect |\n"
        if "## 10. Update Log" in content:
            content = content.replace(
                "| Date |",
                "| Date |",  # keep header
            )
            content += log_entry
        else:
            content += f"\n## New SOUP — {wf_name}\n\n"
            content += "| SOUP ID | Name | Version | Module | Purpose | Risk |\n"
            content += "|---------|------|---------|--------|---------|------|\n"
            content += rows

        soup_path.write_text(content, encoding="utf-8")
        print(f"  ✅ docs/SOUP/SOUP-001_ots-inventory.md (+{len(new_soups)} entries)")
    else:
        print("  ⚠️  SOUP-001 not found — create base docs first")


# ─── FDA-14: Change Management Entry ──────────────────────────────────────────
def generate_cm_entry(dry_run: bool):
    """Append a new CM entry to CM-001 from workflow + all agent contexts."""
    wf   = read_ctx("00_workflow.json")
    arch = read_ctx("01_architect.json")
    sh   = read_ctx("02_shared.json")
    kt   = read_ctx("04_ktor.json")
    qa   = read_ctx("07_qa.json")
    sec  = read_ctx("08_security.json")

    if not wf:
        print("  ⏭️  No workflow context — skipping CM entry")
        return

    wf_data  = wf.get("workflow", {})
    feature  = wf_data.get("feature", "Unknown")
    wf_name  = wf_data.get("name", "unnamed")
    ts       = now_str()
    cm_path  = DOCS_DIR / "CM" / "CM-001_change-log.md"

    # Determine next CM number
    cm_count = 1
    if cm_path.exists():
        content_check = cm_path.read_text(encoding="utf-8")
        cm_count = content_check.count("### CM-") + 1

    cm_id = f"CM-{cm_count:03d}"

    # Gather impacted requirements
    reqs_impacted: list[str] = []
    for ctx in [arch, sh, kt]:
        reqs_impacted += ctx.get("_fda", {}).get("requirements_implemented", [])
    reqs_str = ", ".join(f"`{r}`" for r in sorted(set(reqs_impacted))[:8]) or "—"

    # Gather impacted risks
    risks: list[str] = []
    for ctx in [arch]:
        risks += [r.get("risk_id","") for r in ctx.get("_fda", {}).get("risks", [])]
    sec_risks = [r.get("risk_id","") for r in sec.get("_fda", {}).get("risks_reviewed", [])]
    risks_str = ", ".join(f"`{r}`" for r in sorted(set(risks + sec_risks)) if r) or "—"

    # Determine type
    cm_type = "Feature"

    # Test result
    all_tests_pass = qa.get("outputs", {}).get("all_tests_pass", None)
    test_status = "✅ All tests pass" if all_tests_pass is True else ("❌ Tests failing" if all_tests_pass is False else "⏳ Not yet run")

    # Security critical issues
    crit = sec.get("outputs", {}).get("critical_issues", [])
    security_note = "✅ No critical issues" if not crit else f"⚠️ {len(crit)} critical issue(s): " + "; ".join(crit[:3])

    # Build what changed
    models  = sh.get("outputs", {}).get("domain_models", [])
    routes  = kt.get("outputs", {}).get("routes", [])
    screens = read_ctx("05_compose.json").get("outputs", {}).get("screens", [])

    entry  = f"\n### {cm_id}: [{ts[:10]}] {feature}\n\n"
    entry += f"| Field | Value |\n|-------|-------|\n"
    entry += f"| **Change ID** | {cm_id} |\n"
    entry += f"| **Date** | {ts[:10]} |\n"
    entry += f"| **Type** | {cm_type} |\n"
    entry += f"| **Feature ID** | `{wf_name}` |\n"
    entry += f"| **Author** | kmp-orchestrator |\n"
    entry += f"| **REQ Impacted** | {reqs_str} |\n"
    entry += f"| **RISK Impacted** | {risks_str} |\n"
    entry += f"| **SDD Ref** | SDD-{cm_count:03d}_{re.sub(r'[^a-z0-9]+-','-',wf_name.lower()).strip('-')}.md |\n"
    entry += f"| **VVR Ref** | VVR-{cm_count:03d}_{re.sub(r'[^a-z0-9]+-','-',wf_name.lower()).strip('-')}_results.md |\n\n"

    entry += "#### Description\n\n"
    entry += f"Implemented: **{feature}**.\n\n"

    if models:
        models_str = ', '.join(f'`{m["name"]}`' for m in models)
        entry += f"Domain models added: {models_str}.\n\n"
    if routes:
        routes_str = ', '.join(f'`{r["method"]} {r["path"]}`' for r in routes[:5])
        entry += f"API endpoints: {routes_str}.\n\n"
    if screens:
        screens_str = ', '.join(f'`{s["name"]}`' for s in screens)
        entry += f"UI screens: {screens_str}.\n\n"

    soup_count = len(arch.get('_fda', {}).get('soups_introduced', [])) or 'None'
    tests_mark = 'x' if all_tests_pass else ' '
    sec_mark   = 'x' if not crit else ' '

    entry += "#### Impact Assessment\n\n"
    entry += f"- **Tests**: {test_status}\n"
    entry += f"- **Security**: {security_note}\n"
    entry += f"- **SOUP changes**: {soup_count} new lib(s)\n\n"

    entry += "#### Approval Checklist\n\n"
    entry += "- [ ] Code review passed\n"
    entry += f"- [{tests_mark}] All tests pass (`./gradlew allTests`)\n"
    entry += "- [ ] Documentation updated and committed\n"
    entry += f"- [{sec_mark}] Security review passed\n\n"
    entry += "---\n"

    if dry_run:
        print(f"  [DRY RUN] docs/CM/CM-001_change-log.md (append {cm_id})")
        return

    if cm_path.exists():
        content = cm_path.read_text(encoding="utf-8")
        # Insert new entry after the header/format section, before first existing CM entry
        first_entry = "### CM-001:"
        if first_entry in content:
            content = content.replace(first_entry, entry + first_entry)
        else:
            content += entry
        cm_path.write_text(content, encoding="utf-8")
    else:
        header  = "# CM-001: Change Management Log\n\n"
        header += f"> **Updated**: {ts}\n\n---\n"
        cm_path.parent.mkdir(parents=True, exist_ok=True)
        cm_path.write_text(header + entry, encoding="utf-8")

    print(f"  ✅ docs/CM/CM-001_change-log.md ({cm_id} appended)")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="KMP Documentation Generator — standard + FDA mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
FDA flags (IEC 62304-inspired):
  --srs      SRS addendum per feature (docs/SRS/SRS-NNN_<name>.md)
  --sdd      SDD per feature          (docs/SDD/SDD-NNN_<name>.md)
  --vvr      V&V Results              (docs/VVR/VVR-NNN_<name>_results.md)
  --risk     Append to risk register  (docs/RM/RM-001_risk-analysis.md)
  --tm       Update traceability matrix (docs/TM/TM-001_traceability.md)
  --soup     Update SOUP inventory    (docs/SOUP/SOUP-001_ots-inventory.md)
  --cm       Append change entry      (docs/CM/CM-001_change-log.md)

Standard flags:
  --changelog  --feature  --architecture  --api  --adrs  --setup

Use --all (default) to run everything.
        """
    )
    # Standard flags
    parser.add_argument("--all",          action="store_true")
    parser.add_argument("--changelog",    action="store_true")
    parser.add_argument("--feature",      action="store_true")
    parser.add_argument("--architecture", action="store_true")
    parser.add_argument("--api",          action="store_true")
    parser.add_argument("--adrs",         action="store_true")
    parser.add_argument("--setup",        action="store_true")
    # FDA flags
    parser.add_argument("--srs",          action="store_true", help="SRS addendum")
    parser.add_argument("--sdd",          action="store_true", help="SDD per feature")
    parser.add_argument("--vvr",          action="store_true", help="V&V Results")
    parser.add_argument("--risk",         action="store_true", help="Append to RM risk register")
    parser.add_argument("--tm",           action="store_true", help="Update traceability matrix")
    parser.add_argument("--soup",         action="store_true", help="Update SOUP inventory")
    parser.add_argument("--cm",           action="store_true", help="Append CM change entry")
    parser.add_argument("--dry-run",      action="store_true")
    args = parser.parse_args()

    fda_flags    = [args.srs, args.sdd, args.vvr, args.risk, args.tm, args.soup, args.cm]
    std_flags    = [args.changelog, args.feature, args.architecture, args.api, args.adrs, args.setup]
    run_all      = args.all or not any(fda_flags + std_flags)

    print(f"\n📝 KMP Doc Generator (FDA mode) — {PROJECT_ROOT.name}")
    print(f"   Context : {CONTEXT_DIR}")
    print(f"   Output  : {DOCS_DIR}")
    print(f"   Standard: IEC 62304-inspired\n")

    # ── Standard docs ──
    if run_all or args.changelog:
        print("📋 Change Log (legacy CHANGELOG.md)")
        generate_changelog(args.dry_run)

    if run_all or args.feature:
        print("🚀 Feature doc")
        generate_feature_doc(args.dry_run)

    if run_all or args.architecture:
        print("🏛️  Architecture overview")
        generate_architecture_doc(args.dry_run)

    if run_all or args.api:
        print("📡 API reference")
        generate_api_reference(args.dry_run)

    if run_all or args.adrs:
        print("⚖️  ADR files")
        generate_adrs(args.dry_run)

    if run_all or args.setup:
        print("🛠️  Dev setup guide")
        generate_dev_setup(args.dry_run)

    # ── FDA docs ──
    if run_all or args.srs:
        print("📌 SRS — Requirements addendum")
        generate_srs(args.dry_run)

    if run_all or args.sdd:
        print("🏗️  SDD — Design description")
        generate_sdd(args.dry_run)

    if run_all or args.vvr:
        print("✅ VVR — V&V Results")
        generate_vvr(args.dry_run)

    if run_all or args.risk:
        print("⚠️  RM  — Risk register update")
        generate_risk_update(args.dry_run)

    if run_all or args.tm:
        print("🔗 TM  — Traceability matrix update")
        generate_tm_update(args.dry_run)

    if run_all or args.soup:
        print("📦 SOUP — OTS inventory update")
        generate_soup_update(args.dry_run)

    if run_all or args.cm:
        print("🔄 CM  — Change management entry")
        generate_cm_entry(args.dry_run)

    # Always update README index
    print("📁 Docs index (docs/README.md)")
    generate_docs_index(args.dry_run)

    print(f"\n{'─' * 55}")
    print("✅ Done. Next steps:")
    print("  1. Review generated files in docs/")
    print("  2. Fill TODO sections in SRS/SDD if needed")
    print("  3. git add docs/ && git commit -m 'docs: <feature>'")


if __name__ == "__main__":
    main()
