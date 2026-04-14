import sqlite3
import os
from datetime import datetime
import pytz

DB_PATH = os.environ.get("DB_PATH", "habits.db")
ITALIAN_TZ = pytz.timezone("Europe/Rome")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            timeframe TEXT NOT NULL DEFAULT 'daily',
            created_at TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            label TEXT NOT NULL,
            counter_target INTEGER DEFAULT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            value INTEGER NOT NULL DEFAULT 0,
            period_key TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(item_id, user_id, period_key),
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            period_key TEXT NOT NULL,
            completed_items INTEGER NOT NULL DEFAULT 0,
            total_items INTEGER NOT NULL DEFAULT 0,
            saved_at TEXT NOT NULL,
            UNIQUE(user_id, activity_id, period_key)
        )
    """)

    conn.commit()
    conn.close()

def now_italian():
    return datetime.now(ITALIAN_TZ)

def get_period_key(timeframe: str) -> str:
    now = now_italian()
    if timeframe == "daily":
        return now.strftime("%Y-%m-%d")
    elif timeframe == "weekly":
        return f"{now.year}-W{now.strftime('%W')}"
    elif timeframe == "monthly":
        return now.strftime("%Y-%m")
    return now.strftime("%Y-%m-%d")

# ── Activities ──────────────────────────────────────────────────────────────

def get_activities(user_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM activities WHERE user_id=? ORDER BY position, id",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows

def create_activity(user_id: int, name: str, timeframe: str = "daily") -> int:
    conn = get_conn()
    c = conn.cursor()
    pos = (conn.execute("SELECT COALESCE(MAX(position),0) FROM activities WHERE user_id=?", (user_id,)).fetchone()[0] or 0) + 1
    c.execute(
        "INSERT INTO activities (user_id, name, timeframe, created_at, position) VALUES (?,?,?,?,?)",
        (user_id, name, timeframe, now_italian().isoformat(), pos)
    )
    act_id = c.lastrowid
    conn.commit()
    conn.close()
    return act_id

def get_activity(activity_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM activities WHERE id=?", (activity_id,)).fetchone()
    conn.close()
    return row

def delete_activity(activity_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM activities WHERE id=?", (activity_id,))
    conn.commit()
    conn.close()

def update_activity_timeframe(activity_id: int, timeframe: str):
    conn = get_conn()
    conn.execute("UPDATE activities SET timeframe=? WHERE id=?", (timeframe, activity_id))
    conn.commit()
    conn.close()

# ── Items ────────────────────────────────────────────────────────────────────

def get_items(activity_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM items WHERE activity_id=? ORDER BY position, id",
        (activity_id,)
    ).fetchall()
    conn.close()
    return rows

def add_item(activity_id: int, item_type: str, label: str, counter_target: int = None) -> int:
    conn = get_conn()
    c = conn.cursor()
    pos = (conn.execute("SELECT COALESCE(MAX(position),0) FROM items WHERE activity_id=?", (activity_id,)).fetchone()[0] or 0) + 1
    c.execute(
        "INSERT INTO items (activity_id, type, label, counter_target, position) VALUES (?,?,?,?,?)",
        (activity_id, item_type, label, counter_target, pos)
    )
    item_id = c.lastrowid
    conn.commit()
    conn.close()
    return item_id

def delete_item(item_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

# ── Completions ──────────────────────────────────────────────────────────────

def get_completion(item_id: int, user_id: int, period_key: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM completions WHERE item_id=? AND user_id=? AND period_key=?",
        (item_id, user_id, period_key)
    ).fetchone()
    conn.close()
    return row

def set_completion(item_id: int, user_id: int, period_key: str, value: int):
    conn = get_conn()
    conn.execute(
        """INSERT INTO completions (item_id, user_id, period_key, value, updated_at)
           VALUES (?,?,?,?,?)
           ON CONFLICT(item_id, user_id, period_key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
        (item_id, user_id, period_key, value, now_italian().isoformat())
    )
    conn.commit()
    conn.close()

def get_activity_completion_rate(activity_id: int, user_id: int, period_key: str) -> tuple:
    """Returns (completed_items, total_items)"""
    items = get_items(activity_id)
    if not items:
        return 0, 0
    completed = 0
    for item in items:
        comp = get_completion(item["id"], user_id, period_key)
        val = comp["value"] if comp else 0
        if item["type"] == "checkbox" and val == 1:
            completed += 1
        elif item["type"] == "counter" and item["counter_target"] and val >= item["counter_target"]:
            completed += 1
    return completed, len(items)

def save_snapshot(user_id: int, activity_id: int, period_key: str):
    comp, total = get_activity_completion_rate(activity_id, user_id, period_key)
    conn = get_conn()
    conn.execute(
        """INSERT INTO daily_snapshots (user_id, activity_id, period_key, completed_items, total_items, saved_at)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT(user_id, activity_id, period_key) DO UPDATE SET completed_items=excluded.completed_items, total_items=excluded.total_items, saved_at=excluded.saved_at""",
        (user_id, activity_id, period_key, comp, total, now_italian().isoformat())
    )
    conn.commit()
    conn.close()

# ── Stats ────────────────────────────────────────────────────────────────────

def get_history(user_id: int, activity_id: int, limit: int = 60):
    conn = get_conn()
    rows = conn.execute(
        """SELECT period_key, completed_items, total_items FROM daily_snapshots
           WHERE user_id=? AND activity_id=?
           ORDER BY period_key DESC LIMIT ?""",
        (user_id, activity_id, limit)
    ).fetchall()
    conn.close()
    return rows

def get_streak(user_id: int, activity_id: int) -> int:
    from datetime import timedelta
    rows = get_history(user_id, activity_id, limit=365)
    if not rows:
        return 0
    streak = 0
    today = now_italian().date()
    check_date = today
    history_map = {r["period_key"]: r for r in rows}
    for _ in range(365):
        key = check_date.strftime("%Y-%m-%d")
        if key in history_map and history_map[key]["total_items"] > 0:
            rate = history_map[key]["completed_items"] / history_map[key]["total_items"]
            if rate >= 1.0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        else:
            if check_date == today:
                check_date -= timedelta(days=1)
                continue
            break
    return streak

def get_all_user_ids():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT user_id FROM activities").fetchall()
    conn.close()
    return [r["user_id"] for r in rows]
