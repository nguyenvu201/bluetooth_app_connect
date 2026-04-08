# Context Protocol v2 — KMP IoT Agent Workflow

Thư mục này chứa **state files** cho agent workflow coordination.

---

## Naming Convention

Mỗi file được đánh số theo thứ tự thực thi. Agent đọc file có số thấp hơn của mình.

| File | Written by | Step | Reads |
|------|-----------|------|-------|
| `00_workflow.json` | `kmp-orchestrator` | 0 — Entry | — |
| `01_architect.json` | `kmp-architect` | 1 | `00` |
| `02_shared.json` | `kmp-shared` | 2 | `00`, `01` |
| `03_iot.json` | `kmp-iot` | 3 | `00`, `01` |
| `04_ktor.json` | `kmp-ktor-backend` | 4 | `01`, `02`, `03` |
| `05_compose.json` | `kmp-compose` | 5 | `01`, `02` |
| `06_devops.json` | `kmp-devops` | 6 | `00`, `04` |
| `07_qa.json` | `kmp-qa` | 7 | `02`, `04`, `05` |
| `08_security.json` | `kmp-security` | 8 | `04`, `03` |

---

## Dependency Graph

```
00_workflow.json (kmp-orchestrator)
         │
         ▼
01_architect.json (kmp-architect)
         │
   ┌─────┴──────┐
   ▼             ▼
02_shared    03_iot
   │             │
   └──────┬──────┘
          ▼
     04_ktor  ←───── 02_shared
     05_compose ←─── 02_shared
          │
   ┌──────┴──────┐
   ▼             ▼
06_devops     07_qa
              07_qa ←── 05_compose
08_security ←── 04_ktor, 03_iot
```

---

## Mandatory Schema (tất cả files phải có)

```json
{
  "_schema":      "kmp-workflow/v2",
  "_file":        "NN_agentname.json",
  "_written_by":  "kmp-agent-name",
  "_timestamp":   "2026-04-07T12:00:00Z",
  "_status":      "success | partial | failed",
  "_reads":       ["NN_prev.json"],

  "summary": "Một dòng mô tả những gì đã làm",

  "outputs": {
    // Agent-specific payload — xem từng agent section bên dưới
  },

  "files_created":  ["relative/path/to/File.kt"],
  "files_modified": ["relative/path/to/Existing.kt"],
  "blockers":       [],
  "next_agents":    ["kmp-shared", "kmp-iot"]
}
```

> ⚠️ `_status: "failed"` hoặc `blockers` không rỗng → orchestrator **DỪNG** workflow và báo cáo user.

---

## Schema chi tiết từng Agent

### 00 — kmp-orchestrator (`00_workflow.json`)
```json
{
  "_schema": "kmp-workflow/v2",
  "_file": "00_workflow.json",
  "_written_by": "kmp-orchestrator",
  "_timestamp": "...",
  "_status": "success",
  "_reads": [],

  "summary": "New feature: bluetooth-p2p-monitoring",

  "outputs": {
    "workflow": {
      "name": "bluetooth-p2p-monitoring",
      "feature_description": "Add BLE P2P device monitoring to dashboard",
      "platforms": ["Android", "Desktop"],
      "requires_backend": true,
      "requires_iot": false,
      "priority": "high"
    },
    "tech_stack": {
      "package": "caonguyen.vu",
      "navigation": "Voyager",
      "mqtt_client": "HiveMQ",
      "testing": "kotlin-test + coroutines-test",
      "di": "Koin",
      "orm": "Exposed"
    },
    "agent_plan": [
      { "step": 1, "agent": "kmp-architect",     "parallel_with": [] },
      { "step": 2, "agent": "kmp-shared",         "parallel_with": [] },
      { "step": 3, "agent": "kmp-ktor-backend",   "parallel_with": ["kmp-compose"] },
      { "step": 3, "agent": "kmp-compose",         "parallel_with": ["kmp-ktor-backend"] },
      { "step": 4, "agent": "kmp-qa",             "parallel_with": [] },
      { "step": 5, "agent": "kmp-devops",         "parallel_with": ["kmp-security"] }
    ]
  },

  "files_created": [],
  "files_modified": [],
  "blockers": [],
  "next_agents": ["kmp-architect"]
}
```

### 01 — kmp-architect (`01_architect.json`)
```json
{
  "outputs": {
    "module_plan": {
      "shared_additions": [
        "shared/domain/model/BluetoothDevice.kt",
        "shared/domain/repository/BluetoothRepository.kt"
      ],
      "server_additions": [],
      "compose_additions": [
        "composeApp/ui/bluetooth/BluetoothScannerScreen.kt"
      ]
    },
    "api_contracts": [
      {
        "endpoint": "GET /api/bluetooth/devices",
        "response": { "devices": ["array of BluetoothDevice"] }
      }
    ],
    "adrs": [
      {
        "id": "ADR-001",
        "title": "Use Fake implementation for BLE in Desktop",
        "decision": "FakeBluetoothScanner for Desktop, real BLE for Android",
        "status": "accepted"
      }
    ],
    "koin_modules_needed": ["bluetoothModule"]
  }
}
```

