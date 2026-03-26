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
                    referral_balance REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS promocodes (
                    code TEXT PRIMARY KEY,
                    amount REAL,
                    uses_left INTEGER,
                    is_active INTEGER DEFAULT 1
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS used_promocodes (
                    user_id INTEGER,
                    code TEXT,
                    PRIMARY KEY (user_id, code)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    order_id_api INTEGER,
                    status TEXT,
                    product_type TEXT,
                    product_name TEXT,
                    description TEXT,
                    amount_kzt REAL,
                    profit_kzt REAL,
                    tx_hash TEXT,
                    is_notified INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    subject TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER,
                    sender_id INTEGER,
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS payment_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    method TEXT,
                    receipt_file_id TEXT,
                    comment_code TEXT,
                    status TEXT DEFAULT 'pending',
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

            if version < 2:
                try:
                    await db.execute("ALTER TABLE users ADD COLUMN referral_balance REAL DEFAULT 0.0")
                except: pass
                await db.execute("INSERT OR REPLACE INTO migrations (version) VALUES (2)")

            if version < 3:
                try:
                    await db.execute("ALTER TABLE orders ADD COLUMN product_name TEXT")
                    await db.execute("ALTER TABLE orders ADD COLUMN description TEXT")
                except: pass
                await db.execute("INSERT OR REPLACE INTO migrations (version) VALUES (3)")

            if version < 4:
                try:
                    await db.execute("ALTER TABLE payment_requests ADD COLUMN comment_code TEXT")
                except: pass
                await db.execute("INSERT OR REPLACE INTO migrations (version) VALUES (4)")

            if version < 5:
                try:
                    await db.execute("ALTER TABLE orders ADD COLUMN ton_connected INTEGER DEFAULT 0")
                except: pass
                await db.execute("INSERT OR REPLACE INTO migrations (version) VALUES (5)")

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

    async def create_payment_request(self, user_id: int, amount: float, method: str, receipt_file_id: str = None, comment_code: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO payment_requests (user_id, amount, method, receipt_file_id, comment_code) VALUES (?, ?, ?, ?, ?)",
                (user_id, amount, method, receipt_file_id, comment_code)
            )
            req_id = cursor.lastrowid
            await db.commit()
            return req_id

    async def get_payment_request(self, req_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM payment_requests WHERE id = ?", (req_id,)) as cursor:
                return await cursor.fetchone()

    async def update_payment_request_status(self, req_id: int, status: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE payment_requests SET status = ? WHERE id = ?", (status, req_id))
            await db.commit()

    async def get_top_referrers(self, limit: int = 10):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT referred_by, COUNT(*) as ref_count 
                FROM users 
                WHERE referred_by IS NOT NULL 
                GROUP BY referred_by 
                ORDER BY ref_count DESC 
                LIMIT ?
            """, (limit,)) as cursor:
                return await cursor.fetchall()

    async def get_user_by_id(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def get_today_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Бүгінгі жаңа пайдаланушылар
            async with db.execute("SELECT COUNT(*) FROM users WHERE date(created_at) = date('now')") as c1:
                new_users = (await c1.fetchone())[0]
            # Бүгінгі сауда
            async with db.execute("SELECT SUM(amount_kzt) FROM orders WHERE status = 'completed' AND date(created_at) = date('now')") as c2:
                today_sales = (await c2.fetchone())[0] or 0.0
            # Бүгінгі пайда
            async with db.execute("SELECT SUM(profit_kzt) FROM orders WHERE status = 'completed' AND date(created_at) = date('now')") as c3:
                today_profit = (await c3.fetchone())[0] or 0.0
            return new_users, today_sales, today_profit

    async def get_all_users_ids(self):
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

    async def update_order_ton_connected(self, db_id: int, connected: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE orders SET ton_connected = ? WHERE id = ?", (1 if connected else 0, db_id))
            await db.commit()

    async def update_order_ton_connected_by_api_id(self, api_id: int, connected: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE orders SET ton_connected = ? WHERE order_id_api = ?", (1 if connected else 0, api_id))
            await db.commit()

    async def get_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as c1:
                users = (await c1.fetchone())[0]
            async with db.execute("SELECT SUM(amount_kzt) FROM orders WHERE status = 'completed'") as c2:
                sales = (await c2.fetchone())[0] or 0.0
            return users, sales

    async def get_global_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM orders WHERE product_type = 'stars' AND status = 'completed'") as c1:
                stars = (await c1.fetchone())[0] or 0
            async with db.execute("SELECT COUNT(*) FROM orders WHERE product_type = 'gifts' AND status = 'completed'") as c2:
                gifts = (await c2.fetchone())[0] or 0
            async with db.execute("SELECT COUNT(*) FROM orders WHERE product_type = 'usernames' AND status = 'completed'") as c3:
                usernames = (await c3.fetchone())[0] or 0
            return stars, gifts, usernames

    async def create_order(self, user_id: int, order_id_api: int, product_type: str, product_name: str, description: str, amount_kzt: float, profit_kzt: float, status: str = 'pending'):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO orders (user_id, order_id_api, product_type, product_name, description, amount_kzt, profit_kzt, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, order_id_api, product_type, product_name, description, amount_kzt, profit_kzt, status)
            )
            order_id = cursor.lastrowid
            await db.commit()
            return order_id

    async def get_user_orders(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,)) as cursor:
                return await cursor.fetchall()

    async def get_user_payments(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM payment_requests WHERE user_id = ? ORDER BY created_at DESC", (user_id,)) as cursor:
                return await cursor.fetchall()

    async def get_order(self, order_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cursor:
                return await cursor.fetchone()

    async def get_payment_request(self, req_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM payment_requests WHERE id = ?", (req_id,)) as cursor:
                return await cursor.fetchone()

    async def get_profit_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT SUM(profit_kzt) FROM orders WHERE status = 'completed'") as c:
                return (await c.fetchone())[0] or 0

    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def create_user(self, user_id: int, username: str, referred_by: int = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, referred_by) VALUES (?, ?, ?)",
                (user_id, username, referred_by)
            )
            await db.commit()

    async def update_balance(self, user_id: int, amount: float):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET balance_kzt = balance_kzt + ? WHERE user_id = ?",
                (amount, user_id)
            )
            await db.commit()

    async def get_referral_stats(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*), SUM(referral_balance) FROM users WHERE referred_by = ?", (user_id,)) as c:
                row = await c.fetchone()
                return row[0] or 0, row[1] or 0.0

    async def check_promocode(self, code: str, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT amount, uses_left FROM promocodes WHERE code = ? AND is_active = 1", (code,)) as c:
                promo = await c.fetchone()
                if not promo:
                    return None, "invalid"
                amount, uses_left = promo
                if uses_left <= 0:
                    return None, "expired"
            async with db.execute("SELECT 1 FROM used_promocodes WHERE user_id = ? AND code = ?", (user_id, code)) as c:
                if await c.fetchone():
                    return None, "already_used"
                return amount, "ok"

    async def use_promocode(self, user_id: int, code: str, amount: float):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET balance_kzt = balance_kzt + ? WHERE user_id = ?", (amount, user_id))
            await db.execute("INSERT INTO used_promocodes (user_id, code) VALUES (?, ?)", (user_id, code))
            await db.execute("UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?", (code,))
            await db.commit()

    async def add_referral_earning(self, referrer_id: int, amount: float):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET balance_kzt = balance_kzt + ?, referral_balance = referral_balance + ? WHERE user_id = ?",
                (amount, amount, referrer_id)
            )
            await db.commit()

    async def ban_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
            await db.commit()

    async def unban_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET is_blocked = 0 WHERE user_id = ?", (user_id,))
            await db.commit()

    async def set_user_balance(self, user_id: int, balance: float):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET balance_kzt = ? WHERE user_id = ?", (balance, user_id))
            await db.commit()

    async def get_users_paged(self, limit: int, offset: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM users LIMIT ? OFFSET ?", (limit, offset)) as cursor:
                return await cursor.fetchall()

    async def create_ticket(self, user_id: int, subject: str):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO tickets (user_id, subject) VALUES (?, ?)",
                (user_id, subject)
            )
            ticket_id = cursor.lastrowid
            await db.commit()
            return ticket_id

    async def add_ticket_message(self, ticket_id: int, sender_id: int, text: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO ticket_messages (ticket_id, sender_id, text) VALUES (?, ?, ?)",
                (ticket_id, sender_id, text)
            )
            await db.commit()

    async def get_user_tickets(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC", (user_id,)) as cursor:
                return await cursor.fetchall()

    async def get_all_tickets(self, status: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            if status:
                async with db.execute("SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC", (status,)) as cursor:
                    return await cursor.fetchall()
            else:
                async with db.execute("SELECT * FROM tickets ORDER BY created_at DESC") as cursor:
                    return await cursor.fetchall()

    async def get_ticket(self, ticket_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)) as cursor:
                return await cursor.fetchone()

    async def get_ticket_messages(self, ticket_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY created_at ASC", (ticket_id,)) as cursor:
                return await cursor.fetchall()

    async def update_ticket_status(self, ticket_id: int, status: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
            await db.commit()

    async def update_order_ton_status(self, order_id_api: str, ton_connected: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE orders SET ton_connected = ? WHERE order_id_api = ?", (1 if ton_connected else 0, order_id_api))
            await db.commit()
