from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ========================
# CATEGORY SCHEMAS
# ========================

# User creates a category: ONLY name, no ID
class CategoryCreate(BaseModel):
    name: str


# For updating a category
class CategoryUpdate(BaseModel):
    name: Optional[str] = None


# Returned to the user after creation/GET
class CategoryOut(BaseModel):
    category_id: int
    name: str

    class Config:
        from_attributes = True


# ========================
# EXPENSE SCHEMAS
# ========================

# User creates an expense: category is by NAME
class ExpenseCreate(BaseModel):
    amount: float
    description: str
    category: str   # User selects category by name


# Returned to API clients (includes category_id)
class Expense(BaseModel):
    expense_id: int
    amount: float
    description: str
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None   # Still by name


# ========================
# BUDGET SCHEMAS
# ========================

class BudgetCreate(BaseModel):
    amount: int
    month: int
    year: int
    category: str  # Again, user gives category NAME


class BudgetUpdate(BaseModel):
    amount: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None
    category: Optional[str] = None   # Name, not ID


class BudgetOut(BaseModel):
    budget_id: int
    amount: int
    month: int
    year: int
    category_id: int
    category: Optional[CategoryOut]

    class Config:
        from_attributes = True


# ========================
# SUMMARY RESPONSE
# ========================

class SummaryResponse(BaseModel):
    total_expenses: int
    year: int
    month: Optional[int] = None
    week: Optional[int] = None

    class Config:
        from_attributes = True
