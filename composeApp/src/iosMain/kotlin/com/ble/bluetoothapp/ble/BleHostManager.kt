package com.ble.bluetoothapp.ble

import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.usePinned
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import platform.CoreBluetooth.*
import platform.Foundation.*
import platform.darwin.NSObject

@OptIn(ExperimentalForeignApi::class)
actual class BleHostManager actual constructor() {

    private val _isHosting = MutableStateFlow(false)
    actual val isHosting: StateFlow<Boolean> = _isHosting.asStateFlow()

    private val _incomingMessages = MutableStateFlow<List<ChatMessage>>(emptyList())
    actual val incomingMessages: StateFlow<List<ChatMessage>> = _incomingMessages.asStateFlow()

    private val peripheralDelegate = object : NSObject(), CBPeripheralManagerDelegateProtocol {
        override fun peripheralManagerDidUpdateState(peripheral: CBPeripheralManager) {
            if (peripheral.state == CBManagerStatePoweredOn) {
                setupService()
            }
        }

        override fun peripheralManagerDidStartAdvertising(
            peripheral: CBPeripheralManager,
            error: NSError?
        ) {
            _isHosting.value = error == null
        }

        override fun peripheralManager(
            peripheral: CBPeripheralManager,
            didReceiveWriteRequests: List<*>
        ) {
            didReceiveWriteRequests.forEach { req ->
                val request = req as CBATTRequest
                val data = request.value
                if (data != null) {
                    val bytes = ByteArray(data.length.toInt())
                    data.getBytes(bytes.refTo(0))
                    val messageStr = bytes.decodeToString()
                    
                    _incomingMessages.update { current ->
                        current + ChatMessage(senderName = "Client", message = messageStr, isHost = false)
                    }
                }
                peripheralManager?.respondToRequest(request, CBATTErrorSuccess)
            }
        }
    }

    private var peripheralManager: CBPeripheralManager? = null
    private var txCharacteristic: CBMutableCharacteristic? = null

    // Helper for converting String to CBUUID
    private fun String.toCBUUID() = CBUUID.UUIDWithString(this)

    actual fun startHosting(roomName: String) {
        if (peripheralManager == null) {
            peripheralManager = CBPeripheralManager(peripheralDelegate, null)
        } else if (peripheralManager?.state == CBManagerStatePoweredOn) {
            setupService()
        }
    }

    private fun setupService() {
        val serviceUUID = BleChatConfig.SERVICE_UUID.toCBUUID()
        val txUUID = BleChatConfig.CHAR_TX_UUID.toCBUUID()
        val rxUUID = BleChatConfig.CHAR_RX_UUID.toCBUUID()

        txCharacteristic = CBMutableCharacteristic(
            txUUID,
            CBCharacteristicPropertyNotify or CBCharacteristicPropertyRead,
            null,
            CBAttributePermissionsReadable
        )

        val rxCharacteristic = CBMutableCharacteristic(
            rxUUID,
            CBCharacteristicPropertyWrite or CBCharacteristicPropertyWriteWithoutResponse,
            null,
            CBAttributePermissionsWriteable
        )

        val service = CBMutableService(serviceUUID, primary = true)
        service.characteristics = listOf(txCharacteristic, rxCharacteristic)

        peripheralManager?.addService(service)

        val advertisementData = mapOf<Any?, Any>(
            CBAdvertisementDataServiceUUIDsKey to listOf(serviceUUID)
        )
        peripheralManager?.startAdvertising(advertisementData)
    }

    actual fun stopHosting() {
        peripheralManager?.stopAdvertising()
        peripheralManager?.removeAllServices()
        _isHosting.value = false
    }

    actual fun sendMessage(message: String) {
        val bytes = message.encodeToByteArray()
        val nsData = bytes.usePinned { pinned ->
            NSData.create(
                bytes = pinned.addressOf(0),
                length = bytes.size.toULong()
            )
        }
        
        txCharacteristic?.let { tx ->
            val success = peripheralManager?.updateValue(
                nsData,
                forCharacteristic = tx,
                onSubscribedCentrals = null
            )
            if (success == true) {
                _incomingMessages.update { current ->
                    current + ChatMessage(senderName = "Host", message = message, isHost = true)
                }
            }
        }
    }
}
