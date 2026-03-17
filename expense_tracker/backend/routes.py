from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

import crud as crud
import schemas
from auth import get_current_user
from database import get_db
from services.sms_parser import parse_momo_sms

router = APIRouter()


def _auth_context(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Dependency: require valid JWT and provide db session plus authenticated user."""
    return {"db": db, "user": user}


# ============================================
# CATEGORY ROUTES
# ============================================

@router.post("/categories", response_model=schemas.CategoryOut)
def create_category(category: schemas.CategoryCreate, ctx: dict = Depends(_auth_context)):
    return crud.create_category(ctx["db"], ctx["user"]["user_id"], category)


@router.get("/categories", response_model=list[schemas.CategoryOut])
def get_categories(ctx: dict = Depends(_auth_context)):
    return crud.get_categories(ctx["db"], ctx["user"]["user_id"])


# ============================================
# EXPENSE ROUTES
# ============================================

@router.post("/expenses", response_model=schemas.Expense)
def create_expense(expense: schemas.ExpenseCreate, ctx: dict = Depends(_auth_context)):
    try:
        return crud.create_expense(ctx["db"], ctx["user"]["user_id"], expense)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/expenses")
def get_expenses(
    category: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    ctx: dict = Depends(_auth_context),
):
    return crud.get_expenses(
        ctx["db"],
        ctx["user"]["user_id"],
        category=category,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/expenses/{expense_id}", response_model=schemas.Expense)
def get_expense(expense_id: int, ctx: dict = Depends(_auth_context)):
    expense = crud.get_expense(ctx["db"], ctx["user"]["user_id"], expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, ctx: dict = Depends(_auth_context)):
    success = crud.delete_expense(ctx["db"], ctx["user"]["user_id"], expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"deleted": True, "expense_id": expense_id}


# ============================================
# BUDGET ROUTES
# ============================================

@router.post("/budgets", response_model=schemas.BudgetOut)
def create_budget(budget: schemas.BudgetCreate, ctx: dict = Depends(_auth_context)):
    try:
        return crud.create_budget(ctx["db"], ctx["user"]["user_id"], budget)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/budgets", response_model=list[schemas.BudgetOut])
def get_budgets(ctx: dict = Depends(_auth_context)):
    return crud.get_budgets(ctx["db"], ctx["user"]["user_id"])


# ============================================
# SMS ROUTE
# ============================================

class SMSPayload(BaseModel):
    message: str


@router.post("/sms/incoming")
def receive_sms(payload: SMSPayload, ctx: dict = Depends(_auth_context)):
    return parse_momo_sms(payload.message, ctx["db"], ctx["user"]["user_id"])
