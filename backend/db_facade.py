from typing import List, Dict, Any, Optional
from DB_OP import get_db_mode
import native
from database import SessionLocal, Conversation, Message

class DBBackend:
    def create_conversation(self, title: str) -> int: raise NotImplementedError
    def get_conversation(self, conv_id: int) -> Optional[Dict[str, Any]]: raise NotImplementedError
    def list_conversations(self) -> List[Dict[str, Any]]: raise NotImplementedError
    def delete_conversation(self, conv_id: int) -> None: raise NotImplementedError
    def add_message(self, conv_id: int, role: str, content: str, image_base64: Optional[str] = None) -> int: raise NotImplementedError
    def get_messages(self, conv_id: int) -> List[Dict[str, Any]]: raise NotImplementedError
    def get_history_for_model(self, conv_id: int, last_n: int = 20) -> List[Dict[str, str]]: raise NotImplementedError

class ORMBackend(DBBackend):
    def create_conversation(self, title: str) -> int:
        db = SessionLocal()
        try:
            conv = Conversation(title=title)
            db.add(conv)
            db.commit()
            db.refresh(conv)
            return int(conv.id)  # type: ignore[arg-type]
        finally:
            db.close()

    def get_conversation(self, conv_id: int) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if not conv:
                return None
            return {
                "id": int(conv.id),  # type: ignore[arg-type]
                "title": conv.title,
                "created_at": conv.created_at.isoformat()
            }
        finally:
            db.close()

    def list_conversations(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            convs = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
            result: List[Dict[str, Any]] = []
            for c in convs:
                first_msg = db.query(Message).filter(
                    Message.conversation_id == c.id, Message.role == "user"
                ).first()
                if first_msg and first_msg.content:  # type: ignore[truthy-bool]
                    content: str = first_msg.content  # type: ignore[assignment]
                    title = content[:50] + "..." if len(content) > 50 else content
                else:
                    title = c.title or "Новый чат"
                result.append({
                    "id": int(c.id),  # type: ignore[arg-type]
                    "title": title,
                    "created_at": c.created_at.isoformat()
                })
            return result
        finally:
            db.close()

    def delete_conversation(self, conv_id: int) -> None:
        db = SessionLocal()
        try:
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
            if conv:
                db.delete(conv)
                db.commit()
        finally:
            db.close()

    def add_message(self, conv_id: int, role: str, content: str, image_base64: Optional[str] = None) -> int:
        db = SessionLocal()
        try:
            msg = Message(conversation_id=conv_id, role=role, content=content, image_base64=image_base64)
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return int(msg.id)  # type: ignore[arg-type]
        finally:
            db.close()

    def get_messages(self, conv_id: int) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            msgs = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.id).all()
            return [{
                "id": int(m.id),  # type: ignore[arg-type]
                "role": m.role,
                "content": m.content,
                "image_base64": m.image_base64,
                "timestamp": m.timestamp.isoformat()
            } for m in msgs]
        finally:
            db.close()

    def get_history_for_model(self, conv_id: int, last_n: int = 20) -> List[Dict[str, str]]:
        db = SessionLocal()
        try:
            history = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.id).all()
            recent = history[-last_n:] if len(history) > last_n else history
            return [{"role": msg.role, "content": str(msg.content)} for msg in recent]  # type: ignore[return-value]
        finally:
            db.close()

class NativeBackend(DBBackend):
    def create_conversation(self, title: str) -> int:
        return native.create_conversation(title)
    def get_conversation(self, conv_id: int) -> Optional[Dict[str, Any]]:
        return native.get_conversation(conv_id)
    def list_conversations(self) -> List[Dict[str, Any]]:
        return native.list_conversations()
    def delete_conversation(self, conv_id: int) -> None:
        native.delete_conversation(conv_id)
    def add_message(self, conv_id: int, role: str, content: str, image_base64: Optional[str] = None) -> int:
        return native.add_message(conv_id, role, content, image_base64)
    def get_messages(self, conv_id: int) -> List[Dict[str, Any]]:
        return native.get_messages(conv_id)
    def get_history_for_model(self, conv_id: int, last_n: int = 20) -> List[Dict[str, str]]:
        return native.get_history_for_model(conv_id, last_n)

_current_backend: Optional[DBBackend] = None

def _get_backend() -> DBBackend:
    global _current_backend
    mode = get_db_mode()
    if _current_backend is None:
        if mode == "native":
            _current_backend = NativeBackend()
        else:
            _current_backend = ORMBackend()
    else:
        if mode == "native" and not isinstance(_current_backend, NativeBackend):
            _current_backend = NativeBackend()
        elif mode == "orm" and not isinstance(_current_backend, ORMBackend):
            _current_backend = ORMBackend()
    return _current_backend

def create_conversation(title: str) -> int:
    return _get_backend().create_conversation(title)

def get_conversation(conv_id: int) -> Optional[Dict[str, Any]]:
    return _get_backend().get_conversation(conv_id)

def list_conversations() -> List[Dict[str, Any]]:
    return _get_backend().list_conversations()

def delete_conversation(conv_id: int) -> None:
    return _get_backend().delete_conversation(conv_id)

def add_message(conv_id: int, role: str, content: str, image_base64: Optional[str] = None) -> int:
    return _get_backend().add_message(conv_id, role, content, image_base64)

def get_messages(conv_id: int) -> List[Dict[str, Any]]:
    return _get_backend().get_messages(conv_id)

def get_history_for_model(conv_id: int, last_n: int = 20) -> List[Dict[str, str]]:
    return _get_backend().get_history_for_model(conv_id, last_n)