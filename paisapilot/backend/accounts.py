from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Account, Category, User
from schemas import AccountCreate, AccountOut, CategoryOut
from auth import get_current_user

router = APIRouter()

@router.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(data: AccountCreate, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    acc = Account(user_id=user.id, name=data.name, type=data.type,
                  balance=Decimal(str(data.balance)))
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc

@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    return db.query(Account).filter(Account.user_id == user.id).all()

@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    return db.query(Category).all()