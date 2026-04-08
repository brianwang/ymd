from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.models.base import Base

class OpsConfig(Base):
    __tablename__ = "ops_config"

    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False, unique=True, index=True)
    value = Column(JSON, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
