import asyncio
import asyncpg
import time
import os
import json
import base64
import html
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, WebAppInfo, LinkPreviewOptions
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "8707730826:AAGWTFjqVx7x47JLTp8oQdghzxCqI87UgdE"
SUPER_ADMIN_ID = 1932161126

DATABASE_URL = "postgresql://neondb_owner:npg_jXBYdNn58Kqc@ep-summer-cloud-b4hfhejx-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"

# قنوات المنظومة
SPONSOR_CHANNEL = "@OLKVIP"
SPONSOR_CHANNEL_LINK = "https://t.me/OLKVIP"

PROOFS_CHANNEL = "@LOK_DI"
PROOFS_CHANNEL_LINK = "https://t.me/LOK_DI"

PROJECT_TON_WALLET = "UQCPP2tjnAodTy0eCS-LDGzeG6ss5fTmpMICSk1fiQ_peYKi"

CONVERSION_RATE = 10000
MIN_WITHDRAW_TON = 0.05
REFERRAL_REWARD = 60.0
SIGNUP_BONUS = 50.0
DEFAULT_SPEED = 0.21

ADMIN_MAX_TASK_REWARD = 70.0

# روابط الصور الرسمية المباشرة (رابط مباشر فائق السرعة يدعم تيليجرام بدون حظر imgbox)
WELCOME_IMAGE_URL = "https://i.ibb.co/vzR0j4m/olk-bot-logo.jpg"
PAYOUT_PROOF_IMAGE_URL = "https://i.ibb.co/k5yFzT5/olk-deposit-withdraw.jpg"

WEBAPP_URL = "https://olka-bot-service.onrender.com"

db_pool = None

# قاموس لتتبع رسائل السحب وتحديثها فورياً لدى الجميع لمنع الدفع المكرر
admin_withdrawal_messages = {}

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
    waiting_for_max_users = State()

class AddGroupTaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_group_id = State()
    waiting_for_link = State()
    waiting_for_reward = State()
    waiting_for_max_users = State()

class AddBotTaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_link = State()
    waiting_for_reward = State()
    waiting_for_max_users = State()

class AddAdminStates(StatesGroup):
    waiting_for_id = State()

class UnbanStates(StatesGroup):
    waiting_for_target = State()

class BanStates(StatesGroup):
    waiting_for_target = State()
    waiting_for_reason = State()

class CreatePromoStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_reward = State()
    waiting_for_max_uses = State()

