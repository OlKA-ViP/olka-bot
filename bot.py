import asyncio
import aiosqlite
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

BOT_TOKEN = "8707730826:AAExJ7ZSQe9YFy8Y0O2eG3uPCAwVa_vG6Qc"
ADMIN_ID = 1932161126
SPONSOR_CHANNEL = "@olka_ad"

PROJECT_TON_WALLET = "UQB3Xs8jkbebkVumWJlnEmDkjN4YXsZuHPrXSpZT1RtmZrCB"

CONVERSION_RATE = 10000
MIN_WITHDRAW_TON = 0.1

REFERRAL_REWARD = 80.0
SIGNUP_BONUS = 50.0

CHANNELS_TASKS = [
    {
        "id": "task_chan_main",
        "title": "قناة OLKA AD الرسمية",
        "channel_id": "@olka_ad",
        "link": "https://t.me/olka_ad",
        "reward": 10.0
    }
]

WEBAPP_URL = "https://olka-bot-service.onrender.com"

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

MINI_APP_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>تعدين OLK VIP</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --bg-main: #060a12;
      --card-bg: rgba(15, 23, 42, 0.88);
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
    html, body {
      background-color: var(--bg-main);
      background-image: 
        linear-gradient(rgba(30, 41, 67, 0.22) 1px, transparent 1px),
        linear-gradient(90deg, rgba(30, 41, 67, 0.22) 1px, transparent 1px);
      background-size: 24px 24px;
      color: #ffffff;
      min-height: 100vh;
      height: 100%;
      overflow: hidden;
    }
    .main-scroll-view {
      height: 100vh;
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
      padding: 10px 14px 140px 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
    }
    .top-header {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      gap: 8px;
    }
    .header-signal {
      font-size: 12px;
      color: var(--accent-green);
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 5px;
      background: rgba(34, 197, 94, 0.12);
      padding: 6px 10px;
      border-radius: 12px;
      border: 1px solid rgba(34, 197, 94, 0.25);
    }
    .lang-switch-box {
      display: flex;
      background: rgba(15, 23, 42, 0.95);
      border: 1.5px solid var(--card-border);
      border-radius: 16px;
      padding: 3px;
      gap: 4px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .lang-btn {
      background: transparent;
      border: none;
      color: #94a3b8;
      font-size: 13px;
      font-weight: 800;
      padding: 6px 12px;
      border-radius: 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s ease;
    }
    .lang-btn.active {
      background: linear-gradient(135deg, #1e40af, #2563eb);
      color: #ffffff;
      box-shadow: 0 2px 10px rgba(37, 99, 235, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .assets-container {
      width: 100%;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(20px);
      border-radius: 20px;
      padding: 14px;
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
    .assets-total span { color: var(--gold-primary); direction: ltr; display: inline-block; }
    .assets-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      color: #93c5fd;
      font-size: 12px;
      font-weight: 700;
    }
    .balance-cards-grid {
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 12px;
    }
    .bal-card {
      background: rgba(6, 11, 22, 0.9);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .bal-card-title {
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .bal-card-value {
      font-size: 17px;
      font-weight: 900;
      direction: ltr;
      text-align: left;
    }
    .wallet-connection-banner {
      width: 100%;
      background: linear-gradient(135deg, rgba(37, 99, 235, 0.2), rgba(6, 182, 212, 0.15));
      border: 1.5px solid rgba(56, 189, 248, 0.45);
      border-radius: 16px;
      padding: 12px 14px;
      margin-top: 6px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(2, 132, 199, 0.25);
    }
    .wallet-connection-banner:active { transform: scale(0.98); }
    .wallet-banner-left { display: flex; align-items: center; gap: 10px; }
    .wallet-icon-box {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #0284c7, #0ea5e9);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      color: #ffffff;
      box-shadow: 0 0 12px rgba(14, 165, 233, 0.5);
    }
    .wallet-banner-info { display: flex; flex-direction: column; }
    .wallet-banner-title { font-size: 13px; font-weight: 800; color: #ffffff; }
    .wallet-banner-sub { font-size: 11px; color: #93c5fd; font-weight: 600; direction: ltr; text-align: right; }
    .wallet-status-tag {
      background: #0284c7;
      color: #ffffff;
      font-size: 11px;
      font-weight: 800;
      padding: 6px 12px;
      border-radius: 20px;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .wallet-status-tag.connected {
      background: rgba(34, 197, 94, 0.25);
      color: #4ade80;
      border-color: #22c55e;
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
      border-radius: 24px;
      padding: 16px 14px;
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
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
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
      margin-top: 10px;
      font-weight: 600;
    }
    .unclaimed-counter {
      font-size: 30px;
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
      font-size: 18px;
    }
    .hashrate-capsule {
      background: rgba(15, 23, 42, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      padding: 4px 12px;
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #93c5fd;
      font-weight: 700;
      margin-top: 4px;
    }
    .central-coin-stage {
      margin: 16px 0 12px 0;
      position: relative;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .coin-3d {
      width: 195px;
      height: 195px;
      border-radius: 50%;
      background: radial-gradient(circle at 35% 35%, #fde047 0%, #eab308 35%, #ca8a04 70%, #713f12 100%);
      border: 7px solid #fef08a;
      outline: 5px solid rgba(245, 158, 11, 0.45);
      box-shadow: 0 0 40px var(--gold-glow), inset 0 0 20px rgba(0, 0, 0, 0.5);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: transform 0.08s ease-out;
    }
    .coin-3d:active { transform: scale(0.95); }
    .coin-inner-details {
      width: 155px;
      height: 155px;
      border-radius: 50%;
      border: 2px dashed rgba(254, 240, 138, 0.6);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .coin-symbol {
      font-size: 48px;
      color: #ffffff;
      text-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
    }
    .coin-name {
      font-size: 22px;
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
      padding: 13px;
      font-size: 14px;
      margin-top: 8px;
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
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 12px;
    }
    .btn-upgrade-rig {
      background: linear-gradient(135deg, #1d4ed8, #3b82f6);
      color: #fff;
      font-weight: 800;
      border: none;
      border-radius: 16px;
      padding: 13px;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .btn-wallet-link {
      background: linear-gradient(135deg, #0284c7, #0ea5e9);
      color: #fff;
      font-weight: 800;
      border: none;
      border-radius: 16px;
      padding: 13px;
      font-size: 12px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
    .btn-wallet-link.connected {
      background: rgba(34, 197, 94, 0.2);
      border: 1px solid var(--accent-green);
      color: #4ade80;
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
    .convert-box {
      width: 100%;
      background: rgba(6, 11, 22, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 14px;
      margin-top: 4px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .input-row {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(0, 0, 0, 0.5);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 6px 10px;
    }
    .convert-input {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-size: 15px;
      font-weight: 800;
      direction: ltr;
      text-align: left;
    }
    .btn-max {
      background: rgba(245, 158, 11, 0.2);
      border: 1px solid var(--gold-primary);
      color: var(--gold-primary);
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 800;
      cursor: pointer;
    }
    .exchange-rate-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: var(--text-muted);
      padding: 0 4px;
    }
    .exchange-rate-row span { direction: ltr; }
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
      background: rgba(6, 10, 18, 0.95);
      border-top: 1px solid rgba(43, 62, 99, 0.4);
      backdrop-filter: blur(15px);
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

    #banned-overlay, #channel-lock-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(8, 10, 18, 0.98);
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

  <!-- شاشة الحظر التلقائي -->
  <div id="banned-overlay">
    <i class="fa-solid fa-triangle-exclamation" style="font-size:60px; color:#ef4444; margin-bottom:16px;"></i>
    <h2 style="color:#ef4444; margin-bottom:8px;">⛔ تم حظر هذا الحساب!</h2>
    <p id="ban-reason-text" style="font-size:13px; color:#cbd5e1; line-height:1.6;">تم اكتشاف وجود تكرار للحسابات من نفس الجهاز أو مخالفة لقوانين التعدين.</p>
  </div>

  <!-- قفل الاشتراك الإجباري في القناة -->
  <div id="channel-lock-overlay">
    <i class="fa-brands fa-telegram" style="font-size:65px; color:#38bdf8; margin-bottom:16px;"></i>
    <h2 style="color:#ffffff; margin-bottom:8px;">📢 خطوة أخيرة للتفعيل!</h2>
    <p style="font-size:13px; color:#cbd5e1; line-height:1.6; margin-bottom:20px;">
      لتفعيل جهاز التعدين واستلام مكافأة البداية، يجب الانضمام إلى قناة المشروع الرسمية:
      <br><strong style="color:#f59e0b;">@olka_ad</strong>
    </p>
    <div style="display:flex; flex-direction:column; gap:10px; width:100%; max-width:280px;">
      <button class="btn-upgrade-rig" onclick="window.open('https://t.me/olka_ad', '_blank')">
        <i class="fa-brands fa-telegram"></i> انضم إلى القناة الآن
      </button>
      <button class="btn-claim-rewards" onclick="recheckChannelSubscription()">
        <i class="fa-solid fa-rotate-right"></i> تحقق من الاشتراك وتفعيل التعدين
      </button>
    </div>
  </div>

  <div class="main-scroll-view">
    <div class="top-header">
      <div class="header-signal"><i class="fa-solid fa-signal"></i> <span data-i18n="live">مباشر</span></div>
      
      <div class="lang-switch-box">
        <button class="lang-btn" id="btn-lang-ar" onclick="selectLang('ar')">🇸🇦 AR</button>
        <button class="lang-btn" id="btn-lang-en" onclick="selectLang('en')">🇺🇸 EN</button>
        <button class="lang-btn" id="btn-lang-ru" onclick="selectLang('ru')">🇷🇺 RU</button>
      </div>
    </div>

    <div class="assets-container">
      <div class="assets-title-row">
        <div class="assets-total"><span data-i18n="total_label">الإجمالي:</span> <span id="total-assets">0.0000 OLK</span></div>
        <div class="assets-badge"><i class="fa-solid fa-shield-halved"></i> <span data-i18n="safe_assets">أصولي المحفوظة</span></div>
      </div>
      
      <div class="balance-cards-grid">
        <div class="bal-card">
          <div class="bal-card-title"><i class="fa-solid fa-coins" style="color:var(--gold-primary);"></i> <span data-i18n="olk_balance">رصيد OLK:</span></div>
          <div class="bal-card-value" style="color:var(--gold-primary);" id="app-balance-val">0.00 OLK</div>
        </div>
        <div class="bal-card">
          <div class="bal-card-title"><i class="fa-solid fa-gem" style="color:#60a5fa;"></i> <span data-i18n="ton_balance">رصيد TON (Gram):</span></div>
          <div class="bal-card-value" style="color:#60a5fa;" id="app-ton-val">0.0000 TON</div>
        </div>
      </div>

      <div class="wallet-connection-banner" onclick="handleConnectWalletClick()">
        <div class="wallet-banner-left">
          <div class="wallet-icon-box">
            <i class="fa-solid fa-wallet"></i>
          </div>
          <div class="wallet-banner-info">
            <span class="wallet-banner-title">TON Wallet (Telegram / Tonkeeper)</span>
            <span class="wallet-banner-sub" id="wallet-status-sub" data-i18n="wallet_sub_hint">اضغط لربط المحفظة مباشرة</span>
          </div>
        </div>
        <div class="wallet-status-tag" id="wallet-status-label" data-i18n="connect">اتصال</div>
      </div>
    </div>

    <!-- صفحة 1: شاشة التعدين -->
    <div class="page-tab active" id="tab-mining">
      <div class="mining-hero-card">
        <div class="miner-status-badge">
          <span data-i18n="miner_lvl">معدن مستوى</span> <span id="level-display">1</span>
          <span class="status-online" data-i18n="status_active">نشط</span>
        </div>

        <div class="unclaimed-subtitle" data-i18n="unclaimed_text">أرباح تعدين OLK غير المطالب بها</div>
        <div class="unclaimed-counter">
          <span>OLK</span>
          <div id="unclaimed-val">0.000000</div>
        </div>

        <div class="hashrate-capsule">
          <i class="fa-solid fa-gauge-high"></i>
          <span><span data-i18n="speed_text">السرعة:</span> <strong id="speed-val">0.25</strong> TH/s</span>
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
          <i class="fa-solid fa-cloud-arrow-down"></i> <span data-i18n="btn_claim">المطالبة بأرباح OLK وإضافتها للرصيد</span>
        </button>
      </div>

      <div class="hero-actions-grid">
        <button class="btn-upgrade-rig" onclick="switchNav('miners')">
          <span data-i18n="btn_upgrade_ton">ترقية عبر TON</span> <i class="fa-solid fa-bolt"></i>
        </button>
        <button class="btn-wallet-link" id="btn-connect-wallet" onclick="handleConnectWalletClick()">
          <i class="fa-solid fa-wallet"></i> <span id="wallet-btn-text">CONNECT WALLET</span>
        </button>
      </div>
    </div>

    <!-- صفحة 2: المحفظة -->
    <div class="page-tab" id="tab-wallet">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--gold-primary); font-size:15px; display:flex; justify-content:space-between; align-items:center;">
          <span data-i18n="convert_title">💳 صرافة OLK إلى TON (Gram)</span>
          <span style="font-size:11px; color:#38bdf8; direction:ltr;">1 TON = 10,000 OLK</span>
        </div>

        <div class="convert-box">
          <div style="display:flex; justify-content:space-between; font-size:12px;">
            <span style="color:var(--text-muted);" data-i18n="convert_input_hint">كمية OLK المراد تحويلها لـ TON:</span>
            <span style="color:#f59e0b; direction:ltr;" id="available-olk-convert">0.00</span>
          </div>

          <div class="input-row">
            <input type="number" id="convert-input-amount" class="convert-input" placeholder="1000" oninput="calculateConvertPreview()">
            <button class="btn-max" onclick="setMaxConvert()">MAX</button>
          </div>

          <div class="exchange-rate-row">
            <span data-i18n="will_receive">ستحصل على:</span>
            <strong style="color:#4ade80; font-size:14px;" id="convert-preview-val">0.0000 TON</strong>
          </div>

          <button class="btn-claim-rewards" style="margin-top:2px;" onclick="convertOlkDirect()">
            <i class="fa-solid fa-repeat"></i> <span data-i18n="btn_confirm_convert">تحويل إلى رصيد TON</span>
          </button>
        </div>

        <hr style="border:0; border-top:1px solid var(--card-border); margin:6px 0;">

        <div style="font-weight:bold; color:#38bdf8; font-size:14px; margin-top:2px;" data-i18n="withdraw_section_title">
          <i class="fa-solid fa-money-bill-transfer"></i> سحب TON إلى محفظتك
        </div>
        
        <div class="convert-box">
          <div style="display:flex; justify-content:space-between; font-size:12px;">
            <span style="color:var(--text-muted);" data-i18n="withdraw_amount_hint">أدخل مبلغ TON المراد سحبه:</span>
            <span style="color:#f87171; direction:ltr;" data-i18n="min_withdraw_rule">الحد الأدنى: 0.1 TON</span>
          </div>

          <div class="input-row">
            <input type="number" step="0.01" id="withdraw-custom-amount" class="convert-input" placeholder="0.1" oninput="validateWithdrawAmount()">
            <button class="btn-max" onclick="setMaxWithdraw()">MAX</button>
          </div>
        </div>

        <div style="font-size:12px; color:#cbd5e1; margin-top:4px;" data-i18n="connected_wallet_lbl">المحفظة المرتبطة بالسحب:</div>
        <div id="connected-wallet-display" style="font-size:11px; color:#93c5fd; background:rgba(0,0,0,0.5); padding:10px; border-radius:12px; word-break:break-all; direction:ltr; text-align:left;">
          ⚠️ لم يتم ربط محفظة TON بعد
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:6px;">
          <button class="btn-upgrade-rig" style="background:#059669;" onclick="depositTonDirect()">
            <i class="fa-solid fa-arrow-down"></i> <span data-i18n="btn_deposit">إيداع 0.1 TON</span>
          </button>
          <button class="btn-upgrade-rig" onclick="requestWithdrawalToConnectedWallet()">
            <i class="fa-solid fa-arrow-up"></i> <span data-i18n="btn_withdraw">سحب TON المحدد</span>
          </button>
        </div>
      </div>
    </div>

    <!-- صفحة 3: الأصدقاء -->
    <div class="page-tab" id="tab-frens">
      <div class="card-panel">
        <div style="font-weight:bold; color:#bef264; font-size:15px;"><i class="fa-solid fa-users"></i> <span data-i18n="frens_title">شبكة التعدين التشاركية (الإحالات)</span></div>
        <div style="font-size:13px; color:#cbd5e1;" data-i18n="frens_desc">شارك رابط جهازك واحصل على <strong>80 OLK</strong> مجاناً فور دخول صديقك لتطبيق الويب وتفعيل التعدين!</div>
        <button class="btn-upgrade-rig" style="width:100%;" onclick="copyReferralLink()">
          <i class="fa-solid fa-copy"></i> <span data-i18n="btn_copy_ref">نسخ رابط الدعوة الخاص بي</span>
        </button>
      </div>
    </div>

    <!-- صفحة 4: المعدنون -->
    <div class="page-tab" id="tab-miners">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--accent-cyan); font-size:15px; display:flex; justify-content:space-between; align-items:center;">
          <span><i class="fa-solid fa-microchip"></i> <span data-i18n="miners_title">ترقية أجهزة التعدين</span></span>
          <span style="font-size:11px; color:#38bdf8;" data-i18n="pay_via_ton">الدفع عبر رصيد TON</span>
        </div>
        <div style="font-size:12px; color:var(--text-muted); margin-bottom:4px;" data-i18n="miners_desc">
          قم بإيداع TON في المحفظة لشراء أجهزة التعدين ومضاعفة سرعة جمع عملة OLK!
        </div>
        
        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">CPU S-Cloud Rig</div>
            <div style="font-size:11px; color:var(--accent-green); direction:ltr; text-align:right;">+0.20 TH/s</div>
          </div>
          <button class="btn-upgrade-rig" style="padding:8px 12px; font-size:12px;" onclick="buyRigWithTon(1, 0.05, 0.20)">0.05 TON</button>
        </div>

        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">GPU Quantum Rig</div>
            <div style="font-size:11px; color:var(--accent-green); direction:ltr; text-align:right;">+0.60 TH/s</div>
          </div>
          <button class="btn-upgrade-rig" style="padding:8px 12px; font-size:12px;" onclick="buyRigWithTon(2, 0.15, 0.60)">0.15 TON</button>
        </div>

        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">ASIC VIP Titan</div>
            <div style="font-size:11px; color:var(--accent-green); direction:ltr; text-align:right;">+2.00 TH/s</div>
          </div>
          <button class="btn-upgrade-rig" style="padding:8px 12px; font-size:12px;" onclick="buyRigWithTon(3, 0.40, 2.00)">0.40 TON</button>
        </div>
      </div>
    </div>

    <!-- صفحة 5: المهام -->
    <div class="page-tab" id="tab-tasks">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--gold-primary); font-size:15px;"><i class="fa-solid fa-list-check"></i> <span data-i18n="tasks_title">مهام جمع عملة OLK المجانية</span></div>
        
        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">قناة OLKA AD الرسمية</div>
            <div style="font-size:11px; color:var(--gold-primary);">+10 OLK</div>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="btn-upgrade-rig" style="padding:6px 10px; font-size:11px;" onclick="window.open('https://t.me/olka_ad', '_blank')" data-i18n="btn_join">انضمام</button>
            <button class="btn-upgrade-rig" style="padding:6px 10px; font-size:11px; background:#10b981;" onclick="checkChannelTask('task_chan_main')" data-i18n="btn_verify">تحقق</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="bottom-bar">
    <div class="nav-link" onclick="switchNav('wallet', this)">
      <i class="fa-solid fa-wallet"></i>
      <span data-i18n="nav_wallet">المحفظة</span>
    </div>
    <div class="nav-link" onclick="switchNav('frens', this)">
      <i class="fa-solid fa-user-group"></i>
      <span data-i18n="nav_frens">الأصدقاء</span>
    </div>
    <div class="nav-link active" onclick="switchNav('mining', this)">
      <i class="fa-solid fa-pickaxe"></i>
      <span data-i18n="nav_mine">التعدين</span>
    </div>
    <div class="nav-link" onclick="switchNav('miners', this)">
      <i class="fa-solid fa-bolt"></i>
      <span data-i18n="nav_miners">المعدنون</span>
    </div>
    <div class="nav-link" onclick="switchNav('tasks', this)">
      <div class="notify-dot">1</div>
      <i class="fa-solid fa-clipboard-list"></i>
      <span data-i18n="nav_tasks">المهام</span>
    </div>
  </div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) { tg.ready(); tg.expand(); }

    const urlParams = new URLSearchParams(window.location.search);
    const userId = tg?.initDataUnsafe?.user?.id || urlParams.get('user_id') || 1932161126;

    function generateDeviceFingerprint() {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl');
      const debugInfo = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
      const renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'no-gl';
      const raw = [
        navigator.userAgent,
        screen.height + 'x' + screen.width,
        navigator.hardwareConcurrency || 0,
        renderer
      ].join('###');
      
      let hash = 0;
      for (let i = 0; i < raw.length; i++) {
        hash = ((hash << 5) - hash) + raw.charCodeAt(i);
        hash |= 0;
      }
      return 'dev_' + Math.abs(hash).toString(16);
    }
    const clientFingerprint = generateDeviceFingerprint();

    const translations = {
      ar: {
        live: "مباشر",
        total_label: "الإجمالي:",
        safe_assets: "أصولي المحفوظة",
        olk_balance: "رصيد OLK:",
        ton_balance: "رصيد TON (Gram):",
        wallet_sub_hint: "اضغط لربط المحفظة مباشرة",
        connect: "اتصال",
        miner_lvl: "معدن مستوى",
        status_active: "نشط",
        unclaimed_text: "أرباح تعدين OLK غير المطالب بها",
        speed_text: "السرعة:",
        btn_claim: "المطالبة بأرباح OLK وإضافتها للرصيد",
        btn_upgrade_ton: "ترقية عبر TON",
        convert_title: "💳 صرافة OLK إلى TON (Gram)",
        convert_input_hint: "كمية OLK المراد تحويلها لـ TON:",
        will_receive: "ستحصل على:",
        btn_confirm_convert: "تحويل إلى رصيد TON",
        withdraw_section_title: "سحب TON إلى محفظتك",
        withdraw_amount_hint: "أدخل مبلغ TON المراد سحبه:",
        min_withdraw_rule: "الحد الأدنى: 0.1 TON",
        connected_wallet_lbl: "المحفظة المرتبطة بالسحب:",
        btn_deposit: "إيداع 0.1 TON",
        btn_withdraw: "سحب TON المحدد",
        frens_title: "شبكة التعدين التشاركية (الإحالات)",
        frens_desc: "شارك رابط جهازك واحصل على 80 OLK مجاناً فور دخول صديقك لتطبيق الويب وتفعيل التعدين!",
        btn_copy_ref: "نسخ رابط الدعوة الخاص بي",
        miners_title: "ترقية أجهزة التعدين",
        pay_via_ton: "الدفع عبر رصيد TON",
        miners_desc: "قم بإيداع TON في المحفظة لشراء أجهزة التعدين ومضاعفة سرعة جمع عملة OLK!",
        tasks_title: "مهام جمع عملة OLK المجانية",
        btn_join: "انضمام",
        btn_verify: "تحقق",
        nav_wallet: "المحفظة",
        nav_frens: "الأصدقاء",
        nav_mine: "التعدين",
        nav_miners: "المعدنون",
        nav_tasks: "المهام"
      },
      en: {
        live: "LIVE",
        total_label: "Total:",
        safe_assets: "My Protected Assets",
        olk_balance: "OLK Balance:",
        ton_balance: "TON (Gram) Balance:",
        wallet_sub_hint: "Click to bind wallet directly",
        connect: "Connect",
        miner_lvl: "Miner Level",
        status_active: "Active",
        unclaimed_text: "Unclaimed OLK Mining Earnings",
        speed_text: "Speed:",
        btn_claim: "Claim OLK Earnings to Balance",
        btn_upgrade_ton: "Upgrade via TON",
        convert_title: "💳 Swap OLK to TON (Gram)",
        convert_input_hint: "OLK amount to swap into TON:",
        will_receive: "You will receive:",
        btn_confirm_convert: "Convert to TON Balance",
        withdraw_section_title: "Withdraw TON to Your Wallet",
        withdraw_amount_hint: "Enter TON amount to withdraw:",
        min_withdraw_rule: "Minimum: 0.1 TON",
        connected_wallet_lbl: "Connected withdrawal wallet:",
        btn_deposit: "Deposit 0.1 TON",
        btn_withdraw: "Withdraw Selected TON",
        frens_title: "Mining Referral Network",
        frens_desc: "Share your invite link and get 80 OLK free once your friend opens the web app and activates mining!",
        btn_copy_ref: "Copy My Referral Link",
        miners_title: "Upgrade Mining Hardware",
        pay_via_ton: "Pay via TON Balance",
        miners_desc: "Deposit TON to purchase mining hardware and multiply your OLK generation rate!",
        tasks_title: "Free OLK Reward Tasks",
        btn_join: "Join",
        btn_verify: "Verify",
        nav_wallet: "Wallet",
        nav_frens: "Friends",
        nav_mine: "Mining",
        nav_miners: "Miners",
        nav_tasks: "Tasks"
      },
      ru: {
        live: "ОНЛАЙН",
        total_label: "Всего:",
        safe_assets: "Мои защищенные активы",
        olk_balance: "Баланс OLK:",
        ton_balance: "Баланс TON (Gram):",
        wallet_sub_hint: "Нажмите, чтобы привязать кошелек",
        connect: "Подключить",
        miner_lvl: "Майнер Ур.",
        status_active: "Активен",
        unclaimed_text: "Несобранный доход майнинга OLK",
        speed_text: "Скорость:",
        btn_claim: "Забрать OLK на баланс",
        btn_upgrade_ton: "Улучшить за TON",
        convert_title: "💳 Обмен OLK на TON (Gram)",
        convert_input_hint: "Количество OLK для обмена на TON:",
        will_receive: "Вы получите:",
        btn_confirm_convert: "Конвертировать в TON",
        withdraw_section_title: "Вывод TON на ваш кошелек",
        withdraw_amount_hint: "Введите сумму TON для вывода:",
        min_withdraw_rule: "Минимум: 0.1 TON",
        connected_wallet_lbl: "Привязанный кошелек:",
        btn_deposit: "Депозит 0.1 TON",
        btn_withdraw: "Вывести выбранный TON",
        frens_title: "Партнерская сеть майнинга",
        frens_desc: "Делитесь ссылкой и получайте 80 OLK бесплатно, когда друг войдет в приложение и запустит майнинг!",
        btn_copy_ref: "Скопировать мою ссылку",
        miners_title: "Улучшение оборудования",
        pay_via_ton: "Оплата с баланса TON",
        miners_desc: "Пополняйте TON для покупки оборудования и ускорения добычи OLK!",
        tasks_title: "Задания на получение OLK",
        btn_join: "Войти",
        btn_verify: "Проверить",
        nav_wallet: "Кошелек",
        nav_frens: "Друзья",
        nav_mine: "Майнинг",
        nav_miners: "Майнеры",
        nav_tasks: "Задания"
      }
    };

    let currentLang = localStorage.getItem("olk_lang") || "ar";

    function selectLang(lang) {
      currentLang = lang;
      localStorage.setItem("olk_lang", lang);
      document.querySelectorAll(".lang-btn").forEach(b => b.classList.remove("active"));
      const btn = document.getElementById("btn-lang-" + lang);
      if (btn) btn.classList.add("active");

      document.documentElement.dir = (lang === "ar") ? "rtl" : "ltr";
      const dict = translations[lang] || translations.ar;
      document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (dict[key]) el.innerText = dict[key];
      });
      refreshScreen();
    }

    let appOlk = 0;
    let appTon = 0;
    let unclaimed = 0;
    let speed = 0.25;
    let minerLevel = 1;
    let connectedWalletAddress = null;

    const totalAssetsEl = document.getElementById("total-assets");
    const appBalEl = document.getElementById("app-balance-val");
    const appTonEl = document.getElementById("app-ton-val");
    const unclaimedValEl = document.getElementById("unclaimed-val");
    const speedValEl = document.getElementById("speed-val");
    const levelDisplayEl = document.getElementById("level-display");
    const walletStatusLabel = document.getElementById("wallet-status-label");
    const walletStatusSub = document.getElementById("wallet-status-sub");
    const walletBtn = document.getElementById("btn-connect-wallet");
    const walletBtnText = document.getElementById("wallet-btn-text");
    const walletDisplay = document.getElementById("connected-wallet-display");
    const convertInput = document.getElementById("convert-input-amount");
    const convertPreview = document.getElementById("convert-preview-val");
    const availableOlkConvert = document.getElementById("available-olk-convert");
    const withdrawAmountInput = document.getElementById("withdraw-custom-amount");

    const tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
      manifestUrl: window.location.origin + '/tonconnect-manifest.json'
    });

    tonConnectUI.onStatusChange(async (wallet) => {
      if (wallet) {
        try {
          connectedWalletAddress = TON_CONNECT_UI.toUserFriendlyAddress(wallet.account.address);
        } catch(e) {
          connectedWalletAddress = wallet.account.address;
        }
        
        const shortAddr = connectedWalletAddress.slice(0, 4) + '...' + connectedWalletAddress.slice(-4);
        walletBtnText.innerText = shortAddr;
        walletStatusLabel.innerText = "OK ✅";
        walletStatusLabel.classList.add("connected");
        walletStatusSub.innerText = shortAddr;
        walletBtn.classList.add("connected");
        walletDisplay.innerText = connectedWalletAddress;

        await fetch("/api/save_wallet", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, address: connectedWalletAddress })
        });
      } else {
        connectedWalletAddress = null;
        walletBtnText.innerText = "CONNECT WALLET";
        walletStatusLabel.innerText = (currentLang === "ar") ? "اتصال" : "Connect";
        walletStatusLabel.classList.remove("connected");
        walletStatusSub.innerText = translations[currentLang].wallet_sub_hint;
        walletBtn.classList.remove("connected");
        walletDisplay.innerText = "⚠️ لم يتم ربط محفظة TON بعد";
      }
    });

    function handleConnectWalletClick() {
      if (tonConnectUI.connected) {
        tonConnectUI.disconnect();
      } else {
        tonConnectUI.openModal();
      }
    }

    async function loadData() {
      try {
        const res = await fetch(`/api/get_user?user_id=${userId}&fp=${clientFingerprint}`);
        const data = await res.json();
        if (data.banned) {
          if (data.ban_reason) {
            document.getElementById("ban-reason-text").innerText = "سبب الحظر: " + data.ban_reason;
          }
          document.getElementById("banned-overlay").style.display = "flex";
          return;
        } else {
          document.getElementById("banned-overlay").style.display = "none";
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
          if (data.saved_wallet) {
            connectedWalletAddress = data.saved_wallet;
            const shortAddr = connectedWalletAddress.slice(0, 4) + '...' + connectedWalletAddress.slice(-4);
            walletBtnText.innerText = shortAddr;
            walletStatusLabel.innerText = "OK ✅";
            walletStatusLabel.classList.add("connected");
            walletStatusSub.innerText = shortAddr;
            walletBtn.classList.add("connected");
            walletDisplay.innerText = connectedWalletAddress;
          }
          if (data.offline_mined) {
            unclaimed += data.offline_mined;
          }
          refreshScreen();
        }
      } catch (err) {
        console.error("Data load failed", err);
      }
    }

    async function recheckChannelSubscription() {
      await loadData();
      if (document.getElementById("channel-lock-overlay").style.display === "none") {
        alert("🎉 تم التحقق بنجاح! تم تفعيل جهاز التعدين الخاص بك.");
      } else {
        alert("❌ لم يتم العثور على اشتراكك في القناة بعد! تأكد من الانضمام ثم حاول مجدداً.");
      }
    }

    function refreshScreen() {
      totalAssetsEl.innerText = (appOlk + unclaimed).toFixed(4) + " OLK";
      appBalEl.innerText = appOlk.toFixed(2) + " OLK";
      appTonEl.innerText = appTon.toFixed(4) + " TON";
      unclaimedValEl.innerText = unclaimed.toFixed(6);
      speedValEl.innerText = speed.toFixed(2);
      levelDisplayEl.innerText = minerLevel;
      availableOlkConvert.innerText = (currentLang === "ar" ? "المتاح: " : "Available: ") + appOlk.toFixed(2);
    }

    function calculateConvertPreview() {
      const amt = parseFloat(convertInput.value) || 0;
      const tonVal = amt / 10000;
      convertPreview.innerText = tonVal.toFixed(4) + " TON";
    }

    function setMaxConvert() {
      convertInput.value = Math.floor(appOlk);
      calculateConvertPreview();
    }

    function setMaxWithdraw() {
      withdrawAmountInput.value = appTon.toFixed(4);
    }

    function validateWithdrawAmount() {
      const val = parseFloat(withdrawAmountInput.value) || 0;
      if (val > appTon) withdrawAmountInput.value = appTon.toFixed(4);
    }

    setInterval(() => {
      unclaimed += (speed * 0.000030);
      unclaimedValEl.innerText = unclaimed.toFixed(6);
      totalAssetsEl.innerText = (appOlk + unclaimed).toFixed(4) + " OLK";
    }, 100);

    async function claimRewardsToDb() {
      if (unclaimed < 0.001) {
        alert(currentLang === "ar" ? "⚠️ أرباح التعدين قليلة جداً حالياً، واصل التعدين!" : "⚠️ Not enough mined OLK to claim yet!");
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
      unclaimed += (speed * 0.0010);
      unclaimedValEl.innerText = unclaimed.toFixed(6);
      if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred("light");
    }

    async function buyRigWithTon(rigId, tonCost, speedGain) {
      if (appTon < tonCost) {
        alert(currentLang === "ar" ? `⚠️ رصيد TON غير كافٍ! يلزمك ${tonCost} TON.` : `⚠️ Insufficient TON!`);
        switchNav('wallet');
        return;
      }
      appTon -= tonCost;
      speed += speedGain;
      minerLevel += 1;
      refreshScreen();

      await fetch("/api/upgrade_rig_ton", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, cost_ton: tonCost, new_speed: speed, new_level: minerLevel })
      });
      alert(currentLang === "ar" ? `🎉 تم شراء الترقية بنجاح! السرعة الآن: ${speed.toFixed(2)} TH/s` : `🎉 Hardware upgraded!`);
    }

    async function convertOlkDirect() {
      const amountToConvert = parseFloat(convertInput.value);
      if (!amountToConvert || amountToConvert <= 0) {
        alert(currentLang === "ar" ? "⚠️ يرجى كتابة كمية OLK التي ترغب في تحويلها أولاً!" : "⚠️ Enter OLK amount first!");
        return;
      }
      if (amountToConvert > appOlk) {
        alert(currentLang === "ar" ? "⚠️ الكمية المدخلة أكبر من رصيد OLK المتاح!" : "⚠️ Amount exceeds available balance!");
        return;
      }
      const res = await fetch("/api/convert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, amount: amountToConvert })
      });
      const data = await res.json();
      if (data.ok) {
        appOlk = data.olk_balance;
        appTon = data.ton_balance;
        convertInput.value = "";
        calculateConvertPreview();
        refreshScreen();
        alert(currentLang === "ar" ? `✅ تم تحويل ${amountToConvert} OLK بنجاح!` : `✅ Successfully swapped ${amountToConvert} OLK!`);
      } else {
        alert(data.msg);
      }
    }

    async function depositTonDirect() {
      if (!tonConnectUI.connected) {
        alert(currentLang === "ar" ? "❌ يرجى ربط محفظة TON أولاً!" : "❌ Please connect TON wallet first!");
        handleConnectWalletClick();
        return;
      }
      const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 360,
        messages: [
          {
            address: "PROJECT_TON_WALLET_PLACEHOLDER",
            amount: "100000000"
          }
        ]
      };
      try {
        const result = await tonConnectUI.sendTransaction(transaction);
        if (result) {
          appTon += 0.1;
          refreshScreen();
          await fetch("/api/deposit_ton_credit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, amount_ton: 0.1 })
          });
          alert(currentLang === "ar" ? "🎉 تم تأكيد إيداع 0.1 TON بنجاح!" : "🎉 Deposit of 0.1 TON confirmed!");
        }
      } catch (e) {
        alert(currentLang === "ar" ? "❌ تم إلغاء المعاملة أو فشل الإيداع." : "❌ Transaction cancelled.");
      }
    }

    async function requestWithdrawalToConnectedWallet() {
      if (!connectedWalletAddress) {
        alert(currentLang === "ar" ? "❌ يرجى ربط محفظة TON أولاً عبر زر CONNECT WALLET!" : "❌ Connect TON wallet first!");
        handleConnectWalletClick();
        return;
      }
      const withdrawAmount = parseFloat(withdrawAmountInput.value) || 0;
      if (withdrawAmount < 0.1) {
        alert(currentLang === "ar" ? "⚠️ الحد الأدنى للسحب هو 0.1 TON!" : "⚠️ Minimum withdrawal is 0.1 TON!");
        return;
      }
      if (withdrawAmount > appTon) {
        alert(currentLang === "ar" ? "⚠️ رصيدك المتوفر غير كافٍ لسحب هذا المبلغ!" : "⚠️ Insufficient TON balance!");
        return;
      }

      const res = await fetch("/api/withdraw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, address: connectedWalletAddress, amount_ton: withdrawAmount })
      });
      const data = await res.json();
      if (data.ok) {
        appTon = data.remaining_ton;
        withdrawAmountInput.value = "";
        refreshScreen();
        alert(currentLang === "ar" ? `✅ تم إرسال طلب سحب ${withdrawAmount.toFixed(4)} TON بنجاح للمراجعة!` : `✅ Withdrawal request submitted!`);
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
      alert(currentLang === "ar" ? "✅ تم نسخ رابط الإحالة الخاص بك!" : "✅ Referral link copied!");
    }

    async function checkChannelTask(taskId) {
      try {
        const res = await fetch("/api/verify_channel_task", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId, task_id: taskId })
        });
        const data = await res.json();
        alert(data.msg);
        if (data.ok) {
          appOlk += data.reward;
          refreshScreen();
        }
      } catch (err) {
        alert(currentLang === "ar" ? "حدث خطأ أثناء التحقق!" : "Verification error!");
      }
    }

    selectLang(currentLang);
    loadData();
  </script>
