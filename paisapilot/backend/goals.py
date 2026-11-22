import calendar
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Category, RecurringBill, SavingsGoal, User
from schemas import BillCreate, BillOut, ContributeIn, GoalCreate, GoalOut
from auth import get_current_user

router = APIRouter()

def goal_out(g):
    target, saved = float(g.target_amount), float(g.saved_amount)
    return {"id": g.id, "title": g.title, "target_amount": target,
            "saved_amount": saved, "percent": round(saved / target * 100, 1),
            "status": "achieved" if saved >= target else "in progress",
            "target_date": g.target_date}

def get_goal(db, goal_id, user_id):
    g = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id, SavingsGoal.user_id == user_id).first()
    if not g:
        raise HTTPException(404, "Goal not found")
    return g

@router.post("/goals", response_model=GoalOut, status_code=201)
def create_goal(data: GoalCreate, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    g = SavingsGoal(user_id=user.id, title=data.title,
                    target_amount=Decimal(str(data.target_amount)),
                    saved_amount=Decimal("0"), target_date=data.target_date)
    db.add(g)
    db.commit()
    db.refresh(g)
    return goal_out(g)

@router.get("/goals", response_model=list[GoalOut])
def list_goals(db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    return [goal_out(g) for g in
            db.query(SavingsGoal).filter(SavingsGoal.user_id == user.id).all()]

@router.post("/goals/{goal_id}/contribute", response_model=GoalOut)
def contribute(goal_id: int, data: ContributeIn, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    g = get_goal(db, goal_id, user.id)
    g.saved_amount += Decimal(str(data.amount))
    db.commit()
    db.refresh(g)
    return goal_out(g)

@router.delete("/goals/{goal_id}", status_code=204)
def delete_goal(goal_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    db.delete(get_goal(db, goal_id, user.id))
    db.commit()

# ---------------- recurring bills ----------------
def next_due(due_day, today):
    def clamp(y, m):
        return date(y, m, min(due_day, calendar.monthrange(y, m)[1]))
    d = clamp(today.year, today.month)
    if d >= today:
        return d
    y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    return clamp(y, m)

def bill_out(b, today):
    d = next_due(b.due_day, today)
    return {"id": b.id, "title": b.title, "amount": float(b.amount),
            "due_day": b.due_day, "category_id": b.category_id,
            "is_active": bool(b.is_active), "next_due": d,
            "days_left": (d - today).days}

@router.post("/bills", response_model=BillOut, status_code=201)
def create_bill(data: BillCreate, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    if data.category_id and not db.get(Category, data.category_id):
        raise HTTPException(404, "Category not found")
    b = RecurringBill(user_id=user.id, title=data.title,
                      amount=Decimal(str(data.amount)), due_day=data.due_day,
                      category_id=data.category_id, is_active=True)
    db.add(b)
    db.commit()
    db.refresh(b)
    return bill_out(b, date.today())

@router.get("/bills", response_model=list[BillOut])
def list_bills(db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    today = date.today()
    return [bill_out(b, today) for b in db.query(RecurringBill).filter(
        RecurringBill.user_id == user.id).all()]

@router.get("/bills/upcoming", response_model=list[BillOut])
def upcoming(days: int = Query(7, ge=1, le=60), db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    today = date.today()
    items = [bill_out(b, today) for b in db.query(RecurringBill).filter(
        RecurringBill.user_id == user.id, RecurringBill.is_active.is_(True)).all()]
    return sorted([i for i in items if i["days_left"] <= days],
                  key=lambda i: i["days_left"])

@router.delete("/bills/{bill_id}", status_code=204)
def delete_bill(bill_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    b = db.query(RecurringBill).filter(
        RecurringBill.id == bill_id, RecurringBill.user_id == user.id).first()
    if not b:
        raise HTTPException(404, "Bill not found")
    db.delete(b)
    db.commit()