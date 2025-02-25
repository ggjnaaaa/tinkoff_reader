# models.py

from utils.tinkoff.browser_utils import PageType

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, TIMESTAMP, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import List
from datetime import datetime

Base = declarative_base()

# 
class LoginResponse(BaseModel):
    status: str
    next_page_type: PageType | None 
    current_page_type: PageType | None

    class Config:
        use_enum_values = True

class Keyword(BaseModel):
    description: str
    category_name: str

class SaveKeywordsRequest(BaseModel):
    keywords: List[Keyword]

class TokenizedUrlRequest(BaseModel):
    token: str  # Токен из ссылки


class CategoryExpenses(Base):
    __tablename__ = "category_expenses"
    id = Column(Integer, primary_key=True)
    title = Column(Text)


class CategoryKeyword(Base):
    __tablename__ = "category_expenses_keywords"
    id = Column(Integer, primary_key=True)
    keyword = Column(Text)
    category_id = Column(Integer, ForeignKey("category_expenses.id"))


# Модель для таблицы расходов
class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)
    card_number = Column(Text)
    amount = Column(Integer)
    description = Column(Text)


class TemporaryCode(Base):
    __tablename__ = 'temporary_code'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(4), nullable=False)


class LastError(Base):
    __tablename__ = "last_error"

    id = Column(Integer, primary_key=True, index=True)
    error_text = Column(String, nullable=False)
    error_time = Column(TIMESTAMP, default=datetime.utcnow)
    is_received = Column(Boolean, default=False)


class TgTmpUsers(Base):
    __tablename__ = "tg_tmp_users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chat_id = Column(BigInteger, nullable=False)

    # Связь с таблицей Users
    user = relationship("Users", backref="tmp_users")


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg = Column(Text, nullable=False)
    full_name = Column(Text, nullable=False)
    is_manager = Column(Boolean, default=False)
    is_instructor = Column(Boolean, default=False)
    is_assistant = Column(Boolean, default=False)
    send_button = Column(Boolean, default=False)
    deposit_income = Column(Boolean, default=False)
    enter_operation = Column(Boolean, default=False)
    view_salary = Column(Boolean, default=False)
    contribute_expense = Column(Boolean, default=False)
    is_director = Column(Boolean, default=False)
    chat_id = Column(BigInteger, nullable=True)
    comission = Column(Boolean, default=False)
    penalty = Column(Boolean, default=False)
    is_investor = Column(Boolean, default=False)
    change_salary = Column(Boolean, default=False)
    card_number = Column(Text)


class UserNotifications(Base):
    __tablename__ = "user_notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    receive_error_notifications = Column(Boolean, default=False)
    receive_transfer_notifications = Column(Boolean, default=False)

    # Связь с таблицей Users
    user = relationship("Users", backref="notifications")