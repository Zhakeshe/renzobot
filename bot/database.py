import aiosqlite

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path

    async def setup(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Миграцияларды қадағалау кестесі
            await db.execute("CREATE TABLE IF NOT EXISTS migrations (version INTEGER PRIMARY KEY)")
            
            # Негізгі кестелер
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    balance_kzt REAL DEFAULT 0.0,
                    username TEXT,
                    referred_by INTEGER,
                    language TEXT DEFAULT 'kz',
                    ip_address TEXT,
                    device_id TEXT,
                    is_blocked INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    order_id_api INTEGER,
                    status TEXT,
                    product_type TEXT,
                    amount_kzt REAL,
                    profit_kzt REAL,
                    tx_hash TEXT,
                    is_notified INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Миграция логикасы: жаңа бағандарды қосу
            cursor = await db.execute("SELECT version FROM migrations")
            row = await cursor.fetchone()
            version = row[0] if row else 0

            if version < 1:
                try:
                    await db.execute("ALTER TABLE users ADD COLUMN ip_address TEXT")
                    await db.execute("ALTER TABLE users ADD COLUMN device_id TEXT")
                except: pass # Баған бар болса қате бермейді
                await db.execute("INSERT OR REPLACE INTO migrations (version) VALUES (1)")

            await db.commit()

    async def update_anti_fraud(self, user_id: int, ip: str, device: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET ip_address = ?, device_id = ? WHERE user_id = ?", (ip, device, user_id))
            await db.commit()

    async def check_fraud(self, user_id: int, ip: str):
        async with aiosqlite.connect(self.db_path) as db:
            # Бір IP-мен тіркелген басқа пайдаланушыларды тексеру
            async with db.execute("SELECT COUNT(*) FROM users WHERE ip_address = ? AND user_id != ?", (ip, user_id)) as c:
                count = (await c.fetchone())[0]
                return count > 2 # Егер 2-ден көп болса, күдікті

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                return [row[0] for row in await cursor.fetchall()]

    async def set_language(self, user_id: int, lang: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
            await db.commit()

    async def get_pending_orders(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id, user_id, order_id_api FROM orders WHERE status IN ('pending', 'processing')") as cursor:
                return await cursor.fetchall()

    async def update_order_status(self, db_id: int, status: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, db_id))
            await db.commit()

    async def get_profit_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT SUM(profit_kzt) FROM orders WHERE status = 'completed'") as c:
                return (await c.fetchone())[0] or 0

    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def create_user(self, user_id: int, username: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()

    async def update_balance(self, user_id: int, amount: float):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET balance_kzt = balance_kzt + ? WHERE user_id = ?",
                (amount, user_id)
            )
            await db.commit()
