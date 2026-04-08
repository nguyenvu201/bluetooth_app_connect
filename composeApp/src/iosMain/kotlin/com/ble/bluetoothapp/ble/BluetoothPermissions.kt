package com.ble.bluetoothapp.ble

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect

@Composable
actual fun RequestBluetoothPermissions(
    onPermissionsGranted: () -> Unit,
    onPermissionsDenied: () -> Unit
) {
    // iOS handles Bluetooth permission automatically when scanning starts via CoreBluetooth.
    // We instantly grant it for the UI wrapper.
    LaunchedEffect(Unit) {
        onPermissionsGranted()
    }
}
