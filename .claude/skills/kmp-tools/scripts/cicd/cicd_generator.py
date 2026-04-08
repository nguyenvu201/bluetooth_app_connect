#!/usr/bin/env python3
"""
KMP GitHub Actions CI/CD Generator
Generate GitHub Actions workflows tailored to caonguyen.vu KMP project:
- CI: test shared + server on every PR
- CD: build Android APK + deploy Ktor Docker on push to main

Usage:
  python cicd_generator.py --all
  python cicd_generator.py --ci-only
  python cicd_generator.py --cd-only
  python cicd_generator.py --dry-run
"""

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]
WORKFLOWS_DIR = PROJECT_ROOT / ".github/workflows"


# ─────────────────────────────────────────────────────────────────────────────
# CI Workflow — runs on every PR and push to main/develop
# ─────────────────────────────────────────────────────────────────────────────
CI_WORKFLOW = """\
name: KMP CI — Test & Build

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # ── Shared Module Tests ────────────────────────────────────────────────────
  test-shared:
    name: 🧪 Shared Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - name: Cache Gradle
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
            ~/.konan
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle.kts', '**/libs.versions.toml') }}
          restore-keys: gradle-${{ runner.os }}-

      - name: Make gradlew executable
        run: chmod +x gradlew

      - name: Run shared tests (JVM)
        run: ./gradlew :shared:jvmTest --no-daemon --stacktrace

      - name: Run shared tests (commonTest)
        run: ./gradlew :shared:allTests --no-daemon

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: shared-test-results
          path: shared/build/reports/tests/

  # ── Server Tests ───────────────────────────────────────────────────────────
  test-server:
    name: 🖥️ Ktor Server Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: iotdb_test
          POSTGRES_USER: iot
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - name: Cache Gradle
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle.kts', '**/libs.versions.toml') }}
          restore-keys: gradle-${{ runner.os }}-

      - name: Make gradlew executable
        run: chmod +x gradlew

      - name: Run server tests
        env:
          DATABASE_URL: jdbc:postgresql://localhost:5432/iotdb_test
          DB_USER: iot
          DB_PASSWORD: test_password
          JWT_SECRET: test-jwt-secret-minimum-32-characters-long
          MQTT_BROKER_URL: tcp://localhost:1883
        run: ./gradlew :server:test --no-daemon --stacktrace

      - name: Upload server test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: server-test-results
          path: server/build/reports/tests/

  # ── Android Build ──────────────────────────────────────────────────────────
  build-android:
    name: 📱 Android Debug Build
    needs: [test-shared]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - name: Cache Gradle
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
            ~/.konan
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle.kts', '**/libs.versions.toml') }}
          restore-keys: gradle-${{ runner.os }}-

      - name: Make gradlew executable
        run: chmod +x gradlew

      - name: Build Android Debug APK
        run: ./gradlew :composeApp:assembleDebug --no-daemon

      - name: Upload Debug APK
        uses: actions/upload-artifact@v4
        with:
          name: debug-apk-${{ github.sha }}
          path: composeApp/build/outputs/apk/debug/*.apk
          retention-days: 14

  # ── Desktop Build ──────────────────────────────────────────────────────────
  build-desktop:
    name: 🖥️ Desktop Build
    needs: [test-shared]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - name: Cache Gradle
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle.kts', '**/libs.versions.toml') }}
          restore-keys: gradle-${{ runner.os }}-

      - name: Make gradlew executable
        run: chmod +x gradlew

      - name: Build Desktop JAR
        run: ./gradlew :composeApp:packageDistributionForCurrentOS --no-daemon

      - name: Upload Desktop package
        uses: actions/upload-artifact@v4
        with:
          name: desktop-package-${{ github.sha }}
          path: composeApp/build/compose/binaries/main/
          retention-days: 7
"""

# ─────────────────────────────────────────────────────────────────────────────
# CD Workflow — runs only on push/merge to main
# ─────────────────────────────────────────────────────────────────────────────
CD_WORKFLOW = """\
name: KMP CD — Deploy Server

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        default: "staging"
        type: choice
        options: [staging, production]

jobs:
  # ── Build & Push Docker Image ──────────────────────────────────────────────
  build-server-image:
    name: 🐳 Build Ktor Docker Image
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - name: Cache Gradle
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle.kts', '**/libs.versions.toml') }}

      - name: Make gradlew executable
        run: chmod +x gradlew

      - name: Build server distribution
        run: ./gradlew :server:installDist --no-daemon --stacktrace

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository_owner }}/kmp-iot-server
          tags: |
            type=sha,prefix=sha-
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ── Deploy to Staging ──────────────────────────────────────────────────────
  deploy-staging:
    name: 🚀 Deploy to Staging
    needs: build-server-image
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.your-iot-server.com
    if: github.ref == 'refs/heads/main' || github.event.inputs.environment == 'staging'
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/kmp-iot
            echo "Pulling image: ${{ needs.build-server-image.outputs.image_tag }}"
            docker-compose pull ktor-server
            docker-compose up -d ktor-server
            
            echo "Waiting for health check..."
            sleep 15
            curl -f http://localhost:8085/health || (echo "Health check failed!" && exit 1)
            echo "Deployment successful ✅"

  # ── Deploy to Production (manual approval required) ───────────────────────
  deploy-production:
    name: 🏭 Deploy to Production
    needs: [build-server-image, deploy-staging]
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://your-iot-server.com
    if: github.event.inputs.environment == 'production'
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/kmp-iot
            docker-compose pull ktor-server
            docker-compose up -d ktor-server
            sleep 20
            curl -f http://localhost:8085/health || (echo "Production health check failed!" && exit 1)
            echo "Production deployment successful ✅"
"""

