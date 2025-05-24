pythonfrom sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func

from app.db.base import Base

class Setting(Base):
    __tablename__ = "settings"

    id = Column(String, primary_key=True, index=True)  # مثال: SET-12345
    key = Column(String, unique=True, index=True)
    value = Column(Text)
    description = Column(Text, nullable=True)
    category = Column(String, default="general")  # دسته‌بندی تنظیمات (عمومی، سیستم و...)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())