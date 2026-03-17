import re
from datetime import datetime

from sqlalchemy.orm import Session

from crud import create_expense
from schemas import ExpenseCreate

PATTERNS = [
    re.compile(
        r"TxId:(?P<txid>\d+)\*S\*Your payment of (?P<amount>[\d,]+) RWF to (?P<recipient>.+?) was completed at (?P<date>[\d\-: ]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\*165\*S\*(?P<amount>[\d,]+) RWF transferred to (?P<recipient>.+?) at (?P<date>[\d\-: ]+)",
        re.IGNORECASE,
    ),
]


def parse_momo_sms(message: str, db: Session, user_id: int):
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
            parsed_date = None

        expense = ExpenseCreate(
            amount=amount,
            description=f"MoMo payment to {recipient}",
            category="Other",
            date=parsed_date.date() if parsed_date else None,
        )

        saved = create_expense(db, user_id, expense)

        return {
            "saved": True,
            "amount": amount,
            "recipient": recipient,
            "expense_id": saved.expense_id,
        }

    return {"ignored": True}
