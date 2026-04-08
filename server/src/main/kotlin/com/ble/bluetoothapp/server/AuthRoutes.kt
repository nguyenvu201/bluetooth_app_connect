package com.ble.bluetoothapp.server

import com.auth0.jwt.JWT
import com.auth0.jwt.algorithms.Algorithm
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.Serializable
import org.mindrot.jbcrypt.BCrypt
import java.util.*

@Serializable
data class LoginRequest(val email: String, val password: String)

@Serializable
data class LoginResponse(val token: String)

// Pre-hashed for "admin". Using standard BCrypt.
val dummyHashedPassword = BCrypt.hashpw("admin", BCrypt.gensalt())

fun Route.authRoutes() {
    post("/login") {
        try {
            val req = call.receive<LoginRequest>()
            if (req.email == "admin@iot.com" && BCrypt.checkpw(req.password, dummyHashedPassword)) {
                // 1 week expiration
                val expirationDate = Date(System.currentTimeMillis() + 7L * 24 * 60 * 60 * 1000)
                val token = JWT.create()
                    .withAudience(jwtAudience)
                    .withIssuer(jwtIssuer)
                    .withClaim("email", req.email)
                    .withExpiresAt(expirationDate)
                    .sign(Algorithm.HMAC256(jwtSecret))
                
                call.respond(HttpStatusCode.OK, LoginResponse(token))
            } else {
                call.respond(HttpStatusCode.Unauthorized, "Invalid credentials")
            }
        } catch (e: Exception) {
            call.respond(HttpStatusCode.BadRequest, "Bad request")
        }
    }
}
