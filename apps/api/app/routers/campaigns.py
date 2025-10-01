# apps/api/app/routers/campaigns.py
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter()

# --- Simple models for responses (kept independent of DB for robustness) ---

class CampaignOut(BaseModel):
    id: str
    name: str
    status: str

class CalendarItem(BaseModel):
    date: str           # YYYY-MM-DD
    time: str           # HH:MM (local)
    channel: str        # e.g., instagram
    title: str          # short title/headline
    caption: str        # post text/copy
    asset_url: Optional[str] = None  # image/video URL if any

# --- Minimal list endpoint (returns empty list when nothing yet) ---
@router.get("/", response_model=List[CampaignOut])
def list_campaigns():
    # If you already had a DB-driven implementation, keep it.
    # This version returns an empty list instead of raising.
    return []

# --- Robust calendar endpoint (no DB dependency) ---
@router.get("/calendar", response_model=List[CalendarItem])
def campaign_calendar(
    days: int = Query(14, ge=1, le=60, description="How many days ahead to plan"),
    canales: str = Query("instagram,facebook,whatsapp", description="Comma separated channels"),
):
    """
    Returns a simple, valid posting calendar for the next `days`.
    This version is safe even if there are no campaigns stored yet.
    """
    channels = [c.strip().lower() for c in canales.split(",") if c.strip()]
    if not channels:
        channels = ["instagram"]

    today = date.today()
    out: List[CalendarItem] = []

    # Basic content generators (so you always get something)
    def default_title(d: date, ch: str, idx: int) -> str:
        weekdays = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        return f"{weekdays[d.weekday()]} • {ch.capitalize()} • Día {idx+1}"

    def default_caption(d: date, ch: str, idx: int) -> str:
        return (
            f"Contenido del día {idx+1} para {ch.capitalize()}.\n"
            f"Fecha: {d.isoformat()} • #LeafAI"
        )

    # Use a placeholder image so the frontend can render a card nicely
    def placeholder_asset(seed: str) -> str:
        return f"https://picsum.photos/seed/{seed}/800/600"

    # We’ll post every day at a fixed time for each channel (you can refine later)
    default_time = "10:00"

    for i in range(days):
        d = today + timedelta(days=i)
        for ch in channels:
            out.append(
                CalendarItem(
                    date=d.isoformat(),
                    time=default_time,
                    channel=ch,
                    title=default_title(d, ch, i),
                    caption=default_caption(d, ch, i),
                    asset_url=placeholder_asset(f"{ch}-{d.isoformat()}"),
                )
            )

    return out
