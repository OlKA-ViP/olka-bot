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
            InlineKeyboardButton(text="⛏️ تعدين OLK", callback_data="claim"),
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
            "👋 مرحباً بك في OLKA VIP GAME!\n\n🔒 لحماية النظام من الحسابات المتعددة، يلزم توثيق الحساب برقم الهاتف لمرة واحدة فقط:",
            reply_markup=get_contact_keyboard()
        )
        return

    if not await check_subscription(user_id):
        await message.answer(
            f"⚠️ للمتابعة داخل البوت، يجب أولاً الانضمام لقناتنا الرسمية OLKA AD:\n{SPONSOR_CHANNEL}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="انضم للقناة الآن 📢", url="https://t.me/olka_ad")],
                [InlineKeyboardButton(text="تحقق من الاشتراك ✅", callback_data="verify_sub")]
            ])
        )
        return

    await message.answer("🪙 مرحباً بك في لوحة تحكم OLKA VIP:", reply_markup=main_menu())

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
                await message.answer("⛔ هذا الرقم مستخدم مسبقاً! غير مسموح بتعدد الحسابات.")
                return

        await db.execute("""
            INSERT INTO users (user_id, phone_number, olk_balance) VALUES (?, ?, 10.0)
            ON CONFLICT(user_id) DO UPDATE SET phone_number = excluded.phone_number
        """, (message.from_user.id, contact.phone_number))
        await db.commit()

    await message.answer("✅ تم توثيق حسابك بنجاح وحصلت على مكافأة +10 OLK!", reply_markup=main_menu())

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
            await callback.answer(f"⏳ يمكنك التعدين مجدداً بعد: {hours} ساعة و {mins} دقيقة.", show_alert=True)
            return

        await db.execute("UPDATE users SET olk_balance = olk_balance + 20.0, last_claim = ? WHERE user_id = ?", (current_time, user_id))
        await db.commit()

    await callback.answer("✅ تمت إضافة 20 OLK إلى رصيدك!", show_alert=True)
    await callback.message.edit_text("🎉 تم التعدين بنجاح اليوم.", reply_markup=main_menu())

@dp.callback_query(F.data == "balance")
async def balance_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with aiosqlite.connect("olka_vip.db") as db:
        async with db.execute("SELECT olk_balance, gram_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            olk, gram = row if row else (0.0, 0.0)

    text = f"📊 محفظتك في OLKA VIP:\n\n• رصيد OLK: {olk:.2f} OLK\n• رصيد Gram: {gram:.4f} Gram\n\n💡 الصرف: كل {CONVERSION_RATE} OLK = 1 Gram\n💳 الحد الأدنى للسحب: {MIN_WITHDRAW_GRAM} Gram"
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

    await callback.answer(f"✅ تم تحويل {olk:.2f} OLK إلى {gram_added:.4f} Gram!", show_alert=True)
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

async def health_check(request):
    return web.Response(text="Bot is running!")

async def main():
    await init_db()
    print("Bot is running...")
    
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

