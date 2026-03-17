from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas


# =========================
# USER (AUTH)
# =========================

def get_user_by_google_sub(db: Session, google_sub: str):
    return db.query(models.User).filter(models.User.google_sub == google_sub).first()


def get_or_create_user_by_google_sub(
    db: Session,
    google_sub: str,
    email: str,
    name: str | None = None,
):
    """
    Fetch existing user by Google 'sub' or create a new user.
    Keeps email/name in sync when they change.
    """
    user = get_user_by_google_sub(db, google_sub)
    if user:
        updated = False
        if email and user.email != email:
            user.email = email
            updated = True
        if name is not None and user.name != name:
            user.name = name
            updated = True
        if updated:
            db.commit()
            db.refresh(user)
        return user

    user = models.User(google_sub=google_sub, email=email, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# =========================
# CATEGORY
# =========================

def create_category(db: Session, user_id: int, category: schemas.CategoryCreate):
    existing_category = get_category_by_name(db, user_id, category.name)
    if existing_category:
        return existing_category

    new_category = models.Categories(**category.dict(), user_id=user_id)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


def get_categories(db: Session, user_id: int):
    return db.query(models.Categories).filter(models.Categories.user_id == user_id).all()


def get_category(db: Session, user_id: int, category_id: int):
    return db.query(models.Categories).filter(
        models.Categories.category_id == category_id,
        models.Categories.user_id == user_id,
    ).first()


def get_category_by_name(db: Session, user_id: int, name: str):
    return db.query(models.Categories).filter(
        models.Categories.name == name,
        models.Categories.user_id == user_id,
    ).first()


def update_category(db: Session, user_id: int, category_id: int, category: schemas.CategoryUpdate):
    db_category = get_category(db, user_id, category_id)
    if not db_category:
        return None

    for key, value in category.dict(exclude_unset=True).items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, user_id: int, category_id: int):
    db_category = get_category(db, user_id, category_id)
    if not db_category:
        return None

    db.delete(db_category)
    db.commit()
    return True


# =========================
# EXPENSE
# =========================

def create_expense(db: Session, user_id: int, expense: schemas.ExpenseCreate):
    db_category = None

    if expense.category:
        db_category = get_category_by_name(db, user_id, expense.category)
        if not db_category:
            raise HTTPException(status_code=400, detail="Category does not exist")

    new_expense = models.Expenses(
        amount=expense.amount,
        description=expense.description,
        user_id=user_id,
        category_id=db_category.category_id if db_category else None,
        created_at=expense.date or datetime.utcnow(),
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


def get_expenses(
    db: Session,
    user_id: int,
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
):
    query = db.query(models.Expenses).filter(models.Expenses.user_id == user_id)

    if category:
        query = query.join(models.Categories).filter(
            models.Categories.name == category,
            models.Categories.user_id == user_id,
        )

    if start_date:
        start_dt = datetime.combine(start_date, datetime.min.time())
        query = query.filter(models.Expenses.created_at >= start_dt)

    if end_date:
        end_dt = datetime.combine(end_date, datetime.max.time())
        query = query.filter(models.Expenses.created_at <= end_dt)

    return query.order_by(models.Expenses.created_at.desc()).all()


def get_expense(db: Session, user_id: int, expense_id: int):
    return db.query(models.Expenses).filter(
        models.Expenses.expense_id == expense_id,
        models.Expenses.user_id == user_id,
    ).first()


def update_expense(db: Session, user_id: int, expense_id: int, expense: schemas.ExpenseUpdate):
    db_expense = get_expense(db, user_id, expense_id)
    if not db_expense:
        return None

    update_data = expense.dict(exclude_unset=True)

    if "category" in update_data:
        db_category = get_category_by_name(db, user_id, update_data["category"])
        if not db_category:
            raise ValueError("Category does not exist")
        db_expense.category_id = db_category.category_id
        del update_data["category"]

    for key, value in update_data.items():
        setattr(db_expense, key, value)

    db.commit()
    db.refresh(db_expense)
    return db_expense


def delete_expense(db: Session, user_id: int, expense_id: int):
    db_expense = get_expense(db, user_id, expense_id)
    if not db_expense:
        return None

    db.delete(db_expense)
    db.commit()
    return True


# =========================
# BUDGET
# =========================

def create_budget(db: Session, user_id: int, budget: schemas.BudgetCreate):
    db_category = get_category_by_name(db, user_id, budget.category)
    if not db_category:
        raise ValueError("Category does not exist")

    new_budget = models.Budgets(
        amount=budget.amount,
        month=budget.month,
        year=budget.year,
        user_id=user_id,
        category_id=db_category.category_id,
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


def get_budgets(db: Session, user_id: int):
    return db.query(models.Budgets).filter(models.Budgets.user_id == user_id).all()


def get_budget(db: Session, user_id: int, budget_id: int):
    return db.query(models.Budgets).filter(
        models.Budgets.budget_id == budget_id,
        models.Budgets.user_id == user_id,
    ).first()


def update_budget(db: Session, user_id: int, budget_id: int, budget: schemas.BudgetUpdate):
    db_budget = get_budget(db, user_id, budget_id)
    if not db_budget:
        return None

    update_data = budget.dict(exclude_unset=True)

    if "category" in update_data:
        db_category = get_category_by_name(db, user_id, update_data["category"])
        if not db_category:
            raise ValueError("Category does not exist")
        db_budget.category_id = db_category.category_id
        del update_data["category"]

    for key, value in update_data.items():
        setattr(db_budget, key, value)

    db.commit()
    db.refresh(db_budget)
    return db_budget


def delete_budget(db: Session, user_id: int, budget_id: int):
    db_budget = get_budget(db, user_id, budget_id)
    if not db_budget:
        return None

    db.delete(db_budget)
    db.commit()
    return True


# =========================
# SUMMARY
# =========================

def get_monthly_summary(db: Session, user_id: int, year: int, month: int):
    start = datetime(year, month, 1)
    end = datetime(year + (month // 12), (month % 12) + 1, 1)

    total = db.query(func.sum(models.Expenses.amount)) \
        .filter(
            models.Expenses.user_id == user_id,
            models.Expenses.created_at >= start,
            models.Expenses.created_at < end,
        ) \
        .scalar()

    return {"year": year, "month": month, "total_expenses": total or 0}


def get_yearly_summary(db: Session, user_id: int, year: int):
    start = datetime(year, 1, 1)
    end = datetime(year + 1, 1, 1)

    total = db.query(func.sum(models.Expenses.amount)) \
        .filter(
            models.Expenses.user_id == user_id,
            models.Expenses.created_at >= start,
            models.Expenses.created_at < end,
        ) \
        .scalar()

    return {"year": year, "total_expenses": total or 0}


def get_weekly_summary(db: Session, user_id: int, year: int, week: int):
    start = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
    end = start + timedelta(days=7)

    total = db.query(func.sum(models.Expenses.amount)) \
        .filter(
            models.Expenses.user_id == user_id,
            models.Expenses.created_at >= start,
            models.Expenses.created_at < end,
        ) \
        .scalar()

    return {"year": year, "week": week, "total_expenses": total or 0}
