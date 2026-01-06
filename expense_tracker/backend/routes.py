from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from datetime import date
from database import get_db
from services.sms_parser import parse_momo_sms
from pydantic import BaseModel
import crud as crud, schemas

router = APIRouter()

# ============================================
# CATEGORY ROUTES
# ============================================

@router.post("/categories", response_model=schemas.CategoryOut)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db, category)


@router.get("/categories", response_model=list[schemas.CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)


# ============================================
# EXPENSE ROUTES
# ============================================

@router.post("/expenses", response_model=schemas.Expense)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_expense(db, expense)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/expenses")
def get_expenses(
    category: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db)
):
    return crud.get_expenses(
        db,
        category=category,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/expenses/{expense_id}", response_model=schemas.Expense)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = crud.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    success = crud.delete_expense(db, expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"deleted": True, "expense_id": expense_id}


# ============================================
# BUDGET ROUTES
# ============================================

@router.post("/budgets", response_model=schemas.BudgetOut)
def create_budget(budget: schemas.BudgetCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_budget(db, budget)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/budgets", response_model=list[schemas.BudgetOut])
def get_budgets(db: Session = Depends(get_db)):
    return crud.get_budgets(db)

# ============================================
# SMS ROUTE
# ============================================

class SMSPayload(BaseModel):
    message: str

@router.post("/sms/incoming")
def receive_sms(payload: SMSPayload, db: Session = Depends(get_db)):
    return parse_momo_sms(payload.message, db)

