from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
import database as db
from keyboards import (
    admin_menu_kb, settings_menu_kb, back_to_admin_kb,
    admin_tests_kb, admin_test_manage_kb, confirm_delete_test_kb,
    channels_list_kb, channel_manage_kb,
    tasks_list_kb, task_manage_kb,
    review_kb, referral_settings_kb, cancel_inline_kb
)
from config import ADMIN_IDS

router = Router()


# ── FSM ───────────────────────────────────────────────────────────────────────

class CreateTest(StatesGroup):
    title = State()
    description = State()
    pass_score = State()
    time_limit = State()

class AddQuestion(StatesGroup):
    question = State()
    opt_a = State()
    opt_b = State()
    opt_c = State()
    opt_d = State()
    correct = State()
    explanation = State()

class AddChannel(StatesGroup):
    name = State()
    link = State()
    channel_id = State()
    ctype = State()

class AddTask(StatesGroup):
    title = State()
    description = State()

class EditTask(StatesGroup):
    title = State()
    description = State()

class EditWelcome(StatesGroup):
    text = State()

class RejectNote(StatesGroup):
    note = State()

class SetRefBonus(StatesGroup):
    value = State()

class SetRefMin(StatesGroup):
    value = State()


def adm(uid): return uid in ADMIN_IDS


# ── STATISTIKA ────────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Statistika")
async def stats(message: Message):
    if not adm(message.from_user.id): return
    s = db.get_stats()
    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{s['users']}</b>\n"
        f"📝 Faol testlar: <b>{s['tests']}</b>\n"
        f"📋 Natijalar: <b>{s['results']}</b>\n"
        f"📸 Kutayotgan: <b>{s['pending']}</b>\n"
        f"📢 Kanallar: <b>{s['channels']}</b>\n"
        f"📋 Topshiriqlar: <b>{s['tasks']}</b>\n"
        f"🔗 Jami referallar: <b>{s['referrals']}</b>",
        parse_mode="HTML", reply_markup=admin_menu_kb()
    )


@router.message(F.text == "👥 Foydalanuvchilar")
async def users_list(message: Message):
    if not adm(message.from_user.id): return
    users = db.get_all_users()
    text = f"👥 <b>Foydalanuvchilar ({len(users)}):</b>\n\n"
    for u in users[:20]:
        s = "✅" if u["is_subscribed"] else "❌"
        ss = "📸✅" if u["screenshot_status"] == "approved" else "📸❌"
        ref = f"🔗{u['referral_count']}" if u["referral_count"] else ""
        text += f"{s}{ss} {ref} <b>{u['full_name']}</b> <code>{u['user_id']}</code>\n"
    if len(users) > 20:
        text += f"\n... yana {len(users)-20} ta"
    await message.answer(text, parse_mode="HTML", reply_markup=admin_menu_kb())


# ── SOZLAMALAR ────────────────────────────────────────────────────────────────

@router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(message: Message):
    if not adm(message.from_user.id): return
    await message.answer("⚙️ <b>Sozlamalar</b>", parse_mode="HTML", reply_markup=settings_menu_kb())


@router.message(F.text == "🔙 Admin menyu")
async def back_admin(message: Message, state: FSMContext):
    await state.clear()
    if not adm(message.from_user.id): return
    await message.answer("🔐 Admin panel:", reply_markup=admin_menu_kb())


# ── XUSH KELIBSIZ MATNI ───────────────────────────────────────────────────────

@router.message(F.text == "✏️ Xush kelibsiz matni")
async def edit_welcome_start(message: Message, state: FSMContext):
    if not adm(message.from_user.id): return
    current = db.get_setting("welcome_text")
    await state.set_state(EditWelcome.text)
    await message.answer(
        f"✏️ <b>Joriy matn:</b>\n\n{current}\n\n"
        "Yangi matn yozing:",
        parse_mode="HTML", reply_markup=back_to_admin_kb()
    )

@router.message(EditWelcome.text)
async def save_welcome(message: Message, state: FSMContext):
    db.set_setting("welcome_text", message.text)
    await state.clear()
    await message.answer("✅ Matn yangilandi!", reply_markup=settings_menu_kb())


