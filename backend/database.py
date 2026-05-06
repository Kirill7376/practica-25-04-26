import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

db_path = os.path.join(base_path, "chat.db")

Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default='Новый чат')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    messages = relationship('Message', back_populates='conversation', order_by='Message.id', cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    role = Column(String)
    content = Column(Text)
    image_base64 = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    conversation = relationship('Conversation', back_populates='messages')

engine = create_engine(f'sqlite:///{db_path}')
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)
