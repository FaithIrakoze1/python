import re
from datetime import datetime
from sqlalchemy.orm import Session
from schemas import ExpenseCreate
from crud import create_expense
from models import Expenses

PATTERN = re.compile(
    r"TxId:(\d+).*?payment of (\d+)\s*RWF to (.+?) was completed at ([\d\-: ]+)",
    re.IGNORECASE
)

def parse_momo_sms(message: str, db: Session):
    match = PATTERN.search(message)
    if not match:
        return {"ignored": True}

    tx_id, amount, recipient, date_str = match.groups()

    # Duplicate protection
    existing = db.query(Expenses).filter(
        Expenses.description.contains(tx_id)
    ).first()

    if existing:
        return {"duplicate": True}

    parsed_date = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")

    expense = ExpenseCreate(
        amount=float(amount),
        description=f"MoMo payment to {recipient} (TxId:{tx_id})",
        category="Other"
    )

    saved = create_expense(db, expense)

    # Optional: overwrite created_at if your model allows
    saved.created_at = parsed_date
    db.commit()

    return {
        "saved": True,
        "expense_id": saved.expense_id
    }
