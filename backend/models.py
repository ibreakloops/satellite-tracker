# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
import datetime

class Satellite(Base):
    __tablename__ = "satellites"

    id = Column(Integer, primary_key=True, index=True)
    norad_id = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    line1 = Column(String)
    line2 = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)