#!/usr/bin/env python3
"""
KMP Ktor Route Scaffolder
Scaffold Ktor route handler + service + Exposed table + DAO + test
for caonguyen.vu server module.

Usage:
  python route_scaffolder.py Device
  python route_scaffolder.py SensorReading --dry-run
"""

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]
BASE_PACKAGE = "caonguyen.vu"
SERVER_SRC = PROJECT_ROOT / "server/src/main/kotlin/caonguyen/vu/server"
SERVER_TEST = PROJECT_ROOT / "server/src/test/kotlin/caonguyen/vu"


def to_pascal(s: str) -> str:
    return ''.join(w.title() for w in re.split(r'[_\-]', s))


def to_camel(s: str) -> str:
    p = to_pascal(s)
    return p[0].lower() + p[1:]


def to_plural_lower(s: str) -> str:
    """Simple pluraliser for route paths."""
    s = re.sub(r'([A-Z])', r'-\1', s).lstrip('-').lower()
    return s + 's' if not s.endswith('s') else s


def scaffold_route(name: str, dry_run: bool = False):
    pascal = to_pascal(name)
    camel = to_camel(name)
    route_path = to_plural_lower(pascal)

    print(f"\n🖥  Scaffolding Ktor Route: /api/{route_path}")
    print(f"   Module: {pascal}")
    print(f"   Package: {BASE_PACKAGE}.server\n")

    files = {}

    # ── 1. Exposed Table ──────────────────────────────────────────────────────
    files[SERVER_SRC / f"database/{pascal}Table.kt"] = f'''\
package {BASE_PACKAGE}.server.database

import org.jetbrains.exposed.sql.Table
import org.jetbrains.exposed.sql.kotlin.datetime.CurrentTimestamp
import org.jetbrains.exposed.sql.kotlin.datetime.timestamp

object {pascal}Table : Table("{route_path.replace("-", "_")}") {{
    val id        = varchar("id", 36)
    val name      = varchar("name", 255)
    // TODO: Add {pascal}-specific columns
    val createdAt = timestamp("created_at").defaultExpression(CurrentTimestamp)

    override val primaryKey = PrimaryKey(id)
}}
'''

    # ── 2. DAO ────────────────────────────────────────────────────────────────
    files[SERVER_SRC / f"database/{pascal}Dao.kt"] = f'''\
package {BASE_PACKAGE}.server.database

import kotlinx.coroutines.Dispatchers
import org.jetbrains.exposed.sql.*
import org.jetbrains.exposed.sql.SqlExpressionBuilder.eq
import org.jetbrains.exposed.sql.transactions.experimental.newSuspendedTransaction
import java.util.UUID

data class {pascal}Entity(
    val id: String,
    val name: String,
    // TODO: Match fields to {pascal}Table
)

class {pascal}Dao {{

    suspend fun findAll(): List<{pascal}Entity> = dbQuery {{
        {pascal}Table.selectAll().map {{ it.to{pascal}Entity() }}
    }}

    suspend fun findById(id: String): {pascal}Entity? = dbQuery {{
        {pascal}Table.selectAll()
            .where {{ {pascal}Table.id eq id }}
            .singleOrNull()
            ?.to{pascal}Entity()
    }}

    suspend fun insert(entity: {pascal}Entity): {pascal}Entity = dbQuery {{
        val newId = UUID.randomUUID().toString()
        {pascal}Table.insert {{
            it[id]   = newId
            it[name] = entity.name
            // TODO: Insert additional fields
        }}
        entity.copy(id = newId)
    }}

    suspend fun update(entity: {pascal}Entity): Boolean = dbQuery {{
        {pascal}Table.update({{ {pascal}Table.id eq entity.id }}) {{
            it[name] = entity.name
            // TODO: Update additional fields
        }} > 0
    }}

    suspend fun delete(id: String): Boolean = dbQuery {{
        {pascal}Table.deleteWhere {{ {pascal}Table.id eq id }} > 0
    }}

    private fun ResultRow.to{pascal}Entity() = {pascal}Entity(
        id   = this[{pascal}Table.id],
        name = this[{pascal}Table.name],
        // TODO: Map additional fields
    )

    private suspend fun <T> dbQuery(block: () -> T): T =
        newSuspendedTransaction(Dispatchers.IO) {{ block() }}
}}
'''

    # ── 3. Service ────────────────────────────────────────────────────────────
    files[SERVER_SRC / f"service/{pascal}Service.kt"] = f'''\
package {BASE_PACKAGE}.server.service

import {BASE_PACKAGE}.server.database.{pascal}Dao
import {BASE_PACKAGE}.server.database.{pascal}Entity

class {pascal}Service(private val dao: {pascal}Dao) {{

    suspend fun getAll(): List<{pascal}Entity> = dao.findAll()

    suspend fun getById(id: String): {pascal}Entity? = dao.findById(id)

    suspend fun create(name: String /* TODO: Add params */): {pascal}Entity =
        dao.insert({pascal}Entity(id = "", name = name))

    suspend fun update(id: String, name: String): Boolean {{
        val existing = dao.findById(id) ?: return false
        return dao.update(existing.copy(name = name))
    }}

    suspend fun delete(id: String): Boolean = dao.delete(id)
}}
'''

    # ── 4. Route Handler ──────────────────────────────────────────────────────
    files[SERVER_SRC / f"routes/{pascal}Routes.kt"] = f'''\
package {BASE_PACKAGE}.server.routes

import {BASE_PACKAGE}.server.service.{pascal}Service
import io.ktor.http.*
import io.ktor.server.auth.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.Serializable

@Serializable
data class Create{pascal}Request(val name: String /* TODO: Add fields */)

@Serializable
data class Update{pascal}Request(val name: String /* TODO: Add fields */)

fun Route.{camel}Routes({camel}Service: {pascal}Service) {{

    route("/api/{route_path}") {{

        // GET all
        get {{
            val items = {camel}Service.getAll()
            call.respond(HttpStatusCode.OK, items)
        }}

        // GET by ID
        get("/{{id}}") {{
            val id = call.parameters["id"]
                ?: return@get call.respond(HttpStatusCode.BadRequest, "Missing id")
            val item = {camel}Service.getById(id)
                ?: return@get call.respond(HttpStatusCode.NotFound, "Not found")
            call.respond(item)
        }}

        // POST — create (requires JWT)
        authenticate("jwt-admin") {{
            post {{
                val req = call.receive<Create{pascal}Request>()
                val created = {camel}Service.create(req.name)
                call.respond(HttpStatusCode.Created, created)
            }}

            // PUT — update
            put("/{{id}}") {{
                val id = call.parameters["id"]!!
                val req = call.receive<Update{pascal}Request>()
                val updated = {camel}Service.update(id, req.name)
                if (updated) call.respond(HttpStatusCode.OK)
                else call.respond(HttpStatusCode.NotFound, "Not found")
            }}

            // DELETE
            delete("/{{id}}") {{
                val id = call.parameters["id"]!!
                val deleted = {camel}Service.delete(id)
                if (deleted) call.respond(HttpStatusCode.NoContent)
                else call.respond(HttpStatusCode.NotFound, "Not found")
            }}
        }}
    }}
}}
'''

    # ── 5. Ktor Test ──────────────────────────────────────────────────────────
    files[SERVER_TEST / f"{pascal}RoutesTest.kt"] = f'''\
package {BASE_PACKAGE}

import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.server.testing.*
import kotlin.test.Test
import kotlin.test.assertEquals

class {pascal}RoutesTest {{

    @Test
    fun `GET {route_path} returns 200`() = testApplication {{
        application {{ module() }}

        val response = client.get("/api/{route_path}")
        assertEquals(HttpStatusCode.OK, response.status)
    }}

    @Test
    fun `GET {route_path} by unknown id returns 404`() = testApplication {{
        application {{ module() }}

        val response = client.get("/api/{route_path}/non-existent-id")
        assertEquals(HttpStatusCode.NotFound, response.status)
    }}

    @Test
    fun `POST {route_path} without JWT returns 401`() = testApplication {{
        application {{ module() }}

        val response = client.post("/api/{route_path}") {{
            contentType(ContentType.Application.Json)
            setBody("""{{"name":"test"}}""")
        }}
        assertEquals(HttpStatusCode.Unauthorized, response.status)
    }}
}}
'''

    _write_files(files, dry_run)
    _print_summary(pascal, camel, route_path, dry_run)


