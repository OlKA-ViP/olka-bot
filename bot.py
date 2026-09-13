import asyncio
import aiosqlite
import time
import os
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "8707730826:AAExJ7ZSQe9YFy8Y0O2eG3uPCAwVa_vG6Qc"
ADMIN_ID = 1932161126
SPONSOR_CHANNEL = "@olka_ad"
CONVERSION_RATE = 100
MIN_WITHDRAW_GRAM = 5
REFERRAL_REWARD = 100.0

WEBAPP_URL = "https://olka-bot-service.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AdminBroadcast(StatesGroup):
    waiting_for_message = State()

class UserWithdraw(StatesGroup):
    waiting_for_address = State()

# الواجهة الكاملة للميني آب المتطور
MINI_APP_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>منظومة تعدين OLK VIP</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --bg-main: #060a12;
      --card-bg: rgba(15, 23, 42, 0.78);
      --card-border: rgba(45, 66, 107, 0.55);
      --gold-primary: #f59e0b;
      --gold-glow: rgba(245, 158, 11, 0.4);
      --accent-green: #22c55e;
      --accent-cyan: #06b6d4;
      --accent-blue: #2563eb;
      --text-muted: #94a3b8;
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
      background-color: var(--bg-main);
      background-image: 
        linear-gradient(rgba(30, 41, 67, 0.22) 1px, transparent 1px),
        linear-gradient(90deg, rgba(30, 41, 67, 0.22) 1px, transparent 1px);
      background-size: 24px 24px;
      color: #ffffff;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      overflow: hidden;
    }
    .main-scroll-view {
      flex: 1;
      overflow-y: auto;
      padding: 12px 14px 85px 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
    }
    .top-header {
      width: 100%;
      text-align: center;
      font-size: 18px;
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .assets-container {
      width: 100%;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(20px);
      border-radius: 20px;
      padding: 12px 16px;
      margin-bottom: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .assets-title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      margin-bottom: 10px;
    }
    .assets-total { color: #cbd5e1; font-weight: 700; }
    .assets-total span { color: var(--gold-primary); }
    .assets-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      color: #93c5fd;
      font-size: 12px;
      font-weight: 700;
    }
    .assets-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .asset-pill {
      background: rgba(6, 11, 22, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 14px;
      padding: 8px 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      font-weight: 700;
    }
    .page-tab {
      display: none;
      width: 100%;
      flex-direction: column;
      align-items: center;
      animation: tabFadeIn 0.2s ease-out;
    }
    .page-tab.active { display: flex; }
    @keyframes tabFadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .mining-hero-card {
      width: 100%;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 26px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
      backdrop-filter: blur(20px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
      position: relative;
    }
    .miner-status-badge {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.06);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 800;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .status-online {
      background: var(--accent-green);
      color: #052e16;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 800;
    }
    .unclaimed-subtitle {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 12px;
      font-weight: 600;
    }
    .unclaimed-counter {
      font-size: 32px;
      font-weight: 900;
      color: #ffffff;
      margin-top: 2px;
      display: flex;
      align-items: center;
      gap: 6px;
      letter-spacing: 0.5px;
    }
    .unclaimed-counter span {
      color: var(--gold-primary);
      font-size: 20px;
    }
    .hashrate-capsule {
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      padding: 4px 14px;
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #93c5fd;
      font-weight: 700;
      margin-top: 6px;
    }
    .central-coin-stage {
      margin: 20px 0 14px 0;
      position: relative;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .coin-3d {
      width: 210px;
      height: 210px;
      border-radius: 50%;
      background: radial-gradient(circle at 35% 35%, #fde047 0%, #eab308 35%, #ca8a04 70%, #713f12 100%);
      border: 7px solid #fef08a;
      outline: 5px solid rgba(245, 158, 11, 0.45);
      box-shadow: 0 0 45px var(--gold-glow), inset 0 0 20px rgba(0, 0, 0, 0.5);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: transform 0.08s ease-out;
    }
    .coin-3d:active { transform: scale(0.95); }
    .coin-inner-details {
      width: 170px;
      height: 170px;
      border-radius: 50%;
      border: 2px dashed rgba(254, 240, 138, 0.6);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .coin-symbol {
      font-size: 54px;
      color: #ffffff;
      text-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
    }
    .coin-name {
      font-size: 24px;
      font-weight: 900;
      color: #ffffff;
      letter-spacing: 2px;
      text-shadow: 0 3px 8px rgba(0, 0, 0, 0.8);
      margin-top: -2px;
    }
    .btn-claim-rewards {
      width: 100%;
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #000;
      font-weight: 900;
      border: none;
      border-radius: 16px;
      padding: 14px;
      font-size: 14px;
      margin-top: 10px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
    }
    .btn-claim-rewards:active { transform: scale(0.97); }
    .hero-actions-grid {
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 1.2fr;
      gap: 12px;
      margin-top: 14px;
    }
    .btn-upgrade-rig {
      background: linear-gradient(135deg, #1d4ed8, #3b82f6);
      color: #fff;
      font-weight: 800;
      border: none;
      border-radius: 16px;
      padding: 14px;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .btn-wallet-link {
      background: linear-gradient(135deg, #2563eb, #60a5fa);
      color: #fff;
      font-weight: 800;
      border: none;
      border-radius: 16px;
      padding: 14px;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .card-panel {
      width: 100%;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 16px;
      margin-bottom: 12px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .input-clean {
      width: 100%;
      background: rgba(0, 0, 0, 0.45);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 12px;
      color: #fff;
      font-size: 13px;
      outline: none;
    }
    .rig-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(6, 11, 22, 0.7);
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .bottom-bar {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 68px;
      background: #060a12;
      border-top: 1px solid rgba(43, 62, 99, 0.4);
      display: flex;
      justify-content: space-around;
      align-items: center;
      z-index: 1000;
      padding: 0 6px;
    }
    .nav-link {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      color: #64748b;
      cursor: pointer;
      font-size: 11px;
      font-weight: 700;
      flex: 1;
      position: relative;
    }
    .nav-link i { font-size: 18px; }
    .nav-link.active { color: #bef264; }
    .nav-link.active i { color: #bef264; }
    .notify-dot {
      position: absolute;
      top: -1px;
      left: 20px;
      background: #bef264;
      color: #022c22;
      font-size: 10px;
      font-weight: 900;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  </style>
</head>
<body>

  <div class="main-scroll-view">
    <div class="top-header">
      <div style="font-size:12px; color:var(--text-muted);"><i class="fa-solid fa-server"></i> سحابي 24/7</div>
      <div>تعدين OLK VIP</div>
      <div style="font-size:12px; color:var(--accent-green);"><i class="fa-solid fa-signal"></i> مباشر</div>
    </div>

    <!-- بطاقة الأصول العلوية -->
    <div class="assets-container">
      <div class="assets-title-row">
        <div class="assets-total">الإجمالي: <span id="total-assets">0.00 OLK</span></div>
        <div class="assets-badge"><i class="fa-solid fa-shield-halved"></i> أصولي المحفوظة</div>
      </div>
      <div class="assets-grid">
        <div class="asset-pill">
          <span id="app-balance-val">0.00 OLK</span>
          <span style="color:var(--text-muted);">في التطبيق</span>
        </div>
        <div class="asset-pill">
          <span style="color:#60a5fa;" id="wallet-gram-val">0.0000 Gram</span>
          <span style="color:var(--text-muted);">المحفظة <i class="fa-solid fa-wallet"></i></span>
        </div>
      </div>
    </div>

    <!-- صفحة 1: شاشة التعدين التلقائي -->
    <div class="page-tab active" id="tab-mining">
      <div class="mining-hero-card">
        <div class="miner-status-badge">
          معدن مستوى <span id="level-display">1</span>
          <span class="status-online">نشط</span>
        </div>

        <div class="unclaimed-subtitle">مكافأة التعدين غير المطالب بها</div>
        <div class="unclaimed-counter">
          <span>OLK</span>
          <div id="unclaimed-val">0.000000</div>
        </div>

        <div class="hashrate-capsule">
          <i class="fa-solid fa-gauge-high"></i>
          <span>السرعة: <strong id="speed-val">1.50</strong> TH/s</span>
        </div>

        <div class="central-coin-stage" onclick="manualBoostClick()">
          <div class="coin-3d">
            <div class="coin-inner-details">
              <i class="fa-solid fa-pickaxe coin-symbol"></i>
              <div class="coin-name">OLK</div>
            </div>
          </div>
        </div>

        <button class="btn-claim-rewards" onclick="claimRewardsToDb()">
          <i class="fa-solid fa-cloud-arrow-down"></i> المطالبة بالأرباح وتحويلها للمحفظة
        </button>
      </div>

      <div class="hero-actions-grid">
        <button class="btn-upgrade-rig" onclick="switchNav('miners')">
          ترقية المعدن <i class="fa-solid fa-arrow-left"></i>
        </button>
        <button class="btn-wallet-link" onclick="switchNav('wallet')">
          CONNECT WALLET <i class="fa-solid fa-wallet"></i>
        </button>
      </div>
    </div>

    <!-- صفحة 2: المحفظة والسحب -->
    <div class="page-tab" id="tab-wallet">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--gold-primary); font-size:15px;">💳 إدارة المحفظة وسحب Gram</div>
        <div style="display:flex; justify-content:space-between; font-size:13px;">
          <span>رصيد Gram المتوفر للسحب:</span>
          <strong style="color:var(--accent-green);" id="gram-available-text">0.0000 Gram</strong>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-muted);">
          <span>معدل الصرف الحالي:</span>
          <span>100 OLK = 1 Gram</span>
        </div>
        <button class="btn-claim-rewards" style="margin-top:2px;" onclick="convertOlkDirect()">تحويل كل رصيد OLK إلى Gram 🔄</button>
        
        <hr style="border:0; border-top:1px solid var(--card-border); margin:6px 0;">
        <label style="font-size:12px; color:#cbd5e1;">عنوان محفظتك (TON / Gram Address):</label>
        <input type="text" id="wallet-address-field" class="input-clean" placeholder="UQ... أو EQ...">
        <button class="btn-upgrade-rig" style="width:100%;" onclick="submitWithdrawRequest()">تأكيد طلب السحب وإرساله للإدارة</button>
      </div>
    </div>

    <!-- صفحة 3: الأصدقاء والإحالة -->
    <div class="page-tab" id="tab-frens">
      <div class="card-panel">
        <div style="font-weight:bold; color:#bef264; font-size:15px;"><i class="fa-solid fa-users"></i> شبكة التعدين التشاركية (الإحالات)</div>
        <div style="font-size:13px; color:#cbd5e1;">شارك رابط جهازك واحصل على <strong>100 OLK</strong> فور توثيق صديقك لحسابه!</div>
        <button class="btn-upgrade-rig" style="width:100%;" onclick="copyReferralLink()">
          <i class="fa-solid fa-copy"></i> نسخ رابط الدعوة الخاص بي
        </button>
      </div>
    </div>

    <!-- صفحة 4: المعدنون وترقية الأجهزة -->
    <div class="page-tab" id="tab-miners">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--accent-cyan); font-size:15px;"><i class="fa-solid fa-microchip"></i> ترقية أجهزة التعدين السحابي</div>
        
        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">CPU S-Cloud Rig</div>
            <div style="font-size:11px; color:var(--text-muted);">+1.5 TH/s زيادة سرعة</div>
          </div>
          <button class="btn-upgrade-rig" style="padding:8px 12px; font-size:12px;" onclick="buyRig(1, 100, 1.5)">شراء (100 OLK)</button>
        </div>

        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">GPU Quantum Rig</div>
            <div style="font-size:11px; color:var(--text-muted);">+4.0 TH/s زيادة سرعة</div>
          </div>
          <button class="btn-upgrade-rig" style="padding:8px 12px; font-size:12px;" onclick="buyRig(2, 250, 4.0)">شراء (250 OLK)</button>
        </div>

        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">ASIC VIP Titan</div>
            <div style="font-size:11px; color:var(--text-muted);">+10.0 TH/s زيادة سرعة</div>
          </div>
          <button class="btn-upgrade-rig" style="padding:8px 12px; font-size:12px;" onclick="buyRig(3, 600, 10.0)">شراء (600 OLK)</button>
        </div>
      </div>
    </div>

    <!-- صفحة 5: المهام والمكافآت -->
    <div class="page-tab" id="tab-tasks">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--gold-primary); font-size:15px;"><i class="fa-solid fa-list-check"></i> مهام التعدين السريعة</div>
        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">الانضمام لقناة OLKA AD</div>
            <div style="font-size:11px; color:var(--text-muted);">+500 OLK مكافأة فورية</div>
          </div>
          <button class="btn-upgrade-rig" style="padding:8px 12px; font-size:12px;" onclick="executeTask('channel', 500, 'https://t.me/olka_ad')">انضمام</button>
        </div>
      </div>
    </div>
  </div>

  <!-- الشريط السفلي المطابق للأصل -->
  <div class="bottom-bar">
    <div class="nav-link" onclick="switchNav('wallet', this)">
      <i class="fa-solid fa-wallet"></i>
      <span>المحفظة</span>
    </div>
    <div class="nav-link" onclick="switchNav('frens', this)">
      <i class="fa-solid fa-user-group"></i>
      <span>الأصدقاء</span>
    </div>
    <div class="nav-link active" onclick="switchNav('mining', this)">
      <i class="fa-solid fa-pickaxe"></i>
      <span>التعدين</span>
    </div>
    <div class="nav-link" onclick="switchNav('miners', this)">
      <i class="fa-solid fa-bolt"></i>
      <span>المعدنون</span>
    </div>
    <div class="nav-link" onclick="switchNav('tasks', this)">
      <div class="notify-dot">1</div>
      <i class="fa-solid fa-clipboard-list"></i>
      <span>المهام</span>
    </div>
  </div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) { tg.ready(); tg.expand(); }

    const urlParams = new URLSearchParams(window.location.search);
    const userId = tg?.initDataUnsafe?.user?.id || urlParams.get('user_id') || 1932161126;

    let appOlk = 0;
    let appGram = 0;
    let unclaimed = 0;
    let speed = 1.50;
    let minerLevel = 1;

    const totalAssetsEl = document.getElementById("total-assets");
    const appBalEl = document.getElementById("app-balance-val");
    const walletGramEl = document.getElementById("wallet-gram-val");
    const unclaimedValEl = document.getElementById("unclaimed-val");
    const speedValEl = document.getElementById("speed-val");
    const levelDisplayEl = document.getElementById("level-display");
    const gramAvailTextEl = document.getElementById("gram-available-text");

    async function loadData() {
      try {
        const res = await fetch(`/api/get_user?user_id=${userId}`);
        const data = await res.json();
        if (data.ok) {
          appOlk = data.olk_balance;
          appGram = data.gram_balance;
          speed = data.mining_speed || 1.50;
          minerLevel = data.miner_level || 1;
          
          // حساب التعدين الذي جرى في الخلفية أثناء إغلاق التطبيق
          if (data.offline_mined) {
            unclaimed += data.offline_mined;
          }
          refreshScreen();
        }
      } catch (err) {
        console.error("Data load failed", err);
      }
    }

    function refreshScreen() {
      totalAssetsEl.innerText = (appOlk + unclaimed).toFixed(2) + " OLK";
      appBalEl.innerText = appOlk.toFixed(2) + " OLK";
      walletGramEl.innerText = appGram.toFixed(4) + " Gram";
      gramAvailTextEl.innerText = appGram.toFixed(4) + " Gram";
      unclaimedValEl.innerText = unclaimed.toFixed(6);
      speedValEl.innerText = speed.toFixed(2);
      levelDisplayEl.innerText = minerLevel;
    }

    // محرك التعدين المستمر
    setInterval(() => {
      unclaimed += (speed * 0.00015);
      unclaimedValEl.innerText = unclaimed.toFixed(6);
      totalAssetsEl.innerText = (appOlk + unclaimed).toFixed(2) + " OLK";
    }, 100);

    // المطالبة بالأرباح وحفظها رسمياً في قاعدة البيانات
    async function claimRewardsToDb() {
      if (unclaimed < 0.0001) {
        alert("⚠️ أرباح التعدين قليلة جداً حالياً، انتظر قليلاً!");
        return;
      }
      const reward = unclaimed;
      unclaimed = 0;
      appOlk += reward;
      refreshScreen();

      if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");

      try {
        await fetch("/api/claim_passive", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, amount: reward })
        });
      } catch (e) {
        console.error("Claim request failed", e);
      }
    }

    function manualBoostClick() {
      unclaimed += (speed * 0.005);
      unclaimedValEl.innerText = unclaimed.toFixed(6);
      if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred("light");
    }

    async function buyRig(rigId, cost, speedGain) {
      if (appOlk < cost) {
        alert(`⚠️ رصيدك في التطبيق غير كافٍ! يلزمك ${cost} OLK.`);
        return;
      }
      appOlk -= cost;
      speed += speedGain;
      minerLevel += 1;
      refreshScreen();

      await fetch("/api/upgrade_rig", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, cost: cost, new_speed: speed, new_level: minerLevel })
      });
      alert(`🎉 تم شراء جهاز التعدين بنجاح! السرعة الآن: ${speed.toFixed(2)} TH/s`);
    }

    async function convertOlkDirect() {
      if (appOlk < 100) {
        alert("⚠️ يلزمك 100 OLK على الأقل لتحويلها إلى Gram!");
        return;
      }
      const res = await fetch("/api/convert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId })
      });
      const data = await res.json();
      if (data.ok) {
        appOlk = data.olk_balance;
        appGram = data.gram_balance;
        refreshScreen();
        alert("✅ تم تحويل رصيد OLK إلى Gram بنجاح!");
      }
    }

    async function submitWithdrawRequest() {
      const address = document.getElementById("wallet-address-field").value.trim();
      if (!address) {
        alert("❌ يرجى كتابة عنوان محفظتك!");
        return;
      }
      const res = await fetch("/api/withdraw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, address: address })
      });
      const data = await res.json();
      if (data.ok) {
        appGram = 0;
        refreshScreen();
        document.getElementById("wallet-address-field").value = "";
        alert("✅ تم إرسال طلب السحب بنجاح إلى الإدارة!");
      } else {
        alert(data.msg);
      }
    }

    function switchNav(tabName, el) {
      document.querySelectorAll(".page-tab").forEach(tab => tab.classList.remove("active"));
      document.querySelectorAll(".nav-link").forEach(link => link.classList.remove("active"));
      document.getElementById("tab-" + tabName).classList.add("active");
      if (el) el.classList.add("active");
      if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred("light");
    }

    function copyReferralLink() {
      const invite = `https://t.me/OlkaVip_bot?start=${userId}`;
      navigator.clipboard.writeText(invite);
      alert("✅ تم نسخ رابط الإحالة الخاص بك!");
    }

    function executeTask(task, reward, link) {
      window.open(link, "_blank");
      setTimeout(async () => {
        const res = await fetch("/api/complete_task", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, task: task, reward: reward })
        });
        const d = await res.json();
        if (d.ok) {
          appOlk += reward;
          refreshScreen();
          alert(`🎉 مبروك! حصلت على +${reward} OLK.`);
        }
      }, 3000);
    }

    loadData();
  </script>
