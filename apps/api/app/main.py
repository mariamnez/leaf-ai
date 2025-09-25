# apps/api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .routers import sales, inventory, campaigns, ingest


# Inicialización de BD y modelos
from .db import init_engine, Base
from . import models  # noqa: F401  # Asegura que SQLAlchemy vea los modelos

# Routers
from .routers import sales, inventory, campaigns, ingest


# --- App ---
app = FastAPI(
    title="Leaf AI — API",
    description="Flujo de caja, inventario y campañas para comercios (ES)",
    version="0.1.0",
    contact={"name": "Leaf AI"},
)

# --- CORS (frontend Next en 3000) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Registrar routers ---
app.include_router(sales.router, prefix="/api/sales", tags=["Flujo de Caja"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventario"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campañas"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingesta"])

# --- Health ---
class HealthOut(BaseModel):
    ok: bool
    db: bool

@app.on_event("startup")
def on_startup() -> None:
    """
    Arranca el engine y crea tablas si no existen.
    """
    engine = init_engine()
    Base.metadata.create_all(bind=engine)

@app.get("/api/health", response_model=HealthOut)
def health() -> HealthOut:
    """
    Comprueba que la app está viva y que la base de datos responde.
    """
    try:
        init_engine()
        return HealthOut(ok=True, db=True)
    except Exception:
        return HealthOut(ok=True, db=False)


# --- Raíz: redirige a docs de la API ---
@app.get("/", include_in_schema=False)
def root():
    return {"message": "Leaf AI API. Visita /docs para la documentación."}
