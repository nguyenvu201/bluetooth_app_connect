# Changelog

## [Unreleased]
### Added
- **BLE Chat Room Infrastructure**: Added support for Host (Peripheral) and Client (Central) BLE chat communication.
  - Implemented `actual class BleHostManager` for Android using `BluetoothLeAdvertiser` and `BluetoothGattServer`.
  - Implemented `actual class BleHostManager` for iOS using `CBPeripheralManager`.
  - Created `BleChatClient` utilizing Kable for Central role connection and GATT characteristic subscription.
  - Created unified `BleChatScreen` utilizing Compose Multiplatform.
