# apps/api/app/routers/sales.py
from datetime import date, datetime
from typing import List, Optional, Literal, Dict

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select, cast, Date
from sqlalchemy.orm import aliased

from ..db import SessionLocal
from .. import models

router = APIRouter()

# ---------- Pydantic outputs ----------
class SalesKPI(BaseModel):
    ingresos_neto: float
    cogs_neto: float
    margen_bruto: float
    gastos_neto: float
    beneficio_neto: float

class TSPoint(BaseModel):
    date: date
    ingresos: float
    gastos: float
    cogs: float
    beneficio: float
    margen_bruto: float

class NamedValue(BaseModel):
    name: str
    value: float

# ---------- Helpers ----------
def revenue_expr():
    # ingreso = precio * qty - descuento
    return (models.Transaction.unit_price_gross * models.Transaction.quantity) - func.coalesce(models.Transaction.discount, 0.0)

def cogs_expr():
    # COGS = sum(unit_cost * qty) usando join con products
    return (models.Product.unit_cost * models.Transaction.quantity)

def period_bounds(
    f: Optional[str], t: Optional[str]
) -> (Optional[date], Optional[date]):
    _from = datetime.strptime(f, "%Y-%m-%d").date() if f else None
    _to = datetime.strptime(t, "%Y-%m-%d").date() if t else None
    return _from, _to

def apply_date_range(stmt, col, _from: Optional[date], _to: Optional[date]):
    if _from:
        stmt = stmt.where(col >= _from)
    if _to:
        stmt = stmt.where(col <= _to)
    return stmt

# ---------- KPI ----------
@router.get("/kpi", response_model=SalesKPI)
def kpi(
    org_id: int = 1,
    _from: Optional[str] = None,
    _to: Optional[str] = None,
):
    f, t = period_bounds(_from, _to)

    with SessionLocal() as s:
        # Ingresos
        st_rev = select(func.coalesce(func.sum(revenue_expr()), 0.0)).select_from(models.Transaction).where(models.Transaction.org_id == org_id)
        st_rev = apply_date_range(st_rev, models.Transaction.date, f, t)
        ingresos = s.execute(st_rev).scalar_one()

        # COGS (join a products)
        st_cogs = (
            select(func.coalesce(func.sum(cogs_expr()), 0.0))
            .select_from(models.Transaction)
            .join(models.Product, models.Product.product_id == models.Transaction.product_id)
            .where(models.Transaction.org_id == org_id)
        )
        st_cogs = apply_date_range(st_cogs, models.Transaction.date, f, t)
        cogs = s.execute(st_cogs).scalar_one()

        margen = ingresos - cogs

        # Gastos
        st_exp = (
            select(func.coalesce(func.sum(models.Expense.amount_gross), 0.0))
            .select_from(models.Expense)
            .where(models.Expense.org_id == org_id)
        )
        st_exp = apply_date_range(st_exp, models.Expense.date, f, t)
        gastos = s.execute(st_exp).scalar_one()

        beneficio = margen - gastos

        return SalesKPI(
            ingresos_neto=round(ingresos, 2),
            cogs_neto=round(cogs, 2),
            margen_bruto=round(margen, 2),
            gastos_neto=round(gastos, 2),
            beneficio_neto=round(beneficio, 2),
        )

