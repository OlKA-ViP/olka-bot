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
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "8707730826:AAExJ7ZSQe9YFy8Y0O2eG3uPCAwVa_vG6Qc"
ADMIN_ID = 1932161126
SPONSOR_CHANNEL = "@olka_ad"

PROJECT_TON_WALLET = "UQB3Xs8jkbebkVumWJlnEmDkjN4YXsZuHPrXSpZT1RtmZrCB"

CONVERSION_RATE = 10000
MIN_WITHDRAW_TON = 0.1
REFERRAL_REWARD = 5.0
SIGNUP_BONUS = 5.0

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

# دالة تحويل العنوان الخام (0:...) إلى صيغة المحفظة المقروءة (UQ...)
def raw_to_user_friendly(raw_addr: str) -> str:
    if not raw_addr or not raw_addr.startswith("0:"):
        return raw_addr
    try:
        wc_str, hex_str = raw_addr.split(":", 1)
        wc = int(wc_str)
        account_id = bytes.fromhex(hex_str)
        # 0x51 للعنوان غير القابل للارتداد UQ على الشبكة الرئيسية
        tag = 0x51
        data = bytes([tag, wc & 0xFF]) + account_id

        # حساب كود التحقق CRC16-CCITT/XMODEM
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

MINI_APP_HTML = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>تعدين OLK VIP</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <script src="https://unpkg.com/@tonconnect/ui@latest/dist/tonconnect-ui.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {{
      --bg-main: #060a12;
      --card-bg: rgba(15, 23, 42, 0.88);
      --card-border: rgba(45, 66, 107, 0.55);
      --gold-primary: #f59e0b;
      --gold-glow: rgba(245, 158, 11, 0.4);
      --accent-green: #22c55e;
      --accent-cyan: #06b6d4;
      --accent-blue: #2563eb;
      --text-muted: #94a3b8;
    }}
    * {{
      box-sizing: border-box;
      user-select: none;
      -webkit-user-select: none;
      touch-action: manipulation;
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    html, body {{
      background-color: var(--bg-main);
      background-image: 
        linear-gradient(rgba(30, 41, 67, 0.22) 1px, transparent 1px),
        linear-gradient(90deg, rgba(30, 41, 67, 0.22) 1px, transparent 1px);
      background-size: 24px 24px;
      color: #ffffff;
      min-height: 100vh;
      height: 100%;
      overflow: hidden;
    }}
    .main-scroll-view {{
      height: 100vh;
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
      padding: 12px 14px 140px 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
    }}
    .top-header {{
      width: 100%;
      text-align: center;
      font-size: 18px;
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 12px;
      display: flex;
      justify-content: center;
      align-items: center;
      position: relative;
    }}
    .header-signal {{
      position: absolute;
      right: 4px;
      font-size: 12px;
      color: var(--accent-green);
      font-weight: 600;
    }}
    .assets-container {{
      width: 100%;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(20px);
      border-radius: 20px;
      padding: 14px;
      margin-bottom: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }}
    .assets-title-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      margin-bottom: 10px;
    }}
    .assets-total {{ color: #cbd5e1; font-weight: 700; }}
    .assets-total span {{ color: var(--gold-primary); direction: ltr; display: inline-block; }}
    .assets-badge {{
      display: flex;
      align-items: center;
      gap: 6px;
      color: #93c5fd;
      font-size: 12px;
      font-weight: 700;
    }}

    .wallet-connection-banner {{
      width: 100%;
      background: linear-gradient(135deg, rgba(37, 99, 235, 0.2), rgba(6, 182, 212, 0.15));
      border: 1.5px solid rgba(56, 189, 248, 0.45);
      border-radius: 16px;
      padding: 12px 14px;
      margin-top: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(2, 132, 199, 0.25);
    }}
    .wallet-connection-banner:active {{ transform: scale(0.98); }}
    .wallet-banner-left {{ display: flex; align-items: center; gap: 10px; }}
    .wallet-icon-box {{
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
    }}
    .wallet-banner-info {{ display: flex; flex-direction: column; }}
    .wallet-banner-title {{ font-size: 13px; font-weight: 800; color: #ffffff; }}
    .wallet-banner-sub {{ font-size: 11px; color: #93c5fd; font-weight: 600; direction: ltr; text-align: right; }}
    .wallet-status-tag {{
      background: #0284c7;
      color: #ffffff;
      font-size: 11px;
      font-weight: 800;
      padding: 6px 12px;
      border-radius: 20px;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    .wallet-status-tag.connected {{
      background: rgba(34, 197, 94, 0.25);
      color: #4ade80;
      border-color: #22c55e;
    }}

    .page-tab {{
      display: none;
      width: 100%;
      flex-direction: column;
      align-items: center;
      animation: tabFadeIn 0.2s ease-out;
    }}
    .page-tab.active {{ display: flex; }}
    @keyframes tabFadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .balance-cards-grid {{
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 12px;
    }}
    .bal-card {{
      background: rgba(6, 11, 22, 0.9);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .bal-card-title {{
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 5px;
    }}
    .bal-card-value {{
      font-size: 18px;
      font-weight: 900;
      direction: ltr;
      text-align: left;
    }}

    .convert-box {{
      width: 100%;
      background: rgba(6, 11, 22, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 14px;
      margin-top: 8px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .input-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(0, 0, 0, 0.5);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 6px 10px;
    }}
    .convert-input {{
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-size: 16px;
      font-weight: 800;
      direction: ltr;
      text-align: left;
    }}
    .btn-max {{
      background: rgba(245, 158, 11, 0.2);
      border: 1px solid var(--gold-primary);
      color: var(--gold-primary);
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 800;
      cursor: pointer;
    }}
    .exchange-rate-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: var(--text-muted);
      padding: 0 4px;
    }}
    .exchange-rate-row span {{
      direction: ltr;
    }}

    .mining-hero-card {{
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
    }}
    .miner-status-badge {{
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.06);
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 800;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .status-online {{
      background: var(--accent-green);
      color: #052e16;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 800;
    }}
    .unclaimed-subtitle {{
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 10px;
      font-weight: 600;
    }}
    .unclaimed-counter {{
      font-size: 30px;
      font-weight: 900;
      color: #ffffff;
      margin-top: 2px;
      display: flex;
      align-items: center;
      gap: 6px;
      letter-spacing: 0.5px;
    }}
    .unclaimed-counter span {{
      color: var(--gold-primary);
      font-size: 18px;
    }}
    .hashrate-capsule {{
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
    }}
    .central-coin-stage {{
      margin: 16px 0 12px 0;
      position: relative;
      display: flex;
      justify-content: center;
      align-items: center;
    }}
    .coin-3d {{
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
    }}
    .coin-3d:active {{ transform: scale(0.95); }}
    .coin-inner-details {{
      width: 155px;
      height: 155px;
      border-radius: 50%;
      border: 2px dashed rgba(254, 240, 138, 0.6);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }}
    .coin-symbol {{
      font-size: 48px;
      color: #ffffff;
      text-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
    }}
    .coin-name {{
      font-size: 22px;
      font-weight: 900;
      color: #ffffff;
      letter-spacing: 2px;
      text-shadow: 0 3px 8px rgba(0, 0, 0, 0.8);
      margin-top: -2px;
    }}
    .btn-claim-rewards {{
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
    }}
    .btn-claim-rewards:active {{ transform: scale(0.97); }}
    .hero-actions-grid {{
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 12px;
    }}
    .btn-upgrade-rig {{
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
    }}
    .btn-wallet-link {{
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
    }}
    .btn-wallet-link.connected {{
      background: rgba(34, 197, 94, 0.2);
      border: 1px solid var(--accent-green);
      color: #4ade80;
    }}
    .card-panel {{
      width: 100%;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 16px;
      margin-bottom: 12px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .rig-item {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(6, 11, 22, 0.7);
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }}
    .bottom-bar {{
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
    }}
    .nav-link {{
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
    }}
    .nav-link i {{ font-size: 18px; }}
    .nav-link.active {{ color: #bef264; }}
    .nav-link.active i {{ color: #bef264; }}
    .notify-dot {{
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
    }}
  </style>
</head>
<body>

  <div class="main-scroll-view">
    <div class="top-header">
      <div class="header-signal"><i class="fa-solid fa-signal"></i> مباشر</div>
      <div>تعدين OLK VIP</div>
    </div>

    <!-- كرت الأصول المحفوظة -->
    <div class="assets-container">
      <div class="assets-title-row">
        <div class="assets-total">الإجمالي: <span id="total-assets">0.0000 OLK</span></div>
        <div class="assets-badge"><i class="fa-solid fa-shield-halved"></i> أصولي المحفوظة</div>
      </div>
      
      <div class="balance-cards-grid">
        <div class="bal-card">
          <div class="bal-card-title"><i class="fa-solid fa-coins" style="color:var(--gold-primary);"></i> رصيد OLK:</div>
          <div class="bal-card-value" style="color:var(--gold-primary);" id="app-balance-val">0.00 OLK</div>
        </div>
        <div class="bal-card">
          <div class="bal-card-title"><i class="fa-solid fa-gem" style="color:#60a5fa;"></i> رصيد TON:</div>
          <div class="bal-card-value" style="color:#60a5fa;" id="app-ton-val">0.0000 TON</div>
        </div>
      </div>

      <div class="wallet-connection-banner" onclick="handleConnectWalletClick()">
        <div class="wallet-banner-left">
          <div class="wallet-icon-box">
            <i class="fa-solid fa-wallet"></i>
          </div>
          <div class="wallet-banner-info">
            <span class="wallet-banner-title">محفظة TON (Telegram / Tonkeeper)</span>
            <span class="wallet-banner-sub" id="wallet-status-sub">اضغط لربط المحفظة مباشرة</span>
          </div>
        </div>
        <div class="wallet-status-tag" id="wallet-status-label">اتصال</div>
      </div>
    </div>

    <!-- صفحة 1: شاشة التعدين -->
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
          <span>السرعة: <strong id="speed-val">0.25</strong> TH/s</span>
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
        <button class="btn-wallet-link" id="btn-connect-wallet" onclick="handleConnectWalletClick()">
          <i class="fa-solid fa-wallet"></i> <span id="wallet-btn-text">CONNECT WALLET</span>
        </button>
      </div>
    </div>

    <!-- صفحة 2: المحفظة والتحويل اليدوي -->
    <div class="page-tab" id="tab-wallet">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--gold-primary); font-size:15px; display:flex; justify-content:space-between; align-items:center;">
          <span>💳 صرافة وتحويل العملات</span>
          <span style="font-size:11px; color:#38bdf8; direction:ltr;">1 TON = 10,000 OLK</span>
        </div>

        <div class="convert-box">
          <div style="display:flex; justify-content:space-between; font-size:12px;">
            <span style="color:var(--text-muted);">أدخل كمية OLK المراد تحويلها:</span>
            <span style="color:#f59e0b; direction:ltr;" id="available-olk-convert">المتاح: 0.00</span>
          </div>

          <div class="input-row">
            <input type="number" id="convert-input-amount" class="convert-input" placeholder="مثال: 100 أو 1000" oninput="calculateConvertPreview()">
            <button class="btn-max" onclick="setMaxConvert()">MAX</button>
          </div>

          <div class="exchange-rate-row">
            <span>ستحصل على تقريباً:</span>
            <strong style="color:#4ade80; font-size:14px;" id="convert-preview-val">0.0000 TON</strong>
          </div>

          <button class="btn-claim-rewards" style="margin-top:2px;" onclick="convertOlkDirect()">
            <i class="fa-solid fa-repeat"></i> تأكيد تحويل الكمية المحددة
          </button>
        </div>

        <hr style="border:0; border-top:1px solid var(--card-border); margin:6px 0;">

        <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px;">
          <span style="color:var(--text-muted);">الحد الأدنى المطلوب للسحب:</span>
          <strong style="color:#f87171; direction:ltr;">0.1 TON (1,000 OLK)</strong>
        </div>

        <div style="font-size:12px; color:#cbd5e1; margin-top:2px;">المحفظة المرتبطة بالسحب:</div>
        <div id="connected-wallet-display" style="font-size:11px; color:#93c5fd; background:rgba(0,0,0,0.5); padding:10px; border-radius:12px; word-break:break-all; direction:ltr; text-align:left;">
          ⚠️ لم يتم ربط محفظة TON بعد
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:6px;">
          <button class="btn-upgrade-rig" style="background:#059669;" onclick="depositTonDirect()">
            <i class="fa-solid fa-arrow-down"></i> إيداع 0.1 TON
          </button>
          <button class="btn-upgrade-rig" onclick="requestWithdrawalToConnectedWallet()">
            <i class="fa-solid fa-arrow-up"></i> سحب رصيد TON
          </button>
        </div>
      </div>
    </div>

    <!-- صفحة 3: الأصدقاء -->
    <div class="page-tab" id="tab-frens">
      <div class="card-panel">
        <div style="font-weight:bold; color:#bef264; font-size:15px;"><i class="fa-solid fa-users"></i> شبكة التعدين التشاركية (الإحالات)</div>
        <div style="font-size:13px; color:#cbd5e1;">شارك رابط جهازك واحصل على <strong>5 OLK</strong> فور توثيق صديقك لحسابه!</div>
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
            <div style="font-size:11px; color:var(--text-muted); direction:ltr; text-align:right;">+0.15 TH/s زيادة سرعة</div>
          </div>
          <button class="btn-upgrade-rig" style="padding:8px 12px; font-size:12px;" onclick="buyRig(1, 150, 0.15)">شراء (150 OLK)</button>
        </div>

        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">GPU Quantum Rig</div>
            <div style="font-size:11px; color:var(--text-muted); direction:ltr; text-align:right;">+0.50 TH/s زيادة سرعة</div>
          </div>
          <button class="btn-upgrade-rig" style="padding:8px 12px; font-size:12px;" onclick="buyRig(2, 450, 0.50)">شراء (450 OLK)</button>
        </div>

        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">ASIC VIP Titan</div>
            <div style="font-size:11px; color:var(--text-muted); direction:ltr; text-align:right;">+1.50 TH/s زيادة سرعة</div>
          </div>
          <button class="btn-upgrade-rig" style="padding:8px 12px; font-size:12px;" onclick="buyRig(3, 1200, 1.50)">شراء (1200 OLK)</button>
        </div>
      </div>
    </div>

    <!-- صفحة 5: المهام -->
    <div class="page-tab" id="tab-tasks">
      <div class="card-panel">
        <div style="font-weight:bold; color:var(--gold-primary); font-size:15px;"><i class="fa-solid fa-list-check"></i> مهام التحقق من القنوات</div>
        
        <div class="rig-item">
          <div>
            <div style="font-weight:bold; font-size:13px;">قناة OLKA AD الرسمية</div>
            <div style="font-size:11px; color:var(--text-muted);">+10 OLK مكافأة انضمام</div>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="btn-upgrade-rig" style="padding:6px 10px; font-size:11px;" onclick="window.open('https://t.me/olka_ad', '_blank')">انضمام</button>
            <button class="btn-upgrade-rig" style="padding:6px 10px; font-size:11px; background:#10b981;" onclick="checkChannelTask('task_chan_main')">تحقق</button>
          </div>
        </div>
      </div>
    </div>
  </div>

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
    if (tg) {{ 
      tg.ready(); 
      tg.expand(); 
    }}

    const urlParams = new URLSearchParams(window.location.search);
    const userId = tg?.initDataUnsafe?.user?.id || urlParams.get('user_id') || 1932161126;

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

    const tonConnectUI = new TON_CONNECT_UI.TonConnectUI({{
      manifestUrl: window.location.origin + '/tonconnect-manifest.json'
    }});

    // تحويل العنوان مباشرة إلى صيغة UQ المألوفة
    tonConnectUI.onStatusChange(async (wallet) => {{
      if (wallet) {{
        try {{
          connectedWalletAddress = TON_CONNECT_UI.toUserFriendlyAddress(wallet.account.address);
        }} catch(e) {{
          connectedWalletAddress = wallet.account.address;
        }}
        
        const shortAddr = connectedWalletAddress.slice(0, 4) + '...' + connectedWalletAddress.slice(-4);
        walletBtnText.innerText = shortAddr;
        walletStatusLabel.innerText = "متصل ✅";
        walletStatusLabel.classList.add("connected");
        walletStatusSub.innerText = shortAddr;
        walletBtn.classList.add("connected");
        walletDisplay.innerText = connectedWalletAddress;

        await fetch("/api/save_wallet", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ user_id: userId, address: connectedWalletAddress }})
        }});
      }} else {{
        connectedWalletAddress = null;
        walletBtnText.innerText = "CONNECT WALLET";
        walletStatusLabel.innerText = "اتصال";
        walletStatusLabel.classList.remove("connected");
        walletStatusSub.innerText = "اضغط لربط المحفظة مباشرة";
        walletBtn.classList.remove("connected");
        walletDisplay.innerText = "⚠️ لم يتم ربط محفظة TON بعد";
      }}
    }});

    function handleConnectWalletClick() {{
      if (tonConnectUI.connected) {{
        tonConnectUI.disconnect();
      }} else {{
        tonConnectUI.openModal();
      }}
    }}

    async function loadData() {{
      try {{
        const res = await fetch(`/api/get_user?user_id=${{userId}}`);
        const data = await res.json();
        if (data.ok) {{
          appOlk = data.olk_balance;
          appTon = data.ton_balance;
          speed = data.mining_speed || 0.25;
          minerLevel = data.miner_level || 1;
          if (data.saved_wallet) {{
            connectedWalletAddress = data.saved_wallet;
            const shortAddr = connectedWalletAddress.slice(0, 4) + '...' + connectedWalletAddress.slice(-4);
            walletBtnText.innerText = shortAddr;
            walletStatusLabel.innerText = "مسجلة ✅";
            walletStatusLabel.classList.add("connected");
            walletStatusSub.innerText = shortAddr;
            walletBtn.classList.add("connected");
            walletDisplay.innerText = connectedWalletAddress;
          }}
          if (data.offline_mined) {{
            unclaimed += data.offline_mined;
          }}
          refreshScreen();
        }}
      }} catch (err) {{
        console.error("Data load failed", err);
      }}
    }}

    function refreshScreen() {{
      totalAssetsEl.innerText = (appOlk + unclaimed).toFixed(4) + " OLK";
      appBalEl.innerText = appOlk.toFixed(2) + " OLK";
      appTonEl.innerText = appTon.toFixed(4) + " TON";
      unclaimedValEl.innerText = unclaimed.toFixed(6);
      speedValEl.innerText = speed.toFixed(2);
      levelDisplayEl.innerText = minerLevel;
      availableOlkConvert.innerText = "المتاح: " + appOlk.toFixed(2);
    }}

    function calculateConvertPreview() {{
      const amt = parseFloat(convertInput.value) || 0;
      const tonVal = amt / 10000;
      convertPreview.innerText = tonVal.toFixed(4) + " TON";
    }}

    function setMaxConvert() {{
      convertInput.value = Math.floor(appOlk);
      calculateConvertPreview();
    }}

    setInterval(() => {{
      unclaimed += (speed * 0.000015);
      unclaimedValEl.innerText = unclaimed.toFixed(6);
      totalAssetsEl.innerText = (appOlk + unclaimed).toFixed(4) + " OLK";
    }}, 100);

    async function claimRewardsToDb() {{
      if (unclaimed < 0.001) {{
        alert("⚠️ أرباح التعدين قليلة جداً حالياً، واصل التعدين!");
        return;
      }}
      const reward = unclaimed;
      unclaimed = 0;
      appOlk += reward;
      refreshScreen();

      if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("success");

      try {{
        await fetch("/api/claim_passive", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ user_id: userId, amount: reward }})
        }});
      }} catch (e) {{
        console.error("Claim request failed", e);
      }}
    }}

    function manualBoostClick() {{
      unclaimed += (speed * 0.0005);
      unclaimedValEl.innerText = unclaimed.toFixed(6);
      if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred("light");
    }}

    async function buyRig(rigId, cost, speedGain) {{
      if (appOlk < cost) {{
        alert(`⚠️ رصيدك في التطبيق غير كافٍ! يلزمك ${{cost}} OLK.`);
        return;
      }}
      appOlk -= cost;
      speed += speedGain;
      minerLevel += 1;
      refreshScreen();

      await fetch("/api/upgrade_rig", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ user_id: userId, cost: cost, new_speed: speed, new_level: minerLevel }})
      }});
      alert(`🎉 تم شراء جهاز التعدين بنجاح! السرعة الآن: ${{speed.toFixed(2)}} TH/s`);
    }}

    async function convertOlkDirect() {{
      const amountToConvert = parseFloat(convertInput.value);
      if (!amountToConvert || amountToConvert <= 0) {{
        alert("⚠️ يرجى كتابة كمية OLK التي ترغب في تحويلها أولاً!");
        return;
      }}
      if (amountToConvert > appOlk) {{
        alert("⚠️ الكمية المدخلة أكبر من رصيدك المتاح في التطبيق!");
        return;
      }}
      const res = await fetch("/api/convert", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ user_id: userId, amount: amountToConvert }})
      }});
      const data = await res.json();
      if (data.ok) {{
        appOlk = data.olk_balance;
        appTon = data.ton_balance;
        convertInput.value = "";
        calculateConvertPreview();
        refreshScreen();
        alert(`✅ تم تحويل ${{amountToConvert}} OLK إلى ${{(amountToConvert / 10000).toFixed(4)}} TON بنجاح!`);
      }} else {{
        alert(data.msg);
      }}
    }}

    async function depositTonDirect() {{
      if (!tonConnectUI.connected) {{
        alert("❌ يرجى ربط محفظة TON أولاً!");
        handleConnectWalletClick();
        return;
      }}
      const transaction = {{
        validUntil: Math.floor(Date.now() / 1000) + 360,
        messages: [
          {{
            address: "{PROJECT_TON_WALLET}",
            amount: "100000000"
          }}
        ]
      }};
      try {{
        const result = await tonConnectUI.sendTransaction(transaction);
        if (result) {{
          appOlk += 1000;
          refreshScreen();
          await fetch("/api/claim_passive", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ user_id: userId, amount: 1000 }})
          }});
          alert("🎉 تم تأكيد إيداع 0.1 TON وحصلت على +1,000 OLK فوراً!");
        }}
      }} catch (e) {{
        alert("❌ تم إلغاء المعاملة أو فشل الإيداع.");
      }}
    }}

    async function requestWithdrawalToConnectedWallet() {{
      if (!connectedWalletAddress) {{
        alert("❌ يرجى ربط محفظة TON أولاً عبر زر CONNECT WALLET!");
        handleConnectWalletClick();
        return;
      }}
      if (appTon < 0.1) {{
        alert("⚠️ رصيدك أقل من الحد الأدنى للسحب وهو 0.1 TON!");
        return;
      }}
      const res = await fetch("/api/withdraw", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ user_id: userId, address: connectedWalletAddress }})
      }});
      const data = await res.json();
      if (data.ok) {{
        appTon = 0;
        refreshScreen();
        alert("✅ تم تسجيل طلب سحب TON بنجاح وسيتم التحويل لمحفظتك قريباً!");
      }} else {{
        alert(data.msg);
      }}
    }}

    function switchNav(tabName, el) {{
      document.querySelectorAll(".page-tab").forEach(tab => tab.classList.remove("active"));
      document.querySelectorAll(".nav-link").forEach(link => link.classList.remove("active"));
      document.getElementById("tab-" + tabName).classList.add("active");
      if (el) el.classList.add("active");
      if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred("light");
    }}

    function copyReferralLink() {{
      const invite = `https://t.me/OlkaVip_bot?start=${{userId}}`;
      navigator.clipboard.writeText(invite);
      alert("✅ تم نسخ رابط الإحالة الخاص بك!");
    }}

    async function checkChannelTask(taskId) {{
      try {{
        const res = await fetch("/api/verify_channel_task", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ user_id: userId, task_id: taskId }})
        }});
        const data = await res.json();
        alert(data.msg);
        if (data.ok) {{
          appOlk += data.reward;
          refreshScreen();
        }}
      }} catch (err) {{
        alert("حدث خطأ أثناء التحقق!");
      }}
    }}

    loadData();
  </script>
