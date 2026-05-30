from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import database as db
from keyboards import subscription_kb, main_menu_kb, review_kb, tasks_list_kb
from config import ADMIN_IDS

router = Router()


async def check_tg_subs(bot: Bot, uid: int) -> bool:
    channels = db.get_channels(active_only=True)
    for ch in channels:
        if ch["type"] == "telegram" and ch["channel_id"]:
            try:
                m = await bot.get_chat_member(ch["channel_id"], uid)
                if m.status in ("left", "kicked", "banned"):
                    return False
            except Exception as e:
                print(f"Kanal xato: {e}")
                return False
    return True


async def user_has_access(uid: int, bot: Bot) -> tuple[bool, str]:
    user = db.get_user(uid)
    if not user:
        return False, "not_registered"

    # 1. Telegram kanallar
    if not await check_tg_subs(bot, uid):
        return False, "subscription"

    # 2. Topshiriq (screenshot) talabi
    task_required = db.get_setting("task_required", "1") == "1"
    if task_required:
        tasks = db.get_tasks(active_only=True)
        instagram_tasks = [t for t in tasks if t["type"] == "screenshot"]
        if instagram_tasks and user["screenshot_status"] != "approved":
            return False, "task"

    # 3. Referal talabi
    min_ref = int(db.get_setting("referral_min_count", "0"))
    if min_ref > 0 and (user["referral_count"] or 0) < min_ref:
        return False, "referral"

    return True, "ok"


# ── TESTLAR MENYUSI ───────────────────────────────────────────────────────────

@router.message(F.text == "📝 Testlar")
async def show_tests(message: Message, bot: Bot):
    uid = message.from_user.id
    allowed, reason = await user_has_access(uid, bot)

    if not allowed:
        if reason == "subscription":
            channels = db.get_channels(active_only=True)
            await message.answer(
                "⚠️ <b>Avval kanallarga a'zo bo'ling:</b>",
                parse_mode="HTML",
                reply_markup=subscription_kb(channels)
            )
        elif reason == "task":
            tasks = db.get_tasks(active_only=True)
            task = tasks[0] if tasks else None
            text = (
                "⚠️ <b>Topshiriqni bajaring!</b>\n\n"
                f"📋 <b>{task['title']}</b>\n{task['description']}\n\n"
                "Screenshot olib, <b>📸 Topshiriq yuborish</b> tugmasini bosing."
                if task else "⚠️ Topshiriq bajarilmagan."
            )
            await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())
        elif reason == "referral":
            min_ref = db.get_setting("referral_min_count", "0")
            user = db.get_user(uid)
            cur = user["referral_count"] or 0
            await message.answer(
                f"⚠️ <b>Referal talabi!</b>\n\n"
                f"Testlarga kirish uchun kamida <b>{min_ref} ta</b> do'st taklif qiling.\n"
                f"Hozir: <b>{cur} ta</b>\n\n"
                f"🔗 Referal havolangizni <b>🔗 Referal</b> bo'limida toping.",
                parse_mode="HTML",
                reply_markup=main_menu_kb()
            )
        return

    tests = db.get_tests(active_only=True)
    if not tests:
        await message.answer("📭 Hozircha testlar yo'q.", reply_markup=main_menu_kb())
        return

    from keyboards import tests_list_kb
    await message.answer(
        "📝 <b>Mavjud testlar:</b>",
        parse_mode="HTML",
        reply_markup=tests_list_kb(tests)
    )


# ── OBUNA TEKSHIRISH ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    uid = callback.from_user.id
    ok = await check_tg_subs(bot, uid)
    if ok:
        db.set_subscribed(uid)
        await callback.message.edit_text(
            "✅ <b>Telegram obuna tasdiqlandi!</b>\n\nEndi testlardan o'tishingiz mumkin.",
            parse_mode="HTML"
        )
        await callback.message.answer("Davom eting:", reply_markup=main_menu_kb())
    else:
        await callback.answer("❌ Hali barcha kanallarga a'zo emassiz!", show_alert=True)


# ── SCREENSHOT/TOPSHIRIQ ──────────────────────────────────────────────────────

@router.message(F.text == "📸 Topshiriq yuborish")
async def request_task(message: Message):
    uid = message.from_user.id
    user = db.get_user(uid)

    if user and user["screenshot_status"] == "approved":
        await message.answer("✅ Topshirig'ingiz allaqachon tasdiqlangan!", reply_markup=main_menu_kb())
        return

    subs = db.get_user_submissions(uid)
    if any(s["status"] == "pending" for s in subs):
        await message.answer(
            "⏳ Screenshotingiz ko'rib chiqilmoqda. Admin tasdiqlashini kuting.",
            reply_markup=main_menu_kb()
        )
        return

    tasks = db.get_tasks(active_only=True)
    if not tasks:
        await message.answer("📭 Hozircha topshiriqlar yo'q.", reply_markup=main_menu_kb())
        return

    task = tasks[0]
    await message.answer(
        f"📋 <b>{task['title']}</b>\n\n"
        f"{task['description']}\n\n"
        "📸 Screenshotni hozir yuboring:",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )


@router.message(F.photo)
async def receive_photo(message: Message, bot: Bot):
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user:
        return

    if user["screenshot_status"] == "approved":
        return

    tasks = db.get_tasks(active_only=True)
    task_id = tasks[0]["id"] if tasks else None

    file_id = message.photo[-1].file_id
    sid = db.add_submission(uid, file_id, task_id)

    # Foydalanuvchiga javob
    await message.answer(
        "✅ <b>Screenshot qabul qilindi!</b>\n⏳ Admin ko'rib chiqadi.",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )

    # Adminlarga yuborish
    task_title = tasks[0]["title"] if tasks else "Umumiy topshiriq"
    caption = (
        f"📸 <b>Yangi screenshot!</b>\n\n"
        f"👤 {message.from_user.full_name}\n"
        f"🆔 <code>{uid}</code>\n"
        f"📱 @{message.from_user.username or 'yo\'q'}\n"
        f"📋 Topshiriq: {task_title}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=review_kb(sid, uid)
            )
        except Exception as e:
            print(f"Admin {admin_id} ga yuborib bo'lmadi: {e}")
