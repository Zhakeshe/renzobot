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
    filename: "./bot_database.db",
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
  const ADMIN_ID = parseInt(process.env.ADMIN_ID || "7874477752");

  app.get("/api/user/:id", async (req, res) => {
    const user = await db.get("SELECT * FROM users WHERE user_id = ?", [req.params.id]);
    const orders = await db.all("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", [req.params.id]);
    
    if (!user) return res.status(404).json({ error: "User not found" });
    
    res.json({
      ...user,
      orders,
      is_admin: parseInt(req.params.id) === ADMIN_ID
    });
  });

  // API: Админ статистикасы
  app.get("/api/admin/stats", async (req, res) => {
    const userId = parseInt(req.headers['x-user-id'] as string || "0");
    if (userId !== ADMIN_ID) return res.status(403).json({ error: "Forbidden" });

    const totalUsers = await db.get("SELECT COUNT(*) as count FROM users");
    const totalOrders = await db.get("SELECT COUNT(*) as count FROM orders");
    const totalSales = await db.get("SELECT SUM(amount_kzt) as sum FROM orders WHERE status = 'completed'");
    const totalProfit = await db.get("SELECT SUM(profit_kzt) as sum FROM orders WHERE status = 'completed'");

    const recentUsers = await db.all("SELECT user_id, username, balance_kzt, created_at FROM users ORDER BY created_at DESC LIMIT 5");
    const recentOrders = await db.all("SELECT id, user_id, product_type, amount_kzt, status, created_at FROM orders ORDER BY created_at DESC LIMIT 5");

    res.json({
      usersCount: totalUsers.count || 0,
      ordersCount: totalOrders.count || 0,
      salesSum: totalSales.sum || 0,
      profitSum: totalProfit.sum || 0,
      recentUsers,
      recentOrders
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

  const API_TOKEN = process.env.API_TOKEN || "";
  const API_BASE_URL = process.env.API_BASE_URL || "";
  const MARGIN = parseFloat(process.env.MARGIN || "1.15");
  const KZT_RATE = parseFloat(process.env.RUB_KZT_RATE || "5.2");

  // API: NFT Collections
  app.get("/api/nft/collections", async (req, res) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/client/rent/nft/collections`, {
        headers: { "Authorization": `Bearer ${API_TOKEN}` }
      });
      const data: any = await response.json();
      res.json(data);
    } catch (err) {
      res.status(500).json({ success: false, error: "Failed to fetch collections" });
    }
  });

  // API: NFT List
  app.get("/api/nft/list", async (req, res) => {
    try {
      const { collection_address, cursor } = req.query;
      const url = new URL(`${API_BASE_URL}/api/v1/client/rent/nft/list`);
      url.searchParams.append("collection_address", collection_address as string);
      if (cursor) url.searchParams.append("cursor", cursor as string);

      const response = await fetch(url.toString(), {
        headers: { "Authorization": `Bearer ${API_TOKEN}` }
      });
      const data: any = await response.json();
      
      if (data.success && data.items) {
        data.items = data.items.map((item: any) => ({
          ...item,
          price_per_day_rub_with_margin: item.price_per_day_rub * MARGIN,
          price_per_day_kzt: item.price_per_day_rub * MARGIN * KZT_RATE
        }));
      }
      
      res.json(data);
    } catch (err) {
      res.status(500).json({ success: false, error: "Failed to fetch NFT list" });
    }
  });

  // API: NFT Rent Order
  app.post("/api/nft/rent", async (req, res) => {
    try {
      const { userId, nft_address, days, amountKzt } = req.body;
      
      // Check balance
      const user = await db.get("SELECT balance_kzt FROM users WHERE user_id = ?", [userId]);
      if (!user || user.balance_kzt < amountKzt) {
        return res.status(400).json({ error: "Insufficient balance" });
      }

      // Place order in third-party API
      const response = await fetch(`${API_BASE_URL}/api/v1/client/orders/rent/nft`, {
        method: "POST",
        headers: { 
          "Authorization": `Bearer ${API_TOKEN}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ nft_address, days })
      });
      const apiData: any = await response.json();

      if (!apiData.success) {
        return res.status(400).json({ error: apiData.error || "API error" });
      }

      // Deduct balance and save order
      await db.run("UPDATE users SET balance_kzt = balance_kzt - ? WHERE user_id = ?", [amountKzt, userId]);
      await db.run(
        "INSERT INTO orders (user_id, product_type, amount_kzt, status, order_id_api) VALUES (?, ?, ?, ?, ?)",
        [userId, 'nft_rent', amountKzt, 'pending', apiData.order.id]
      );

      res.json({ success: true, order: apiData.order });
    } catch (err) {
      res.status(500).json({ error: "Internal server error" });
    }
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
