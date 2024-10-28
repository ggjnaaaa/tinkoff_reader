# models.py

from typing import List, Optional
from pydantic import BaseModel


class Expense(BaseModel):
    date_time: str
    card_number: str
    transaction_type: str
    amount: float
    description: str
    category: Optional[str] = None

class Category(BaseModel):
    id: int
    category_name: str
    keywords: Optional[List[str]] = None

class CategoryRequest(BaseModel):
    category_name: str
    keywords: Optional[List[str]] = None

class CategorySaveRequest(BaseModel):
    categories: List[str]