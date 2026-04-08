---
description: Generate or update project documentation from workflow context files
---

# Update Documentation

Tạo hoặc cập nhật toàn bộ tài liệu dự án từ context files sau khi hoàn thành feature/bugfix.

## Khi nào chạy

Chạy command này sau khi:
- ✅ Hoàn thành implement feature mới
- ✅ Fix bug có thay đổi business logic / API / domain model
- ✅ Thay đổi architecture (thêm module, đổi tech)
- ✅ Cập nhật API contracts

## Steps

1. **Verify workflow context đầy đủ**
   ```bash
   python .claude/skills/kmp-tools/scripts/context_manager.py status
   ```
   Đảm bảo ít nhất `00_workflow.json` tồn tại.

2. **Generate tất cả docs**
   ```bash
   python .claude/skills/kmp-tools/scripts/doc_generator.py
   ```

3. **Review output**
   Kiểm tra các file được tạo/cập nhật:
   - `docs/features/<name>.md` — Tech spec của feature
   - `CHANGELOG.md` — Entry mới được prepend
   - `docs/architecture/overview.md` — Cập nhật tech stack và principles
   - `docs/api/endpoints.md` — REST + WebSocket + MQTT reference
   - `docs/adrs/*.md` — Architecture decisions mới

4. **Edit thủ công nếu cần**
   Fill in các TODOs trong generated files:
   - Context / rationale của ADRs
   - Mô tả chi tiết hơn trong feature doc
   - Thêm diagrams nếu muốn

5. **Commit documentation**
   ```bash
   git add docs/ CHANGELOG.md
   git commit -m "docs: <feature-name>"
   ```

## Generate từng phần

```bash
# Chỉ CHANGELOG
python .claude/skills/kmp-tools/scripts/doc_generator.py --changelog

# Chỉ feature doc (sau khi agent workflow xong)
python .claude/skills/kmp-tools/scripts/doc_generator.py --feature

# Chỉ API reference (sau kmp-ktor-backend)
python .claude/skills/kmp-tools/scripts/doc_generator.py --api

# Chỉ architecture (sau kmp-architect)
python .claude/skills/kmp-tools/scripts/doc_generator.py --architecture

# Preview without writing
python .claude/skills/kmp-tools/scripts/doc_generator.py --dry-run
```

## Docs Structure

```
docs/
├── README.md              ← Index, auto-updated
├── CHANGELOG.md           ← Ở root project, auto-updated
├── features/
│   ├── bluetooth-p2p.md   ← Mỗi feature 1 file
│   └── sensor-dashboard.md
├── api/
│   └── endpoints.md       ← REST + WS + MQTT reference
├── architecture/
│   ├── overview.md        ← Auto-generated
│   └── kmp-dependency-analysis.md ← Auto-generated bởi module_analyzer
├── adrs/
│   └── adr_001_*.md       ← 1 file per ADR
└── guides/
    ├── dev-setup.md       ← Getting started
    └── deployment.md      ← Deploy guide (manual)
```

---

**Lưu ý**: Script đọc từ `.claude/context/NN_*.json`. Nếu workflow chưa chạy hoặc agents chưa ghi output, một số sections sẽ bị skip. Đây là behavior đúng — chỉ document những gì đã thực sự được implement.
