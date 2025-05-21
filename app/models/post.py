from sqlalchemy import Column, String, Integer
from app.core.db import Base

class Post(Base):
    __tablename__ = "posts"

    uid = Column(String, primary_key=True, index=True)
    post_url = Column(String)
    video_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    comments = Column(Integer, default=0)
    reactions = Column(Integer, default=0)
    category = Column(String)
