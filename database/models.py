"""
Database models for NFe extraction system
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float, LargeBinary
from sqlalchemy.orm import relationship
from .session import Base


class Document(Base):
    """
    Modelo para documentos processados
    """
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    
    document_type = Column(String(50))
    document_number = Column(String(100))
    access_key = Column(String(44), index=True)
    
    issuer_cnpj = Column(String(20), index=True)
    issuer_name = Column(String(255))
    recipient_cnpj = Column(String(20))
    recipient_cpf = Column(String(15))
    recipient_name = Column(String(255))
    
    total_value = Column(Float)
    tax_total = Column(Float)
    issue_date = Column(DateTime)
    
    extracted_data = Column(JSON)
    classification_data = Column(JSON)
    validation_data = Column(JSON)
    
    is_valid = Column(Boolean, default=False)
    has_errors = Column(Boolean, default=False)
    processing_status = Column(String(50), default='pending')
    
    batch_id = Column(String(100), index=True, nullable=True)
    batch_name = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agent_logs = relationship("AgentLog", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document {self.filename} - {self.document_type}>"


class AgentLog(Base):
    """
    Modelo para logs de processamento de agentes
    """
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    
    agent_name = Column(String(100), nullable=False)
    agent_status = Column(String(50))
    
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    document = relationship("Document", back_populates="agent_logs")
    
    def __repr__(self):
        return f"<AgentLog {self.agent_name} - Doc {self.document_id}>"


class ProcessingQueue(Base):
    """
    Modelo para fila de processamento em lote
    """
    __tablename__ = 'processing_queue'
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(100), index=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    
    filename = Column(String(255))
    file_path = Column(String(500))
    
    priority = Column(Integer, default=0)
    status = Column(String(50), default='pending')
    
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    attempts = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text)
    
    meta_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ProcessingQueue {self.batch_id} - {self.status}>"


class Batch(Base):
    """
    Modelo para metadados de lotes de documentos
    """
    __tablename__ = 'batches'
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(100), unique=True, nullable=False, index=True)
    batch_name = Column(String(255))
    
    origin = Column(String(50))
    document_count = Column(Integer, default=0)
    total_value = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Batch {self.batch_name} - {self.document_count} docs>"


class Credential(Base):
    """
    Modelo para armazenar credenciais e certificados digitais criptografados
    """
    __tablename__ = 'credentials'
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(255), nullable=False)
    credential_type = Column(String(50), nullable=False)
    
    certificate_data = Column(LargeBinary)
    private_key_data = Column(LargeBinary)
    password_hash = Column(String(255))
    
    cnpj = Column(String(20), index=True)
    environment = Column(String(20), default='production')
    
    is_active = Column(Boolean, default=True)
    is_valid = Column(Boolean, default=True)
    
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    rotation_count = Column(Integer, default=0)
    
    meta_info = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Credential {self.name} - {self.credential_type}>"


class ChatSession(Base):
    """
    Modelo para sessões de chat
    """
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    
    title = Column(String(255))
    user_id = Column(String(100), index=True)
    
    is_active = Column(Boolean, default=True)
    meta_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    
    def __repr__(self):
        return f"<ChatSession {self.session_id} - {self.title}>"


class ChatMessage(Base):
    """
    Modelo para mensagens de chat
    """
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=False)
    
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    
    agent_used = Column(String(100))
    reasoning = Column(Text)
    critic_analysis = Column(Text)
    confidence_score = Column(Float)
    
    attached_document_id = Column(Integer, ForeignKey('documents.id'))
    meta_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")
    attached_document = relationship("Document")
    
    def __repr__(self):
        return f"<ChatMessage {self.role} - Session {self.session_id}>"
