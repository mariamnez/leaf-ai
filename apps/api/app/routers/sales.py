from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class SalesKPI(BaseModel):
    ingresos_neto: float
    cogs_neto: float
    margen_bruto: float
    gastos_neto: float
    beneficio_neto: float

@router.get("/kpi", response_model=SalesKPI)
def kpi():
    return SalesKPI(
        ingresos_neto=12345.67,
        cogs_neto=4567.89,
        margen_bruto=7777.78,
        gastos_neto=3000.00,
        beneficio_neto=4777.78,
    )
