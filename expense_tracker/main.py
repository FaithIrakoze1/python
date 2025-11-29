from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import json
import os

app = FastAPI(title="Expense Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "expenses.json"

class Category(str, Enum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    OTHER = "Other"

class ExpenseCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Expense amount (must be positive)")
    category: Category
    description: str = Field(..., min_length=1, max_length=200)
    date: Optional[str] = None

class Expense(ExpenseCreate):
    id: int
    date: str

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[Category] = None
    description: Optional[str] = Field(None, min_length=1, max_length=200)
    date: Optional[str] = None

def load_expenses()  -> List[dict]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_expenses(expenses: List[dict]):
    with open(DATA_FILE, 'w') as f:
        json.dump(expenses, f, indent=2)

def get_next_id(expenses: List[dict]) -> int:
    return max([e['id'] for e in expenses], default=0) + 1

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/api/expenses", response_model=List[Expense])
async def get_expenses(category: Optional[Category] = None):
    expenses = load_expenses()
    if category:
        expenses = [e for e in expenses if e['category'] == category]
    return expenses

@app.get("/api/expenses/{expense_id}", response_model=Expense)
async def get_expense(expense_id: int):
    expenses = load_expenses()
    expense = next((e for e in expenses if e['id'] == expense_id), None)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@app.post("/api/expenses", response_model=Expense, status_code=201)
async def create_expense(expense: ExpenseCreate):
    expenses = load_expenses()
    new_expense = expense.dict()
    new_expense['id'] = get_next_id(expenses)
    new_expense['date'] = expense.date
    expenses.append(new_expense)
    save_expenses(expenses)
    return new_expense

@app.put("/api/expenses/{expense_id}", response_model=Expense)
async def update_expense(expense_id: int, expense_update: ExpenseUpdate):
    expenses = load_expenses()
    expense_idx = next((i for i, e in enumerate(expenses) if e['id'] == expense_id), None)

    if expense_idx is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    update_data = expense_update.dict(exclude_unset=True)
    expenses[expense_idx].update(update_data)
    save_expenses(expenses)
    return expenses[expense_idx]

@app.delete("/api/expenses/{expense_id}")
async def delete_expense(expense_id: int):
    expenses = load_expenses()
    expense_idx = next((i for i, e in enumerate(expenses) if e['id'] == expense_id), None)

    if expense_idx is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    deleted = expenses.pop(expense_idx)
    save_expenses(expenses)
    return {"message": "Expense deleted successfully", "expense": deleted}

@app.get("/api/summary")
async def get_summary():
    expenses = load_expenses()

    if not expenses:
        return {"total": 0, "by_category": {}, "count": 0}

    total = sum(e['amount'] for e in expenses)
    by_category = {}

    for expense in expenses:
        category = expense['category']
        by_category[category] = by_category.get(category, 0) + expense['amount']

    return {
        "total": round(total, 2),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "count": len(expenses)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.1", port=8000)
