from sqlalchemy import Column, ForeignKey, Integer, String
from database import Base

class Categories(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

class Expenses(Base):
    __tablename__ = "expenses"

    expense_id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, index=True)
    description = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"))

class Budgets(Base):
    __tablename__ = "budgets"

    budget_id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, index=True)
    month = Column(String, index=True)
    year = Column(String, index=True)