# ── KANALLAR ──────────────────────────────────────────────────────────────────

@router.message(F.text == "📢 Kanallar")
async def channels_menu(message: Message):
    if not adm(message.from_user.id): return
    channels = db.get_channels(active_only=False)
    await message.answer(
        "📢 <b>Kanallar va sahifalar:</b>",
        parse_mode="HTML",
        reply_markup=channels_list_kb(channels)
    )

@router.callback_query(F.data == "add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    if not adm(callback.from_user.id): return
    await state.set_state(AddChannel.name)
    await callback.message.answer("📢 Kanal nomini kiriting (masalan: Asosiy kanal):")
    await callback.answer()

@router.message(AddChannel.name)
async def add_channel_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddChannel.link)
    await message.answer("🔗 Havola kiriting (https://t.me/... yoki https://instagram.com/...):")

@router.message(AddChannel.link)
async def add_channel_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text)
    await state.set_state(AddChannel.ctype)
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="📢 Telegram", callback_data="ch_type_telegram"),
        InlineKeyboardButton(text="📸 Instagram", callback_data="ch_type_instagram")
    )
    await message.answer("Kanal turini tanlang:", reply_markup=b.as_markup())

@router.callback_query(F.data.startswith("ch_type_"))
async def add_channel_type(callback: CallbackQuery, state: FSMContext):
    ctype = callback.data.split("_")[2]
    await state.update_data(ctype=ctype)
    if ctype == "telegram":
        await state.set_state(AddChannel.channel_id)
        await callback.message.answer(
            "🆔 Kanal username kiriting (@username yoki -100xxxxxxx):\n"
            "(<i>Obuna tekshirish uchun bot kanalda admin bo'lishi kerak</i>)",
            parse_mode="HTML"
        )
    else:
        data = await state.get_data()
        db.add_channel(data["name"], data["link"], ctype, "")
        await state.clear()
        await callback.message.answer("✅ Instagram sahifa qo'shildi!", reply_markup=settings_menu_kb())
    await callback.answer()

@router.message(AddChannel.channel_id)
async def add_channel_id(message: Message, state: FSMContext):
    data = await state.get_data()
    db.add_channel(data["name"], data["link"], data["ctype"], message.text.strip())
    await state.clear()
    await message.answer("✅ Kanal qo'shildi!", reply_markup=settings_menu_kb())

@router.callback_query(F.data.startswith("ch_manage_"))
async def channel_manage(callback: CallbackQuery):
    cid = int(callback.data.split("_")[2])
    channels = db.get_channels(active_only=False)
    ch = next((c for c in channels if c["id"] == cid), None)
    if not ch:
        await callback.answer("Topilmadi!", show_alert=True); return
    tp = "Telegram" if ch["type"] == "telegram" else "Instagram"
    text = (
        f"📢 <b>{ch['name']}</b>\n"
        f"🔗 {ch['link']}\n"
        f"📱 Tur: {tp}\n"
        f"📊 Holat: {'✅ Faol' if ch['is_active'] else '❌ Nofaol'}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=channel_manage_kb(cid, ch["is_active"]))

@router.callback_query(F.data.startswith("ch_toggle_"))
async def ch_toggle(callback: CallbackQuery):
    cid = int(callback.data.split("_")[2])
    db.toggle_channel(cid)
    await callback.answer("Holat o'zgardi!")
    channels = db.get_channels(active_only=False)
    ch = next((c for c in channels if c["id"] == cid), None)
    if ch:
        tp = "Telegram" if ch["type"] == "telegram" else "Instagram"
        await callback.message.edit_text(
            f"📢 <b>{ch['name']}</b>\n🔗 {ch['link']}\n📱 {tp}\n📊 {'✅ Faol' if ch['is_active'] else '❌ Nofaol'}",
            parse_mode="HTML", reply_markup=channel_manage_kb(cid, ch["is_active"])
        )

@router.callback_query(F.data.startswith("ch_delete_"))
async def ch_delete(callback: CallbackQuery):
    cid = int(callback.data.split("_")[2])
    db.delete_channel(cid)
    await callback.message.edit_text("✅ Kanal o'chirildi!")

@router.callback_query(F.data == "ch_back")
async def ch_back(callback: CallbackQuery):
    channels = db.get_channels(active_only=False)
    await callback.message.edit_text("📢 <b>Kanallar:</b>", parse_mode="HTML", reply_markup=channels_list_kb(channels))


# ── TOPSHIRIQLAR ──────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Topshiriqlar")
async def tasks_menu(message: Message):
    if not adm(message.from_user.id): return
    tasks = db.get_tasks(active_only=False)
    await message.answer("📋 <b>Topshiriqlar:</b>", parse_mode="HTML", reply_markup=tasks_list_kb(tasks))

@router.callback_query(F.data == "add_task")
async def add_task_start(callback: CallbackQuery, state: FSMContext):
    if not adm(callback.from_user.id): return
    await state.set_state(AddTask.title)
    await callback.message.answer("📋 Topshiriq nomini kiriting:")
    await callback.answer()

@router.message(AddTask.title)
async def add_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddTask.description)
    await message.answer(
        "📝 Topshiriq mazmunini kiriting:\n"
        "<i>(Foydalanuvchiga ko'rsatiladigan to'liq ko'rsatma)</i>",
        parse_mode="HTML"
    )