</body>
</html>
"""

# تهيئة وتحديث قاعدة البيانات
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
            ref_reward_claimed INTEGER DEFAULT 0,
            mining_speed REAL DEFAULT 1.50,
            miner_level INTEGER DEFAULT 1,
            last_mining_timestamp INTEGER DEFAULT 0,
            tasks_completed TEXT DEFAULT '[]'
        )
        """)
        # ترقية الأعمدة للجداول القديمة بسلاسة
        for col_def in [
            "referred_by INTEGER DEFAULT NULL",
            "ref_reward_claimed INTEGER DEFAULT 0",
            "mining_speed REAL DEFAULT 1.50",
            "miner_level INTEGER DEFAULT 1",
            "last_mining_timestamp INTEGER DEFAULT 0",
            "tasks_completed TEXT DEFAULT '[]'"
        ]:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col_def}")
            except Exception:
                pass

        await db.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount_gram REAL,
            wallet_address TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at INTEGER DEFAULT 0
        )
        """)
        await db.commit()

# واجهات API السحابية
async def api_get_user(request):
    try:
        user_id = int(request.query.get("user_id", 0))
        now = int(time.time())
        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT olk_balance, gram_balance, mining_speed, miner_level, last_mining_timestamp FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if row:
                    olk, gram, speed, lvl, last_ts = row
                    offline_mined = 0.0
                    if last_ts > 0:
                        diff = min(now - last_ts, 86400) # كحد أقصى 24 ساعة أوفلاين
                        offline_mined = diff * (speed * 0.00015 * 10)
                    
                    await db.execute("UPDATE users SET last_mining_timestamp = ? WHERE user_id = ?", (now, user_id))
                    await db.commit()
                    return web.json_response({
                        "ok": True,
                        "olk_balance": olk,
                        "gram_balance": gram,
                        "mining_speed": speed,
                        "miner_level": lvl,
                        "offline_mined": offline_mined
                    })
                else:
                    await db.execute("INSERT OR IGNORE INTO users (user_id, last_mining_timestamp) VALUES (?, ?)", (user_id, now))
                    await db.commit()
                    return web.json_response({"ok": True, "olk_balance": 0.0, "gram_balance": 0.0, "mining_speed": 1.5, "miner_level": 1, "offline_mined": 0.0})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_claim_passive(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        amount = float(data.get("amount", 0))
        now = int(time.time())
        async with aiosqlite.connect("olka_vip.db") as db:
            await db.execute("UPDATE users SET olk_balance = olk_balance + ?, last_mining_timestamp = ? WHERE user_id = ?", (amount, now, user_id))
            await db.commit()
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_upgrade_rig(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        cost = float(data.get("cost"))
        new_speed = float(data.get("new_speed"))
        new_level = int(data.get("new_level"))

        async with aiosqlite.connect("olka_vip.db") as db:
            await db.execute("UPDATE users SET olk_balance = olk_balance - ?, mining_speed = ?, miner_level = ? WHERE user_id = ?",
                             (cost, new_speed, new_level, user_id))
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
                    return web.json_response({"ok": False, "msg": "رصيد OLK غير كافٍ"})
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
        now = int(time.time())

        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT gram_balance, phone_number FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if not row or row[0] < MIN_WITHDRAW_GRAM:
                    return web.json_response({"ok": False, "msg": f"الحد الأدنى للسحب هو {MIN_WITHDRAW_GRAM} Gram"})

                gram_bal, phone = row[0], row[1] or "غير موثق"
                cur_ins = await db.execute("INSERT INTO withdrawals (user_id, amount_gram, wallet_address, created_at) VALUES (?, ?, ?, ?)",
                                 (user_id, gram_bal, address, now))
                withdrawal_id = cur_ins.lastrowid
                await db.execute("UPDATE users SET gram_balance = 0.0 WHERE user_id = ?", (user_id,))
                await db.commit()

        # إرسال إشعار تليجرام للمسؤول مع أزرار الموافقة/الرفض
        admin_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ موافقة وتأكيد", callback_data=f"adm_app_{withdrawal_id}"),
                InlineKeyboardButton(text="❌ رفض", callback_data=f"adm_rej_{withdrawal_id}")
            ]
        ])
        admin_notification = (
            f"🚨 **طلب سحب جديد #{withdrawal_id}**\n\n"
            f"👤 المستخدم: `{user_id}`\n"
            f"📱 الهاتف: `{phone}`\n"
            f"💰 المبلغ: `{gram_bal:.4f} Gram`\n"
            f"📫 المحفظة:\n`{address}`"
        )
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=admin_notification, reply_markup=admin_kb, parse_mode="Markdown")
        except Exception:
            pass

        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_complete_task(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        task = data.get("task")
        reward = float(data.get("reward", 0))

        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT tasks_completed FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                tasks = json.loads(row[0]) if row and row[0] else []
                if task in tasks:
                    return web.json_response({"ok": False, "msg": "المهمة منجزة مسبقاً"})
                tasks.append(task)
                await db.execute("UPDATE users SET olk_balance = olk_balance + ?, tasks_completed = ? WHERE user_id = ?",
                                 (reward, json.dumps(tasks), user_id))
                await db.commit()
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

# لوحات المفاتيح
def get_contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⚡ توثيق الحساب واستلام هدية +10 OLK 🚀", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main_dashboard_keyboard(user_id: int):
    app_url = f"{WEBAPP_URL}?user_id={user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⛏️ فتح جهاز التعدين السحابي (OLK App) 🚀", web_app=WebAppInfo(url=app_url))
        ],
        [
            InlineKeyboardButton(text="⚡ مكافأة يومية (+20)", callback_data="claim"),
            InlineKeyboardButton(text="🔄 صرافة Gram", callback_data="convert")
        ],
        [
            InlineKeyboardButton(text="💳 المحفظة والسحب", callback_data="balance"),
            InlineKeyboardButton(text="👥 شبكة الإحالة", callback_data="referral")
        ],
        [
            InlineKeyboardButton(text="📢 قناة المشروع الرسمية", url="https://t.me/olka_ad")
        ]
    ])

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except Exception:
        return True

# معالجة أوامر الإدارة المتقدمة
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT COUNT(*), SUM(olk_balance), SUM(gram_balance) FROM users") as cur:
            users_count, total_olk, total_gram = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) FROM withdrawals WHERE status = 'PENDING'") as cur:
            pending_withdraws = (await cur.fetchone())[0]

    admin_msg = (
        "👑 **لوحة تحكم إدارة المشروع (VIP Admin):**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 إجمالي المستخدمين: `{users_count}`\n"
        f"🪙 إجمالي عملات OLK: `{(total_olk or 0):.2f}`\n"
        f"💎 إجمالي عملات Gram: `{(total_gram or 0):.4f}`\n"
        f"⏳ طلبات السحب المعلقة: `{pending_withdraws}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "لإرسال إذاعة جماعية لكافة المستخدمين أرسل: `/broadcast`"
    )
    await message.answer(admin_msg, parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("📝 أرسل الآن الرسالة التي تريد إذاعتها لجميع المشتركين:")
    await state.set_state(AdminBroadcast.waiting_for_message)

@dp.message(AdminBroadcast.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    await state.clear()
    text = message.text
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()

    success, fail = 0, 0
    await message.answer(f"🚀 بدأت عملية الإذاعة لـ {len(rows)} مستخدم...")
    for row in rows:
        uid = row[0]
        try:
            await bot.send_message(chat_id=uid, text=text)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    await message.answer(f"✅ اكتملت الإذاعة!\n\n• الناجحة: {success}\n• الفاشلة: {fail}")

# موافقة أو رفض طلبات السحب
@dp.callback_query(F.data.startswith("adm_app_"))
async def approve_withdraw(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    w_id = int(callback.data.split("_")[2])
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT user_id, amount_gram FROM withdrawals WHERE id = ?", (w_id,)) as cur:
            row = await cur.fetchone()
            if row:
                uid, amount = row
                await db.execute("UPDATE withdrawals SET status = 'APPROVED' WHERE id = ?", (w_id,))
                await db.commit()
                try:
                    await bot.send_message(chat_id=uid, text=f"🎉 **تمت معالجة وإرسال طلب السحب الخاص بك بنجاح!**\n💰 المبلغ: `{amount:.4f} Gram`", parse_mode="Markdown")
                except Exception:
                    pass
    await callback.message.edit_text(callback.message.text + "\n\n✅ **تمت الموافقة والإرسال بنجاح.**")

@dp.callback_query(F.data.startswith("adm_rej_"))
async def reject_withdraw(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    w_id = int(callback.data.split("_")[2])
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT user_id, amount_gram FROM withdrawals WHERE id = ?", (w_id,)) as cur:
            row = await cur.fetchone()
            if row:
                uid, amount = row
                # إعادة الرصيد للمستخدم
                await db.execute("UPDATE users SET gram_balance = gram_balance + ? WHERE user_id = ?", (amount, uid))
                await db.execute("UPDATE withdrawals SET status = 'REJECTED' WHERE id = ?", (w_id,))
                await db.commit()
                try:
                    await bot.send_message(chat_id=uid, text=f"❌ **تم رفض طلب السحب وإعادة المبلغ لحسابك.**\n💰 المبلغ: `{amount:.4f} Gram`", parse_mode="Markdown")
                except Exception:
                    pass
    await callback.message.edit_text(callback.message.text + "\n\n❌ **تم رفض الطلب وإعادة الرصيد للمستخدم.**")

@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    user_id = message.from_user.id
    ref_param = command.args
    now = int(time.time())

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT phone_number, olk_balance, gram_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

        if not user and ref_param:
            try:
                clean_ref = ref_param.replace("ref_", "")
                referrer_id = int(clean_ref)
                if referrer_id != user_id:
                    await db.execute("""
                        INSERT INTO users (user_id, referred_by, last_mining_timestamp) VALUES (?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET referred_by = excluded.referred_by
                    """, (user_id, referrer_id, now))
                    await db.commit()
            except ValueError:
                pass
        elif not user:
            await db.execute("INSERT OR IGNORE INTO users (user_id, last_mining_timestamp) VALUES (?, ?)", (user_id, now))
            await db.commit()

    if not user or not user[0]:
        welcome_banner = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌟 **مرحباً بك في إمبراطورية OLKA VIP** 🌟\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⛏️ أقوى نظام تعدين سحابي أوتوماتيكي مع سحب Gram حقيقي.\n"
            "🎁 **هدية التوثيق:** `+10 OLK`\n\n"
            "👇 **اضغط على الزر بالأسفل لتوثيق حسابك والمطالبة بالهدية:**"
        )
        await message.answer(welcome_banner, parse_mode="Markdown", reply_markup=get_contact_keyboard())
        return

    if not await check_subscription(user_id):
        sub_banner = (
            "⚠️ **خطوة أخيرة لتفعيل جهاز التعدين!**\n\n"
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
        f"👑 **لوحة تحكم معدن OLKA VIP:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 المعرّف: `{user_id}`\n"
        f"💰 رصيد OLK المحفوظ: `{user[1]:.2f} OLK`\n"
        f"💳 رصيد Gram المتاح: `{user[2]:.4f} Gram`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 اضغط على زر جهاز التعدين بالأسفل لفتح الواجهة السحابية واللعب!"
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
                await message.answer("⛔ هذا الرقم مسجل مسبقاً في حساب آخر!")
                return

        await db.execute("""
            INSERT INTO users (user_id, phone_number, olk_balance) VALUES (?, ?, 10.0)
            ON CONFLICT(user_id) DO UPDATE SET phone_number = excluded.phone_number, olk_balance = olk_balance + 10.0
        """, (user_id, contact.phone_number))
        await db.commit()

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
                        f"💰 تمت إضافة **+{REFERRAL_REWARD:.0f} OLK** إلى محفظتك فوراً!"
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
            await callback.answer(f"⏳ يمكنك المطالبة مجدداً بعد: {hours} ساعة و {mins} دقيقة.", show_alert=True)
            return

        await db.execute("UPDATE users SET olk_balance = olk_balance + 20.0, last_claim = ? WHERE user_id = ?", (current_time, user_id))
        await db.commit()

    await callback.answer("✅ استلمت +20 OLK بنجاح!", show_alert=True)
    await callback.message.edit_text("🎉 **تم استلام المكافأة اليومية بنجاح (+20 OLK)!**", parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

@dp.callback_query(F.data == "balance")
async def balance_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT olk_balance, gram_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            olk, gram = row if row else (0.0, 0.0)

    text = (
        "💼 **محفظة التعدين السحابي (OLKA VIP):**\n"
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
        f"🎁 المكافأة: `+{REFERRAL_REWARD:.0f} OLK` لكل صديق يوثق حسابه\n\n"
        f"🔗 الرابط الخاص بك:\n`{ref_link}`"
    )
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 مشاركة الرابط", url=f"https://t.me/share/url?url={ref_link}&text=انضم%20الآن%20إلى%20جهاز%20تعدين%20OLK%20VIP!")],
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
async def withdraw_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT gram_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            gram = row[0] if row else 0.0

    if gram < MIN_WITHDRAW_GRAM:
        await callback.answer(f"⚠️ رصيدك أقل من الحد الأدنى للسحب ({MIN_WITHDRAW_GRAM} Gram).", show_alert=True)
        return

    await state.set_state(UserWithdraw.waiting_for_address)
    await callback.message.answer(f"💳 الرصيد المتاح للسحب: `{gram:.4f} Gram`\n\n📝 أرسل الآن عنوان محفظتك (TON / Gram Address):", parse_mode="Markdown")
    await callback.answer()

@dp.message(UserWithdraw.waiting_for_address)
async def process_withdraw_address(message: Message, state: FSMContext):
    user_id = message.from_user.id
    wallet_address = message.text.strip()
    await state.clear()
    now = int(time.time())

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT gram_balance, phone_number FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            gram_balance, phone = row if row else (0.0, "غير معروف")

        if gram_balance < MIN_WITHDRAW_GRAM:
            await message.answer("❌ الرصيد غير كافٍ لإتمام السحب.")
            return

        cur_ins = await db.execute("INSERT INTO withdrawals (user_id, amount_gram, wallet_address, created_at) VALUES (?, ?, ?, ?)",
                         (user_id, gram_balance, wallet_address, now))
        withdrawal_id = cur_ins.lastrowid
        await db.execute("UPDATE users SET gram_balance = 0.0 WHERE user_id = ?", (user_id,))
        await db.commit()

    await message.answer(f"✅ تم تسجيل طلب السحب بنجاح بمبلغ `{gram_balance:.4f} Gram`!", parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ موافقة وتأكيد", callback_data=f"adm_app_{withdrawal_id}"),
            InlineKeyboardButton(text="❌ رفض", callback_data=f"adm_rej_{withdrawal_id}")
        ]
    ])
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 **طلب سحب جديد #{withdrawal_id}**\n👤 المعرف: `{user_id}`\n📱 الهاتف: `{phone}`\n💰 المبلغ: `{gram_balance:.4f} Gram`\n📫 المحفظة:\n`{wallet_address}`",
            reply_markup=admin_kb,
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
        f"👑 **لوحة تحكم معدن OLKA VIP:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 المعرّف: `{user_id}`\n"
        f"💰 رصيد OLK المحفوظ: `{user[1]:.2f} OLK`\n"
        f"💳 رصيد Gram المتاح: `{user[2]:.4f} Gram`\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(dash_text, parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

async def web_handler(request):
    return web.Response(text=MINI_APP_HTML, content_type="text/html")

async def main():
    await init_db()
    print("OLK Ultra Mega Cloud Engine is online...")

    app = web.Application()
    app.router.add_get("/", web_handler)
    app.router.add_get("/api/get_user", api_get_user)
    app.router.add_post("/api/claim_passive", api_claim_passive)
    app.router.add_post("/api/upgrade_rig", api_upgrade_rig)
    app.router.add_post("/api/convert", api_convert)
    app.router.add_post("/api/withdraw", api_withdraw)
    app.router.add_post("/api/complete_task", api_complete_task)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
