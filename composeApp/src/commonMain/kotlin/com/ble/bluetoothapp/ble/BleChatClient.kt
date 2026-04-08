package com.ble.bluetoothapp.ble

import com.juul.kable.Advertisement
import com.juul.kable.Peripheral
import com.juul.kable.State
import com.juul.kable.WriteType
import com.juul.kable.characteristicOf
import com.juul.kable.peripheral
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.IO

class BleChatClient(private val clientName: String = "Client") {

    private var peripheral: Peripheral? = null
    private var connectionJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO)

    private val _incomingMessages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val incomingMessages: StateFlow<List<ChatMessage>> = _incomingMessages.asStateFlow()

    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected.asStateFlow()

    private val rxCharacteristic = characteristicOf(
        service = BleChatConfig.SERVICE_UUID,
        characteristic = BleChatConfig.CHAR_RX_UUID
    )

    private val txCharacteristic = characteristicOf(
        service = BleChatConfig.SERVICE_UUID,
        characteristic = BleChatConfig.CHAR_TX_UUID
    )

    fun connectToHost(advertisement: Advertisement) {
        connectionJob?.cancel()
        connectionJob = scope.launch {
            val p = scope.peripheral(advertisement)
            peripheral = p
            
            p.state.collect { state ->
                _isConnected.value = state is State.Connected
            }
        }

        scope.launch {
            peripheral?.connect()
            
            // Subscribe to TX characteristic
            peripheral?.observe(txCharacteristic)
                ?.catch { e -> println("Observe failed: ${e.message}") }
                ?.collect { data ->
                    val receivedStr = data.decodeToString()
                    _incomingMessages.update { current ->
                        current + ChatMessage(senderName = "Host", message = receivedStr, isHost = true)
                    }
                }
        }
    }

    suspend fun sendMessage(message: String) {
        val p = peripheral ?: return
        if (_isConnected.value) {
            val data = message.encodeToByteArray()
            try {
                p.write(rxCharacteristic, data, WriteType.WithResponse)
                _incomingMessages.update { current ->
                    current + ChatMessage(senderName = clientName, message = message, isHost = false)
                }
            } catch (e: Exception) {
                println("Failed to send message: ${e.message}")
            }
        }
    }

    suspend fun disconnect() {
        peripheral?.disconnect()
        connectionJob?.cancel()
        peripheral = null
    }
}
