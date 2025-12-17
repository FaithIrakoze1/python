from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import models
import schemas


# =========================
# CATEGORY
# =========================

def create_category(db: Session, category: schemas.CategoryCreate):
    new_category = models.Categories(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


def get_categories(db: Session):
    return db.query(models.Categories).all()


def get_category(db: Session, category_id: int):
    return db.query(models.Categories).filter(models.Categories.category_id == category_id).first()


def get_category_by_name(db: Session, name: str):
    return db.query(models.Categories).filter(models.Categories.name == name).first()


def update_category(db: Session, category_id: int, category: schemas.CategoryUpdate):
    db_category = get_category(db, category_id)
    if not db_category:
        return None

    for key, value in category.dict(exclude_unset=True).items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id)
    if not db_category:
        return None

    db.delete(db_category)
    db.commit()
    return True


# =========================
# EXPENSE
# =========================

def create_expense(db: Session, expense: schemas.ExpenseCreate):
    # Category lookup by name
    db_category = get_category_by_name(db, expense.category)
    if not db_category:
        raise ValueError("Category does not exist")

    new_expense = models.Expenses(
        amount=expense.amount,
        description=expense.description,
        category_id=db_category.category_id,
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


def get_expenses(db: Session):
    return db.query(models.Expenses).all()


def get_expense(db: Session, expense_id: int):
    return db.query(models.Expenses).filter(models.Expenses.expense_id == expense_id).first()


def update_expense(db: Session, expense_id: int, expense: schemas.ExpenseUpdate):
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        return None

    update_data = expense.dict(exclude_unset=True)

    # If category name was given, convert to category_id
    if "category" in update_data:
        db_category = get_category_by_name(db, update_data["category"])
        if not db_category:
            raise ValueError("Category does not exist")
        db_expense.category_id = db_category.category_id
        del update_data["category"]

    # Update other fields
    for key, value in update_data.items():
        setattr(db_expense, key, value)

    db.commit()
    db.refresh(db_expense)
    return db_expense


def delete_expense(db: Session, expense_id: int):
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        return None

    db.delete(db_expense)
    db.commit()
    return True


# =========================
# BUDGET
# =========================

def create_budget(db: Session, budget: schemas.BudgetCreate):
    # Convert category name → category_id
    db_category = get_category_by_name(db, budget.category)
    if not db_category:
        raise ValueError("Category does not exist")

    new_budget = models.Budgets(
        amount=budget.amount,
        month=budget.month,
        year=budget.year,
        category_id=db_category.category_id
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


def get_budgets(db: Session):
    return db.query(models.Budgets).all()


def get_budget(db: Session, budget_id: int):
    return db.query(models.Budgets).filter(models.Budgets.budget_id == budget_id).first()


def update_budget(db: Session, budget_id: int, budget: schemas.BudgetUpdate):
    db_budget = get_budget(db, budget_id)
    if not db_budget:
        return None

    update_data = budget.dict(exclude_unset=True)

    # If category name is updated
    if "category" in update_data:
        db_category = get_category_by_name(db, update_data["category"])
        if not db_category:
            raise ValueError("Category does not exist")
        db_budget.category_id = db_category.category_id
        del update_data["category"]

    for key, value in update_data.items():
        setattr(db_budget, key, value)

    db.commit()
    db.refresh(db_budget)
    return db_budget


def delete_budget(db: Session, budget_id: int):
    db_budget = get_budget(db, budget_id)
    if not db_budget:
        return None

    db.delete(db_budget)
    db.commit()
    return True


# =========================
# SUMMARY
# =========================

def get_monthly_summary(db: Session, year: int, month: int):
    start = datetime(year, month, 1)
    end = datetime(year + (month // 12), (month % 12) + 1, 1)

    total = db.query(func.sum(models.Expenses.amount))\
        .filter(models.Expenses.created_at >= start,
                models.Expenses.created_at < end)\
        .scalar()

    return {"year": year, "month": month, "total_expenses": total or 0}


def get_yearly_summary(db: Session, year: int):
    start = datetime(year, 1, 1)
    end = datetime(year + 1, 1, 1)

    total = db.query(func.sum(models.Expenses.amount))\
        .filter(models.Expenses.created_at >= start,
                models.Expenses.created_at < end)\
        .scalar()

    return {"year": year, "total_expenses": total or 0}


def get_weekly_summary(db: Session, year: int, week: int):
    start = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
    end = start + timedelta(days=7)

    total = db.query(func.sum(models.Expenses.amount))\
        .filter(models.Expenses.created_at >= start,
                models.Expenses.created_at < end)\
        .scalar()

    return {"year": year, "week": week, "total_expenses": total or 0}
