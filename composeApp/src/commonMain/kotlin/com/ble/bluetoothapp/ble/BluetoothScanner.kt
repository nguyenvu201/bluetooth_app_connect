package com.ble.bluetoothapp.ble

import com.juul.kable.Advertisement
import com.juul.kable.Scanner
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.flow.update

class BluetoothScanner {
    private val scanner = Scanner()

    private val _discoveredDevices = MutableStateFlow<List<Advertisement>>(emptyList())
    val discoveredDevices: StateFlow<List<Advertisement>> = _discoveredDevices.asStateFlow()

    private val _isScanning = MutableStateFlow(false)
    val isScanning: StateFlow<Boolean> = _isScanning.asStateFlow()

    suspend fun startScan() {
        if (_isScanning.value) return

        _isScanning.value = true
        _discoveredDevices.value = emptyList() // clear previous scan results

        scanner.advertisements
            .catch { e ->
                // Handle scan failure
                println("Scan failed: ${e.message}")
            }
            .onCompletion {
                _isScanning.value = false
            }
            .collect { advertisement ->
                _discoveredDevices.update { currentList ->
                    val index = currentList.indexOfFirst { it.identifier == advertisement.identifier }
                    if (index >= 0) {
                        val toMutableList = currentList.toMutableList()
                        toMutableList[index] = advertisement
                        toMutableList
                    } else {
                        currentList + advertisement
                    }
                }
            }
    }

    fun stopScan() {
        _isScanning.value = false
    }
}
