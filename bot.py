import asyncio
import asyncpg
import time
import os
import json
import base64
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, WebAppInfo
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "8707730826:AAGWTFjqVx7x47JLTp8oQdghzxCqI87UgdE"
SUPER_ADMIN_ID = 1932161126

DATABASE_URL = "postgresql://neondb_owner:npg_jXBYdNn58Kqc@ep-summer-cloud-b4hfhejx-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"

SPONSOR_CHANNEL = "@OLKVIP"
SPONSOR_CHANNEL_LINK = "https://t.me/OLKVIP"

PROJECT_TON_WALLET = "UQB3Xs8jkbebkVumWJlnEmDkjN4YXsZuHPrXSpZT1RtmZrCB"

CONVERSION_RATE = 10000
MIN_WITHDRAW_TON = 0.1

REFERRAL_REWARD = 80.0
SIGNUP_BONUS = 50.0

WEBAPP_URL = "https://olka-bot-service.onrender.com"

db_pool = None

def raw_to_user_friendly(raw_addr: str) -> str:
    if not raw_addr or not str(raw_addr).startswith("0:"):
        return str(raw_addr) if raw_addr else ""
    try:
        wc_str, hex_str = raw_addr.split(":", 1)
        wc = int(wc_str)
        account_id = bytes.fromhex(hex_str)
        tag = 0x51
        data = bytes([tag, wc & 0xFF]) + account_id

        poly = 0x1021
        crc = 0
        for b in data:
            crc ^= (b << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ poly) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        full_data = data + crc.to_bytes(2, byteorder='big')
        return base64.urlsafe_b64encode(full_data).decode('utf-8')
    except Exception:
        return raw_addr

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AdminBroadcast(StatesGroup):
    waiting_for_message = State()

class AddTaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_channel_id = State()
    waiting_for_link = State()
    waiting_for_reward = State()

class AddAdminStates(StatesGroup):
    waiting_for_id = State()

