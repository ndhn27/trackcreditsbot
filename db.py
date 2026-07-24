"""
Async database access, schema management, and callback-hash persistence.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import time
import unicodedata
from contextlib import asynccontextmanager
from typing import Any, Sequence

import asyncpg

from config import DATABASE_URL, logger
from metrics import metric_inc


class Database:
    def __init__(
        self,
        *,
        dsn: str | None = None,
        min_size: int = 1,
        max_size: int = 10,
        command_timeout: int = 60,
    ) -> None:
        self._dsn = dsn if dsn is not None else DATABASE_URL
        self._min_size = min_size
        self._max_size = max_size
        self._command_timeout = command_timeout

        self._pool: asyncpg.Pool | None = None
        self._pool_lock = asyncio.Lock()

        self._track_hash_ttl_seconds = 3600
        self._track_hash_cache: dict[str, tuple[str, int]] = {}
        self._track_hash_lock = asyncio.Lock()
        self._track_hash_last_cleanup = 0

    async def start(self) -> None:
        if self._pool is not None:
            return
        if not self._dsn:
            raise ValueError("DATABASE_URL is not configured.")

        async with self._pool_lock:
            if self._pool is not None:
                return
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=self._min_size,
                max_size=self._max_size,
                command_timeout=self._command_timeout,
            )

    async def stop(self) -> None:
        async with self._pool_lock:
            pool = self._pool
            self._pool = None
        if pool is not None:
            await pool.close()

    @staticmethod
    def _normalize_row(row: asyncpg.Record | None) -> tuple | None:
        return tuple(row) if row is not None else None

    @staticmethod
    def _normalize_rows(rows: list[asyncpg.Record]) -> list[tuple]:
        return [tuple(row) for row in rows]

    @staticmethod
    def _rowcount_from_status(status: str) -> int:
        try:
            return int(status.rsplit(" ", 1)[-1])
        except (TypeError, ValueError):
            return 0

    async def execute(
        self,
        query: str,
        params: Sequence[Any] = (),
        *,
        fetch: bool = False,
        fetch_all: bool = False,
        returning: bool = False,
    ) -> Any:
        await self.start()
        if self._pool is None:
            raise RuntimeError(
                "Database pool is not initialized. "
                "This should not happen after start() — check app startup sequence."
            )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self._pool.acquire() as conn:
                    if fetch_all:
                        return self._normalize_rows(await conn.fetch(query, *params))
                    if returning:
                        return await conn.fetchval(query, *params)
                    if fetch:
                        return self._normalize_row(await conn.fetchrow(query, *params))
                    return self._rowcount_from_status(await conn.execute(query, *params))
            except (asyncpg.InterfaceError, asyncpg.PostgresConnectionError, ConnectionError, OSError) as exc:
                metric_inc("db_retry")
                if attempt < max_retries - 1:
                    wait_time = 0.5 * (2**attempt)
                    logger.warning(
                        "DB connection error attempt %d/%d; retrying in %.1fs: %s",
                        attempt + 1,
                        max_retries,
                        wait_time,
                        exc,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                logger.error("DB connection error after %d attempts: %s", max_retries, exc)
                raise
            except Exception:
                logger.exception("DB error while executing query: %.160s", query)
                raise

    async def _ensure_migrations_table(self, conn) -> None:
        """
        Tạo bảng schema_migrations nếu chưa có.
        Bảng này lưu lại migration nào đã được chạy để không chạy lại.
        """
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version     TEXT PRIMARY KEY,
                applied_at  BIGINT NOT NULL
            )
            """
        )

    async def run_migrations(self) -> None:
        """
        Tìm và chạy tất cả file .sql trong thư mục migrations/ theo thứ tự số.
        Chỉ chạy những migration chưa được apply — idempotent và an toàn khi
        restart nhiều lần.
        """
        import pathlib

        await self.start()
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized.")

        migrations_dir = pathlib.Path(__file__).parent / "migrations"
        if not migrations_dir.exists():
            logger.warning("migrations/ directory not found, skipping.")
            return

        sql_files = sorted(migrations_dir.glob("*.sql"))
        if not sql_files:
            return

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await self._ensure_migrations_table(conn)

                applied = {
                    row[0]
                    for row in await conn.fetch("SELECT version FROM schema_migrations")
                }

                for sql_file in sql_files:
                    version = sql_file.stem
                    if version in applied:
                        logger.debug("Migration %s already applied, skipping.", version)
                        continue

                    sql = sql_file.read_text(encoding="utf-8")
                    logger.info("Applying migration: %s", version)
                    await conn.execute(sql)
                    await conn.execute(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES ($1, $2)",
                        version,
                        int(time.time()),
                    )
                    logger.info("Migration %s applied successfully.", version)

        logger.info("All migrations up to date.")

    async def init_db(self) -> None:
        """
        Apply all pending database migrations.
        Safe to call on every startup — migrations đã applied sẽ bị bỏ qua.
        """
        await self.run_migrations()
    async def add_score(self, user_id: int, username: str, points: int) -> None:
        await self.execute(
            "INSERT INTO leaderboard (user_id, username, score) VALUES ($1, $2, $3) "
            "ON CONFLICT (user_id) DO UPDATE SET score = leaderboard.score + $4, username = $5",
            (user_id, username, points, points, username),
        )

    @staticmethod
    def make_key(title: str, artist: str) -> str:
        raw = unicodedata.normalize("NFKC", f"{title}:{artist}")
        return re.sub(r"\s+", "", raw.casefold().strip())

    @staticmethod
    def hash_track_key(track_key: str) -> str:
        return hashlib.md5(track_key.encode("utf-8")).hexdigest()[:16]

    def _cleanup_track_hash_cache(self, now: int) -> None:
        expired = [
            track_hash
            for track_hash, (_, expires_at) in self._track_hash_cache.items()
            if expires_at <= now
        ]
        for track_hash in expired:
            self._track_hash_cache.pop(track_hash, None)

    async def _cleanup_track_hash_table(self, now: int) -> None:
        if now - self._track_hash_last_cleanup < 300:
            return
        try:
            await self.execute("DELETE FROM track_hashes WHERE expires_at <= $1", (now,))
            self._track_hash_last_cleanup = now
        except Exception as exc:
            logger.warning("Failed to cleanup expired track hashes: %s", exc)

    async def store_track_hash(self, track_key: str, track_hash: str | None = None) -> str:
        now = int(time.time())
        expires_at = now + self._track_hash_ttl_seconds
        track_hash = track_hash or self.hash_track_key(track_key)

        async with self._track_hash_lock:
            self._cleanup_track_hash_cache(now)
            self._track_hash_cache[track_hash] = (track_key, expires_at)

        try:
            await self.execute(
                "INSERT INTO track_hashes (track_hash, track_key, expires_at) VALUES ($1, $2, $3) "
                "ON CONFLICT (track_hash) DO UPDATE SET track_key = EXCLUDED.track_key, expires_at = EXCLUDED.expires_at",
                (track_hash, track_key, expires_at),
            )
        except Exception as exc:
            logger.warning("Failed to persist track hash %s: %s", track_hash, exc)

        await self._cleanup_track_hash_table(now)
        return track_hash

    async def get_track_key_from_hash(self, track_hash: str) -> str | None:
        now = int(time.time())

        async with self._track_hash_lock:
            self._cleanup_track_hash_cache(now)
            cached = self._track_hash_cache.get(track_hash)
            if cached:
                return cached[0]

        await self._cleanup_track_hash_table(now)
        row = await self.execute(
            "SELECT track_key, expires_at FROM track_hashes WHERE track_hash = $1",
            (track_hash,),
            fetch=True,
        )
        if not row:
            return None

        track_key, expires_at = row
        if expires_at <= now:
            try:
                await self.execute("DELETE FROM track_hashes WHERE track_hash = $1", (track_hash,))
            except Exception as exc:
                logger.warning("Failed to delete expired track hash %s: %s", track_hash, exc)
            return None

        async with self._track_hash_lock:
            self._track_hash_cache[track_hash] = (track_key, expires_at)
        return track_key

    @asynccontextmanager
    async def transaction(self):
        """
        Async context manager cấp một asyncpg connection với transaction đang hoạt động.

        Truy cập self._pool hợp lệ ở đây vì đây là method của class — đây chính xác
        là sự khác biệt so với hàm module-level db_transaction() cũ, vốn phải khoét
        vào _db._pool từ bên ngoài class (vi phạm encapsulation).

        Usage:
            async with db.transaction() as conn:
                await db_execute_conn(conn, "UPDATE ...")
                await db_execute_conn(conn, "INSERT ...")
            # commit tại đây; rollback tự động nếu có exception
        """
        await self.start()
        # Sau start(), _pool được đảm bảo không None. Guard này chỉ để
        # type-checker yên tâm — trên thực tế start() đã raise nếu pool không tạo được.
        if self._pool is None:
            raise RuntimeError(
                "Database pool is not initialized after start() — "
                "check application startup sequence."
            )
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn


