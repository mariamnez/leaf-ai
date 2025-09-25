from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .db import init_engine, Base
from . import models  # noqa: F401
from .routers import sales, inventory, campaigns

app = FastAPI(
    title="Leaf AI — API",
    description="Flujo de Caja, Inventario y Campañas (ES)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(sales.router, prefix="/api/sales", tags=["Flujo de Caja"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventario"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campañas"])

class HealthOut(BaseModel):
    ok: bool
    db: bool

@app.on_event("startup")
def startup() -> None:
    engine = init_engine()
    Base.metadata.create_all(bind=engine)

@app.get("/api/health", response_model=HealthOut)
def health() -> HealthOut:
    try:
        init_engine()
        return HealthOut(ok=True, db=True)
    except Exception:
        return HealthOut(ok=True, db=False)
