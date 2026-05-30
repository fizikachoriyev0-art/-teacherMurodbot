# 🤖 Telegram Test Bot

## 📁 Fayl tuzilmasi
```
telegram_bot/
├── bot.py              — Asosiy ishga tushirish fayli
├── config.py           — Token va admin ID sozlamalari
├── database.py         — SQLite bazasi (barcha jadvallar)
├── keyboards.py        — Barcha tugmalar
├── requirements.txt    — Kutubxonalar
└── handlers/
    ├── user.py         — /start, profil (referal link bilan)
    ├── subscription.py — Obuna tekshirish, screenshot qabul
    ├── test_handler.py — Testni yechish jarayoni
    ├── referral.py     — Referal sahifasi
    └── admin.py        — Admin panel (barcha sozlamalar)
```

## ⚙️ O'rnatish

```bash
pip install aiogram==3.7.0
```

## 🔧 Sozlash

`config.py` faylida:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN"   # @BotFather dan oling
ADMIN_IDS = [123456789]        # Sizning Telegram ID ingiz
```

## ▶️ Ishga tushirish

```bash
python bot.py
```

---

## 🗃️ Database jadvallari

| Jadval | Vazifasi |
|--------|----------|
| `users` | Foydalanuvchilar (referal_count, referral_bonus) |
| `referrals` | Kim kimni taklif qildi |
| `channels` | Majburiy kanallar/Instagram |
| `tasks` | Topshiriqlar (screenshot) |
| `tests` | Testlar |
| `questions` | Savollar |
| `test_results` | Natijalar |
| `submissions` | Yuborilgan screenshotlar |
| `settings` | Bot sozlamalari |

---

## 👤 Foydalanuvchi yo'li

```
/start → Obuna tekshirish → Topshiriq (screenshot) → Test yechish
```

**Referal bilan:**
```
/start ref_12345 → Avtomatik bog'lanadi → Taklif qiluvchiga bonus
```

---

## 🔐 Admin panel imkoniyatlari

### ⚙️ Sozlamalar:
- **📢 Kanallar** — Telegram/Instagram qo'shish, o'chirish, yoqish/o'chirish
- **📋 Topshiriqlar** — Topshiriq qo'shish, tahrirlash, o'chirish
- **🔗 Referal sozlash** — Bonus soni, minimal referal talabi, top ro'yxat
- **✏️ Xush kelibsiz matni** — Start xabari matni

### 📝 Test boshqaruvi:
- Test yaratish (nom, tavsif, o'tish bali, vaqt)
- Savol qo'shish (A/B/C/D + to'g'ri javob + izoh)
- Testni yoqish/o'chirish
- Natijalarni ko'rish

### 📸 Screenshot tasdiqlash:
- Kutayotgan screenshotlar ro'yxati
- Tasdiqlash → foydalanuvchiga xabar
- Rad etish + sabab → foydalanuvchiga xabar

---

## 🔗 Referal tizimi

- Har foydalanuvchi `/start ref_{ID}` link orqali taklif qiladi
- Taklif qiluvchi bonus oladi (admin sozlaydi)
- Admin minimal referal soni qo'yishi mumkin (test kirish sharti)
- Top referal ro'yxati admin panelda
- Foydalanuvchi o'z statistikasini **🔗 Referal** tugmasida ko'radi

---

## 🔒 Kirish shartlari (admin sozlaydi)

1. **Telegram kanallarga obuna** (tekshiriladi)
2. **Instagram screenshot tasdiqlash** (admin qo'lda tasdiqlaydi)
3. **Minimal referal soni** (0 = talab yo'q, admin o'rnatadi)