MINI_APP_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>OLK VIP Cyber Mining Engine</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --bg-dark: #070e18;
      --card-blue: #0d1e36;
      --card-blue-light: #132a4d;
      --card-border: #1e3d6b;
      --cyan-neon: #00e5ff;
      --cyan-glow: rgba(0, 229, 255, 0.4);
      --gold-neon: #f59e0b;
      --gold-glow: rgba(245, 158, 11, 0.4);
      --green-neon: #10b981;
      --text-muted: #94a9c9;
    }
    * {
      box-sizing: border-box;
      user-select: none;
      -webkit-user-select: none;
      touch-action: manipulation;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    html, body {
      background-color: var(--bg-dark);
      color: #ffffff;
      min-height: 100vh;
      overflow-x: hidden;
    }
    .main-scroll-view {
      padding: 12px 14px 110px 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
      max-width: 480px;
      margin: 0 auto;
    }
    .top-header {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .brand-tag {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 800;
      color: var(--cyan-neon);
      background: #0f2744;
      border: 1px solid var(--card-border);
      padding: 5px 12px;
      border-radius: 12px;
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green-neon);
      box-shadow: 0 0 8px var(--green-neon);
      animation: pulse 1.8s infinite;
    }
    @keyframes pulse {
      0% { opacity: 0.4; }
      50% { opacity: 1; }
      100% { opacity: 0.4; }
    }
    .wallet-hero-glass {
      width: 100%;
      background: linear-gradient(145deg, #102648, #0a182e);
      border: 1.5px solid #255393;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6);
      border-radius: 20px;
      padding: 14px 16px;
      margin-bottom: 14px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .wallet-hero-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .wallet-icon-hexagon {
      width: 44px;
      height: 44px;
      background: linear-gradient(135deg, #0284c7, #0369a1);
      border: 1px solid #38bdf8;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: #fff;
    }
    .wallet-text-group { display: flex; flex-direction: column; }
    .wallet-title { font-size: 13px; font-weight: 800; color: #f8fafc; }
    .wallet-subtitle { font-size: 11px; color: var(--text-muted); direction: ltr; text-align: right; }
    .wallet-badge-btn {
      background: #0f2d57;
      border: 1px solid var(--cyan-neon);
      color: var(--cyan-neon);
      font-size: 11px;
      font-weight: 800;
      padding: 6px 14px;
      border-radius: 20px;
    }
    .wallet-badge-btn.connected {
      background: #064e3b;
      border-color: var(--green-neon);
      color: #34d399;
    }
    .overview-grid {
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 14px;
    }
    .overview-card {
      background: var(--card-blue);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .overview-label {
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .overview-value {
      font-size: 18px;
      font-weight: 900;
      direction: ltr;
      text-align: left;
    }
    .mining-stage-card {
      width: 100%;
      background: linear-gradient(180deg, #0f2444 0%, #09172c 100%);
      border: 1.5px solid var(--card-border);
      border-radius: 24px;
      padding: 20px 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
    }
    .status-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      background: #081426;
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 5px 14px;
      font-size: 11px;
      font-weight: 700;
      color: #94a3b8;
    }
    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #64748b;
    }
    .status-dot.active {
      background: var(--green-neon);
      box-shadow: 0 0 8px var(--green-neon);
    }
    .unclaimed-label {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 14px;
      font-weight: 700;
    }
    .unclaimed-display {
      font-size: 34px;
      font-weight: 900;
      color: #fff;
      margin-top: 2px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .unclaimed-display span {
      font-size: 18px;
      color: var(--gold-neon);
    }
    .cyber-timer-box {
      margin-top: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
      background: #07172e;
      border: 1px solid var(--cyan-neon);
      border-radius: 12px;
      padding: 6px 16px;
      font-size: 13px;
      color: var(--cyan-neon);
      font-weight: 800;
      direction: ltr;
    }
    .progress-bar-track {
      width: 100%;
      height: 9px;
      background: #061122;
      border-radius: 10px;
      margin-top: 16px;
      overflow: hidden;
      border: 1px solid var(--card-border);
    }
    .progress-bar-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #0284c7, var(--cyan-neon));
      border-radius: 10px;
      transition: width 0.3s ease;
    }
    .central-rig-emblem {
      margin: 18px 0 14px 0;
      width: 130px;
      height: 130px;
      border-radius: 50%;
      background: radial-gradient(circle, #122d54 0%, #081526 80%);
      border: 2px solid var(--cyan-neon);
      box-shadow: 0 0 25px rgba(0, 229, 255, 0.25);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .central-rig-emblem i {
      font-size: 44px;
      color: var(--cyan-neon);
    }
    .speed-badge {
      font-size: 12px;
      font-weight: 800;
      color: #cbd5e1;
      margin-top: 4px;
      direction: ltr;
    }
    .btn-main-action {
      width: 100%;
      background: linear-gradient(135deg, #0284c7, #0ea5e9);
      border: none;
      color: #fff;
      font-weight: 900;
      padding: 14px;
      border-radius: 16px;
      font-size: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 10px;
    }
    .btn-main-action.claim-state {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #000;
    }
    .btn-main-action:disabled {
      background: #1e293b;
      color: #64748b;
      cursor: not-allowed;
    }
    .page-tab {
      display: none;
      width: 100%;
      flex-direction: column;
      align-items: center;
    }
    .page-tab.active { display: flex; }
    .card-panel {
      width: 100%;
      background: var(--card-blue);
      border: 1.5px solid var(--card-border);
      border-radius: 20px;
      padding: 16px;
      margin-bottom: 12px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .plan-card {
      background: var(--card-blue-light);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .plan-info-title { font-size: 13px; font-weight: 800; color: #fff; }
    .plan-info-sub { font-size: 11px; color: var(--green-neon); margin-top: 2px; direction: ltr; text-align: right; }
    .plan-roi-sub { font-size: 10px; color: var(--text-muted); }
    .btn-buy-plan {
      background: linear-gradient(135deg, #0284c7, #0ea5e9);
      border: none;
      color: #fff;
      font-weight: 800;
      font-size: 12px;
      padding: 9px 14px;
      border-radius: 12px;
      cursor: pointer;
    }
    .convert-input-box {
      background: #081324;
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 10px 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .convert-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-size: 16px;
      font-weight: 800;
      direction: ltr;
      text-align: left;
    }
    .bottom-bar {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 68px;
      background: #081426;
      border-top: 2px solid var(--card-border);
      display: flex;
      justify-content: space-around;
      align-items: center;
      z-index: 1000;
      padding: 0 8px;
    }
    .nav-btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      color: #64748b;
      cursor: pointer;
      font-size: 11px;
      font-weight: 700;
      flex: 1;
    }
    .nav-btn i { font-size: 18px; }
    .nav-btn.active { color: var(--cyan-neon); }
    .nav-btn.active i { color: var(--cyan-neon); }
    #banned-overlay, #channel-lock-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: #060e1a;
      z-index: 99999;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      text-align: center;
    }
  </style>
</head>
<body>

  <div id="banned-overlay">
    <i class="fa-solid fa-ban" style="font-size:60px; color:#ef4444; margin-bottom:16px;"></i>
    <h2 style="color:#ef4444; margin-bottom:8px;">⛔ تم حظر هذا الحساب!</h2>
    <p id="ban-reason-text" style="font-size:13px; color:#cbd5e1; line-height:1.6;">تم اكتشاف مخالفة لقوانين المنظومة.</p>
  </div>

  <div id="channel-lock-overlay">
    <i class="fa-brands fa-telegram" style="font-size:65px; color:var(--cyan-neon); margin-bottom:16px;"></i>
    <h2 style="color:#ffffff; margin-bottom:8px;">📢 خطوة أخيرة للتفعيل!</h2>
    <p style="font-size:13px; color:#cbd5e1; line-height:1.6; margin-bottom:20px;">
      لتفعيل محطة التعدين السحابية، يجب الانضمام إلى القناة الرسمية:
      <br><strong style="color:var(--gold-neon);">@OLKVIP</strong>
    </p>
    <button class="btn-main-action" style="width:260px;" onclick="window.open('https://t.me/OLKVIP', '_blank')">
      انضم إلى القناة الآن
    </button>
    <button class="btn-main-action claim-state" style="width:260px; margin-top:8px;" onclick="loadData()">
      تحقق وتفعيل الآن
    </button>
  </div>

  <div class="main-scroll-view">
    <div class="top-header">
      <div class="brand-tag"><div class="pulse-dot"></div> OLK VIP PROTOCOL</div>
      <div style="font-size:11px; color:var(--text-muted); font-weight:700;"><i class="fa-solid fa-server"></i> Cloud Node #1</div>
    </div>

    <div class="wallet-hero-glass" onclick="handleWalletClick()">
      <div class="wallet-hero-left">
        <div class="wallet-icon-hexagon">
          <i class="fa-solid fa-wallet"></i>
        </div>
        <div class="wallet-text-group">
          <span class="wallet-title">TON Web3 Wallet</span>
          <span class="wallet-subtitle" id="wallet-addr-text">اضغط لربط المحفظة مباشرة</span>
        </div>
      </div>
      <div class="wallet-badge-btn" id="wallet-badge-btn">اتصال</div>
    </div>

    <div class="overview-grid">
      <div class="overview-card">
        <div class="overview-label"><i class="fa-solid fa-coins" style="color:var(--gold-neon);"></i> رصيد OLK الأساسي:</div>
        <div class="overview-value" style="color:var(--gold-neon);" id="olk-bal-val">0.00 OLK</div>
      </div>
      <div class="overview-card">
        <div class="overview-label"><i class="fa-solid fa-gem" style="color:var(--cyan-neon);"></i> رصيد TON (Gram):</div>
        <div class="overview-value" style="color:var(--cyan-neon);" id="ton-bal-val">0.0000 TON</div>
      </div>
    </div>

    <!-- تبويب التعدين -->
    <div class="page-tab active" id="tab-mining">
      <div class="mining-stage-card">
        <div class="status-pill">
          <div class="status-dot" id="mining-status-dot"></div>
          <span id="mining-status-text">جاهز لبدء الجلسة</span>
        </div>

        <div class="unclaimed-label">أرباح جلسة التعدين الحالية:</div>
        <div class="unclaimed-display">
          <span>OLK</span>
          <div id="unclaimed-counter">0.000000</div>
        </div>

        <div class="cyber-timer-box">
          <i class="fa-solid fa-stopwatch"></i>
          <span id="session-timer-text">08:00:00</span>
        </div>

        <div class="progress-bar-track">
          <div class="progress-bar-fill" id="session-progress-fill"></div>
        </div>

        <div class="central-rig-emblem">
          <i class="fa-solid fa-microchip"></i>
          <div class="speed-badge" id="speed-display">0.25 TH/s</div>
        </div>

        <button class="btn-main-action" id="btn-session-control" onclick="handleMiningAction()">
          <i class="fa-solid fa-power-off"></i> <span>تشغيل جلسة التعدين (8 ساعات)</span>
        </button>
      </div>
    </div>

    <!-- تبويب الباقات -->
    <div class="page-tab" id="tab-miners">
      <div class="card-panel">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-weight:900; color:var(--cyan-neon); font-size:14px;"><i class="fa-solid fa-bolt"></i> باقات أجهزة التعدين</span>
          <span style="font-size:10px; color:var(--text-muted);">استرجاع رأس المال: 15 يوماً</span>
        </div>

        <div class="plan-card">
          <div>
            <div class="plan-info-title">CPU Micro Rig</div>
            <div class="plan-info-sub">+0.15 TH/s (~66.7 OLK/يوم)</div>
            <div class="plan-roi-sub">استرجاع رأس المال خلال 15 يوماً</div>
          </div>
          <button class="btn-buy-plan" onclick="purchasePlan(0.1, 0.15)">0.1 TON</button>
        </div>

        <div class="plan-card">
          <div>
            <div class="plan-info-title">GPU Pro Miner</div>
            <div class="plan-info-sub">+0.77 TH/s (~333.3 OLK/يوم)</div>
            <div class="plan-roi-sub">استرجاع رأس المال خلال 15 يوماً</div>
          </div>
          <button class="btn-buy-plan" onclick="purchasePlan(0.5, 0.77)">0.5 TON</button>
        </div>

        <div class="plan-card">
          <div>
            <div class="plan-info-title">ASIC Mini Rig</div>
            <div class="plan-info-sub">+1.55 TH/s (~666.7 OLK/يوم)</div>
            <div class="plan-roi-sub">استرجاع رأس المال خلال 15 يوماً</div>
          </div>
          <button class="btn-buy-plan" onclick="purchasePlan(1.0, 1.55)">1.0 TON</button>
        </div>

        <div class="plan-card">
          <div>
            <div class="plan-info-title">Titan Quantum Rig</div>
            <div class="plan-info-sub">+3.86 TH/s (~1,666.7 OLK/يوم)</div>
            <div class="plan-roi-sub">استرجاع رأس المال خلال 15 يوماً</div>
          </div>
          <button class="btn-buy-plan" onclick="purchasePlan(2.5, 3.86)">2.5 TON</button>
        </div>

        <div class="plan-card">
          <div>
            <div class="plan-info-title">Enterprise Mining Node</div>
            <div class="plan-info-sub">+7.72 TH/s (~3,333.3 OLK/يوم)</div>
            <div class="plan-roi-sub">استرجاع رأس المال خلال 15 يوماً</div>
          </div>
          <button class="btn-buy-plan" onclick="purchasePlan(5.0, 7.72)">5.0 TON</button>
        </div>

        <div class="plan-card" style="border: 1.5px solid var(--gold-neon);">
          <div>
            <div class="plan-info-title" style="color:var(--gold-neon);">Apex VIP Supercluster</div>
            <div class="plan-info-sub" style="color:var(--gold-neon);">+15.43 TH/s (~6,666.7 OLK/يوم)</div>
            <div class="plan-roi-sub">استرجاع رأس المال خلال 15 يوماً</div>
          </div>
          <button class="btn-buy-plan" style="background:linear-gradient(135deg, #f59e0b, #d97706); color:#000;" onclick="purchasePlan(10.0, 15.43)">10.0 TON</button>
        </div>
      </div>
    </div>

    <!-- تبويب المحفظة -->
    <div class="page-tab" id="tab-wallet">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--gold-neon); font-size:14px; display:flex; justify-content:space-between;">
          <span>💳 صرافة OLK إلى TON</span>
          <span style="font-size:11px; color:var(--cyan-neon); direction:ltr;">1 TON = 10,000 OLK</span>
        </div>

        <div class="convert-input-box">
          <input type="number" id="swap-olk-input" class="convert-input" placeholder="1000" oninput="calcSwap()">
          <button style="background:#1e3d6b; border:1px solid var(--gold-neon); color:var(--gold-neon); padding:5px 12px; border-radius:8px; font-size:11px; font-weight:800; cursor:pointer;" onclick="setMaxSwap()">MAX</button>
        </div>

        <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted);">
          <span>ستحصل على:</span>
          <strong style="color:var(--green-neon); font-size:13px;" id="swap-preview">0.0000 TON</strong>
        </div>

        <button class="btn-main-action claim-state" style="margin-top:2px;" onclick="executeSwap()">
          تحويل الآن إلى رصيد TON
        </button>

        <hr style="border:0; border-top:1px solid var(--card-border); margin:4px 0;">

        <div style="font-weight:bold; color:var(--cyan-neon); font-size:14px;">
          <i class="fa-solid fa-money-bill-transfer"></i> سحب TON إلى محفظتك
        </div>

        <div class="convert-input-box">
          <input type="number" step="0.01" id="withdraw-amt-input" class="convert-input" placeholder="0.1">
          <span style="font-size:11px; color:#f87171;">الحد الأدنى: 0.1 TON</span>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
          <button class="btn-main-action" style="background:#059669;" onclick="depositDirect()">
            <i class="fa-solid fa-arrow-down"></i> إيداع TON
          </button>
          <button class="btn-main-action" onclick="submitWithdraw()">
            <i class="fa-solid fa-arrow-up"></i> سحب TON
          </button>
        </div>
      </div>
    </div>

    <!-- تبويب الإحالات -->
    <div class="page-tab" id="tab-frens">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--cyan-neon); font-size:14px;"><i class="fa-solid fa-users"></i> شبكة التعدين التشاركية</div>
        <div style="font-size:12px; color:#cbd5e1; line-height:1.6;">
          شارك رابط جهازك واحصل على <strong>80 OLK</strong> مجاناً فور قيام صديقك بتشغيل جلسة التعدين الأولى!
        </div>
        <button class="btn-main-action" onclick="copyInvite()">
          <i class="fa-solid fa-copy"></i> نسخ رابط الدعوة الخاص بي
        </button>
      </div>
    </div>

    <!-- تبويب المهام -->
    <div class="page-tab" id="tab-tasks">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--gold-neon); font-size:14px;"><i class="fa-solid fa-list-check"></i> المهام الإضافية المتاحة</div>
        <div id="dynamic-tasks-list" style="display:flex; flex-direction:column; gap:8px;">
          <div style="font-size:12px; color:var(--text-muted); text-align:center;">جاري تحميل المهام...</div>
        </div>
      </div>
    </div>
  </div>

  <div class="bottom-bar">
    <div class="nav-btn active" onclick="switchTab('mining', this)"><i class="fa-solid fa-pickaxe"></i><span>التعدين</span></div>
    <div class="nav-btn" onclick="switchTab('miners', this)"><i class="fa-solid fa-bolt"></i><span>الأجهزة</span></div>
    <div class="nav-btn" onclick="switchTab('wallet', this)"><i class="fa-solid fa-wallet"></i><span>المحفظة</span></div>
    <div class="nav-btn" onclick="switchTab('frens', this)"><i class="fa-solid fa-users"></i><span>الأصدقاء</span></div>
    <div class="nav-btn" onclick="switchTab('tasks', this)"><i class="fa-solid fa-clipboard-list"></i><span>المهام</span></div>
  </div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) { tg.ready(); tg.expand(); }

    const urlParams = new URLSearchParams(window.location.search);
    const userId = tg?.initDataUnsafe?.user?.id || urlParams.get('user_id') || 1932161126;

    let appOlk = 0.0;
    let appTon = 0.0;
    let speed = 0.25;
    let minerLevel = 1;
    let connectedWallet = null;

    let sessionActive = false;
    let sessionStartTs = 0;
    let sessionClaimReady = false;
    let currentUnclaimed = 0.0;

    const EIGHT_HOURS_SEC = 8 * 3600;

    const tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
      manifestUrl: window.location.origin + '/tonconnect-manifest.json'
    });

    tonConnectUI.onStatusChange(async (wallet) => {
      if (wallet) {
        try {
          connectedWallet = TON_CONNECT_UI.toUserFriendlyAddress(wallet.account.address);
        } catch(e) {
          connectedWallet = wallet.account.address;
        }
        document.getElementById("wallet-addr-text").innerText = connectedWallet.slice(0, 4) + '...' + connectedWallet.slice(-4);
        const b = document.getElementById("wallet-badge-btn");
        b.innerText = "متصل ✅";
        b.classList.add("connected");

        await fetch("/api/save_wallet", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, address: connectedWallet })
        });
      } else {
        connectedWallet = null;
        document.getElementById("wallet-addr-text").innerText = "اضغط لربط المحفظة مباشرة";
        const b = document.getElementById("wallet-badge-btn");
        b.innerText = "اتصال";
        b.classList.remove("connected");
      }
    });

    function handleWalletClick() {
      if (tonConnectUI.connected) {
        tonConnectUI.disconnect();
      } else {
        tonConnectUI.openModal();
      }
    }

    async function loadData() {
      try {
        const res = await fetch(`/api/get_user?user_id=${userId}`);
        const data = await res.json();
        if (data.banned) {
          document.getElementById("ban-reason-text").innerText = "سبب الحظر: " + (data.ban_reason || "");
          document.getElementById("banned-overlay").style.display = "flex";
          return;
        }
        if (data.need_sub) {
          document.getElementById("channel-lock-overlay").style.display = "flex";
          return;
        } else {
          document.getElementById("channel-lock-overlay").style.display = "none";
        }

        if (data.ok) {
          appOlk = data.olk_balance;
          appTon = data.ton_balance;
          speed = data.mining_speed || 0.25;
          minerLevel = data.miner_level || 1;
          sessionStartTs = data.session_start_timestamp || 0;
          sessionActive = data.session_active || false;

          document.getElementById("olk-bal-val").innerText = appOlk.toFixed(2) + " OLK";
          document.getElementById("ton-bal-val").innerText = appTon.toFixed(4) + " TON";
          document.getElementById("speed-display").innerText = speed.toFixed(2) + " TH/s";

          if (data.saved_wallet) {
            connectedWallet = data.saved_wallet;
            document.getElementById("wallet-addr-text").innerText = connectedWallet.slice(0, 4) + '...' + connectedWallet.slice(-4);
            const b = document.getElementById("wallet-badge-btn");
            b.innerText = "متصل ✅";
            b.classList.add("connected");
          }
          evaluateSessionState();
          loadTasks();
        }
      } catch (e) {
        console.error("Load failed", e);
      }
    }

    async function loadTasks() {
      try {
        const res = await fetch(`/api/get_tasks?user_id=${userId}`);
        const data = await res.json();
        const container = document.getElementById("dynamic-tasks-list");
        container.innerHTML = "";

        if (!data.tasks || data.tasks.length === 0) {
          container.innerHTML = `<div style="font-size:12px; color:var(--text-muted); text-align:center;">لا توجد مهام إضافية حالياً.</div>`;
          return;
        }

        data.tasks.forEach(task => {
          const isDone = data.completed_ids.includes(task.id);
          const div = document.createElement("div");
          div.className = "plan-card";
          div.innerHTML = `
            <div>
              <div class="plan-info-title">${task.title}</div>
              <div class="plan-info-sub" style="color:var(--gold-neon);">+${task.reward} OLK</div>
            </div>
            <div style="display:flex; gap:6px;">
              <button class="btn-buy-plan" onclick="window.open('${task.link}', '_blank')">انضمام</button>
              ${isDone 
                ? `<button class="btn-buy-plan" style="background:#475569; cursor:default;" disabled>مكتملة ✅</button>`
                : `<button class="btn-buy-plan" style="background:#10b981;" onclick="verifyTask(${task.id})">تحقق</button>`
              }
            </div>
          `;
          container.appendChild(div);
        });
      } catch (e) {
        console.error("Tasks load failed", e);
      }
    }

    function evaluateSessionState() {
      const now = Math.floor(Date.now() / 1000);
      const elapsed = now - sessionStartTs;

      if (sessionActive && elapsed < EIGHT_HOURS_SEC) {
        sessionClaimReady = false;
        document.getElementById("mining-status-dot").classList.add("active");
        document.getElementById("mining-status-text").innerText = "جلسة التعدين نشطة الآن";

        const btn = document.getElementById("btn-session-control");
        btn.classList.remove("claim-state");
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> التعدين يعمل الآن تلقائياً...`;
      } else if (sessionActive && elapsed >= EIGHT_HOURS_SEC) {
        sessionClaimReady = true;
        document.getElementById("mining-status-dot").classList.remove("active");
        document.getElementById("mining-status-text").innerText = "اكتملت الجلسة! طالب بأرباحك الآن";

        const btn = document.getElementById("btn-session-control");
        btn.classList.add("claim-state");
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-hand-holding-dollar"></i> المطالبة بأرباح الجلسة وتحديث المحفظة`;
      } else {
        sessionClaimReady = false;
        document.getElementById("mining-status-dot").classList.remove("active");
        document.getElementById("mining-status-text").innerText = "متوقف (جاهز لبدء 8 ساعات جديدة)";

        const btn = document.getElementById("btn-session-control");
        btn.classList.remove("claim-state");
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-power-off"></i> تشغيل جلسة التعدين (8 ساعات)`;
      }
    }

    setInterval(() => {
      if (!sessionActive || sessionStartTs === 0) {
        document.getElementById("session-timer-text").innerText = "08:00:00";
        document.getElementById("session-progress-fill").style.width = "0%";
        document.getElementById("unclaimed-counter").innerText = "0.000000";
        return;
      }
      const now = Math.floor(Date.now() / 1000);
      const elapsed = Math.max(0, now - sessionStartTs);

      if (elapsed < EIGHT_HOURS_SEC) {
        const remaining = EIGHT_HOURS_SEC - elapsed;
        const h = String(Math.floor(remaining / 3600)).padStart(2, '0');
        const m = String(Math.floor((remaining % 3600) / 60)).padStart(2, '0');
        const s = String(remaining % 60).padStart(2, '0');
        document.getElementById("session-timer-text").innerText = `${h}:${m}:${s}`;

        const pct = ((elapsed / EIGHT_HOURS_SEC) * 100).toFixed(1);
        document.getElementById("session-progress-fill").style.width = `${pct}%`;

        currentUnclaimed = elapsed * (speed * 0.000030 * 10);
        document.getElementById("unclaimed-counter").innerText = currentUnclaimed.toFixed(6);
      } else {
        document.getElementById("session-timer-text").innerText = "00:00:00";
        document.getElementById("session-progress-fill").style.width = "100%";
        currentUnclaimed = EIGHT_HOURS_SEC * (speed * 0.000030 * 10);
        document.getElementById("unclaimed-counter").innerText = currentUnclaimed.toFixed(6);
        evaluateSessionState();
      }
    }, 1000);

    async function handleMiningAction() {
      if (sessionClaimReady) {
        const res = await fetch("/api/claim_session_rewards", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, amount: currentUnclaimed })
        });
        const data = await res.json();
        if (data.ok) {
          appOlk = data.olk_balance;
          document.getElementById("olk-bal-val").innerText = appOlk.toFixed(2) + " OLK";
          sessionActive = false;
          sessionStartTs = 0;
          sessionClaimReady = false;
          currentUnclaimed = 0;
          evaluateSessionState();
          alert(`🎉 تم تحويل +${data.claimed.toFixed(2)} OLK بنجاح إلى رصيدك الأساسي!`);
        }
      } else {
        const res = await fetch("/api/start_mining_session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId })
        });
        const data = await res.json();
        if (data.ok) {
          sessionActive = true;
          sessionStartTs = data.session_start_timestamp;
          evaluateSessionState();
          alert("🚀 تم تشغيل جهاز التعدين لمدة 8 ساعات بنجاح!");
        }
      }
    }

    async function purchasePlan(costTon, speedGain) {
      if (appTon < costTon) {
        alert(`⚠️ رصيد TON غير كافٍ! يلزمك ${costTon} TON للمتابعة.`);
        switchTab('wallet');
        return;
      }
      const res = await fetch("/api/upgrade_rig_ton", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, cost_ton: costTon, speed_gain: speedGain })
      });
      const data = await res.json();
      if (data.ok) {
        appTon = data.ton_balance;
        speed = data.mining_speed;
        document.getElementById("ton-bal-val").innerText = appTon.toFixed(4) + " TON";
        document.getElementById("speed-display").innerText = speed.toFixed(2) + " TH/s";
        alert(`🎉 تمت ترقية العتاد بنجاح! السرعة الآن: ${speed.toFixed(2)} TH/s`);
      } else {
        alert(data.msg);
      }
    }

    function calcSwap() {
      const v = parseFloat(document.getElementById("swap-folk-input")?.value || document.getElementById("swap-olk-input").value) || 0;
      document.getElementById("swap-preview").innerText = (v / 10000).toFixed(4) + " TON";
    }

    function setMaxSwap() {
      document.getElementById("swap-olk-input").value = Math.floor(appOlk);
      calcSwap();
    }

    async function executeSwap() {
      const amt = parseFloat(document.getElementById("swap-olk-input").value) || 0;
      if (amt <= 0 || amt > appOlk) {
        alert("⚠️ يرجى إدخال كمية OLK صالحة ومتوفرة!");
        return;
      }
      const res = await fetch("/api/convert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, amount: amt })
      });
      const data = await res.json();
      if (data.ok) {
        appOlk = data.olk_balance;
        appTon = data.ton_balance;
        document.getElementById("olk-bal-val").innerText = appOlk.toFixed(2) + " OLK";
        document.getElementById("ton-bal-val").innerText = appTon.toFixed(4) + " TON";
        document.getElementById("swap-olk-input").value = "";
        calcSwap();
        alert(`✅ تم تحويل ${amt} OLK إلى TON بنجاح!`);
      } else {
        alert(data.msg);
      }
    }

    async function depositDirect() {
      if (!connectedWallet) {
        alert("❌ يرجى ربط المحفظة أولاً عبر شريط TON Wallet بالأعلى!");
        handleWalletClick();
        return;
      }
      const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 360,
        messages: [{ address: "PROJECT_TON_WALLET_PLACEHOLDER", amount: "100000000" }]
      };
      try {
        const result = await tonConnectUI.sendTransaction(transaction);
        if (result) {
          appTon += 0.1;
          document.getElementById("ton-bal-val").innerText = appTon.toFixed(4) + " TON";
          await fetch("/api/deposit_ton_credit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, amount_ton: 0.1 })
          });
          alert("🎉 تم تأكيد إيداع 0.1 TON بنجاح!");
        }
      } catch (e) {
        alert("❌ تم إلغاء الإيداع.");
      }
    }

    async function submitWithdraw() {
      if (!connectedWallet) {
        alert("❌ يرجى ربط محفظتك أولاً!");
        handleWalletClick();
        return;
      }
      const amt = parseFloat(document.getElementById("withdraw-amt-input").value) || 0;
      if (amt < 0.1 || amt > appTon) {
        alert("⚠️ المبلغ أقل من 0.1 TON أو أكبر من رصيدك المتوفر!");
        return;
      }
      const res = await fetch("/api/withdraw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, address: connectedWallet, amount_ton: amt })
      });
      const data = await res.json();
      if (data.ok) {
        appTon = data.remaining_ton;
        document.getElementById("ton-bal-val").innerText = appTon.toFixed(4) + " TON";
        document.getElementById("withdraw-amt-input").value = "";
        alert("✅ تم إرسال طلب السحب بنجاح للمراجعة والإرسال إلى محفظتك!");
      } else {
        alert(data.msg);
      }
    }

    function switchTab(name, el) {
      document.querySelectorAll(".page-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
      document.getElementById("tab-" + name).classList.add("active");
      if (el) el.classList.add("active");
      if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred("light");
    }

    function copyInvite() {
      const link = `https://t.me/OlkaVip_bot?start=${userId}`;
      navigator.clipboard.writeText(link);
      alert("✅ تم نسخ رابط الدعوة الخاص بك!");
    }

    async function verifyTask(taskId) {
      const res = await fetch("/api/verify_channel_task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, task_id: taskId })
      });
      const data = await res.json();
      alert(data.msg);
      if (data.ok) {
        appOlk += data.reward;
        document.getElementById("olk-bal-val").innerText = appOlk.toFixed(2) + " OLK";
        loadTasks();
      }
    }

    loadData();
  </script>
