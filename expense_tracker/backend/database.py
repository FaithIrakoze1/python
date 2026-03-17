import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "env" / ".env"

load_dotenv(dotenv_path=ENV_PATH)

db_url = os.getenv("DATABASE_URL")
if db_url is None:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_user_scoping_columns()


def ensure_user_scoping_columns():
    inspector = inspect(engine)
    scoped_tables = ("categories", "expenses", "budgets")

    with engine.begin() as connection:
        for table_name in scoped_tables:
            columns = {column["name"] for column in inspector.get_columns(table_name)}
            if "user_id" in columns:
                continue
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN user_id INTEGER"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
