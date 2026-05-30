from aiogram import Router, F, Bot
from aiogram.types import Message
import database as db
from keyboards import main_menu_kb

router = Router()


@router.message(F.text == "🔗 Referal")
async def show_referral(message: Message, bot: Bot):
    uid = message.from_user.id
    me = await bot.get_me()
    ref_link = f"https://t.me/{me.username}?start=ref_{uid}"

    referrals, ref_data = db.get_referral_stats(uid)
    ref_count = ref_data["referral_count"] if ref_data else 0
    ref_bonus = ref_data["referral_bonus"] if ref_data else 0

    bonus_per_ref = db.get_setting("referral_bonus", "1")
    min_count = db.get_setting("referral_min_count", "0")

    # Oxirgi 5 ta referal
    recent_txt = ""
    if referrals:
        recent_txt = "\n\n<b>🕐 So'nggi referallar:</b>\n"
        for r in list(referrals)[:5]:
            name = r["full_name"] or r["username"] or f"ID:{r['referred_id']}"
            date = r["created_at"][:10]
            recent_txt += f"• {name} — {date}\n"

    min_info = ""
    if int(min_count) > 0:
        done = "✅" if ref_count >= int(min_count) else "❌"
        min_info = f"\n🎯 Minimal referal talabi: {min_count} ta {done}"

    text = (
        f"🔗 <b>Referal tizimi</b>\n\n"
        f"Do'stlaringizni taklif qiling va bonus oling!\n\n"
        f"🎁 Har bir referal uchun: <b>+{bonus_per_ref} bonus</b>{min_info}\n\n"
        f"<b>Sizning havolangiz:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"📊 Taklif qilganlar: <b>{ref_count} ta</b>\n"
        f"💰 Jami bonus: <b>{ref_bonus} ta</b>"
        f"{recent_txt}\n\n"
        f"💡 Havolani do'stlaringizga yuboring. Ular botga kirganida siz avtomatik bonus olasiz!"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())
