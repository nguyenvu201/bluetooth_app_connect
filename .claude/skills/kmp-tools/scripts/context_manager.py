#!/usr/bin/env python3
"""
KMP Context Manager — Workflow State & Agent Handover Utility
Manages .claude/context/ files for agent coordination.

Usage:
  python context_manager.py init <workflow_name>
  python context_manager.py read <agent_name>
  python context_manager.py status
  python context_manager.py validate <agent_output.json>
  python context_manager.py history
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def _find_project_root() -> Path:
    """Walk up from this script until we find the directory containing .claude/"""
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir() and (parent / ".claude" / "agents").is_dir():
            return parent
    # Fallback: 5 levels up
    return current.parents[5]

PROJECT_ROOT = _find_project_root()
CONTEXT_DIR  = PROJECT_ROOT / ".claude/context"


# ─── Agent Registry ──────────────────────────────────────────────────────────
AGENT_REGISTRY = {
    "kmp-orchestrator": {
        "output_file": "00_workflow.json",
        "reads":       [],
        "emoji":       "🎯",
    },
    "kmp-architect": {
        "output_file": "01_architect.json",
        "reads":       ["00_workflow.json"],
        "emoji":       "🏛",
    },
    "kmp-shared": {
        "output_file": "02_shared.json",
        "reads":       ["00_workflow.json", "01_architect.json"],
        "emoji":       "📦",
    },
    "kmp-iot": {
        "output_file": "03_iot.json",
        "reads":       ["00_workflow.json", "01_architect.json"],
        "emoji":       "🔌",
    },
    "kmp-ktor-backend": {
        "output_file": "04_ktor.json",
        "reads":       ["01_architect.json", "02_shared.json", "03_iot.json"],
        "emoji":       "🖥",
    },
    "kmp-compose": {
        "output_file": "05_compose.json",
        "reads":       ["01_architect.json", "02_shared.json"],
        "emoji":       "🎨",
    },
    "kmp-devops": {
        "output_file": "06_devops.json",
        "reads":       ["00_workflow.json", "04_ktor.json"],
        "emoji":       "🚀",
    },
    "kmp-qa": {
        "output_file": "07_qa.json",
        "reads":       ["02_shared.json", "04_ktor.json", "05_compose.json"],
        "emoji":       "🧪",
    },
    "kmp-security": {
        "output_file": "08_security.json",
        "reads":       ["04_ktor.json", "03_iot.json"],
        "emoji":       "🔒",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_context(file_name: str) -> dict | None:
    path = CONTEXT_DIR / file_name
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON error in {file_name}: {e}", file=sys.stderr)
    return None


def write_context(file_name: str, data: dict):
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    path = CONTEXT_DIR / file_name
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ─── Commands ─────────────────────────────────────────────────────────────────
def cmd_init(workflow_name: str, feature: str):
    """Initialize a new workflow session."""
    data = {
        "_schema":       "kmp-workflow/v2",
        "_file":         "00_workflow.json",
        "_written_by":   "kmp-orchestrator",
        "_timestamp":    now_iso(),
        "workflow": {
            "name":          workflow_name,
            "feature":       feature,
            "status":        "started",
            "started_at":    now_iso(),
            "completed_at":  None,
        },
        "tech_stack": {
            "package":       "caonguyen.vu",
            "navigation":    "Voyager",
            "mqtt_client":   "HiveMQ",
            "testing":       "kotlin-test + coroutines-test",
            "di":            "Koin",
            "orm":           "Exposed",
            "rs485":         "jSerialComm",
        },
        "decisions": [],
        "agent_status": {a: "pending" for a in AGENT_REGISTRY},
    }
    write_context("00_workflow.json", data)
    print(f"✅ Workflow initialized: {CONTEXT_DIR / '00_workflow.json'}")


def cmd_status():
    """Show current workflow status."""
    wf = read_context("00_workflow.json")
    if not wf:
        print("❌ No workflow started. Run: context_manager.py init <name> <feature>")
        return

    print(f"\n📋 Workflow: {wf['workflow']['name']} — {wf['workflow']['feature']}")
    print(f"   Status : {wf['workflow']['status']}")
    print(f"   Started: {wf['workflow'].get('started_at', '?')}\n")

    for agent, meta in AGENT_REGISTRY.items():
        out_file = meta["output_file"]
        ctx = read_context(out_file)
        emoji = meta["emoji"]
        if ctx:
            status = ctx.get("_status", "?")
            ts     = ctx.get("_timestamp", "?")[:19].replace("T", " ")
            icon   = "✅" if status == "success" else "⚠️" if status == "partial" else "❌"
            print(f"  {icon} {emoji} {agent:<25} {out_file}  ({ts})")
        else:
            print(f"  ⬜ {emoji} {agent:<25} {out_file}  (pending)")


def cmd_read(agent_name: str):
    """Print context that an agent should read before starting."""
    if agent_name not in AGENT_REGISTRY:
        print(f"❌ Unknown agent: {agent_name}")
        print(f"   Known: {', '.join(AGENT_REGISTRY)}")
        return

    reads = AGENT_REGISTRY[agent_name]["reads"]
    print(f"\n📖 Context for {agent_name}:")
    if not reads:
        print("  (No dependencies — this is the entry point)")
        return

    for fname in reads:
        ctx = read_context(fname)
        print(f"\n── {fname} ──")
        if ctx:
            print(json.dumps(ctx, indent=2, ensure_ascii=False)[:2000])
            if len(json.dumps(ctx)) > 2000:
                print("  ... (truncated)")
        else:
            print("  ⬜ Not yet written")


def cmd_validate(file_name: str):
    """Validate an agent output file against required schema fields."""
    ctx = read_context(file_name)
    if not ctx:
        print(f"❌ File not found or invalid JSON: {CONTEXT_DIR / file_name}")
        return

    required = ["_schema", "_file", "_written_by", "_timestamp", "_status"]
    errors = []
    for field in required:
        if field not in ctx:
            errors.append(f"Missing required field: {field}")

    if errors:
        print(f"❌ Validation failed for {file_name}:")
        for e in errors:
            print(f"   • {e}")
    else:
        print(f"✅ {file_name} — valid ({ctx.get('_status')})")


def cmd_history():
    """Show history of all written context files."""
    files = sorted(CONTEXT_DIR.glob("*.json"))
    print(f"\n📁 Context files in {CONTEXT_DIR}:\n")
    for f in files:
        try:
            ctx = json.loads(f.read_text())
            agent  = ctx.get("_written_by", "?")
            status = ctx.get("_status", "?")
            ts     = ctx.get("_timestamp", "?")[:19].replace("T", " ")
            print(f"  {f.name:<30} agent={agent:<25} status={status} at={ts}")
        except:
            print(f"  {f.name:<30} (unreadable)")


def main():
    parser = argparse.ArgumentParser(description="KMP Context Manager")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Initialize workflow")
    p_init.add_argument("name",    help="Workflow name e.g. 'bluetooth-feature'")
    p_init.add_argument("feature", nargs="?", default="", help="Feature description")

    p_read = sub.add_parser("read", help="Show context for an agent")
    p_read.add_argument("agent", help="Agent name e.g. kmp-shared")

    p_val = sub.add_parser("validate", help="Validate agent output file")
    p_val.add_argument("file", help="File name e.g. 02_shared.json")

    sub.add_parser("status",  help="Show current workflow status")
    sub.add_parser("history", help="List all context files")

    args = parser.parse_args()

    if args.cmd == "init":
        cmd_init(args.name, args.feature)
    elif args.cmd == "status":
        cmd_status()
    elif args.cmd == "read":
        cmd_read(args.agent)
    elif args.cmd == "validate":
        cmd_validate(args.file)
    elif args.cmd == "history":
        cmd_history()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
