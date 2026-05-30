from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ── REPLY KEYBOARDS ───────────────────────────────────────────────────────────

def main_menu_kb():
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="📝 Testlar"), KeyboardButton(text="📊 Natijalarim"))
    b.row(KeyboardButton(text="📸 Topshiriq yuborish"), KeyboardButton(text="🔗 Referal"))
    b.row(KeyboardButton(text="👤 Profilim"))
    return b.as_markup(resize_keyboard=True)


def admin_menu_kb():
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="➕ Test yaratish"), KeyboardButton(text="📋 Testlar"))
    b.row(KeyboardButton(text="📸 Screenshotlar"), KeyboardButton(text="📊 Statistika"))
    b.row(KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="👥 Foydalanuvchilar"))
    b.row(KeyboardButton(text="🔙 Asosiy menyu"))
    return b.as_markup(resize_keyboard=True)


def settings_menu_kb():
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="📢 Kanallar"), KeyboardButton(text="📋 Topshiriqlar"))
    b.row(KeyboardButton(text="🔗 Referal sozlash"), KeyboardButton(text="✏️ Xush kelibsiz matni"))
    b.row(KeyboardButton(text="🔙 Admin menyu"))
    return b.as_markup(resize_keyboard=True)


def back_to_admin_kb():
    b = ReplyKeyboardBuilder()
    b.add(KeyboardButton(text="🔙 Admin menyu"))
    return b.as_markup(resize_keyboard=True)


def remove_kb():
    return ReplyKeyboardRemove()


# ── SUBSCRIPTION ──────────────────────────────────────────────────────────────

def subscription_kb(channels: list):
    b = InlineKeyboardBuilder()
    for ch in channels:
        icon = "📢" if ch["type"] == "telegram" else "📸"
        b.row(InlineKeyboardButton(text=f"{icon} {ch['name']}", url=ch["link"]))
    b.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription"))
    return b.as_markup()


# ── TESTS ─────────────────────────────────────────────────────────────────────

def tests_list_kb(tests: list):
    b = InlineKeyboardBuilder()
    for t in tests:
        b.row(InlineKeyboardButton(text=f"📝 {t['title']}", callback_data=f"test_info_{t['id']}"))
    return b.as_markup()


def test_start_kb(test_id: int):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="▶️ Boshlash", callback_data=f"start_test_{test_id}"))
    return b.as_markup()


def answer_kb(q_index: int, options: dict):
    b = InlineKeyboardBuilder()
    for key, val in options.items():
        label = val[:45] + "…" if len(val) > 45 else val
        b.row(InlineKeyboardButton(text=f"{key}) {label}", callback_data=f"answer_{q_index}_{key}"))
    return b.as_markup()


# ── ADMIN – TEST ──────────────────────────────────────────────────────────────

def admin_tests_kb(tests: list):
    b = InlineKeyboardBuilder()
    for t in tests:
        icon = "✅" if t["is_active"] else "❌"
        b.row(InlineKeyboardButton(text=f"{icon} {t['title']}", callback_data=f"adm_test_{t['id']}"))
    b.row(InlineKeyboardButton(text="➕ Yangi test", callback_data="create_new_test"))
    return b.as_markup()


def admin_test_manage_kb(test_id: int, is_active: int):
    b = InlineKeyboardBuilder()
    toggle_txt = "❌ O'chirish" if is_active else "✅ Yoqish"
    b.row(
        InlineKeyboardButton(text="➕ Savol", callback_data=f"add_q_{test_id}"),
        InlineKeyboardButton(text="📋 Savollar", callback_data=f"list_q_{test_id}")
    )
    b.row(
        InlineKeyboardButton(text=toggle_txt, callback_data=f"toggle_test_{test_id}"),
        InlineKeyboardButton(text="📊 Natijalar", callback_data=f"test_res_{test_id}")
    )
    b.row(InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_test_ask_{test_id}"))
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_tests_back"))
    return b.as_markup()


def confirm_delete_test_kb(test_id: int):
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Ha, o'chir", callback_data=f"del_test_{test_id}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data=f"adm_test_{test_id}")
    )
    return b.as_markup()


# ── ADMIN – CHANNELS ──────────────────────────────────────────────────────────

def channels_list_kb(channels: list):
    b = InlineKeyboardBuilder()
    for ch in channels:
        icon = "✅" if ch["is_active"] else "❌"
        tp = "TG" if ch["type"] == "telegram" else "IG"
        b.row(InlineKeyboardButton(
            text=f"{icon}[{tp}] {ch['name']}",
            callback_data=f"ch_manage_{ch['id']}"
        ))
    b.row(InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel"))
    return b.as_markup()


def channel_manage_kb(ch_id: int, is_active: int):
    b = InlineKeyboardBuilder()
    toggle_txt = "❌ O'chirish" if is_active else "✅ Yoqish"
    b.row(
        InlineKeyboardButton(text=toggle_txt, callback_data=f"ch_toggle_{ch_id}"),
        InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"ch_delete_{ch_id}")
    )
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ch_back"))
    return b.as_markup()


# ── ADMIN – TASKS ─────────────────────────────────────────────────────────────

def tasks_list_kb(tasks: list):
    b = InlineKeyboardBuilder()
    for t in tasks:
        icon = "✅" if t["is_active"] else "❌"
        b.row(InlineKeyboardButton(text=f"{icon} {t['title']}", callback_data=f"task_manage_{t['id']}"))
    b.row(InlineKeyboardButton(text="➕ Topshiriq qo'shish", callback_data="add_task"))
    return b.as_markup()


def task_manage_kb(task_id: int, is_active: int):
    b = InlineKeyboardBuilder()
    toggle_txt = "❌ O'chirish" if is_active else "✅ Yoqish"
    b.row(
        InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"task_edit_{task_id}"),
        InlineKeyboardButton(text=toggle_txt, callback_data=f"task_toggle_{task_id}")
    )
    b.row(InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"task_delete_{task_id}"))
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="task_back"))
    return b.as_markup()


# ── ADMIN – SCREENSHOT ────────────────────────────────────────────────────────

def review_kb(sid: int, uid: int):
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"appr_{sid}_{uid}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rej_{sid}_{uid}")
    )
    return b.as_markup()


# ── REFERRAL ──────────────────────────────────────────────────────────────────

def referral_settings_kb():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🎁 Bonus sonini o'zgartir", callback_data="ref_set_bonus"))
    b.row(InlineKeyboardButton(text="🔢 Minimal referal soni", callback_data="ref_set_min"))
    b.row(InlineKeyboardButton(text="🏆 Top referal ro'yxati", callback_data="ref_top"))
    b.row(InlineKeyboardButton(text="📊 Barcha referallar", callback_data="ref_all_stats"))
    return b.as_markup()


def cancel_inline_kb():
    b = InlineKeyboardBuilder()
    b.add(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_inline"))
    return b.as_markup()
