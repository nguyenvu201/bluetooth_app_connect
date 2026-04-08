package com.ble.bluetoothapp.ble

import androidx.compose.runtime.Composable

@Composable
actual fun RequestBluetoothPermissions(
    onPermissionsGranted: () -> Unit,
    onPermissionsDenied: () -> Unit
) {
    // Desktop currently does not require strict granular permissions like Android.
    // Just invoke the granted callback immediately.
    onPermissionsGranted()
}
