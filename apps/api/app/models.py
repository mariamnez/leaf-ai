# apps/api/app/models.py
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.db import Base


# ---------------------------
#  Organización y usuarios
# ---------------------------

class Org(Base):
    __tablename__ = "orgs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False, unique=True)

    users = relationship("User", back_populates="org", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="org", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="org", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="org", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="org", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="org", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Org id={self.id} name={self.name!r}>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    name = Column(String(120), nullable=True)

    org = relationship("Org", back_populates="users")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


# ---------------------------
#  Catálogo / productos
# ---------------------------

class Product(Base):
    """
    Producto de catálogo. El coste unitario y el IVA (vat_rate) nos sirven
    para calcular COGS y márgenes en /api/sales/kpi.
    """
    __tablename__ = "products"

    id = Column(String(60), primary_key=True)  # p.ej. SKU o slug
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=True)

    name = Column(String(200), nullable=False)
    category = Column(String(120), nullable=True)

    # Coste unitario (sin impuestos) para COGS
    unit_cost = Column(Float, nullable=False, default=0.0)

    # IVA aplicable al producto (0.21, 0.10, 0.04, etc.)
    vat_rate = Column(Float, nullable=False, default=0.21)

    org = relationship("Org", back_populates="products")
    transactions = relationship("Transaction", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product id={self.id!r} name={self.name!r}>"


# ---------------------------
#  Ventas / transacciones
# ---------------------------

class Transaction(Base):
    """
    Venta/Transacción. Se usa en KPIs (/api/sales/kpi).
    MUY IMPORTANTE: 'created_at' para solucionar el error de columna ausente.
    """
    __tablename__ = "transactions"

    # ID de la transacción (puede venir del TPV / ERP, lo tratamos como texto)
    txn_id = Column(String(80), primary_key=True)

    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=True)

    # Fecha comercial de la transacción (el día de la venta)
    date = Column(Date, nullable=False)

    product_id = Column(String(60), ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)

    # Precio unitario BRUTO (con impuestos); lo usamos como "ingreso bruto unitario"
    unit_price_gross = Column(Float, nullable=False)

    # Descuento total aplicado a la transacción (importe positivo)
    discount = Column(Float, default=0.0)

    payment_method = Column(String(80), nullable=True)

    # IVA aplicado (0.21, 0.10, 0.04, ...)
    vat_rate = Column(Float, default=0.21)

    # 👇 Campo que faltaba en tu BD; es clave tenerlo
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org = relationship("Org", back_populates="transactions")
    product = relationship("Product", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Txn id={self.txn_id!r} date={self.date} prod={self.product_id!r} qty={self.quantity}>"


# ---------------------------
#  Gastos
# ---------------------------

class Expense(Base):
    """
    Gastos de la tienda (publicidad, suministros, etc.). Sirven para el KPI
    'gastos_neto' y también para campañas si quisiéramos calcular ROAS.
    """
    __tablename__ = "expenses"

    id = Column(String(80), primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=True)

    date = Column(Date, nullable=False)
    category = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)

    # Importe BRUTO del gasto
    amount_gross = Column(Float, nullable=False)

    vat_rate = Column(Float, default=0.21)
    payment_method = Column(String(80), nullable=True)

    org = relationship("Org", back_populates="expenses")

    def __repr__(self) -> str:
        return f"<Expense id={self.id!r} date={self.date} gross={self.amount_gross}>"


# ---------------------------
#  Inventario (para reaprovisionamiento / forecast simple)
# ---------------------------

class Inventory(Base):
    """
    Estado de inventario por producto: lo usamos en el endpoint
    /api/inventory/reorder para calcular cantidades a pedir según
    demanda, LT y stock de seguridad.
    """
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=True)

    product_id = Column(String(60), ForeignKey("products.id"), nullable=False)
    name = Column(String(200), nullable=True)

    # Demanda por hora/día (según lo que uses en tu lógica)
    demand_h = Column(Float, nullable=True, default=0.0)

    # Stock disponible actualmente
    stock_on_hand = Column(Float, nullable=True, default=0.0)

    # Plazo de entrega (días)
    lead_time_days = Column(Integer, nullable=True, default=0)

    # Stock de seguridad (unidades)
    safety_stock = Column(Float, nullable=True, default=0.0)

    org = relationship("Org", back_populates="inventory")

    def __repr__(self) -> str:
        return f"<Inventory pid={self.product_id!r} stock={self.stock_on_hand}>"


# ---------------------------
#  Campañas (plan + posts)
# ---------------------------

class Campaign(Base):
    """
    Campaña de marketing (plan base) para una organización.
    """
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("orgs.id"), nullable=True)

    title = Column(String(200), nullable=False)
    objective = Column(String(200), nullable=True)
    audience = Column(String(200), nullable=True)
    tone = Column(String(100), nullable=True)

    # Fechas de campaña
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Presupuesto en euros (bruto)
    budget_eur = Column(Float, nullable=True, default=0.0)

    # Canales, como lista en texto (p. ej. "instagram,facebook,whatsapp")
    channels = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org = relationship("Org", back_populates="campaigns")
    posts = relationship("CampaignPost", back_populates="campaign", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Campaign id={self.id} title={self.title!r}>"


class CampaignPost(Base):
    """
    Publicación planificada dentro de una campaña para un canal concreto.
    """
    __tablename__ = "campaign_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)

    channel = Column(String(80), nullable=False)         # p.ej. instagram, facebook, whatsapp
    day_date = Column(Date, nullable=False)

    caption = Column(Text, nullable=True)                # copy del post
    image_url = Column(Text, nullable=True)              # url a imagen generada/subida
    hashtags = Column(Text, nullable=True)               # "#Bullas #Murcia ... "
    cta = Column(String(160), nullable=True)             # Llamada a la acción

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    campaign = relationship("Campaign", back_populates="posts")

    def __repr__(self) -> str:
        return f"<CampaignPost id={self.id} ch={self.channel!r} day={self.day_date}>"
