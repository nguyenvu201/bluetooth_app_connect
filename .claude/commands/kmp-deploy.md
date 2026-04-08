---
description: Deploy the Ktor server and build Android/Desktop applications for the KMP IoT project
---

# KMP Deploy Workflow

Execute the deployment workflow cho KMP IoT project: Ktor server + Docker + Android APK.

## Workflow Steps

1. **Pre-deployment Validation** (kmp-qa)
   - Chạy tất cả unit tests (`./gradlew :shared:allTests :server:test`)
   - Verify Gradle build thành công tất cả modules
   - Kiểm tra test coverage đạt threshold
   - Verify không có failing Compose UI tests

2. **Security Validation** (kmp-security)
   - Kiểm tra environment variables đầy đủ (JWT_SECRET, DB_PASSWORD...)
   - MQTT ACL file up-to-date
   - Không có secrets hardcode trong code
   - Dependencies scan cho known vulnerabilities

3. **Server Deployment** (kmp-devops)
   - Build Ktor server distribution (`./gradlew :server:installDist`)
   - Build Docker image
   - Push to registry hoặc deploy trực tiếp
   - docker-compose up với health check
   - Verify `/health` endpoint

4. **Android Build** (kmp-devops)
   - Build debug APK (`./gradlew :composeApp:assembleDebug`)
   - Build release APK với signing (nếu production)
   - Upload artifact

5. **Post-deployment Check** (kmp-qa)
   - Smoke test API endpoints
   - Verify MQTT broker kết nối
   - Test WebSocket connection
   - Test Android app kết nối server

## Deployment Targets

### Development
```bash
./gradlew :server:run
# hoặc
docker-compose up
```

### Staging/Production
```bash
./gradlew :server:installDist
docker build -t iot-server:$(git rev-parse --short HEAD) .
docker-compose -f docker-compose.prod.yml up -d
```

### Android
```bash
./gradlew :composeApp:assembleDebug   # Debug
./gradlew :composeApp:assembleRelease # Release (cần signing config)
```

### Desktop
```bash
./gradlew :composeApp:run             # Run locally
./gradlew :composeApp:packageDistributionForCurrentOS  # Package
```

## Required Information

Cung cấp:
- Target environment: development / staging / production
- Deploy Ktor server: yes / no
- Build Android APK: yes / no
- Build Desktop app: yes / no
- Version tag (nếu có)

## Rollback

Nếu deployment fail:
1. `docker-compose down`
2. Restore previous image: `docker-compose -f docker-compose.prod.yml up -d --no-build`
3. Kiểm tra logs: `docker-compose logs ktor-server`

---

**Orchestrator**: Bắt đầu bằng invoke `kmp-qa` cho pre-deployment validation, sau đó `kmp-security` check, cuối cùng `kmp-devops` cho deployment execution.
