# Feature Context: BLE Chat Room (feat/BLE-CHAT)

## Objective
Establish a Host-Client chat ecosystem via BLE. Devices can either broadcast their presence (Host/Peripheral) or scan and connect to hosts (Client/Central).

## Architecture Details

1. **Host (Peripheral)**
   - Utilizes `expect`/`actual` standard in KMP.
   - **Android**: Custom `actual class BleHostManager` utilizing `BluetoothLeAdvertiser` and `BluetoothGattServer`.
   - **iOS**: Custom `actual class BleHostManager` utilizing `CBPeripheralManager`.
   - GATT Service: One custom Chat Service UUID.
   - GATT Characteristics: TX (Host sends to Client via Notification), RX (Client writes to Host).

2. **Client (Central)**
   - Utilizes [Kable](https://github.com/JuulLabs/kable) directly from `commonMain`.
   - Modifies `BluetoothScanner.kt` to allow filtering by the Chat Service UUID.
   - Implement `BleChatClient.kt` to manage `Peripheral` state connection, subscribe to the TX characteristic, and write to the RX characteristic.

## UI / Compose Layout
- Unified role selection to initiate the process.
- Real-time `LazyColumn` powered by a `StateFlow<List<ChatMessage>>`.

## API Spec
- **Service UUID**: `0000180D-0000-1000-8000-00805f9b34fb` (Using Heart Rate as placeholder or custom UUID `e54737d2-4ce0-4820-94d3-05c0d575ec68`).
- **TX Char (Host -> Client)**: `...-0001`
- **RX Char (Client -> Host)**: `...-0002`

*Document generated via kmp-architect orchestration workflow rule validation.*
