# src/message_board.py
import sqlite3
from typing import List, Dict, Optional
from .utils import current_timestamp

class MessageBoard:
    def __init__(self, session_id: str = "default_session", db_path: str = "database.db"):
        self.session_id = session_id
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            sender TEXT,
            content TEXT,
            tags TEXT,
            timestamp REAL
        )
        """)
        conn.close()

    def post_message(self, sender: str, content: str, tags: Optional[List[str]] = None):
        tags_str = ",".join(tags) if tags else ""
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO messages (session_id, sender, content, tags, timestamp) VALUES (?,?,?,?,?)",
                     (self.session_id, sender, content, tags_str, current_timestamp()))
        conn.commit()
        conn.close()

    def get_all_messages(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT sender, content, tags, timestamp FROM messages WHERE session_id=? ORDER BY timestamp ASC",
                    (self.session_id,))
        rows = cur.fetchall()
        conn.close()

        results = []
        for r in rows:
            sender, content, tags_str, ts = r
            tags = tags_str.split(",") if tags_str else []
            results.append({
                "sender": sender,
                "content": content,
                "tags": tags,
                "timestamp": ts
            })
        return results

    def read_messages(self, since: float = 0.0) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT sender, content, tags, timestamp FROM messages WHERE session_id=? AND timestamp>? ORDER BY timestamp ASC",
                    (self.session_id, since))
        rows = cur.fetchall()
        conn.close()

        results = []
        for r in rows:
            sender, content, tags_str, ts = r
            tags = tags_str.split(",") if tags_str else []
            results.append({
                "sender": sender,
                "content": content,
                "tags": tags,
                "timestamp": ts
            })
        return results

    def count_messages(self) -> int:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM messages WHERE session_id=?", (self.session_id,))
        (count,) = cur.fetchone()
        conn.close()
        return count
