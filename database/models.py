from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Interval,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    subscription_end = Column(DateTime, nullable=True)
    registration_date = Column(DateTime, default=func.now(), nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    promo_type = Column(String, nullable=False)
    value = Column(String, nullable=False)
    max_uses = Column(BigInteger, nullable=False)


class JobDirection(Base):
    __tablename__ = "job_directions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    direction_name = Column(String, nullable=False)
    recommended_keywords = Column(String, nullable=True)


class UserJobDirection(Base):
    __tablename__ = "user_job_directions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    direction_id = Column(BigInteger, ForeignKey("job_directions.id"), nullable=False)
    selected_keywords = Column(String, nullable=True)

    user = relationship("User", backref="user_job_directions")
    direction = relationship("JobDirection", backref="user_job_directions")


class PromoCodeUsage(Base):
    __tablename__ = "promo_code_usage"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    promo_code_id = Column(BigInteger, ForeignKey("promo_codes.id"), nullable=False)
    used_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User", backref="promo_code_usages")
    promo_code = relationship("PromoCode", backref="usages")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    duration = Column(Interval, nullable=False)
    price = Column(BigInteger, nullable=False)


class BotSetting(Base):
    __tablename__ = "bot_settings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    support_message = Column(String, nullable=True)
    new_user_greeting = Column(String, nullable=True)
    registered_user_greeting = Column(String, nullable=True)
    technical_works = Column(String, nullable=True)
    message_send_interval = Column(String, nullable=True)
    check_interval = Column(String, nullable=True)
    max_requests = Column(String, nullable=True)
    request_period = Column(String, nullable=True)
    update_interval = Column(String, nullable=True)
    post_cache_duration = Column(String, nullable=True)
    message_fetch_limit = Column(String, nullable=True)


class Channel(Base):
    __tablename__ = "channels"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)


class LoadHistory(Base):
    __tablename__ = "load_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    cpu_load = Column(BigInteger, nullable=False)
    memory_load = Column(BigInteger, nullable=False)
    average_load = Column(BigInteger, nullable=False)
