package com.ble.bluetoothapp.ble

import kotlinx.coroutines.flow.StateFlow

// Fixed Custom UUIDs for the BLE Chat Room
object BleChatConfig {
    const val SERVICE_UUID = "e54737d2-4ce0-4820-94d3-05c0d575ec68"
    const val CHAR_TX_UUID = "e54737d2-4ce0-4820-94d3-05c0d5750001" // Host -> Client (Notify)
    const val CHAR_RX_UUID = "e54737d2-4ce0-4820-94d3-05c0d5750002" // Client -> Host (Write)
}

data class ChatMessage(
    val senderName: String,
    val message: String,
    val isHost: Boolean
)

expect class BleHostManager() {
    val isHosting: StateFlow<Boolean>
    val incomingMessages: StateFlow<List<ChatMessage>>

    fun startHosting(roomName: String)
    fun stopHosting()
    fun sendMessage(message: String)
}
