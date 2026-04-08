package com.ble.bluetoothapp.server

import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.server.testing.*
import kotlin.test.*

class AuthRouteTest {

    @Test
    fun `test invalid login returns 401 Unauthorized`() = testApplication {
        application {
            module()
        }

        val response = client.post("/login") {
            header(HttpHeaders.ContentType, ContentType.Application.Json.toString())
            setBody("""{"email": "admin@iot.com", "password": "wrongpassword"}""")
        }

        assertEquals(HttpStatusCode.Unauthorized, response.status)
    }

    @Test
    fun `test valid login returns 200 OK and JWT Token`() = testApplication {
        application {
            module()
        }

        val response = client.post("/login") {
            header(HttpHeaders.ContentType, ContentType.Application.Json.toString())
            setBody("""{"email": "admin@iot.com", "password": "admin"}""")
        }

        assertEquals(HttpStatusCode.OK, response.status)
        val bodyText = response.bodyAsText()
        assertTrue(bodyText.contains("token"), "Response should contain a JWT token")
    }
}