# ── Module-level injectable registry ──────────────────────────────────────────
#
# Trước đây: _db = Database()  ← singleton tạo ngay lúc import, không thể inject.
# Bây giờ: _db bắt đầu là None. app_factory.py gọi set_default_db(instance) một lần
# duy nhất trong quá trình khởi động, sau đó tất cả db_execute / db_transaction
# đều đi qua instance đó — cùng một instance với AppContext.db.
#
# Lợi ích chính:
#   1. Không còn hai connection pool song song.
#   2. Test có thể inject mock Database mà không cần monkey-patch module.
#   3. db_transaction() không cần truy cập _db._pool nữa — nó gọi .transaction()
#      vốn là public method của class.

_db: Database | None = None


def set_default_db(db: Database) -> None:
    """
    Gán Database instance làm default cho toàn module.

    Phải được gọi đúng một lần trong app_factory.setup_app_context(),
    SAU khi db instance được tạo và TRƯỚC khi bất kỳ handler nào chạy.
    """
    global _db
    _db = db


def _get_db() -> Database:
    """
    Trả về default Database instance. Raise rõ ràng nếu chưa được inject.

    Thay thế cho việc truy cập trực tiếp biến _db — mọi wrapper function
    đều đi qua đây để lỗi thiếu inject được phát hiện sớm, không silent.
    """
    if _db is None:
        raise RuntimeError(
            "Default database chưa được cấu hình. "
            "Gọi db.set_default_db(instance) trong app_factory.setup_app_context()."
        )
    return _db


