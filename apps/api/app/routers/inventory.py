from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ReorderRow(BaseModel):
    product_id: str
    name: str | None = None
    demand_h: float
    stock_on_hand: int
    lead_time_days: int
    safety_stock: int
    reorder_qty: int

@router.get("/reorder", response_model=List[ReorderRow])
def reorder(h: int = 14):
    return [
        ReorderRow(product_id="SKU-001", name="Sandalia", demand_h=20, stock_on_hand=5, lead_time_days=7, safety_stock=4, reorder_qty=9),
        ReorderRow(product_id="SKU-002", name="Novela", demand_h=8, stock_on_hand=10, lead_time_days=5, safety_stock=2, reorder_qty=0),
    ]
