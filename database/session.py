"""
Database session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/nfe_extractor')

# Pool de conexões otimizado para evitar SSL timeouts
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,              # Máximo de 10 conexões no pool
    max_overflow=20,           # Até 20 conexões extras em picos
    pool_recycle=3600,         # Recicla conexões a cada 1 hora
    pool_pre_ping=True,        # Testa conexão antes de usar (detecta SSL mortas)
    connect_args={
        "connect_timeout": 10,  # Timeout de 10s para conectar
        "options": "-c statement_timeout=30000"  # 30s timeout para queries
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session() -> Session:
    """
    Retorna uma sessão do banco de dados
    """
    return SessionLocal()


def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas
    """
    from .models import Document, AgentLog, ProcessingQueue, Batch, Credential, ChatSession, ChatMessage
    Base.metadata.create_all(bind=engine)
