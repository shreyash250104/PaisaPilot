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