def _write_files(files: dict, dry_run: bool):
    for path, content in files.items():
        if dry_run:
            print(f"  [DRY RUN] {path.relative_to(PROJECT_ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                print(f"  ⏭️  Exists: {path.relative_to(PROJECT_ROOT)}")
            else:
                path.write_text(content, encoding="utf-8")
                print(f"  ✅ Created: {path.relative_to(PROJECT_ROOT)}")


def _print_summary(pascal: str, camel: str, route_path: str, dry_run: bool):
    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{'─' * 55}")
    print(f"{mode}✅ Ktor route scaffold for /api/{route_path} — done")
    print(f"\nNext steps:")
    print(f"  1. Add table to DatabaseFactory.kt SchemaUtils.create()")
    print(f"     SchemaUtils.create({pascal}Table)")
    print(f"  2. Register route in Application.kt routing block:")
    print(f"     {camel}Routes({pascal}Service({pascal}Dao()))")
    print(f"  3. Fill in TODO fields in {pascal}Table, {pascal}Dao, {pascal}Entity")
    print(f"  4. Run: ./gradlew :server:test")


def main():
    parser = argparse.ArgumentParser(description="Scaffold Ktor REST route")
    parser.add_argument("name", help="Resource name, e.g. 'Device', 'SensorReading'")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    scaffold_route(args.name, args.dry_run)


if __name__ == "__main__":
    main()
