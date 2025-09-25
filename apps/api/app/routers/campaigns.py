from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class Brief(BaseModel):
    objetivo: str
    publico: str
    tono: str
    producto: str
    beneficio: str
    precio: str | None = None
    oferta: str | None = None
    canales: List[str] = ["Instagram","Facebook","WhatsApp"]

class PostOut(BaseModel):
    canal: str
    caption: str
    hashtags: List[str]
    cta: str

class CampaignPack(BaseModel):
    posts: List[PostOut]

@router.post("/generate", response_model=CampaignPack)
def generate(brief: Brief):
    base = f"{brief.producto}: {brief.beneficio}. {brief.oferta or ''}".strip()
    tags = ["#Bullas","#Murcia","#ComercioLocal","#Ofertas"]
    posts = [PostOut(canal=c, caption=f"{base} ¡Te esperamos!", hashtags=tags, cta="Escríbenos por WhatsApp") for c in brief.canales]
    return CampaignPack(posts=posts)
