from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(50), nullable=True)
    status = Column(String(20), default="draft")
    stock = Column(Integer, default=0)
    tags = Column(JSON, default=[])
    images = Column(JSON, default=[])
    attributes = Column(JSON, default={})
    view_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    owner = relationship("User", backref="items")

    def __repr__(self):
        return f"<Item {self.title}>"