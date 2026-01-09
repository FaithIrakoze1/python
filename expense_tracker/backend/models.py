from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Categories(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    # Relationships
    expenses = relationship("Expenses", back_populates="category")
    budgets = relationship("Budgets", back_populates="category")


class Expenses(Base):
    __tablename__ = "expenses"

    expense_id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, index=True)
    description = Column(String, index=True)

    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=True)
    category = relationship("Categories", back_populates="expenses")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Budgets(Base):
    __tablename__ = "budgets"

    budget_id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, index=True)
    month = Column(Integer, index=True)
    year = Column(String, index=True)

    category_id = Column(Integer, ForeignKey("categories.category_id"))
    category = relationship("Categories", back_populates="budgets")
