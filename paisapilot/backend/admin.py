from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from models import (Account, AuditLog, BudgetAlert, ExpenseGroup,
                    Transaction, User)
from auth import get_current_user

router = APIRouter()

def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admins only")
    return user

@router.get("/admin/stats")
def stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    def count(model):
        return db.query(func.count(model.id)).scalar()
    return {"users": count(User), "accounts": count(Account),
            "transactions": count(Transaction), "groups": count(ExpenseGroup),
            "budget_alerts": count(BudgetAlert), "audit_entries": count(AuditLog)}

@router.get("/admin/audit")
def audit(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db),
          admin: User = Depends(require_admin)):
    rows = (db.query(AuditLog, User.email)
            .outerjoin(User, User.id == AuditLog.user_id)
            .order_by(AuditLog.id.desc()).limit(limit).all())
    return [{"id": a.id, "user": email, "action": a.action,
             "table": a.table_name, "record_id": a.record_id,
             "at": a.created_at} for a, email in rows]