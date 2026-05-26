import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "chat.db")

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_conversation(title: str) -> int:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (title, created_at) VALUES (?, ?)",
            (title, datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        last_id = cursor.lastrowid
        if last_id is None:
            raise RuntimeError("Failed to insert conversation")
        return last_id

def get_conversation(conv_id: int) -> Optional[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, created_at FROM conversations WHERE id = ?", (conv_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def list_conversations() -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, created_at FROM conversations ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

def delete_conversation(conv_id: int) -> None:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        conn.commit()

def add_message(conv_id: int, role: str, content: str, image_base64: Optional[str] = None) -> int:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content, image_base64, timestamp) VALUES (?, ?, ?, ?, ?)",
            (conv_id, role, content, image_base64, datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        last_id = cursor.lastrowid
        if last_id is None:
            raise RuntimeError("Failed to insert message")
        return last_id

def get_messages(conv_id: int) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, role, content, image_base64, timestamp FROM messages WHERE conversation_id = ? ORDER BY id",
            (conv_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def get_last_n_messages(conv_id: int, last_n: int = 20) -> List[Dict[str, Any]]:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
            (conv_id, last_n)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in reversed(rows)]

def get_history_for_model(conv_id: int, last_n: int = 20) -> List[Dict[str, str]]:
    rows = get_last_n_messages(conv_id, last_n)
    return [{"role": row["role"], "content": row["content"]} for row in rows]