from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    union_id = Column(String, unique=True, index=True, nullable=True)
    open_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    nickname = Column(String, index=True, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 积分
    points = Column(Integer, default=0)

    # 用户偏好位置（Preferred Location）
    preferred_location_lat = Column(Float, nullable=True)
    preferred_location_lng = Column(Float, nullable=True)
    preferred_location_display_name = Column(String, nullable=True)
    preferred_location_city = Column(String, nullable=True)
    # manual | device
    preferred_location_source = Column(String, nullable=True)
    preferred_location_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def preferred_location(self):
        """
        Convenience attribute for Pydantic `from_attributes`:
        - returns None if lat/lng missing
        - returns a dict compatible with PreferredLocation schema otherwise
        """
        if self.preferred_location_lat is None or self.preferred_location_lng is None:
            return None
        return {
            "lat": self.preferred_location_lat,
            "lng": self.preferred_location_lng,
            "display_name": self.preferred_location_display_name,
            "city": self.preferred_location_city,
            "source": self.preferred_location_source,
            "updated_at": self.preferred_location_updated_at,
        }
