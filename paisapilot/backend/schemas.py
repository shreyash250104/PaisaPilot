from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    model_config = {"from_attributes": True}

class TokenOut(BaseModel):
    access_token: str
    token_type: str
    
class AccountCreate(BaseModel):
    name: str
    type: Literal["cash", "bank", "upi"]
    balance: float = 0

class AccountOut(BaseModel):
    id: int
    name: str
    type: str
    balance: float
    model_config = {"from_attributes": True}

class CategoryOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}

class TransactionCreate(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    amount: float = Field(gt=0)
    type: Literal["income", "expense"]
    description: Optional[str] = None
    txn_date: date

class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: float = Field(gt=0)
    type: Literal["income", "expense"]
    description: Optional[str] = None
    txn_date: date

class TransactionOut(BaseModel):
    id: int
    account_id: int
    category_id: Optional[int]
    amount: float
    type: str
    description: Optional[str]
    txn_date: date
    model_config = {"from_attributes": True}

class BudgetSet(BaseModel):
    category_id: int
    month_year: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    limit_amount: float = Field(gt=0)

class BudgetProgress(BaseModel):
    id: int
    category_id: int
    category: str
    month_year: str
    limit_amount: float
    spent: float
    percent: float
    status: str

class AlertOut(BaseModel):
    id: int
    budget_id: int
    category: str
    month_year: str
    level: int
    is_read: bool
    
    
class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class GroupOut(BaseModel):
    id: int
    name: str
    created_by: int
    model_config = {"from_attributes": True}

class MemberAdd(BaseModel):
    email: EmailStr

class MemberOut(BaseModel):
    user_id: int
    name: str
    email: EmailStr

class GroupDetail(BaseModel):
    id: int
    name: str
    created_by: int
    members: list[MemberOut]

class SplitItem(BaseModel):
    user_id: int
    share: float = Field(gt=0)

class SharedExpenseCreate(BaseModel):
    description: str
    amount: float = Field(gt=0)
    paid_by: int
    split_type: Literal["equal", "custom"] = "equal"
    split_among: Optional[list[int]] = None
    splits: Optional[list[SplitItem]] = None
    expense_date: date

class ExpenseOut(BaseModel):
    id: int
    group_id: int
    paid_by: int
    amount: float
    description: Optional[str]
    split_type: str
    expense_date: date
    model_config = {"from_attributes": True}

class BalanceItem(BaseModel):
    user_id: int
    name: str
    net: float

class PaymentItem(BaseModel):
    from_user: int
    from_name: str
    to_user: int
    to_name: str
    amount: float

class BalancesOut(BaseModel):
    group_id: int
    balances: list[BalanceItem]
    payments: list[PaymentItem]

class SettleCreate(BaseModel):
    from_user: int
    to_user: int
    amount: float = Field(gt=0)
    settled_on: date

class SettlementOut(BaseModel):
    id: int
    group_id: int
    from_user: int
    to_user: int
    amount: float
    settled_on: date
    model_config = {"from_attributes": True}
    
    
class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    target_amount: float = Field(gt=0)
    target_date: Optional[date] = None

class ContributeIn(BaseModel):
    amount: float = Field(gt=0)

class GoalOut(BaseModel):
    id: int
    title: str
    target_amount: float
    saved_amount: float
    percent: float
    status: str
    target_date: Optional[date]

class BillCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0)
    due_day: int = Field(ge=1, le=31)
    category_id: Optional[int] = None

class BillOut(BaseModel):
    id: int
    title: str
    amount: float
    due_day: int
    category_id: Optional[int]
    is_active: bool
    next_due: date
    days_left: int