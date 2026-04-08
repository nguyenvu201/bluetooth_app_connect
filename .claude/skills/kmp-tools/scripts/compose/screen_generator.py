#!/usr/bin/env python3
"""
KMP Compose Screen Generator
Generate Compose screen + ViewModel + State cho caonguyen.vu project.
Follows Voyager navigator pattern used in the project.

Usage:
  python screen_generator.py Dashboard
  python screen_generator.py BluetoothDevice --with-list
  python screen_generator.py SensorDetail --dry-run
"""

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]
BASE_PACKAGE = "caonguyen.vu"
COMPOSE_COMMON_MAIN = PROJECT_ROOT / "composeApp/src/commonMain/kotlin/caonguyen/vu"
COMPOSE_COMMON_TEST = PROJECT_ROOT / "composeApp/src/commonTest/kotlin/caonguyen/vu"


def to_pascal(s: str) -> str:
    return ''.join(w.title() for w in re.split(r'[_\-]', s))


def to_camel(s: str) -> str:
    p = to_pascal(s)
    return p[0].lower() + p[1:]


def scaffold_screen(name: str, with_list: bool = False, dry_run: bool = False):
    pascal = to_pascal(name)
    camel = to_camel(name)
    pkg_ui = f"{BASE_PACKAGE}.ui.{camel.lower()}"

    print(f"\n🎨 Generating Compose Screen: {pascal}Screen")
    print(f"   Package : {pkg_ui}")
    print(f"   Navigator: Voyager\n")

    files = {}
    ui_dir = COMPOSE_COMMON_MAIN / f"ui/{camel.lower()}"
    test_dir = COMPOSE_COMMON_TEST / f"ui/{camel.lower()}"

    # ── 1. State ──────────────────────────────────────────────────────────────
    files[ui_dir / f"{pascal}State.kt"] = _state_template(pascal, pkg_ui, with_list)

    # ── 2. ViewModel ─────────────────────────────────────────────────────────
    files[ui_dir / f"{pascal}ViewModel.kt"] = _viewmodel_template(pascal, pkg_ui, camel)

    # ── 3. Screen (Voyager) ───────────────────────────────────────────────────
    files[ui_dir / f"{pascal}Screen.kt"] = _screen_template(pascal, pkg_ui, camel, with_list)

    _write_files(files, dry_run)
    _print_nav_hint(pascal, camel, dry_run)


def _state_template(pascal: str, pkg: str, with_list: bool) -> str:
    list_field = f"\n    val items: List<String> = emptyList()," if with_list else ""
    return f'''\
package {pkg}

data class {pascal}State(
    val isLoading: Boolean = false,
    val error: String? = null,{list_field}
    // TODO: Add {pascal}-specific state fields
)

sealed interface {pascal}Event {{
    object Refresh : {pascal}Event
    data class OnError(val message: String) : {pascal}Event
    // TODO: Add {pascal}-specific events
}}
'''


def _viewmodel_template(pascal: str, pkg: str, camel: str) -> str:
    return f'''\
package {pkg}

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class {pascal}ViewModel(
    private val coroutineScope: CoroutineScope
) {{
    private val _state = MutableStateFlow({pascal}State())
    val state: StateFlow<{pascal}State> = _state.asStateFlow()

    init {{
        load()
    }}

    fun onEvent(event: {pascal}Event) {{
        when (event) {{
            {pascal}Event.Refresh -> load()
            is {pascal}Event.OnError -> _state.update {{ it.copy(error = event.message) }}
        }}
    }}

    private fun load() {{
        coroutineScope.launch {{
            _state.update {{ it.copy(isLoading = true, error = null) }}
            // TODO: Load data here
            _state.update {{ it.copy(isLoading = false) }}
        }}
    }}
}}
'''


