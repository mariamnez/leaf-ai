import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Cargar .env de forma robusta (busca apps/api/.env o leaf-ai/.env)
HERE = Path(__file__).resolve()
API_DIR = HERE.parents[1]      # .../apps/api
ROOT_DIR = HERE.parents[2]     # .../leaf-ai
for candidate in (API_DIR / ".env", ROOT_DIR / ".env"):
    if candidate.exists():
        load_dotenv(candidate, override=False)
        break
else:
    load_dotenv(override=False)

DATABASE_URL = os.getenv("DATABASE_URL")

_engine = None
SessionLocal = None

class Base(DeclarativeBase):
    pass

def init_engine():
    global _engine, SessionLocal
    if _engine is None:
        assert DATABASE_URL, "DATABASE_URL no configurada"
        connect_args = {}
        if DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine
