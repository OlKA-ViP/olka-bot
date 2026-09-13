import asyncio
import aiosqlite
import time
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
)

BOT_TOKEN = "8707730826:AAExJ7ZSQe9YFy8Y0O2eG3uPCAwVa_vG6Qc"
ADMIN_ID = 1932161126
SPONSOR_CHANNEL = "@olka_ad"
CONVERSION_RATE = 100
MIN_WITHDRAW_GRAM = 5

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

withdraw_state = {}

# واجهة الويب الاحترافية متعددة الصفحات (AAA Mini App)
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
      --card-surface: rgba(255, 255, 255, 0.04);
      --card-border: rgba(255, 255, 255, 0.08);
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
      padding: 16px 20px 85px 20px;
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
      animation: fadeIn 0.25s ease-out forwards;
    }
    .page.active {
      display: flex;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* الشريط العلوي */
    .top-bar {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-surface);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(16px);
      padding: 10px 16px;
      border-radius: 20px;
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
      box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
    }
    .username {
      font-size: 14px;
      font-weight: 700;
    }
    .user-rank {
      font-size: 11px;
      color: var(--gold-light);
      font-weight: 600;
    }
    .server-status {
      font-size: 11px;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      padding: 5px 12px;
      border-radius: 14px;
      border: 1px solid rgba(52, 211, 153, 0.3);
      font-weight: 600;
    }

    /* عداد الرصيد */
    .score-container {
      text-align: center;
      margin: 10px 0;
    }
    .score-title {
      font-size: 12px;
      color: #94a3b8;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      font-weight: 700;
    }
    .score-value {
      font-size: 48px;
      font-weight: 900;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin-top: 4px;
      text-shadow: 0 0 30px var(--gold-glow);
    }
    .score-coin-icon {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: linear-gradient(135deg, #fbbf24, #d97706);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      font-weight: 900;
      color: #78350f;
      border: 2px solid #fef08a;
    }

    /* منطقة العملة */
    .coin-wrapper {
      position: relative;
      margin: 25px 0;
      perspective: 1000px;
    }
    .coin-glow-bg {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 280px;
      height: 280px;
      background: radial-gradient(circle, rgba(245, 158, 11, 0.25) 0%, transparent 70%);
      z-index: 0;
      pointer-events: none;
      animation: pulseGlow 3s infinite alternate;
    }
    @keyframes pulseGlow {
      from { transform: translate(-50%, -50%) scale(0.9); opacity: 0.5; }
      to { transform: translate(-50%, -50%) scale(1.15); opacity: 0.9; }
    }
    .tap-coin {
      width: 240px;
      height: 240px;
      border-radius: 50%;
      background: radial-gradient(circle at 35% 30%, #fde047 0%, #d97706 60%, #78350f 100%);
      border: 8px solid #fef08a;
      box-shadow: 0 12px 35px rgba(0,0,0,0.8), 0 0 50px var(--gold-glow), inset 0 0 25px rgba(0,0,0,0.5);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      transition: transform 0.08s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      z-index: 1;
    }
    .coin-logo {
      font-size: 46px;
      font-weight: 900;
      letter-spacing: 4px;
      color: #ffffff;
      text-shadow: 0 4px 12px rgba(0,0,0,0.7);
    }
    .coin-sub {
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 5px;
      color: rgba(255,255,255,0.9);
      margin-top: -2px;
    }
    .float-num {
      position: absolute;
      color: #fffbeb;
      font-size: 32px;
      font-weight: 900;
      pointer-events: none;
      animation: floatUp 0.75s ease-out forwards;
      text-shadow: 0 0 15px var(--gold);
      z-index: 100;
    }
    @keyframes floatUp {
      0% { opacity: 1; transform: translateY(0) scale(1); }
      100% { opacity: 0; transform: translateY(-100px) scale(1.35); }
    }

    /* شريط الطاقة */
    .energy-card {
      width: 100%;
      background: var(--card-surface);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 12px 16px;
      backdrop-filter: blur(12px);
      margin-top: 10px;
    }
    .energy-meta {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 8px;
    }
    .bar-outer {
      width: 100%;
      height: 12px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      width: 100%;
      background: linear-gradient(90deg, #0284c7, #38bdf8);
      border-radius: 12px;
      transition: width 0.15s ease-out;
    }

    /* القوائم والبطاقات (صفحات المهام، التطوير، الإحالة) */
    .section-title {
      font-size: 18px;
      font-weight: 800;
      margin: 10px 0 15px 0;
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
      margin-bottom: 12px;
      backdrop-filter: blur(10px);
    }
    .card-info {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .card-icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
    }
    .card-title {
      font-size: 14px;
      font-weight: 700;
    }
    .card-subtitle {
      font-size: 12px;
      color: #94a3b8;
      margin-top: 2px;
    }
    .btn-action {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #000;
      font-weight: 800;
      padding: 8px 16px;
      border-radius: 12px;
      border: none;
      cursor: pointer;
      font-size: 12px;
      transition: transform 0.1s;
    }
    .btn-action:active {
      transform: scale(0.95);
    }
    .btn-done {
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
      border: 1px solid rgba(52, 211, 153, 0.3);
      cursor: default;
    }

    /* الشريط السفلي للتنقل */
    .bottom-nav {
      position: fixed;
      bottom: 12px;
      left: 14px;
      right: 14px;
      height: 66px;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid var(--card-border);
      border-radius: 22px;
      display: flex;
      justify-content: space-around;
      align-items: center;
      backdrop-filter: blur(25px);
      z-index: 999;
      box-shadow: 0 10px 30px rgba(0,0,0,0.7);
    }
    .nav-btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      color: #64748b;
      cursor: pointer;
      transition: all 0.2s;
      flex: 1;
    }
    .nav-btn.active {
      color: var(--gold-light);
      transform: translateY(-2px);
    }
    .nav-btn i {
      font-size: 20px;
    }
    .nav-btn span {
      font-size: 11px;
      font-weight: 700;
    }
  </style>
</head>
<body>

  <div class="main-view">
    <!-- الشريط العلوي المستمر -->
    <div class="top-bar">
      <div class="user-profile">
        <div class="avatar-icon" id="user-avatar">O</div>
        <div class="user-text">
          <span class="username" id="user-name">VIP Miner</span>
          <span class="user-rank" id="user-rank">🥉 رتبة: برونزي</span>
        </div>
      </div>
      <div class="server-status">🟢 متصل بالسيرفر</div>
    </div>

    <!-- الصفحة 1: التعدين الرئيسي -->
    <div class="page active" id="page-mine">
      <div class="score-container">
        <div class="score-title">إجمالي رصيد التعدين (OLK)</div>
        <div class="score-value">
          <span class="score-coin-icon">🪙</span>
          <span id="score-display">0</span>
        </div>
      </div>

      <div class="coin-wrapper">
        <div class="coin-glow-bg"></div>
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

    <!-- الصفحة 2: متجر التطويرات (Boosters) -->
    <div class="page" id="page-boost">
      <div class="section-title"><i class="fa-solid fa-rocket"></i> تطويرات التعدين الخارقة</div>

      <div class="card-item">
        <div class="card-info">
          <div class="card-icon" style="background:rgba(245, 158, 11, 0.15); color:var(--gold);"><i class="fa-solid fa-hand-pointer"></i></div>
          <div>
            <div class="card-title">Multi-Tap (قوة النقر)</div>
            <div class="card-subtitle">احصل على +1 إضافية لكل ضغطة</div>
          </div>
        </div>
        <button class="btn-action" onclick="upgradeMultiTap()">تطوير (100 OLK)</button>
      </div>

      <div class="card-item">
        <div class="card-info">
          <div class="card-icon" style="background:rgba(56, 189, 248, 0.15); color:var(--accent-blue);"><i class="fa-solid fa-battery-full"></i></div>
          <div>
            <div class="card-title">مخزن الطاقة الأقصى</div>
            <div class="card-subtitle">زيادة الحد الأقصى للطاقة +500</div>
          </div>
        </div>
        <button class="btn-action" onclick="upgradeEnergyMax()">شراء (200 OLK)</button>
      </div>

      <div class="card-item">
        <div class="card-info">
          <div class="card-icon" style="background:rgba(16, 185, 129, 0.15); color:var(--accent-green);"><i class="fa-solid fa-bolt-lightning"></i></div>
          <div>
            <div class="card-title">إعادة شحن فورية (Full Tank)</div>
            <div class="card-subtitle">ملء خزان طاقتك 100% فوراً</div>
          </div>
        </div>
        <button class="btn-action" onclick="refillEnergy()">شحن مجاني</button>
      </div>
    </div>

    <!-- الصفحة 3: المهام والمكافآت (Tasks) -->
    <div class="page" id="page-tasks">
      <div class="section-title"><i class="fa-solid fa-list-check"></i> المهام والمكافآت السريعة</div>

      <div class="card-item">
        <div class="card-info">
          <div class="card-icon" style="background:rgba(59, 130, 246, 0.15); color:#60a5fa;"><i class="fa-brands fa-telegram"></i></div>
          <div>
            <div class="card-title">متابعة قناة OLKA AD</div>
            <div class="card-subtitle">+500 OLK مكافأة فورية</div>
          </div>
        </div>
        <button class="btn-action" id="task-btn-tg" onclick="completeTask('tg', 500, 'https://t.me/olka_ad')">انضمام</button>
      </div>

      <div class="card-item">
        <div class="card-info">
          <div class="card-icon" style="background:rgba(236, 72, 153, 0.15); color:#f472b6;"><i class="fa-solid fa-gift"></i></div>
          <div>
            <div class="card-title">مكافأة الدخول اليومي</div>
            <div class="card-subtitle">+200 OLK كل 24 ساعة</div>
          </div>
        </div>
        <button class="btn-action" id="daily-claim-btn" onclick="claimDailyBonus()">استلام</button>
      </div>
    </div>

    <!-- الصفحة 4: الإحالة والأصدقاء (Frens) -->
    <div class="page" id="page-frens">
      <div class="section-title"><i class="fa-solid fa-user-group"></i> نظام دعوة الأصدقاء</div>

      <div class="card-item" style="flex-direction:column; align-items:flex-start; gap:10px;">
        <div style="font-size:13px; color:#cbd5e1;">شارك رابط الإحالة الخاص بك واحصل على <strong>100 OLK</strong> فوراً لكل صديق يسجل في البوت!</div>
        <button class="btn-action" style="width:100%; padding:12px; font-size:14px;" onclick="copyInviteLink()"><i class="fa-solid fa-copy"></i> نسخ رابط الدعوة الخاص بي</button>
      </div>

      <div class="section-title" style="margin-top:15px;"><i class="fa-solid fa-trophy"></i> صدارة المعدنين (VIP Leaderboard)</div>
      <div class="card-item">
        <div class="card-info">
          <div style="font-weight:900; color:var(--gold); font-size:16px;">#1</div>
          <div class="avatar-icon" style="background:#eab308; color:#000;">👑</div>
          <div>
            <div class="card-title">VIP Whale</div>
            <div class="card-subtitle">85,200 OLK</div>
          </div>
        </div>
        <span style="font-size:12px; color:var(--gold-light); font-weight:bold;">💎 أسطوري</span>
      </div>
    </div>
  </div>

  <!-- شريط التنقل السفلي الاحترافي -->
  <div class="bottom-nav">
    <div class="nav-btn active" onclick="switchTab('mine', this)">
      <i class="fa-solid fa-pickaxe"></i>
      <span>تعدين</span>
    </div>
    <div class="nav-btn" onclick="switchTab('boost', this)">
      <i class="fa-solid fa-rocket"></i>
      <span>تطويرات</span>
    </div>
    <div class="nav-btn" onclick="switchTab('tasks', this)">
      <i class="fa-solid fa-list-check"></i>
      <span>مهام</span>
    </div>
    <div class="nav-btn" onclick="switchTab('frens', this)">
      <i class="fa-solid fa-user-group"></i>
      <span>أصدقاء</span>
    </div>
  </div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
    }

    const userNameEl = document.getElementById("user-name");
    const userAvatarEl = document.getElementById("user-avatar");
    const userRankEl = document.getElementById("user-rank");
    const scoreEl = document.getElementById("score-display");
    const energyCounterEl = document.getElementById("energy-counter");
    const energyProgressEl = document.getElementById("energy-progress");
    const coinBtn = document.getElementById("coin-btn");

    const tgUser = tg?.initDataUnsafe?.user;
    if (tgUser && tgUser.first_name) {
      userNameEl.innerText = tgUser.first_name;
      userAvatarEl.innerText = tgUser.first_name.charAt(0).toUpperCase();
    }

    let balance = parseFloat(localStorage.getItem("olk_v2_balance") || "0");
    let maxEnergy = parseInt(localStorage.getItem("olk_v2_max_energy") || "1000");
    let energy = parseInt(localStorage.getItem("olk_v2_energy") || maxEnergy.toString());
    let clickPower = parseInt(localStorage.getItem("olk_v2_tap_power") || "1");

    function updateRank() {
      if (balance >= 20000) userRankEl.innerText = "💎 رتبة: أسطوري";
      else if (balance >= 10000) userRankEl.innerText = "🥇 رتبة: ذهبي";
      else if (balance >= 3000) userRankEl.innerText = "🥈 رتبة: فضي";
      else userRankEl.innerText = "🥉 رتبة: برونزي";
    }

    function renderUI() {
      scoreEl.innerText = balance.toLocaleString();
      energyCounterEl.innerText = `${energy} / ${maxEnergy}`;
      const pct = (energy / maxEnergy) * 100;
      energyProgressEl.style.width = pct + "%";
      updateRank();
    }

    renderUI();

    // استعادة الطاقة تدريجياً
    setInterval(() => {
      if (energy < maxEnergy) {
        energy = Math.min(maxEnergy, energy + 4);
        renderUI();
        localStorage.setItem("olk_v2_energy", energy);
      }
    }, 1000);

    // النقر التفاعلي
    coinBtn.addEventListener("pointerdown", (event) => {
      if (energy < clickPower) {
        if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("error");
        return;
      }

      energy -= clickPower;
      balance += clickPower;
      renderUI();

      localStorage.setItem("olk_v2_balance", balance);
      localStorage.setItem("olk_v2_energy", energy);

      if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred("medium");

      // تأثير انحناء العملة عند الضغط (3D Tilt)
      const rect = coinBtn.getBoundingClientRect();
      const x = event.clientX - rect.left - rect.width / 2;
      const y = event.clientY - rect.top - rect.height / 2;
      coinBtn.style.transform = `scale(0.94) rotateX(${-y/10}deg) rotateY(${x/10}deg)`;

      // الرقم العائم
      const floatEl = document.createElement("div");
      floatEl.className = "float-num";
      floatEl.innerText = "+" + clickPower;
      floatEl.style.left = (event.clientX - rect.left - 15) + "px";
      floatEl.style.top = (event.clientY - rect.top - 25) + "px";
      coinBtn.parentElement.appendChild(floatEl);

      setTimeout(() => floatEl.remove(), 750);
    });

    coinBtn.addEventListener("pointerup", () => {
      coinBtn.style.transform = "scale(1) rotateX(0deg) rotateY(0deg)";
    });

    // التنقل بين التبويبات
    function switchTab(tabId, el) {
      document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
      document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
      document.getElementById("page-" + tabId).classList.add("active");
      el.classList.add("active");
      if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred("light");
    }

    // التطويرات (Boosts)
    function upgradeMultiTap() {
      if (balance >= 100) {
        balance -= 100;
        clickPower += 1;
        localStorage.setItem("olk_v2_balance", balance);
        localStorage.setItem("olk_v2_tap_power", clickPower);
        renderUI();
        if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
        alert("🎉 تم تطوير قوة النقر بنجاح!");
      } else {
        alert("⚠️ لا تملك رصيداً كافياً (تحتاج 100 OLK)");
      }
    }

    function upgradeEnergyMax() {
      if (balance >= 200) {
        balance -= 200;
        maxEnergy += 500;
        energy = maxEnergy;
        localStorage.setItem("olk_v2_balance", balance);
        localStorage.setItem("olk_v2_max_energy", maxEnergy);
        localStorage.setItem("olk_v2_energy", energy);
        renderUI();
        if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
        alert("⚡ تم توسيع خزان الطاقة بنجاح!");
      } else {
        alert("⚠️ لا تملك رصيداً كافياً (تحتاج 200 OLK)");
      }
    }

    function refillEnergy() {
      energy = maxEnergy;
      localStorage.setItem("olk_v2_energy", energy);
      renderUI();
      if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
      alert("⚡ تم ملء الطاقة بالكامل مجاناً!");
    }

    // المهام
    function completeTask(taskName, reward, link) {
      window.open(link, "_blank");
      setTimeout(() => {
        balance += reward;
        localStorage.setItem("olk_v2_balance", balance);
        renderUI();
        const btn = document.getElementById("task-btn-" + taskName);
        btn.className = "btn-action btn-done";
        btn.innerText = "تم التحقق ✅";
        btn.disabled = true;
        if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
      }, 3000);
    }

    function claimDailyBonus() {
      balance += 200;
      localStorage.setItem("olk_v2_balance", balance);
      renderUI();
      const btn = document.getElementById("daily-claim-btn");
      btn.className = "btn-action btn-done";
      btn.innerText = "تم الاستلام ✅";
      btn.disabled = true;
      if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
    }

    function copyInviteLink() {
      const botUser = "OlkaVip_bot";
      const userId = tgUser?.id || "123456";
      const inviteUrl = `https://t.me/${botUser}?start=ref_${userId}`;
      navigator.clipboard.writeText(inviteUrl);
      if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");
      alert("✅ تم نسخ رابط الدعوة الخاص بك!");
    }
  </script>
</body>
</html>
"""

async def init_db():
    async with aiosqlite.connect("olka_vip.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            phone_number TEXT UNIQUE,
            olk_balance REAL DEFAULT 0.0,
            gram_balance REAL DEFAULT 0.0,
            last_claim INTEGER DEFAULT 0
        )
        """)
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

def get_contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 توثيق الحساب برقم الهاتف", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⛏️ تعدين OLK اليومي", callback_data="claim"),
            InlineKeyboardButton(text="🔄 تحويل إلى Gram", callback_data="convert")
        ],
        [
            InlineKeyboardButton(text="💰 المحفظة والرصيد", callback_data="balance"),
            InlineKeyboardButton(text="💳 طلب سحب Gram", callback_data="withdraw")
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
async def start_handler(message: Message):
    user_id = message.from_user.id

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT phone_number FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

    if not user or not user[0]:
        await message.answer(
            "👋 مرحباً بك في مشروع OLKA VIP EMPIRE!\n\n🔒 لحماية البوت من التكرار، يرجى توثيق حسابك بمشاركة رقم هاتفك لمرة واحدة فقط:",
            reply_markup=get_contact_keyboard()
        )
        return

    if not await check_subscription(user_id):
        await message.answer(
            f"⚠️ للمتابعة داخل البوت، يجب أولاً الانضمام لقناتنا الرسمية:\n{SPONSOR_CHANNEL}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="انضم للقناة الآن 📢", url="https://t.me/olka_ad")],
                [InlineKeyboardButton(text="تحقق من الاشتراك ✅", callback_data="verify_sub")]
            ])
        )
        return

    await message.answer("🪙 مرحباً بك في لوحة تحكم OLKA VIP EMPIRE:\nاضغط على زر **Open** بالأسفل لدخول عالم التعدين والمهام!", reply_markup=main_menu())

@dp.message(F.contact)
async def contact_handler(message: Message):
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("❌ يجب إرسال رقم هاتفك الخاص بك فقط!")
        return

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE phone_number = ?", (contact.phone_number,)) as cursor:
            existing = await cursor.fetchone()
            if existing and existing[0] != message.from_user.id:
                await message.answer("⛔ هذا الرقم مستخدم مسبقاً في حساب آخر!")
                return

        await db.execute("""
            INSERT INTO users (user_id, phone_number, olk_balance) VALUES (?, ?, 10.0)
            ON CONFLICT(user_id) DO UPDATE SET phone_number = excluded.phone_number
        """, (message.from_user.id, contact.phone_number))
        await db.commit()

    await message.answer("✅ تم توثيق حسابك بنجاح وحصلت على مكافأة ترحيبية +10 OLK!", reply_markup=main_menu())

@dp.callback_query(F.data == "verify_sub")
async def verify_sub_handler(callback: CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("✅ تم التحقق من الاشتراك بنجاح!", reply_markup=main_menu())
    else:
        await callback.answer("❌ لم تنضم للقناة بعد، اضغط على الرابط وانضم أولاً.", show_alert=True)

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
            await callback.answer(f"⏳ يمكنك المطالبة مجدداً بعد: {hours} ساعة و {mins} دقيقة.", show_alert=True)
            return

        await db.execute("UPDATE users SET olk_balance = olk_balance + 20.0, last_claim = ? WHERE user_id = ?", (current_time, user_id))
        await db.commit()

    await callback.answer("✅ تمت إضافة 20 OLK إلى رصيدك بنجاح!", show_alert=True)
    await callback.message.edit_text("🎉 تم استلام التعدين اليومي بنجاح.", reply_markup=main_menu())

@dp.callback_query(F.data == "balance")
async def balance_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT olk_balance, gram_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            olk, gram = row if row else (0.0, 0.0)

    text = f"📊 محفظتك في OLKA VIP:\n\n• رصيد OLK: {olk:.2f} OLK\n• رصيد Gram: {gram:.4f} Gram\n\n💡 سعر الصرف: كل {CONVERSION_RATE} OLK = 1 Gram\n💳 الحد الأدنى للسحب: {MIN_WITHDRAW_GRAM} Gram"
    await callback.message.edit_text(text, reply_markup=main_menu())

@dp.callback_query(F.data == "convert")
async def convert_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT olk_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            olk = row[0] if row else 0.0

        if olk < CONVERSION_RATE:
            await callback.answer(f"⚠️ تحتاج إلى {CONVERSION_RATE} OLK على الأقل للتحويل.", show_alert=True)
            return

        gram_added = olk / CONVERSION_RATE
        await db.execute("UPDATE users SET olk_balance = 0.0, gram_balance = gram_balance + ? WHERE user_id = ?", (gram_added, user_id))
        await db.commit()

    await callback.answer(f"✅ تم تحويل {olk:.2f} OLK إلى {gram_added:.4f} Gram بنجاح!", show_alert=True)
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
    await callback.message.answer(f"💳 الرصيد المتاح للسحب: {gram:.4f} Gram\n\n📝 أرسل الآن عنوان محفظتك (TON / Gram Wallet):")
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

    await message.answer(f"✅ تم تسجيل طلب السحب بنجاح!\n\n• الكمية: {gram_balance:.4f} Gram\n• المحفظة: {wallet_address}\n\nستتم مراجعة الطلب والتحويل قريباً.", reply_markup=main_menu())

    admin_notification = f"🚨 طلب سحب جديد من OLKA VIP!\n\n👤 المعرف: {user_id} (@{message.from_user.username or 'بدون'})\n📱 الهاتف: {phone}\n💰 المبلغ: {gram_balance:.4f} Gram\n📫 عنوان المحفظة:\n{wallet_address}"
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_notification)
    except Exception as e:
        print(f"تعذر إرسال الإشعار للمسؤول: {e}")

async def web_handler(request):
    return web.Response(text=MINI_APP_HTML, content_type="text/html")

async def main():
    await init_db()
    print("Bot is running with Advanced Multi-Tab Web App...")

    app = web.Application()
    app.router.add_get("/", web_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
