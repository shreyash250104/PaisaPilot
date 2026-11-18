from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from database import get_db
from models import Category, Transaction, User
from auth import get_current_user
from budgets import month_range
from dsa.heap_utils import top_n
from dsa.trends import moving_average, is_unusual

router = APIRouter()
MONTH = r"^\d{4}-(0[1-9]|1[0-2])$"

def f(x):
    return float(x or 0)

@router.get("/reports/summary")
def summary(month: Optional[str] = Query(None, pattern=MONTH),
            db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    month = month or date.today().strftime("%Y-%m")
    start, end = month_range(month)
    base = [Transaction.user_id == user.id,
            Transaction.txn_date >= start, Transaction.txn_date < end]
    income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        *base, Transaction.type == "income").scalar()
    rows = (db.query(Category.name, func.sum(Transaction.amount))
            .select_from(Transaction)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .filter(*base, Transaction.type == "expense")
            .group_by(Category.name)
            .order_by(func.sum(Transaction.amount).desc()).all())
    expense = sum((a for _, a in rows), 0)
    return {"month": month, "income": f(income), "expense": f(expense),
            "savings": f(income) - f(expense),
            "categories": [{"category": name or "Uncategorized",
                            "total": f(a),
                            "percent": round(f(a) / f(expense) * 100, 1) if expense else 0}
                           for name, a in rows]}

@router.get("/reports/trend")
def trend(months: int = Query(6, ge=1, le=24),
          db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    rows = db.execute(text("""
        SELECT month_year, income, expense,
               LAG(expense) OVER (ORDER BY month_year) AS prev_expense
        FROM v_monthly_totals
        WHERE user_id = :uid
        ORDER BY month_year"""), {"uid": user.id}).mappings().all()
    out = []
    for r in rows:
        prev = f(r["prev_expense"])
        change = round((f(r["expense"]) - prev) / prev * 100, 1) if prev > 0 else None
        out.append({"month": r["month_year"], "income": f(r["income"]),
                    "expense": f(r["expense"]),
                    "savings": f(r["income"]) - f(r["expense"]),
                    "change_vs_previous_month_percent": change})
    return out[-months:]

@router.get("/reports/top-expenses")
def top_expenses(month: Optional[str] = Query(None, pattern=MONTH),
                 n: int = Query(5, ge=1, le=50),
                 db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    month = month or date.today().strftime("%Y-%m")
    start, end = month_range(month)
    rows = (db.query(Transaction, Category.name)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .filter(Transaction.user_id == user.id, Transaction.type == "expense",
                    Transaction.txn_date >= start, Transaction.txn_date < end).all())
    best = top_n(rows, n, key=lambda r: r[0].amount)
    return {"month": month,
            "top": [{"id": t.id, "date": str(t.txn_date),
                     "description": t.description,
                     "category": name or "Uncategorized",
                     "amount": f(t.amount)} for t, name in best]}

@router.get("/reports/forecast")
def forecast(db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    cm = date.today().strftime("%Y-%m")
    totals = db.execute(text(
        "SELECT month_year, expense FROM v_monthly_totals "
        "WHERE user_id = :uid AND month_year < :cm ORDER BY month_year"),
        {"uid": user.id, "cm": cm}).all()[-3:]
    values = [f(r[1]) for r in totals]

    names = {c.id: c.name for c in db.query(Category).all()}
    cat_rows = db.execute(text(
        "SELECT category_id, month_year, total_spent FROM v_monthly_category_spend "
        "WHERE user_id = :uid ORDER BY month_year"), {"uid": user.id}).all()
    by_cat = {}
    for cid, my, total in cat_rows:
        by_cat.setdefault(cid, {})[my] = f(total)
    unusual = []
    for cid, months in by_cat.items():
        current = months.get(cm, 0)
        history = [v for m, v in sorted(months.items()) if m < cm][-3:]
        if is_unusual(current, history):
            avg = moving_average(history)
            unusual.append({"category": names.get(cid, "Uncategorized"),
                            "this_month": current,
                            "usual_average": round(avg, 2),
                            "times_usual": round(current / avg, 2)})
    return {"forecast": {"for_month": month_range(cm)[1].strftime("%Y-%m"),
                         "predicted_expense": round(moving_average(values), 2),
                         "based_on_months": [r[0] for r in totals]},
            "unusual_spending": unusual}