</body>
</html>
""".replace("PROJECT_TON_WALLET_PLACEHOLDER", PROJECT_TON_WALLET)

TON_MANIFEST = {
    "url": WEBAPP_URL,
    "name": "OLKA VIP CYBER MINING",
    "iconUrl": "https://telegram.org/img/t_logo.png",
    "termsOfUseUrl": WEBAPP_URL,
    "privacyPolicyUrl": WEBAPP_URL
}

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            phone_number TEXT,
            olk_balance DOUBLE PRECISION DEFAULT 0.0,
            ton_balance DOUBLE PRECISION DEFAULT 0.0,
            last_claim BIGINT DEFAULT 0,
            referred_by BIGINT DEFAULT NULL,
            ref_reward_claimed INTEGER DEFAULT 0,
            mining_speed DOUBLE PRECISION DEFAULT 0.25,
            miner_level INTEGER DEFAULT 1,
            last_mining_timestamp BIGINT DEFAULT 0,
            session_start_timestamp BIGINT DEFAULT 0,
            session_active INTEGER DEFAULT 0,
            tasks_completed TEXT DEFAULT '[]',
            saved_wallet TEXT DEFAULT NULL,
            ip_address TEXT DEFAULT NULL,
            device_fingerprint TEXT DEFAULT NULL,
            is_banned INTEGER DEFAULT 0,
            ban_reason TEXT DEFAULT NULL,
            activated_miner INTEGER DEFAULT 0,
            is_whitelisted INTEGER DEFAULT 0
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS bot_admins (
            user_id BIGINT PRIMARY KEY,
            can_manage_withdrawals INTEGER DEFAULT 1,
            can_manage_tasks INTEGER DEFAULT 0,
            can_broadcast INTEGER DEFAULT 0,
            can_ban_users INTEGER DEFAULT 0,
            created_at BIGINT DEFAULT 0
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_tasks (
            id SERIAL PRIMARY KEY,
            title TEXT,
            channel_id TEXT,
            link TEXT,
            reward DOUBLE PRECISION DEFAULT 10.0,
            is_active INTEGER DEFAULT 1
        );
        """)

        task_exists = await conn.fetchval("SELECT COUNT(*) FROM dynamic_tasks")
        if task_exists == 0:
            await conn.execute("""
                INSERT INTO dynamic_tasks (title, channel_id, link, reward)
                VALUES ('قناة OLKA AD الإعلانية', '@olka_ad', 'https://t.me/olka_ad', 10.0)
            """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount_ton DOUBLE PRECISION,
            wallet_address TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at BIGINT DEFAULT 0
        );
        """)

async def get_admin_permissions(user_id: int):
    if user_id == SUPER_ADMIN_ID:
        return {
            "is_super": True,
            "can_manage_withdrawals": True,
            "can_manage_tasks": True,
            "can_broadcast": True,
            "can_ban_users": True
        }
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM bot_admins WHERE user_id = $1", user_id)
        if row:
            return {
                "is_super": False,
                "can_manage_withdrawals": bool(row["can_manage_withdrawals"]),
                "can_manage_tasks": bool(row["can_manage_tasks"]),
                "can_broadcast": bool(row["can_broadcast"]),
                "can_ban_users": bool(row["can_ban_users"])
            }
    return None

async def api_manifest(request):
    return web.json_response(TON_MANIFEST)

async def api_save_wallet(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        address = str(data.get("address", "")).strip()
        friendly_address = raw_to_user_friendly(address)

        async with db_pool.acquire() as conn:
            await conn.execute("UPDATE users SET saved_wallet = $1 WHERE user_id = $2", friendly_address, user_id)
        return web.json_response({"ok": True, "address": friendly_address})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_get_tasks(request):
    try:
        user_id = int(request.query.get("user_id", 0))
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, title, channel_id, link, reward FROM dynamic_tasks WHERE is_active = 1 ORDER BY id DESC")
            tasks = [dict(r) for r in rows]
            u_row = await conn.fetchrow("SELECT tasks_completed FROM users WHERE user_id = $1", user_id)
            completed_ids = json.loads(u_row["tasks_completed"]) if u_row and u_row["tasks_completed"] else []
        return web.json_response({"ok": True, "tasks": tasks, "completed_ids": completed_ids})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_get_user(request):
    try:
        user_id = int(request.query.get("user_id", 0))
        now = int(time.time())

        is_sub = True
        try:
            member = await bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
            if member.status in ["left", "kicked"]:
                is_sub = False
        except Exception:
            is_sub = True

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT is_banned, ban_reason, olk_balance, ton_balance, mining_speed, miner_level,
                       saved_wallet, referred_by, ref_reward_claimed, activated_miner,
                       session_start_timestamp, session_active
                FROM users WHERE user_id = $1
            """, user_id)

            if row and row["is_banned"] == 1:
                return web.json_response({"ok": False, "banned": True, "ban_reason": row["ban_reason"]})

            if not is_sub:
                return web.json_response({"ok": True, "need_sub": True})

            if row:
                olk = row["olk_balance"]
                if row["activated_miner"] == 0:
                    olk += SIGNUP_BONUS
                    await conn.execute("UPDATE users SET activated_miner = 1, olk_balance = $1 WHERE user_id = $2", olk, user_id)

                return web.json_response({
                    "ok": True,
                    "need_sub": False,
                    "banned": False,
                    "olk_balance": olk,
                    "ton_balance": row["ton_balance"],
                    "mining_speed": row["mining_speed"],
                    "miner_level": row["miner_level"],
                    "saved_wallet": raw_to_user_friendly(row["saved_wallet"]),
                    "session_start_timestamp": row["session_start_timestamp"] or 0,
                    "session_active": bool(row["session_active"])
                })
            else:
                await conn.execute("""
                    INSERT INTO users (user_id, last_mining_timestamp, mining_speed, olk_balance, activated_miner)
                    VALUES ($1, $2, 0.25, $3, 1) ON CONFLICT (user_id) DO NOTHING
                """, user_id, now, SIGNUP_BONUS)
                return web.json_response({
                    "ok": True,
                    "need_sub": False,
                    "banned": False,
                    "olk_balance": SIGNUP_BONUS,
                    "ton_balance": 0.0,
                    "mining_speed": 0.25,
                    "miner_level": 1,
                    "saved_wallet": None,
                    "session_start_timestamp": 0,
                    "session_active": False
                })
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_start_mining_session(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        now = int(time.time())

        async with db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET session_start_timestamp = $1, session_active = 1 WHERE user_id = $2
            """, now, user_id)

            row = await conn.fetchrow("SELECT referred_by, ref_reward_claimed FROM users WHERE user_id = $1", user_id)
            if row and row["referred_by"] and row["ref_reward_claimed"] == 0:
                ref_by = row["referred_by"]
                await conn.execute("UPDATE users SET olk_balance = olk_balance + $1 WHERE user_id = $2", REFERRAL_REWARD, ref_by)
                await conn.execute("UPDATE users SET ref_reward_claimed = 1 WHERE user_id = $1", user_id)
                try:
                    await bot.send_message(
                        chat_id=ref_by,
                        text=f"🎉 **إحالة مؤكدة!** قام صديقك بتشغيل جلسة التعدين الأولى.\n💰 أضيفت **+{REFERRAL_REWARD:.0f} OLK** إلى محفظتك بنجاح!"
                    )
                except Exception:
                    pass

        return web.json_response({"ok": True, "session_start_timestamp": now})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_claim_session_rewards(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        amount = float(data.get("amount", 0))

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT olk_balance FROM users WHERE user_id = $1", user_id)
            new_bal = (row["olk_balance"] if row else 0.0) + amount

            await conn.execute("""
                UPDATE users SET olk_balance = $1, session_active = 0, session_start_timestamp = 0 WHERE user_id = $2
            """, new_bal, user_id)

        return web.json_response({"ok": True, "olk_balance": new_bal, "claimed": amount})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_upgrade_rig_ton(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        cost_ton = float(data.get("cost_ton"))
        speed_gain = float(data.get("speed_gain"))

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT ton_balance, mining_speed, miner_level FROM users WHERE user_id = $1", user_id)
            if not row or row["ton_balance"] < cost_ton:
                return web.json_response({"ok": False, "msg": "رصيد TON غير كافٍ"})

            new_ton = row["ton_balance"] - cost_ton
            new_speed = row["mining_speed"] + speed_gain
            new_lvl = row["miner_level"] + 1

            await conn.execute("""
                UPDATE users SET ton_balance = $1, mining_speed = $2, miner_level = $3 WHERE user_id = $4
            """, new_ton, new_speed, new_lvl, user_id)

        return web.json_response({"ok": True, "ton_balance": new_ton, "mining_speed": new_speed})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_deposit_ton_credit(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        amount_ton = float(data.get("amount_ton", 0.1))

        async with db_pool.acquire() as conn:
            await conn.execute("UPDATE users SET ton_balance = ton_balance + $1 WHERE user_id = $2", amount_ton, user_id)
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_convert(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        amount = float(data.get("amount", 0))

        if amount <= 0:
            return web.json_response({"ok": False, "msg": "كمية غير صالحة"})

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT olk_balance, ton_balance FROM users WHERE user_id = $1", user_id)
            if not row or row["olk_balance"] < amount:
                return web.json_response({"ok": False, "msg": "رصيد OLK غير كافٍ"})

            ton_add = amount / CONVERSION_RATE
            new_olk = row["olk_balance"] - amount
            new_ton = row["ton_balance"] + ton_add

            await conn.execute("UPDATE users SET olk_balance = $1, ton_balance = $2 WHERE user_id = $3", new_olk, new_ton, user_id)
            return web.json_response({"ok": True, "olk_balance": new_olk, "ton_balance": new_ton})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_withdraw(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        address = str(data.get("address", "")).strip()
        withdraw_amount = float(data.get("amount_ton", 0))
        friendly_address = raw_to_user_friendly(address)
        now = int(time.time())

        if withdraw_amount < MIN_WITHDRAW_TON:
            return web.json_response({"ok": False, "msg": f"الحد الأدنى للسحب هو {MIN_WITHDRAW_TON} TON"})

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT ton_balance FROM users WHERE user_id = $1", user_id)
            if not row or row["ton_balance"] < withdraw_amount:
                return web.json_response({"ok": False, "msg": "رصيدك غير كافٍ"})

            remaining = row["ton_balance"] - withdraw_amount
            w_id = await conn.fetchval(
                "INSERT INTO withdrawals (user_id, amount_ton, wallet_address, created_at) VALUES ($1, $2, $3, $4) RETURNING id",
                user_id, withdraw_amount, friendly_address, now
            )
            await conn.execute("UPDATE users SET ton_balance = $1 WHERE user_id = $2", remaining, user_id)

        admin_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ موافقة ودفع", callback_data=f"adm_app_{w_id}"),
                InlineKeyboardButton(text="❌ رفض", callback_data=f"adm_rej_{w_id}")
            ]
        ])
        admin_notification = (
            f"🚨 **طلب سحب TON جديد #{w_id}**\n\n"
            f"👤 المستخدم: `{user_id}`\n"
            f"💎 المبلغ: `{withdraw_amount:.4f} TON`\n"
            f"📫 المحفظة:\n`{friendly_address}`"
        )
        try:
            await bot.send_message(chat_id=SUPER_ADMIN_ID, text=admin_notification, reply_markup=admin_kb, parse_mode="Markdown")
        except Exception:
            pass

        return web.json_response({"ok": True, "remaining_ton": remaining})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_verify_channel_task(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        task_id = int(data.get("task_id"))

        async with db_pool.acquire() as conn:
            task = await conn.fetchrow("SELECT * FROM dynamic_tasks WHERE id = $1 AND is_active = 1", task_id)
            if not task:
                return web.json_response({"ok": False, "msg": "المهمة غير متوفرة"})

            row = await conn.fetchrow("SELECT tasks_completed FROM users WHERE user_id = $1", user_id)
            tasks = json.loads(row["tasks_completed"]) if row and row["tasks_completed"] else []

            if task_id in tasks:
                return web.json_response({"ok": False, "msg": "تم استلام مكافأة هذه المهمة مسبقاً!"})

            try:
                chat_member = await bot.get_chat_member(chat_id=task["channel_id"], user_id=user_id)
                if chat_member.status in ["left", "kicked"]:
                    return web.json_response({"ok": False, "msg": "❌ لم تنضم للقناة بعد! انضم ثم تحقق."})
            except Exception:
                return web.json_response({"ok": False, "msg": "⚠️ تعذر التحقق، تأكد من إضافة البوت مشرفاً في القناة."})

            tasks.append(task_id)
            reward = task["reward"]
            await conn.execute("UPDATE users SET olk_balance = olk_balance + $1, tasks_completed = $2 WHERE user_id = $3",
                               reward, json.dumps(tasks), user_id)

            return web.json_response({"ok": True, "reward": reward, "msg": f"✅ مبروك! تمت إضافة +{reward:.0f} OLK"})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

# ==================== لوحة التحكم والتبديل المباشر ====================

def build_combined_start_keyboard(user_id: int, perms: dict | None):
    app_url = f"{WEBAPP_URL}?user_id={user_id}"
    buttons = [
        [InlineKeyboardButton(text="⚡ فتح محطة التعدين السحابية (Play Now) 🚀", web_app=WebAppInfo(url=app_url))]
    ]
    if perms:
        buttons.append([InlineKeyboardButton(text="👑 فتح لوحة التحكم الإدارية (Admin Panel)", callback_data="adm_home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def build_main_admin_keyboard(perms):
    buttons = [
        [InlineKeyboardButton(text="📊 إحصائيات المنظومة والمستخدمين", callback_data="adm_stats")]
    ]
    if perms.get("can_manage_withdrawals"):
        buttons.append([InlineKeyboardButton(text="⏳ طلبات السحب المعلقة", callback_data="adm_view_withdraws")])
    if perms.get("can_manage_tasks"):
        buttons.append([InlineKeyboardButton(text="📢 إدارة مهام القنوات (إضافة/حذف)", callback_data="adm_tasks_menu")])
    if perms.get("can_broadcast"):
        buttons.append([InlineKeyboardButton(text="📨 إرسال إذاعة عامة (Broadcast)", callback_data="adm_start_bc")])
    if perms.get("is_super"):
        buttons.append([InlineKeyboardButton(text="👑 إدارة المشرفين والصلاحيات (خاص بالرئيس)", callback_data="adm_manage_admins")])
    buttons.append([InlineKeyboardButton(text="🔙 العودة لقائمة البوت", callback_data="adm_back_to_start")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def render_admin_perms_keyboard(target_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM bot_admins WHERE user_id = $1", target_id)

    if not row:
        return None

    def mark(val): return "✅ مفعّل" if val == 1 else "❌ معطل"

    buttons = [
        [InlineKeyboardButton(text=f"إدارة السحب: {mark(row['can_manage_withdrawals'])}", callback_data=f"adm_tog_{target_id}_w")],
        [InlineKeyboardButton(text=f"إدارة المهام: {mark(row['can_manage_tasks'])}", callback_data=f"adm_tog_{target_id}_t")],
        [InlineKeyboardButton(text=f"إرسال إذاعة: {mark(row['can_broadcast'])}", callback_data=f"adm_tog_{target_id}_b")],
        [InlineKeyboardButton(text=f"حظر المستخدمين: {mark(row['can_ban_users'])}", callback_data=f"adm_tog_{target_id}_u")],
        [InlineKeyboardButton(text="🗑️ إزالة هذا المشرف بالكامل", callback_data=f"adm_rm_admin_{target_id}")],
        [InlineKeyboardButton(text="🔙 رجوع لقائمة المشرفين", callback_data="adm_manage_admins")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    ref_param = command.args
    now = int(time.time())

    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT is_banned, ban_reason FROM users WHERE user_id = $1", user_id)

        if user and user["is_banned"] == 1:
            await message.answer(f"⛔ هذا الحساب محظور: {user['ban_reason']}")
            return

        if not user and ref_param:
            try:
                referrer_id = int(ref_param.replace("ref_", ""))
                if referrer_id != user_id:
                    await conn.execute("""
                        INSERT INTO users (user_id, referred_by, last_mining_timestamp, mining_speed, olk_balance, activated_miner)
                        VALUES ($1, $2, $3, 0.25, 0, 0)
                        ON CONFLICT (user_id) DO UPDATE SET referred_by = EXCLUDED.referred_by
                    """, user_id, referrer_id, now)
            except ValueError:
                pass
        elif not user:
            await conn.execute("""
                INSERT INTO users (user_id, last_mining_timestamp, mining_speed, olk_balance, activated_miner)
                VALUES ($1, $2, 0.25, 0, 0)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id, now)

    perms = await get_admin_permissions(user_id)
    welcome_text = (
        "⚡ **مرحباً بك في منظومة OLKA VIP Cyber Mining**\n"
        "──────────────────────\n"
        "⛏️ **جلسات تعدين يدوية كل 8 ساعات:** اضغط على زر التشغيل لبدء الإنتاج السحابي.\n"
        "💰 **أرباح فورية ومضمونة:** أرباحك تذهب مباشرة لمحفظتك داخل التطبيق.\n"
        "🎁 **مكافأة البدء:** احصل على **+50 OLK** فور تشغيل الجلسة الأولى!\n"
        "──────────────────────\n"
        "اختر أحد الخيارات للبدء:"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=build_combined_start_keyboard(user_id, perms))