def _screen_template(pascal: str, pkg: str, camel: str, with_list: bool) -> str:
    list_content = ""
    if with_list:
        list_content = """\

        if (state.items.isEmpty() && !state.isLoading) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Text("No items yet", color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        } else {
            LazyColumn(contentPadding = padding) {
                items(state.items) { item ->
                    ListItem(headlineContent = { Text(item) })
                    HorizontalDivider()
                }
            }
        }\
"""
    else:
        list_content = """\

        Box(
            modifier = Modifier.fillMaxSize().padding(padding),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "${pascal} Screen",
                style = MaterialTheme.typography.headlineMedium
            )
        }\
"""

    extra_imports = ""
    if with_list:
        extra_imports = "import androidx.compose.foundation.lazy.LazyColumn\nimport androidx.compose.foundation.lazy.items\nimport androidx.compose.material3.HorizontalDivider\nimport androidx.compose.material3.ListItem\n"

    return f'''\
package {pkg}

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import cafe.adriel.voyager.core.screen.Screen
import cafe.adriel.voyager.navigator.LocalNavigator
import cafe.adriel.voyager.navigator.currentOrThrow
import kotlinx.coroutines.flow.StateFlow
{extra_imports}
/**
 * {pascal} Voyager Screen.
 * Register in Koin: factory {{ {pascal}ViewModel(get()) }}
 * Navigate to it: navigator.push({pascal}Screen)
 */
object {pascal}Screen : Screen {{

    @Composable
    override fun Content() {{
        val navigator = LocalNavigator.currentOrThrow
        // val viewModel = rememberKoinScreenViewModel<{pascal}ViewModel>()
        // val state by viewModel.state.collectAsState()

        {pascal}Content(
            state = {pascal}State(),
            onEvent = {{ /* viewModel.onEvent(it) */ }},
            onBack = {{ navigator.pop() }}
        )
    }}
}}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun {pascal}Content(
    state: {pascal}State,
    onEvent: ({pascal}Event) -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {{
    Scaffold(
        modifier = modifier,
        topBar = {{
            TopAppBar(
                title = {{ Text("{pascal}") }},
                navigationIcon = {{
                    IconButton(onClick = onBack) {{
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back"
                        )
                    }}
                }},
                actions = {{
                    IconButton(onClick = {{ onEvent({pascal}Event.Refresh) }}) {{
                        // Icon(Icons.Default.Refresh, "Refresh")
                    }}
                }}
            )
        }}
    ) {{ padding ->{list_content}

        // Loading overlay
        if (state.isLoading) {{
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {{
                CircularProgressIndicator()
            }}
        }}

        // Error snackbar
        state.error?.let {{ error ->
            // TODO: Show SnackbarHost
        }}
    }}
}}
'''


def _write_files(files: dict, dry_run: bool):
    for path, content in files.items():
        if dry_run:
            print(f"  [DRY RUN] {path.relative_to(PROJECT_ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                print(f"  ⏭️  Exists: {path.relative_to(PROJECT_ROOT)}")
            else:
                path.write_text(content, encoding="utf-8")
                print(f"  ✅ Created: {path.relative_to(PROJECT_ROOT)}")


def _print_nav_hint(pascal: str, camel: str, dry_run: bool):
    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{'─' * 55}")
    print(f"{mode}✅ {pascal}Screen scaffold complete")
    print(f"\nNext steps:")
    print(f"  1. Add ViewModel to Koin in composeApp/di/AppModule.kt:")
    print(f"       factory {{ {pascal}ViewModel(get()) }}")
    print(f"  2. Navigate from another screen:")
    print(f"       navigator.push({pascal}Screen)")
    print(f"  3. Uncomment viewModel lines in {pascal}Screen.Content()")
    print(f"  4. Add state fields in {pascal}State.kt")


def main():
    parser = argparse.ArgumentParser(description="Scaffold Compose Multiplatform Screen (Voyager)")
    parser.add_argument("name", help="Screen name, e.g. 'Dashboard', 'DeviceDetail'")
    parser.add_argument("--with-list", action="store_true", help="Include LazyColumn list layout")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    scaffold_screen(args.name, args.with_list, args.dry_run)


if __name__ == "__main__":
    main()