async def db_execute(
    query: str,
    params: Sequence[Any] = (),
    *,
    fetch: bool = False,
    fetch_all: bool = False,
    returning: bool = False,
) -> Any:
    return await _get_db().execute(
        query,
        params,
        fetch=fetch,
        fetch_all=fetch_all,
        returning=returning,
    )


@asynccontextmanager
async def db_transaction():
    """
    Async context manager that yields an asyncpg connection with an active
    PostgreSQL transaction.  All queries executed through the yielded
    connection are committed atomically when the ``async with`` block exits
    normally, or rolled back on any exception.

    Usage::

        async with db_transaction() as conn:
            await db_execute_conn(conn, "UPDATE ...", (...,))
            await db_execute_conn(conn, "INSERT ...", (...,))
        # commit happens here; invalidate caches AFTER this point

    Delegate sang Database.transaction() — không còn truy cập _db._pool trực tiếp.
    """
    async with _get_db().transaction() as conn:
        yield conn


async def db_execute_conn(
    conn,
    query: str,
    params: Sequence[Any] = (),
    *,
    fetch: bool = False,
    fetch_all: bool = False,
    returning: bool = False,
) -> Any:
    """
    Execute *query* on an already-acquired *conn* (e.g. from
    :func:`db_transaction`).  Signature mirrors :func:`db_execute`.
    """
    if fetch_all:
        return Database._normalize_rows(await conn.fetch(query, *params))
    if returning:
        return await conn.fetchval(query, *params)
    if fetch:
        return Database._normalize_row(await conn.fetchrow(query, *params))
    return Database._rowcount_from_status(await conn.execute(query, *params))


async def init_db() -> None:
    await _get_db().init_db()


async def close_db_pool() -> None:
    await _get_db().stop()


async def add_score(user_id: int, username: str, points: int) -> None:
    await _get_db().add_score(user_id, username, points)


def make_key(title: str, artist: str) -> str:
    return Database.make_key(title, artist)


def hash_track_key(track_key: str) -> str:
    return Database.hash_track_key(track_key)


async def store_track_hash(track_key: str, track_hash: str | None = None) -> str:
    return await _get_db().store_track_hash(track_key, track_hash)


async def get_track_key_from_hash(track_hash: str) -> str | None:
    return await _get_db().get_track_key_from_hash(track_hash)

