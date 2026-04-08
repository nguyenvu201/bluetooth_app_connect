package com.ble.bluetoothapp.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ble.bluetoothapp.ble.BleChatClient
import com.ble.bluetoothapp.ble.BleHostManager
import com.ble.bluetoothapp.ble.BluetoothScanner
import com.ble.bluetoothapp.ble.RequestBluetoothPermissions
import com.juul.kable.Advertisement
import kotlinx.coroutines.launch

enum class ChatMode { NONE, HOST, CLIENT, CHAT_AS_CLIENT }

@Composable
fun BleChatScreen() {
    var chatMode by remember { mutableStateOf(ChatMode.NONE) }
    var permissionsGranted by remember { mutableStateOf(false) }
    var permissionsRequested by remember { mutableStateOf(false) }

    val hostManager = remember { BleHostManager() }
    val chatClient = remember { BleChatClient("Mobile Client") }

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

    if (!permissionsGranted) {
        Column(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
            Text("Bluetooth Permissions are required to proceed.")
            Button(onClick = { permissionsRequested = false }) {
                Text("Retry")
            }
        }
        return
    }

    when (chatMode) {
        ChatMode.NONE -> {
            Column(
                modifier = Modifier.fillMaxSize(),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text("Select Room Mode", style = MaterialTheme.typography.headlineMedium)
                Spacer(modifier = Modifier.height(24.dp))
                Button(onClick = { chatMode = ChatMode.HOST }) {
                    Text("Host a Chat Room")
                }
                Spacer(modifier = Modifier.height(16.dp))
                Button(onClick = { chatMode = ChatMode.CLIENT }) {
                    Text("Join a Chat Room")
                }
            }
        }
        ChatMode.HOST -> {
            HostRoomScreen(
                hostManager = hostManager,
                onBack = {
                    hostManager.stopHosting()
                    chatMode = ChatMode.NONE
                }
            )
        }
        ChatMode.CLIENT -> {
            JoinRoomScreen(
                onConnect = { adv ->
                    chatClient.connectToHost(adv)
                    chatMode = ChatMode.CHAT_AS_CLIENT
                },
                onBack = { chatMode = ChatMode.NONE }
            )
        }
        ChatMode.CHAT_AS_CLIENT -> {
            ClientChatScreen(
                client = chatClient,
                onBack = {
                    chatMode = ChatMode.CLIENT
                }
            )
        }
    }
}

@Composable
fun HostRoomScreen(hostManager: BleHostManager, onBack: () -> Unit) {
    val isHosting by hostManager.isHosting.collectAsState()
    val messages by hostManager.incomingMessages.collectAsState()
    var input by remember { mutableStateOf("") }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Host Room", style = MaterialTheme.typography.titleLarge)
            Button(onClick = onBack) { Text("Back") }
        }
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = {
            if (isHosting) hostManager.stopHosting() else hostManager.startHosting("Room A")
        }) {
            Text(if (isHosting) "Stop Hosting" else "Start Hosting")
        }

        Spacer(modifier = Modifier.height(16.dp))
        LazyColumn(modifier = Modifier.weight(1f)) {
            items(messages) { msg ->
                val bg = if (msg.isHost) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.secondaryContainer
                Card(modifier = Modifier.padding(4.dp).fillMaxWidth()) {
                    Column(modifier = Modifier.padding(8.dp)) {
                        Text(msg.senderName, style = MaterialTheme.typography.labelSmall)
                        Text(msg.message)
                    }
                }
            }
        }
        Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            TextField(value = input, onValueChange = { input = it }, modifier = Modifier.weight(1f))
            Button(onClick = {
                if (input.isNotBlank()) {
                    hostManager.sendMessage(input)
                    input = ""
                }
            }) {
                Text("Send")
            }
        }
    }
}

@Composable
fun JoinRoomScreen(onConnect: (Advertisement) -> Unit, onBack: () -> Unit) {
    val scanner = remember { BluetoothScanner() }
    val discoveredDevices by scanner.discoveredDevices.collectAsState()
    val isScanning by scanner.isScanning.collectAsState()
    val coroutineScope = rememberCoroutineScope()

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Join Room (Scan)", style = MaterialTheme.typography.titleLarge)
            Button(onClick = onBack) { Text("Back") }
        }
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = {
            coroutineScope.launch {
                if (isScanning) scanner.stopScan() else scanner.startScan()
            }
        }) {
            Text(if (isScanning) "Stop Scan" else "Scan for Hosts")
        }

        Spacer(modifier = Modifier.height(16.dp))
        LazyColumn {
            items(discoveredDevices) { device ->
                Card(
                    modifier = Modifier.fillMaxWidth().padding(4.dp),
                    onClick = { onConnect(device) }
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(device.name ?: "Unknown Host", style = MaterialTheme.typography.titleMedium)
                        Text(device.identifier, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@Composable
fun ClientChatScreen(client: BleChatClient, onBack: () -> Unit) {
    val messages by client.incomingMessages.collectAsState()
    val isConnected by client.isConnected.collectAsState()
    var input by remember { mutableStateOf("") }
    val coroutineScope = rememberCoroutineScope()

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Client Chat", style = MaterialTheme.typography.titleLarge)
            Button(onClick = {
                coroutineScope.launch { client.disconnect() }
                onBack()
            }) { Text("Disconnect") }
        }
        Text(if (isConnected) "Connected" else "Connecting...", color = if (isConnected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error)
        
        Spacer(modifier = Modifier.height(16.dp))
        LazyColumn(modifier = Modifier.weight(1f)) {
            items(messages) { msg ->
                val bg = if (msg.isHost) MaterialTheme.colorScheme.secondaryContainer else MaterialTheme.colorScheme.primaryContainer
                Card(modifier = Modifier.padding(4.dp).fillMaxWidth()) {
                    Column(modifier = Modifier.padding(8.dp)) {
                        Text(msg.senderName, style = MaterialTheme.typography.labelSmall)
                        Text(msg.message)
                    }
                }
            }
        }
        Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            TextField(value = input, onValueChange = { input = it }, modifier = Modifier.weight(1f))
            Button(
                enabled = isConnected,
                onClick = {
                    if (input.isNotBlank()) {
                        coroutineScope.launch { client.sendMessage(input) }
                        input = ""
                    }
                }
            ) {
                Text("Send")
            }
        }
    }
}
