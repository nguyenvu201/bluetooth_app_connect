package com.ble.bluetoothapp.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ble.bluetoothapp.ble.BluetoothScanner
import com.ble.bluetoothapp.ble.RequestBluetoothPermissions
import com.juul.kable.Advertisement
import kotlinx.coroutines.launch

@Composable
fun ScannerScreen() {
    val scanner = remember { BluetoothScanner() }
    val discoveredDevices by scanner.discoveredDevices.collectAsState()
    val isScanning by scanner.isScanning.collectAsState()

    var permissionsGranted by remember { mutableStateOf(false) }
    var permissionsRequested by remember { mutableStateOf(false) }

    val coroutineScope = rememberCoroutineScope()

    if (!permissionsGranted && !permissionsRequested) {
        RequestBluetoothPermissions(
            onPermissionsGranted = { 
                permissionsGranted = true 
                permissionsRequested = true
            },
            onPermissionsDenied = { 
                permissionsGranted = false 
                permissionsRequested = true
            }
        )
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(
            text = "Bluetooth BLE Scanner",
            style = MaterialTheme.typography.headlineMedium
        )

        if (!permissionsGranted && permissionsRequested) {
            Text("Bluetooth permissions are required to scan for devices.", color = MaterialTheme.colorScheme.error)
            Button(onClick = { permissionsRequested = false }) {
                Text("Request Permissions Again")
            }
        } else {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    onClick = {
                        coroutineScope.launch {
                            if (isScanning) scanner.stopScan() else scanner.startScan()
                        }
                    },
                    enabled = permissionsGranted
                ) {
                    Text(if (isScanning) "Stop Scan" else "Start Scan")
                }
            }

            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(discoveredDevices) { device ->
                    DeviceItem(device)
                }
            }
        }
    }
}

@Composable
fun DeviceItem(device: Advertisement) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = device.name ?: "Unknown Device", style = MaterialTheme.typography.titleMedium)
            Text(text = device.identifier, style = MaterialTheme.typography.bodySmall)
            Text(text = "RSSI: ${device.rssi}", style = MaterialTheme.typography.bodySmall)
        }
    }
}
