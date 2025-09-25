from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from pydantic import BaseModel
from typing import Literal
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import init_engine, SessionLocal
from .. import models

router = APIRouter()

DataKind = Literal["products", "sales", "expenses", "inventory"]

TEMPLATES: dict[DataKind, list[str]] = {
    "products": ["product_id", "name", "category", "unit_cost", "vat_rate"],
    "sales": [
        "txn_id", "date", "product_id", "quantity",
        "unit_price_gross", "discount", "payment_method", "vat_rate"
    ],
    "expenses": [
        "exp_id", "date", "category", "description",
        "amount_gross", "vat_rate", "payment_method"
    ],
    "inventory": ["product_id", "stock_on_hand", "lead_time_days", "safety_stock"],
}

class IngestSummary(BaseModel):
    kind: DataKind
    rows_in_file: int
    inserted: int
    updated: int
    skipped: int
    errors: int

def _read_table(file: UploadFile) -> pd.DataFrame:
    name = (file.filename or "").lower()
    if name.endswith(".csv"):
        return pd.read_csv(file.file)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(file.file)
    raise HTTPException(400, "Formato no soportado. Usa .csv o .xlsx")

@router.get("/template")
def template(kind: DataKind):
    return {"kind": kind, "columns": TEMPLATES[kind]}

@router.post("/upload", response_model=IngestSummary)
def upload(kind: DataKind = Query(...), file: UploadFile = File(...)):
    init_engine()
    df = _read_table(file)
    df.columns = [c.strip() for c in df.columns]

    required = set(TEMPLATES[kind])
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(400, f"Faltan columnas: {missing}. Esperadas: {sorted(required)}")

    # Limpieza
    for col in df.columns:
        if col.endswith("_gross") or col in {"unit_cost", "unit_price_gross", "discount", "vat_rate"}:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        if col in {"quantity", "stock_on_hand", "lead_time_days", "safety_stock"}:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        if col == "date":
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date.astype(str)

    ins = upd = skipped = err = 0

    with SessionLocal() as db:
        org = db.scalar(select(models.Org).where(models.Org.id == 1))
        if not org:
            org = models.Org(id=1, name="Demo")
            db.add(org); db.commit()

        try:
            if kind == "products":
                ins, upd, skipped, err = _upsert_products(df, db)
            elif kind == "sales":
                ins, upd, skipped, err = _upsert_sales(df, db)
            elif kind == "expenses":
                ins, upd, skipped, err = _upsert_expenses(df, db)
            elif kind == "inventory":
                ins, upd, skipped, err = _upsert_inventory(df, db)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(500, f"Error guardando datos: {e}") from e

    return IngestSummary(kind=kind, rows_in_file=len(df),
                         inserted=ins, updated=upd, skipped=skipped, errors=err)

# ---- helpers ----
def _upsert_products(df: pd.DataFrame, db: Session):
    ins = upd = skipped = err = 0
    for _, r in df.iterrows():
        try:
            obj = db.get(models.Product, r["product_id"])
            if obj:
                obj.name = str(r.get("name") or obj.name)
                obj.category = str(r.get("category") or obj.category or "")
                if pd.notna(r.get("unit_cost")): obj.unit_cost = float(r["unit_cost"])
                if pd.notna(r.get("vat_rate")): obj.vat_rate = float(r["vat_rate"])
                upd += 1
            else:
                db.add(models.Product(
                    product_id=str(r["product_id"]), org_id=1,
                    name=str(r.get("name") or ""), category=str(r.get("category") or ""),
                    unit_cost=float(r.get("unit_cost") or 0.0),
                    vat_rate=float(r.get("vat_rate") or 0.21),
                ))
                ins += 1
        except Exception:
            err += 1
    return ins, upd, skipped, err

def _upsert_sales(df: pd.DataFrame, db: Session):
    ins = upd = skipped = err = 0
    for _, r in df.iterrows():
        try:
            pid = str(r["product_id"])
            if not db.get(models.Product, pid):
                db.add(models.Product(product_id=pid, org_id=1, name=pid, category="", unit_cost=0.0, vat_rate=float(r.get("vat_rate") or 0.21)))
            obj = db.get(models.Transaction, str(r["txn_id"]))
            if obj:
                obj.date = str(r["date"]); obj.product_id = pid
                obj.quantity = int(r["quantity"])
                obj.unit_price_gross = float(r["unit_price_gross"])
                obj.discount = float(r.get("discount") or 0.0)
                obj.payment_method = str(r.get("payment_method") or "efectivo")
                obj.vat_rate = float(r.get("vat_rate") or 0.21)
                upd += 1
            else:
                db.add(models.Transaction(
                    txn_id=str(r["txn_id"]), org_id=1, date=str(r["date"]),
                    product_id=pid, quantity=int(r["quantity"]),
                    unit_price_gross=float(r["unit_price_gross"]),
                    discount=float(r.get("discount") or 0.0),
                    payment_method=str(r.get("payment_method") or "efectivo"),
                    vat_rate=float(r.get("vat_rate") or 0.21),
                )); ins += 1
        except Exception:
            err += 1
    return ins, upd, skipped, err

def _upsert_expenses(df: pd.DataFrame, db: Session):
    ins = upd = skipped = err = 0
    for _, r in df.iterrows():
        try:
            obj = db.get(models.Expense, str(r["exp_id"]))
            if obj:
                obj.date = str(r["date"]); obj.category = str(r["category"])
                obj.description = str(r.get("description") or "")
                obj.amount_gross = float(r["amount_gross"])
                obj.vat_rate = float(r.get("vat_rate") or 0.21)
                obj.payment_method = str(r.get("payment_method") or "transferencia")
                upd += 1
            else:
                db.add(models.Expense(
                    exp_id=str(r["exp_id"]), org_id=1, date=str(r["date"]),
                    category=str(r["category"]), description=str(r.get("description") or ""),
                    amount_gross=float(r["amount_gross"]),
                    vat_rate=float(r.get("vat_rate") or 0.21),
                    payment_method=str(r.get("payment_method") or "transferencia"),
                )); ins += 1
        except Exception:
            err += 1
    return ins, upd, skipped, err

def _upsert_inventory(df: pd.DataFrame, db: Session):
    ins = upd = skipped = err = 0
    for _, r in df.iterrows():
        try:
            pid = str(r["product_id"])
            obj = db.get(models.Inventory, pid)
            if obj:
                obj.stock_on_hand = int(r["stock_on_hand"])
                obj.lead_time_days = int(r.get("lead_time_days") or obj.lead_time_days)
                obj.safety_stock = int(r.get("safety_stock") or obj.safety_stock)
                upd += 1
            else:
                if not db.get(models.Product, pid):
                    db.add(models.Product(product_id=pid, org_id=1, name=pid, category="", unit_cost=0.0, vat_rate=0.21))
                db.add(models.Inventory(
                    product_id=pid, org_id=1,
                    stock_on_hand=int(r["stock_on_hand"]),
                    lead_time_days=int(r.get("lead_time_days") or 7),
                    safety_stock=int(r.get("safety_stock") or 3),
                )); ins += 1
        except Exception:
            err += 1
    return ins, upd, skipped, err
