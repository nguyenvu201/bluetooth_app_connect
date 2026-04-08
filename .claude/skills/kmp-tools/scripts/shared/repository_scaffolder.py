#!/usr/bin/env python3
"""
KMP Repository Scaffolder
Scaffold Repository interface + implementation + Koin module + test
cho caonguyen.vu KMP project.
Usage: python repository_scaffolder.py DeviceName [--module shared|server]
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[5]
BASE_PACKAGE = "caonguyen.vu"

SHARED_COMMON_MAIN = PROJECT_ROOT / "shared/src/commonMain/kotlin/caonguyen/vu"
SHARED_COMMON_TEST = PROJECT_ROOT / "shared/src/commonTest/kotlin/caonguyen/vu"


def to_pascal(s: str) -> str:
    return ''.join(w.title() for w in s.replace('-', '_').split('_'))


def to_snake(s: str) -> str:
    import re
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
    return s.lower()


def scaffold_repository(name: str, dry_run: bool = False):
    pascal = to_pascal(name)
    snake = to_snake(pascal)
    feature = snake.replace('_', '')
    pkg_feature = f"{BASE_PACKAGE}.shared.{feature}"

    print(f"\n🔧 Scaffolding Repository: {pascal}Repository")
    print(f"   Package: {pkg_feature}")
    print(f"   Project root: {PROJECT_ROOT}\n")

    files = {}

    # ── 1. Domain Model ──────────────────────────────────────────────────────
    files[SHARED_COMMON_MAIN / f"shared/models/{pascal}.kt"] = f'''\
package {BASE_PACKAGE}.shared.models

import kotlinx.serialization.Serializable

@Serializable
data class {pascal}(
    val id: String,
    val name: String,
    // TODO: Add fields specific to {pascal}
)
'''

    # ── 2. Repository Interface ───────────────────────────────────────────────
    files[SHARED_COMMON_MAIN / f"shared/repository/{pascal}Repository.kt"] = f'''\
package {BASE_PACKAGE}.shared.repository

import {BASE_PACKAGE}.shared.models.{pascal}
import kotlinx.coroutines.flow.Flow

interface {pascal}Repository {{

    /** Observe all {pascal} items as a reactive stream. */
    fun observeAll(): Flow<List<{pascal}>>

    /** Get a single {pascal} by ID. */
    suspend fun getById(id: String): {pascal}?

    /** Add or update a {pascal}. */
    suspend fun save(item: {pascal}): Result<Unit>

    /** Remove a {pascal} by ID. */
    suspend fun delete(id: String): Result<Unit>
}}
'''

    # ── 3. Fake / In-Memory Implementation (for commonTest & desktop preview) ─
    files[SHARED_COMMON_MAIN / f"shared/repository/Fake{pascal}Repository.kt"] = f'''\
package {BASE_PACKAGE}.shared.repository

import {BASE_PACKAGE}.shared.models.{pascal}
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map

/**
 * In-memory fake implementation — use in tests and desktop previews.
 */
class Fake{pascal}Repository(
    initial: List<{pascal}> = emptyList()
) : {pascal}Repository {{

    private val _items = MutableStateFlow(initial)

    override fun observeAll(): Flow<List<{pascal}>> = _items.asStateFlow()

    override suspend fun getById(id: String): {pascal}? =
        _items.value.find {{ it.id == id }}

    override suspend fun save(item: {pascal}): Result<Unit> = runCatching {{
        _items.value = _items.value
            .filterNot {{ it.id == item.id }} + item
    }}

    override suspend fun delete(id: String): Result<Unit> = runCatching {{
        _items.value = _items.value.filterNot {{ it.id == id }}
    }}
}}
'''

    # ── 4. Koin DI Module entry (single file, appended manually) ─────────────
    koin_hint = f'''\
// ── Add to shared/src/commonMain/kotlin/{BASE_PACKAGE.replace(".", "/")}/shared/di/Koin.kt ──
// import {pkg_feature}.repository.{pascal}Repository
// import {pkg_feature}.repository.Fake{pascal}Repository
//
// single<{pascal}Repository> {{ Fake{pascal}Repository() }}
// (Replace Fake with real implementation when available)
'''
    files[SHARED_COMMON_MAIN / f"shared/repository/{pascal}Module_HINT.txt"] = koin_hint

    # ── 5. Unit Test ──────────────────────────────────────────────────────────
    files[SHARED_COMMON_TEST / f"shared/repository/Fake{pascal}RepositoryTest.kt"] = f'''\
package {BASE_PACKAGE}.shared.repository

import {BASE_PACKAGE}.shared.models.{pascal}
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class Fake{pascal}RepositoryTest {{

    private fun makeItem(id: String = "1") = {pascal}(id = id, name = "Test {pascal} $id")
    private fun repo(vararg items: {pascal}) = Fake{pascal}Repository(items.toList())

    @Test
    fun `observeAll emits initial items`() = runTest {{
        val item = makeItem()
        val r = repo(item)
        assertEquals(listOf(item), r.observeAll().first())
    }}

    @Test
    fun `getById returns item when present`() = runTest {{
        val item = makeItem("abc")
        val r = repo(item)
        assertEquals(item, r.getById("abc"))
    }}

    @Test
    fun `getById returns null when absent`() = runTest {{
        val r = repo()
        assertNull(r.getById("missing"))
    }}

    @Test
    fun `save adds new item`() = runTest {{
        val r = repo()
        val item = makeItem()
        r.save(item)
        assertEquals(listOf(item), r.observeAll().first())
    }}

    @Test
    fun `save updates existing item`() = runTest {{
        val r = repo(makeItem("1"))
        val updated = {pascal}(id = "1", name = "Updated")
        r.save(updated)
        assertEquals(updated, r.getById("1"))
    }}

    @Test
    fun `delete removes item`() = runTest {{
        val r = repo(makeItem("1"), makeItem("2"))
        r.delete("1")
        val items = r.observeAll().first()
        assertTrue(items.none {{ it.id == "1" }})
        assertEquals(1, items.size)
    }}
}}
'''

    _write_files(files, dry_run)
    _print_summary(pascal, files, dry_run)


def _write_files(files: dict, dry_run: bool):
    for path, content in files.items():
        if dry_run:
            print(f"  [DRY RUN] Would create: {path.relative_to(PROJECT_ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                print(f"  ⏭️  Skipping (exists): {path.relative_to(PROJECT_ROOT)}")
            else:
                path.write_text(content, encoding="utf-8")
                print(f"  ✅ Created: {path.relative_to(PROJECT_ROOT)}")


def _print_summary(pascal: str, files: dict, dry_run: bool):
    mode = "DRY RUN" if dry_run else "DONE"
    print(f"\n{'─' * 55}")
    print(f"[{mode}] {pascal}Repository scaffold — {len(files)} files")
    print(f"\nNext steps:")
    print(f"  1. Open shared/models/{pascal}.kt and add your fields")
    print(f"  2. Check _HINT.txt for Koin DI registration")
    print(f"  3. When ready → implement a real {pascal}Repository")
    print(f"     (e.g. Network + SQLDelight backed)")
    print(f"  4. Run: ./gradlew :shared:allTests")


def main():
    parser = argparse.ArgumentParser(description="Scaffold KMP Repository pattern")
    parser.add_argument("name", help="Entity name, e.g. 'Device' or 'SensorReading'")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating files")
    args = parser.parse_args()

    scaffold_repository(args.name, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
