package com.ble.bluetoothapp

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeContentPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue

@Composable
@Preview
fun App() {
    MaterialTheme {
        Column(
            modifier = Modifier
                .background(MaterialTheme.colorScheme.background)
                .safeContentPadding()
                .fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            var isLoggedIn by androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf<Boolean>(false) }

            if (isLoggedIn == false) {
                com.ble.bluetoothapp.ui.LoginScreen(onLoginSuccess = { isLoggedIn = true })
            } else {
                com.ble.bluetoothapp.ui.ScannerScreen()
            }
        }
    }
}