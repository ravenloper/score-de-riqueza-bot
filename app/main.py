from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.db import engine, Base, get_db
from app.services.whatsapp_logic import (
    extract_message_and_number,
    get_or_create_user,
    get_or_create_session,
    process_message,
)


class WhatsAppWebhook(BaseModel):
    # "from" é palavra reservada em Python, então usamos from_ com alias
    from_: Optional[str] = Field(default=None, alias="from")
    text: Optional[str] = None

    class Config:
        # permite usar tanto "from_" quanto "from" se precisar
        allow_population_by_field_name = True


app = FastAPI(title="Score de Riqueza Bot", version="0.1.0")


# Evento de startup: cria as tabelas no banco ao subir o servidor
@app.on_event("startup")
def on_startup():
    # Importa os models para registrar as tabelas antes do create_all
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Score de Riqueza Bot rodando"}


# Endpoint de verificação do webhook (para provedores tipo Meta/Facebook)
@app.get("/webhook/whatsapp")
async def verify_webhook(
    mode: Optional[str] = None,
    challenge: Optional[str] = None,
    verify_token: Optional[str] = None,
):
    """
    Alguns provedores chamam este endpoint para verificar o webhook.
    Comparamos o verify_token com o WHATSAPP_VERIFY_TOKEN do .env.
    """
    if verify_token != settings.whatsapp_verify_token:
        raise HTTPException(status_code=403, detail="Token de verificação inválido")

    return PlainTextResponse(challenge or "")


@app.post("/webhook/whatsapp")
async def receive_whatsapp_webhook(
    payload: WhatsAppWebhook,
    db=Depends(get_db),
):
    """
    Endpoint que vai receber as mensagens do WhatsApp via webhook.
    Aqui já:
    - extrai número e texto
    - cria/recupera usuário
    - cria/recupera sessão
    - delega para a máquina de estados em process_message
    """
    # Converte o modelo em dict usando o alias "from"
    body = payload.dict(by_alias=True, exclude_none=True)

    number, message = extract_message_and_number(body)

    if not number:
        return JSONResponse({"status": "ignored", "reason": "no number"})

    user = get_or_create_user(db, number)
    session = get_or_create_session(db, user)

    reply = process_message(db, user, session, message)

    return JSONResponse({"reply": reply})