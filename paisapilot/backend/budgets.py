from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from models import Budget, BudgetAlert, Category, Transaction, User
from schemas import BudgetSet, BudgetProgress, AlertOut
from auth import get_current_user

router = APIRouter()

def month_range(month_year):
    y, m = int(month_year[:4]), int(month_year[5:7])
    return date(y, m, 1), date(y + (m == 12), (m % 12) + 1, 1)

def progress(db, b, cat_name):
    start, end = month_range(b.month_year)
    spent = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == b.user_id,
        Transaction.category_id == b.category_id,
        Transaction.type == "expense",
        Transaction.txn_date >= start,
        Transaction.txn_date < end).scalar()
    percent = round(float(spent) / float(b.limit_amount) * 100, 1)
    status = "exceeded" if percent >= 100 else "warning" if percent >= 80 else "ok"
    return {"id": b.id, "category_id": b.category_id, "category": cat_name,
            "month_year": b.month_year, "limit_amount": float(b.limit_amount),
            "spent": float(spent), "percent": percent, "status": status}

@router.post("/budgets", response_model=BudgetProgress, status_code=201)
def set_budget(data: BudgetSet, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    cat = db.get(Category, data.category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    b = db.query(Budget).filter(
        Budget.user_id == user.id, Budget.category_id == data.category_id,
        Budget.month_year == data.month_year).first()
    if b:
        b.limit_amount = Decimal(str(data.limit_amount))
    else:
        b = Budget(user_id=user.id, category_id=data.category_id,
                   month_year=data.month_year,
                   limit_amount=Decimal(str(data.limit_amount)))
        db.add(b)
    db.commit()
    db.refresh(b)
    return progress(db, b, cat.name)

@router.get("/budgets", response_model=list[BudgetProgress])
def list_budgets(month: Optional[str] = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
                 db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    month = month or date.today().strftime("%Y-%m")
    rows = (db.query(Budget, Category.name)
            .join(Category, Category.id == Budget.category_id)
            .filter(Budget.user_id == user.id, Budget.month_year == month).all())
    return [progress(db, b, name) for b, name in rows]

@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(unread_only: bool = False, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    q = (db.query(BudgetAlert, Budget, Category.name)
         .join(Budget, Budget.id == BudgetAlert.budget_id)
         .join(Category, Category.id == Budget.category_id)
         .filter(BudgetAlert.user_id == user.id))
    if unread_only:
        q = q.filter(BudgetAlert.is_read.is_(False))
    rows = q.order_by(BudgetAlert.id.desc()).all()
    return [{"id": a.id, "budget_id": b.id, "category": name,
             "month_year": b.month_year, "level": a.level,
             "is_read": bool(a.is_read)} for a, b, name in rows]

@router.put("/alerts/{alert_id}/read", response_model=AlertOut)
def mark_read(alert_id: int, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    a = db.query(BudgetAlert).filter(
        BudgetAlert.id == alert_id, BudgetAlert.user_id == user.id).first()
    if not a:
        raise HTTPException(404, "Alert not found")
    a.is_read = True
    db.commit()
    b = db.get(Budget, a.budget_id)
    return {"id": a.id, "budget_id": b.id, "category": db.get(Category, b.category_id).name,
            "month_year": b.month_year, "level": a.level, "is_read": True}