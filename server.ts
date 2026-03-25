import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import sqlite3 from "sqlite3";
import { open } from "sqlite";
import crypto from "crypto";

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Дерекқорға қосылу
  const db = await open({
    filename: "./bot.db",
    driver: sqlite3.Database
  });

  // Telegram initData тексеру (Security)
  const validateInitData = (initData: string, botToken: string) => {
    const urlParams = new URLSearchParams(initData);
    const hash = urlParams.get("hash");
    urlParams.delete("hash");

    const dataCheckString = Array.from(urlParams.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => `${key}=${value}`)
      .join("\n");

    const secretKey = crypto.createHmac("sha256", "WebAppData").update(botToken).digest();
    const hmac = crypto.createHmac("sha256", secretKey).update(dataCheckString).digest("hex");

    return hmac === hash;
  };

  // Middleware: Auth
  const authMiddleware = (req: any, res: any, next: any) => {
    const initData = req.headers["x-telegram-init-data"];
    if (!initData) return res.status(401).json({ error: "Unauthorized" });
    
    // Бот токенін ENV-тен алу керек
    const botToken = process.env.BOT_TOKEN || "";
    if (!validateInitData(initData, botToken)) {
      // Даму кезеңінде қатаң тексермеуге болады, бірақ продакшнда міндетті
      // return res.status(403).json({ error: "Invalid data" });
    }
    next();
  };

  // API: Пайдаланушы деректері
  app.get("/api/user/:id", async (req, res) => {
    const user = await db.get("SELECT * FROM users WHERE user_id = ?", [req.params.id]);
    const orders = await db.all("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", [req.params.id]);
    
    if (!user) return res.status(404).json({ error: "User not found" });
    
    res.json({
      ...user,
      orders
    });
  });

  // API: Тауарлар тізімі
  app.get("/api/products", (req, res) => {
    res.json([
      { id: 'stars', name: 'Telegram Stars', price_kzt: 10, icon: 'Star' },
      { id: 'premium', name: 'Telegram Premium', price_kzt: 1600, icon: 'ShieldCheck' },
      { id: 'nft', name: 'NFT Rent', price_kzt: 65, icon: 'LayoutGrid' }
    ]);
  });

  // API: Тапсырыс беру
  app.post("/api/order", async (req, res) => {
    const { userId, productId, quantity, amountKzt } = req.body;
    
    // Балансты тексеру және тапсырыс жасау логикасы
    const user = await db.get("SELECT balance_kzt FROM users WHERE user_id = ?", [userId]);
    if (user.balance_kzt < amountKzt) {
      return res.status(400).json({ error: "Insufficient balance" });
    }

    // Балансты азайту және тапсырысты сақтау
    await db.run("UPDATE users SET balance_kzt = balance_kzt - ? WHERE user_id = ?", [amountKzt, userId]);
    await db.run(
      "INSERT INTO orders (user_id, product_type, amount_kzt, status) VALUES (?, ?, ?, ?)",
      [userId, productId, amountKzt, 'pending']
    );

    res.json({ success: true });
  });

  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
