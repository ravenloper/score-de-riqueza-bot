# app/models.py
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    whatsapp_number = Column(String(50), index=True, nullable=False)
    nome = Column(String(255), nullable=True)
    instagram = Column(String(255), nullable=True)
    renda_faixa = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    score_sessions = relationship("ScoreSession", back_populates="user")


class ScoreSession(Base):
    __tablename__ = "score_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(String(30), default="em_andamento")  # em_andamento, concluida, abandonada
    estado_atual = Column(String(50), nullable=True)

    perfil_nome = Column(String(50), nullable=True)
    score_total = Column(Integer, nullable=True)
    pilar_dominante = Column(String(50), nullable=True)
    pilar_toxico = Column(String(50), nullable=True)
    renda_qualificada = Column(Boolean, default=False)
    pdf_url = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="score_sessions")
    answers = relationship(
        "ScoreAnswer", back_populates="session", cascade="all, delete-orphan"
    )
    open_answers = relationship(
        "ScoreOpenAnswers", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )
    pillars = relationship(
        "ScorePillars", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )


class ScoreAnswer(Base):
    __tablename__ = "score_answers"

    id = Column(Integer, primary_key=True, index=True)
    score_session_id = Column(Integer, ForeignKey("score_sessions.id"), nullable=False)

    question_number = Column(Integer, nullable=False)  # 1 a 30
    pillar_code = Column(String(30), nullable=False)   # tempo, familia, decisao etc.
    answer_value = Column(Integer, nullable=False)     # 1 a 5

    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ScoreSession", back_populates="answers")


class ScoreOpenAnswers(Base):
    __tablename__ = "score_open_answers"

    id = Column(Integer, primary_key=True, index=True)
    score_session_id = Column(Integer, ForeignKey("score_sessions.id"), nullable=False)

    motivo_compra = Column(Text, nullable=True)
    ganho_buscado = Column(Text, nullable=True)
    maior_desafio = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ScoreSession", back_populates="open_answers")


class ScorePillars(Base):
    __tablename__ = "score_pillars"

    id = Column(Integer, primary_key=True, index=True)
    score_session_id = Column(Integer, ForeignKey("score_sessions.id"), nullable=False)

    tempo = Column(Integer, nullable=True)
    familia = Column(Integer, nullable=True)
    decisao = Column(Integer, nullable=True)
    dinheiro = Column(Integer, nullable=True)
    fe_principios = Column(Integer, nullable=True)
    legado = Column(Integer, nullable=True)
    energia_saude = Column(Integer, nullable=True)
    networking = Column(Integer, nullable=True)
    aprendizado = Column(Integer, nullable=True)
    risco_medo = Column(Integer, nullable=True)

    session = relationship("ScoreSession", back_populates="pillars")