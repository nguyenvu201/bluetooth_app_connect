plugins {
    kotlin("jvm")
    id("io.ktor.plugin") version "3.1.1"
    kotlin("plugin.serialization") version "2.3.20"
}

group = "com.ble.bluetoothapp.server"
version = "1.0.0"

application {
    mainClass.set("com.ble.bluetoothapp.server.ApplicationKt")
}

dependencies {
    implementation(libs.ktor.server.core)
    implementation(libs.ktor.server.netty)
    implementation(libs.ktor.server.auth)
    implementation(libs.ktor.server.auth.jwt)
    implementation(libs.ktor.server.content.negotiation)
    implementation(libs.ktor.serialization.kotlinx.json)
    implementation(libs.jbcrypt)
    
    testImplementation(libs.kotlin.testJunit)
    testImplementation(libs.ktor.server.test.host)
}
