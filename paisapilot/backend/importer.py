import csv, io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import Account, Category, Transaction, User
from auth import get_current_user
from dsa.trie import build_default_trie

router = APIRouter()
trie = build_default_trie()
DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y")

def parse_date(s):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError("bad date")

def norm(s):
    return " ".join(s.lower().split())

@router.post("/import/csv")
async def import_csv(account_id: int, save: bool = False,
                     file: UploadFile = File(...),
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    acc = db.query(Account).filter(
        Account.id == account_id, Account.user_id == user.id).first()
    if not acc:
        raise HTTPException(404, "Account not found")

    raw = (await file.read()).decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    if not reader.fieldnames:
        raise HTTPException(400, "Empty file")
    cols = {c.strip().lower(): c for c in reader.fieldnames}
    for need in ("date", "description", "amount"):
        if need not in cols:
            raise HTTPException(400, "Missing column: " + need)

    cat_ids = {c.name: c.id for c in db.query(Category).all()}
    seen = {(t.txn_date, Decimal(t.amount), norm(t.description or ""), t.type)
            for t in db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.account_id == account_id)}

    rows, to_save = [], []
    for n, r in enumerate(reader, start=2):
        try:
            d = parse_date(r[cols["date"]].strip())
            amt = Decimal(r[cols["amount"]].replace(",", "").strip())
            if amt == 0:
                raise ValueError("zero")
        except (ValueError, InvalidOperation, AttributeError):
            rows.append({"row": n, "status": "error",
                         "reason": "Invalid date or amount"})
            continue
        ttype = "income" if amt > 0 else "expense"
        amount = abs(amt).quantize(Decimal("0.01"))
        desc = r[cols["description"]].strip()[:255]
        category = trie.categorize(desc)
        key = (d, amount, norm(desc), ttype)
        status = "duplicate" if key in seen else "new"
        if status == "new":
            seen.add(key)
            to_save.append((d, amount, desc, ttype, category))
        rows.append({"row": n, "date": str(d), "description": desc,
                     "amount": float(amount), "type": ttype,
                     "category": category, "status": status})

    if save:
        for d, amount, desc, ttype, category in to_save:
            db.add(Transaction(user_id=user.id, account_id=account_id,
                               category_id=cat_ids.get(category),
                               amount=amount, type=ttype,
                               description=desc, txn_date=d))
            acc.balance += amount if ttype == "income" else -amount
        db.commit()       # all rows and the balance saved together

    return {"saved": save,
            "new": len(to_save),
            "duplicates": sum(1 for r in rows if r["status"] == "duplicate"),
            "errors": sum(1 for r in rows if r["status"] == "error"),
            "rows": rows}