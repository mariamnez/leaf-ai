from sqlalchemy import String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Org(Base):
    __tablename__ = "orgs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(160), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id"))
    org: Mapped["Org"] = relationship()

class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id"))
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80), default="")
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    vat_rate: Mapped[float] = mapped_column(Float, default=0.21)

class Transaction(Base):
    __tablename__ = "transactions"
    txn_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id"))
    date: Mapped[str] = mapped_column(String(10))  # ISO yyyy-mm-dd
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_gross: Mapped[float] = mapped_column(Float)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    payment_method: Mapped[str] = mapped_column(String(40), default="efectivo")
    vat_rate: Mapped[float] = mapped_column(Float, default=0.21)

class Expense(Base):
    __tablename__ = "expenses"
    exp_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id"))
    date: Mapped[str] = mapped_column(String(10))
    category: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
    amount_gross: Mapped[float] = mapped_column(Float)
    vat_rate: Mapped[float] = mapped_column(Float, default=0.21)
    payment_method: Mapped[str] = mapped_column(String(40), default="transferencia")

class Inventory(Base):
    __tablename__ = "inventory"
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("orgs.id"))
    stock_on_hand: Mapped[int] = mapped_column(Integer, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    safety_stock: Mapped[int] = mapped_column(Integer, default=3)