MINI_APP_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl" id="html-root">
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
    .lang-toggle-btn {
      background: #0f2744;
      border: 1px solid var(--card-border);
      color: var(--gold-neon);
      font-weight: 800;
      font-size: 11px;
      padding: 5px 10px;
      border-radius: 10px;
      cursor: pointer;
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green-neon);
      box-shadow: 0 0 8px var(--green-neon);
      animation: pulse 1.8s infinite;
    }
    @keyframes pulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }
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
    .wallet-hero-left { display: flex; align-items: center; gap: 12px; }
    .wallet-icon-hexagon {
      width: 44px; height: 44px;
      background: linear-gradient(135deg, #0284c7, #0369a1);
      border: 1px solid #38bdf8;
      border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      font-size: 20px; color: #fff;
    }
    .wallet-text-group { display: flex; flex-direction: column; }
    .wallet-title { font-size: 13px; font-weight: 800; color: #f8fafc; }
    .wallet-subtitle { font-size: 11px; color: var(--text-muted); direction: ltr; text-align: right; }
    .wallet-badge-btn {
      background: #0f2d57;
      border: 1px solid var(--cyan-neon);
      color: var(--cyan-neon);
      font-size: 11px; font-weight: 800;
      padding: 6px 14px; border-radius: 20px;
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
      display: flex; flex-direction: column; gap: 4px;
    }
    .overview-label {
      font-size: 11px; color: var(--text-muted);
      display: flex; align-items: center; gap: 6px;
    }
    .overview-value { font-size: 18px; font-weight: 900; direction: ltr; text-align: left; }
    .mining-stage-card {
      width: 100%;
      background: linear-gradient(180deg, #0f2444 0%, #09172c 100%);
      border: 1.5px solid var(--card-border);
      border-radius: 24px;
      padding: 20px 14px;
      display: flex; flex-direction: column; align-items: center;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
    }
    .status-pill {
      display: flex; align-items: center; gap: 8px;
      background: #081426; border: 1px solid var(--card-border);
      border-radius: 20px; padding: 5px 14px;
      font-size: 11px; font-weight: 700; color: #94a3b8;
    }
    .status-dot { width: 7px; height: 7px; border-radius: 50%; background: #64748b; }
    .status-dot.active { background: var(--green-neon); box-shadow: 0 0 8px var(--green-neon); }
    .unclaimed-label { font-size: 12px; color: var(--text-muted); margin-top: 14px; font-weight: 700; }
    .unclaimed-display {
      font-size: 34px; font-weight: 900; color: #fff; margin-top: 2px;
      display: flex; align-items: center; gap: 6px;
    }
    .unclaimed-display span { font-size: 18px; color: var(--gold-neon); }
    .cyber-timer-box {
      margin-top: 8px; display: flex; align-items: center; gap: 8px;
      background: #07172e; border: 1px solid var(--cyan-neon);
      border-radius: 12px; padding: 6px 16px;
      font-size: 13px; color: var(--cyan-neon); font-weight: 800; direction: ltr;
    }
    .progress-bar-track {
      width: 100%; height: 9px; background: #061122;
      border-radius: 10px; margin-top: 16px; overflow: hidden;
      border: 1px solid var(--card-border);
    }
    .progress-bar-fill {
      height: 100%; width: 0%;
      background: linear-gradient(90deg, #0284c7, var(--cyan-neon));
      border-radius: 10px; transition: width 0.3s ease;
    }
    .central-rig-emblem {
      margin: 18px 0 14px 0; width: 130px; height: 130px; border-radius: 50%;
      background: radial-gradient(circle, #122d54 0%, #081526 80%);
      border: 2px solid var(--cyan-neon);
      box-shadow: 0 0 25px rgba(0, 229, 255, 0.25);
      display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .central-rig-emblem i { font-size: 44px; color: var(--cyan-neon); }
    .speed-badge { font-size: 12px; font-weight: 800; color: #cbd5e1; margin-top: 4px; direction: ltr; }
    .btn-main-action {
      width: 100%; background: linear-gradient(135deg, #0284c7, #0ea5e9);
      border: none; color: #fff; font-weight: 900;
      padding: 14px; border-radius: 16px; font-size: 14px;
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      gap: 8px; margin-top: 10px;
    }
    .btn-main-action.claim-state { background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; }
    .btn-main-action:disabled { background: #1e293b; color: #64748b; cursor: not-allowed; }
    .page-tab { display: none; width: 100%; flex-direction: column; align-items: center; }
    .page-tab.active { display: flex; }
    .card-panel {
      width: 100%; background: var(--card-blue);
      border: 1.5px solid var(--card-border);
      border-radius: 20px; padding: 16px; margin-bottom: 12px;
      display: flex; flex-direction: column; gap: 12px;
    }
    .plan-card {
      background: var(--card-blue-light); border: 1px solid var(--card-border);
      border-radius: 16px; padding: 14px;
      display: flex; justify-content: space-between; align-items: center;
      gap: 8px;
    }
    .plan-info-title { font-size: 13px; font-weight: 800; color: #fff; }
    .plan-info-sub { font-size: 11px; color: var(--green-neon); margin-top: 2px; direction: ltr; text-align: right; }
    .plan-buy-buttons { display: flex; gap: 6px; align-items: center; }
    .btn-buy-plan {
      background: linear-gradient(135deg, #0284c7, #0ea5e9);
      border: none; color: #fff; font-weight: 800; font-size: 11px;
      padding: 8px 10px; border-radius: 10px; cursor: pointer;
      white-space: nowrap;
    }
    .btn-buy-olk {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      border: none; color: #000; font-weight: 800; font-size: 11px;
      padding: 8px 10px; border-radius: 10px; cursor: pointer;
      white-space: nowrap;
    }
    .convert-input-box {
      background: #081324; border: 1px solid var(--card-border);
      border-radius: 12px; padding: 10px 12px;
      display: flex; align-items: center; gap: 8px;
    }
    .convert-input {
      flex: 1; background: transparent; border: none; outline: none;
      color: #fff; font-size: 14px; font-weight: 800; direction: ltr; text-align: left;
    }
    .tasks-horizontal-nav {
      display: flex; width: 100%; gap: 6px; margin-bottom: 12px;
      background: #091527; padding: 5px; border-radius: 14px;
      border: 1px solid var(--card-border);
    }
    .tasks-subtab-btn {
      flex: 1; padding: 9px 0; border: none; border-radius: 10px;
      background: transparent; color: #94a3b8; font-size: 12px;
      font-weight: 800; cursor: pointer; display: flex; align-items: center;
      justify-content: center; gap: 6px; transition: all 0.2s ease;
    }
    .tasks-subtab-btn.active {
      background: linear-gradient(135deg, #0284c7, #0369a1);
      color: #ffffff; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
    }
    .tasks-view-content { display: none; width: 100%; flex-direction: column; gap: 8px; }
    .tasks-view-content.active { display: flex; }

    .bottom-bar {
      position: fixed; bottom: 0; left: 0; right: 0; height: 68px;
      background: #081426; border-top: 2px solid var(--card-border);
      display: flex; justify-content: space-around; align-items: center;
      z-index: 1000; padding: 0 8px;
    }
    .nav-btn {
      display: flex; flex-direction: column; align-items: center;
      gap: 4px; color: #64748b; cursor: pointer; font-size: 11px;
      font-weight: 700; flex: 1;
    }
    .nav-btn i { font-size: 18px; }
    .nav-btn.active { color: var(--cyan-neon); }
    .nav-btn.active i { color: var(--cyan-neon); }
    #banned-overlay, #channel-lock-overlay {
      display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: #060e1a; z-index: 99999; flex-direction: column;
      align-items: center; justify-content: center; padding: 24px; text-align: center;
    }
  </style>
</head>
<body>

  <div id="banned-overlay">
    <i class="fa-solid fa-ban" style="font-size:60px; color:#ef4444; margin-bottom:16px;"></i>
    <h2 style="color:#ef4444; margin-bottom:8px;" id="t-banned-title">⛔ تم حظر هذا الحساب!</h2>
    <p id="ban-reason-text" style="font-size:13px; color:#cbd5e1; line-height:1.6;">تم اكتشاف مخالفة لقوانين المنظومة.</p>
  </div>

  <div id="channel-lock-overlay">
    <i class="fa-brands fa-telegram" style="font-size:65px; color:var(--cyan-neon); margin-bottom:16px;"></i>
    <h2 style="color:#ffffff; margin-bottom:8px;" id="t-lock-title">📢 خطوة أخيرة للتفعيل!</h2>
    <p style="font-size:13px; color:#cbd5e1; line-height:1.6; margin-bottom:16px;" id="t-lock-desc">
      لتفعيل محطة التعدين السحابية، يجب الانضمام إلى القناتين التاليتين:
      <br><strong style="color:var(--gold-neon);">@OLKVIP</strong> (القناة الرسمية)
      <br><strong style="color:var(--cyan-neon);">@LOK_DI</strong> (قناة الإثباتات)
    </p>
    <div style="display:flex; flex-direction:column; gap:8px; width:100%; max-width:280px;">
      <button class="btn-main-action" style="margin-top:0;" onclick="window.open('https://t.me/OLKVIP', '_blank')" id="t-lock-join-1">📢 انضم للقناة الرسمية</button>
      <button class="btn-main-action" style="margin-top:0; background:linear-gradient(135deg, #0369a1, #0284c7);" onclick="window.open('https://t.me/LOK_DI', '_blank')" id="t-lock-join-2">🧾 انضم لقناة الإثباتات</button>
      <button class="btn-main-action claim-state" style="margin-top:6px;" onclick="loadData()" id="t-lock-verify">تحقق وتفعيل الآن</button>
    </div>
  </div>

  <div class="main-scroll-view">
    <div class="top-header">
      <div class="brand-tag"><div class="pulse-dot"></div> OLK VIP PROTOCOL</div>
      <button class="lang-toggle-btn" onclick="toggleLanguage()"><i class="fa-solid fa-globe"></i> <span id="lang-btn-text">EN</span></button>
    </div>

    <div class="wallet-hero-glass" onclick="handleWalletClick()">
      <div class="wallet-hero-left">
        <div class="wallet-icon-hexagon"><i class="fa-solid fa-wallet"></i></div>
        <div class="wallet-text-group">
          <span class="wallet-title">TON Web3 Wallet</span>
          <span class="wallet-subtitle" id="wallet-addr-text">اضغط لربط المحفظة مباشرة</span>
        </div>
      </div>
      <div class="wallet-badge-btn" id="wallet-badge-btn">اتصال</div>
    </div>

    <div class="overview-grid">
      <div class="overview-card">
        <div class="overview-label"><i class="fa-solid fa-coins" style="color:var(--gold-neon);"></i> <span id="t-folk-bal-lbl">رصيد OLK الأساسي:</span></div>
        <div class="overview-value" style="color:var(--gold-neon);" id="olk-bal-val">0.00 OLK</div>
      </div>
      <div class="overview-card">
        <div class="overview-label"><i class="fa-solid fa-gem" style="color:var(--cyan-neon);"></i> <span id="t-ton-bal-lbl">رصيد TON (Gram):</span></div>
        <div class="overview-value" style="color:var(--cyan-neon);" id="ton-bal-val">0.0000 TON</div>
      </div>
    </div>

    <!-- تبويب التعدين والبرومو كود -->
    <div class="page-tab active" id="tab-mining">
      <div class="mining-stage-card">
        <div class="status-pill">
          <div class="status-dot" id="mining-status-dot"></div>
          <span id="mining-status-text">جاهز لبدء الجلسة</span>
        </div>

        <div class="unclaimed-label" id="t-mining-earnings-lbl">أرباح جلسة التعدين الحالية:</div>
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
          <div class="speed-badge" id="speed-display">0.21 TH/s</div>
        </div>

        <button class="btn-main-action" id="btn-session-control" onclick="handleMiningAction()">
          <i class="fa-solid fa-power-off"></i> <span id="t-btn-mine-text">تشغيل جلسة التعدين</span>
        </button>
      </div>

      <div class="card-panel" style="margin-top: 14px;">
        <div style="font-weight:900; color:var(--gold-neon); font-size:13px; display:flex; align-items:center; gap:6px;">
          <i class="fa-solid fa-gift"></i> <span id="t-promo-title">رمز الهدية الترويجي (Promo Code)</span>
        </div>
        <div style="display:flex; gap:8px;">
          <input type="text" id="promo-code-input" class="convert-input" placeholder="ادخل الرمز هنا..." style="background:#081324; border:1px solid var(--card-border); border-radius:12px; padding:10px; font-size:13px;">
          <button class="btn-main-action claim-state" style="width:110px; margin-top:0; font-size:12px;" onclick="redeemPromoCode()" id="t-promo-btn">تفعيل ⚡</button>
        </div>
      </div>
    </div>

    <!-- تبويب الباقات -->
    <div class="page-tab" id="tab-miners">
      <div class="card-panel">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-weight:900; color:var(--cyan-neon); font-size:14px;"><i class="fa-solid fa-bolt"></i> <span id="t-plans-title">باقات أجهزة التعدين</span></span>
        </div>

        <div class="plan-card">
          <div><div class="plan-info-title">CPU Micro Rig</div><div class="plan-info-sub">+0.18 TH/s</div></div>
          <div class="plan-buy-buttons">
            <button class="btn-buy-plan" onclick="purchasePlan(0.1, 0.18)">0.1 TON</button>
            <button class="btn-buy-olk" onclick="purchasePlanWithOlk(1000, 0.18)">1,000 OLK</button>
          </div>
        </div>

        <div class="plan-card">
          <div><div class="plan-info-title">GPU Pro Miner</div><div class="plan-info-sub">+0.89 TH/s</div></div>
          <div class="plan-buy-buttons">
            <button class="btn-buy-plan" onclick="purchasePlan(0.5, 0.89)">0.5 TON</button>
            <button class="btn-buy-olk" onclick="purchasePlanWithOlk(5000, 0.89)">5,000 OLK</button>
          </div>
        </div>

        <div class="plan-card">
          <div><div class="plan-info-title">ASIC Mini Rig</div><div class="plan-info-sub">+1.78 TH/s</div></div>
          <div class="plan-buy-buttons">
            <button class="btn-buy-plan" onclick="purchasePlan(1.0, 1.78)">1.0 TON</button>
            <button class="btn-buy-olk" onclick="purchasePlanWithOlk(10000, 1.78)">10,000 OLK</button>
          </div>
        </div>

        <div class="plan-card">
          <div><div class="plan-info-title">Titan Quantum Rig</div><div class="plan-info-sub">+4.46 TH/s</div></div>
          <div class="plan-buy-buttons">
            <button class="btn-buy-plan" onclick="purchasePlan(2.5, 4.46)">2.5 TON</button>
            <button class="btn-buy-olk" onclick="purchasePlanWithOlk(25000, 4.46)">25,000 OLK</button>
          </div>
        </div>

        <div class="plan-card">
          <div><div class="plan-info-title">Enterprise Mining Node</div><div class="plan-info-sub">+8.91 TH/s</div></div>
          <div class="plan-buy-buttons">
            <button class="btn-buy-plan" onclick="purchasePlan(5.0, 8.91)">5.0 TON</button>
            <button class="btn-buy-olk" onclick="purchasePlanWithOlk(50000, 8.91)">50,000 OLK</button>
          </div>
        </div>

        <div class="plan-card" style="border: 1.5px solid var(--gold-neon);">
          <div><div class="plan-info-title" style="color:var(--gold-neon);">Apex VIP Supercluster</div><div class="plan-info-sub" style="color:var(--gold-neon);">+17.82 TH/s</div></div>
          <div class="plan-buy-buttons">
            <button class="btn-buy-plan" style="background:linear-gradient(135deg, #0284c7, #0ea5e9);" onclick="purchasePlan(10.0, 17.82)">10.0 TON</button>
            <button class="btn-buy-olk" onclick="purchasePlanWithOlk(100000, 17.82)">100,000 OLK</button>
          </div>
        </div>
      </div>
    </div>

    <!-- تبويب المحفظة -->
    <div class="page-tab" id="tab-wallet">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--gold-neon); font-size:14px; display:flex; justify-content:space-between;">
          <span id="t-swap-title">💳 صرافة OLK إلى TON</span>
          <span style="font-size:11px; color:var(--cyan-neon); direction:ltr;">1 TON = 10,000 OLK</span>
        </div>
        <div class="convert-input-box">
          <input type="number" id="swap-folk-input" class="convert-input" placeholder="1000" oninput="calcSwap()">
          <button style="background:#1e3d6b; border:1px solid var(--gold-neon); color:var(--gold-neon); padding:5px 12px; border-radius:8px; font-size:11px; font-weight:800; cursor:pointer;" onclick="setMaxSwap()">MAX</button>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted);">
          <span id="t-swap-receive">ستحصل على:</span>
          <strong style="color:var(--green-neon); font-size:13px;" id="swap-preview">0.0000 TON</strong>
        </div>
        <button class="btn-main-action claim-state" style="margin-top:2px;" onclick="executeSwap()" id="t-btn-swap">تحويل الآن إلى رصيد TON</button>
        
        <hr style="border:0; border-top:1px solid var(--card-border); margin:4px 0;">
        
        <div style="font-weight:bold; color:var(--cyan-neon); font-size:14px;">
          <i class="fa-solid fa-money-bill-transfer"></i> <span id="t-withdraw-title">سحب TON إلى محفظتك</span>
        </div>

        <div class="convert-input-box">
          <input type="number" step="0.01" id="withdraw-amt-input" class="convert-input" placeholder="0.05">
          <span style="font-size:11px; color:#f87171;" id="t-min-withdraw">الحد الأدنى: 0.05 TON</span>
        </div>

        <div style="display:flex; flex-direction:column; gap:4px;">
          <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted);">
            <span id="t-dest-wallet-lbl">عنوان محفظة السحب (TON / Gram):</span>
            <span style="color:var(--cyan-neon); cursor:pointer; font-weight:700;" onclick="useConnectedWalletAsDest()" id="t-btn-use-connected">استخدام المربوطة ⚡</span>
          </div>
          <div class="convert-input-box">
            <input type="text" id="custom-wallet-input" class="convert-input" placeholder="UQ... أو عنوان محفظتك">
          </div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
          <button class="btn-main-action" style="background:#059669;" onclick="depositDirect()"><i class="fa-solid fa-arrow-down"></i> <span id="t-btn-deposit">إيداع TON</span></button>
          <button class="btn-main-action" onclick="submitWithdraw()"><i class="fa-solid fa-arrow-up"></i> <span id="t-btn-withdraw">سحب TON</span></button>
        </div>
      </div>
    </div>

    <!-- تبويب الإحالات -->
    <div class="page-tab" id="tab-frens">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--cyan-neon); font-size:14px;"><i class="fa-solid fa-users"></i> <span id="t-frens-title">شبكة التعدين التشاركية</span></div>
        <div style="font-size:12px; color:#cbd5e1; line-height:1.6;" id="t-frens-desc">
          شارك رابط جهازك واحصل على <strong>70 OLK</strong> فور قيام صديقك بالاشتراك في القنوات وتشغيل أول جلسة تعدين!
        </div>

        <button class="btn-main-action" onclick="copyInvite()"><i class="fa-solid fa-copy"></i> <span id="t-btn-copy-invite">نسخ رابط الدعوة الخاص بي</span></button>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:8px;">
          <div style="background:#081324; border:1px solid var(--card-border); border-radius:12px; padding:10px; text-align:center;">
            <div style="font-size:11px; color:var(--text-muted);" id="t-total-invites-lbl">إجمالي الإحالات</div>
            <div style="font-size:18px; font-weight:900; color:#fff; margin-top:4px;" id="ref-count-val">0</div>
          </div>
          <div style="background:#081324; border:1px solid var(--card-border); border-radius:12px; padding:10px; text-align:center;">
            <div style="font-size:11px; color:var(--text-muted);" id="t-total-ref-earnings-lbl">أرباح الإحالات</div>
            <div style="font-size:18px; font-weight:900; color:var(--gold-neon); margin-top:4px;" id="ref-earned-val">0 OLK</div>
          </div>
        </div>

        <hr style="border:0; border-top:1px solid var(--card-border); margin:6px 0;">

        <div style="font-weight:bold; color:#fff; font-size:13px; display:flex; justify-content:space-between;">
          <span id="t-invited-friends-lbl">الأصدقاء المدعوون</span>
          <span style="font-size:11px; color:var(--text-muted);" id="ref-list-count-text">0 أصدقاء</span>
        </div>

        <div id="referred-users-list" style="display:flex; flex-direction:column; gap:6px; max-height:220px; overflow-y:auto;">
          <div style="font-size:12px; color:var(--text-muted); text-align:center; padding:10px;">لا توجد إحالات مسجلة بعد.</div>
        </div>
      </div>
    </div>

    <!-- تبويب المهام -->
    <div class="page-tab" id="tab-tasks">
      <div class="tasks-horizontal-nav">
        <button class="tasks-subtab-btn active" onclick="switchTasksSubtab('channels', this)"><i class="fa-solid fa-bullhorn"></i> <span id="t-subtab-channels">القنوات</span></button>
        <button class="tasks-subtab-btn" onclick="switchTasksSubtab('groups', this)"><i class="fa-solid fa-user-group"></i> <span id="t-subtab-groups">المجموعات</span></button>
        <button class="tasks-subtab-btn" onclick="switchTasksSubtab('bots', this)"><i class="fa-solid fa-robot"></i> <span id="t-subtab-bots">البوتات</span></button>
      </div>

      <div class="card-panel">
        <div class="tasks-view-content active" id="subtab-channels">
          <div style="font-weight:bold; color:var(--gold-neon); font-size:13px; margin-bottom:4px;"><i class="fa-solid fa-bullhorn"></i> <span id="t-channels-title">قنوات تيليجرام</span></div>
          <div id="dynamic-tasks-list" style="display:flex; flex-direction:column; gap:8px;"></div>
        </div>

        <div class="tasks-view-content" id="subtab-groups">
          <div style="font-weight:bold; color:var(--green-neon); font-size:13px; margin-bottom:4px;"><i class="fa-solid fa-user-group"></i> <span id="t-groups-title">مجموعات تيليجرام</span></div>
          <div id="dynamic-groups-list" style="display:flex; flex-direction:column; gap:8px;"></div>
        </div>

        <div class="tasks-view-content" id="subtab-bots">
          <div style="font-weight:bold; color:var(--cyan-neon); font-size:13px; margin-bottom:4px;"><i class="fa-solid fa-robot"></i> <span id="t-bots-title">بوتات تيليجرام</span></div>
          <div id="dynamic-bot-tasks-list" style="display:flex; flex-direction:column; gap:8px;"></div>
        </div>
      </div>
    </div>
  </div>

  <div class="bottom-bar">
    <div class="nav-btn active" onclick="switchTab('mining', this)"><i class="fa-solid fa-pickaxe"></i><span id="t-nav-mining">التعدين</span></div>
    <div class="nav-btn" onclick="switchTab('miners', this)"><i class="fa-solid fa-bolt"></i><span id="t-nav-rigs">الأجهزة</span></div>
    <div class="nav-btn" onclick="switchTab('wallet', this)"><i class="fa-solid fa-wallet"></i><span id="t-nav-wallet">المحفظة</span></div>
    <div class="nav-btn" onclick="switchTab('frens', this)"><i class="fa-solid fa-users"></i><span id="t-nav-frens">الأصدقاء</span></div>
    <div class="nav-btn" onclick="switchTab('tasks', this)"><i class="fa-solid fa-clipboard-list"></i><span id="t-nav-tasks">المهام</span></div>
  </div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) { tg.ready(); tg.expand(); }

    const urlParams = new URLSearchParams(window.location.search);
    let userId = tg?.initDataUnsafe?.user?.id || urlParams.get('user_id') || 1932161126;

    function getDeviceFingerprint() {
      const nav = window.navigator;
      const screen = window.screen;
      let str = [
        nav.userAgent,
        nav.language,
        screen.colorDepth,
        screen.width + 'x' + screen.height,
        new Date().getTimezoneOffset()
      ].join('###');
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
      }
      return 'FP_' + Math.abs(hash);
    }
    const currentFingerprint = getDeviceFingerprint();

    let currentLang = localStorage.getItem("olk_lang") || "ar";
    const i18n = {
      ar: {
        dir: "rtl",
        btnLang: "EN",
        olkBal: "رصيد OLK الأساسي:",
        tonBal: "رصيد TON (Gram):",
        miningEarnings: "أرباح جلسة التعدين الحالية:",
        btnMine: "تشغيل جلسة التعدين",
        btnMineActive: "التعدين يعمل الآن تلقائياً...",
        btnClaim: "المطالبة بأرباح الجلسة وتحديث المحفظة",
        statusReady: "متوقف (جاهز لبدء جلسة جديدة)",
        statusActive: "جلسة التعدين نشطة الآن",
        statusClaim: "اكتملت الجلسة! طالب بأرباحك الآن",
        plansTitle: "باقات أجهزة التعدين",
        swapTitle: "💳 صرافة OLK إلى TON",
        swapReceive: "ستحصل على:",
        btnSwap: "تحويل الآن إلى رصيد TON",
        withdrawTitle: "سحب TON إلى محفظتك",
        destWalletLbl: "عنوان محفظة السحب (TON / Gram):",
        btnUseConnected: "استخدام المربوطة ⚡",
        minWithdraw: "الحد الأدنى: 0.05 TON",
        btnDeposit: "إيداع TON",
        btnWithdraw: "سحب TON",
        frensTitle: "شبكة التعدين التشاركية",
        frensDesc: "شارك رابط جهازك واحصل على 70 OLK فور قيام صديقك بالاشتراك في القنوات وتشغيل أول جلسة تعدين!",
        btnCopyInvite: "نسخ رابط الدعوة الخاص بي",
        totalInvitesLbl: "إجمالي الإحالات",
        totalRefEarningsLbl: "أرباح الإحالات",
        invitedFriendsLbl: "الأصدقاء المدعوون",
        promoTitle: "رمز الهدية الترويجي (Promo Code)",
        promoBtn: "تفعيل ⚡",
        subtabChannels: "القنوات",
        subtabGroups: "المجموعات",
        subtabBots: "البوتات",
        channelsTitle: "قنوات تيليجرام",
        groupsTitle: "مجموعات تيليجرام",
        botsTitle: "بوتات تيليجرام",
        navMining: "التعدين",
        navRigs: "الأجهزة",
        navWallet: "المحفظة",
        navFrens: "الأصدقاء",
        navTasks: "المهام",
        btnConnect: "اتصال",
        btnConnected: "متصل ✅",
        btnJoin: "انضمام",
        btnVerify: "تحقق",
        btnClaimReward: "استلام",
        btnStartBot: "دخول البوت",
        btnDone: "مكتملة ✅",
        lockTitle: "📢 خطوة أخيرة للتفعيل!",
        lockDesc: "لتفعيل محطة التعدين السحابية، يجب الانضمام إلى القناتين الرسمية والإثباتات:",
        lockJoin1: "📢 انضم للقناة الرسمية",
        lockJoin2: "🧾 انضم لقناة الإثباتات",
        lockVerify: "تحقق وتفعيل الآن",
        bannedTitle: "⛔ تم حظر هذا الحساب!"
      },
      en: {
        dir: "ltr",
        btnLang: "عربي",
        olkBal: "Main OLK Balance:",
        tonBal: "TON (Gram) Balance:",
        miningEarnings: "Current Session Rewards:",
        btnMine: "Start Mining Session",
        btnMineActive: "Mining in progress...",
        btnClaim: "Claim Mining Rewards",
        statusReady: "Idle (Ready to Start)",
        statusActive: "Mining Session Active",
        statusClaim: "Completed! Claim your rewards",
        plansTitle: "Mining Rig Bundles",
        swapTitle: "💳 Swap OLK to TON",
        swapReceive: "You will receive:",
        btnSwap: "Convert to TON Balance",
        withdrawTitle: "Withdraw TON to Wallet",
        destWalletLbl: "Destination Wallet (TON / Gram):",
        btnUseConnected: "Use Connected ⚡",
        minWithdraw: "Minimum: 0.05 TON",
        btnDeposit: "Deposit TON",
        btnWithdraw: "Withdraw TON",
        frensTitle: "Collaborative Mining Network",
        frensDesc: "Share your referral link and get 70 OLK once your invited friend joins the channels and runs their first session!",
        btnCopyInvite: "Copy My Invite Link",
        totalInvitesLbl: "Total Invites",
        totalRefEarningsLbl: "Referral Earnings",
        invitedFriendsLbl: "Invited Friends",
        promoTitle: "Promo Code Gift",
        promoBtn: "Redeem ⚡",
        subtabChannels: "Channels",
        subtabGroups: "Groups",
        subtabBots: "Bots",
        channelsTitle: "Telegram Channels",
        groupsTitle: "Telegram Groups",
        botsTitle: "Telegram Bots",
        navMining: "Mining",
        navRigs: "Rigs",
        navWallet: "Wallet",
        navFrens: "Frens",
        navTasks: "Tasks",
        btnConnect: "Connect",
        btnConnected: "Connected ✅",
        btnJoin: "Join",
        btnVerify: "Verify",
        btnClaimReward: "Claim",
        btnStartBot: "Open Bot",
        btnDone: "Completed ✅",
        lockTitle: "📢 One Last Step!",
        lockDesc: "To activate the mining node, you must join both the official and proofs channels:",
        lockJoin1: "📢 Join Official Channel",
        lockJoin2: "🧾 Join Proofs Channel",
        lockVerify: "Verify & Activate",
        bannedTitle: "⛔ Account Suspended!"
      }
    };

    function applyLanguage(lang) {
      currentLang = lang;
      localStorage.setItem("olk_lang", lang);
      const t = i18n[lang];
      document.getElementById("html-root").dir = t.dir;
      document.getElementById("lang-btn-text").innerText = t.btnLang;

      document.getElementById("t-folk-bal-lbl").innerText = t.olkBal;
      document.getElementById("t-ton-bal-lbl").innerText = t.tonBal;
      document.getElementById("t-mining-earnings-lbl").innerText = t.miningEarnings;
      document.getElementById("t-plans-title").innerText = t.plansTitle;
      document.getElementById("t-swap-title").innerText = t.swapTitle;
      document.getElementById("t-swap-receive").innerText = t.swapReceive;
      document.getElementById("t-btn-swap").innerText = t.btnSwap;
      document.getElementById("t-withdraw-title").innerText = t.withdrawTitle;
      document.getElementById("t-dest-wallet-lbl").innerText = t.destWalletLbl;
      document.getElementById("t-btn-use-connected").innerText = t.btnUseConnected;
      document.getElementById("t-min-withdraw").innerText = t.minWithdraw;
      document.getElementById("t-btn-deposit").innerText = t.btnDeposit;
      document.getElementById("t-btn-withdraw").innerText = t.btnWithdraw;
      document.getElementById("t-frens-title").innerText = t.frensTitle;
      document.getElementById("t-frens-desc").innerText = t.frensDesc;
      document.getElementById("t-btn-copy-invite").innerText = t.btnCopyInvite;
      document.getElementById("t-total-invites-lbl").innerText = t.totalInvitesLbl;
      document.getElementById("t-total-ref-earnings-lbl").innerText = t.totalRefEarningsLbl;
      document.getElementById("t-invited-friends-lbl").innerText = t.invitedFriendsLbl;
      document.getElementById("t-promo-title").innerText = t.promoTitle;
      document.getElementById("t-promo-btn").innerText = t.promoBtn;
      document.getElementById("t-subtab-channels").innerText = t.subtabChannels;
      document.getElementById("t-subtab-groups").innerText = t.subtabGroups;
      document.getElementById("t-subtab-bots").innerText = t.subtabBots;
      document.getElementById("t-channels-title").innerText = t.channelsTitle;
      document.getElementById("t-groups-title").innerText = t.groupsTitle;
      document.getElementById("t-bots-title").innerText = t.botsTitle;
      document.getElementById("t-nav-mining").innerText = t.navMining;
      document.getElementById("t-nav-rigs").innerText = t.navRigs;
      document.getElementById("t-nav-wallet").innerText = t.navWallet;
      document.getElementById("t-nav-frens").innerText = t.navFrens;
      document.getElementById("t-nav-tasks").innerText = t.navTasks;
      document.getElementById("t-lock-title").innerText = t.lockTitle;
      document.getElementById("t-lock-join-1").innerText = t.lockJoin1;
      document.getElementById("t-lock-join-2").innerText = t.lockJoin2;
      document.getElementById("t-lock-verify").innerText = t.lockVerify;
      document.getElementById("t-banned-title").innerText = t.bannedTitle;

      evaluateSessionState();
    }

    function toggleLanguage() {
      applyLanguage(currentLang === "ar" ? "en" : "ar");
    }

    let appOlk = 0.0;
    let appTon = 0.0;
    let speed = 0.21;
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
      const t = i18n[currentLang];
      if (wallet) {
        try {
          connectedWallet = TON_CONNECT_UI.toUserFriendlyAddress(wallet.account.address);
        } catch(e) {
          connectedWallet = wallet.account.address;
        }
        document.getElementById("wallet-addr-text").innerText = connectedWallet.slice(0, 4) + '...' + connectedWallet.slice(-4);
        const b = document.getElementById("wallet-badge-btn");
        b.innerText = t.btnConnected;
        b.classList.add("connected");

        await fetch("/api/save_wallet", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, address: connectedWallet, fingerprint: currentFingerprint })
        });
      } else {
        connectedWallet = null;
        document.getElementById("wallet-addr-text").innerText = currentLang === "ar" ? "اضغط لربط المحفظة مباشرة" : "Click to connect wallet";
        const b = document.getElementById("wallet-badge-btn");
        b.innerText = t.btnConnect;
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

    function useConnectedWalletAsDest() {
      if (!connectedWallet) {
        alert(currentLang === "ar" ? "❌ لم تقم بربط محفظة بعد!" : "❌ No connected wallet found!");
        return;
      }
      document.getElementById("custom-wallet-input").value = connectedWallet;
    }

    async function redeemPromoCode() {
      const code = document.getElementById("promo-code-input").value.trim();
      if (!code) {
        alert(currentLang === "ar" ? "⚠️ يرجى كتابة الرمز الترويجي أولاً!" : "⚠️ Please enter the promo code!");
        return;
      }
      try {
        const res = await fetch("/api/redeem_promo", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, code: code, fingerprint: currentFingerprint })
        });
        const data = await res.json();
        alert(data.msg);
        if (data.ok) {
          appOlk = data.olk_balance;
          document.getElementById("olk-bal-val").innerText = appOlk.toFixed(2) + " OLK";
          document.getElementById("promo-code-input").value = "";
        }
      } catch (e) {
        alert("Server error");
      }
    }

    async function loadData() {
      try {
        const res = await fetch(`/api/get_user?user_id=${userId}&fp=${currentFingerprint}`);
        const data = await res.json();
        if (data.banned) {
          document.getElementById("ban-reason-text").innerText = (currentLang === "ar" ? "سبب الحظر: " : "Reason: ") + (data.ban_reason || "");
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
          speed = data.mining_speed || 0.21;
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
            b.innerText = i18n[currentLang].btnConnected;
            b.classList.add("connected");
          }
          evaluateSessionState();
          loadTasks();
          loadReferralsData();
        }
      } catch (e) {
        console.error("Load failed", e);
      }
    }

    async function loadReferralsData() {
      try {
        const res = await fetch(`/api/get_referrals?user_id=${userId}`);
        const data = await res.json();
        if (data.ok) {
          document.getElementById("ref-count-val").innerText = data.total_count;
          document.getElementById("ref-earned-val").innerText = (data.earned_olk || 0).toFixed(0) + " OLK";
          document.getElementById("ref-list-count-text").innerText = `${data.total_count} ${currentLang === "ar" ? "أصدقاء" : "frens"}`;

          const listEl = document.getElementById("referred-users-list");
          listEl.innerHTML = "";

          if (!data.referrals || data.referrals.length === 0) {
            listEl.innerHTML = `<div style="font-size:12px; color:var(--text-muted); text-align:center; padding:10px;">${currentLang === "ar" ? "لا توجد إحالات مسجلة بعد." : "No referrals yet."}</div>`;
            return;
          }

          data.referrals.forEach(ref => {
            const row = document.createElement("div");
            row.style.display = "flex";
            row.style.justifyContent = "space-between";
            row.style.alignItems = "center";
            row.style.background = "#081324";
            row.style.border = "1px solid var(--card-border)";
            row.style.borderRadius = "10px";
            row.style.padding = "8px 12px";

            const statusBadge = ref.is_active 
              ? `<span style="color:var(--green-neon); font-size:11px; font-weight:800;">+70 OLK ✅</span>`
              : `<span style="color:#eab308; font-size:11px; font-weight:700;">${currentLang === "ar" ? "قيد التفعيل" : "Pending"} ⏳</span>`;

            row.innerHTML = `
              <div style="display:flex; align-items:center; gap:8px;">
                <i class="fa-solid fa-circle-user" style="font-size:18px; color:var(--cyan-neon);"></i>
                <div style="display:flex; flex-direction:column;">
                  <span style="font-size:12px; font-weight:800; color:#fff;">${ref.name || 'User'}</span>
                  <span style="font-size:10px; color:var(--text-muted); direction:ltr; text-align:left;">${ref.username ? '@' + ref.username : 'ID: ' + ref.user_id}</span>
                </div>
              </div>
              <div>${statusBadge}</div>
            `;
            listEl.appendChild(row);
          });
        }
      } catch (e) {
        console.error("Referrals load failed", e);
      }
    }

    function switchTasksSubtab(target, btn) {
      document.querySelectorAll(".tasks-subtab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tasks-view-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("subtab-" + target).classList.add("active");
    }

    async function loadTasks() {
      try {
        const t = i18n[currentLang];
        const res = await fetch(`/api/get_tasks?user_id=${userId}`);
        const data = await res.json();
        
        const container = document.getElementById("dynamic-tasks-list");
        container.innerHTML = "";
        if (!data.tasks || data.tasks.length === 0) {
          container.innerHTML = `<div style="font-size:12px; color:var(--text-muted); text-align:center;">${currentLang === "ar" ? "لا توجد قنوات حالياً." : "No channels available."}</div>`;
        } else {
          data.tasks.forEach(task => {
            const isDone = data.completed_ids.includes(task.id);
            const countText = task.max_users > 0 ? ` (${task.current_completions || 0}/${task.max_users})` : '';
            const div = document.createElement("div");
            div.className = "plan-card";
            div.innerHTML = `
              <div>
                <div class="plan-info-title">${task.title}</div>
                <div class="plan-info-sub" style="color:var(--gold-neon);">+${task.reward} OLK <span style="color:#94a3b8; font-size:10px;">${countText}</span></div>
              </div>
              <div style="display:flex; gap:6px;">
                <button class="btn-buy-plan" onclick="window.open('${task.link}', '_blank')">${t.btnJoin}</button>
                ${isDone 
                  ? `<button class="btn-buy-plan" style="background:#475569; cursor:default;" disabled>${t.btnDone}</button>`
                  : `<button class="btn-buy-plan" style="background:#10b981;" onclick="verifyTask(${task.id})">${t.btnVerify}</button>`
                }
              </div>
            `;
            container.appendChild(div);
          });
        }

        const groupContainer = document.getElementById("dynamic-groups-list");
        groupContainer.innerHTML = "";
        if (!data.group_tasks || data.group_tasks.length === 0) {
          groupContainer.innerHTML = `<div style="font-size:12px; color:var(--text-muted); text-align:center;">${currentLang === "ar" ? "لا توجد مجموعات حالياً." : "No groups available."}</div>`;
        } else {
          data.group_tasks.forEach(task => {
            const isDone = (data.completed_group_ids || []).includes(task.id);
            const countText = task.max_users > 0 ? ` (${task.current_completions || 0}/${task.max_users})` : '';
            const div = document.createElement("div");
            div.className = "plan-card";
            div.innerHTML = `
              <div>
                <div class="plan-info-title">${task.title}</div>
                <div class="plan-info-sub" style="color:var(--green-neon);">+${task.reward} OLK <span style="color:#94a3b8; font-size:10px;">${countText}</span></div>
              </div>
              <div style="display:flex; gap:6px;">
                <button class="btn-buy-plan" onclick="window.open('${task.link}', '_blank')">${t.btnJoin}</button>
                ${isDone 
                  ? `<button class="btn-buy-plan" style="background:#475569; cursor:default;" disabled>${t.btnDone}</button>`
                  : `<button class="btn-buy-plan" style="background:#10b981;" onclick="verifyGroupTask(${task.id})">${t.btnVerify}</button>`
                }
              </div>
            `;
            groupContainer.appendChild(div);
          });
        }

        const botContainer = document.getElementById("dynamic-bot-tasks-list");
        botContainer.innerHTML = "";
        if (!data.bot_tasks || data.bot_tasks.length === 0) {
          botContainer.innerHTML = `<div style="font-size:12px; color:var(--text-muted); text-align:center;">${currentLang === "ar" ? "لا توجد بوتات حالياً." : "No bots available."}</div>`;
        } else {
          data.bot_tasks.forEach(task => {
            const isDone = (data.completed_bot_ids || []).includes(task.id);
            const countText = task.max_users > 0 ? ` (${task.current_completions || 0}/${task.max_users})` : '';
            const div = document.createElement("div");
            div.className = "plan-card";
            div.innerHTML = `
              <div>
                <div class="plan-info-title">${task.title}</div>
                <div class="plan-info-sub" style="color:var(--cyan-neon);">+${task.reward} OLK <span style="color:#94a3b8; font-size:10px;">${countText}</span></div>
              </div>
              <div style="display:flex; gap:6px;">
                <button class="btn-buy-plan" onclick="window.open('${task.link}', '_blank')">${t.btnStartBot}</button>
                ${isDone 
                  ? `<button class="btn-buy-plan" style="background:#475569; cursor:default;" disabled>${t.btnDone}</button>`
                  : `<button class="btn-buy-plan" style="background:#0284c7;" onclick="verifyBotTask(${task.id})">${t.btnClaimReward}</button>`
                }
              </div>
            `;
            botContainer.appendChild(div);
          });
        }

      } catch (e) {
        console.error("Tasks load failed", e);
      }
    }

    function evaluateSessionState() {
      const t = i18n[currentLang];
      const now = Math.floor(Date.now() / 1000);
      const elapsed = Math.max(0, now - sessionStartTs);

      const btn = document.getElementById("btn-session-control");
      const dot = document.getElementById("mining-status-dot");
      const statusText = document.getElementById("mining-status-text");

      if (sessionActive && elapsed < EIGHT_HOURS_SEC) {
        sessionClaimReady = false;
        dot.classList.add("active");
        statusText.innerText = t.statusActive;

        btn.classList.remove("claim-state");
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${t.btnMineActive}`;
      } else if (sessionActive && elapsed >= EIGHT_HOURS_SEC) {
        sessionClaimReady = true;
        dot.classList.remove("active");
        statusText.innerText = t.statusClaim;

        btn.classList.add("claim-state");
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-hand-holding-dollar"></i> ${t.btnClaim}`;
      } else {
        sessionClaimReady = false;
        dot.classList.remove("active");
        statusText.innerText = t.statusReady;

        btn.classList.remove("claim-state");
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-power-off"></i> <span>${t.btnMine}</span>`;
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
      const btn = document.getElementById("btn-session-control");
      btn.disabled = true;

      if (sessionClaimReady) {
        try {
          const res = await fetch("/api/claim_session_rewards", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, amount: currentUnclaimed, fingerprint: currentFingerprint })
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
            alert(`🎉 +${data.claimed.toFixed(2)} OLK!`);
          } else {
            alert(data.msg || "Error");
            btn.disabled = false;
          }
        } catch (err) {
          alert("Server error");
          btn.disabled = false;
        }
      } else {
        try {
          const res = await fetch("/api/start_mining_session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, fingerprint: currentFingerprint })
          });
          const data = await res.json();
          if (data.ok) {
            sessionActive = true;
            sessionStartTs = data.session_start_timestamp;
            evaluateSessionState();
            alert(currentLang === "ar" ? "🚀 تم تشغيل جهاز التعدين بنجاح!" : "🚀 Mining started successfully!");
          } else {
            alert(data.msg || "Error starting session");
            btn.disabled = false;
          }
        } catch (err) {
          alert("Server connection error");
          btn.disabled = false;
        }
      }
    }

    async function purchasePlan(costTon, speedGain) {
      if (!connectedWallet) {
        alert(currentLang === "ar" ? "❌ يرجى ربط محفظتك أولاً للدفع المباشر!" : "❌ Please connect your wallet first to proceed!");
        handleWalletClick();
        return;
      }

      const nanoTons = Math.round(costTon * 1e9).toString();
      const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 360,
        messages: [{
          address: "PROJECT_TON_WALLET_PLACEHOLDER",
          amount: nanoTons
        }]
      };

      try {
        const result = await tonConnectUI.sendTransaction(transaction);
        if (result) {
          const res = await fetch("/api/upgrade_rig_ton_direct", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_id: userId,
              cost_ton: costTon,
              speed_gain: speedGain,
              fingerprint: currentFingerprint
            })
          });
          const data = await res.json();
          if (data.ok) {
            speed = data.mining_speed;
            document.getElementById("speed-display").innerText = speed.toFixed(2) + " TH/s";
            alert(currentLang === "ar" 
              ? `🎉 تم الدفع بنجاح وترقية جهاز التعدين! السرعة الجديدة: ${speed.toFixed(2)} TH/s` 
              : `🎉 Payment successful! New speed: ${speed.toFixed(2)} TH/s`);
          } else {
            alert(data.msg || "حدث خطأ أثناء حفظ الترقية");
          }
        }
      } catch (e) {
        alert(currentLang === "ar" ? "❌ تم إلغاء عملية الدفع من المحفظة." : "❌ Payment canceled in wallet.");
      }
    }

    async function purchasePlanWithOlk(costOlk, speedGain) {
      if (appOlk < costOlk) {
        alert(currentLang === "ar" 
          ? `⚠️ رصيدك من OLK غير كافٍ! يلزمك ${costOlk.toLocaleString()} OLK للمتابعة.` 
          : `⚠️ Insufficient OLK balance! You need ${costOlk.toLocaleString()} OLK.`);
        return;
      }

      const confirmMsg = currentLang === "ar" 
        ? `هل تريد ترقية الجهاز بمقدار +${speedGain} TH/s مقابل ${costOlk.toLocaleString()} OLK؟`
        : `Upgrade rig by +${speedGain} TH/s for ${costOlk.toLocaleString()} OLK?`;

      if (!confirm(confirmMsg)) return;

      try {
        const res = await fetch("/api/upgrade_rig_olk", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: userId,
            cost_olk: costOlk,
            speed_gain: speedGain,
            fingerprint: currentFingerprint
          })
        });
        const data = await res.json();
        if (data.ok) {
          appOlk = data.olk_balance;
          speed = data.mining_speed;
          document.getElementById("olk-bal-val").innerText = appOlk.toFixed(2) + " OLK";
          document.getElementById("speed-display").innerText = speed.toFixed(2) + " TH/s";
          alert(currentLang === "ar" 
            ? `🎉 تم خصم ${costOlk.toLocaleString()} OLK وترقية جهاز التعدين بنجاح! السرعة الآن: ${speed.toFixed(2)} TH/s` 
            : `🎉 Upgraded successfully! Current speed: ${speed.toFixed(2)} TH/s`);
        } else {
          alert(data.msg || "حدث خطأ أثناء الترقية");
        }
      } catch (e) {
        alert("Server error");
      }
    }

    function calcSwap() {
      const v = parseFloat(document.getElementById("swap-folk-input").value) || 0;
      document.getElementById("swap-preview").innerText = (v / 10000).toFixed(4) + " TON";
    }

    function setMaxSwap() {
      document.getElementById("swap-folk-input").value = Math.floor(appOlk);
      calcSwap();
    }

    async function executeSwap() {
      const amt = parseFloat(document.getElementById("swap-folk-input").value) || 0;
      if (amt <= 0 || amt > appOlk) {
        alert(currentLang === "ar" ? "⚠️ يرجى إدخال كمية OLK صالحة!" : "⚠️ Invalid OLK amount!");
        return;
      }
      const res = await fetch("/api/convert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, amount: amt, fingerprint: currentFingerprint })
      });
      const data = await res.json();
      if (data.ok) {
        appOlk = data.olk_balance;
        appTon = data.ton_balance;
        document.getElementById("olk-bal-val").innerText = appOlk.toFixed(2) + " OLK";
        document.getElementById("ton-bal-val").innerText = appTon.toFixed(4) + " TON";
        document.getElementById("swap-folk-input").value = "";
        calcSwap();
        alert(currentLang === "ar" ? `✅ تم التحويل بنجاح!` : `✅ Converted successfully!`);
      } else {
        alert(data.msg);
      }
    }

    async function depositDirect() {
      if (!connectedWallet) {
        alert(currentLang === "ar" ? "❌ يرجى ربط المحفظة أولاً!" : "❌ Please connect wallet first!");
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
            body: JSON.stringify({ user_id: userId, amount_ton: 0.1, fingerprint: currentFingerprint })
          });
          alert(currentLang === "ar" ? "🎉 تم تأكيد إيداع 0.1 TON بنجاح!" : "🎉 0.1 TON deposit confirmed!");
        }
      } catch (e) {
        alert(currentLang === "ar" ? "❌ تم إلغاء الإيداع." : "❌ Deposit canceled.");
      }
    }

    async function submitWithdraw() {
      const amt = parseFloat(document.getElementById("withdraw-amt-input").value) || 0;
      if (amt < 0.05 || amt > appTon) {
        alert(currentLang === "ar" ? "⚠️ المبلغ غير صالح! الحد الأدنى هو 0.05 TON" : "⚠️ Invalid amount! Minimum is 0.05 TON");
        return;
      }

      let destWallet = document.getElementById("custom-wallet-input").value.trim();
      if (!destWallet && connectedWallet) {
        destWallet = connectedWallet;
      }

      if (!destWallet) {
        alert(currentLang === "ar" ? "❌ يرجى كتابة عنوان محفظة السحب أو ربط محفظتك أولاً!" : "❌ Please enter a destination wallet address or connect your wallet!");
        return;
      }

      const res = await fetch("/api/withdraw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, address: destWallet, amount_ton: amt, fingerprint: currentFingerprint })
      });
      const data = await res.json();
      if (data.ok) {
        appTon = data.remaining_ton;
        document.getElementById("ton-bal-val").innerText = appTon.toFixed(4) + " TON";
        document.getElementById("withdraw-amt-input").value = "";
        alert(currentLang === "ar" ? `✅ تم إرسال طلب السحب بنجاح إلى المحفظة:\n${destWallet}` : `✅ Withdrawal request submitted to:\n${destWallet}`);
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
      alert(currentLang === "ar" ? "✅ تم نسخ رابط الدعوة الخاص بك!" : "✅ Invite link copied!");
    }

    async function verifyTask(taskId) {
      const res = await fetch("/api/verify_channel_task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, task_id: taskId, fingerprint: currentFingerprint })
      });
      const data = await res.json();
      alert(data.msg);
      if (data.ok) {
        appOlk += data.reward;
        document.getElementById("olk-bal-val").innerText = appOlk.toFixed(2) + " OLK";
        loadTasks();
      }
    }

    async function verifyGroupTask(taskId) {
      const res = await fetch("/api/verify_group_task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, task_id: taskId, fingerprint: currentFingerprint })
      });
      const data = await res.json();
      alert(data.msg);
      if (data.ok) {
        appOlk += data.reward;
        document.getElementById("olk-bal-val").innerText = appOlk.toFixed(2) + " OLK";
        loadTasks();
      }
    }

    async function verifyBotTask(taskId) {
      const res = await fetch("/api/verify_bot_task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, task_id: taskId, fingerprint: currentFingerprint })
      });
      const data = await res.json();
      alert(data.msg);
      if (data.ok) {
        appOlk += data.reward;
        document.getElementById("olk-bal-val").innerText = appOlk.toFixed(2) + " OLK";
        loadTasks();
      }
    }

    applyLanguage(currentLang);
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
            username TEXT,
            first_name TEXT,
            phone_number TEXT,
            olk_balance DOUBLE PRECISION DEFAULT 0.0,
            ton_balance DOUBLE PRECISION DEFAULT 0.0,
            last_claim BIGINT DEFAULT 0,
            referred_by BIGINT DEFAULT NULL,
            ref_reward_claimed INTEGER DEFAULT 0,
            mining_speed DOUBLE PRECISION DEFAULT 0.21,
            miner_level INTEGER DEFAULT 1,
            last_mining_timestamp BIGINT DEFAULT 0,
            session_start_timestamp BIGINT DEFAULT 0,
            session_active INTEGER DEFAULT 0,
            tasks_completed TEXT DEFAULT '[]',
            group_tasks_completed TEXT DEFAULT '[]',
            bot_tasks_completed TEXT DEFAULT '[]',
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
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='username') THEN
                ALTER TABLE users ADD COLUMN username TEXT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='first_name') THEN
                ALTER TABLE users ADD COLUMN first_name TEXT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='session_start_timestamp') THEN
                ALTER TABLE users ADD COLUMN session_start_timestamp BIGINT DEFAULT 0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='session_active') THEN
                ALTER TABLE users ADD COLUMN session_active INTEGER DEFAULT 0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='group_tasks_completed') THEN
                ALTER TABLE users ADD COLUMN group_tasks_completed TEXT DEFAULT '[]';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='bot_tasks_completed') THEN
                ALTER TABLE users ADD COLUMN bot_tasks_completed TEXT DEFAULT '[]';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='device_fingerprint') THEN
                ALTER TABLE users ADD COLUMN device_fingerprint TEXT DEFAULT NULL;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='ip_address') THEN
                ALTER TABLE users ADD COLUMN ip_address TEXT DEFAULT NULL;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='is_whitelisted') THEN
                ALTER TABLE users ADD COLUMN is_whitelisted INTEGER DEFAULT 0;
            END IF;
        END $$;
        """)

        await conn.execute("""
            UPDATE users SET mining_speed = 0.21 WHERE miner_level = 1;
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
        CREATE TABLE IF NOT EXISTS promo_codes (
            id SERIAL PRIMARY KEY,
            code TEXT UNIQUE,
            reward DOUBLE PRECISION DEFAULT 100.0,
            max_uses INTEGER DEFAULT 0,
            current_uses INTEGER DEFAULT 0,
            created_at BIGINT DEFAULT 0,
            is_active INTEGER DEFAULT 1
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS promo_claims (
            user_id BIGINT,
            code_id INTEGER,
            claimed_at BIGINT,
            PRIMARY KEY (user_id, code_id)
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_tasks (
            id SERIAL PRIMARY KEY,
            title TEXT,
            channel_id TEXT,
            link TEXT,
            reward DOUBLE PRECISION DEFAULT 10.0,
            max_users INTEGER DEFAULT 0,
            current_completions INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_group_tasks (
            id SERIAL PRIMARY KEY,
            title TEXT,
            group_id TEXT,
            link TEXT,
            reward DOUBLE PRECISION DEFAULT 10.0,
            max_users INTEGER DEFAULT 0,
            current_completions INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_bot_tasks (
            id SERIAL PRIMARY KEY,
            title TEXT,
            link TEXT,
            reward DOUBLE PRECISION DEFAULT 10.0,
            max_users INTEGER DEFAULT 0,
            current_completions INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        );
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

async def check_multi_account_fraud(conn, user_id: int, fp: str, ip: str, wallet: str = None) -> tuple[bool, str]:
    u_row = await conn.fetchrow("SELECT is_whitelisted FROM users WHERE user_id = $1", user_id)
    if u_row and u_row["is_whitelisted"] == 1:
        return False, ""

    if fp:
        multi_fp = await conn.fetchval(
            "SELECT user_id FROM users WHERE device_fingerprint = $1 AND user_id != $2 AND is_whitelisted = 0 LIMIT 1",
            fp, user_id
        )
        if multi_fp:
            return True, "كشف حسابات متعددة على نفس الجهاز (Anti-Multi Device)"

    if wallet:
        multi_wallet = await conn.fetchval(
            "SELECT user_id FROM users WHERE saved_wallet = $1 AND user_id != $2 AND is_whitelisted = 0 LIMIT 1",
            wallet, user_id
        )
        if multi_wallet:
            return True, "كشف محفظة مستخدمة في أكثر من حساب (Anti-Multi Wallet)"

    return False, ""

async def check_user_channel_subscribed(user_id: int) -> bool:
    try:
        member1 = await bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
        if member1.status in ["left", "kicked"]:
            return False
    except Exception:
        pass

    try:
        member2 = await bot.get_chat_member(chat_id=PROOFS_CHANNEL, user_id=user_id)
        if member2.status in ["left", "kicked"]:
            return False
    except Exception:
        pass

    return True

async def api_manifest(request):
    return web.json_response(TON_MANIFEST)

async def api_save_wallet(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        address = str(data.get("address", "")).strip()
        friendly_address = raw_to_user_friendly(address)
        fp = str(data.get("fingerprint", ""))
        client_ip = request.headers.get("X-Forwarded-For", request.remote)

        async with db_pool.acquire() as conn:
            is_fraud, reason = await check_multi_account_fraud(conn, user_id, fp, client_ip, friendly_address)
            if is_fraud:
                await conn.execute("UPDATE users SET is_banned = 1, ban_reason = $1 WHERE user_id = $2", reason, user_id)
                return web.json_response({"ok": False, "msg": reason})

            await conn.execute("UPDATE users SET saved_wallet = $1, device_fingerprint = $2, ip_address = $3 WHERE user_id = $4",
                               friendly_address, fp, client_ip, user_id)

        return web.json_response({"ok": True, "address": friendly_address})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_redeem_promo(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        code = str(data.get("code", "")).strip().upper()
        now = int(time.time())

        if not code:
            return web.json_response({"ok": False, "msg": "يرجى إدخال الرمز"})

        async with db_pool.acquire() as conn:
            promo = await conn.fetchrow("SELECT * FROM promo_codes WHERE code = $1 AND is_active = 1", code)
            if not promo:
                return web.json_response({"ok": False, "msg": "❌ الكود غير صحيح أو منتهي الصلاحية!"})

            if promo["max_uses"] > 0 and promo["current_uses"] >= promo["max_uses"]:
                return web.json_response({"ok": False, "msg": "❌ عذراً، اكتمل الحد الأقصى للمستفيدين من هذا الكود!"})

            already_claimed = await conn.fetchval("SELECT 1 FROM promo_claims WHERE user_id = $1 AND code_id = $2", user_id, promo["id"])
            if already_claimed:
                return web.json_response({"ok": False, "msg": "⚠️ لقد قمت باستخدام هذا الكود الترويجي مسبقاً!"})

            await conn.execute("INSERT INTO promo_claims (user_id, code_id, claimed_at) VALUES ($1, $2, $3)", user_id, promo["id"], now)
            await conn.execute("UPDATE promo_codes SET current_uses = current_uses + 1 WHERE id = $1", promo["id"])
            await conn.execute("UPDATE users SET olk_balance = olk_balance + $1 WHERE user_id = $2", promo["reward"], user_id)
            
            new_bal = await conn.fetchval("SELECT olk_balance FROM users WHERE user_id = $1", user_id)

        return web.json_response({"ok": True, "olk_balance": new_bal, "msg": f"🎉 مبروك! تم تفعيل الكود بنجاح وإضافة +{promo['reward']:.0f} OLK!"})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_get_referrals(request):
    try:
        user_id = int(request.query.get("user_id", 0))
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, username, first_name, ref_reward_claimed 
                FROM users 
                WHERE referred_by = $1 
                ORDER BY user_id DESC
            """, user_id)

            referrals = []
            active_count = 0
            for r in rows:
                is_active = bool(r["ref_reward_claimed"] == 1)
                if is_active:
                    active_count += 1
                referrals.append({
                    "user_id": r["user_id"],
                    "username": r["username"] or "",
                    "name": r["first_name"] or "User",
                    "is_active": is_active
                })

            earned_olk = active_count * REFERRAL_REWARD

        return web.json_response({
            "ok": True,
            "total_count": len(rows),
            "active_count": active_count,
            "earned_olk": earned_olk,
            "referrals": referrals
        })
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_get_tasks(request):
    try:
        user_id = int(request.query.get("user_id", 0))
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, title, channel_id, link, reward, max_users, current_completions 
                FROM dynamic_tasks 
                WHERE is_active = 1 AND (max_users = 0 OR current_completions < max_users)
                ORDER BY id DESC
            """)
            tasks = [dict(r) for r in rows]

            group_rows = await conn.fetch("""
                SELECT id, title, group_id, link, reward, max_users, current_completions 
                FROM dynamic_group_tasks 
                WHERE is_active = 1 AND (max_users = 0 OR current_completions < max_users)
                ORDER BY id DESC
            """)
            group_tasks = [dict(r) for r in group_rows]

            bot_rows = await conn.fetch("""
                SELECT id, title, link, reward, max_users, current_completions 
                FROM dynamic_bot_tasks 
                WHERE is_active = 1 AND (max_users = 0 OR current_completions < max_users)
                ORDER BY id DESC
            """)
            bot_tasks = [dict(r) for r in bot_rows]

            u_row = await conn.fetchrow("SELECT tasks_completed, group_tasks_completed, bot_tasks_completed FROM users WHERE user_id = $1", user_id)
            completed_ids = json.loads(u_row["tasks_completed"]) if u_row and u_row["tasks_completed"] else []
            completed_group_ids = json.loads(u_row["group_tasks_completed"]) if u_row and u_row["group_tasks_completed"] else []
            completed_bot_ids = json.loads(u_row["bot_tasks_completed"]) if u_row and u_row["bot_tasks_completed"] else []

        return web.json_response({
            "ok": True,
            "tasks": tasks,
            "group_tasks": group_tasks,
            "bot_tasks": bot_tasks,
            "completed_ids": completed_ids,
            "completed_group_ids": completed_group_ids,
            "completed_bot_ids": completed_bot_ids
        })
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_get_user(request):
    try:
        user_id = int(request.query.get("user_id", 0))
        fp = str(request.query.get("fp", ""))
        client_ip = request.headers.get("X-Forwarded-For", request.remote)
        now = int(time.time())

        is_sub = await check_user_channel_subscribed(user_id)

        async with db_pool.acquire() as conn:
            is_fraud, reason = await check_multi_account_fraud(conn, user_id, fp, client_ip)
            if is_fraud:
                await conn.execute("UPDATE users SET is_banned = 1, ban_reason = $1 WHERE user_id = $2", reason, user_id)

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
                    await conn.execute("UPDATE users SET activated_miner = 1, olk_balance = $1, device_fingerprint = $2, ip_address = $3 WHERE user_id = $4",
                                       olk, fp, client_ip, user_id)

                return web.json_response({
                    "ok": True,
                    "need_sub": False,
                    "banned": False,
                    "olk_balance": olk,
                    "ton_balance": row["ton_balance"],
                    "mining_speed": row["mining_speed"] or DEFAULT_SPEED,
                    "miner_level": row["miner_level"],
                    "saved_wallet": raw_to_user_friendly(row["saved_wallet"]),
                    "session_start_timestamp": row["session_start_timestamp"] or 0,
                    "session_active": bool(row["session_active"])
                })
            else:
                await conn.execute("""
                    INSERT INTO users (user_id, last_mining_timestamp, mining_speed, olk_balance, activated_miner, device_fingerprint, ip_address)
                    VALUES ($1, $2, $3, $4, 1, $5, $6) ON CONFLICT (user_id) DO NOTHING
                """, user_id, now, DEFAULT_SPEED, SIGNUP_BONUS, fp, client_ip)
                return web.json_response({
                    "ok": True,
                    "need_sub": False,
                    "banned": False,
                    "olk_balance": SIGNUP_BONUS,
                    "ton_balance": 0.0,
                    "mining_speed": DEFAULT_SPEED,
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
        fp = str(data.get("fingerprint", ""))
        client_ip = request.headers.get("X-Forwarded-For", request.remote)
        now = int(time.time())

        is_sub = await check_user_channel_subscribed(user_id)
        if not is_sub:
            return web.json_response({"ok": False, "msg": "يجب الاشتراك بالقناة الرسمية وقناة الإثباتات لتفعيل التعدين"})

        async with db_pool.acquire() as conn:
            is_fraud, reason = await check_multi_account_fraud(conn, user_id, fp, client_ip)
            if is_fraud:
                await conn.execute("UPDATE users SET is_banned = 1, ban_reason = $1 WHERE user_id = $2", reason, user_id)
                return web.json_response({"ok": False, "msg": reason})

            await conn.execute("""
                UPDATE users SET session_start_timestamp = $1, session_active = 1, device_fingerprint = $2, ip_address = $3 WHERE user_id = $4
            """, now, fp, client_ip, user_id)

            row = await conn.fetchrow("SELECT referred_by, ref_reward_claimed FROM users WHERE user_id = $1", user_id)
            if row and row["referred_by"] and row["ref_reward_claimed"] == 0:
                ref_by = row["referred_by"]
                await conn.execute("UPDATE users SET olk_balance = olk_balance + $1 WHERE user_id = $2", REFERRAL_REWARD, ref_by)
                await conn.execute("UPDATE users SET ref_reward_claimed = 1 WHERE user_id = $1", user_id)
                try:
                    await bot.send_message(
                        chat_id=ref_by,
                        text=f"🎉 <b>إحالة مؤكدة!</b> قام صديقك بالاشتراك بالقنوات وتشغيل جلسة التعدين.\n💰 تمت إضافة <b>+{REFERRAL_REWARD:.0f} OLK</b> إلى محفظتك بنجاح!",
                        parse_mode="HTML"
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

async def api_upgrade_rig_ton_direct(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        speed_gain = float(data.get("speed_gain"))

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT mining_speed, miner_level FROM users WHERE user_id = $1", user_id)
            if not row:
                return web.json_response({"ok": False, "msg": "المستخدم غير موجود"})

            new_speed = row["mining_speed"] + speed_gain
            new_lvl = row["miner_level"] + 1

            await conn.execute("""
                UPDATE users SET mining_speed = $1, miner_level = $2 WHERE user_id = $3
            """, new_speed, new_lvl, user_id)

        return web.json_response({"ok": True, "mining_speed": new_speed})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_upgrade_rig_olk(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        cost_olk = float(data.get("cost_olk", 0))
        speed_gain = float(data.get("speed_gain", 0))

        if cost_olk <= 0 or speed_gain <= 0:
            return web.json_response({"ok": False, "msg": "بيانات غير صالحة"})

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT olk_balance, mining_speed, miner_level FROM users WHERE user_id = $1", user_id)
            if not row or row["olk_balance"] < cost_olk:
                return web.json_response({"ok": False, "msg": "رصيد OLK غير كافٍ"})

            new_olk = row["olk_balance"] - cost_olk
            new_speed = row["mining_speed"] + speed_gain
            new_lvl = row["miner_level"] + 1

            await conn.execute("""
                UPDATE users SET olk_balance = $1, mining_speed = $2, miner_level = $3 WHERE user_id = $4
            """, new_olk, new_speed, new_lvl, user_id)

        return web.json_response({"ok": True, "olk_balance": new_olk, "mining_speed": new_speed})
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

        if not friendly_address:
            return web.json_response({"ok": False, "msg": "يرجى تحديد عنوان محفظة صالح"})

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

            admin_rows = await conn.fetch("SELECT user_id FROM bot_admins WHERE can_manage_withdrawals = 1")
            admin_ids = {SUPER_ADMIN_ID}
            for ar in admin_rows:
                admin_ids.add(ar["user_id"])

        admin_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ موافقة ودفع", callback_data=f"adm_app_{w_id}"),
                InlineKeyboardButton(text="❌ رفض", callback_data=f"adm_rej_{w_id}")
            ]
        ])
        admin_notification = (
            f"🚨 <b>طلب سحب TON جديد #{w_id}</b>\n\n"
            f"👤 المستخدم: <code>{user_id}</code>\n"
            f"💎 المبلغ: <code>{withdraw_amount:.4f} TON</code>\n"
            f"📫 المحفظة:\n<code>{friendly_address}</code>"
        )
        
        admin_withdrawal_messages[w_id] = []
        for adm_id in admin_ids:
            try:
                sent_msg = await bot.send_message(chat_id=adm_id, text=admin_notification, reply_markup=admin_kb, parse_mode="HTML")
                admin_withdrawal_messages[w_id].append((adm_id, sent_msg.message_id))
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

            if task["max_users"] > 0 and task["current_completions"] >= task["max_users"]:
                return web.json_response({"ok": False, "msg": "عذراً! انتهت هذه المهمة واكتمل الحد الأقصى للمشتركين."})

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
            await conn.execute("UPDATE dynamic_tasks SET current_completions = current_completions + 1 WHERE id = $1", task_id)

            return web.json_response({"ok": True, "reward": reward, "msg": f"✅ مبروك! تمت إضافة +{reward:.0f} OLK"})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_verify_group_task(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        task_id = int(data.get("task_id"))

        async with db_pool.acquire() as conn:
            task = await conn.fetchrow("SELECT * FROM dynamic_group_tasks WHERE id = $1 AND is_active = 1", task_id)
            if not task:
                return web.json_response({"ok": False, "msg": "المجموعة غير متوفرة"})

            if task["max_users"] > 0 and task["current_completions"] >= task["max_users"]:
                return web.json_response({"ok": False, "msg": "عذراً! اكتمل الحد الأقصى للمشتركين في هذه المهمة."})

            row = await conn.fetchrow("SELECT group_tasks_completed FROM users WHERE user_id = $1", user_id)
            tasks = json.loads(row["group_tasks_completed"]) if row and row["group_tasks_completed"] else []

            if task_id in tasks:
                return web.json_response({"ok": False, "msg": "تم استلام مكافأة هذه المجموعة مسبقاً!"})

            try:
                chat_member = await bot.get_chat_member(chat_id=task["group_id"], user_id=user_id)
                if chat_member.status in ["left", "kicked"]:
                    return web.json_response({"ok": False, "msg": "❌ لم تنضم للمجموعة بعد! انضم ثم تحقق."})
            except Exception:
                return web.json_response({"ok": False, "msg": "⚠️ تعذر التحقق، تأكد من إضافة البوت مشرفاً في المجموعة."})

            tasks.append(task_id)
            reward = task["reward"]
            await conn.execute("UPDATE users SET olk_balance = olk_balance + $1, group_tasks_completed = $2 WHERE user_id = $3",
                               reward, json.dumps(tasks), user_id)
            await conn.execute("UPDATE dynamic_group_tasks SET current_completions = current_completions + 1 WHERE id = $1", task_id)

            return web.json_response({"ok": True, "reward": reward, "msg": f"✅ مبروك! تمت إضافة +{reward:.0f} OLK"})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_verify_bot_task(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        task_id = int(data.get("task_id"))

        async with db_pool.acquire() as conn:
            task = await conn.fetchrow("SELECT * FROM dynamic_bot_tasks WHERE id = $1 AND is_active = 1", task_id)
            if not task:
                return web.json_response({"ok": False, "msg": "مهمة البوت غير متوفرة"})

            if task["max_users"] > 0 and task["current_completions"] >= task["max_users"]:
                return web.json_response({"ok": False, "msg": "عذراً! اكتمل العدد المطلوب لهذه المهمة."})

            row = await conn.fetchrow("SELECT bot_tasks_completed FROM users WHERE user_id = $1", user_id)
            tasks = json.loads(row["bot_tasks_completed"]) if row and row["bot_tasks_completed"] else []

            if task_id in tasks:
                return web.json_response({"ok": False, "msg": "تم استلام مكافأة هذا البوت مسبقاً!"})

            tasks.append(task_id)
            reward = task["reward"]
            await conn.execute("UPDATE users SET olk_balance = olk_balance + $1, bot_tasks_completed = $2 WHERE user_id = $3",
                               reward, json.dumps(tasks), user_id)
            await conn.execute("UPDATE dynamic_bot_tasks SET current_completions = current_completions + 1 WHERE id = $1", task_id)

            return web.json_response({"ok": True, "reward": reward, "msg": f"✅ مبروك! تمت إضافة +{reward:.0f} OLK"})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

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
        [InlineKeyboardButton(text="📊 إحصائيات المنظومة والمستخدمين", callback_data="adm_stats")],
        [InlineKeyboardButton(text="🏆 توب 20 الأكثر إحالة (Top 20 Referrers)", callback_data="adm_top_refs")]
    ]
    if perms.get("is_super"):
        buttons.append([InlineKeyboardButton(text="🎁 إنشاء كود برومو (خاص بالرئيس)", callback_data="adm_create_promo_start")])
    if perms.get("can_manage_withdrawals"):
        buttons.append([InlineKeyboardButton(text="⏳ طلبات السحب المعلقة", callback_data="adm_view_withdraws")])
    if perms.get("can_manage_tasks"):
        buttons.append([InlineKeyboardButton(text="📢 إدارة مهام القنوات (إضافة/حذف)", callback_data="adm_tasks_menu")])
        buttons.append([InlineKeyboardButton(text="👥 إدارة مهام المجموعات (إضافة/حذف)", callback_data="adm_groups_menu")])
        buttons.append([InlineKeyboardButton(text="🤖 إدارة مهام البوتات (إضافة/حذف)", callback_data="adm_bot_tasks_menu")])
    if perms.get("can_ban_users"):
        buttons.append([
            InlineKeyboardButton(text="🚫 حظر مستخدم (Ban)", callback_data="adm_ban_start"),
            InlineKeyboardButton(text="🔓 فك الحظر (Unban)", callback_data="adm_unban_start")
        ])
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
        [InlineKeyboardButton(text=f"حظر وفك حظر: {mark(row['can_ban_users'])}", callback_data=f"adm_tog_{target_id}_u")],
        [InlineKeyboardButton(text="🗑️ إزالة هذا المشرف بالكامل", callback_data=f"adm_rm_admin_{target_id}")],
        [InlineKeyboardButton(text="🔙 رجوع لقائمة المشرفين", callback_data="adm_manage_admins")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = (message.from_user.username or "").lower().replace("@", "")
    first_name = message.from_user.first_name or "User"
    ref_param = command.args
    now = int(time.time())

    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT is_banned, ban_reason FROM users WHERE user_id = $1", user_id)

        if user and user["is_banned"] == 1:
            await message.answer(f"⛔ هذا الحساب محظور:\nالسبب: {user['ban_reason']}\nإذا كنت تعتقد أن هذا خطأ تواصل مع الإدارة.")
            return

        if not user and ref_param:
            try:
                referrer_id = int(ref_param.replace("ref_", ""))
                if referrer_id != user_id:
                    await conn.execute("""
                        INSERT INTO users (user_id, username, first_name, referred_by, last_mining_timestamp, mining_speed, olk_balance, activated_miner)
                        VALUES ($1, $2, $3, $4, $5, $6, 0, 0)
                        ON CONFLICT (user_id) DO UPDATE SET 
                            referred_by = EXCLUDED.referred_by,
                            username = EXCLUDED.username,
                            first_name = EXCLUDED.first_name
                    """, user_id, username, first_name, referrer_id, now, DEFAULT_SPEED)
            except ValueError:
                pass
        elif not user:
            await conn.execute("""
                INSERT INTO users (user_id, username, first_name, last_mining_timestamp, mining_speed, olk_balance, activated_miner)
                VALUES ($1, $2, $3, $4, $5, 0, 0)
                ON CONFLICT (user_id) DO UPDATE SET 
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name
            """, user_id, username, first_name, now, DEFAULT_SPEED)
        else:
            await conn.execute("""
                UPDATE users SET username = $1, first_name = $2 WHERE user_id = $3
            """, username, first_name, user_id)

    perms = await get_admin_permissions(user_id)
    
    welcome_text = (
        f'<a href="{WELCOME_IMAGE_URL}">&#8288;</a>'
        "🐐⚡ أهلاً بك في عالم <b>OLK VIP CYBER MINING</b> ⚡\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⛏️ ابدأ التعدين واجمع العملات بكل سهولة!\n\n"
        "💰 تابع أرباحك ومكافآتك من داخل البوت.\n\n"
        "🎁 اكتشف مكافآت البداية وانطلق بقوة!\n\n"
        "👥 ادعُ أصدقاءك واكسب مكافأة 70 Olk على الإحالة.\n\n"
        "📋 أنجز المهام اليومية واجمع المزيد من المكافآت.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚀 رحلتك تبدأ الآن... كن جزءاً من عالم OLK! 👾\n\n"
        "👇 اضغط هنا في الأسفل للبدء معنا وتحقيق الأرباح."
    )
    
    preview_opts = LinkPreviewOptions(
        is_disabled=False,
        url=WELCOME_IMAGE_URL,
        prefer_small_media=True,
        show_above_text=True
    )

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=build_combined_start_keyboard(user_id, perms),
        link_preview_options=preview_opts
    )

@dp.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    perms = await get_admin_permissions(user_id)
    if not perms:
        return
    rank = "👑 الرئيس الأعلى (Super Admin)" if perms.get("is_super") else "🛡️ مشرف فرعي (Sub-Admin)"
    await message.answer(
        f"⚡ <b>لوحة التحكم والإدارة</b>\nرتبتك: <b>{rank}</b>\n\nاختر من الأزرار أدناه:",
        reply_markup=build_main_admin_keyboard(perms),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "adm_create_promo_start")
async def cb_create_promo_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID:
        await callback.answer("⛔ هذا الخيار مخصص للرئيس الأعلى فقط!", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer("🎁 أرسل الآن **رمز البرومو كود** الذي تريده (مثال: `VIP2026` أو `FREE50`):")
    await state.set_state(CreatePromoStates.waiting_for_code)

@dp.message(CreatePromoStates.waiting_for_code)
async def state_promo_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.update_data(code=code)
    await message.answer(f"💰 كم **عدد نقاط OLK** التي سيكسبها المستخدم عند إدخال كود `{code}`؟ (مثال: `100`):", parse_mode="Markdown")
    await state.set_state(CreatePromoStates.waiting_for_reward)

@dp.message(CreatePromoStates.waiting_for_reward)
async def state_promo_reward(message: Message, state: FSMContext):
    try:
        reward = float(message.text.strip())
        if reward <= 0:
            await message.answer("❌ القيمة يجب أن تكون أكبر من 0:")
            return
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح:")
        return

    await state.update_data(reward=reward)
    await message.answer("👥 أرسل الآن **الحد الأقصى لعدد المستفيدين** من هذا الكود (مثال: `50`، أو اكتب `0` لجعله غير محدود):")
    await state.set_state(CreatePromoStates.waiting_for_max_uses)

@dp.message(CreatePromoStates.waiting_for_max_uses)
async def state_promo_max_uses(message: Message, state: FSMContext):
    try:
        max_uses = int(message.text.strip())
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح:")
        return

    data = await state.get_data()
    await state.clear()
    now = int(time.time())

    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO promo_codes (code, reward, max_uses, current_uses, created_at, is_active)
            VALUES ($1, $2, $3, 0, $4, 1)
            ON CONFLICT (code) DO UPDATE SET 
                reward = EXCLUDED.reward,
                max_uses = EXCLUDED.max_uses,
                current_uses = 0,
                is_active = 1
        """, data["code"], data["reward"], max_uses, now)

    limit_text = f"{max_uses} مستخدم" if max_uses > 0 else "غير محدود"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة للوحة التحكم", callback_data="adm_home")]])
    await message.answer(
        f"🎉 <b>تم إنشاء كود البرومو بنجاح!</b>\n\n"
        f"🏷️ الكود: <code>{data['code']}</code>\n"
        f"🎁 المكافأة: <b>+{data['reward']:.0f} OLK</b>\n"
        f"👥 الحد الأقصى: <b>{limit_text}</b>\n\n"
        f"يمكن للمستخدمين كتابته وتفعيله الآن مباشرة من الصفحة الرئيسية!",
        parse_mode="HTML",
        reply_markup=kb
    )

@dp.callback_query(F.data == "adm_top_refs")
async def cb_admin_top_refs(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms:
        return
    await callback.answer()

    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    u.user_id,
                    u.username,
                    u.first_name,
                    COUNT(r.user_id) AS ref_count
                FROM users r
                JOIN users u ON u.user_id = r.referred_by
                WHERE r.referred_by IS NOT NULL
                GROUP BY u.user_id, u.username, u.first_name
                ORDER BY ref_count DESC
                LIMIT 20;
            """)

        if not rows:
            text = "🏆 <b>قائمة أفضل 20 مستخدم في الإحالات:</b>\n\nلا توجد إحالات مسجلة حتى الآن."
        else:
            text = "🏆 <b>ترتيب أفضل 20 مستخدم من ناحية الإحالات:</b>\n──────────────────────\n"
            for idx, r in enumerate(rows, 1):
                if r['username']:
                    uname_esc = html.escape(r['username'])
                    name_display = f"@{uname_esc}"
                else:
                    fname_esc = html.escape(r['first_name'] or 'User')
                    name_display = f"{fname_esc} (<code>{r['user_id']}</code>)"

                text += f"<b>{idx}.</b> {name_display} — 👥 <code>{r['ref_count']}</code> إحالة\n"
            text += "──────────────────────"
    except Exception as e:
        text = f"⚠️ حدث خطأ أثناء جلب قائمة التوب: {e}"

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة للرئيسية", callback_data="adm_home")]])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "adm_ban_start")
async def cb_ban_start(callback: CallbackQuery, state: FSMContext):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_ban_users"):
        await callback.answer("⛔ ليس لديك صلاحية الحظر", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer("🚫 أرسل الآن **معرّف المستخدم (Telegram ID)** أو **اليوزر (@username)** لحظره:")
    await state.set_state(BanStates.waiting_for_target)

@dp.message(BanStates.waiting_for_target)
async def state_ban_target(message: Message, state: FSMContext):
    raw = message.text.strip()
    target_clean = raw.lower().replace("@", "")

    async with db_pool.acquire() as conn:
        if raw.isdigit():
            user = await conn.fetchrow("SELECT user_id, username, first_name FROM users WHERE user_id = $1", int(raw))
        else:
            user = await conn.fetchrow("SELECT user_id, username, first_name FROM users WHERE LOWER(username) = $1", target_clean)

    if not user:
        await message.answer("❌ لم يتم العثور على هذا المستخدم في قاعدة البيانات! تأكد من المعرف أو اليوزر:")
        return

    await state.update_data(target_id=user["user_id"], target_name=user["first_name"] or str(user["user_id"]))
    await message.answer(f"⚠️ المستخدم المحدد: <b>{html.escape(user['first_name'] or '')}</b> (<code>{user['user_id']}</code>)\n\nأرسل الآن **سبب الحظر** (أو اكتب `مخالفة الشروط`):", parse_mode="HTML")
    await state.set_state(BanStates.waiting_for_reason)

@dp.message(BanStates.waiting_for_reason)
async def state_ban_execute(message: Message, state: FSMContext):
    reason = message.text.strip()
    data = await state.get_data()
    target_id = data.get("target_id")
    await state.clear()

    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE users SET is_banned = 1, ban_reason = $1, is_whitelisted = 0 WHERE user_id = $2", reason, target_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة للوحة التحكم", callback_data="adm_home")]])
    await message.answer(f"✅ تم حظر المستخدم <code>{target_id}</code> بنجاح!\nالسبب: {html.escape(reason)}", parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "adm_unban_start")
async def cb_unban_start(callback: CallbackQuery, state: FSMContext):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_ban_users"):
        await callback.answer("⛔ ليس لديك صلاحية فك الحظر", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer("🔓 أرسل الآن **معرّف المستخدم (Telegram ID)** أو **اليوزر (@username)** لفك الحظر عنه فوراً:")
    await state.set_state(UnbanStates.waiting_for_target)

@dp.message(UnbanStates.waiting_for_target)
async def state_execute_unban(message: Message, state: FSMContext):
    raw = message.text.strip()
    target_clean = raw.lower().replace("@", "")

    async with db_pool.acquire() as conn:
        if raw.isdigit():
            user = await conn.fetchrow("SELECT user_id, username, first_name FROM users WHERE user_id = $1", int(raw))
        else:
            user = await conn.fetchrow("SELECT user_id, username, first_name FROM users WHERE LOWER(username) = $1", target_clean)

        if not user:
            await message.answer("❌ لم يتم العثور على هذا المستخدم في قاعدة البيانات! تأكد من صحة الـ ID أو اليوزر:")
            return

        target_id = user["user_id"]
        await conn.execute("UPDATE users SET is_banned = 0, ban_reason = NULL, is_whitelisted = 1 WHERE user_id = $1", target_id)

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة للوحة التحكم", callback_data="adm_home")]])
    await message.answer(f"✅ تم فك الحظر عن <code>{target_id}</code> بنجاح وإدراجه في القائمة البيضاء لمنع الحظر التلقائي!", parse_mode="HTML", reply_markup=kb)

@dp.message(Command("unban"))
async def unban_user_direct(message: Message, command: CommandObject):
    perms = await get_admin_permissions(message.from_user.id)
    if not perms or not perms.get("can_ban_users"): return
    if not command.args:
        await message.answer("⚠️ الصيغة:\n`/unban USER_ID أو @username`", parse_mode="Markdown")
        return
    raw = command.args.strip()
    target_clean = raw.lower().replace("@", "")
    async with db_pool.acquire() as conn:
        if raw.isdigit():
            user = await conn.fetchrow("SELECT user_id, username, first_name FROM users WHERE user_id = $1", int(raw))
        else:
            user = await conn.fetchrow("SELECT user_id, username, first_name FROM users WHERE LOWER(username) = $1", target_clean)

        if not user:
            await message.answer("❌ المستخدم غير موجود.")
            return

        await conn.execute("UPDATE users SET is_banned = 0, ban_reason = NULL, is_whitelisted = 1 WHERE user_id = $1", user["user_id"])
    await message.answer(f"✅ تم فك الحظر عن `{user['user_id']}` بنجاح!", parse_mode="Markdown")

@dp.message(Command("ban"))
async def ban_user_direct(message: Message, command: CommandObject):
    perms = await get_admin_permissions(message.from_user.id)
    if not perms or not perms.get("can_ban_users"): return
    if not command.args:
        await message.answer("⚠️ الصيغة:\n`/ban USER_ID_او_يوزر سبب الحظر`", parse_mode="Markdown")
        return
    parts = command.args.split(maxsplit=1)
    raw = parts[0].strip()
    target_clean = raw.lower().replace("@", "")
    reason = parts[1] if len(parts) > 1 else "حظر إداري"

    async with db_pool.acquire() as conn:
        if raw.isdigit():
            user = await conn.fetchrow("SELECT user_id, username, first_name FROM users WHERE user_id = $1", int(raw))
        else:
            user = await conn.fetchrow("SELECT user_id, username, first_name FROM users WHERE LOWER(username) = $1", target_clean)

        if not user:
            await message.answer("❌ المستخدم غير موجود.")
            return

        await conn.execute("UPDATE users SET is_banned = 1, ban_reason = $1, is_whitelisted = 0 WHERE user_id = $2", reason, user["user_id"])
    await message.answer(f"✅ تم حظر المستخدم `{user['user_id']}` بنجاح.", parse_mode="Markdown")

@dp.callback_query(F.data == "adm_back_to_start")
async def cb_back_to_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    user_id = callback.from_user.id
    perms = await get_admin_permissions(user_id)
    welcome_text = (
        f'<a href="{WELCOME_IMAGE_URL}">&#8288;</a>'
        "🐐⚡ أهلاً بك في عالم <b>OLK VIP CYBER MINING</b> ⚡\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⛏️ ابدأ التعدين واجمع العملات بكل سهولة!\n\n"
        "💰 تابع أرباحك ومكافآتك من داخل البوت.\n\n"
        "🎁 اكتشف مكافآت البداية وانطلق بقوة!\n\n"
        "👥 ادعُ أصدقاءك واكسب مكافأة 70 Olk على الإحالة.\n\n"
        "📋 أنجز المهام اليومية واجمع المزيد من المكافآت.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚀 رحلتك تبدأ الآن... كن جزءاً من عالم OLK! 👾\n\n"
        "👇 اضغط هنا في الأسفل للبدء معنا وتحقيق الأرباح."
    )
    preview_opts = LinkPreviewOptions(
        is_disabled=False,
        url=WELCOME_IMAGE_URL,
        prefer_small_media=True,
        show_above_text=True
    )
    await callback.message.edit_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=build_combined_start_keyboard(user_id, perms),
        link_preview_options=preview_opts
    )

@dp.callback_query(F.data == "adm_home")
async def cb_admin_home(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms:
        return
    rank = "👑 الرئيس الأعلى (Super Admin)" if perms.get("is_super") else "🛡️ مشرف فرعي (Sub-Admin)"
    await callback.message.edit_text(
        f"⚡ <b>لوحة التحكم والإدارة</b>\nرتبتك: <b>{rank}</b>\n\nاختر من الأزرار أدناه:",
        reply_markup=build_main_admin_keyboard(perms),
        parse_mode="HTML"
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
        banned_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_banned = 1") or 0
        pending_withdraws = await conn.fetchval("SELECT COUNT(*) FROM withdrawals WHERE status = 'PENDING'") or 0
        active_tasks = await conn.fetchval("SELECT COUNT(*) FROM dynamic_tasks WHERE is_active = 1") or 0
        active_group_tasks = await conn.fetchval("SELECT COUNT(*) FROM dynamic_group_tasks WHERE is_active = 1") or 0
        active_bot_tasks = await conn.fetchval("SELECT COUNT(*) FROM dynamic_bot_tasks WHERE is_active = 1") or 0

    stats_msg = (
        "📊 <b>إحصائيات المنظومة الحية:</b>\n"
        "──────────────────────\n"
        f"👥 إجمالي المستخدمين النشطين: <code>{users_count}</code>\n"
        f"🚫 المحظورين: <code>{banned_users}</code>\n"
        f"🪙 إجمالي رصيد OLK: <code>{total_olk:.2f}</code>\n"
        f"💎 إجمالي رصيد TON: <code>{total_ton:.4f}</code>\n"
        f"⏳ طلبات السحب المعلقة: <code>{pending_withdraws}</code>\n"
        f"📢 مهام القنوات: <code>{active_tasks}</code>\n"
        f"👥 مهام المجموعات: <code>{active_group_tasks}</code>\n"
        f"🤖 مهام البوتات: <code>{active_bot_tasks}</code>\n"
        "──────────────────────"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة للرئيسية", callback_data="adm_home")]])
    await callback.message.edit_text(stats_msg, parse_mode="HTML", reply_markup=kb)

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
                InlineKeyboardButton(text="❌ رفض", callback_data=f"adm_rej_{w_id}")
            ]
        ])
        await callback.message.answer(
            f"📄 <b>طلب سحب #{w_id}</b>\n👤 المستخدم: <code>{uid}</code>\n💎 المبلغ: <code>{amt:.4f} TON</code>\n📫 المحفظة:\n<code>{w_addr}</code>",
            parse_mode="HTML",
            reply_markup=kb
        )

# مهام القنوات
@dp.callback_query(F.data == "adm_tasks_menu")
async def cb_tasks_menu(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"):
        await callback.answer("⛔ ليس لديك صلاحية إدارة المهام", show_alert=True)
        return
    await callback.answer()

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, title, reward, max_users, current_completions FROM dynamic_tasks WHERE is_active = 1 ORDER BY id DESC")

    buttons = [[InlineKeyboardButton(text="➕ إضافة مهمة قناة جديدة", callback_data="adm_add_task_start")]]
    for r in rows:
        lim_str = f"({r['current_completions']}/{r['max_users']})" if r['max_users'] > 0 else "(غير محدود)"
        buttons.append([InlineKeyboardButton(text=f"🗑️ حذف: {r['title']} {lim_str}", callback_data=f"adm_del_task_{r['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 العودة للرئيسية", callback_data="adm_home")])

    await callback.message.edit_text("📢 <b>إدارة مهام القنوات:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "adm_add_task_start")
async def cb_add_task_start(callback: CallbackQuery, state: FSMContext):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"): return
    await callback.answer()
    await callback.message.answer("📝 أرسل الآن **عنوان مهمة القناة**:")
    await state.set_state(AddTaskStates.waiting_for_title)

@dp.message(AddTaskStates.waiting_for_title)
async def state_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("📢 أرسل الآن **معرّف القناة** (مثال: `@channel_name`):")
    await state.set_state(AddTaskStates.waiting_for_channel_id)

@dp.message(AddTaskStates.waiting_for_channel_id)
async def state_task_channel_id(message: Message, state: FSMContext):
    await state.update_data(channel_id=message.text.strip())
    await message.answer("🔗 أرسل الآن **رابط القناة** (مثال: `https://t.me/channel_name`):")
    await state.set_state(AddTaskStates.waiting_for_link)

@dp.message(AddTaskStates.waiting_for_link)
async def state_task_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text.strip())
    is_super = (message.from_user.id == SUPER_ADMIN_ID)
    hint = "أي قيمة تريدها (صلاحية الرئيس)" if is_super else f"الحد الأقصى المسموح لك هو {ADMIN_MAX_TASK_REWARD:.0f} OLK"
    await message.answer(f"💰 أرسل **قيمة المكافأة** بعملة OLK ({hint}):")
    await state.set_state(AddTaskStates.waiting_for_reward)

@dp.message(AddTaskStates.waiting_for_reward)
async def state_task_reward(message: Message, state: FSMContext):
    try: 
        reward = float(message.text.strip())
        if reward <= 0:
            await message.answer("❌ يجب أن تكون المكافأة أكبر من 0:")
            return
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح للمكافأة:")
        return

    if message.from_user.id != SUPER_ADMIN_ID and reward > ADMIN_MAX_TASK_REWARD:
        await message.answer(f"⚠️ عذراً، لا يمكنك وضع مكافأة تتعدى {ADMIN_MAX_TASK_REWARD:.0f} نقطة!\nيرجى كتابة قيمة صالحة (70 أو أقل):")
        return

    await state.update_data(reward=reward)
    await message.answer("👥 أرسل الآن **الحد الأقصى لعدد المشتركين** (مثال: `100`، أو اكتب `0` لجعلها غير محدودة):")
    await state.set_state(AddTaskStates.waiting_for_max_users)

@dp.message(AddTaskStates.waiting_for_max_users)
async def state_task_max_users(message: Message, state: FSMContext):
    try:
        max_users = int(message.text.strip())
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح:")
        return

    data = await state.get_data()
    await state.clear()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO dynamic_tasks (title, channel_id, link, reward, max_users, current_completions) 
            VALUES ($1, $2, $3, $4, $5, 0)
        """, data["title"], data["channel_id"], data["link"], data["reward"], max_users)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة لقائمة القنوات", callback_data="adm_tasks_menu")]])
    limit_text = f"الحد الأقصى: {max_users} عضو" if max_users > 0 else "غير محدود"
    await message.answer(f"🎉 تمت إضافة مهمة القناة: {data['title']}\nالمكافأة: +{data['reward']} OLK ({limit_text})", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_del_task_"))
async def cb_del_task(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"): return
    t_id = int(callback.data.split("_")[3])
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE dynamic_tasks SET is_active = 0 WHERE id = $1", t_id)
    await callback.answer("🗑️ تم حذف المهمة!", show_alert=True)
    await cb_tasks_menu(callback)

# مهام المجموعات
@dp.callback_query(F.data == "adm_groups_menu")
async def cb_groups_menu(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"):
        await callback.answer("⛔ ليس لديك صلاحية إدارة المهام", show_alert=True)
        return
    await callback.answer()

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, title, reward, max_users, current_completions FROM dynamic_group_tasks WHERE is_active = 1 ORDER BY id DESC")

    buttons = [[InlineKeyboardButton(text="➕ إضافة مهمة مجموعة جديدة", callback_data="adm_add_group_start")]]
    for r in rows:
        lim_str = f"({r['current_completions']}/{r['max_users']})" if r['max_users'] > 0 else "(غير محدود)"
        buttons.append([InlineKeyboardButton(text=f"🗑️ حذف: {r['title']} {lim_str}", callback_data=f"adm_del_group_{r['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 العودة للرئيسية", callback_data="adm_home")])

    await callback.message.edit_text("👥 <b>إدارة مهام المجموعات:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "adm_add_group_start")
async def cb_add_group_start(callback: CallbackQuery, state: FSMContext):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"): return
    await callback.answer()
    await callback.message.answer("📝 أرسل الآن **عنوان مهمة المجموعة**:")
    await state.set_state(AddGroupTaskStates.waiting_for_title)

@dp.message(AddGroupTaskStates.waiting_for_title)
async def state_group_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("👥 أرسل الآن **معرّف المجموعة** (مثال: `@group_name` أو الـ Chat ID):")
    await state.set_state(AddGroupTaskStates.waiting_for_group_id)

@dp.message(AddGroupTaskStates.waiting_for_group_id)
async def state_group_id(message: Message, state: FSMContext):
    await state.update_data(group_id=message.text.strip())
    await message.answer("🔗 أرسل الآن **رابط المجموعة**:")
    await state.set_state(AddGroupTaskStates.waiting_for_link)

@dp.message(AddGroupTaskStates.waiting_for_link)
async def state_group_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text.strip())
    is_super = (message.from_user.id == SUPER_ADMIN_ID)
    hint = "أي قيمة تريدها (صلاحية الرئيس)" if is_super else f"الحد الأقصى المسموح لك هو {ADMIN_MAX_TASK_REWARD:.0f} OLK"
    await message.answer(f"💰 أرسل **قيمة المكافأة** بعملة OLK ({hint}):")
    await state.set_state(AddGroupTaskStates.waiting_for_reward)

@dp.message(AddGroupTaskStates.waiting_for_reward)
async def state_group_reward(message: Message, state: FSMContext):
    try: 
        reward = float(message.text.strip())
        if reward <= 0:
            await message.answer("❌ يجب أن تكون المكافأة أكبر من 0:")
            return
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح للمكافأة:")
        return

    if message.from_user.id != SUPER_ADMIN_ID and reward > ADMIN_MAX_TASK_REWARD:
        await message.answer(f"⚠️ عذراً، لا يمكنك وضع مكافأة تتعدى {ADMIN_MAX_TASK_REWARD:.0f} نقطة!\nيرجى كتابة قيمة صالحة (70 أو أقل):")
        return

    await state.update_data(reward=reward)
    await message.answer("👥 أرسل الآن **الحد الأقصى لعدد المشتركين** (مثال: `100`، أو اكتب `0` لجعلها غير محدودة):")
    await state.set_state(AddGroupTaskStates.waiting_for_max_users)

@dp.message(AddGroupTaskStates.waiting_for_max_users)
async def state_group_max_users(message: Message, state: FSMContext):
    try:
        max_users = int(message.text.strip())
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح:")
        return

    data = await state.get_data()
    await state.clear()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO dynamic_group_tasks (title, group_id, link, reward, max_users, current_completions) 
            VALUES ($1, $2, $3, $4, $5, 0)
        """, data["title"], data["group_id"], data["link"], data["reward"], max_users)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة لقائمة المجموعات", callback_data="adm_groups_menu")]])
    limit_text = f"الحد الأقصى: {max_users} عضو" if max_users > 0 else "غير محدود"
    await message.answer(f"🎉 تمت إضافة مهمة المجموعة: {data['title']}\nالمكافأة: +{data['reward']} OLK ({limit_text})", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_del_group_"))
async def cb_del_group(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"): return
    t_id = int(callback.data.split("_")[3])
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE dynamic_group_tasks SET is_active = 0 WHERE id = $1", t_id)
    await callback.answer("🗑️ تم حذف مهمة المجموعة!", show_alert=True)
    await cb_groups_menu(callback)

# مهام البوتات
@dp.callback_query(F.data == "adm_bot_tasks_menu")
async def cb_bot_tasks_menu(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"):
        await callback.answer("⛔ ليس لديك صلاحية إدارة المهام", show_alert=True)
        return
    await callback.answer()

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, title, reward, max_users, current_completions FROM dynamic_bot_tasks WHERE is_active = 1 ORDER BY id DESC")

    buttons = [[InlineKeyboardButton(text="➕ إضافة مهمة بوت جديدة", callback_data="adm_add_bot_task_start")]]
    for r in rows:
        lim_str = f"({r['current_completions']}/{r['max_users']})" if r['max_users'] > 0 else "(غير محدود)"
        buttons.append([InlineKeyboardButton(text=f"🗑️ حذف: {r['title']} (+{r['reward']} OLK) {lim_str}", callback_data=f"adm_del_bottask_{r['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 العودة للرئيسية", callback_data="adm_home")])

    await callback.message.edit_text("🤖 <b>إدارة مهام البوتات:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "adm_add_bot_task_start")
async def cb_add_bot_task_start(callback: CallbackQuery, state: FSMContext):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"): return
    await callback.answer()
    await callback.message.answer("📝 أرسل **اسم أو عنوان البوت**:")
    await state.set_state(AddBotTaskStates.waiting_for_title)

@dp.message(AddBotTaskStates.waiting_for_title)
async def state_bot_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("🔗 أرسل **رابط البوت أو رابط إحالتك للبوت**:")
    await state.set_state(AddBotTaskStates.waiting_for_link)

@dp.message(AddBotTaskStates.waiting_for_link)
async def state_bot_task_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text.strip())
    is_super = (message.from_user.id == SUPER_ADMIN_ID)
    hint = "أي قيمة تريدها (صلاحية الرئيس)" if is_super else f"الحد الأقصى المسموح لك هو {ADMIN_MAX_TASK_REWARD:.0f} OLK"
    await message.answer(f"💰 أرسل **قيمة المكافأة** بعملة OLK ({hint}):")
    await state.set_state(AddBotTaskStates.waiting_for_reward)

@dp.message(AddBotTaskStates.waiting_for_reward)
async def state_bot_task_reward(message: Message, state: FSMContext):
    try: 
        reward = float(message.text.strip())
        if reward <= 0:
            await message.answer("❌ يجب أن تكون المكافأة أكبر من 0:")
            return
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح للمكافأة:")
        return

    if message.from_user.id != SUPER_ADMIN_ID and reward > ADMIN_MAX_TASK_REWARD:
        await message.answer(f"⚠️ عذراً، لا يمكنك وضع مكافأة تتعدى {ADMIN_MAX_TASK_REWARD:.0f} نقطة!\nيرجى كتابة قيمة صالحة (70 أو أقل):")
        return

    await state.update_data(reward=reward)
    await message.answer("👥 أرسل الآن **الحد الأقصى لعدد المشتركين** (مثال: `100`، أو اكتب `0` لجعلها غير محدودة):")
    await state.set_state(AddBotTaskStates.waiting_for_max_users)

@dp.message(AddBotTaskStates.waiting_for_max_users)
async def state_bot_task_max_users(message: Message, state: FSMContext):
    try:
        max_users = int(message.text.strip())
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح:")
        return

    data = await state.get_data()
    await state.clear()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO dynamic_bot_tasks (title, link, reward, max_users, current_completions) 
            VALUES ($1, $2, $3, $4, 0)
        """, data["title"], data["link"], data["reward"], max_users)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة لقائمة البوتات", callback_data="adm_bot_tasks_menu")]])
    limit_text = f"الحد الأقصى: {max_users} عضو" if max_users > 0 else "غير محدود"
    await message.answer(f"🎉 تمت إضافة مهمة البوت: {data['title']}\nالمكافأة: +{data['reward']} OLK ({limit_text})", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_del_bottask_"))
async def cb_del_bot_task(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_tasks"): return
    t_id = int(callback.data.split("_")[3])
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE dynamic_bot_tasks SET is_active = 0 WHERE id = $1", t_id)
    await callback.answer("🗑️ تم حذف مهمة البوت!", show_alert=True)
    await cb_bot_tasks_menu(callback)

# إدارة المشرفين
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

    await callback.message.edit_text("👑 <b>إدارة المشرفين والصلاحيات:</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data == "adm_add_admin_start")
async def cb_add_admin_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID: return
    await callback.answer()
    await callback.message.answer("🆔 أرسل الآن **معرّف المشرف (Telegram ID)** الذي تريد إضافته:")
    await state.set_state(AddAdminStates.waiting_for_id)

@dp.message(AddAdminStates.waiting_for_id)
async def state_save_new_admin(message: Message, state: FSMContext):
    try: new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ المعرف يجب أن يكون رقماً صحيحاً:")
        return

    await state.clear()
    now = int(time.time())
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO bot_admins (user_id, can_manage_withdrawals, can_manage_tasks, can_broadcast, can_ban_users, created_at)
            VALUES ($1, 1, 0, 0, 0, $2) ON CONFLICT (user_id) DO NOTHING
        """, new_admin_id, now)

    await message.answer(f"✅ تم إضافة المشرف <code>{new_admin_id}</code> بنجاح!", parse_mode="HTML")

@dp.callback_query(F.data.startswith("adm_edit_admin_"))
async def cb_edit_admin(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id != SUPER_ADMIN_ID: return
    target_id = int(callback.data.split("_")[3])
    kb = await render_admin_perms_keyboard(target_id)
    if not kb: return
    await callback.message.edit_text(f"⚙️ <b>ضبط صلاحيات المشرف:</b> <code>{target_id}</code>", parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_tog_"))
async def cb_toggle_permission(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id != SUPER_ADMIN_ID: return
    parts = callback.data.split("_")
    target_id, field_code = int(parts[2]), parts[3]
    col_map = {"w": "can_manage_withdrawals", "t": "can_manage_tasks", "b": "can_broadcast", "u": "can_ban_users"}
    col = col_map.get(field_code)
    if not col: return

    async with db_pool.acquire() as conn:
        await conn.execute(f"UPDATE bot_admins SET {col} = (CASE WHEN {col} = 1 THEN 0 ELSE 1 END) WHERE user_id = $1", target_id)

    kb = await render_admin_perms_keyboard(target_id)
    if kb:
        try: await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception: pass

@dp.callback_query(F.data.startswith("adm_rm_admin_"))
async def cb_remove_admin(callback: CallbackQuery):
    if callback.from_user.id != SUPER_ADMIN_ID: return
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

# الموافقة على السحب مع قفل فوري وتحديث لجميع الإداريين
@dp.callback_query(F.data.startswith("adm_app_"))
async def approve_withdraw(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_withdrawals"): return
    w_id = int(callback.data.split("_")[2])

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT w.id, w.user_id, w.amount_ton, w.wallet_address, w.status, u.username, u.first_name 
            FROM withdrawals w
            LEFT JOIN users u ON u.user_id = w.user_id
            WHERE w.id = $1
        """, w_id)

        if not row:
            await callback.answer("⚠️ طلب السحب غير موجود.", show_alert=True)
            return

        if row["status"] != 'PENDING':
            await callback.answer("⚠️ تم اتخاذ إجراء على هذا الطلب مسبقاً!", show_alert=True)
            try:
                await callback.message.edit_text(callback.message.text + f"\n\n🔒 <b>هذا الطلب منفذ بالفعل بحالة: {row['status']}</b>", parse_mode="HTML")
            except Exception: pass
            return

        uid = row["user_id"]
        amount = row["amount_ton"]
        wallet_raw = row["wallet_address"]
        uname = row["username"]
        fname = row["first_name"] or "مستخدم"

        await conn.execute("UPDATE withdrawals SET status = 'APPROVED' WHERE id = $1", w_id)

    await callback.answer("✅ تمت الموافقة بنجاح!", show_alert=False)

    try:
        await bot.send_message(
            chat_id=uid,
            text=f"🎉 <b>تمت الموافقة ودفع سحب {amount:.4f} TON لمحفظتك بنجاح!</b>\n\nتأكد من محفظتك الآن، شكراً لثقتكم.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    if len(wallet_raw) > 10:
        masked_wallet = wallet_raw[:4] + "..." + wallet_raw[-4:]
    else:
        masked_wallet = wallet_raw

    user_tag = f"@{uname}" if uname else f"{fname}"
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    proof_caption = (
        "✅ <b>إثبات دفع وسحب جديد | NEW PAYOUT</b>\n\n"
        f"👤 <b>المستلم:</b> {html.escape(user_tag)}\n"
        f"💰 <b>المبلغ:</b> <code>{amount:.4f} TON</code> 💎\n"
        f"📫 <b>المحفظة:</b> <code>{masked_wallet}</code>\n"
        f"⚡ <b>الحالة:</b> مكتمل ومدفوع (Paid)\n"
        f"🕒 <b>التاريخ:</b> <code>{now_time}</code>\n\n"
        "💎 <i>استمر في التعدين واكسب TON و OLK يومياً!</i>\n"
        "🤖 <b>البوت الرسمي:</b> @OlkaVip_bot"
    )

    proof_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ ابدأ التعدين الآن", url="https://t.me/OlkaVip_bot")]
    ])

    try:
        await bot.send_photo(
            chat_id=PROOFS_CHANNEL,
            photo=PAYOUT_PROOF_IMAGE_URL,
            caption=proof_caption,
            parse_mode="HTML",
            reply_markup=proof_kb
        )
    except Exception as e:
        print(f"Error posting photo proof: {e}")
        try:
            await bot.send_message(chat_id=PROOFS_CHANNEL, text=proof_caption, parse_mode="HTML", reply_markup=proof_kb)
        except Exception: pass

    admin_done_by = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"
    updated_notice = (
        f"📄 <b>طلب سحب #{w_id}</b>\n"
        f"👤 المستخدم: <code>{uid}</code>\n"
        f"💎 المبلغ: <code>{amount:.4f} TON</code>\n"
        f"📫 المحفظة:\n<code>{wallet_raw}</code>\n\n"
        f"✅ <b>تمت الموافقة والدفع ونشر الإثبات!</b>\n"
        f"🛡️ <b>بواسطة:</b> {admin_done_by}"
    )

    if w_id in admin_withdrawal_messages:
        for c_id, m_id in admin_withdrawal_messages[w_id]:
            try:
                await bot.edit_message_text(chat_id=c_id, message_id=m_id, text=updated_notice, parse_mode="HTML")
            except Exception:
                pass
        del admin_withdrawal_messages[w_id]
    else:
        try:
            await callback.message.edit_text(updated_notice, parse_mode="HTML")
        except Exception: pass

# رفض السحب نهائياً بدون إعادة الرصيد وتحديث الحالة عند الجميع
@dp.callback_query(F.data.startswith("adm_rej_"))
async def reject_withdraw(callback: CallbackQuery):
    perms = await get_admin_permissions(callback.from_user.id)
    if not perms or not perms.get("can_manage_withdrawals"): return
    w_id = int(callback.data.split("_")[2])

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT user_id, amount_ton, wallet_address, status FROM withdrawals WHERE id = $1", w_id)
        if not row:
            await callback.answer("⚠️ الطلب غير موجود.", show_alert=True)
            return

        if row["status"] != 'PENDING':
            await callback.answer("⚠️ تم اتخاذ إجراء على هذا الطلب مسبقاً!", show_alert=True)
            try:
                await callback.message.edit_text(callback.message.text + f"\n\n🔒 <b>هذا الطلب منفذ بالفعل بحالة: {row['status']}</b>", parse_mode="HTML")
            except Exception: pass
            return

        uid, amount, wallet_raw = row["user_id"], row["amount_ton"], row["wallet_address"]
        await conn.execute("UPDATE withdrawals SET status = 'REJECTED' WHERE id = $1", w_id)

    await callback.answer("❌ تم رفض الطلب (دون إعادة الرصيد)", show_alert=False)

    try:
        await bot.send_message(
            chat_id=uid,
            text=f"❌ <b>تم رفض طلب السحب الخاص بك بمبلغ {amount:.4f} TON.</b>\nسبب الرفض: مخالفة شروط وسياسات المنظومة.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    admin_done_by = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"
    rejected_notice = (
        f"📄 <b>طلب سحب #{w_id}</b>\n"
        f"👤 المستخدم: <code>{uid}</code>\n"
        f"💎 المبلغ: <code>{amount:.4f} TON</code>\n"
        f"📫 المحفظة:\n<code>{wallet_raw}</code>\n\n"
        f"❌ <b>تم رفض هذا الطلب نهائياً (لم يتم إرجاع الرصيد).</b>\n"
        f"🛡️ <b>بواسطة:</b> {admin_done_by}"
    )

    if w_id in admin_withdrawal_messages:
        for c_id, m_id in admin_withdrawal_messages[w_id]:
            try:
                await bot.edit_message_text(chat_id=c_id, message_id=m_id, text=rejected_notice, parse_mode="HTML")
            except Exception:
                pass
        del admin_withdrawal_messages[w_id]
    else:
        try:
            await callback.message.edit_text(rejected_notice, parse_mode="HTML")
        except Exception: pass

async def web_handler(request):
    return web.Response(text=MINI_APP_HTML, content_type="text/html")

async def main():
    await init_db()
    print("OLK Cyber Session, Proof Image Fixed, Multi-Admin Payout Sync & Promo Engine is LIVE...")

    app = web.Application()
    app.router.add_get("/", web_handler)
    app.router.add_get("/tonconnect-manifest.json", api_manifest)
    app.router.add_get("/api/get_user", api_get_user)
    app.router.add_get("/api/get_tasks", api_get_tasks)
    app.router.add_get("/api/get_referrals", api_get_referrals)
    app.router.add_post("/api/save_wallet", api_save_wallet)
    app.router.add_post("/api/redeem_promo", api_redeem_promo)
    app.router.add_post("/api/start_mining_session", api_start_mining_session)
    app.router.add_post("/api/claim_session_rewards", api_claim_session_rewards)
    app.router.add_post("/api/upgrade_rig_ton_direct", api_upgrade_rig_ton_direct)
    app.router.add_post("/api/upgrade_rig_olk", api_upgrade_rig_olk)
    app.router.add_post("/api/deposit_ton_credit", api_deposit_ton_credit)
    app.router.add_post("/api/convert", api_convert)
    app.router.add_post("/api/withdraw", api_withdraw)
    app.router.add_post("/api/verify_channel_task", api_verify_channel_task)
    app.router.add_post("/api/verify_group_task", api_verify_group_task)
    app.router.add_post("/api/verify_bot_task", api_verify_bot_task)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