# ---------- Timeseries ----------
@router.get("/timeseries", response_model=List[TSPoint])
def timeseries(
    org_id: int = 1,
    granularity: Literal["day", "week", "month"] = "day",
    _from: Optional[str] = None,
    _to: Optional[str] = None,
):
    f, t = period_bounds(_from, _to)
    with SessionLocal() as s:
        # Group date function
        if granularity == "day":
            gdate = cast(models.Transaction.date, Date)
        elif granularity == "week":
            # ISO week start; group by year-week -> approximate by date_trunc in PG
            gdate = func.date_trunc("week", models.Transaction.date).cast(Date)
        else:
            gdate = func.date_trunc("month", models.Transaction.date).cast(Date)

        # ingresos / cogs grouped
        st_rev = (
            select(
                gdate.label("d"),
                func.coalesce(func.sum(revenue_expr()), 0.0).label("ingresos"),
                func.coalesce(func.sum(cogs_expr()), 0.0).label("cogs"),
            )
            .select_from(models.Transaction)
            .join(models.Product, models.Product.product_id == models.Transaction.product_id)
            .where(models.Transaction.org_id == org_id)
            .group_by(gdate)
            .order_by(gdate)
        )
        st_rev = apply_date_range(st_rev, models.Transaction.date, f, t)
        rows = s.execute(st_rev).all()

        # gastos grouped
        if granularity == "day":
            egdate = cast(models.Expense.date, Date)
        elif granularity == "week":
            egdate = func.date_trunc("week", models.Expense.date).cast(Date)
        else:
            egdate = func.date_trunc("month", models.Expense.date).cast(Date)

        st_exp = (
            select(
                egdate.label("d"),
                func.coalesce(func.sum(models.Expense.amount_gross), 0.0).label("gastos")
            )
            .select_from(models.Expense)
            .where(models.Expense.org_id == org_id)
            .group_by(egdate)
            .order_by(egdate)
        )
        st_exp = apply_date_range(st_exp, models.Expense.date, f, t)
        exp_rows = dict(s.execute(st_exp).all())

        out: List[TSPoint] = []
        for d, ingresos, cogs in rows:
            gastos = float(exp_rows.get(d, 0.0))
            margen = ingresos - cogs
            beneficio = margen - gastos
            out.append(
                TSPoint(
                    date=d,
                    ingresos=round(ingresos, 2),
                    gastos=round(gastos, 2),
                    cogs=round(cogs, 2),
                    margen_bruto=round(margen, 2),
                    beneficio=round(beneficio, 2),
                )
            )
        return out

# ---------- Top products ----------
@router.get("/top-products", response_model=List[NamedValue])
def top_products(
    org_id: int = 1,
    limit: int = 10,
    _from: Optional[str] = None,
    _to: Optional[str] = None,
):
    f, t = period_bounds(_from, _to)
    with SessionLocal() as s:
        st = (
            select(
                models.Product.name,
                func.coalesce(func.sum(revenue_expr()), 0.0).label("ingresos"),
            )
            .select_from(models.Transaction)
            .join(models.Product, models.Product.product_id == models.Transaction.product_id)
            .where(models.Transaction.org_id == org_id)
            .group_by(models.Product.name)
            .order_by(func.coalesce(func.sum(revenue_expr()), 0.0).desc())
            .limit(limit)
        )
        st = apply_date_range(st, models.Transaction.date, f, t)
        rows = s.execute(st).all()
        return [NamedValue(name=r[0], value=round(float(r[1]), 2)) for r in rows]

# ---------- By category ----------
@router.get("/by-category", response_model=List[NamedValue])
def by_category(
    org_id: int = 1,
    limit: int = 10,
    _from: Optional[str] = None,
    _to: Optional[str] = None,
):
    f, t = period_bounds(_from, _to)
    with SessionLocal() as s:
        st = (
            select(
                models.Product.category,
                func.coalesce(func.sum(revenue_expr()), 0.0).label("ingresos"),
            )
            .select_from(models.Transaction)
            .join(models.Product, models.Product.product_id == models.Transaction.product_id)
            .where(models.Transaction.org_id == org_id)
            .group_by(models.Product.category)
            .order_by(func.coalesce(func.sum(revenue_expr()), 0.0).desc())
            .limit(limit)
        )
        st = apply_date_range(st, models.Transaction.date, f, t)
        rows = s.execute(st).all()
        return [NamedValue(name=r[0] or "Sin categoría", value=round(float(r[1]), 2)) for r in rows]

# ---------- Cashflow (ingresos vs gastos) ----------
@router.get("/cashflow", response_model=List[TSPoint])
def cashflow(
    org_id: int = 1,
    _from: Optional[str] = None,
    _to: Optional[str] = None,
):
    # daily line good for small shops
    return timeseries(org_id=org_id, granularity="day", _from=_from, _to=_to)
