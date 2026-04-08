---
description: Security audit for the KMP IoT project covering backend auth, MQTT security, and IoT device security
---

# KMP Security Audit Workflow

Execute comprehensive security review cho KMP IoT project.

## Workflow Steps

1. **Ktor Backend Security Review** (kmp-security)
   - JWT configuration review (secret strength, expiry, claims)
   - Route authorization (đúng roles cho endpoint)
   - Input validation completeness
   - Rate limiting configuration
   - CORS configuration
   - Dependencies audit (CVE check)

2. **MQTT Security Review** (kmp-security)
   - Broker authentication (không allow anonymous)
   - ACL file review (principle of least privilege)
   - TLS configuration và certificate validity
   - Topic permission per device
   - Rate limit per MQTT client

3. **IoT Device Security** (kmp-iot + kmp-security)
   - Device identity và authentication scheme
   - OTA update security
   - Firmware credential storage
   - Physical security considerations
   - Network segmentation

4. **Coroutine & Thread Safety** (kmp-security)
   - StateFlow mutation patterns (atomic update)
   - SharedState giữa coroutines
   - Race condition analysis trong MQTT message handling
   - WebSocket session management

5. **Data Security** (kmp-security)
   - Sensitive data logging review
   - Android keystore usage
   - API response filtering (không expose internal data)
   - Database credential management

6. **Remediation Plan** (kmp-architect)
   - Prioritize vulnerabilities (Critical/High/Medium/Low)
   - Architecture changes nếu cần
   - Timeline estimate

## Security Checklist sẽ được Verify

### Critical (phải fix trước deploy)
- [ ] JWT_SECRET >= 32 chars, từ environment variable
- [ ] MQTT anonymous login disabled
- [ ] Không hardcode credentials trong source code
- [ ] Database password từ environment variable

### High
- [ ] MQTT TLS enabled trong production
- [ ] MQTT ACL per-device configured
- [ ] JWT expiry <= 1 hour
- [ ] Rate limiting trên auth endpoints
- [ ] Input validation trên tất cả API endpoints

### Medium
- [ ] Sensor data validation (range checks)
- [ ] CORS whitelist configured
- [ ] Log không chứa sensitive data
- [ ] Android EncryptedSharedPreferences cho tokens

### Low
- [ ] Security headers (HSTS, X-Frame-Options)
- [ ] API versioning
- [ ] Dependency updates

## Required Information

Cung cấp:
- Scope: full-audit / backend-only / mqtt-only / iot-only
- Compliance requirements: GDPR / internal-only / none
- Known concerns (nếu có)
- Environment: development / staging / production

---

**Orchestrator**: Bắt đầu bằng `kmp-security` cho comprehensive review, coord với `kmp-iot` cho device security, cuối cùng `kmp-architect` cho remediation plan.
