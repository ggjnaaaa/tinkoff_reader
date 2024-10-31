# models.py

from servises.browser_utils import PageType

from typing import List, Optional, Dict
from pydantic import BaseModel

# 
class LoginResponse(BaseModel):
    status: str
    next_page_type: PageType | None 

    class Config:
        use_enum_values = True

class Expense(BaseModel):
    date_time: str
    card_number: str
    transaction_type: str
    amount: float
    description: str
    category: Optional[str] = None

# Модель для добавления новых категорий
class CategoryRequest(BaseModel):
    categories: List[str]

# Модель для обновления ключевых слов
class KeywordsUpdateRequest(BaseModel):
    keywords: List[Dict[str, Optional[int]]]

# Модель для удаления категорий
class DeleteCategoryRequest(BaseModel):
    ids: List[int]