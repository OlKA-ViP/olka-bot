import asyncio
import aiosqlite
import time
import os
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)

BOT_TOKEN = "8707730826:AAExJ7ZSQe9YFy8Y0O2eG3uPCAwVa_vG6Qc"
ADMIN_ID = 1932161126
SPONSOR_CHANNEL = "@olka_ad"
CONVERSION_RATE = 100
MIN_WITHDRAW_GRAM = 5
REFERRAL_REWARD = 100.0

WEBAPP_URL = "https://olka-bot-service.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

withdraw_state = {}

# واجهة الويب المتكاملة مع السيرفر وقاعدة البيانات
MINI_APP_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>OLKA VIP EMPIRE</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --bg-dark: #07090e;
      --gold: #f59e0b;
      --gold-light: #fef08a;
      --gold-glow: rgba(245, 158, 11, 0.45);
      --card-surface: rgba(255, 255, 255, 0.05);
      --card-border: rgba(255, 255, 255, 0.1);
      --accent-blue: #38bdf8;
      --accent-green: #10b981;
    }
    * {
      box-sizing: border-box;
      user-select: none;
      -webkit-user-select: none;
      touch-action: manipulation;
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    body {
      background: radial-gradient(circle at 50% 5%, #1e1b4b 0%, var(--bg-dark) 85%);
      color: #ffffff;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      overflow: hidden;
    }
    .main-view {
      flex: 1;
      overflow-y: auto;
      padding: 14px 16px 85px 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
    }
    .page {
      display: none;
      width: 100%;
      flex-direction: column;
      align-items: center;
      animation: fadeIn 0.2s ease-out forwards;
    }
    .page.active {
      display: flex;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .top-bar {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-surface);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(16px);
      padding: 10px 14px;
      border-radius: 18px;
      margin-bottom: 12px;
    }
    .user-profile {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .avatar-icon {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: linear-gradient(135deg, #6366f1, #d946ef);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 15px;
      box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
    }
    .username { font-size: 14px; font-weight: 700; }
    .user-rank { font-size: 11px; color: var(--gold-light); font-weight: 600; }
    .sync-status {
      font-size: 11px;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      padding: 4px 10px;
      border-radius: 12px;
      border: 1px solid rgba(52, 211, 153, 0.3);
      font-weight: 600;
    }
    .score-container { text-align: center; margin: 8px 0; }
    .score-title { font-size: 12px; color: #94a3b8; font-weight: 700; }
    .score-value {
      font-size: 44px;
      font-weight: 900;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 4px;
      text-shadow: 0 0 25px var(--gold-glow);
    }
    .coin-wrapper {
      position: relative;
      margin: 20px 0;
    }
    .tap-coin {
      width: 230px;
      height: 230px;
      border-radius: 50%;
      background: radial-gradient(circle at 35% 30%, #fde047 0%, #d97706 60%, #78350f 100%);
      border: 8px solid #fef08a;
      box-shadow: 0 10px 30px rgba(0,0,0,0.8), 0 0 50px var(--gold-glow);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      transition: transform 0.08s;
      position: relative;
    }
    .tap-coin:active { transform: scale(0.93); }
    .coin-logo { font-size: 46px; font-weight: 900; letter-spacing: 3px; }
    .coin-sub { font-size: 12px; font-weight: 800; letter-spacing: 4px; }
    .float-num {
      position: absolute;
      color: #fff;
      font-size: 30px;
      font-weight: 900;
      pointer-events: none;
      animation: floatUp 0.7s ease-out forwards;
      text-shadow: 0 0 15px var(--gold);
      z-index: 100;
    }
    @keyframes floatUp {
      0% { opacity: 1; transform: translateY(0); }
      100% { opacity: 0; transform: translateY(-90px) scale(1.25); }
    }
    .energy-card {
      width: 100%;
      background: var(--card-surface);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 12px 14px;
      backdrop-filter: blur(12px);
    }
    .energy-meta {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 6px;
    }
    .bar-outer {
      width: 100%;
      height: 10px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 10px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      width: 100%;
      background: linear-gradient(90deg, #0284c7, #38bdf8);
      border-radius: 10px;
      transition: width 0.15s ease-out;
    }
    .section-title {
      font-size: 16px;
      font-weight: 800;
      margin: 10px 0 12px 0;
      width: 100%;
      text-align: right;
      color: var(--gold-light);
    }
    .card-item {
      width: 100%;
      background: var(--card-surface);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
      backdrop-filter: blur(10px);
    }
    .card-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .card-icon {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
    }
    .card-title { font-size: 14px; font-weight: 700; }
    .card-subtitle { font-size: 12px; color: #94a3b8; }
    .btn-action {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #000;
      font-weight: 800;
      padding: 8px 14px;
      border-radius: 10px;
      border: none;
      cursor: pointer;
      font-size: 12px;
    }
    .btn-action:active { transform: scale(0.96); }
    .input-box {
      width: 100%;
      padding: 12px;
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      color: #fff;
      font-size: 14px;
      margin: 8px 0 12px 0;
      outline: none;
    }
    .bottom-nav {
      position: fixed;
      bottom: 12px;
      left: 12px;
      right: 12px;
      height: 64px;
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      display: flex;
      justify-content: space-around;
      align-items: center;
      backdrop-filter: blur(25px);
      z-index: 999;
    }
    .nav-btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      color: #64748b;
      cursor: pointer;
      flex: 1;
    }
    .nav-btn.active { color: var(--gold-light); transform: translateY(-2px); }
    .nav-btn i { font-size: 18px; }
    .nav-btn span { font-size: 11px; font-weight: 700; }
  </style>
</head>
<body>

  <div class="main-view">
    <div class="top-bar">
      <div class="user-profile">
        <div class="avatar-icon" id="user-avatar">O</div>
        <div class="user-text">
          <span class="username" id="user-name">VIP Miner</span>
          <span class="user-rank" id="user-rank">🥉 رتبة: برونزي</span>
        </div>
      </div>
      <div class="sync-status" id="sync-badge">🟢 متصل ومحفوظ</div>
    </div>

    <!-- تبويب التعدين -->
    <div class="page active" id="page-mine">
      <div class="score-container">
        <div class="score-title">رصيد التعدين المباشر (OLK)</div>
        <div class="score-value">
          <span>🪙</span>
          <span id="score-display">0.00</span>
        </div>
      </div>

      <div class="coin-wrapper">
        <div class="tap-coin" id="coin-btn">
          <div class="coin-logo">OLK</div>
          <div class="coin-sub">VIP MINER</div>
        </div>
      </div>

      <div class="energy-card">
        <div class="energy-meta">
          <span style="color:#94a3b8;"><i class="fa-solid fa-bolt" style="color:var(--accent-blue);"></i> الطاقة المتبقية</span>
          <span style="color:var(--accent-blue);" id="energy-counter">1000 / 1000</span>
        </div>
        <div class="bar-outer">
          <div class="bar-fill" id="energy-progress"></div>
        </div>
      </div>
    </div>

    <!-- تبويب المحفظة والسحب المباشر -->
    <div class="page" id="page-wallet">
      <div class="section-title"><i class="fa-solid fa-wallet"></i> المحفظة والسحب السريع</div>

      <div class="card-item" style="flex-direction:column; align-items:stretch;">
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
          <span>رصيد Gram القابل للسحب:</span>
          <strong style="color:#34d399;" id="gram-wallet-val">0.0000 Gram</strong>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
          <span>سعر الصرف الحالي:</span>
          <span style="color:#94a3b8;">100 OLK = 1 Gram</span>
        </div>
        <button class="btn-action" style="margin-bottom:12px;" onclick="convertOlkToGram()">تحويل رصيد OLK إلى Gram 🔄</button>

        <hr style="border:0; border-top:1px solid var(--card-border); margin:8px 0;">

        <label style="font-size:12px; color:#cbd5e1; margin-top:8px;">عنوان محفظتك (TON / Gram Address):</label>
        <input type="text" id="wallet-address-input" class="input-box" placeholder="UQ... أو EQ...">
        <button class="btn-action" style="background:#10b981; color:#fff;" onclick="submitWebWithdraw()">تأكيد وإرسال طلب السحب 💳</button>
      </div>
    </div>

    <!-- تبويب التطويرات -->
    <div class="page" id="page-boost">
      <div class="section-title"><i class="fa-solid fa-rocket"></i> تطويرات التعدين</div>

      <div class="card-item">
        <div class="card-info">
          <div class="card-icon" style="background:rgba(245, 158, 11, 0.15); color:var(--gold);"><i class="fa-solid fa-hand-pointer"></i></div>
          <div>
            <div class="card-title">Multi-Tap (قوة النقر)</div>
            <div class="card-subtitle">احصل على +1 لكل ضغطة</div>
          </div>
        </div>
        <button class="btn-action" onclick="upgradeMultiTap()">تطوير (100 OLK)</button>
      </div>

      <div class="card-item">
        <div class="card-info">
          <div class="card-icon" style="background:rgba(56, 189, 248, 0.15); color:var(--accent-blue);"><i class="fa-solid fa-battery-full"></i></div>
          <div>
            <div class="card-title">توسيع خزان الطاقة</div>
            <div class="card-subtitle">+500 حد أقصى</div>
          </div>
        </div>
        <button class="btn-action" onclick="upgradeEnergyMax()">شراء (200 OLK)</button>
      </div>
    </div>

    <!-- تبويب الإحالة والأصدقاء -->
    <div class="page" id="page-frens">
      <div class="section-title"><i class="fa-solid fa-user-group"></i> نظام الإحالة المتكامل</div>

      <div class="card-item" style="flex-direction:column; align-items:stretch; gap:10px;">
        <div style="font-size:13px; color:#cbd5e1;">شارك رابطك الخاص واربح <strong>100 OLK</strong> تضاف لحسابك تلقائياً عند توثيق صديقك!</div>
        <button class="btn-action" style="padding:12px;" onclick="copyInviteLink()"><i class="fa-solid fa-copy"></i> نسخ رابط الدعوة الخاص بي</button>
      </div>
    </div>
  </div>

  <div class="bottom-nav">
    <div class="nav-btn active" onclick="switchTab('mine', this)">
      <i class="fa-solid fa-pickaxe"></i>
      <span>تعدين</span>
    </div>
    <div class="nav-btn" onclick="switchTab('wallet', this)">
      <i class="fa-solid fa-wallet"></i>
      <span>المحفظة</span>
    </div>
    <div class="nav-btn" onclick="switchTab('boost', this)">
      <i class="fa-solid fa-rocket"></i>
      <span>تطويرات</span>
    </div>
    <div class="nav-btn" onclick="switchTab('frens', this)">
      <i class="fa-solid fa-user-group"></i>
      <span>أصدقاء</span>
    </div>
  </div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) { tg.ready(); tg.expand(); }

    const tgUser = tg?.initDataUnsafe?.user;
    const userId = tgUser?.id || 1932161126;

    const userNameEl = document.getElementById("user-name");
    const userAvatarEl = document.getElementById("user-avatar");
    const scoreEl = document.getElementById("score-display");
    const gramWalletEl = document.getElementById("gram-wallet-val");
    const energyCounterEl = document.getElementById("energy-counter");
    const energyProgressEl = document.getElementById("energy-progress");
    const coinBtn = document.getElementById("coin-btn");
    const syncBadge = document.getElementById("sync-badge");

    if (tgUser?.first_name) {
      userNameEl.innerText = tgUser.first_name;
      userAvatarEl.innerText = tgUser.first_name.charAt(0).toUpperCase();
    }

    let olkBalance = 0;
    let gramBalance = 0;
    let unsavedClicks = 0;
    let maxEnergy = 1000;
    let energy = 1000;
    let clickPower = 1;

    // جلب البيانات الأصلية من سيرفر البوت (قاعدة البيانات)
    async function loadUserData() {
      try {
        const res = await fetch(`/api/get_user?user_id=${userId}`);
        const data = await res.json();
        if (data.ok) {
          olkBalance = data.olk_balance;
          gramBalance = data.gram_balance;
          renderUI();
        }
      } catch (err) {
        console.log("Error loading DB data:", err);
      }
    }

    function renderUI() {
      scoreEl.innerText = olkBalance.toFixed(2);
      gramWalletEl.innerText = gramBalance.toFixed(4) + " Gram";
      energyCounterEl.innerText = `${energy} / ${maxEnergy}`;
      energyProgressEl.style.width = ((energy / maxEnergy) * 100) + "%";
    }

    // إرسال ومزامنة النقرات مع قاعدة بيانات البوت
    async function syncBalance() {
      if (unsavedClicks === 0) return;
      syncBadge.innerText = "⏳ جاري المزامنة...";
      try {
        const res = await fetch("/api/sync", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, added_olk: unsavedClicks })
        });
        const d = await res.json();
        if (d.ok) {
          unsavedClicks = 0;
          syncBadge.innerText = "🟢 متصل ومحفوظ";
        }
      } catch (e) {
        syncBadge.innerText = "⚠️ فشل الحفظ";
      }
    }

    setInterval(syncBalance, 3000);

    // النقر وزيادة العداد
    coinBtn.addEventListener("pointerdown", (event) => {
      if (energy < clickPower) {
        if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("error");
        return;
      }

      energy -= clickPower;
      olkBalance += clickPower;
      unsavedClicks += clickPower;
      renderUI();

      if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred("medium");

      const rect = coinBtn.getBoundingClientRect();
      const floatEl = document.createElement("div");
      floatEl.className = "float-num";
      floatEl.innerText = "+" + clickPower;
      floatEl.style.left = (event.clientX - rect.left - 15) + "px";
      floatEl.style.top = (event.clientY - rect.top - 25) + "px";
      coinBtn.parentElement.appendChild(floatEl);
      setTimeout(() => floatEl.remove(), 700);
    });

    setInterval(() => {
      if (energy < maxEnergy) {
        energy = Math.min(maxEnergy, energy + 4);
        renderUI();
      }
    }, 1000);

    function switchTab(tabId, el) {
      document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
      document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
      document.getElementById("page-" + tabId).classList.add("active");
      el.classList.add("active");
    }

    async function convertOlkToGram() {
      await syncBalance();
      if (olkBalance < 100) {
        alert("⚠️ تحتاج إلى 100 OLK على الأقل للتحويل.");
        return;
      }
      const res = await fetch("/api/convert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId })
      });
      const data = await res.json();
      if (data.ok) {
        olkBalance = data.olk_balance;
        gramBalance = data.gram_balance;
        renderUI();
        alert("✅ تم تحويل الرصيد بنجاح!");
      } else {
        alert(data.msg);
      }
    }

    async function submitWebWithdraw() {
      const address = document.getElementById("wallet-address-input").value.trim();
      if (!address) {
        alert("❌ يرجى إدخال عنوان محفظتك!");
        return;
      }
      const res = await fetch("/api/withdraw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, address: address })
      });
      const data = await res.json();
      if (data.ok) {
        gramBalance = 0;
        renderUI();
        document.getElementById("wallet-address-input").value = "";
        alert("✅ تم إرسال طلب السحب للمسؤول بنجاح!");
      } else {
        alert(data.msg);
      }
    }

    function upgradeMultiTap() {
      if (olkBalance >= 100) {
        olkBalance -= 100;
        unsavedClicks -= 100;
        clickPower += 1;
        renderUI();
        syncBalance();
        alert("🎉 تم تطوير قوة النقر!");
      } else {
        alert("⚠️ لا تملك رصيداً كافياً");
      }
    }

    function upgradeEnergyMax() {
      if (olkBalance >= 200) {
        olkBalance -= 200;
        unsavedClicks -= 200;
        maxEnergy += 500;
        energy = maxEnergy;
        renderUI();
        syncBalance();
        alert("⚡ تم توسيع خزان الطاقة!");
      } else {
        alert("⚠️ لا تملك رصيداً كافياً");
      }
    }

    function copyInviteLink() {
      const botUser = "OlkaVip_bot";
      const inviteUrl = `https://t.me/${botUser}?start=${userId}`;
      navigator.clipboard.writeText(inviteUrl);
      alert("✅ تم نسخ رابط الإحالة الخاص بك بنجاح!");
    }

    loadUserData();
  </script>
</body>
</html>
"""

# تجهيز قاعدة البيانات
async def init_db():
    async with aiosqlite.connect("olka_vip.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            phone_number TEXT,
            olk_balance REAL DEFAULT 0.0,
            gram_balance REAL DEFAULT 0.0,
            last_claim INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT NULL,
            ref_reward_claimed INTEGER DEFAULT 0
        )
        """)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN ref_reward_claimed INTEGER DEFAULT 0")
        except Exception:
            pass

        await db.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount_gram REAL,
            wallet_address TEXT,
            status TEXT DEFAULT 'PENDING'
        )
        """)
        await db.commit()

# مسارات واجهة برمجة التطبيقات (API) لربط الويب بقاعدة بيانات البوت
async def api_get_user(request):
    try:
        user_id = int(request.query.get("user_id", 0))
        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT olk_balance, gram_balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if row:
                    return web.json_response({"ok": True, "olk_balance": row[0], "gram_balance": row[1]})
                else:
                    await db.execute("INSERT OR IGNORE INTO users (user_id, olk_balance) VALUES (?, 0.0)", (user_id,))
                    await db.commit()
                    return web.json_response({"ok": True, "olk_balance": 0.0, "gram_balance": 0.0})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_sync(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        added_olk = float(data.get("added_olk", 0))
        async with aiosqlite.connect("olka_vip.db") as db:
            await db.execute("UPDATE users SET olk_balance = olk_balance + ? WHERE user_id = ?", (added_olk, user_id))
            await db.commit()
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_convert(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT olk_balance, gram_balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if not row or row[0] < CONVERSION_RATE:
                    return web.json_response({"ok": False, "msg": "رصيد OLK غير كافٍ للتحويل"})
                olk = row[0]
                gram_add = olk / CONVERSION_RATE
                new_gram = row[1] + gram_add
                await db.execute("UPDATE users SET olk_balance = 0.0, gram_balance = ? WHERE user_id = ?", (new_gram, user_id))
                await db.commit()
                return web.json_response({"ok": True, "olk_balance": 0.0, "gram_balance": new_gram})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_withdraw(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        address = str(data.get("address", "")).strip()

        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT gram_balance, phone_number FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if not row or row[0] < MIN_WITHDRAW_GRAM:
                    return web.json_response({"ok": False, "msg": f"الحد الأدنى للسحب هو {MIN_WITHDRAW_GRAM} Gram"})

                gram_bal, phone = row[0], row[1] or "غير موثق بعد"
                await db.execute("INSERT INTO withdrawals (user_id, amount_gram, wallet_address) VALUES (?, ?, ?)",
                                 (user_id, gram_bal, address))
                await db.execute("UPDATE users SET gram_balance = 0.0 WHERE user_id = ?", (user_id,))
                await db.commit()

        # إشعار المدير
        admin_notification = (
            f"🚨 **طلب سحب جديد من Mini App**\n\n"
            f"👤 المعرف: `{user_id}`\n"
            f"📱 الهاتف: `{phone}`\n"
            f"💰 المبلغ: `{gram_bal:.4f} Gram`\n"
            f"📫 المحفظة:\n`{address}`"
        )
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=admin_notification, parse_mode="Markdown")
        except Exception:
            pass

        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

def get_contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⚡ توثيق الحساب والمطالبة بـ 10 OLK 🚀", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main_dashboard_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎮 فتح لعبة ومحفظة الويب (Mini App) 🚀", web_app=WebAppInfo(url=WEBAPP_URL))
        ],
        [
            InlineKeyboardButton(text="⚡ تعدين يومي (+20)", callback_data="claim"),
            InlineKeyboardButton(text="🔄 صرافة Gram", callback_data="convert")
        ],
        [
            InlineKeyboardButton(text="💳 المحفظة والسحب", callback_data="balance"),
            InlineKeyboardButton(text="👥 دعوة الأصدقاء", callback_data="referral")
        ],
        [
            InlineKeyboardButton(text="📢 قناة OLKA AD الرسمية", url="https://t.me/olka_ad")
        ]
    ])

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except Exception:
        return True

@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    user_id = message.from_user.id
    ref_param = command.args

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT phone_number, olk_balance, gram_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

        # تسجيل الإحالة للمستخدم الجديد
        if not user and ref_param:
            try:
                clean_ref = ref_param.replace("ref_", "")
                referrer_id = int(clean_ref)
                if referrer_id != user_id:
                    await db.execute("""
                        INSERT INTO users (user_id, referred_by) VALUES (?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET referred_by = excluded.referred_by
                    """, (user_id, referrer_id))
                    await db.commit()
            except ValueError:
                pass
        elif not user:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()

    if not user or not user[0]:
        welcome_banner = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌟 **مرحباً بك في إمبراطورية OLKA VIP** 🌟\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⛏️ انضم لأقوى نظام تعدين وسحب Gram على تليجرام.\n\n"
            "🎁 **هدية التوثيق:** `+10 OLK`\n"
            "👇 **اضغط على الزر بالأسفل لتوثيق حسابك برقم الهاتف:**"
        )
        await message.answer(welcome_banner, parse_mode="Markdown", reply_markup=get_contact_keyboard())
        return

    if not await check_subscription(user_id):
        sub_banner = (
            "⚠️ **خطوة أخيرة لتفعيل حسابك!**\n\n"
            f"يرجى الانضمام إلى قناتنا الرسمية:\n"
            f"📢 **{SPONSOR_CHANNEL}**"
        )
        await message.answer(
            sub_banner,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 انضم إلى القناة الآن", url="https://t.me/olka_ad")],
                [InlineKeyboardButton(text="✅ تحقق من انضمامي", callback_data="verify_sub")]
            ])
        )
        return

    dash_text = (
        f"👑 **لوحة تحكم OLKA VIP:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 المعرّف: `{user_id}`\n"
        f"💰 رصيد OLK: `{user[1]:.2f} OLK`\n"
        f"💳 رصيد Gram: `{user[2]:.4f} Gram`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 اضغط على زر اللعبة بالأسفل لفتح اللعبة والمحفظة السحابية المتزامنة!"
    )
    await message.answer(dash_text, parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

@dp.message(F.contact)
async def contact_handler(message: Message):
    contact = message.contact
    user_id = message.from_user.id

    if contact.user_id != user_id:
        await message.answer("❌ يجب إرسال رقم هاتفك الخاص بك فقط!")
        return

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE phone_number = ?", (contact.phone_number,)) as cursor:
            existing = await cursor.fetchone()
            if existing and existing[0] != user_id:
                await message.answer("⛔ هذا الرقم مستخدم مسبقاً في حساب آخر!")
                return

        await db.execute("""
            INSERT INTO users (user_id, phone_number, olk_balance) VALUES (?, ?, 10.0)
            ON CONFLICT(user_id) DO UPDATE SET phone_number = excluded.phone_number, olk_balance = olk_balance + 10.0
        """, (user_id, contact.phone_number))
        await db.commit()

        # مكافأة المُحيل فوراً بعد التوثيق
        async with db.execute("SELECT referred_by, ref_reward_claimed FROM users WHERE user_id = ?", (user_id,)) as cursor:
            ref_row = await cursor.fetchone()

        if ref_row and ref_row[0] and ref_row[1] == 0:
            referrer_id = ref_row[0]
            await db.execute("UPDATE users SET olk_balance = olk_balance + ? WHERE user_id = ?", (REFERRAL_REWARD, referrer_id))
            await db.execute("UPDATE users SET ref_reward_claimed = 1 WHERE user_id = ?", (user_id,))
            await db.commit()

            try:
                invited_name = message.from_user.first_name or "مستخدم جديد"
                await bot.send_message(
                    chat_id=referrer_id,
                    text=(
                        f"🎉 **إحالة ناجحة جديدة!**\n\n"
                        f"قام صديقك ({invited_name}) بتوثيق حسابه.\n"
                        f"💰 تمت إضافة **+{REFERRAL_REWARD:.0f} OLK** إلى رصيدك فوراً في البوت والويب!"
                    ),
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    await message.answer("✅ **تم توثيق الحساب بنجاح وإضافة مكافأة +10 OLK!**", parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

@dp.callback_query(F.data == "verify_sub")
async def verify_sub_handler(callback: CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("✅ **تم التحقق بنجاح!**", reply_markup=main_dashboard_keyboard(callback.from_user.id))
    else:
        await callback.answer("❌ لم تنضم للقناة بعد!", show_alert=True)

@dp.callback_query(F.data == "claim")
async def claim_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    current_time = int(time.time())
    cooldown = 86400

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT last_claim FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            last_claim = row[0] if row else 0

        if current_time - last_claim < cooldown:
            rem = cooldown - (current_time - last_claim)
            hours = rem // 3600
            mins = (rem % 3600) // 60
            await callback.answer(f"⏳ يمكنك التعدين مجدداً بعد: {hours} ساعة و {mins} دقيقة.", show_alert=True)
            return

        await db.execute("UPDATE users SET olk_balance = olk_balance + 20.0, last_claim = ? WHERE user_id = ?", (current_time, user_id))
        await db.commit()

    await callback.answer("✅ استلمت +20 OLK بنجاح!", show_alert=True)
    await callback.message.edit_text("🎉 **تم استلام التعدين اليومي بنجاح (+20 OLK)!**", parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

@dp.callback_query(F.data == "balance")
async def balance_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT olk_balance, gram_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            olk, gram = row if row else (0.0, 0.0)

    text = (
        "💼 **المحفظة الاستثمارية (OLKA VIP):**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 **رصيد OLK:** `{olk:.2f} OLK`\n"
        f"💎 **رصيد Gram:** `{gram:.4f} Gram`\n\n"
        f"💡 سعر الصرف: `{CONVERSION_RATE} OLK = 1 Gram`\n"
        f"💳 الحد الأدنى للسحب: `{MIN_WITHDRAW_GRAM} Gram`\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 تحويل إلى Gram", callback_data="convert"),
            InlineKeyboardButton(text="💳 سحب Gram", callback_data="withdraw")
        ],
        [InlineKeyboardButton(text="🔙 العودة للرئيسية", callback_data="back_home")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=buttons)

@dp.callback_query(F.data == "referral")
async def referral_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE referred_by = ? AND phone_number IS NOT NULL", (user_id,)) as cursor:
            row = await cursor.fetchone()
            ref_count = row[0] if row else 0

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    text = (
        "👥 **نظام دعوة الأصدقاء (الإحالات المباشرة):**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤝 أصدقاؤك الموثقون: `{ref_count}`\n"
        f"🎁 المكافأة: `+{REFERRAL_REWARD:.0f} OLK` لكل صديق يوثق رقمه\n\n"
        f"🔗 الرابط الخاص بك:\n`{ref_link}`"
    )
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 مشاركة الرابط", url=f"https://t.me/share/url?url={ref_link}&text=انضم%20الآن%20إلى%20مشروع%20OLKA%20VIP!")],
        [InlineKeyboardButton(text="🔙 العودة للرئيسية", callback_data="back_home")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=buttons)

@dp.callback_query(F.data == "convert")
async def convert_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT olk_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            olk = row[0] if row else 0.0

        if olk < CONVERSION_RATE:
            await callback.answer(f"⚠️ تحتاج إلى {CONVERSION_RATE} OLK على الأقل للتحويل!", show_alert=True)
            return

        gram_added = olk / CONVERSION_RATE
        await db.execute("UPDATE users SET olk_balance = 0.0, gram_balance = gram_balance + ? WHERE user_id = ?", (gram_added, user_id))
        await db.commit()

    await callback.answer(f"✅ تم تحويل {olk:.2f} OLK بنجاح!", show_alert=True)
    await balance_handler(callback)

@dp.callback_query(F.data == "withdraw")
async def withdraw_start(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT gram_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            gram = row[0] if row else 0.0

    if gram < MIN_WITHDRAW_GRAM:
        await callback.answer(f"⚠️ رصيدك أقل من الحد الأدنى للسحب ({MIN_WITHDRAW_GRAM} Gram).", show_alert=True)
        return

    withdraw_state[user_id] = True
    await callback.message.answer(f"💳 الرصيد المتاح: `{gram:.4f} Gram`\n\n📝 أرسل الآن عنوان محفظتك (TON / Gram Address):", parse_mode="Markdown")
    await callback.answer()

@dp.message(F.text)
async def process_address(message: Message):
    user_id = message.from_user.id
    if user_id not in withdraw_state:
        return

    wallet_address = message.text.strip()
    del withdraw_state[user_id]

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT gram_balance, phone_number FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            gram_balance, phone = row if row else (0.0, "غير معروف")

        if gram_balance < MIN_WITHDRAW_GRAM:
            await message.answer("❌ الرصيد غير كافٍ لإتمام السحب.")
            return

        await db.execute("INSERT INTO withdrawals (user_id, amount_gram, wallet_address) VALUES (?, ?, ?)",
                         (user_id, gram_balance, wallet_address))
        await db.execute("UPDATE users SET gram_balance = 0.0 WHERE user_id = ?", (user_id,))
        await db.commit()

    await message.answer(f"✅ تم تسجيل طلب السحب بنجاح بمبلغ `{gram_balance:.4f} Gram`!", parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 **طلب سحب من البوت**\n👤 المعرف: `{user_id}`\n📱 الهاتف: `{phone}`\n💰 المبلغ: `{gram_balance:.4f} Gram`\n📫 المحفظة:\n`{wallet_address}`",
            parse_mode="Markdown"
        )
    except Exception:
        pass

@dp.callback_query(F.data == "back_home")
async def back_home_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT phone_number, olk_balance, gram_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

    dash_text = (
        f"👑 **لوحة تحكم OLKA VIP:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 المعرّف: `{user_id}`\n"
        f"💰 رصيد OLK: `{user[1]:.2f} OLK`\n"
        f"💳 رصيد Gram: `{user[2]:.4f} Gram`\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(dash_text, parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

async def web_handler(request):
    return web.Response(text=MINI_APP_HTML, content_type="text/html")

async def main():
    await init_db()
    print("Bot is running with full DB Web Sync...")

    app = web.Application()
    app.router.add_get("/", web_handler)
    app.router.add_get("/api/get_user", api_get_user)
    app.router.add_post("/api/sync", api_sync)
    app.router.add_post("/api/convert", api_convert)
    app.router.add_post("/api/withdraw", api_withdraw)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
