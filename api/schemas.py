"""
Pydantic schemas for API requests and responses
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    """Response após upload de documento"""
    document_id: int
    filename: str
    status: str
    message: str


class DocumentSummary(BaseModel):
    """Resumo de documento para listagens"""
    id: int
    filename: str
    document_type: Optional[str]
    document_number: Optional[str]
    issuer_name: Optional[str]
    total_value: Optional[float]
    is_valid: bool
    has_errors: bool
    processing_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentDetail(BaseModel):
    """Detalhes completos de um documento"""
    id: int
    filename: str
    file_type: Optional[str]
    document_type: Optional[str]
    document_number: Optional[str]
    access_key: Optional[str]
    issuer_cnpj: Optional[str]
    issuer_name: Optional[str]
    recipient_cnpj: Optional[str]
    recipient_cpf: Optional[str]
    recipient_name: Optional[str]
    total_value: Optional[float]
    tax_total: Optional[float]
    issue_date: Optional[datetime]
    extracted_data: Optional[Dict[str, Any]]
    classification_data: Optional[Dict[str, Any]]
    validation_data: Optional[Dict[str, Any]]
    is_valid: bool
    has_errors: bool
    processing_status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentLogSummary(BaseModel):
    """Log de execução de agente"""
    id: int
    agent_name: str
    agent_status: Optional[str]
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    
    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    """Request para criar sessão de chat"""
    user_id: Optional[str] = "default"
    title: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """Response com dados da sessão de chat"""
    id: int
    session_id: str
    title: str
    user_id: str
    is_active: bool
    created_at: str
    message_count: int


class ChatMessageCreate(BaseModel):
    """Request para enviar mensagem"""
    session_id: str
    message: str
    uploaded_file_path: Optional[str] = None
    uploaded_filename: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Response com mensagem e metadados"""
    message_id: Optional[int] = None
    role: str
    content: str
    agent_used: Optional[str] = None
    reasoning: Optional[str] = None
    critic_analysis: Optional[str] = None
    confidence_score: Optional[float] = None
    intent_analysis: Optional[Dict[str, Any]] = None
    critic_review: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    error: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    """Response com histórico de mensagens"""
    session_id: str
    messages: List[Dict[str, Any]]


class StatisticsResponse(BaseModel):
    """Estatísticas gerais do sistema"""
    total: int
    valid: int
    invalid: int
    total_value: float
    tax_total: float
    by_type: Dict[str, int]


class ProcessingQueueItem(BaseModel):
    """Item da fila de processamento"""
    id: int
    batch_id: Optional[str]
    priority: int
    status: str
    scheduled_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class BatchStatusResponse(BaseModel):
    """Status de um lote de processamento"""
    batch_id: str
    total: int
    pending: int
    processing: int
    completed: int
    failed: int