</body>
</html>
"""

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
            saved_wallet TEXT DEFAULT NULL
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
            "saved_wallet TEXT DEFAULT NULL"
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
        now = int(time.time())
        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT olk_balance, ton_balance, mining_speed, miner_level, last_mining_timestamp, saved_wallet FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if row:
                    olk, ton, speed, lvl, last_ts, saved_wallet = row
                    offline_mined = 0.0
                    if last_ts > 0:
                        diff = min(now - last_ts, 86400)
                        offline_mined = diff * (speed * 0.000015 * 10)
                    
                    await db.execute("UPDATE users SET last_mining_timestamp = ? WHERE user_id = ?", (now, user_id))
                    await db.commit()
                    return web.json_response({
                        "ok": True,
                        "olk_balance": olk,
                        "ton_balance": ton,
                        "mining_speed": speed,
                        "miner_level": lvl,
                        "saved_wallet": raw_to_user_friendly(saved_wallet),
                        "offline_mined": offline_mined
                    })
                else:
                    await db.execute("INSERT OR IGNORE INTO users (user_id, last_mining_timestamp, mining_speed) VALUES (?, ?, 0.25)", (user_id, now))
                    await db.commit()
                    return web.json_response({"ok": True, "olk_balance": 0.0, "ton_balance": 0.0, "mining_speed": 0.25, "miner_level": 1, "saved_wallet": None, "offline_mined": 0.0})
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
        friendly_address = raw_to_user_friendly(address)
        now = int(time.time())

        async with aiosqlite.connect("olka_vip.db") as db:
            async with db.execute("SELECT ton_balance, phone_number FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if not row or row[0] < MIN_WITHDRAW_TON:
                    return web.json_response({"ok": False, "msg": f"الحد الأدنى للسحب هو {MIN_WITHDRAW_TON} TON"})

                ton_bal, phone = row[0], row[1] or "غير موثق"
                cur_ins = await db.execute("INSERT INTO withdrawals (user_id, amount_ton, wallet_address, created_at) VALUES (?, ?, ?, ?)",
                                 (user_id, ton_bal, friendly_address, now))
                withdrawal_id = cur_ins.lastrowid
                await db.execute("UPDATE users SET ton_balance = 0.0 WHERE user_id = ?", (user_id,))
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
            f"💎 المبلغ: `{ton_bal:.4f} TON`\n"
            f"📫 المحفظة المستلمة:\n`{friendly_address}`"
        )
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=admin_notification, reply_markup=admin_kb, parse_mode="Markdown")
        except Exception:
            pass

        return web.json_response({"ok": True})
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

def get_contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⚡ توثيق الحساب واستلام هدية +5 OLK 🚀", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main_dashboard_keyboard(user_id: int):
    app_url = f"{WEBAPP_URL}?user_id={user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⛏️ فتح جهاز التعدين والمحفظة (OLK App) 🚀", web_app=WebAppInfo(url=app_url))
        ],
        [
            InlineKeyboardButton(text="⚡ مكافأة يومية (+2 OLK)", callback_data="claim"),
            InlineKeyboardButton(text="🔄 صرافة TON", callback_data="convert")
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

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT COUNT(*), SUM(olk_balance), SUM(ton_balance) FROM users") as cur:
            users_count, total_olk, total_ton = await cur.fetchone()
        async with db.execute("SELECT COUNT(*) FROM withdrawals WHERE status = 'PENDING'") as cur:
            pending_withdraws = (await cur.fetchone())[0]

    admin_msg = (
        "👑 **لوحة تحكم إدارة المشروع (VIP Admin):**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 إجمالي المستخدمين: `{users_count}`\n"
        f"🪙 إجمالي عملات OLK: `{(total_olk or 0):.2f}`\n"
        f"💎 إجمالي عملات TON: `{(total_ton or 0):.4f}`\n"
        f"⏳ طلبات السحب المعلقة: `{pending_withdraws}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "لإرسال إذاعة جماعية أرسل: `/broadcast`"
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
        async with db.execute("SELECT phone_number, olk_balance, ton_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

        if not user and ref_param:
            try:
                clean_ref = ref_param.replace("ref_", "")
                referrer_id = int(clean_ref)
                if referrer_id != user_id:
                    await db.execute("""
                        INSERT INTO users (user_id, referred_by, last_mining_timestamp, mining_speed) VALUES (?, ?, ?, 0.25)
                        ON CONFLICT(user_id) DO UPDATE SET referred_by = excluded.referred_by
                    """, (user_id, referrer_id, now))
                    await db.commit()
            except ValueError:
                pass
        elif not user:
            await db.execute("INSERT OR IGNORE INTO users (user_id, last_mining_timestamp, mining_speed) VALUES (?, ?, 0.25)", (user_id, now))
            await db.commit()

    if not user or not user[0]:
        welcome_banner = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌟 **مرحباً بك في إمبراطورية OLKA VIP** 🌟\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⛏️ أقوى نظام تعدين سحابي أوتوماتيكي مع ربط محفظة TON.\n"
            f"🎁 **هدية التوثيق:** `+{SIGNUP_BONUS:.0f} OLK`\n\n"
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
        f"🪙 رصيد OLK: `{user[1]:.2f} OLK`\n"
        f"💎 رصيد TON: `{user[2]:.4f} TON`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 اضغط على زر جهاز التعدين بالأسفل لفتح اللعبة والمحفظة!"
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
            INSERT INTO users (user_id, phone_number, olk_balance, mining_speed) VALUES (?, ?, ?, 0.25)
            ON CONFLICT(user_id) DO UPDATE SET phone_number = excluded.phone_number, olk_balance = olk_balance + ?
        """, (user_id, contact.phone_number, SIGNUP_BONUS, SIGNUP_BONUS))
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

    await message.answer(f"✅ **تم توثيق الحساب بنجاح وإضافة مكافأة +{SIGNUP_BONUS:.0f} OLK!**", parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

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

        await db.execute("UPDATE users SET olk_balance = olk_balance + 2.0, last_claim = ? WHERE user_id = ?", (current_time, user_id))
        await db.commit()

    await callback.answer("✅ استلمت +2 OLK بنجاح!", show_alert=True)
    await callback.message.edit_text("🎉 **تم استلام المكافأة اليومية بنجاح (+2 OLK)!**", parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

@dp.callback_query(F.data == "balance")
async def balance_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT olk_balance, ton_balance, saved_wallet FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            olk, ton, saved_w = row if row else (0.0, 0.0, None)

    friendly_saved = raw_to_user_friendly(saved_w)
    wallet_info = f"`{friendly_saved}`" if friendly_saved else "⚠️ لم يتم ربط محفظة بعد"
    text = (
        "💼 **محفظة التعدين السحابي (OLKA VIP):**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🪙 **رصيد OLK:** `{olk:.2f} OLK`\n"
        f"💎 **رصيد TON:** `{ton:.4f} TON`\n"
        f"📫 **المحفظة المتصلة:** {wallet_info}\n\n"
        f"💡 سعر الصرف: `1 TON = {CONVERSION_RATE} OLK`\n"
        f"💳 الحد الأدنى للسحب: `{MIN_WITHDRAW_TON} TON`\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 صرافة TON", callback_data="convert"),
            InlineKeyboardButton(text="💳 سحب TON", callback_data="withdraw")
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
        async with db.execute("SELECT olk_balance, ton_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            olk = row[0] if row else 0.0

    await callback.message.answer(
        f"🪙 **صرافة OLK إلى TON:**\n\nرصيدك الحالي: `{olk:.2f} OLK`\n\n💡 للتحويل بالكمية التي تريدها بالضبط، افتح تبويب **المحفظة** من داخل الـ Mini App واكتب المبلغ المطلوب في حاسبة التحويل!",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "withdraw")
async def withdraw_start(callback: CallbackQuery):
    user_id = callback.from_user.id
    now = int(time.time())
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT ton_balance, saved_wallet, phone_number FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            ton, saved_w, phone = row if row else (0.0, None, "غير موثق")

    if ton < MIN_WITHDRAW_TON:
        await callback.answer(f"⚠️ رصيدك أقل من الحد الأدنى للسحب ({MIN_WITHDRAW_TON} TON).", show_alert=True)
        return

    if not saved_w:
        await callback.answer("❌ يرجى ربط محفظة TON أولاً من داخل التطبيق!", show_alert=True)
        return

    friendly_saved = raw_to_user_friendly(saved_w)

    async with aiosqlite.connect("olka_vip.db") as db:
        cur_ins = await db.execute("INSERT INTO withdrawals (user_id, amount_ton, wallet_address, created_at) VALUES (?, ?, ?, ?)",
                         (user_id, ton, friendly_saved, now))
        withdrawal_id = cur_ins.lastrowid
        await db.execute("UPDATE users SET ton_balance = 0.0 WHERE user_id = ?", (user_id,))
        await db.commit()

    await callback.message.answer(f"✅ تم تسجيل طلب السحب بنجاح بمبلغ `{ton:.4f} TON` إلى محفظتك:\n`{friendly_saved}`", parse_mode="Markdown")

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ موافقة وتأكيد", callback_data=f"adm_app_{withdrawal_id}"),
            InlineKeyboardButton(text="❌ رفض", callback_data=f"adm_rej_{withdrawal_id}")
        ]
    ])
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 **طلب سحب TON #{withdrawal_id}**\n👤 المعرف: `{user_id}`\n📱 الهاتف: `{phone}`\n💎 المبلغ: `{ton:.4f} TON`\n📫 المحفظة المستلمة:\n`{friendly_saved}`",
            reply_markup=admin_kb,
            parse_mode="Markdown"
        )
    except Exception:
        pass

@dp.callback_query(F.data == "back_home")
async def back_home_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT phone_number, olk_balance, ton_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

    dash_text = (
        f"👑 **لوحة تحكم معدن OLKA VIP:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 المعرّف: `{user_id}`\n"
        f"🪙 رصيد OLK: `{user[1]:.2f} OLK`\n"
        f"💎 رصيد TON: `{user[2]:.4f} TON`\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(dash_text, parse_mode="Markdown", reply_markup=main_dashboard_keyboard(user_id))

async def web_handler(request):
    return web.Response(text=MINI_APP_HTML, content_type="text/html")

async def main():
    await init_db()
    print("OLK Ultra Engine with Pure UQ User-Friendly Addresses is live...")

    app = web.Application()
    app.router.add_get("/", web_handler)
    app.router.add_get("/tonconnect-manifest.json", api_manifest)
    app.router.add_get("/api/get_user", api_get_user)
    app.router.add_post("/api/save_wallet", api_save_wallet)
    app.router.add_post("/api/claim_passive", api_claim_passive)
    app.router.add_post("/api/upgrade_rig", api_upgrade_rig)
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
