from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Account, Category, Transaction, User
from schemas import TransactionCreate, TransactionUpdate, TransactionOut
from auth import get_current_user

router = APIRouter()

def effect(txn_type, amount):
    amount = Decimal(str(amount))
    return amount if txn_type == "income" else -amount

def get_own_txn(db, txn_id, user_id):
    txn = db.query(Transaction).filter(
        Transaction.id == txn_id, Transaction.user_id == user_id).first()
    if not txn:
        raise HTTPException(404, "Transaction not found")
    return txn

@router.post("/transactions", response_model=TransactionOut, status_code=201)
def add_transaction(data: TransactionCreate, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    acc = db.query(Account).filter(
        Account.id == data.account_id, Account.user_id == user.id).first()
    if not acc:
        raise HTTPException(404, "Account not found")
    if data.category_id and not db.get(Category, data.category_id):
        raise HTTPException(404, "Category not found")
    txn = Transaction(user_id=user.id, **data.model_dump())
    acc.balance += effect(data.type, data.amount)
    db.add(txn)
    db.commit()          # transaction and balance saved together
    db.refresh(txn)
    return txn

@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(account_id: Optional[int] = None,
                      category_id: Optional[int] = None,
                      type: Optional[str] = None,
                      limit: int = 50,
                      db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    q = db.query(Transaction).filter(Transaction.user_id == user.id)
    if account_id:
        q = q.filter(Transaction.account_id == account_id)
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if type:
        q = q.filter(Transaction.type == type)
    return q.order_by(Transaction.txn_date.desc(),
                      Transaction.id.desc()).limit(limit).all()

@router.put("/transactions/{txn_id}", response_model=TransactionOut)
def update_transaction(txn_id: int, data: TransactionUpdate,
                       db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    txn = get_own_txn(db, txn_id, user.id)
    acc = db.get(Account, txn.account_id)
    acc.balance -= effect(txn.type, txn.amount)      # undo old effect
    txn.category_id = data.category_id
    txn.amount = Decimal(str(data.amount))
    txn.type = data.type
    txn.description = data.description
    txn.txn_date = data.txn_date
    acc.balance += effect(data.type, data.amount)    # apply new effect
    db.commit()
    db.refresh(txn)
    return txn

@router.delete("/transactions/{txn_id}", status_code=204)
def delete_transaction(txn_id: int, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    txn = get_own_txn(db, txn_id, user.id)
    acc = db.get(Account, txn.account_id)
    acc.balance -= effect(txn.type, txn.amount)
    db.delete(txn)
    db.commit()