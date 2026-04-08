package com.ble.bluetoothapp

interface Platform {
    val name: String
}

expect fun getPlatform(): Platform