import os
import time
import aiosqlite

# Railway'da Volume ulab, DB_PATH=/data/bot.db qilib qo'ying (aks holda deploydan keyin baza o'chadi)
DB = os.getenv("DB_PATH", "bot.db")


async def init():
    os.makedirs(os.path.dirname(os.path.abspath(DB)), exist_ok=True)
    async with aiosqlite.connect(DB) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY, currency TEXT DEFAULT 'UZS');
            CREATE TABLE IF NOT EXISTS orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, username TEXT, player_id TEXT,
                uc INTEGER, amount_uzs INTEGER, method TEXT, promo TEXT,
                status TEXT, created_at INTEGER);
            """
        )
        await db.commit()


async def get_currency(uid: int) -> str:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT currency FROM users WHERE id=?", (uid,))
        row = await cur.fetchone()
        return row[0] if row else "UZS"


async def set_currency(uid: int, currency: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO users(id, currency) VALUES(?, ?) "
            "ON CONFLICT(id) DO UPDATE SET currency=excluded.currency",
            (uid, currency),
        )
        await db.commit()


async def create_order(user_id, username, player_id, uc, amount, method, promo) -> int:
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "INSERT INTO orders(user_id, username, player_id, uc, amount_uzs, "
            "method, promo, status, created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (user_id, username, player_id, uc, amount, method, promo,
             "pending", int(time.time())),
        )
        await db.commit()
        return cur.lastrowid


async def get_order(order_id: int):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        return await cur.fetchone()


async def set_status(order_id: int, status: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        await db.commit()


async def stats():
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT status, COUNT(*), COALESCE(SUM(amount_uzs),0) "
            "FROM orders GROUP BY status"
        )
        return await cur.fetchall()
