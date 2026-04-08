#!/usr/bin/env python3
"""
KMP Module Dependency Analyzer
Phân tích dependencies giữa các Kotlin modules trong KMP project.
Detect circular dependencies và coupling metrics.
"""

import argparse
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set, Any


class KMPDependencyAnalyzer:
    """Analyze Kotlin module dependencies in KMP project."""

    def __init__(self, project_path: str, output_dir: str = "./docs/architecture"):
        self.project_path = Path(project_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # KMP module → set of imported packages
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        # module → files
        self.module_files: Dict[str, List[Path]] = defaultdict(list)

    def analyze(self) -> Dict[str, Any]:
        """Full dependency analysis."""
        print(f"🔍 Analyzing KMP project: {self.project_path}")
        self._scan_kotlin_files()

        results = {
            "timestamp": datetime.now().isoformat(),
            "project": str(self.project_path),
            "modules": list(self.module_files.keys()),
            "module_file_counts": {m: len(files) for m, files in self.module_files.items()},
            "circular_dependencies": self._detect_circular_deps(),
            "module_coupling": self._calculate_coupling(),
            "mermaid_diagram": self._generate_mermaid(),
        }

        self._save_results(results)
        self._print_summary(results)
        return results

    def _scan_kotlin_files(self):
        """Scan all .kt files and map to modules."""
        kt_files = list(self.project_path.rglob("*.kt"))
        skip_dirs = {"build", ".gradle", ".kotlin", ".idea", "generated"}

        for kt_file in kt_files:
            # Skip build directories
            if any(skip in kt_file.parts for skip in skip_dirs):
                continue

            module = self._resolve_module(kt_file)
            if module:
                self.module_files[module].append(kt_file)
                self._extract_imports(kt_file, module)

    def _resolve_module(self, file_path: Path) -> str | None:
        """Resolve which KMP module a file belongs to."""
        rel = file_path.relative_to(self.project_path)
        parts = rel.parts

        # Known top-level modules
        known_modules = {"shared", "composeApp", "server", "iosApp"}
        if parts[0] in known_modules:
            return parts[0]

        # Detect by build.gradle.kts presence
        for i in range(len(parts) - 1, 0, -1):
            check_path = self.project_path / Path(*parts[:i])
            if (check_path / "build.gradle.kts").exists():
                return parts[i - 1] if i > 0 else parts[0]

        return parts[0] if parts else None

    def _extract_imports(self, file_path: Path, module: str):
        """Extract Kotlin import statements."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            import_pattern = re.compile(r"^import\s+([\w.]+)", re.MULTILINE)
            for match in import_pattern.finditer(content):
                pkg = match.group(1)
                # Only track internal project packages
                if any(
                    pkg.startswith(prefix)
                    for prefix in ["com.project", "com.nguyenvu", "vu.nguyen", "kmp"]
                ):
                    self.imports[module].add(pkg)
        except Exception as e:
            pass

    def _detect_circular_deps(self) -> List[List[str]]:
        """Detect circular module dependencies (simplified)."""
        # Build inter-module dependency graph
        module_deps: Dict[str, Set[str]] = defaultdict(set)
        modules = set(self.module_files.keys())

        for module, pkgs in self.imports.items():
            for pkg in pkgs:
                for other_module in modules:
                    if other_module != module and other_module.lower() in pkg.lower():
                        module_deps[module].add(other_module)

        # DFS cycle detection
        cycles = []
        visited = set()
        path = []

        def dfs(node: str):
            if node in path:
                idx = path.index(node)
                cycles.append(path[idx:] + [node])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for dep in module_deps.get(node, []):
                dfs(dep)
            path.pop()

        for m in modules:
            dfs(m)

        return cycles

    def _calculate_coupling(self) -> Dict[str, Any]:
        """Calculate per-module import counts."""
        return {
            module: {
                "file_count": len(files),
                "import_count": len(self.imports.get(module, set())),
            }
            for module, files in self.module_files.items()
        }

    def _generate_mermaid(self) -> str:
        """Generate Mermaid diagram of KMP module structure."""
        diagram = ["```mermaid", "graph TD"]

        modules = list(self.module_files.keys())

        # Standard KMP dependency arrows
        dep_map = {
            "composeApp": ["shared"],
            "server": ["shared"],
            "iosApp": ["shared"],
        }

        for module in modules:
            label = module
            if module == "shared":
                diagram.append(f'    {module}["🔷 {label}<br/>KMP Shared Logic"]')
            elif module == "composeApp":
                diagram.append(f'    {module}["📱 {label}<br/>Compose Multiplatform UI"]')
            elif module == "server":
                diagram.append(f'    {module}["🖥️ {label}<br/>Ktor Backend"]')
            elif module == "iosApp":
                diagram.append(f'    {module}["🍎 {label}<br/>iOS SwiftUI"]')
            else:
                diagram.append(f'    {module}["{label}"]')

        for src, dsts in dep_map.items():
            if src in modules:
                for dst in dsts:
                    if dst in modules:
                        diagram.append(f"    {src} --> {dst}")

        diagram.append("```")
        return "\n".join(diagram)

    def _save_results(self, results: Dict[str, Any]):
        """Save analysis results."""
        # JSON
        json_file = self.output_dir / "kmp-dependency-analysis.json"
        json_file.write_text(json.dumps(results, indent=2))

        # Markdown report
        md = self._build_markdown(results)
        md_file = self.output_dir / "kmp-dependency-analysis.md"
        md_file.write_text(md)

        print(f"\n📁 Results saved to: {self.output_dir}/")

    def _build_markdown(self, results: Dict[str, Any]) -> str:
        modules = results["modules"]
        coupling = results["module_coupling"]
        circular = results["circular_dependencies"]

        lines = [
            "# KMP Module Dependency Analysis",
            f"\n**Generated**: {results['timestamp']}",
            f"\n## Modules Found ({len(modules)})\n",
        ]

        for m in modules:
            c = coupling.get(m, {})
            lines.append(
                f"- **{m}**: {c.get('file_count', 0)} Kotlin files, "
                f"{c.get('import_count', 0)} cross-module imports"
            )

        lines.append("\n## Module Dependency Diagram\n")
        lines.append(results["mermaid_diagram"])

        lines.append("\n## Circular Dependencies\n")
        if circular:
            for cycle in circular:
                lines.append(f"⚠️ `{' → '.join(cycle)}`")
        else:
            lines.append("✅ No circular dependencies detected")

        return "\n".join(lines)

    def _print_summary(self, results: Dict[str, Any]):
        print("\n" + "=" * 50)
        print("KMP Dependency Analysis Summary")
        print("=" * 50)
        for m, c in results["module_coupling"].items():
            print(f"  📦 {m}: {c['file_count']} files")

        circular = results["circular_dependencies"]
        if circular:
            print(f"\n⚠️  {len(circular)} circular dependency cycle(s) found!")
        else:
            print("\n✅ No circular dependencies")


def main():
    parser = argparse.ArgumentParser(description="KMP Module Dependency Analyzer")
    parser.add_argument("project_path", nargs="?", default=".", help="KMP project root")
    parser.add_argument("--output", default="./docs/architecture", help="Output directory")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    args = parser.parse_args()

    analyzer = KMPDependencyAnalyzer(args.project_path, args.output)
    results = analyzer.analyze()

    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