</body>
</html>
""".replace("PROJECT_TON_WALLET_PLACEHOLDER", PROJECT_TON_WALLET)

TON_MANIFEST = {
    "url": WEBAPP_URL,
    "name": "OLKA VIP GAME",
    "iconUrl": "https://telegram.org/img/t_logo.png",
    "termsOfUseUrl": WEBAPP_URL,
    "privacyPolicyUrl": WEBAPP_URL
}

async def init_db():
    async with aiosqlite.connect("olka_vip.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            phone_number TEXT,
            olk_balance REAL DEFAULT 0.0,
            ton_balance REAL DEFAULT 0.0,
            last_claim INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT NULL,
            ref_reward_claimed INTEGER DEFAULT 0,
            mining_speed REAL DEFAULT 0.25,
            miner_level INTEGER DEFAULT 1,
            last_mining_timestamp INTEGER DEFAULT 0,
            tasks_completed TEXT DEFAULT '[]',
            saved_wallet TEXT DEFAULT NULL,
            ip_address TEXT DEFAULT NULL,
            device_fingerprint TEXT DEFAULT NULL,
            is_banned INTEGER DEFAULT 0,
            ban_reason TEXT DEFAULT NULL,
            activated_miner INTEGER DEFAULT 0,
            is_whitelisted INTEGER DEFAULT 0
        )
        """)
        for col_def in [
            "ton_balance REAL DEFAULT 0.0",
            "referred_by INTEGER DEFAULT NULL",
            "ref_reward_claimed INTEGER DEFAULT 0",
            "mining_speed REAL DEFAULT 0.25",
            "miner_level INTEGER DEFAULT 1",
            "last_mining_timestamp INTEGER DEFAULT 0",
            "tasks_completed TEXT DEFAULT '[]'",
            "saved_wallet TEXT DEFAULT NULL",
            "ip_address TEXT DEFAULT NULL",
            "device_fingerprint TEXT DEFAULT NULL",
            "is_banned INTEGER DEFAULT 0",
            "ban_reason TEXT DEFAULT NULL",
            "activated_miner INTEGER DEFAULT 0",
            "is_whitelisted INTEGER DEFAULT 0"
        ]:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col_def}")
            except Exception:
                pass

        await db.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount_ton REAL,
            wallet_address TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at INTEGER DEFAULT 0
        )
        """)
        await db.commit()

async def api_manifest(request):
    return web.json_response(TON_MANIFEST)

async def api_save_wallet(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        address = str(data.get("address", "")).strip()
        friendly_address = raw_to_user_friendly(address)

        async with aiosqlite.connect("olka_vip.db") as db:
            await db.execute("UPDATE users SET saved_wallet = ? WHERE user_id = ?", (friendly_address, user_id))
            await db.commit()
        return web.json_response({"ok": True, "address": friendly_address})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_get_user(request):
    try:
        user_id = int(request.query.get("user_id", 0))
        client_fp = str(request.query.get("fp", "")).strip()
        client_ip = request.headers.get("X-Forwarded-For", request.remote).split(",")[0].strip()
        now = int(time.time())

        is_sub = True
        try:
            member = await bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
            if member.status in ["left", "kicked"]:
                is_sub = False
        except Exception:
            is_sub = True

        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT is_banned, ban_reason, olk_balance, ton_balance, mining_speed, miner_level, last_mining_timestamp, saved_wallet, referred_by, ref_reward_claimed, activated_miner, is_whitelisted FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()

            if row and row[0] == 1:
                return web.json_response({"ok": False, "banned": True, "ban_reason": row[1] or "مخالفة شروط التعدين"})

            # إذا كان المستخدم موثقاً ومضافاً للقائمة البيضاء، يتم تجاوز فحص البصمة نهائياً
            is_whitelisted = (row and row[11] == 1) or (user_id == ADMIN_ID)

            if client_fp and not is_whitelisted:
                async with db.execute("SELECT user_id FROM users WHERE device_fingerprint = ? AND user_id != ? AND is_whitelisted = 0", (client_fp, user_id)) as cur:
                    duplicate = await cur.fetchone()
                    if duplicate:
                        await db.execute("UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?", ("استخدام نفس الجهاز لعدة حسابات", user_id))
                        await db.commit()
                        try:
                            await bot.send_message(
                                chat_id=ADMIN_ID,
                                text=f"🚨 **تنبيه أمني: حظر جهاز مكرر تلقائياً**\n\n👤 الحساب المخالف: `{user_id}`\n🌐 مرتبط بنفس جهاز الحساب: `{duplicate[0]}`\n📱 البصمة: `{client_fp}`",
                                parse_mode="Markdown"
                            )
                        except Exception:
                            pass
                        return web.json_response({"ok": False, "banned": True, "ban_reason": "استخدام نفس الجهاز لعدة حسابات"})

            if not is_sub:
                return web.json_response({"ok": True, "need_sub": True})

            if row:
                olk, ton, speed, lvl, last_ts, saved_wallet, ref_by, ref_claimed, activated = row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]
                
                if activated == 0:
                    olk += SIGNUP_BONUS
                    await db.execute("UPDATE users SET activated_miner = 1, olk_balance = ? WHERE user_id = ?", (olk, user_id))
                    
                    if ref_by and ref_claimed == 0:
                        await db.execute("UPDATE users SET olk_balance = olk_balance + ? WHERE user_id = ?", (REFERRAL_REWARD, ref_by))
                        await db.execute("UPDATE users SET ref_reward_claimed = 1 WHERE user_id = ?", (user_id,))
                        try:
                            await bot.send_message(
                                chat_id=ref_by,
                                text=f"🎉 **إحالة مؤكدة وناجحة!**\nقام صديقك بالدخول للتطبيق وتفعيل جهاز التعدين.\n💰 تمت إضافة **+{REFERRAL_REWARD:.0f} OLK** إلى محفظتك بنجاح!"
                            )
                        except Exception:
                            pass

                offline_mined = 0.0
                if last_ts > 0:
                    diff = min(now - last_ts, 86400)
                    offline_mined = diff * (speed * 0.000030 * 10)
                
                await db.execute("UPDATE users SET last_mining_timestamp = ?, ip_address = ?, device_fingerprint = ? WHERE user_id = ?",
                                 (now, client_ip, client_fp, user_id))
                await db.commit()
                return web.json_response({
                    "ok": True,
                    "need_sub": False,
                    "banned": False,
                    "olk_balance": olk,
                    "ton_balance": ton,
                    "mining_speed": speed,
                    "miner_level": lvl,
                    "saved_wallet": raw_to_user_friendly(saved_wallet),
                    "offline_mined": offline_mined
                })
            else:
                await db.execute("INSERT OR IGNORE INTO users (user_id, last_mining_timestamp, mining_speed, ip_address, device_fingerprint, olk_balance, activated_miner) VALUES (?, ?, 0.25, ?, ?, ?, 1)",
                                 (user_id, now, client_ip, client_fp, SIGNUP_BONUS))
                await db.commit()
                return web.json_response({
                    "ok": True,
                    "need_sub": False,
                    "banned": False,
                    "olk_balance": SIGNUP_BONUS,
                    "ton_balance": 0.0,
                    "mining_speed": 0.25,
                    "miner_level": 1,
                    "saved_wallet": None,
                    "offline_mined": 0.0
                })
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

async def api_upgrade_rig_ton(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        cost_ton = float(data.get("cost_ton"))
        new_speed = float(data.get("new_speed"))
        new_level = int(data.get("new_level"))

        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT ton_balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if not row or row[0] < cost_ton:
                    return web.json_response({"ok": False, "msg": "رصيد TON غير كافٍ"})

            await db.execute("UPDATE users SET ton_balance = ton_balance - ?, mining_speed = ?, miner_level = ? WHERE user_id = ?",
                             (cost_ton, new_speed, new_level, user_id))
            await db.commit()
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_deposit_ton_credit(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        amount_ton = float(data.get("amount_ton", 0.1))

        async with aiosqlite.connect("olka_vip.db") as db:
            await db.execute("UPDATE users SET ton_balance = ton_balance + ? WHERE user_id = ?", (amount_ton, user_id))
            await db.commit()
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_convert(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        amount = float(data.get("amount", 0))

        if amount <= 0:
            return web.json_response({"ok": False, "msg": "يرجى تحديد كمية صحيحة"})

        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT olk_balance, ton_balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if not row or row[0] < amount:
                    return web.json_response({"ok": False, "msg": "رصيد OLK غير كافٍ للتحويل"})
                
                olk_current, ton_current = row[0], row[1]
                ton_add = amount / CONVERSION_RATE
                new_olk = olk_current - amount
                new_ton = ton_current + ton_add

                await db.execute("UPDATE users SET olk_balance = ?, ton_balance = ? WHERE user_id = ?", (new_olk, new_ton, user_id))
                await db.commit()
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

        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT ton_balance, phone_number FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if not row or row[0] < withdraw_amount:
                    return web.json_response({"ok": False, "msg": "رصيدك المتوفر أقل من المبلغ المطلوب"})

                current_ton, phone = row[0], row[1] or "غير موثق"
                remaining = current_ton - withdraw_amount

                cur_ins = await db.execute("INSERT INTO withdrawals (user_id, amount_ton, wallet_address, created_at) VALUES (?, ?, ?, ?)",
                                 (user_id, withdraw_amount, friendly_address, now))
                withdrawal_id = cur_ins.lastrowid
                await db.execute("UPDATE users SET ton_balance = ? WHERE user_id = ?", (remaining, user_id))
                await db.commit()

        admin_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ موافقة وإرسال", callback_data=f"adm_app_{withdrawal_id}"),
                InlineKeyboardButton(text="❌ رفض", callback_data=f"adm_rej_{withdrawal_id}")
            ]
        ])
        admin_notification = (
            f"🚨 **طلب سحب TON جديد #{withdrawal_id}**\n\n"
            f"👤 المستخدم: `{user_id}`\n"
            f"📱 الهاتف: `{phone}`\n"
            f"💎 المبلغ المطلوب: `{withdraw_amount:.4f} TON`\n"
            f"📫 المحفظة المستلمة:\n`{friendly_address}`"
        )
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=admin_notification, reply_markup=admin_kb, parse_mode="Markdown")
        except Exception:
            pass

        return web.json_response({"ok": True, "remaining_ton": remaining})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

async def api_verify_channel_task(request):
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        task_id = data.get("task_id")

        task_data = next((t for t in CHANNELS_TASKS if t["id"] == task_id), None)
        if not task_data:
            return web.json_response({"ok": False, "msg": "المهمة غير موجودة"})

        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT tasks_completed FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                tasks = json.loads(row[0]) if row and row[0] else []
                
                if task_id in tasks:
                    return web.json_response({"ok": False, "msg": "لقد استلمت مكافأة هذه القناة مسبقاً!"})

                try:
                    chat_member = await bot.get_chat_member(chat_id=task_data["channel_id"], user_id=user_id)
                    if chat_member.status in ["left", "kicked"]:
                        return web.json_response({"ok": False, "msg": "❌ لم تنضم للقناة بعد! انضم أولاً ثم تحقق."})
                except Exception:
                    return web.json_response({"ok": False, "msg": "⚠️ تعذر التحقق، تأكد من إضافة البوت كمشرف في القناة."})

                tasks.append(task_id)
                reward = task_data["reward"]
                await db.execute("UPDATE users SET olk_balance = olk_balance + ?, tasks_completed = ? WHERE user_id = ?",
                                 (reward, json.dumps(tasks), user_id))
                await db.commit()

                return web.json_response({"ok": True, "reward": reward, "msg": f"✅ مبروك! تمت إضافة +{reward:.0f} OLK"})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})

def web_only_keyboard(user_id: int):
    app_url = f"{WEBAPP_URL}?user_id={user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ ابدأ التعدين الآن (Play Now) 🚀", web_app=WebAppInfo(url=app_url))
        ]
    ])

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT COUNT(*), SUM(olk_balance), SUM(ton_balance) FROM users WHERE is_banned = 0") as cur:
            users_count, total_olk, total_ton = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) FROM withdrawals WHERE status = 'PENDING'") as cur:
            pending_withdraws = (await cur.fetchone())[0]

    admin_msg = (
        "👑 **لوحة تحكم إدارة المشروع (VIP Admin):**\n"
        "──────────────────────\n"
        f"👥 إجمالي المستخدمين النشطين: `{users_count}`\n"
        f"🪙 إجمالي عملات OLK: `{(total_olk or 0):.2f}`\n"
        f"💎 إجمالي عملات TON: `{(total_ton or 0):.4f}`\n"
        f"⏳ طلبات السحب المعلقة: `{pending_withdraws}`\n"
        "──────────────────────\n"
        "📢 لإرسال إذاعة: `/broadcast`\n"
        "⛔ لحظر مستخدم: `/ban USER_ID السبب`\n"
        "✅ لفك حظر مستخدم وحمايته: `/unban USER_ID`"
    )
    await message.answer(admin_msg, parse_mode="Markdown")

@dp.message(Command("ban"))
async def ban_user_cmd(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    if not command.args:
        await message.answer("⚠️ الصيغة الصحيحة:\n`/ban USER_ID سبب الحظر`", parse_mode="Markdown")
        return

    parts = command.args.split(maxsplit=1)
    target_id_str = parts[0]
    reason = parts[1] if len(parts) > 1 else "مخالفة سياسات وقوانين التعدين"

    try:
        target_id = int(target_id_str)
    except ValueError:
        await message.answer("❌ المعرّف يجب أن يكون رقماً صحيحاً!")
        return

    async with aiosqlite.connect("olka_vip.db") as db:
        await db.execute("UPDATE users SET is_banned = 1, ban_reason = ?, is_whitelisted = 0 WHERE user_id = ?", (reason, target_id))
        await db.commit()

    await message.answer(f"✅ **تم حظر المستخدم بنجاح!**\n🆔 المعرف: `{target_id}`\n📝 السبب: `{reason}`", parse_mode="Markdown")

@dp.message(Command("unban"))
async def unban_user_cmd(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return
    if not command.args:
        await message.answer("⚠️ الصيغة الصحيحة:\n`/unban USER_ID`", parse_mode="Markdown")
        return

    try:
        target_id = int(command.args.strip())
    except ValueError:
        await message.answer("❌ المعرّف يجب أن يكون رقماً صحيحاً!")
        return

    async with aiosqlite.connect("olka_vip.db") as db:
        # فك الحظر وإضافة المستخدم إلى القائمة البيضاء الموثوقة لمنع حظره مجدداً
        await db.execute("UPDATE users SET is_banned = 0, ban_reason = NULL, is_whitelisted = 1 WHERE user_id = ?", (target_id,))
        await db.commit()

    await message.answer(f"✅ **تم فك الحظر عن المستخدم `{target_id}` بنجاح وإضافته للقائمة الموثوقة لمنع حظره مجدداً!**", parse_mode="Markdown")

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
        async with db.execute("SELECT user_id FROM users WHERE is_banned = 0") as cur:
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

@dp.callback_query(F.data.startswith("adm_app_"))
async def approve_withdraw(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    w_id = int(callback.data.split("_")[2])
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT user_id, amount_ton FROM withdrawals WHERE id = ?", (w_id,)) as cur:
            row = await cur.fetchone()
            if row:
                uid, amount = row
                await db.execute("UPDATE withdrawals SET status = 'APPROVED' WHERE id = ?", (w_id,))
                await db.commit()
                try:
                    await bot.send_message(chat_id=uid, text=f"🎉 **تمت معالجة وإرسال طلب سحب TON بنجاح!**\n💎 المبلغ: `{amount:.4f} TON`", parse_mode="Markdown")
                except Exception:
                    pass
    await callback.message.edit_text(callback.message.text + "\n\n✅ **تمت الموافقة والإرسال بنجاح.**")

@dp.callback_query(F.data.startswith("adm_rej_"))
async def reject_withdraw(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    w_id = int(callback.data.split("_")[2])
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT user_id, amount_ton FROM withdrawals WHERE id = ?", (w_id,)) as cur:
            row = await cur.fetchone()
            if row:
                uid, amount = row
                await db.execute("UPDATE users SET ton_balance = ton_balance + ? WHERE user_id = ?", (amount, uid))
                await db.execute("UPDATE withdrawals SET status = 'REJECTED' WHERE id = ?", (w_id,))
                await db.commit()
                try:
                    await bot.send_message(chat_id=uid, text=f"❌ **تم رفض طلب السحب وإعادة المبلغ لحسابك.**\n💎 المبلغ: `{amount:.4f} TON`", parse_mode="Markdown")
                except Exception:
                    pass
    await callback.message.edit_text(callback.message.text + "\n\n❌ **تم رفض الطلب وإعادة الرصيد للمستخدم.**")

@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    user_id = message.from_user.id
    ref_param = command.args
    now = int(time.time())

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT is_banned, ban_reason FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

        if user and user[0] == 1:
            reason = user[1] or "مخالفة قوانين التعدين"
            await message.answer(f"⛔ **عذراً، هذا الحساب محظور نهائياً.**\nسبب الحظر: `{reason}`", parse_mode="Markdown")
            return

        if not user and ref_param:
            try:
                clean_ref = ref_param.replace("ref_", "")
                referrer_id = int(clean_ref)
                if referrer_id != user_id:
                    await db.execute("""
                        INSERT INTO users (user_id, referred_by, last_mining_timestamp, mining_speed, olk_balance, activated_miner) VALUES (?, ?, ?, 0.25, 0, 0)
                        ON CONFLICT(user_id) DO UPDATE SET referred_by = excluded.referred_by
                    """, (user_id, referrer_id, now))
                    await db.commit()
            except ValueError:
                pass
        elif not user:
            await db.execute("INSERT OR IGNORE INTO users (user_id, last_mining_timestamp, mining_speed, olk_balance, activated_miner) VALUES (?, ?, 0.25, 0, 0)",
                             (user_id, now))
            await db.commit()

    welcome_text = (
        "⚡ **مرحباً بك في منصة OLKA VIP**\n"
        "──────────────────────\n"
        "🚀 **منظومة التعدين السحابي المباشر على شبكة TON**\n\n"
        "⛏️ **تعدين آلي 24/7:** يعمل جهازك السحابي دون انقطاع حتى عند إغلاق التطبيق.\n"
        "💎 **سحب مباشر:** تحويل فوري لأرباحك إلى عملة TON على محفظتك.\n"
        "🎁 **هدية البداية:** يتم إيداع **+50 OLK** فور تشغيل التعدين في الويب!\n"
        "──────────────────────\n"
        "اضغط على الزر أدناه لتشغيل جهاز التعدين والتحكم بمحفظتك:"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=web_only_keyboard(user_id))

async def web_handler(request):
    return web.Response(text=MINI_APP_HTML, content_type="text/html")

async def main():
    await init_db()
    print("OLK Engine with Safe Whitelist & Immune Unban System is running...")

    app = web.Application()
    app.router.add_get("/", web_handler)
    app.router.add_get("/tonconnect-manifest.json", api_manifest)
    app.router.add_get("/api/get_user", api_get_user)
    app.router.add_post("/api/save_wallet", api_save_wallet)
    app.router.add_post("/api/claim_passive", api_claim_passive)
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