@dp.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    perms = await get_admin_permissions(user_id)
    if not perms:
        return
    rank = "👑 الرئيس الأعلى (Super Admin)" if perms.get("is_super") else "🛡️ مشرف فرعي (Sub-Admin)"
    await message.answer(
        f"⚡ **لوحة التحكم والإدارة**\nرتبتك: **{rank}**\n\nاختر من الأزرار أدناه:",
        reply_markup=build_main_admin_keyboard(perms),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "adm_back_to_start")
async def cb_back_to_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    user_id = callback.from_user.id
    perms = await get_admin_permissions(user_id)
    welcome_text = (
        "⚡ **منظومة OLKA VIP Cyber Mining**\n"
        "──────────────────────\n"
        "اختر أحد الخيارات للبدء:"
    )
    await callback.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=build_combined_start_keyboard(user_id, perms))

@dp.callback_query(F.data == "adm_home")
async def cb_admin_home(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms:
        return
    rank = "👑 الرئيس الأعلى (Super Admin)" if perms.get("is_super") else "🛡️ مشرف فرعي (Sub-Admin)"
    await callback.message.edit_text(
        f"⚡ **لوحة التحكم والإدارة**\nرتبتك: **{rank}**\n\nاختر من الأزرار أدناه:",
        reply_markup=build_main_admin_keyboard(perms),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "adm_stats")
async def cb_admin_stats(callback: CallbackQuery):
    await callback.answer()
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms:
        return

    async with db_pool.acquire() as conn:
        row_users = await conn.fetchrow("SELECT COUNT(*), SUM(olk_balance), SUM(ton_balance) FROM users WHERE is_banned = 0")
        users_count = row_users[0] or 0
        total_olk = row_users[1] or 0.0
        total_ton = row_users[2] or 0.0
        pending_withdraws = await conn.fetchval("SELECT COUNT(*) FROM withdrawals WHERE status = 'PENDING'") or 0
        active_tasks = await conn.fetchval("SELECT COUNT(*) FROM dynamic_tasks WHERE is_active = 1") or 0

    stats_msg = (
        "📊 **إحصائيات المنظومة الحية:**\n"
        "──────────────────────\n"
        f"👥 إجمالي المستخدمين: `{users_count}`\n"
        f"🪙 إجمالي رصيد OLK: `{total_olk:.2f}`\n"
        f"💎 إجمالي رصيد TON: `{total_ton:.4f}`\n"
        f"⏳ طلبات السحب المعلقة: `{pending_withdraws}`\n"
        f"📢 المهام النشطة: `{active_tasks}`\n"
        "──────────────────────"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة للرئيسية", callback_data="adm_home")]])
    await callback.message.edit_text(stats_msg, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data == "adm_view_withdraws")
async def cb_view_withdraws(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_withdrawals"):
        await callback.answer("⛔ ليس لديك صلاحية إدارة السحب", show_alert=True)
        return
    await callback.answer()

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, user_id, amount_ton, wallet_address FROM withdrawals WHERE status = 'PENDING' ORDER BY id ASC LIMIT 5")

    if not rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة", callback_data="adm_home")]])
        await callback.message.edit_text("✅ لا توجد طلبات سحب معلقة حالياً!", reply_markup=kb)
        return

    for r in rows:
        w_id = r["id"]
        uid = r["user_id"]
        amt = r["amount_ton"]
        w_addr = r["wallet_address"]

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ موافقة ودفع", callback_data=f"adm_app_{w_id}"),
                InlineKeyboardButton(text="❌ رفض وإرجاع الرصيد", callback_data=f"adm_rej_{w_id}")
            ]
        ])
        await callback.message.answer(
            f"📄 **طلب سحب #{w_id}**\n👤 المستخدم: `{uid}`\n💎 المبلغ: `{amt:.4f} TON`\n📫 المحفظة:\n`{w_addr}`",
            parse_mode="Markdown",
            reply_markup=kb
        )

