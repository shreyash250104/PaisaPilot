from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from models import (ExpenseGroup, GroupMember, SharedExpense, ExpenseSplit,
                    Settlement, User)
from schemas import (GroupCreate, GroupOut, MemberAdd, GroupDetail, MemberOut,
                     SharedExpenseCreate, ExpenseOut, BalancesOut,
                     SettleCreate, SettlementOut)
from auth import get_current_user
from dsa.settle import simplify

router = APIRouter()

def money(x):
    return Decimal(str(x)).quantize(Decimal("0.01"))

def require_member(db, group_id, user_id):
    g = db.get(ExpenseGroup, group_id)
    if not g:
        raise HTTPException(404, "Group not found")
    if not db.get(GroupMember, (group_id, user_id)):
        raise HTTPException(403, "You are not a member of this group")
    return g

def member_ids(db, group_id):
    return [m.user_id for m in
            db.query(GroupMember).filter(GroupMember.group_id == group_id)]

def equal_shares(amount, users):
    total = int(amount * 100)
    base, rem = divmod(total, len(users))
    return {u: Decimal(base + (1 if i < rem else 0)) / 100
            for i, u in enumerate(users)}

def compute_net(db, group_id):
    net = {u: Decimal("0") for u in member_ids(db, group_id)}
    paid = (db.query(SharedExpense.paid_by, func.sum(SharedExpense.amount))
            .filter(SharedExpense.group_id == group_id)
            .group_by(SharedExpense.paid_by).all())
    for u, amt in paid:
        net[u] += amt
    owed = (db.query(ExpenseSplit.user_id, func.sum(ExpenseSplit.share_amount))
            .join(SharedExpense, SharedExpense.id == ExpenseSplit.expense_id)
            .filter(SharedExpense.group_id == group_id)
            .group_by(ExpenseSplit.user_id).all())
    for u, amt in owed:
        net[u] -= amt
    for s in db.query(Settlement).filter(Settlement.group_id == group_id):
        net[s.from_user] += s.amount
        net[s.to_user] -= s.amount
    return net

@router.post("/groups", response_model=GroupOut, status_code=201)
def create_group(data: GroupCreate, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    g = ExpenseGroup(name=data.name, created_by=user.id)
    db.add(g)
    db.flush()
    db.add(GroupMember(group_id=g.id, user_id=user.id))
    db.commit()
    db.refresh(g)
    return g

@router.get("/groups", response_model=list[GroupOut])
def my_groups(db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    return (db.query(ExpenseGroup)
            .join(GroupMember, GroupMember.group_id == ExpenseGroup.id)
            .filter(GroupMember.user_id == user.id).all())

@router.get("/groups/{group_id}", response_model=GroupDetail)
def group_detail(group_id: int, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    g = require_member(db, group_id, user.id)
    users = db.query(User).filter(User.id.in_(member_ids(db, group_id))).all()
    return {"id": g.id, "name": g.name, "created_by": g.created_by,
            "members": [{"user_id": u.id, "name": u.name, "email": u.email}
                        for u in users]}

@router.post("/groups/{group_id}/members", response_model=MemberOut, status_code=201)
def add_member(group_id: int, data: MemberAdd, db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    require_member(db, group_id, user.id)
    new = db.query(User).filter(User.email == data.email).first()
    if not new:
        raise HTTPException(404, "No registered user with that e-mail")
    if db.get(GroupMember, (group_id, new.id)):
        raise HTTPException(400, "Already a member")
    db.add(GroupMember(group_id=group_id, user_id=new.id))
    db.commit()
    return {"user_id": new.id, "name": new.name, "email": new.email}

@router.post("/groups/{group_id}/expenses", response_model=ExpenseOut, status_code=201)
def add_expense(group_id: int, data: SharedExpenseCreate,
                db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    require_member(db, group_id, user.id)
    members = member_ids(db, group_id)
    if data.paid_by not in members:
        raise HTTPException(400, "Payer is not a member of the group")
    amount = money(data.amount)
    if data.split_type == "equal":
        users = data.split_among or members
        if len(set(users)) != len(users) or any(u not in members for u in users):
            raise HTTPException(400, "split_among must list distinct group members")
        shares = equal_shares(amount, users)
    else:
        if not data.splits:
            raise HTTPException(400, "splits are required for a custom split")
        shares = {}
        for s in data.splits:
            if s.user_id not in members or s.user_id in shares:
                raise HTTPException(400, "Invalid or repeated member in splits")
            shares[s.user_id] = money(s.share)
        if sum(shares.values()) != amount:
            raise HTTPException(400, "Shares must add up to the amount")
    exp = SharedExpense(group_id=group_id, paid_by=data.paid_by, amount=amount,
                        description=data.description, split_type=data.split_type,
                        expense_date=data.expense_date)
    db.add(exp)
    db.flush()
    for u, share in shares.items():
        db.add(ExpenseSplit(expense_id=exp.id, user_id=u, share_amount=share))
    db.commit()           # the expense and all its splits are saved together
    db.refresh(exp)
    return exp

@router.get("/groups/{group_id}/expenses", response_model=list[ExpenseOut])
def list_expenses(group_id: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    require_member(db, group_id, user.id)
    return (db.query(SharedExpense).filter(SharedExpense.group_id == group_id)
            .order_by(SharedExpense.expense_date.desc(), SharedExpense.id.desc()).all())

@router.get("/groups/{group_id}/balances", response_model=BalancesOut)
def balances(group_id: int, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    require_member(db, group_id, user.id)
    net = compute_net(db, group_id)
    names = {u.id: u.name for u in
             db.query(User).filter(User.id.in_(list(net))).all()}
    return {"group_id": group_id,
            "balances": [{"user_id": u, "name": names[u], "net": float(a)}
                         for u, a in net.items()],
            "payments": [{"from_user": d, "from_name": names[d],
                          "to_user": c, "to_name": names[c], "amount": float(a)}
                         for d, c, a in simplify(net)]}

@router.post("/groups/{group_id}/settle", response_model=SettlementOut, status_code=201)
def settle(group_id: int, data: SettleCreate, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    require_member(db, group_id, user.id)
    members = member_ids(db, group_id)
    if data.from_user == data.to_user:
        raise HTTPException(400, "Payer and receiver must be different")
    if data.from_user not in members or data.to_user not in members:
        raise HTTPException(400, "Both users must be group members")
    amount = money(data.amount)
    owed = -compute_net(db, group_id)[data.from_user]
    if amount > owed:
        raise HTTPException(400, "Amount is more than the amount owed (%s)" % owed)
    s = Settlement(group_id=group_id, from_user=data.from_user,
                   to_user=data.to_user, amount=amount, settled_on=data.settled_on)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s