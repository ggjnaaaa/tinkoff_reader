# models.py

from utils.tinkoff.browser_utils import PageType

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, TIMESTAMP
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