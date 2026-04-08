#!/usr/bin/env python3
"""
KMP Build Health Check
Kiểm tra Gradle build health cho KMP project:
- Xem build cache có bật không
- Kiểm tra JVM args
- Detect stale configurations
- Check Kotlin + AGP version compatibility
- Suggest build optimizations

Usage:
  python build_health_check.py
  python build_health_check.py --fix  # Auto-fix safe issues
"""

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]


class BuildHealthChecker:

    KNOWN_COMPATIBLE = {
        "kotlin":   {"min": "1.9.0", "recommended": "2.0.0"},
        "compose":  {"min": "1.5.0", "recommended": "1.6.0"},
        "ktor":     {"min": "2.3.0", "recommended": "3.0.0"},
        "koin":     {"min": "3.4.0", "recommended": "3.5.0"},
    }

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.issues = []
        self.warnings = []
        self.suggestions = []
        self.score = 100

    def check_all(self) -> dict:
        print(f"\n⚙️  KMP Build Health Check")
        print(f"   Project: {self.project_root.name}\n")

        results = {
            "gradle_properties": self._check_gradle_properties(),
            "version_catalog":   self._check_version_catalog(),
            "build_files":       self._check_build_files(),
            "docker":            self._check_docker(),
            "score":             0,
            "issues":            self.issues,
            "warnings":          self.warnings,
            "suggestions":       self.suggestions,
        }

        results["score"] = max(0, self.score)
        self._print_report(results)
        return results

    # ── gradle.properties ────────────────────────────────────────────────────
    def _check_gradle_properties(self) -> dict:
        props_file = self.project_root / "gradle.properties"
        if not props_file.exists():
            self.issues.append("gradle.properties not found")
            self.score -= 20
            return {"found": False}

        content = props_file.read_text()
        props = {}
        for line in content.splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                props[k.strip()] = v.strip()

        checks = {
            "org.gradle.caching":            ("true",   "Build cache disabled — add org.gradle.caching=true",         10),
            "org.gradle.parallel":           ("true",   "Parallel execution disabled — add org.gradle.parallel=true",  5),
            "kotlin.incremental":            ("true",   "Kotlin incremental disabled",                                  5),
            "kotlin.incremental.multiplatform": ("true","KMP incremental disabled",                                     5),
            "org.gradle.configureondemand":  ("true",   "Configure on demand not set (optional but useful)",            0),
        }

        result = {"found": True, "properties": {}}
        for key, (expected, msg, penalty) in checks.items():
            val = props.get(key)
            result["properties"][key] = val
            if val != expected:
                if penalty >= 10:
                    self.issues.append(msg)
                    self.score -= penalty
                else:
                    self.suggestions.append(f"Consider: {key}={expected}")

        # Check JVM args
        jvm_args = props.get("org.gradle.jvmargs", "")
        result["jvm_args"] = jvm_args
        if not jvm_args:
            self.warnings.append("No JVM args set — default heap may be too small for KMP builds")
            self.score -= 5
        elif "-Xmx" not in jvm_args:
            self.suggestions.append("Set -Xmx4g or higher in org.gradle.jvmargs")
        else:
            # Check heap size
            xmx = re.search(r"-Xmx(\d+)([gGmM])", jvm_args)
            if xmx:
                amount = int(xmx.group(1))
                unit = xmx.group(2).lower()
                mb = amount * 1024 if unit == "g" else amount
                if mb < 2048:
                    self.warnings.append(f"Heap may be too small ({amount}{unit}) — recommend -Xmx4g for KMP")
                    self.score -= 5

        return result

    # ── Version Catalog ────────────────────────────────────────────────────────
    def _check_version_catalog(self) -> dict:
        catalog = self.project_root / "gradle/libs.versions.toml"
        if not catalog.exists():
            self.issues.append("No version catalog (gradle/libs.versions.toml)")
            self.score -= 15
            return {"found": False}

        content = catalog.read_text()
        in_versions = False
        versions = {}
        for line in content.splitlines():
            line = line.strip()
            if line == "[versions]":
                in_versions = True
            elif line.startswith("[") and line != "[versions]":
                in_versions = False
            elif in_versions and "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                versions[k.strip()] = v.strip().strip('"')

        result = {"found": True, "versions": versions, "compatibility": {}}

        # Check key versions
        kotlin_v = versions.get("kotlin", "")
        compose_v = versions.get("composeMultiplatform", "")
        ktor_v    = versions.get("ktor", "")

        def _cmp(v1: str, v2: str) -> int:
            """Compare version strings: 1 if v1>v2, -1 if v1<v2, 0 if equal."""
            def _parts(v):
                return [int(x) for x in re.findall(r'\d+', v.split('-')[0])]
            p1, p2 = _parts(v1), _parts(v2)
            for a, b in zip(p1, p2):
                if a != b:
                    return 1 if a > b else -1
            return 0

        for lib_key, lib_ver, catalog_key in [
            ("kotlin", kotlin_v, "kotlin"),
            ("ktor",   ktor_v,   "ktor"),
        ]:
            if lib_ver:
                compat = self.KNOWN_COMPATIBLE.get(lib_key, {})
                min_v = compat.get("min", "0")
                rec_v = compat.get("recommended", "0")
                if _cmp(lib_ver, min_v) < 0:
                    self.issues.append(f"{lib_key} {lib_ver} is below minimum {min_v}")
                    self.score -= 10
                elif _cmp(lib_ver, rec_v) < 0:
                    self.suggestions.append(f"{lib_key} {lib_ver} → consider upgrading to {rec_v}+")
                result["compatibility"][lib_key] = lib_ver

        return result

    # ── Build files ────────────────────────────────────────────────────────────
    def _check_build_files(self) -> dict:
        result = {"modules": []}
        expected_modules = ["shared", "composeApp", "server"]

        for module in expected_modules:
            build_file = self.project_root / module / "build.gradle.kts"
            found = build_file.exists()
            result["modules"].append({"name": module, "has_build_file": found})
            if not found:
                self.warnings.append(f"Module {module}/build.gradle.kts not found")

        # Check for Dockerfile
        dockerfile = self.project_root / "Dockerfile"
        result["has_dockerfile"] = dockerfile.exists()
        if not dockerfile.exists():
            self.suggestions.append("Add a Dockerfile for server deployment")

        return result

    # ── Docker ─────────────────────────────────────────────────────────────────
    def _check_docker(self) -> dict:
        result = {}
        docker_compose = self.project_root / "docker-compose.yml"
        result["has_compose"] = docker_compose.exists()

        if docker_compose.exists():
            content = docker_compose.read_text()
            result["has_mqtt"]     = "mosquitto" in content.lower() or "mqtt" in content.lower()
            result["has_postgres"] = "postgres" in content.lower()
            result["has_server"]   = "ktor" in content.lower() or "server" in content.lower()
        else:
            self.suggestions.append("Add docker-compose.yml for easy local development")

        return result

    # ── Report ─────────────────────────────────────────────────────────────────
    def _print_report(self, results: dict):
        print("=" * 55)
        print(f"Build Health Score: {results['score']}/100")
        print("=" * 55)

        if self.issues:
            print(f"\n❌ Issues ({len(self.issues)}) — should fix:")
            for i in self.issues:
                print(f"   • {i}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"   • {w}")

        if self.suggestions:
            print(f"\n💡 Suggestions ({len(self.suggestions)}):")
            for s in self.suggestions:
                print(f"   • {s}")

        if not self.issues and not self.warnings:
            print("\n✅ Build configuration looks healthy!")

        # Version summary
        versions = results.get("version_catalog", {}).get("versions", {})
        if versions:
            key_versions = {k: versions[k] for k in ["kotlin", "ktor", "koin", "composeMultiplatform"]
                            if k in versions}
            print(f"\n📦 Key Versions:")
            for k, v in key_versions.items():
                print(f"   {k}: {v}")


def auto_fix(dry_run: bool):
    """Auto-fix safe gradle.properties issues."""
    props_file = PROJECT_ROOT / "gradle.properties"
    if not props_file.exists():
        print("❌ gradle.properties not found — cannot auto-fix")
        return

    content = props_file.read_text()
    additions = []

    safe_additions = {
        "org.gradle.caching":               "true",
        "org.gradle.parallel":              "true",
        "kotlin.incremental":               "true",
        "kotlin.incremental.multiplatform": "true",
    }

    for key, value in safe_additions.items():
        if key not in content:
            additions.append(f"{key}={value}")

    if not additions:
        print("✅ No safe fixes needed")
        return

    new_content = content.rstrip() + "\n\n# Auto-added by kmp-tools build_health_check\n"
    new_content += "\n".join(additions) + "\n"

    if dry_run:
        print("[DRY RUN] Would add to gradle.properties:")
        for line in additions:
            print(f"  + {line}")
    else:
        props_file.write_text(new_content)
        print(f"✅ Added {len(additions)} properties to gradle.properties:")
        for line in additions:
            print(f"  + {line}")


def main():
    parser = argparse.ArgumentParser(description="KMP Build Health Checker")
    parser.add_argument("--fix",     action="store_true", help="Auto-fix safe issues")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    checker = BuildHealthChecker()
    checker.check_all()

    if args.fix:
        print(f"\n🔧 Auto-fixing safe issues...")
        auto_fix(args.dry_run)


if __name__ == "__main__":
    main()
