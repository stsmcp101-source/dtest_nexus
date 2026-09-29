"""
Read-only access layer behind the Data Explorer.

Two "sources" are supported:
  - "sqlite": the app's own currently-configured default database
    (django.db.connection — SQLite in development), browsed through
    Django's own introspection API.
  - an actual DatabaseConnection row: a separate SQL Server reached
    fresh, per request, via pyodbc using that row's stored credentials.

Table names are never interpolated into SQL from raw user input: every
load_table() call re-fetches the real table list from the database's
own metadata and rejects anything that isn't an exact match, before the
(bracket-quoted) identifier is used to build the SELECT.
"""
import pyodbc
from django.db import connection as django_connection
from django.utils import timezone

ROW_LIMIT = 200
CONNECT_TIMEOUT_SECONDS = 5


class QueryError(Exception):
    """Raised with a Thai, user-facing message on any connection/query failure."""


def build_connection_string(server, database, username, password, driver, port=None):
    host = f"{server},{port}" if port else server
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={host}",
        f"DATABASE={database}",
        f"UID={username}",
        f"PWD={password}",
        "TrustServerCertificate=yes",
    ]
    return ";".join(parts)


def test_connection(server, database, username, password, driver, port=None):
    """Attempts a real connection + SELECT 1. Returns (ok, message)."""
    if not server or not database:
        return False, "กรุณากรอก Server และ Database"
    try:
        cs = build_connection_string(server, database, username, password, driver, port)
        with pyodbc.connect(cs, timeout=CONNECT_TIMEOUT_SECONDS) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True, "เชื่อมต่อสำเร็จ"
    except pyodbc.Error as exc:
        msg = str(exc.args[-1] if exc.args else exc)
        return False, f"เชื่อมต่อไม่สำเร็จ: {msg}"
    except Exception as exc:  # noqa: BLE001 - surfaced to the admin as a test result, not a 500
        return False, f"เกิดข้อผิดพลาด: {exc}"


def _connect(conn_row):
    cs = build_connection_string(
        conn_row.server, conn_row.database_name, conn_row.username, conn_row.get_password(),
        conn_row.driver, conn_row.port,
    )
    return pyodbc.connect(cs, timeout=CONNECT_TIMEOUT_SECONDS)


def list_tables(source, conn_row=None):
    """Returns a sorted list of table identifiers (strings) for the given
    source. For sqlite these are bare table names; for mssql they are
    'schema.table'."""
    if source == "sqlite":
        try:
            return sorted(django_connection.introspection.table_names())
        except Exception as exc:  # noqa: BLE001
            raise QueryError(f"ไม่สามารถอ่านรายชื่อตารางได้: {exc}") from exc

    try:
        with _connect(conn_row) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_SCHEMA, TABLE_NAME"
            )
            return [f"{schema}.{table}" for schema, table in cursor.fetchall()]
    except pyodbc.Error as exc:
        msg = str(exc.args[-1] if exc.args else exc)
        raise QueryError(f"ไม่สามารถเชื่อมต่อเพื่ออ่านรายชื่อตารางได้: {msg}") from exc


def load_table(source, table_name, conn_row=None, limit=ROW_LIMIT):
    """Validates table_name against a fresh table list, then returns
    {"columns": [...], "rows": [[...], ...], "truncated": bool}."""
    valid_tables = list_tables(source, conn_row)
    if table_name not in valid_tables:
        raise QueryError("ไม่พบตารางนี้ในฐานข้อมูล")

    if source == "sqlite":
        quoted = f'"{table_name}"'
        with django_connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {quoted} LIMIT %s", [limit + 1])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
        truncated = len(rows) > limit
        return {"columns": columns, "rows": [list(r) for r in rows[:limit]], "truncated": truncated}

    schema, _, bare_table = table_name.partition(".")
    quoted = f"[{schema}].[{bare_table}]"
    try:
        with _connect(conn_row) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT TOP {int(limit) + 1} * FROM {quoted}")
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
    except pyodbc.Error as exc:
        msg = str(exc.args[-1] if exc.args else exc)
        raise QueryError(f"อ่านข้อมูลไม่สำเร็จ: {msg}") from exc
    truncated = len(rows) > limit
    return {"columns": columns, "rows": [list(r) for r in rows[:limit]], "truncated": truncated}


def record_test_result(conn_row, ok, message):
    conn_row.last_test_ok = ok
    conn_row.last_test_message = message[:500]
    conn_row.last_test_at = timezone.now()
    conn_row.save(update_fields=["last_test_ok", "last_test_message", "last_test_at"])
