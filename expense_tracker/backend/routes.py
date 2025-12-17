from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
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

@router.post("/api/expenses", response_model=schemas.Expense)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_expense(db, expense)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/api/expenses", response_model=list[schemas.Expense])
def get_expenses(db: Session = Depends(get_db)):
    return crud.get_expenses(db)


@router.get("/api/expenses/{expense_id}", response_model=schemas.Expense)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = crud.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


# ============================================
# BUDGET ROUTES
# ============================================

@router.post("/api/budgets", response_model=schemas.BudgetOut)
def create_budget(budget: schemas.BudgetCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_budget(db, budget)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/api/budgets", response_model=list[schemas.BudgetOut])
def get_budgets(db: Session = Depends(get_db)):
    return crud.get_budgets(db)


# ============================================
# SUMMARY ROUTES
# ============================================

@router.get("/api/summary/monthly")
def monthly_summary(year: int, month: int, db: Session = Depends(get_db)):
    return crud.get_monthly_summary(db, year, month)


@router.get("/api/summary/yearly")
def yearly_summary(year: int, db: Session = Depends(get_db)):
    return crud.get_yearly_summary(db, year)


@router.get("/api/summary/weekly")
def weekly_summary(year: int, week: int, db: Session = Depends(get_db)):
    return crud.get_weekly_summary(db, year, week)
