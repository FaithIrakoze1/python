from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    google_sub = Column(String, unique=True, index=True)  # Google's stable user ID
    email = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)

    expenses = relationship("Expenses", back_populates="user")
    budgets = relationship("Budgets", back_populates="user")
    categories = relationship("Categories", back_populates="user")


class Categories(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)

    user = relationship("User", back_populates="categories")
    expenses = relationship("Expenses", back_populates="category")
    budgets = relationship("Budgets", back_populates="category")


class Expenses(Base):
    __tablename__ = "expenses"

    expense_id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, index=True)
    description = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)

    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=True)
    user = relationship("User", back_populates="expenses")
    category = relationship("Categories", back_populates="expenses")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Budgets(Base):
    __tablename__ = "budgets"

    budget_id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, index=True)
    month = Column(Integer, index=True)
    year = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)

    category_id = Column(Integer, ForeignKey("categories.category_id"))
    user = relationship("User", back_populates="budgets")
    category = relationship("Categories", back_populates="budgets")
