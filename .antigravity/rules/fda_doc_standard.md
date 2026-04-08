---
role: FDA Documentation Standard
description: Quy chuẩn tài liệu FDA/IEC 62304 cho tất cả agents trong KMP IoT project.
applies_to: ["orchestrator", "kmp-architect", "kmp-shared", "kmp-iot", "kmp-ktor-backend", "kmp-compose", "kmp-qa", "kmp-security", "reviewer_logic"]
---

# FDA Documentation Standard — KMP IoT

## 1. Tại Sao FDA?

Dự án KMP IoT kiểm soát thiết bị vật lý qua MQTT và WebSocket. Một lỗi logic có thể gây ra **hành động sai trên phần cứng**. Vì vậy, codebase phải có traceability rõ ràng từ **user need → requirement → design → code → test**.

Standard áp dụng: **IEC 62304-inspired + FDA 21 CFR 820.30 spirit** (scale-down cho IoT, không phải medical device).

---

## 2. Document System

Toàn bộ tài liệu nằm trong `docs/`. Xem index tại `docs/README.md`.

| Loại | Thư mục | Ví dụ |
|------|---------|-------|
| Software Dev Plan | `docs/SDP/` | `SDP-001_software-dev-plan.md` |
| Requirements | `docs/SRS/` | `SRS-001_system-requirements.md` |
| Design | `docs/SDD/` | `SDD-001_architecture.md` |
| Test Plan | `docs/VVP/` | `VVP-001_test-plan.md` |
| Test Results | `docs/VVR/` | `VVR-NNN_<feature>_results.md` |
| Traceability | `docs/TM/` | `TM-001_traceability.md` (**LIVE**) |
| Risk Register | `docs/RM/` | `RM-001_risk-analysis.md` (**LIVE**) |
| SOUP / OTS | `docs/SOUP/` | `SOUP-001_ots-inventory.md` |
| Change Log | `docs/CM/` | `CM-001_change-log.md` (**LIVE**) |
| Release Notes | `docs/REL/` | `REL-NNN_v<x.y.z>.md` |
| Architecture ADR | `docs/ADR/` | `ADR-NNN_<title>.md` |

---

## 3. ID Conventions (PHẢI tuân theo)

```
Documents:  <TYPE>-<NNN>_<slug>.md       SRS-002_bluetooth-feature.md
Requirements: REQ-<layer><NNN>            REQ-B001 (Backend), REQ-N001 (Network)
Test Cases:   TST-<layer><NNN>            TST-B001, TST-SC001
Risk Items:   RISK-<NNN>                  RISK-004
SOUP/OTS:     SOUP-<prefix><NNN>          SOUP-I001 (IoT), SOUP-B001 (Backend)
Change Items: CM-<NNN>                    CM-002
```

**Requirement Layer Codes:**
```
S  = System     A  = Architecture    N  = Network/IoT
U  = UI/Compose B  = Backend/Ktor    Q  = Quality/Test   SC = Security
```

---

## 4. Agent `_fda` Block (MANDATORY)

Mỗi agent khi viết context JSON **PHẢI có `_fda` block**. Thiếu block này → orchestrator coi là thiếu compliance.

### Architect (`01_architect.json`):
```json
"_fda": {
  "doc_refs": ["SRS-001", "SDD-001"],
  "srs_addendum": "docs/SRS/SRS-NNN_<feature>.md",
  "sdd_created": "docs/SDD/SDD-NNN_<feature>.md",
  "soups_introduced": [
    { "soup_id": "SOUP-Xxx", "name": "LibName", "version": "x.y.z",
      "purpose": "why", "risk_level": "Low|Medium|High" }
  ],
  "risks": [
    { "risk_id": "RISK-NNN", "hazard": "description",
      "severity": "Low|Medium|High|Critical",
      "likelihood": "Rare|Unlikely|Possible|Likely|Almost Certain",
      "control": "mitigation measure", "req_ref": "REQ-Xxx" }
  ],
  "adrs_created": ["docs/ADR/ADR-NNN_<title>.md"]
}
```

### Implementation agents (`02_shared`, `03_iot`, `04_ktor`, `05_compose`):
```json
"_fda": {
  "requirements_implemented": ["REQ-A001", "REQ-B001"],
  "doc_ref": "SDD-NNN §<section>",
  "soups_used": ["SOUP-B001 (Ktor 3.3.3)", "SOUP-C004 (Koin 3.6.0)"]
}
```