@dp.callback_query(F.data == "adm_tasks_menu")
async def cb_tasks_menu(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"):
        await callback.answer("⛔ ليس لديك صلاحية إدارة المهام", show_alert=True)
        return
    await callback.answer()

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, title, reward FROM dynamic_tasks WHERE is_active = 1 ORDER BY id DESC")

    buttons = [[InlineKeyboardButton(text="➕ إضافة مهمة قناة جديدة", callback_data="adm_add_task_start")]]
    for r in rows:
        buttons.append([
            InlineKeyboardButton(text=f"🗑️ حذف: {r['title']} (+{r['reward']} OLK)", callback_data=f"adm_del_task_{r['id']}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 العودة للرئيسية", callback_data="adm_home")])

    await callback.message.edit_text("📢 **إدارة مهام القنوات:**\nيمكنك إضافة قنوات جديدة تظهر فوراً بالتطبيق أو حذف القنوات القديمة:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "adm_add_task_start")
async def cb_add_task_start(callback: CallbackQuery, state: FSMContext):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"):
        return
    await callback.answer()
    await callback.message.answer("📝 أرسل الآن **عنوان المهمة** (مثال: اشترك في قناة الأخبار):")
    await state.set_state(AddTaskStates.waiting_for_title)

@dp.message(AddTaskStates.waiting_for_title)
async def state_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("📢 أرسل الآن **معرّف القناة** (مثال: `@channel_name` أو الـ Chat ID مع التأكد من إضافة البوت مشرفاً فيها):")
    await state.set_state(AddTaskStates.waiting_for_channel_id)

@dp.message(AddTaskStates.waiting_for_channel_id)
async def state_task_channel_id(message: Message, state: FSMContext):
    await state.update_data(channel_id=message.text.strip())
    await message.answer("🔗 أرسل الآن **رابط القناة** ليضغط عليه المستخدم (مثال: `https://t.me/channel_name`):")
    await state.set_state(AddTaskStates.waiting_for_link)

@dp.message(AddTaskStates.waiting_for_link)
async def state_task_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text.strip())
    await message.answer("💰 أرسل **قيمة المكافأة** بعملة OLK (مثال: 15):")
    await state.set_state(AddTaskStates.waiting_for_reward)

@dp.message(AddTaskStates.waiting_for_reward)
async def state_task_reward(message: Message, state: FSMContext):
    try:
        reward = float(message.text.strip())
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح للمكافأة:")
        return

    data = await state.get_data()
    await state.clear()

    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO dynamic_tasks (title, channel_id, link, reward)
            VALUES ($1, $2, $3, $4)
        """, data["title"], data["channel_id"], data["link"], reward)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة لقائمة المهام", callback_data="adm_tasks_menu")]])
    await message.answer(f"🎉 **تمت إضافة المهمة بنجاح!**\nالعنوان: {data['title']}\nالمكافأة: +{reward} OLK", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("adm_del_task_"))
async def cb_del_task(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"):
        return
    t_id = int(callback.data.split("_")[3])
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE dynamic_tasks SET is_active = 0 WHERE id = $1", t_id)
    await callback.answer("🗑️ تم حذف المهمة بنجاح!", show_alert=True)
    await cb_tasks_menu(callback)

@dp.callback_query(F.data == "adm_manage_admins")
async def cb_manage_admins(callback: CallbackQuery):
    if callback.from_user.id != SUPER_ADMIN_ID:
        await callback.answer("⛔ هذا القسم محصور بالرئيس الأعلى فقط!", show_alert=True)
        return
    await callback.answer()

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM bot_admins")

    buttons = [[InlineKeyboardButton(text="➕ إضافة مشرف جديد", callback_data="adm_add_admin_start")]]
    for r in rows:
        buttons.append([InlineKeyboardButton(text=f"⚙️ المشرف: {r['user_id']}", callback_data=f"adm_edit_admin_{r['user_id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 العودة للرئيسية", callback_data="adm_home")])

    await callback.message.edit_text("👑 **إدارة المشرفين والصلاحيات:**\nيمكنك تعيين مشرفين جدد وتحديد ما يظهر لكل منهم:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "adm_add_admin_start")
async def cb_add_admin_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID:
        return
    await callback.answer()
    await callback.message.answer("🆔 أرسل الآن **معرّف المشرف (Telegram ID)** الذي تريد إضافته:")
    await state.set_state(AddAdminStates.waiting_for_id)

@dp.message(AddAdminStates.waiting_for_id)
async def state_save_new_admin(message: Message, state: FSMContext):
    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ المعرف يجب أن يكون رقماً صحيحاً:")
        return

    await state.clear()
    now = int(time.time())
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO bot_admins (user_id, can_manage_withdrawals, can_manage_tasks, can_broadcast, can_ban_users, created_at)
            VALUES ($1, 1, 0, 0, 0, $2)
            ON CONFLICT (user_id) DO NOTHING
        """, new_admin_id, now)

    await message.answer(f"✅ تم إضافة المشرف `{new_admin_id}` بنجاح! يمكنك الآن ضبط صلاحياته من قائمة المشرفين.", parse_mode="Markdown")