### 02 — kmp-shared (`02_shared.json`)
```json
{
  "outputs": {
    "domain_models": [
      {
        "name": "BluetoothDevice",
        "file": "shared/src/commonMain/kotlin/caonguyen/vu/shared/models/BluetoothDevice.kt",
        "fields": ["id: String", "name: String", "rssi: Int", "status: DeviceStatus"]
      }
    ],
    "repositories": [
      {
        "interface": "BluetoothRepository",
        "fake_impl": "FakeBluetoothRepository",
        "file": "shared/src/commonMain/kotlin/caonguyen/vu/shared/repository/BluetoothRepository.kt"
      }
    ],
    "use_cases": [],
    "koin_module": {
      "name": "sharedModule",
      "file": "shared/src/commonMain/kotlin/caonguyen/vu/shared/di/Koin.kt",
      "bindings": ["BluetoothRepository → FakeBluetoothRepository"]
    },
    "expect_actual": []
  }
}
```

### 03 — kmp-iot (`03_iot.json`)
```json
{
  "outputs": {
    "devices": [
      {
        "id_prefix": "esp01",
        "type": "ESP8266",
        "sensors": ["temperature", "humidity"],
        "actuators": ["relay"]
      }
    ],
    "mqtt_topics": {
      "subscribe": ["devices/+/data", "devices/+/status", "devices/register"],
      "publish":   ["devices/+/command"]
    },
    "payload_schemas": {
      "data": { "timestamp": "Long", "temperature": "Double?", "humidity": "Double?" },
      "status": { "online": "Boolean", "rssi": "Int?", "firmware": "String?" }
    },
    "data_flow": "ESP8266 → MQTT(HiveMQ) → Ktor → WebSocket → Compose"
  }
}
```

### 04 — kmp-ktor-backend (`04_ktor.json`)
```json
{
  "outputs": {
    "routes": [
      {
        "method": "GET", "path": "/api/devices",
        "auth": "none", "handler": "server/.../routes/DeviceRoutes.kt"
      }
    ],
    "websocket_endpoints": ["/ws/devices/realtime"],
    "database_tables": ["DeviceTable", "SensorReadingTable"],
    "jwt_config": { "issuer": "iot-server", "expiry_hours": 1 },
    "mqtt_subscriptions": ["devices/+/data", "devices/+/status"],
    "health_endpoint": "/health"
  }
}
```

### 05 — kmp-compose (`05_compose.json`)
```json
{
  "outputs": {
    "screens": [
      {
        "name": "BluetoothScannerScreen",
        "file": "composeApp/src/commonMain/kotlin/caonguyen/vu/ui/bluetooth/BluetoothScannerScreen.kt",
        "viewmodel": "BluetoothViewModel",
        "navigator": "Voyager",
        "state_fields": ["devices: List<BluetoothDevice>", "isScanning: Boolean"]
      }
    ],
    "viewmodels": ["BluetoothViewModel"],
    "koin_registrations": ["factory { BluetoothViewModel(get()) }"],
    "navigation_added_to": "composeApp/src/commonMain/kotlin/caonguyen/vu/App.kt"
  }
}
```

### 06 — kmp-devops (`06_devops.json`)
```json
{
  "outputs": {
    "dockerfile": { "path": "Dockerfile", "status": "created|updated|exists" },
    "docker_compose": { "services": ["ktor-server", "postgres", "mosquitto"] },
    "github_actions": {
      "ci": ".github/workflows/ci.yml",
      "cd": ".github/workflows/cd.yml"
    },
    "gradle_properties_added": ["org.gradle.parallel=true"],
    "deployment_url": "http://localhost:8085"
  }
}
```

### 07 — kmp-qa (`07_qa.json`)
```json
{
  "outputs": {
    "tests_created": [
      {
        "file": "shared/src/commonTest/.../FakeBluetoothRepositoryTest.kt",
        "type": "repository",
        "count": 6
      }
    ],
    "coverage": {
      "shared_domain_pct": 85,
      "server_routes_pct": 70,
      "compose_viewmodel_pct": 80
    },
    "all_tests_pass": true,
    "run_command": "./gradlew allTests"
  }
}
```

### 08 — kmp-security (`08_security.json`)
```json
{
  "outputs": {
    "jwt_review": { "secret_from_env": true, "expiry_ok": true },
    "mqtt_review": {
      "anonymous_disabled": true,
      "acl_configured": false,
      "tls_enabled": false,
      "risk": "MEDIUM"
    },
    "critical_issues": [],
    "high_issues": ["MQTT TLS not enabled in production"],
    "checklist_passed_pct": 75
  }
}
```

---

## Cách Agent đọc context

Mỗi agent phải làm ngay khi bắt đầu:

```
1. Đọc 00_workflow.json → lấy feature description, platforms, tech stack
2. Đọc các file phụ thuộc (xem bảng trên)
3. Extract thông tin cần thiết từ "outputs" của file trước
4. Thực hiện task của mình
5. Ghi file output với đúng naming convention
```

## Cách ghi Context

Khi agent xong, phải ghi output file với format đầy đủ:

```
File: .claude/context/NN_agentname.json (NN = số thứ tự)
```

---

## Tool hỗ trợ

```bash
# Khởi tạo workflow mới
python .claude/skills/kmp-tools/scripts/context_manager.py init bluetooth-feature "BLE P2P monitoring"

# Xem trạng thái workflow hiện tại
python .claude/skills/kmp-tools/scripts/context_manager.py status

# Xem context mà một agent cần đọc
python .claude/skills/kmp-tools/scripts/context_manager.py read kmp-shared

# Validate output file của một agent
python .claude/skills/kmp-tools/scripts/context_manager.py validate 02_shared.json

# Xem lịch sử tất cả context files
python .claude/skills/kmp-tools/scripts/context_manager.py history
```
