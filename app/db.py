# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Usa a DATABASE_URL do .env ou, se estiver vazia, cai no sqlite local
SQLALCHEMY_DATABASE_URL = settings.database_url or "sqlite:///./score.db"

# Para sqlite precisamos desse connect_args específico
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependência para usar sessão de banco nas rotas, quando precisarmos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()