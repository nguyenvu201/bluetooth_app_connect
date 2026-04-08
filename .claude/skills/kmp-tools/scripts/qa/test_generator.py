#!/usr/bin/env python3
"""
KMP Test Generator
Generate kotlin-test + coroutines-test specs for any existing Kotlin class.
Supports: Repository, ViewModel, UseCase, Service.

Usage:
  python test_generator.py shared/src/commonMain/kotlin/caonguyen/vu/shared/repository/DeviceRepository.kt
  python test_generator.py --class DeviceRepository --type repository
  python test_generator.py --class DashboardViewModel --type viewmodel
  python test_generator.py --class MqttGateway --type service --module server
"""

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]
BASE_PACKAGE = "caonguyen.vu"


def to_pascal(s: str) -> str:
    return ''.join(w.title() for w in re.split(r'[_\-]', s))


def infer_type(class_name: str) -> str:
    name = class_name.lower()
    if "repository" in name:   return "repository"
    if "viewmodel" in name:    return "viewmodel"
    if "usecase" in name:      return "usecase"
    if "service" in name:      return "service"
    if "gateway" in name:      return "service"
    return "generic"


def infer_module(class_name: str, file_path: str = "") -> str:
    if "server" in file_path.lower() or "Service" in class_name or "Gateway" in class_name:
        return "server"
    return "shared"


def resolve_test_path(class_name: str, module: str, sub_pkg: str) -> Path:
    if module == "server":
        return PROJECT_ROOT / f"server/src/test/kotlin/{BASE_PACKAGE.replace('.', '/')}/{class_name}Test.kt"
    else:
        return PROJECT_ROOT / f"shared/src/commonTest/kotlin/{BASE_PACKAGE.replace('.', '/')}/{sub_pkg}/{class_name}Test.kt"


def get_sub_pkg(class_type: str) -> str:
    mapping = {
        "repository": "shared/repository",
        "viewmodel":  "ui",
        "usecase":    "shared/usecase",
        "service":    "server/service",
        "generic":    "shared",
    }
    return mapping.get(class_type, "shared")


def generate_repository_test(pascal: str, pkg: str) -> str:
    fake_class = f"Fake{pascal.replace('Repository', '')}Repository" if "Repository" in pascal else f"Fake{pascal}"
    return f'''\
package {pkg}

import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Tests for {pascal}.
 * Uses in-memory fake — no Mocking framework needed.
 */
class {pascal}Test {{

    // Replace with actual type returned by your repository
    private data class TestEntity(val id: String, val name: String)

    private lateinit var repository: {pascal}

    @BeforeTest
    fun setUp() {{
        // TODO: Instantiate your repository or its fake
        // repository = Fake{pascal.replace("Repository", "")}Repository()
    }}

    @Test
    fun `observeAll emits empty list initially`() = runTest {{
        // TODO: Uncomment after setUp
        // val items = repository.observeAll().first()
        // assertTrue(items.isEmpty())
    }}

    @Test
    fun `getById returns null when item absent`() = runTest {{
        // TODO: Uncomment after setUp
        // assertNull(repository.getById("non-existent"))
    }}

    @Test
    fun `save then getById returns same item`() = runTest {{
        // TODO: Implement with your actual entity type
    }}

    @Test
    fun `delete removes item`() = runTest {{
        // TODO: Implement
    }}
}}
'''


def generate_viewmodel_test(pascal: str, pkg: str) -> str:
    return f'''\
package {pkg}

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.*
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertNull

/**
 * Tests for {pascal}.
 * Uses TestCoroutineScheduler for deterministic coroutine execution.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class {pascal}Test {{

    private val testDispatcher = StandardTestDispatcher()

    // TODO: Declare mock / fake dependencies here
    // private val fakeRepository = FakeXxxRepository()

    private lateinit var viewModel: {pascal}

    @BeforeTest
    fun setUp() {{
        Dispatchers.setMain(testDispatcher)
        // viewModel = {pascal}(fakeRepository, CoroutineScope(testDispatcher))
    }}

    @AfterTest
    fun tearDown() {{
        Dispatchers.resetMain()
    }}

    @Test
    fun `initial state has no error and not loading`() = runTest {{
        // viewModel = {pascal}(fakeRepository, this)
        // val state = viewModel.state.first()
        // assertNull(state.error)
        // assertFalse(state.isLoading)
    }}

    @Test
    fun `state updates after data loads`() = runTest {{
        // TODO: Implement with actual state fields
    }}

    @Test
    fun `onEvent Refresh triggers data reload`() = runTest {{
        // TODO: Implement
    }}
}}
'''


