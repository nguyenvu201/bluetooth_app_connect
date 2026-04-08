package com.ble.bluetoothapp.ble

import androidx.compose.runtime.Composable

@Composable
expect fun RequestBluetoothPermissions(
    onPermissionsGranted: () -> Unit,
    onPermissionsDenied: () -> Unit
)