### QA (`07_qa.json`):
```json
"_fda": {
  "vvr_ref": "docs/VVR/VVR-NNN_<feature>_results.md",
  "vvp_ref": "VVP-001",
  "tests": [
    { "tst_id": "TST-N001", "req_ref": "REQ-N001",
      "result": "PASS|FAIL|SKIP", "date": "2026-04-07", "notes": "" }
  ],
  "coverage_meets_threshold": true,
  "risks_verified": ["RISK-001", "RISK-002"]
}
```

### Security (`08_security.json`):
```json
"_fda": {
  "rm_ref": "RM-001",
  "risks_reviewed": [
    { "risk_id": "RISK-001", "status": "verified|open|accepted" }
  ],
  "requirements_verified": ["REQ-SC001", "REQ-SC002"],
  "soup_risk_assessed": ["SOUP-I001", "SOUP-I002"],
  "cm_entry_required": false
}
```

---

## 5. Documentation Generation (doc_generator.py)

Sau khi workflow hoàn thành, orchestrator PHẢI chạy:

```bash
# Full FDA documentation package
python .claude/skills/kmp-tools/scripts/doc_generator.py --all

# Hoặc từng loại
python .claude/skills/kmp-tools/scripts/doc_generator.py --srs   # SRS addendum
python .claude/skills/kmp-tools/scripts/doc_generator.py --sdd   # SDD per feature
python .claude/skills/kmp-tools/scripts/doc_generator.py --vvr   # V&V Results
python .claude/skills/kmp-tools/scripts/doc_generator.py --risk  # Risk register
python .claude/skills/kmp-tools/scripts/doc_generator.py --tm    # Traceability matrix
python .claude/skills/kmp-tools/scripts/doc_generator.py --soup  # SOUP inventory
python .claude/skills/kmp-tools/scripts/doc_generator.py --cm    # Change log entry

# Preview (không ghi file)
python .claude/skills/kmp-tools/scripts/doc_generator.py --dry-run
```

---

## 6. Risk Severity Scale

| Severity | Meaning | Examples |
|----------|---------|---------|
| **Critical** | System failure, hardware hazard | MQTT anonymous access → device hijack |
| **High** | Security breach, data loss | JWT secret hardcoded |
| **Medium** | Feature degraded, misleading data | Wrong sensor reading |
| **Low** | Minor UX, cosmetic | Layout issue on desktop |

**Likelihood**: `Rare / Unlikely / Possible / Likely / Almost Certain`

---

## 7. FDA Gates (KHÔNG được bỏ qua)

| Gate | Condition | Action nếu FAIL |
|------|-----------|----------------|
| V&V Gate | `07_qa.all_tests_pass == true` | STOP — fix tests |
| Security Gate | `08_security.critical_issues == []` | STOP — resolve critical issues |
| Risk Gate | Mọi Critical risk phải có control | WARN — document mitigation |
| Doc Gate | `_fda` block phải tồn tại trong mọi context JSON | WARN — incomplete traceability |

---

## 8. Reviewer FDA Checklist

Khi review code, **reviewer_logic PHẢI check thêm:**

- [ ] Không có `GlobalScope` trong production code → REQ-A004
- [ ] JWT secret load từ env var, không hardcode → REQ-SC002
- [ ] MQTT payload được validate trước khi lưu → REQ-N001
- [ ] Không expose DB port ra bên ngoài Docker network
- [ ] Mọi `@Throws` có exception được handled → avoid silent failure
- [ ] `_fda.requirements_implemented` khớp với code thực tế

---

## 9. SOUP Change Protocol

Khi thêm thư viện mới:
1. **Thêm vào `libs.versions.toml`**
2. **Điền vào `_fda.soups_introduced`** trong `01_architect.json`
3. **Chạy** `doc_generator.py --soup` để update `SOUP-001`
4. **Tạo CM entry**: `doc_generator.py --cm`

---
*Rule file: fda_doc_standard.md | Standard: IEC 62304 / FDA 21 CFR 820.30*
*Owned by: kmp-orchestrator | Updated: 2026-04-07*