def generate_usecase_test(pascal: str, pkg: str) -> str:
    return f'''\
package {pkg}

import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.runTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * Tests for {pascal}.
 */
class {pascal}Test {{

    // TODO: Declare dependencies
    // private val fakeRepository = FakeXxxRepository()
    private lateinit var useCase: {pascal}

    @BeforeTest
    fun setUp() {{
        // useCase = {pascal}(fakeRepository)
    }}

    @Test
    fun `invoke emits data from repository`() = runTest {{
        // TODO: Implement
    }}

    @Test
    fun `invoke emits empty when repository is empty`() = runTest {{
        // TODO: Implement
    }}
}}
'''


def generate_service_test(pascal: str, pkg: str, is_ktor: bool) -> str:
    if is_ktor:
        return f'''\
package {pkg}

import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.server.testing.*
import caonguyen.vu.module
import kotlin.test.Test
import kotlin.test.assertEquals

/**
 * Integration tests for {pascal} via Ktor testApplication.
 */
class {pascal}Test {{

    @Test
    fun `health endpoint returns 200`() = testApplication {{
        application {{ module() }}
        val response = client.get("/health")
        assertEquals(HttpStatusCode.OK, response.status)
    }}

    @Test
    fun `TODO add {pascal}-specific route tests`() = testApplication {{
        application {{ module() }}
        // TODO: Test routes exposed by {pascal}
    }}
}}
'''
    else:
        return f'''\
package {pkg}

import kotlinx.coroutines.test.runTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertNotNull

class {pascal}Test {{

    private lateinit var service: {pascal}

    @BeforeTest
    fun setUp() {{
        // service = {pascal}(/* deps */)
    }}

    @Test
    fun `TODO add {pascal} service tests`() = runTest {{
        // Implement tests
    }}
}}
'''


def generate_generic_test(pascal: str, pkg: str) -> str:
    return f'''\
package {pkg}

import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertTrue

class {pascal}Test {{

    @Test
    fun `TODO add tests for {pascal}`() = runTest {{
        assertTrue(true, "Replace with real assertion")
    }}
}}
'''


def scaffold_test(class_name: str, class_type: str, module: str, dry_run: bool):
    pascal = to_pascal(class_name)
    sub_pkg = get_sub_pkg(class_type)
    test_path = resolve_test_path(pascal, module, sub_pkg)

    pkg_str = BASE_PACKAGE
    if module == "server":
        pkg_str = f"{BASE_PACKAGE}.server"
    else:
        pkg_str = f"{BASE_PACKAGE}.{sub_pkg.replace('/', '.')}"

    print(f"\n🧪 Generating test for: {pascal}")
    print(f"   Type   : {class_type}")
    print(f"   Module : {module}")
    print(f"   Output : {test_path.relative_to(PROJECT_ROOT)}\n")

    if class_type == "repository":
        content = generate_repository_test(pascal, pkg_str)
    elif class_type == "viewmodel":
        content = generate_viewmodel_test(pascal, pkg_str)
    elif class_type == "usecase":
        content = generate_usecase_test(pascal, pkg_str)
    elif class_type == "service":
        is_ktor = module == "server"
        content = generate_service_test(pascal, pkg_str, is_ktor)
    else:
        content = generate_generic_test(pascal, pkg_str)

    if dry_run:
        print(f"[DRY RUN] Would create: {test_path.relative_to(PROJECT_ROOT)}")
        print("\n--- Preview ---")
        print(content[:800] + "\n...")
    else:
        test_path.parent.mkdir(parents=True, exist_ok=True)
        if test_path.exists():
            print(f"⏭️  Test already exists: {test_path.relative_to(PROJECT_ROOT)}")
        else:
            test_path.write_text(content, encoding="utf-8")
            print(f"✅ Created: {test_path.relative_to(PROJECT_ROOT)}")

    print(f"\nRun tests with:")
    if module == "server":
        print(f"  ./gradlew :server:test")
    else:
        print(f"  ./gradlew :shared:jvmTest    # Fast JVM run")
        print(f"  ./gradlew :shared:allTests   # All platforms")


def main():
    parser = argparse.ArgumentParser(description="Generate kotlin-test spec for KMP class")
    parser.add_argument("--class",   dest="class_name", required=True,
                        help="Class name, e.g. DeviceRepository, DashboardViewModel")
    parser.add_argument("--type",    dest="class_type",
                        choices=["repository", "viewmodel", "usecase", "service", "generic"],
                        help="Class type (auto-detected if omitted)")
    parser.add_argument("--module",  choices=["shared", "server"], default=None,
                        help="Which module (auto-detected if omitted)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    class_type = args.class_type or infer_type(args.class_name)
    module = args.module or infer_module(args.class_name)

    scaffold_test(args.class_name, class_type, module, args.dry_run)


if __name__ == "__main__":
    main()
