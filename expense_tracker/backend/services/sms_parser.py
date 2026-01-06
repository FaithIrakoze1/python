import re
from datetime import datetime
from sqlalchemy.orm import Session
from schemas import ExpenseCreate
from crud import create_expense

PATTERNS = [
    # FORMAT A: Merchant payment
    re.compile(
        r"TxId:(?P<txid>\d+)\*S\*Your payment of (?P<amount>[\d,]+) RWF to (?P<recipient>.+?) was completed at (?P<date>[\d\-: ]+)",
        re.IGNORECASE
    ),

    # FORMAT B: Person transfer
    re.compile(
        r"\*165\*S\*(?P<amount>[\d,]+) RWF transferred to (?P<recipient>.+?) at (?P<date>[\d\-: ]+)",
        re.IGNORECASE
    ),
]


def parse_momo_sms(message: str, db: Session):
    for pattern in PATTERNS:
        match = pattern.search(message)
        if not match:
            continue

        data = match.groupdict()

        amount = float(data["amount"].replace(",", ""))
        recipient = data["recipient"].strip()
        date_str = data["date"].strip()

        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            parsed_date = None  # fallback to DB default

        expense = ExpenseCreate(
            amount=amount,
            description=f"MoMo payment to {recipient}",
            category="Other"
        )

        saved = create_expense(db, expense)

        return {
            "saved": True,
            "amount": amount,
            "recipient": recipient,
            "expense_id": saved.expense_id
        }

    # If no pattern matched
    return {"ignored": True}
