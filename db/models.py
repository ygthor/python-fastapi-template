from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Date, DateTime
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(100))

    # ✅ Relationships
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    api_usage_logs = relationship("ApiUsage", back_populates="user", cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    receipt_scans = Column(Integer, default=0)
    invoice_scans = Column(Integer, default=0)
    any_scans = Column(Integer, default=0)

    user_subscriptions = relationship("UserSubscription", back_populates="subscription", cascade="all, delete-orphan")


class UserSubscription(Base):
    __tablename__ = "user_subscription"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)

    amount = Column(Float, nullable=True)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    subscribed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")
    subscription = relationship("Subscription", back_populates="user_subscriptions")


class ApiUsage(Base):
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    period = Column(String(7), nullable=False)  # Format: "YYYY-MM"

    receipt_scans = Column(Integer, default=0)
    invoice_scans = Column(Integer, default=0)
    any_scans = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="api_usage_logs")


class ApiCallLog(Base):
    __tablename__ = "api_call_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    endpoint = Column(String(255), nullable=False)
    request_time = Column(DateTime, default=datetime.utcnow)
