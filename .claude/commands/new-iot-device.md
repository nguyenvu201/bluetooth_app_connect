---
description: Integrate a new IoT device (ESP8266/ESP32/RS485 sensor) into the KMP IoT system
---

# New IoT Device Integration Workflow

Execute the complete IoT device integration workflow for ESP8266, ESP32, RS485 sensors, hoặc bất kỳ thiết bị MQTT-compatible nào.

## Workflow Steps

1. **IoT Design** (kmp-iot)
   - Xác định device type và communication protocol (MQTT/RS485/WebSocket)
   - Design MQTT topic convention cho device mới
   - Define sensor data schema (JSON payload format)
   - Design command/response protocol
   - Document firmware requirements cho ESP

2. **Shared Data Models** (kmp-shared)
   - Domain models cho device type mới
   - SensorPayload với validation rules
   - Repository interface cho device
   - Real-time Flow cho live data

3. **Ktor Backend** (kmp-ktor-backend)
   - MQTT subscription cho device topics
   - Message handler và validation
   - WebSocket bridge cho real-time updates
   - REST API endpoints (device management)
   - Database schema cho sensor readings

4. **Compose Dashboard** (kmp-compose)
   - Device card component
   - Real-time sensor dashboard screen
   - Device control panel (nếu có actuators)
   - Status indicator và alert UI

5. **Quality Assurance** (kmp-qa)
   - Unit tests với mock sensor data
   - MQTT message parsing tests
   - WebSocket integration tests
   - UI tests cho device dashboard

## Required Information

Cung cấp:
- Loại thiết bị: ESP8266 / ESP32 / RS485 sensor / Relay board / ...
- Communication protocol: MQTT / RS485 / WebSocket / HTTP
- Sensors/actuators: temperature, humidity, voltage, relay, PWM, ...
- Data update frequency: mỗi 5s / 30s / triggered by event
- Control commands cần thiết (nếu có)
- Unique device identifier scheme

## Device Integration Examples

### Temperature/Humidity ESP8266
```
MQTT Topics:
- Publish: devices/{id}/data    → { "temp": 28.5, "humidity": 65 }
- Subscribe: devices/{id}/command → { "type": "RESTART" }
```

### RS485 Energy Meter
```
MQTT Topics (qua ESP8266 bridge):
- Publish: devices/{id}/data    → { "voltage": 220, "current": 5.2, "power": 1144 }
- Subscribe: devices/{id}/command → { "type": "READ_RS485", "register": 0, "count": 10 }
```

### Relay Control Board
```
MQTT Topics:
- Publish: devices/{id}/status  → { "relays": [true, false, true, false] }
- Subscribe: devices/{id}/command → { "type": "TOGGLE_RELAY", "relay": 2, "state": true }
```

---

**Orchestrator**: Bắt đầu bằng cách invoke `kmp-iot` để design device integration, sau đó coordinate `kmp-shared` → `kmp-ktor-backend` → `kmp-compose` → `kmp-qa`.