@dp.callback_query(F.data.startswith("adm_edit_admin_"))
async def cb_edit_admin(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id != SUPER_ADMIN_ID:
        return
    target_id = int(callback.data.split("_")[3])
    kb = await render_admin_perms_keyboard(target_id)
    if not kb:
        await callback.message.answer("المشرف غير موجود")
        return

    await callback.message.edit_text(
        f"⚙️ **ضبط صلاحيات المشرف:** `{target_id}`\nانقر على أي خيار لتفعيله أو تعطيله فورياً:",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("adm_tog_"))
async def cb_toggle_permission(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id != SUPER_ADMIN_ID:
        return
    parts = callback.data.split("_")
    target_id = int(parts[2])
    field_code = parts[3]

    col_map = {
        "w": "can_manage_withdrawals",
        "t": "can_manage_tasks",
        "b": "can_broadcast",
        "u": "can_ban_users"
    }
    col = col_map.get(field_code)
    if not col:
        return

    async with db_pool.acquire() as conn:
        await conn.execute(
            f"UPDATE bot_admins SET {col} = (CASE WHEN {col} = 1 THEN 0 ELSE 1 END) WHERE user_id = $1",
            target_id
        )

    kb = await render_admin_perms_keyboard(target_id)
    if kb:
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            pass

@dp.callback_query(F.data.startswith("adm_rm_admin_"))
async def cb_remove_admin(callback: CallbackQuery):
    if callback.from_user.id != SUPER_ADMIN_ID:
        return
    target_id = int(callback.data.split("_")[3])
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM bot_admins WHERE user_id = $1", target_id)
    await callback.answer("🗑️ تم حذف المشرف بنجاح!", show_alert=True)
    await cb_manage_admins(callback)

@dp.callback_query(F.data == "adm_start_bc")
async def cb_start_broadcast(callback: CallbackQuery, state: FSMContext):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_broadcast"):
        await callback.answer("⛔ ليس لديك صلاحية الإذاعة", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer("📝 أرسل الآن الرسالة المراد إذاعتها لجميع المشتركين:")
    await state.set_state(AdminBroadcast.waiting_for_message)

@dp.message(AdminBroadcast.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    await state.clear()
    text = message.text
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users WHERE is_banned = 0")

    success, fail = 0, 0
    await message.answer(f"🚀 بدء الإذاعة لـ {len(rows)} مستخدم...")
    for row in rows:
        try:
            await bot.send_message(chat_id=row["user_id"], text=text)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    await message.answer(f"✅ اكتملت الإذاعة!\nالناجحة: {success} | الفاشلة: {fail}")

@dp.callback_query(F.data.startswith("adm_app_"))
async def approve_withdraw(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_withdrawals"):
        return
    await callback.answer()
    w_id = int(callback.data.split("_")[2])
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT user_id, amount_ton FROM withdrawals WHERE id = $1", w_id)
        if row:
            uid, amount = row["user_id"], row["amount_ton"]
            await conn.execute("UPDATE withdrawals SET status = 'APPROVED' WHERE id = $1", w_id)
            try:
                await bot.send_message(chat_id=uid, text=f"🎉 **تمت الموافقة ودفع سحب {amount:.4f} TON لمحفظتك!**", parse_mode="Markdown")
            except Exception:
                pass
    await callback.message.edit_text(callback.message.text + "\n\n✅ **تمت الموافقة والدفع بنجاح.**")

@dp.callback_query(F.data.startswith("adm_rej_"))
async def reject_withdraw(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_withdrawals"):
        return
    await callback.answer()
    w_id = int(callback.data.split("_")[2])
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT user_id, amount_ton FROM withdrawals WHERE id = $1", w_id)
        if row:
            uid, amount = row["user_id"], row["amount_ton"]
            await conn.execute("UPDATE users SET ton_balance = ton_balance + $1 WHERE user_id = $2", amount, uid)
            await conn.execute("UPDATE withdrawals SET status = 'REJECTED' WHERE id = $1", w_id)
            try:
                await bot.send_message(chat_id=uid, text=f"❌ **تم رفض طلب السحب وإعادة {amount:.4f} TON لرصيدك.**", parse_mode="Markdown")
            except Exception:
                pass
    await callback.message.edit_text(callback.message.text + "\n\n❌ **تم رفض الطلب وإعادة الرصيد.**")

async def web_handler(request):
    return web.Response(text=MINI_APP_HTML, content_type="text/html")

async def main():
    await init_db()
    print("OLK Cyber 8-Hour Session & Admin Engine is LIVE...")

    app = web.Application()
    app.router.add_get("/", web_handler)
    app.router.add_get("/tonconnect-manifest.json", api_manifest)
    app.router.add_get("/api/get_user", api_get_user)
    app.router.add_get("/api/get_tasks", api_get_tasks)
    app.router.add_post("/api/save_wallet", api_save_wallet)
    app.router.add_post("/api/start_mining_session", api_start_mining_session)
    app.router.add_post("/api/claim_session_rewards", api_claim_session_rewards)
    app.router.add_post("/api/upgrade_rig_ton", api_upgrade_rig_ton)
    app.router.add_post("/api/deposit_ton_credit", api_deposit_ton_credit)
    app.router.add_post("/api/convert", api_convert)
    app.router.add_post("/api/withdraw", api_withdraw)
    app.router.add_post("/api/verify_channel_task", api_verify_channel_task)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
