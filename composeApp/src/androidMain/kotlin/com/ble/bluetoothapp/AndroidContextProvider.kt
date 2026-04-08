package com.ble.bluetoothapp

import android.annotation.SuppressLint
import android.content.Context

@SuppressLint("StaticFieldLeak")
object AndroidContextProvider {
    var context: Context? = null
}
