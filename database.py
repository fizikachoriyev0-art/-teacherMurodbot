import sqlite3
import json
from datetime import datetime
from config import DB_FILE


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id          INTEGER PRIMARY KEY,
        username         TEXT,
        full_name        TEXT,
        is_subscribed    INTEGER DEFAULT 0,
        screenshot_status TEXT DEFAULT 'none',
        task_completed   INTEGER DEFAULT 0,
        referred_by      INTEGER DEFAULT NULL,
        referral_count   INTEGER DEFAULT 0,
        referral_bonus   INTEGER DEFAULT 0,
        joined_at        TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS referrals (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id  INTEGER NOT NULL,
        referred_id  INTEGER NOT NULL UNIQUE,
        bonus_given  INTEGER DEFAULT 0,
        created_at   TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (referrer_id) REFERENCES users(user_id),
        FOREIGN KEY (referred_id) REFERENCES users(user_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS channels (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        link       TEXT NOT NULL,
        type       TEXT NOT NULL DEFAULT 'telegram',
        channel_id TEXT,
        is_active  INTEGER DEFAULT 1
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT NOT NULL,
        description TEXT NOT NULL,
        type        TEXT DEFAULT 'screenshot',
        is_active   INTEGER DEFAULT 1,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tests (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT NOT NULL,
        description TEXT,
        pass_score  INTEGER DEFAULT 60,
        time_limit  INTEGER DEFAULT 0,
        is_active   INTEGER DEFAULT 1,
        created_by  INTEGER,
        created_at  TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS questions (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id        INTEGER NOT NULL,
        question_text  TEXT NOT NULL,
        option_a       TEXT NOT NULL,
        option_b       TEXT NOT NULL,
        option_c       TEXT NOT NULL,
        option_d       TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        explanation    TEXT DEFAULT '',
        order_num      INTEGER DEFAULT 0,
        FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS test_results (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL,
        test_id         INTEGER NOT NULL,
        score           INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        correct_answers INTEGER NOT NULL,
        passed          INTEGER DEFAULT 0,
        answers_json    TEXT,
        completed_at    TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL,
        task_id      INTEGER,
        file_id      TEXT NOT NULL,
        status       TEXT DEFAULT 'pending',
        admin_note   TEXT,
        reviewed_by  INTEGER,
        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        reviewed_at  TEXT
    )""")

    defaults = {
        "welcome_text":       "👋 Botga xush kelibsiz!\n\nTestlardan o'tish uchun quyidagi shartlarni bajaring.",
        "task_required":      "1",
        "bot_name":           "Test Bot",
        "referral_bonus":     "1",
        "referral_required":  "0",
        "referral_min_count": "0",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()


# ── SETTINGS ──────────────────────────────────────────────────────────────────

def get_setting(key: str, default="") -> str:
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


# ── CHANNELS ──────────────────────────────────────────────────────────────────

def get_channels(active_only=True):
    conn = get_conn()
    q = "SELECT * FROM channels" + (" WHERE is_active=1" if active_only else "") + " ORDER BY id"
    rows = conn.execute(q).fetchall()
    conn.close()
    return rows


def add_channel(name, link, ctype, channel_id="") -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO channels (name, link, type, channel_id) VALUES (?, ?, ?, ?)",
        (name, link, ctype, channel_id)
    )
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def delete_channel(cid: int):
    conn = get_conn()
    conn.execute("DELETE FROM channels WHERE id=?", (cid,))
    conn.commit()
    conn.close()


def toggle_channel(cid: int):
    conn = get_conn()
    conn.execute("UPDATE channels SET is_active = 1 - is_active WHERE id=?", (cid,))
    conn.commit()
    conn.close()


# ── TASKS ─────────────────────────────────────────────────────────────────────

def get_tasks(active_only=True):
    conn = get_conn()
    q = "SELECT * FROM tasks" + (" WHERE is_active=1" if active_only else "") + " ORDER BY id"
    rows = conn.execute(q).fetchall()
    conn.close()
    return rows


def get_task(tid: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    conn.close()
    return row


def add_task(title, description, ttype="screenshot") -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO tasks (title, description, type) VALUES (?, ?, ?)",
        (title, description, ttype)
    )
    tid = cur.lastrowid
    conn.commit()
    conn.close()
    return tid


def update_task(tid: int, title: str, description: str):
    conn = get_conn()
    conn.execute("UPDATE tasks SET title=?, description=? WHERE id=?", (title, description, tid))
    conn.commit()
    conn.close()


def toggle_task(tid: int):
    conn = get_conn()
    conn.execute("UPDATE tasks SET is_active = 1 - is_active WHERE id=?", (tid,))
    conn.commit()
    conn.close()


def delete_task(tid: int):
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id=?", (tid,))
    conn.commit()
    conn.close()


# ── USERS ─────────────────────────────────────────────────────────────────────

def get_user(uid: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return row


def upsert_user(uid: int, username: str, full_name: str, referred_by: int = None):
    conn = get_conn()
    existing = conn.execute("SELECT user_id FROM users WHERE user_id=?", (uid,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE users SET username=?, full_name=? WHERE user_id=?",
            (username or "", full_name or "", uid)
        )
    else:
        conn.execute(
            "INSERT INTO users (user_id, username, full_name, referred_by) VALUES (?, ?, ?, ?)",
            (uid, username or "", full_name or "", referred_by)
        )
    conn.commit()
    conn.close()


def set_subscribed(uid: int):
    conn = get_conn()
    conn.execute("UPDATE users SET is_subscribed=1 WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM users ORDER BY joined_at DESC").fetchall()
    conn.close()
    return rows


# ── REFERRAL ──────────────────────────────────────────────────────────────────

def register_referral(referrer_id: int, referred_id: int) -> bool:
    """Referal bog'liqligini yaratish. True qaytarsa muvaffaqiyatli."""
    if referrer_id == referred_id:
        return False
    conn = get_conn()
    existing = conn.execute(
        "SELECT id FROM referrals WHERE referred_id=?", (referred_id,)
    ).fetchone()
    if existing:
        conn.close()
        return False
    try:
        conn.execute(
            "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
            (referrer_id, referred_id)
        )
        # Taklif qiluvchining hisobini oshirish
        bonus = int(get_setting("referral_bonus", "1"))
        conn.execute(
            "UPDATE users SET referral_count = referral_count + 1, referral_bonus = referral_bonus + ? WHERE user_id=?",
            (bonus, referrer_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Referral xato: {e}")
        conn.close()
        return False


def get_referral_stats(uid: int):
    conn = get_conn()
    referrals = conn.execute("""
        SELECT r.*, u.full_name, u.username, u.joined_at
        FROM referrals r
        JOIN users u ON r.referred_id = u.user_id
        WHERE r.referrer_id = ?
        ORDER BY r.created_at DESC
    """, (uid,)).fetchall()
    user = conn.execute("SELECT referral_count, referral_bonus FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return referrals, user


def get_top_referrers(limit=10):
    conn = get_conn()
    rows = conn.execute("""
        SELECT user_id, full_name, username, referral_count, referral_bonus
        FROM users
        WHERE referral_count > 0
        ORDER BY referral_count DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def check_referral_requirement(uid: int) -> bool:
    """Foydalanuvchi minimal referal soniga yetganini tekshirish."""
    min_count = int(get_setting("referral_min_count", "0"))
    if min_count == 0:
        return True
    conn = get_conn()
    row = conn.execute("SELECT referral_count FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return row and row["referral_count"] >= min_count


# ── SUBMISSIONS ───────────────────────────────────────────────────────────────

def add_submission(uid: int, file_id: str, task_id=None) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO submissions (user_id, file_id, task_id) VALUES (?, ?, ?)",
        (uid, file_id, task_id)
    )
    sid = cur.lastrowid
    conn.commit()
    conn.close()
    return sid


def get_pending_submissions():
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.*, u.full_name, u.username, t.title as task_title
        FROM submissions s
        JOIN users u ON s.user_id = u.user_id
        LEFT JOIN tasks t ON s.task_id = t.id
        WHERE s.status = 'pending'
        ORDER BY s.submitted_at ASC
    """).fetchall()
    conn.close()
    return rows


def review_submission(sid: int, status: str, admin_id: int, note="") -> int:
    conn = get_conn()
    row = conn.execute("SELECT user_id FROM submissions WHERE id=?", (sid,)).fetchone()
    uid = row["user_id"] if row else None
    conn.execute("""UPDATE submissions
        SET status=?, admin_note=?, reviewed_by=?, reviewed_at=? WHERE id=?
    """, (status, note, admin_id, datetime.now().isoformat(), sid))
    if uid:
        if status == "approved":
            conn.execute(
                "UPDATE users SET screenshot_status='approved', task_completed=1 WHERE user_id=?", (uid,)
            )
        else:
            conn.execute(
                "UPDATE users SET screenshot_status='rejected' WHERE user_id=?", (uid,)
            )
    conn.commit()
    conn.close()
    return uid


def get_user_submissions(uid: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM submissions WHERE user_id=? ORDER BY submitted_at DESC", (uid,)
    ).fetchall()
    conn.close()
    return rows


# ── TESTS ─────────────────────────────────────────────────────────────────────

def create_test(title, description, pass_score, time_limit, created_by) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO tests (title, description, pass_score, time_limit, created_by) VALUES (?,?,?,?,?)",
        (title, description, pass_score, time_limit, created_by)
    )
    tid = cur.lastrowid
    conn.commit()
    conn.close()
    return tid


def get_tests(active_only=True):
    conn = get_conn()
    q = "SELECT * FROM tests" + (" WHERE is_active=1" if active_only else "") + " ORDER BY created_at DESC"
    rows = conn.execute(q).fetchall()
    conn.close()
    return rows


def get_test(tid: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM tests WHERE id=?", (tid,)).fetchone()
    conn.close()
    return row


def toggle_test(tid: int):
    conn = get_conn()
    conn.execute("UPDATE tests SET is_active = 1 - is_active WHERE id=?", (tid,))
    conn.commit()
    conn.close()


def delete_test(tid: int):
    conn = get_conn()
    conn.execute("DELETE FROM questions WHERE test_id=?", (tid,))
    conn.execute("DELETE FROM tests WHERE id=?", (tid,))
    conn.commit()
    conn.close()


# ── QUESTIONS ─────────────────────────────────────────────────────────────────

def add_question(test_id, text, a, b, c, d, correct, explanation="") -> int:
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM questions WHERE test_id=?", (test_id,)).fetchone()[0]
    cur = conn.execute(
        "INSERT INTO questions (test_id,question_text,option_a,option_b,option_c,option_d,correct_answer,explanation,order_num) VALUES (?,?,?,?,?,?,?,?,?)",
        (test_id, text, a, b, c, d, correct, explanation, n + 1)
    )
    qid = cur.lastrowid
    conn.commit()
    conn.close()
    return qid


def get_questions(test_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM questions WHERE test_id=? ORDER BY order_num", (test_id,)
    ).fetchall()
    conn.close()
    return rows


def count_questions(test_id: int) -> int:
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM questions WHERE test_id=?", (test_id,)).fetchone()[0]
    conn.close()
    return n


def delete_question(qid: int):
    conn = get_conn()
    conn.execute("DELETE FROM questions WHERE id=?", (qid,))
    conn.commit()
    conn.close()


# ── TEST RESULTS ──────────────────────────────────────────────────────────────

def save_result(uid, test_id, correct, total, answers, pass_score) -> int:
    score = round(correct / total * 100) if total else 0
    passed = 1 if score >= pass_score else 0
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO test_results (user_id,test_id,score,total_questions,correct_answers,passed,answers_json) VALUES (?,?,?,?,?,?,?)",
        (uid, test_id, score, total, correct, passed, json.dumps(answers))
    )
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid


def get_user_results(uid: int):
    conn = get_conn()
    rows = conn.execute("""
        SELECT tr.*, t.title as test_title
        FROM test_results tr JOIN tests t ON tr.test_id = t.id
        WHERE tr.user_id=? ORDER BY tr.completed_at DESC
    """, (uid,)).fetchall()
    conn.close()
    return rows


def get_test_results(test_id: int):
    conn = get_conn()
    rows = conn.execute("""
        SELECT tr.*, u.full_name, u.username
        FROM test_results tr JOIN users u ON tr.user_id = u.user_id
        WHERE tr.test_id=? ORDER BY tr.score DESC
    """, (test_id,)).fetchall()
    conn.close()
    return rows


def get_stats():
    conn = get_conn()
    s = {
        "users":    conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "tests":    conn.execute("SELECT COUNT(*) FROM tests WHERE is_active=1").fetchone()[0],
        "results":  conn.execute("SELECT COUNT(*) FROM test_results").fetchone()[0],
        "pending":  conn.execute("SELECT COUNT(*) FROM submissions WHERE status='pending'").fetchone()[0],
        "tasks":    conn.execute("SELECT COUNT(*) FROM tasks WHERE is_active=1").fetchone()[0],
        "channels": conn.execute("SELECT COUNT(*) FROM channels WHERE is_active=1").fetchone()[0],
        "referrals":conn.execute("SELECT COUNT(*) FROM referrals").fetchone()[0],
    }
    conn.close()
    return s
