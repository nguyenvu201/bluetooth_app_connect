package com.ble.bluetoothapp.ble

import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattServer
import android.bluetooth.BluetoothGattServerCallback
import android.bluetooth.BluetoothGattService
import android.bluetooth.BluetoothManager
import android.bluetooth.le.AdvertiseCallback
import android.bluetooth.le.AdvertiseData
import android.bluetooth.le.AdvertiseSettings
import android.bluetooth.le.BluetoothLeAdvertiser
import android.content.Context
import android.os.ParcelUuid
import com.ble.bluetoothapp.AndroidContextProvider
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import java.util.UUID

@SuppressLint("MissingPermission")
actual class BleHostManager actual constructor() {

    private val context = AndroidContextProvider.context
    private val bluetoothManager = context?.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
    private val bluetoothAdapter = bluetoothManager?.adapter
    private var advertiser: BluetoothLeAdvertiser? = null
    private var gattServer: BluetoothGattServer? = null
    private var connectedDevice: BluetoothDevice? = null
    private var txCharacteristic: BluetoothGattCharacteristic? = null

    private val _isHosting = MutableStateFlow(false)
    actual val isHosting: StateFlow<Boolean> = _isHosting.asStateFlow()

    private val _incomingMessages = MutableStateFlow<List<ChatMessage>>(emptyList())
    actual val incomingMessages: StateFlow<List<ChatMessage>> = _incomingMessages.asStateFlow()

    private val advertiseCallback = object : AdvertiseCallback() {
        override fun onStartSuccess(settingsInEffect: AdvertiseSettings?) {
            _isHosting.value = true
        }

        override fun onStartFailure(errorCode: Int) {
            _isHosting.value = false
        }
    }

    private val gattServerCallback = object : BluetoothGattServerCallback() {
        override fun onConnectionStateChange(device: BluetoothDevice, status: Int, newState: Int) {
            if (newState == BluetoothGatt.STATE_CONNECTED) {
                connectedDevice = device
            } else if (newState == BluetoothGatt.STATE_DISCONNECTED) {
                connectedDevice = null
            }
        }

        override fun onCharacteristicWriteRequest(
            device: BluetoothDevice, requestId: Int, characteristic: BluetoothGattCharacteristic,
            preparedWrite: Boolean, responseNeeded: Boolean, offset: Int, value: ByteArray
        ) {
            if (characteristic.uuid == UUID.fromString(BleChatConfig.CHAR_RX_UUID)) {
                val messageStr = String(value)
                _incomingMessages.update { current ->
                    current + ChatMessage(senderName = "Client", message = messageStr, isHost = false)
                }
                if (responseNeeded) {
                    gattServer?.sendResponse(device, requestId, BluetoothGatt.GATT_SUCCESS, 0, null)
                }
            }
        }
    }

    actual fun startHosting(roomName: String) {
        if (bluetoothAdapter?.isEnabled != true) return

        advertiser = bluetoothAdapter.bluetoothLeAdvertiser
        val settings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_BALANCED)
            .setConnectable(true)
            .build()

        val parcelUuid = ParcelUuid(UUID.fromString(BleChatConfig.SERVICE_UUID))
        val data = AdvertiseData.Builder()
            .setIncludeDeviceName(false)
            .addServiceUuid(parcelUuid)
            .build()

        setupGattServer()
        advertiser?.startAdvertising(settings, data, advertiseCallback)
    }

    private fun setupGattServer() {
        if (context == null) return
        gattServer = bluetoothManager?.openGattServer(context, gattServerCallback)

        val service = BluetoothGattService(
            UUID.fromString(BleChatConfig.SERVICE_UUID),
            BluetoothGattService.SERVICE_TYPE_PRIMARY
        )

        // TX (Host -> Client)
        txCharacteristic = BluetoothGattCharacteristic(
            UUID.fromString(BleChatConfig.CHAR_TX_UUID),
            BluetoothGattCharacteristic.PROPERTY_NOTIFY or BluetoothGattCharacteristic.PROPERTY_READ,
            BluetoothGattCharacteristic.PERMISSION_READ
        )

        // RX (Client -> Host)
        val rxChar = BluetoothGattCharacteristic(
            UUID.fromString(BleChatConfig.CHAR_RX_UUID),
            BluetoothGattCharacteristic.PROPERTY_WRITE or BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE,
            BluetoothGattCharacteristic.PERMISSION_WRITE
        )

        service.addCharacteristic(txCharacteristic)
        service.addCharacteristic(rxChar)

        gattServer?.addService(service)
    }

    actual fun stopHosting() {
        advertiser?.stopAdvertising(advertiseCallback)
        gattServer?.close()
        gattServer = null
        connectedDevice = null
        _isHosting.value = false
    }

    actual fun sendMessage(message: String) {
        val device = connectedDevice ?: return
        val tx = txCharacteristic ?: return
        tx.value = message.encodeToByteArray()
        gattServer?.notifyCharacteristicChanged(device, tx, false)

        _incomingMessages.update { current ->
            current + ChatMessage(senderName = "Host", message = message, isHost = true)
        }
    }
}
