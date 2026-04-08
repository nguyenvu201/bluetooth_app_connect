#!/usr/bin/env python3
"""
KMP Quality Analyzer
Phân tích code quality cho Kotlin Multiplatform project:
- Gradle build health
- Kotlin file stats
- Test coverage reports (Kover/Jacoco)
- Detekt/ktlint violations
- Dead code detection
"""

import argparse
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class KMPQualityAnalyzer:
    """Analyze code quality for Kotlin Multiplatform project."""

    # KMP-specific quality thresholds
    COVERAGE_TARGETS = {
        "shared_domain": 85,
        "shared_data": 75,
        "server": 70,
        "compose_viewmodel": 80,
    }

    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path).resolve()
        self.verbose = verbose
        self.gradle = self.project_path / "gradlew"

    def analyze_all(self) -> Dict[str, Any]:
        """Run comprehensive KMP quality analysis."""
        print(f"🔍 Analyzing KMP quality: {self.project_path}")

        results = {
            "timestamp": datetime.now().isoformat(),
            "project": str(self.project_path),
            "kotlin_stats": self._analyze_kotlin_files(),
            "gradle_health": self._check_gradle_health(),
            "test_summary": self._analyze_test_files(),
            "coverage": self._read_coverage_report(),
            "quality_score": 0,
            "recommendations": [],
        }

        results["quality_score"] = self._calculate_score(results)
        results["recommendations"] = self._generate_recommendations(results)

        self._print_summary(results)
        return results

    def _analyze_kotlin_files(self) -> Dict[str, Any]:
        """Count Kotlin files per module and source set."""
        stats = {}
        skip = {"build", ".gradle", ".kotlin", ".idea", "generated"}

        modules = ["shared", "composeApp", "server", "iosApp"]
        for module in modules:
            module_path = self.project_path / module
            if not module_path.exists():
                continue

            kt_files = [
                f for f in module_path.rglob("*.kt")
                if not any(s in f.parts for s in skip)
            ]

            # Classify by source set
            common = [f for f in kt_files if "commonMain" in str(f)]
            android = [f for f in kt_files if "androidMain" in str(f)]
            ios = [f for f in kt_files if "iosMain" in str(f)]
            jvm = [f for f in kt_files if "jvmMain" in str(f)]
            desktop = [f for f in kt_files if "desktopMain" in str(f)]
            test_files = [f for f in kt_files if "Test" in str(f) or "test" in str(f).lower()]
            main_files = [f for f in kt_files if f not in test_files]

            # Calculate test ratio
            test_ratio = (
                round(len(test_files) / len(kt_files) * 100, 1) if kt_files else 0
            )

            stats[module] = {
                "total_files": len(kt_files),
                "main_files": len(main_files),
                "test_files": len(test_files),
                "test_ratio_pct": test_ratio,
                "source_sets": {
                    "commonMain": len(common),
                    "androidMain": len(android),
                    "iosMain": len(ios),
                    "jvmMain": len(jvm),
                    "desktopMain": len(desktop),
                },
            }

        # Count total lines
        total_lines = 0
        all_kt = [f for f in self.project_path.rglob("*.kt")
                  if not any(s in f.parts for s in skip)]
        for f in all_kt:
            try:
                total_lines += len(f.read_text(errors="ignore").splitlines())
            except:
                pass

        return {
            "modules": stats,
            "total_kt_files": len(all_kt),
            "total_lines": total_lines,
        }

    def _check_gradle_health(self) -> Dict[str, Any]:
        """Check Gradle build health."""
        health = {
            "has_version_catalog": False,
            "has_build_cache": False,
            "has_parallel_builds": False,
            "lib_versions": {},
            "modules_found": [],
        }

        # Check version catalog
        catalog = self.project_path / "gradle" / "libs.versions.toml"
        if catalog.exists():
            health["has_version_catalog"] = True
            health["lib_versions"] = self._parse_version_catalog(catalog)

        # Check gradle.properties for optimizations
        props_file = self.project_path / "gradle.properties"
        if props_file.exists():
            props = props_file.read_text()
            health["has_build_cache"] = "org.gradle.caching=true" in props
            health["has_parallel_builds"] = "org.gradle.parallel=true" in props

        # Find submodules
        for build_file in self.project_path.glob("*/build.gradle.kts"):
            health["modules_found"].append(build_file.parent.name)

        return health

    def _parse_version_catalog(self, catalog_path: Path) -> Dict[str, str]:
        """Parse versions from libs.versions.toml."""
        versions = {}
        try:
            content = catalog_path.read_text()
            in_versions = False
            for line in content.splitlines():
                line = line.strip()
                if line == "[versions]":
                    in_versions = True
                elif line.startswith("[") and line != "[versions]":
                    in_versions = False
                elif in_versions and "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    versions[key.strip()] = val.strip().strip('"')
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not parse version catalog: {e}")
        return versions

    def _analyze_test_files(self) -> Dict[str, Any]:
        """Analyze test file structure and patterns."""
        skip = {"build", ".gradle", ".kotlin"}
        test_summary = {
            "kotest_specs": [],
            "kotlin_test": [],
            "compose_ui_tests": [],
            "ktor_tests": [],
            "total_test_files": 0,
        }

        all_test_files = [
            f for f in self.project_path.rglob("*Test*.kt")
            if not any(s in f.parts for s in skip)
        ] + [
            f for f in self.project_path.rglob("*Spec*.kt")
            if not any(s in f.parts for s in skip)
        ]

        test_summary["total_test_files"] = len(all_test_files)

        for f in all_test_files:
            try:
                content = f.read_text(errors="ignore")
                name = f.name

                if "FunSpec" in content or "BehaviorSpec" in content or "DescribeSpec" in content:
                    test_summary["kotest_specs"].append(name)
                elif "@Test" in content or "kotlin.test" in content:
                    test_summary["kotlin_test"].append(name)

                if "composeTestRule" in content or "createComposeRule" in content:
                    test_summary["compose_ui_tests"].append(name)

                if "testApplication" in content or "ktor-test" in content:
                    test_summary["ktor_tests"].append(name)
            except:
                pass

        return test_summary

    def _read_coverage_report(self) -> Optional[Dict[str, Any]]:
        """Read Kover or Jacoco coverage report if available."""
        # Kover XML report
        kover_reports = list(self.project_path.rglob("koverReport*.xml")) + \
                        list(self.project_path.rglob("report.xml"))

        for report in kover_reports:
            if "kover" in str(report).lower() or "build/reports" in str(report):
                try:
                    content = report.read_text()
                    # Extract line coverage from Kover XML
                    match = re.search(r'<counter type="LINE"[^/]* missed="(\d+)" covered="(\d+)"', content)
                    if match:
                        missed = int(match.group(1))
                        covered = int(match.group(2))
                        total = missed + covered
                        pct = round(covered / total * 100, 1) if total > 0 else 0
                        return {
                            "source": "kover",
                            "line_coverage_pct": pct,
                            "lines_covered": covered,
                            "lines_missed": missed,
                            "report_path": str(report),
                        }
                except:
                    pass

        # Jacoco
        jacoco_reports = list(self.project_path.rglob("jacocoTestReport.xml"))
        if jacoco_reports:
            return {"source": "jacoco", "report_found": True, "path": str(jacoco_reports[0])}

        return {"source": None, "note": "No coverage report found. Run ./gradlew koverMergedReport"}

    def _calculate_score(self, results: Dict[str, Any]) -> int:
        """Calculate overall quality score 0-100."""
        score = 100
        stats = results.get("kotlin_stats", {})
        health = results.get("gradle_health", {})
        tests = results.get("test_summary", {})

        # Penalize for low test ratio
        for module, data in stats.get("modules", {}).items():
            ratio = data.get("test_ratio_pct", 0)
            if ratio < 10:
                score -= 15
            elif ratio < 20:
                score -= 5

        # Reward for good Gradle setup
        if health.get("has_version_catalog"):
            pass  # Good
        else:
            score -= 10

        if health.get("has_build_cache"):
            pass
        else:
            score -= 5

        # Reward for having tests
        if tests.get("kotest_specs"):
            pass
        elif tests.get("kotlin_test"):
            pass
        else:
            score -= 20

        return max(0, min(100, score))

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        stats = results.get("kotlin_stats", {})
        health = results.get("gradle_health", {})
        tests = results.get("test_summary", {})
        coverage = results.get("coverage", {})

        # Test coverage
        for module, data in stats.get("modules", {}).items():
            ratio = data.get("test_ratio_pct", 0)
            if ratio < 15 and data.get("main_files", 0) > 5:
                recs.append(f"[{module}] Test file ratio is {ratio}% — add more unit tests (Kotest + MockK)")

        # Gradle
        if not health.get("has_version_catalog"):
            recs.append("Add gradle/libs.versions.toml for centralized dependency management")
        if not health.get("has_build_cache"):
            recs.append("Add org.gradle.caching=true to gradle.properties to speed up builds")

        # Tests
        if not tests.get("kotest_specs") and not tests.get("kotlin_test"):
            recs.append("No test files detected — create Kotest specs in shared/src/commonTest/")
        if not tests.get("compose_ui_tests"):
            recs.append("No Compose UI tests found — add composeTestRule tests for critical screens")
        if not tests.get("ktor_tests"):
            recs.append("No Ktor API tests found — add testApplication tests for REST routes")

        # Coverage
        if coverage and coverage.get("source") is None:
            recs.append("Configure Kover plugin for test coverage: apply plugin 'kotlinx-kover'")

        return recs

    def _print_summary(self, results: Dict[str, Any]):
        print("\n" + "=" * 55)
        print(f"KMP Quality Score: {results['quality_score']}/100")
        print("=" * 55)

        # Kotlin stats
        stats = results["kotlin_stats"]
        print(f"\n📊 Kotlin Files: {stats['total_kt_files']} files / {stats['total_lines']:,} lines")
        for module, data in stats.get("modules", {}).items():
            print(
                f"   📦 {module}: {data['main_files']} src + {data['test_files']} tests "
                f"({data['test_ratio_pct']}% test ratio)"
            )

        # Gradle health
        health = results["gradle_health"]
        print(f"\n⚙️  Gradle Health:")
        print(f"   Version Catalog: {'✅' if health.get('has_version_catalog') else '❌'}")
        print(f"   Build Cache: {'✅' if health.get('has_build_cache') else '❌'}")
        print(f"   Parallel Builds: {'✅' if health.get('has_parallel_builds') else '❌'}")

        # Tests
        tests = results["test_summary"]
        print(f"\n🧪 Tests Found: {tests['total_test_files']} test files")
        if tests["kotest_specs"]:
            print(f"   Kotest Specs: {len(tests['kotest_specs'])}")
        if tests["compose_ui_tests"]:
            print(f"   Compose UI: {len(tests['compose_ui_tests'])}")
        if tests["ktor_tests"]:
            print(f"   Ktor Tests: {len(tests['ktor_tests'])}")

        # Coverage
        coverage = results.get("coverage", {})
        if coverage and coverage.get("line_coverage_pct") is not None:
            pct = coverage["line_coverage_pct"]
            icon = "✅" if pct >= 70 else "⚠️"
            print(f"\n📈 Coverage ({coverage['source']}): {icon} {pct}%")

        # Recommendations
        recs = results.get("recommendations", [])
        if recs:
            print(f"\n💡 Recommendations ({len(recs)}):")
            for rec in recs:
                print(f"   → {rec}")
        else:
            print("\n✅ No major recommendations")


def main():
    parser = argparse.ArgumentParser(description="KMP Quality Analyzer")
    parser.add_argument("project_path", nargs="?", default=".", help="KMP project root")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    analyzer = KMPQualityAnalyzer(args.project_path, args.verbose)
    results = analyzer.analyze_all()

    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