@router.message(AddTask.description)
async def add_task_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    db.add_task(data["title"], message.text)
    await state.clear()
    await message.answer("✅ Topshiriq qo'shildi!", reply_markup=settings_menu_kb())

@router.callback_query(F.data.startswith("task_manage_"))
async def task_manage(callback: CallbackQuery):
    tid = int(callback.data.split("_")[2])
    t = db.get_task(tid)
    if not t:
        await callback.answer("Topilmadi!", show_alert=True); return
    text = (
        f"📋 <b>{t['title']}</b>\n\n"
        f"{t['description']}\n\n"
        f"📊 Holat: {'✅ Faol' if t['is_active'] else '❌ Nofaol'}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=task_manage_kb(tid, t["is_active"]))

@router.callback_query(F.data.startswith("task_toggle_"))
async def task_toggle(callback: CallbackQuery):
    tid = int(callback.data.split("_")[2])
    db.toggle_task(tid)
    await callback.answer("Holat o'zgardi!")
    t = db.get_task(tid)
    await callback.message.edit_text(
        f"📋 <b>{t['title']}</b>\n\n{t['description']}\n\n📊 {'✅ Faol' if t['is_active'] else '❌ Nofaol'}",
        parse_mode="HTML", reply_markup=task_manage_kb(tid, t["is_active"])
    )

@router.callback_query(F.data.startswith("task_edit_"))
async def task_edit_start(callback: CallbackQuery, state: FSMContext):
    tid = int(callback.data.split("_")[2])
    t = db.get_task(tid)
    await state.set_state(EditTask.title)
    await state.update_data(task_id=tid, old_desc=t["description"])
    await callback.message.answer(
        f"✏️ Yangi nom kiriting:\n<i>Joriy: {t['title']}</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(EditTask.title)
async def task_edit_title(message: Message, state: FSMContext):
    await state.update_data(new_title=message.text)
    await state.set_state(EditTask.description)
    data = await state.get_data()
    await message.answer(
        f"✏️ Yangi mazmun kiriting:\n<i>Joriy: {data['old_desc'][:100]}</i>",
        parse_mode="HTML"
    )

@router.message(EditTask.description)
async def task_edit_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    db.update_task(data["task_id"], data["new_title"], message.text)
    await state.clear()
    await message.answer("✅ Topshiriq yangilandi!", reply_markup=settings_menu_kb())

@router.callback_query(F.data.startswith("task_delete_"))
async def task_delete(callback: CallbackQuery):
    tid = int(callback.data.split("_")[2])
    db.delete_task(tid)
    await callback.message.edit_text("✅ Topshiriq o'chirildi!")

@router.callback_query(F.data == "task_back")
async def task_back(callback: CallbackQuery):
    tasks = db.get_tasks(active_only=False)
    await callback.message.edit_text("📋 <b>Topshiriqlar:</b>", parse_mode="HTML", reply_markup=tasks_list_kb(tasks))


# ── REFERAL SOZLASH ───────────────────────────────────────────────────────────

@router.message(F.text == "🔗 Referal sozlash")
async def referral_settings(message: Message):
    if not adm(message.from_user.id): return
    bonus = db.get_setting("referral_bonus", "1")
    min_count = db.get_setting("referral_min_count", "0")
    stats = db.get_stats()
    text = (
        f"🔗 <b>Referal sozlamalari</b>\n\n"
        f"🎁 Har bir referal uchun bonus: <b>{bonus} ta</b>\n"
        f"🔢 Minimal referal talabi: <b>{min_count} ta</b>\n"
        f"   {'(talab yo\'q)' if min_count == '0' else '(test uchun shart)'}\n\n"
        f"📊 Jami referallar: <b>{stats['referrals']}</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=referral_settings_kb())

@router.callback_query(F.data == "ref_set_bonus")
async def ref_bonus_start(callback: CallbackQuery, state: FSMContext):
    if not adm(callback.from_user.id): return
    await state.set_state(SetRefBonus.value)
    current = db.get_setting("referral_bonus", "1")
    await callback.message.answer(
        f"🎁 Har bir referal uchun bonus sonini kiriting:\n<i>Joriy: {current}</i>",
        parse_mode="HTML", reply_markup=cancel_inline_kb()
    )
    await callback.answer()

@router.message(SetRefBonus.value)
async def ref_bonus_save(message: Message, state: FSMContext):
    try:
        val = int(message.text)
        if val < 0: raise ValueError
    except ValueError:
        await message.answer("❌ Musbat son kiriting!"); return
    db.set_setting("referral_bonus", str(val))
    await state.clear()
    await message.answer(f"✅ Bonus {val} ta qilib o'rnatildi!", reply_markup=settings_menu_kb())

@router.callback_query(F.data == "ref_set_min")
async def ref_min_start(callback: CallbackQuery, state: FSMContext):
    if not adm(callback.from_user.id): return
    await state.set_state(SetRefMin.value)
    current = db.get_setting("referral_min_count", "0")
    await callback.message.answer(
        f"🔢 Testlarga kirish uchun minimal referal sonini kiriting:\n"
        f"<i>Joriy: {current} (0 = talab yo'q)</i>",
        parse_mode="HTML", reply_markup=cancel_inline_kb()
    )
    await callback.answer()

@router.message(SetRefMin.value)
async def ref_min_save(message: Message, state: FSMContext):
    try:
        val = int(message.text)
        if val < 0: raise ValueError
    except ValueError:
        await message.answer("❌ 0 yoki undan katta son kiriting!"); return
    db.set_setting("referral_min_count", str(val))
    await state.clear()
    msg = f"✅ Minimal referal: {val} ta" + (" (talab yo'q)" if val == 0 else " (test uchun shart)")
    await message.answer(msg, reply_markup=settings_menu_kb())

@router.callback_query(F.data == "ref_top")
async def ref_top(callback: CallbackQuery):
    top = db.get_top_referrers(10)
    if not top:
        await callback.answer("Hali referallar yo'q!", show_alert=True); return
    text = "🏆 <b>Top referal qiluvchilar:</b>\n\n"
    medals = ["🥇","🥈","🥉"] + ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    for i, u in enumerate(top):
        name = u["full_name"] or u["username"] or f"ID:{u['user_id']}"
        text += f"{medals[i]} {name} — {u['referral_count']} ta referal (bonus: {u['referral_bonus']})\n"
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "ref_all_stats")
async def ref_all(callback: CallbackQuery):
    from database import get_conn
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.*, u1.full_name as ref_name, u2.full_name as new_name
        FROM referrals r
        JOIN users u1 ON r.referrer_id = u1.user_id
        JOIN users u2 ON r.referred_id = u2.user_id
        ORDER BY r.created_at DESC LIMIT 20
    """).fetchall()
    conn.close()
    if not rows:
        await callback.answer("Hali referallar yo'q!", show_alert=True); return
    text = "📊 <b>So'nggi referallar:</b>\n\n"
    for r in rows:
        text += f"👤 {r['ref_name']} → {r['new_name']} ({r['created_at'][:10]})\n"
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# ── TEST YARATISH ─────────────────────────────────────────────────────────────

@router.message(F.text == "➕ Test yaratish")
async def create_test_start(message: Message, state: FSMContext):
    if not adm(message.from_user.id): return
    await state.set_state(CreateTest.title)
    await message.answer("📝 Test nomini kiriting:", reply_markup=back_to_admin_kb())

@router.message(CreateTest.title)
async def ct_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(CreateTest.description)
    await message.answer("✏️ Tavsif kiriting (o'tkazish uchun — yuboring):")

@router.message(CreateTest.description)
async def ct_desc(message: Message, state: FSMContext):
    await state.update_data(description="" if message.text == "-" else message.text)
    await state.set_state(CreateTest.pass_score)
    await message.answer("🎯 O'tish bali (%) kiriting (standart: 60):")

@router.message(CreateTest.pass_score)
async def ct_score(message: Message, state: FSMContext):
    try:
        s = int(message.text)
        if not 1 <= s <= 100: raise ValueError
    except ValueError:
        await message.answer("❌ 1-100 orasida son kiriting!"); return
    await state.update_data(pass_score=s)
    await state.set_state(CreateTest.time_limit)
    await message.answer("⏱ Vaqt chegarasi (daqiqada, cheksiz uchun 0):")

@router.message(CreateTest.time_limit)
async def ct_time(message: Message, state: FSMContext):
    try:
        t = int(message.text)
        if t < 0: raise ValueError
    except ValueError:
        await message.answer("❌ 0 yoki musbat son kiriting!"); return
    data = await state.get_data()
    tid = db.create_test(data["title"], data["description"], data["pass_score"], t, message.from_user.id)
    await state.clear()
    await message.answer(
        f"✅ <b>Test yaratildi!</b>\n📝 {data['title']}\n🎯 {data['pass_score']}%",
        parse_mode="HTML",
        reply_markup=admin_test_manage_kb(tid, 1)
    )


# ── TESTLAR RO'YXATI ──────────────────────────────────────────────────────────

@router.message(F.text == "📋 Testlar")
async def tests_list(message: Message):
    if not adm(message.from_user.id): return
    tests = db.get_tests(active_only=False)
    if not tests:
        await message.answer("📭 Testlar yo'q.", reply_markup=admin_menu_kb()); return
    await message.answer("📋 <b>Testlar:</b>", parse_mode="HTML", reply_markup=admin_tests_kb(tests))

@router.callback_query(F.data.startswith("adm_test_"))
async def adm_test_detail(callback: CallbackQuery):
    tid = int(callback.data.split("_")[2])
    test = db.get_test(tid)
    if not test:
        await callback.answer("Topilmadi!", show_alert=True); return
    qc = db.count_questions(tid)
    await callback.message.edit_text(
        f"📝 <b>{test['title']}</b>\n\n"
        f"❓ Savollar: {qc} ta\n"
        f"🎯 O'tish bali: {test['pass_score']}%\n"
        f"📊 Holat: {'✅ Faol' if test['is_active'] else '❌ Nofaol'}",
        parse_mode="HTML",
        reply_markup=admin_test_manage_kb(tid, test["is_active"])
    )

@router.callback_query(F.data == "adm_tests_back")
async def adm_tests_back(callback: CallbackQuery):
    tests = db.get_tests(active_only=False)
    await callback.message.edit_text("📋 <b>Testlar:</b>", parse_mode="HTML", reply_markup=admin_tests_kb(tests))

@router.callback_query(F.data.startswith("toggle_test_"))
async def toggle_test_cb(callback: CallbackQuery):
    tid = int(callback.data.split("_")[2])
    db.toggle_test(tid)
    test = db.get_test(tid)
    qc = db.count_questions(tid)
    await callback.answer("Holat o'zgardi!")
    await callback.message.edit_text(
        f"📝 <b>{test['title']}</b>\n\n❓ Savollar: {qc} ta\n📊 {'✅ Faol' if test['is_active'] else '❌ Nofaol'}",
        parse_mode="HTML",
        reply_markup=admin_test_manage_kb(tid, test["is_active"])
    )

@router.callback_query(F.data.startswith("del_test_ask_"))
async def del_test_ask(callback: CallbackQuery):
    tid = int(callback.data.split("_")[3])
    test = db.get_test(tid)
    await callback.message.edit_text(
        f"⚠️ '<b>{test['title']}</b>' testini o'chirasizmi?\nBarcha savollar ham o'chadi!",
        parse_mode="HTML", reply_markup=confirm_delete_test_kb(tid)
    )

@router.callback_query(F.data.startswith("del_test_"))
async def del_test_cb(callback: CallbackQuery):
    # del_test_ask_ bilan boshlanadigan callbacklarni filtr
    if "ask" in callback.data: return
    tid = int(callback.data.split("_")[2])
    db.delete_test(tid)
    await callback.message.edit_text("✅ Test o'chirildi!")


# ── SAVOL QO'SHISH ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("add_q_"))
async def add_q_start(callback: CallbackQuery, state: FSMContext):
    tid = int(callback.data.split("_")[2])
    await state.set_state(AddQuestion.question)
    await state.update_data(test_id=tid)
    await callback.message.answer(
        "➕ <b>Savol qo'shish</b>\n\nSavol matnini kiriting:\n<i>Bekor qilish: /cancel</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AddQuestion.question)
async def aq_q(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await state.set_state(AddQuestion.opt_a)
    await message.answer("A) variantini kiriting:")

@router.message(AddQuestion.opt_a)
async def aq_a(message: Message, state: FSMContext):
    await state.update_data(opt_a=message.text)
    await state.set_state(AddQuestion.opt_b)
    await message.answer("B) variantini kiriting:")

@router.message(AddQuestion.opt_b)
async def aq_b(message: Message, state: FSMContext):
    await state.update_data(opt_b=message.text)
    await state.set_state(AddQuestion.opt_c)
    await message.answer("C) variantini kiriting:")

@router.message(AddQuestion.opt_c)
async def aq_c(message: Message, state: FSMContext):
    await state.update_data(opt_c=message.text)
    await state.set_state(AddQuestion.opt_d)
    await message.answer("D) variantini kiriting:")

@router.message(AddQuestion.opt_d)
async def aq_d(message: Message, state: FSMContext):
    await state.update_data(opt_d=message.text)
    await state.set_state(AddQuestion.correct)
    await message.answer("✅ To'g'ri javob: A, B, C yoki D?")

@router.message(AddQuestion.correct)
async def aq_correct(message: Message, state: FSMContext):
    ans = message.text.upper().strip()
    if ans not in ("A","B","C","D"):
        await message.answer("❌ Faqat A, B, C yoki D kiriting!"); return
    await state.update_data(correct=ans)
    await state.set_state(AddQuestion.explanation)
    await message.answer("💡 Izoh kiriting (ixtiyoriy, o'tkazish uchun — yuboring):")

@router.message(AddQuestion.explanation)
async def aq_expl(message: Message, state: FSMContext):
    data = await state.get_data()
    expl = "" if message.text == "-" else message.text
    db.add_question(
        data["test_id"], data["question"],
        data["opt_a"], data["opt_b"], data["opt_c"], data["opt_d"],
        data["correct"], expl
    )
    qc = db.count_questions(data["test_id"])
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="➕ Yana savol", callback_data=f"add_q_{data['test_id']}"),
        InlineKeyboardButton(text="📋 Testga qayt", callback_data=f"adm_test_{data['test_id']}")
    )
    await state.update_data(test_id=data["test_id"])
    await state.set_state(None)
    await message.answer(
        f"✅ Savol qo'shildi! Jami: <b>{qc} ta</b>",
        parse_mode="HTML", reply_markup=b.as_markup()
    )

@router.callback_query(F.data.startswith("list_q_"))
async def list_q(callback: CallbackQuery):
    tid = int(callback.data.split("_")[2])
    qs = db.get_questions(tid)
    if not qs:
        await callback.answer("Savollar yo'q!", show_alert=True); return
    text = f"📋 <b>Savollar ({len(qs)} ta):</b>\n\n"
    for i, q in enumerate(qs, 1):
        short = q["question_text"][:60] + ("…" if len(q["question_text"]) > 60 else "")
        text += f"{i}. {short}\n   ✅ {q['correct_answer']}\n\n"
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("test_res_"))
async def test_results_cb(callback: CallbackQuery):
    tid = int(callback.data.split("_")[2])
    results = db.get_test_results(tid)
    test = db.get_test(tid)
    if not results:
        await callback.answer("Natijalar yo'q!", show_alert=True); return
    passed = sum(1 for r in results if r["passed"])
    avg = round(sum(r["score"] for r in results) / len(results))
    text = (
        f"📊 <b>{test['title']} — Natijalar</b>\n\n"
        f"👥 Qatnashdi: {len(results)}\n"
        f"✅ O'tdi: {passed} ({round(passed/len(results)*100)}%)\n"
        f"📈 O'rtacha: {avg}%\n\n"
        "<b>Top natijalar:</b>\n"
    )
    for i, r in enumerate(results[:10], 1):
        icon = "✅" if r["passed"] else "❌"
        name = r["full_name"] or r["username"] or f"ID:{r['user_id']}"
        text += f"{i}. {icon} {name} — {r['score']}%\n"
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# ── SCREENSHOT TASDIQLASH ─────────────────────────────────────────────────────

@router.message(F.text == "📸 Screenshotlar")
async def pending_screenshots(message: Message):
    if not adm(message.from_user.id): return
    subs = db.get_pending_submissions()
    if not subs:
        await message.answer("✅ Kutayotgan screenshotlar yo'q.", reply_markup=admin_menu_kb()); return
    await message.answer(f"📸 <b>{len(subs)} ta screenshot kutmoqda</b>", parse_mode="HTML", reply_markup=admin_menu_kb())
    for s in subs[:5]:
        name = s["full_name"] or s["username"] or f"ID:{s['user_id']}"
        caption = (
            f"📸 <b>Yangi screenshot</b>\n\n"
            f"👤 {name}\n"
            f"🆔 <code>{s['user_id']}</code>\n"
            f"📋 {s['task_title'] or 'Umumiy topshiriq'}\n"
            f"🕐 {s['submitted_at'][:16]}"
        )
        try:
            await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=s["file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=review_kb(s["id"], s["user_id"])
            )
        except Exception as e:
            print(f"Screenshot yuborishda xato: {e}")

@router.callback_query(F.data.startswith("appr_"))
async def approve_cb(callback: CallbackQuery, bot: Bot):
    if not adm(callback.from_user.id): return
    parts = callback.data.split("_")
    sid, uid = int(parts[1]), int(parts[2])
    db.review_submission(sid, "approved", callback.from_user.id)
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n✅ <b>TASDIQLANDI</b>",
        parse_mode="HTML"
    )
    try:
        await bot.send_message(uid, "✅ <b>Screenshotingiz tasdiqlandi!</b>\nEndi testlarga kiring. 📝", parse_mode="HTML")
    except: pass
    await callback.answer("✅ Tasdiqlandi!")

@router.callback_query(F.data.startswith("rej_"))
async def reject_start(callback: CallbackQuery, state: FSMContext):
    if not adm(callback.from_user.id): return
    parts = callback.data.split("_")
    sid, uid = int(parts[1]), int(parts[2])
    await state.set_state(RejectNote.note)
    await state.update_data(sid=sid, uid=uid)
    await callback.message.answer("❌ Rad etish sababini yozing:")
    await callback.answer()

@router.message(RejectNote.note)
async def reject_save(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    db.review_submission(data["sid"], "rejected", message.from_user.id, message.text)
    await state.clear()
    try:
        await bot.send_message(
            data["uid"],
            f"❌ <b>Screenshot rad etildi</b>\n\n📝 Sabab: {message.text}\n\nQaytadan urinib ko'ring.",
            parse_mode="HTML"
        )
    except: pass
    await message.answer("❌ Rad etildi, foydalanuvchiga xabar yuborildi.", reply_markup=admin_menu_kb())


# ── BEKOR QILISH ──────────────────────────────────────────────────────────────

@router.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    await state.clear()
    kb = admin_menu_kb() if adm(message.from_user.id) else None
    await message.answer("❌ Bekor qilindi.", reply_markup=kb)

@router.callback_query(F.data == "cancel_inline")
async def cancel_inline(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()
