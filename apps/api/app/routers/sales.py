from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select
from ..db import SessionLocal
from .. import models

router = APIRouter()

class SalesKPI(BaseModel):
    ingresos_neto: float
    cogs_neto: float
    margen_bruto: float
    gastos_neto: float
    beneficio_neto: float

@router.get("/kpi", response_model=SalesKPI)
def kpi():
    with SessionLocal() as db:
        # Ingresos netos: suma de (precio * qty - descuento)
        ingresos = db.execute(
            select(func.coalesce(func.sum((models.Transaction.unit_price_gross * models.Transaction.quantity) - models.Transaction.discount), 0.0))
        ).scalar() or 0.0

        # COGS: unit_cost * qty (join products)
        cogs = db.execute(
            select(func.coalesce(func.sum(models.Product.unit_cost * models.Transaction.quantity), 0.0)
            ).select_from(models.Transaction).join(models.Product, models.Product.product_id == models.Transaction.product_id)
        ).scalar() or 0.0

        margen_bruto = ingresos - cogs

        # Gastos netos
        gastos = db.execute(
            select(func.coalesce(func.sum(models.Expense.amount_gross), 0.0))
        ).scalar() or 0.0

        beneficio = margen_bruto - gastos

        return SalesKPI(
            ingresos_neto=round(ingresos, 2),
            cogs_neto=round(cogs, 2),
            margen_bruto=round(margen_bruto, 2),
            gastos_neto=round(gastos, 2),
            beneficio_neto=round(beneficio, 2),
        )