# ─────────────────────────────────────────────────────────────────────────────
# Pre-commit check script (runs locally via git hook)
# ─────────────────────────────────────────────────────────────────────────────
PRE_COMMIT_SCRIPT = """\
#!/bin/bash
# KMP Pre-commit hook
# Install: cp .claude/skills/kmp-tools/scripts/cicd/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

set -e

echo "🔍 Running KMP pre-commit checks..."

# 1. Shared module tests
echo "  Running shared tests..."
./gradlew :shared:jvmTest --quiet --no-daemon
echo "  ✅ Shared tests passed"

# 2. Server tests  
echo "  Running server tests..."
./gradlew :server:test --quiet --no-daemon
echo "  ✅ Server tests passed"

# 3. Quality analysis
echo "  Running quality check..."
python .claude/skills/kmp-tools/scripts/qa/quality_analyzer.py . --json > /tmp/kmp_quality.json 2>/dev/null
SCORE=$(python -c "import json; d=json.load(open('/tmp/kmp_quality.json')); print(d['quality_score'])" 2>/dev/null || echo "0")
echo "  Quality Score: $SCORE/100"
if [ "$SCORE" -lt "50" ]; then
    echo "  ⚠️  Quality score below 50 — consider adding more tests"
fi

echo ""
echo "✅ All pre-commit checks passed!"
"""


def generate_ci(dry_run: bool):
    _write_file(WORKFLOWS_DIR / "ci.yml", CI_WORKFLOW, dry_run)


def generate_cd(dry_run: bool):
    _write_file(WORKFLOWS_DIR / "cd.yml", CD_WORKFLOW, dry_run)


def generate_pre_commit(dry_run: bool):
    script_dir = PROJECT_ROOT / ".claude/skills/kmp-tools/scripts/cicd"
    _write_file(script_dir / "pre-commit", PRE_COMMIT_SCRIPT, dry_run)
    if not dry_run:
        hook_path = PROJECT_ROOT / ".git/hooks/pre-commit"
        if not hook_path.exists():
            hook_path.write_text(PRE_COMMIT_SCRIPT)
            hook_path.chmod(0o755)
            print(f"  ✅ Installed git hook: .git/hooks/pre-commit")
        else:
            print(f"  ⏭️  Git hook already exists: .git/hooks/pre-commit")


def generate_secrets_checklist(dry_run: bool):
    content = """\
# GitHub Actions — Required Secrets

Go to: GitHub repo → Settings → Secrets and variables → Actions

## CI Secrets (needed for server tests)
# These are set automatically by GitHub Actions, no action needed:
# GITHUB_TOKEN — auto-provided

## CD Secrets (needed for deployment)

### Staging
STAGING_HOST=        # IP or hostname of staging server
STAGING_USER=        # SSH username (e.g. ubuntu, deploy)
STAGING_SSH_KEY=     # Private SSH key (entire contents of id_rsa)

### Production
PROD_HOST=           # IP or hostname of production server
PROD_USER=           # SSH username
PROD_SSH_KEY=        # Private SSH key

## Server Environment Variables (set in docker-compose on the server)
# These should be in /opt/kmp-iot/.env on the server:
JWT_SECRET=          # Min 32 chars, random string
DB_PASSWORD=         # PostgreSQL password
MQTT_USERNAME=       # Mosquitto username
MQTT_PASSWORD=       # Mosquitto password

## How to generate JWT secret
# python -c "import secrets; print(secrets.token_hex(32))"
"""
    docs_dir = PROJECT_ROOT / "docs/cicd"
    _write_file(docs_dir / "secrets-checklist.md", content, dry_run)


def _write_file(path: Path, content: str, dry_run: bool):
    if dry_run:
        print(f"  [DRY RUN] Would create: {path.relative_to(PROJECT_ROOT)}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            print(f"  ⏭️  Exists: {path.relative_to(PROJECT_ROOT)}")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"  ✅ Created: {path.relative_to(PROJECT_ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="Generate GitHub Actions workflows for KMP IoT project")
    parser.add_argument("--all",          action="store_true", help="Generate all workflows")
    parser.add_argument("--ci-only",      action="store_true", help="CI workflow only")
    parser.add_argument("--cd-only",      action="store_true", help="CD workflow only")
    parser.add_argument("--pre-commit",   action="store_true", help="Install git pre-commit hook")
    parser.add_argument("--dry-run",      action="store_true")
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    print(f"\n🚀 KMP CI/CD Generator")
    print(f"   Project: {PROJECT_ROOT.name}\n")

    if args.all or args.ci_only:
        print("Generating CI workflow...")
        generate_ci(args.dry_run)

    if args.all or args.cd_only:
        print("Generating CD workflow...")
        generate_cd(args.dry_run)

    if args.all or args.pre_commit:
        print("Setting up pre-commit hook...")
        generate_pre_commit(args.dry_run)

    if args.all:
        print("Generating secrets checklist...")
        generate_secrets_checklist(args.dry_run)

    print(f"\n{'─' * 55}")
    print("Next steps:")
    print("  1. Review .github/workflows/ci.yml and cd.yml")
    print("  2. Set GitHub Secrets (see docs/cicd/secrets-checklist.md)")
    print("  3. Push to GitHub — CI will trigger automatically")
    print("  4. For CD: Configure server SSH access")


if __name__ == "__main__":
    main()
