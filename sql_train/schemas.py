from datetime import datetime as DateTime
from sqlalchemy import (
    UniqueConstraint,
    Column,
    Integer,
    String,
    TIMESTAMP,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    posts = relationship("Post", back_populates="author")


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        Index("all_posts_user_id", "user_id"),
        # UniqueConstraint("user_id", "id", name="user_unique"),
    )
    id = Column(Integer, primary_key=True)
    body = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    create_at = Column(TIMESTAMP, default=DateTime.now())

    author = relationship("User", back_populates="posts")


class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="user_post_unique"),)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
