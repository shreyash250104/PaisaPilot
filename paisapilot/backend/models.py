from sqlalchemy import (Column, Integer, String, DateTime, Date,
                        Numeric, ForeignKey, func)
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(10), nullable=False)
    balance = Column(Numeric(12, 2), default=0)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(60), nullable=False)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10), nullable=False)
    description = Column(String(255))
    txn_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())