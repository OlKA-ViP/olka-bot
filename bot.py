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

# الإعدادات والمعلومات الأساسية
BOT_TOKEN = "8707730826:AAExJ7ZSQe9YFy8Y0O2eG3uPCAwVa_vG6Qc"
ADMIN_ID = 1932161126
SPONSOR_CHANNEL = "@olka_ad"
CONVERSION_RATE = 100
MIN_WITHDRAW_GRAM = 5

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

withdraw_state = {}

# واجهة الويب المتطورة للميني آب (Mini App UI)
MINI_APP_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>OLKA VIP MINER</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {
      --bg-gradient: radial-gradient(circle at 50% 10%, #1e1b4b 0%, #090d16 100%);
      --gold-primary: #f59e0b;
      --gold-light: #fef08a;
      --gold-glow: rgba(245, 158, 11, 0.45);
      --card-bg: rgba(255, 255, 255, 0.04);
      --card-border: rgba(255, 255, 255, 0.08);
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
    body {
      background: var(--bg-gradient);
      color: #ffffff;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      overflow: hidden;
    }
    .top-bar {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(12px);
      padding: 10px 16px;
      border-radius: 20px;
    }
    .user-profile {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .avatar-icon {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: linear-gradient(135deg, #6366f1, #a855f7);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 14px;
      box-shadow: 0 0 10px rgba(99, 102, 241, 0.4);
    }
    .user-text {
      display: flex;
      flex-direction: column;
    }
    .username {
      font-size: 14px;
      font-weight: 700;
    }
    .user-league {
      font-size: 11px;
      color: var(--gold-light);
      font-weight: 600;
    }
    .live-badge {
      font-size: 11px;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      padding: 4px 10px;
      border-radius: 12px;
      border: 1px solid rgba(52, 211, 153, 0.3);
      font-weight: 600;
    }
    .score-container {
      text-align: center;
      margin: 10px 0;
    }
    .score-title {
      font-size: 12px;
      color: #94a3b8;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      font-weight: 600;
    }
    .score-value {
      font-size: 46px;
      font-weight: 900;
      color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 2px;
      text-shadow: 0 0 25px var(--gold-glow);
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
    .tap-container {
      position: relative;
      display: flex;
      justify-content: center;
      align-items: center;
      margin: 15px 0;
    }
    .tap-coin {
      width: 230px;
      height: 230px;
      border-radius: 50%;
      background: radial-gradient(circle at 35% 30%, #fde047 0%, #d97706 60%, #78350f 100%);
      border: 7px solid #fef08a;
      box-shadow: 0 10px 30px rgba(0,0,0,0.6), 0 0 50px var(--gold-glow), inset 0 0 20px rgba(0,0,0,0.4);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      transition: transform 0.07s ease-out;
      position: relative;
    }
    .tap-coin:active {
      transform: scale(0.93) translateY(4px);
    }
    .coin-logo {
      font-size: 44px;
      font-weight: 900;
      letter-spacing: 3px;
      color: #ffffff;
      text-shadow: 0 4px 10px rgba(0,0,0,0.6);
    }
    .coin-sub {
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 4px;
      color: rgba(255,255,255,0.85);
      margin-top: -2px;
    }
    .float-num {
      position: absolute;
      color: #fffbeb;
      font-size: 30px;
      font-weight: 900;
      pointer-events: none;
      animation: floatUp 0.75s ease-out forwards;
      text-shadow: 0 0 12px var(--gold-primary);
      z-index: 100;
    }
    @keyframes floatUp {
      0% { opacity: 1; transform: translateY(0) scale(1); }
      100% { opacity: 0; transform: translateY(-90px) scale(1.3); }
    }
    .bottom-section {
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .energy-wrapper {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 10px 14px;
      backdrop-filter: blur(10px);
    }
    .energy-meta {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 6px;
    }
    .energy-label {
      color: #94a3b8;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .energy-num {
      color: #38bdf8;
    }
    .bar-outer {
      width: 100%;
      height: 10px;
      background: rgba(255, 255, 255, 0.08);
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
  </style>
</head>
<body>

  <div class="top-bar">
    <div class="user-profile">
      <div class="avatar-icon" id="user-avatar">O</div>
      <div class="user-text">
        <span class="username" id="user-name">عضو VIP</span>
        <span class="user-league" id="user-league">🏆 رتبة: برونزي</span>
      </div>
    </div>
    <div class="live-badge">🟢 متصل بالسيرفر</div>
  </div>

  <div class="score-container">
    <div class="score-title">إجمالي رصيد التعدين (OLK)</div>
    <div class="score-value">
      <span class="score-coin-icon">🪙</span>
      <span id="score-display">0</span>
    </div>
  </div>

  <div class="tap-container">
    <div class="tap-coin" id="coin-btn">
      <div class="coin-logo">OLK</div>
      <div class="coin-sub">VIP MINER</div>
    </div>
  </div>

  <div class="bottom-section">
    <div class="energy-wrapper">
      <div class="energy-meta">
        <span class="energy-label">⚡ الطاقة المتبقية</span>
        <span class="energy-num" id="energy-counter">1000 / 1000</span>
      </div>
      <div class="bar-outer">
        <div class="bar-fill" id="energy-progress"></div>
      </div>
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
    const userLeagueEl = document.getElementById("user-league");
    const scoreEl = document.getElementById("score-display");
    const energyCounterEl = document.getElementById("energy-counter");
    const energyProgressEl = document.getElementById("energy-progress");
    const coinBtn = document.getElementById("coin-btn");

    const tgUser = tg?.initDataUnsafe?.user;
    if (tgUser && tgUser.first_name) {
      userNameEl.innerText = tgUser.first_name;
      userAvatarEl.innerText = tgUser.first_name.charAt(0).toUpperCase();
    }

    const MAX_ENERGY = 1000;
    let balance = parseFloat(localStorage.getItem("olk_game_balance") || "0");
    let energy = parseInt(localStorage.getItem("olk_game_energy") || MAX_ENERGY.toString());

    function updateLeague() {
      if (balance >= 10000) userLeagueEl.innerText = "💎 رتبة: ماسي";
      else if (balance >= 5000) userLeagueEl.innerText = "🥇 رتبة: ذهبي";
      else if (balance >= 1000) userLeagueEl.innerText = "🥈 رتبة: فضي";
      else userLeagueEl.innerText = "🥉 رتبة: برونزي";
    }

    function renderUI() {
      scoreEl.innerText = balance.toLocaleString();
      energyCounterEl.innerText = `${energy} / ${MAX_ENERGY}`;
      const pct = (energy / MAX_ENERGY) * 100;
      energyProgressEl.style.width = pct + "%";
      updateLeague();
    }

    renderUI();

    // تجديد الطاقة تلقائياً كل ثانية
    setInterval(() => {
      if (energy < MAX_ENERGY) {
        energy = Math.min(MAX_ENERGY, energy + 3);
        renderUI();
        localStorage.setItem("olk_game_energy", energy);
      }
    }, 1000);

    // حدث النقر
    coinBtn.addEventListener("pointerdown", (event) => {
      if (energy <= 0) {
        if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred("error");
        return;
      }

      energy -= 1;
      balance += 1;
      renderUI();

      localStorage.setItem("olk_game_balance", balance);
      localStorage.setItem("olk_game_energy", energy);

      if (tg?.HapticFeedback) {
        tg.HapticFeedback.impactOccurred("medium");
      }

      // تأثير الرقم العائم (+1)
      const rect = coinBtn.getBoundingClientRect();
      const floatEl = document.createElement("div");
      floatEl.className = "float-num";
      floatEl.innerText = "+1";
      floatEl.style.left = (event.clientX - rect.left - 12) + "px";
      floatEl.style.top = (event.clientY - rect.top - 24) + "px";
      coinBtn.parentElement.appendChild(floatEl);

      setTimeout(() => floatEl.remove(), 750);
    });
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

# لوحات المفاتيح (Keyboards)
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

# التحقق من الاشتراك في القناة
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except Exception:
        return True

# معالجة أمر /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id

    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT phone_number FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()

    if not user or not user[0]:
        await message.answer(
            "👋 مرحباً بك في مشروع OLKA VIP GAME!\n\n🔒 لحماية البوت من الحسابات الوهمية والتكرار، يرجى توثيق حسابك بمشاركة رقم هاتفك لمرة واحدة فقط:",
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

    await message.answer("🪙 مرحباً بك في لوحة تحكم OLKA VIP:\nيمكنك استخدام القائمة أدناه أو الضغط على زر اللعبة بالأسفل لفتح الواجهة التفاعلية!", reply_markup=main_menu())

# التحقق من رقم الهاتف لمنع التكرار (Anti-Cheat)
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
                await message.answer("⛔ هذا الرقم مستخدم مسبقاً في حساب آخر! غير مسموح بتكرار الحسابات.")
                return

        await db.execute("""
            INSERT INTO users (user_id, phone_number, olk_balance) VALUES (?, ?, 10.0)
            ON CONFLICT(user_id) DO UPDATE SET phone_number = excluded.phone_number
        """, (message.from_user.id, contact.phone_number))
        await db.commit()

    await message.answer("✅ تم توثيق حسابك بنجاح وحصلت على مكافأة ترحيبية +10 OLK!", reply_markup=main_menu())

# فحص الاشتراك
@dp.callback_query(F.data == "verify_sub")
async def verify_sub_handler(callback: CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("✅ تم التحقق من الاشتراك بنجاح!", reply_markup=main_menu())
    else:
        await callback.answer("❌ لم تنضم للقناة بعد، اضغط على الرابط وانضم أولاً.", show_alert=True)

# التعدين اليومي
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

# عرض الرصيد
@dp.callback_query(F.data == "balance")
async def balance_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT olk_balance, gram_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            olk, gram = row if row else (0.0, 0.0)

    text = f"📊 محفظتك في OLKA VIP:\n\n• رصيد OLK: {olk:.2f} OLK\n• رصيد Gram: {gram:.4f} Gram\n\n💡 سعر الصرف: كل {CONVERSION_RATE} OLK = 1 Gram\n💳 الحد الأدنى للسحب: {MIN_WITHDRAW_GRAM} Gram"
    await callback.message.edit_text(text, reply_markup=main_menu())

# تحويل الرصيد
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

# طلب سحب
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

# معالجة عنوان المحفظة وإرسال الإشعار
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

# خادم الويب لعرض صفحة الميني آب وإبقاء الخدمة نشطة
async def web_handler(request):
    return web.Response(text=MINI_APP_HTML, content_type="text/html")

async def main():
    await init_db()
    print("Bot is running with Web App support...")

    # تشغيل خادم aiohttp المتوافق مع متطلبات Render
    app = web.Application()
    app.router.add_get("/", web_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    # تشغيل استطلاع البوت
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
