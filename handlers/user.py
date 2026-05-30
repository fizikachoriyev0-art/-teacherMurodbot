from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
import database as db
from keyboards import main_menu_kb, admin_menu_kb, subscription_kb
from config import ADMIN_IDS

router = Router()


async def check_tg_subscriptions(bot: Bot, uid: int) -> bool:
    channels = db.get_channels(active_only=True)
    for ch in channels:
        if ch["type"] == "telegram" and ch["channel_id"]:
            try:
                m = await bot.get_chat_member(ch["channel_id"], uid)
                if m.status in ("left", "kicked", "banned"):
                    return False
            except Exception as e:
                print(f"Kanal tekshiruv xato: {e}")
                return False
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    u = message.from_user

    # Referal parametrini tekshirish: /start ref_12345
    referrer_id = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1][4:])
        except ValueError:
            pass

    # Foydalanuvchini bazaga yozish
    db.upsert_user(u.id, u.username, u.full_name, referred_by=referrer_id)

    # Agar yangi foydalanuvchi va referal bo'lsa
    if referrer_id and referrer_id != u.id:
        success = db.register_referral(referrer_id, u.id)
        if success:
            # Taklif qiluvchiga xabar yuborish
            try:
                bonus = db.get_setting("referral_bonus", "1")
                referrer = db.get_user(referrer_id)
                await bot.send_message(
                    chat_id=referrer_id,
                    text=(
                        f"🎉 <b>Yangi referal!</b>\n\n"
                        f"👤 {u.full_name} sizning havolangiz orqali botga qo'shildi!\n"
                        f"🎁 Sizga +{bonus} bonus berildi.\n\n"
                        f"Jami referallaringiz: {(referrer['referral_count'] or 0) + 1} ta"
                    ),
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Referalga xabar yuborib bo'lmadi: {e}")

    is_admin = u.id in ADMIN_IDS
    kb = admin_menu_kb() if is_admin else main_menu_kb()
    welcome = db.get_setting("welcome_text", "👋 Botga xush kelibsiz!")

    text = (
        f"👋 Salom, <b>{u.full_name}</b>!\n\n"
        f"{welcome}"
    )
    if is_admin:
        text += "\n\n🔐 <b>Admin rejimida ishlamoqdasiz</b>"

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Ruxsat yo'q!")
        return
    await message.answer("🔐 Admin panel:", reply_markup=admin_menu_kb())


@router.message(F.text == "👤 Profilim")
async def show_profile(message: Message):
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user:
        await message.answer("❌ /start bosing.")
        return

    results = db.get_user_results(uid)
    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    sub_icon = "✅" if user["is_subscribed"] else "❌"
    ss = user["screenshot_status"]
    ss_icon = "✅ Tasdiqlangan" if ss == "approved" else ("⏳ Kutilmoqda" if ss == "pending" else "❌ Yuklanmagan")

    referrals, ref_data = db.get_referral_stats(uid)
    ref_count = ref_data["referral_count"] if ref_data else 0
    ref_bonus = ref_data["referral_bonus"] if ref_data else 0

    bot_username = (await message.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{uid}"

    text = (
        f"👤 <b>Profil</b>\n\n"
        f"📛 {user['full_name']}\n"
        f"🆔 <code>{uid}</code>\n"
        f"📱 @{user['username'] or 'yo\'q'}\n\n"
        f"<b>📊 Test natijalari:</b>\n"
        f"├ Jami: {total} ta\n"
        f"├ O'tildi: {passed} ta\n"
        f"└ Muvaffaqiyat: {round(passed/total*100) if total else 0}%\n\n"
        f"<b>✅ Holat:</b>\n"
        f"├ Obuna: {sub_icon}\n"
        f"└ Topshiriq: {ss_icon}\n\n"
        f"<b>🔗 Referal:</b>\n"
        f"├ Taklif qilganlar: {ref_count} ta\n"
        f"├ Bonus: {ref_bonus} ta\n"
        f"└ Havola: {ref_link}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())


@router.message(F.text == "🔙 Asosiy menyu")
async def back_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu_kb())
