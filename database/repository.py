"""
Repository layer for database operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func
from .models import Document, AgentLog, ProcessingQueue, Batch, Credential


class DocumentRepository:
    """
    Repository para operações com documentos
    """
    
    @staticmethod
    def create_document(session: Session, document_data: Dict[str, Any]) -> Document:
        """
        Cria um novo documento no banco
        """
        doc = Document(**document_data)
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc
    
    @staticmethod
    def get_document_by_id(session: Session, doc_id: int) -> Optional[Document]:
        """
        Busca documento por ID
        """
        return session.query(Document).filter(Document.id == doc_id).first()
    
    @staticmethod
    def get_document_by_access_key(session: Session, access_key: str) -> Optional[Document]:
        """
        Busca documento pela chave de acesso
        """
        return session.query(Document).filter(Document.access_key == access_key).first()
    
    @staticmethod
    def get_all_documents(session: Session, limit: int = 100, offset: int = 0) -> List[Document]:
        """
        Retorna todos os documentos ordenados por data de criação
        """
        return session.query(Document).order_by(desc(Document.created_at)).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_documents_by_batch_ids(session: Session, batch_ids: List[str]) -> List[Document]:
        """
        Retorna documentos filtrados por IDs de lotes
        """
        return session.query(Document).filter(Document.batch_id.in_(batch_ids)).order_by(desc(Document.created_at)).all()
    
    @staticmethod
    def search_documents(session: Session, query: str, document_type: Optional[str] = None) -> List[Document]:
        """
        Busca documentos por texto ou tipo
        """
        q = session.query(Document)
        
        if query:
            q = q.filter(
                or_(
                    Document.filename.ilike(f'%{query}%'),
                    Document.issuer_name.ilike(f'%{query}%'),
                    Document.recipient_name.ilike(f'%{query}%'),
                    Document.document_number.ilike(f'%{query}%')
                )
            )
        
        if document_type:
            q = q.filter(Document.document_type == document_type)
        
        return q.order_by(desc(Document.created_at)).all()
    
    @staticmethod
    def update_document(session: Session, doc_id: int, update_data: Dict[str, Any]) -> Optional[Document]:
        """
        Atualiza um documento
        """
        doc = session.query(Document).filter(Document.id == doc_id).first()
        if doc:
            for key, value in update_data.items():
                setattr(doc, key, value)
            doc.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(doc)
        return doc
    
    @staticmethod
    def delete_document(session: Session, doc_id: int) -> bool:
        """
        Deleta um documento
        """
        doc = session.query(Document).filter(Document.id == doc_id).first()
        if doc:
            session.delete(doc)
            session.commit()
            return True
        return False
    
    @staticmethod
    def delete_all_documents(session: Session) -> int:
        """
        Deleta todos os documentos do banco de dados
        Também deleta agent_logs e processing_queue relacionados
        Retorna o número de documentos deletados
        """
        from .models import AgentLog, ProcessingQueue
        
        # Conta documentos antes de deletar
        count = session.query(Document).count()
        
        # Deleta tabelas relacionadas primeiro (foreign key constraints)
        session.query(AgentLog).delete()
        session.query(ProcessingQueue).delete()
        
        # Deleta todos os documentos
        session.query(Document).delete()
        
        session.commit()
        return count
    
    @staticmethod
    def get_statistics(session: Session) -> Dict[str, Any]:
        """
        Retorna estatísticas gerais dos documentos
        """
        from sqlalchemy import func
        
        total = session.query(Document).count()
        valid = session.query(Document).filter(Document.is_valid == True).count()
        invalid = session.query(Document).filter(Document.has_errors == True).count()
        
        # Calcula totais financeiros
        totals = session.query(
            func.sum(Document.total_value),
            func.sum(Document.tax_total)
        ).first()
        
        total_value = float(totals[0]) if totals[0] else 0.0
        tax_total = float(totals[1]) if totals[1] else 0.0
        
        types = session.query(Document.document_type).distinct().all()
        type_counts = {}
        for doc_type in types:
            if doc_type[0]:
                count = session.query(Document).filter(Document.document_type == doc_type[0]).count()
                type_counts[doc_type[0]] = count
        
        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'total_value': total_value,
            'tax_total': tax_total,
            'by_type': type_counts
        }


class AgentLogRepository:
    """
    Repository para logs de agentes
    """
    
    @staticmethod
    def create_log(session: Session, log_data: Dict[str, Any]) -> AgentLog:
        """
        Cria um novo log de agente
        """
        log = AgentLog(**log_data)
        session.add(log)
        session.commit()
        session.refresh(log)
        return log
    
    @staticmethod
    def get_logs_by_document(session: Session, doc_id: int) -> List[AgentLog]:
        """
        Retorna logs de um documento
        """
        return session.query(AgentLog).filter(AgentLog.document_id == doc_id).order_by(AgentLog.started_at).all()
    
    @staticmethod
    def update_log(session: Session, log_id: int, update_data: Dict[str, Any]) -> Optional[AgentLog]:
        """
        Atualiza um log
        """
        log = session.query(AgentLog).filter(AgentLog.id == log_id).first()
        if log:
            for key, value in update_data.items():
                setattr(log, key, value)
            session.commit()
            session.refresh(log)
        return log


class ProcessingQueueRepository:
    """
    Repository para fila de processamento
    """
    
    @staticmethod
    def add_to_queue(session: Session, queue_data: Dict[str, Any]) -> ProcessingQueue:
        """
        Adiciona item à fila
        """
        item = ProcessingQueue(**queue_data)
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
    
    @staticmethod
    def create(batch_id: str, filename: str, file_path: str = None, priority: int = 1, meta_data: Dict = None) -> ProcessingQueue:
        """
        Cria novo item na fila (sem precisar de session)
        """
        from database import get_session
        session = get_session()
        try:
            item = ProcessingQueue(
                batch_id=batch_id,
                filename=filename,
                file_path=file_path,
                priority=priority,
                status='pending',
                meta_data=meta_data or {},
                attempts=0
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            session.expunge(item)  # Desanexa o objeto da sessão para uso posterior
            return item
        finally:
            session.close()
    
    @staticmethod
    def get_by_batch(batch_id: str) -> List[ProcessingQueue]:
        """
        Retorna todos os itens de um lote
        """
        from database import get_session
        session = get_session()
        try:
            items = session.query(ProcessingQueue).filter(ProcessingQueue.batch_id == batch_id).all()
            for item in items:
                session.expunge(item)  # Desanexa cada objeto
            return items
        finally:
            session.close()
    
    @staticmethod
    def get_pending(limit: int = 10) -> List[ProcessingQueue]:
        """
        Retorna itens pendentes
        """
        from database import get_session
        session = get_session()
        try:
            items = session.query(ProcessingQueue).filter(
                ProcessingQueue.status == 'pending'
            ).order_by(
                desc(ProcessingQueue.priority),
                ProcessingQueue.created_at
            ).limit(limit).all()
            for item in items:
                session.expunge(item)  # Desanexa cada objeto
            return items
        finally:
            session.close()
    
    @staticmethod
    def get_all(limit: int = 1000) -> List[ProcessingQueue]:
        """
        Retorna todos os itens
        """
        from database import get_session
        session = get_session()
        try:
            items = session.query(ProcessingQueue).order_by(desc(ProcessingQueue.created_at)).limit(limit).all()
            for item in items:
                session.expunge(item)  # Desanexa cada objeto
            return items
        finally:
            session.close()
    
    @staticmethod
    def update_status(queue_id: int, status: str, **kwargs) -> None:
        """
        Atualiza status de um item
        """
        from database import get_session
        session = get_session()
        try:
            item = session.query(ProcessingQueue).filter(ProcessingQueue.id == queue_id).first()
            if item:
                item.status = status
                for key, value in kwargs.items():
                    setattr(item, key, value)
                item.updated_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()
    
    @staticmethod
    def get_pending_items(session: Session, limit: int = 10) -> List[ProcessingQueue]:
        """
        Retorna itens pendentes da fila
        """
        return session.query(ProcessingQueue).filter(
            ProcessingQueue.status == 'pending'
        ).order_by(
            desc(ProcessingQueue.priority),
            ProcessingQueue.created_at
        ).limit(limit).all()
    
    @staticmethod
    def update_queue_item(session: Session, item_id: int, update_data: Dict[str, Any]) -> Optional[ProcessingQueue]:
        """
        Atualiza item da fila
        """
        item = session.query(ProcessingQueue).filter(ProcessingQueue.id == item_id).first()
        if item:
            for key, value in update_data.items():
                setattr(item, key, value)
            item.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(item)
        return item
    
    @staticmethod
    def get_batch_status(session: Session, batch_id: str) -> Dict[str, Any]:
        """
        Retorna status de um lote
        """
        items = session.query(ProcessingQueue).filter(ProcessingQueue.batch_id == batch_id).all()
        
        total = len(items)
        pending = sum(1 for item in items if item.status == 'pending')
        processing = sum(1 for item in items if item.status == 'processing')
        completed = sum(1 for item in items if item.status == 'completed')
        failed = sum(1 for item in items if item.status == 'failed')
        
        return {
            'batch_id': batch_id,
            'total': total,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed
        }


class BatchRepository:
    """
    Repository para gerenciamento de lotes de documentos
    """
    
    @staticmethod
    def create_batch(session: Session, batch_data: Dict[str, Any]) -> Batch:
        """
        Cria um novo lote
        """
        batch = Batch(**batch_data)
        session.add(batch)
        session.commit()
        session.refresh(batch)
        return batch
    
    @staticmethod
    def get_batch_by_id(session: Session, batch_id: str) -> Optional[Batch]:
        """
        Busca lote por batch_id
        """
        return session.query(Batch).filter(Batch.batch_id == batch_id).first()
    
    @staticmethod
    def get_all_batches(session: Session, limit: int = 100, offset: int = 0) -> List[Batch]:
        """
        Retorna todos os lotes ordenados por data de criação
        """
        return session.query(Batch).order_by(desc(Batch.created_at)).limit(limit).offset(offset).all()
    
    @staticmethod
    def update_batch_stats(session: Session, batch_id: str) -> Optional[Batch]:
        """
        Atualiza estatísticas do lote (document_count e total_value)
        """
        batch = session.query(Batch).filter(Batch.batch_id == batch_id).first()
        if not batch:
            return None
        
        # Calcula estatísticas a partir dos documentos
        stats = session.query(
            func.count(Document.id).label('count'),
            func.sum(Document.total_value).label('total')
        ).filter(Document.batch_id == batch_id).first()
        
        batch.document_count = stats.count or 0
        batch.total_value = float(stats.total or 0.0)
        batch.updated_at = datetime.utcnow()
        
        session.commit()
        session.refresh(batch)
        return batch
    
    @staticmethod
    def delete_batch(session: Session, batch_id: str) -> bool:
        """
        Deleta um lote (não deleta os documentos, apenas remove o batch_id deles)
        """
        batch = session.query(Batch).filter(Batch.batch_id == batch_id).first()
        if batch:
            # Remove batch_id dos documentos
            session.query(Document).filter(Document.batch_id == batch_id).update(
                {'batch_id': None, 'batch_name': None}
            )
            
            session.delete(batch)
            session.commit()
            return True
        return False
    
    @staticmethod
    def get_documents_by_batch(session: Session, batch_id: str) -> List[Document]:
        """
        Retorna todos os documentos de um lote
        """
        return session.query(Document).filter(Document.batch_id == batch_id).order_by(desc(Document.created_at)).all()


class CredentialRepository:
    """
    Repository para gerenciamento de credenciais e certificados digitais
    """
    
    @staticmethod
    def create_credential(session: Session, credential_data: Dict[str, Any]) -> Credential:
        """
        Cria uma nova credencial
        """
        credential = Credential(**credential_data)
        session.add(credential)
        session.commit()
        session.refresh(credential)
        return credential
    
    @staticmethod
    def get_credential_by_id(session: Session, cred_id: int) -> Optional[Credential]:
        """
        Busca credencial por ID
        """
        return session.query(Credential).filter(Credential.id == cred_id).first()
    
    @staticmethod
    def get_active_credentials(session: Session, credential_type: Optional[str] = None) -> List[Credential]:
        """
        Retorna credenciais ativas
        """
        q = session.query(Credential).filter(Credential.is_active == True)
        
        if credential_type:
            q = q.filter(Credential.credential_type == credential_type)
        
        return q.order_by(desc(Credential.created_at)).all()
    
    @staticmethod
    def get_credential_by_cnpj(session: Session, cnpj: str) -> Optional[Credential]:
        """
        Busca credencial por CNPJ
        """
        return session.query(Credential).filter(
            Credential.cnpj == cnpj,
            Credential.is_active == True
        ).first()
    
    @staticmethod
    def update_credential(session: Session, cred_id: int, update_data: Dict[str, Any]) -> Optional[Credential]:
        """
        Atualiza uma credencial
        """
        cred = session.query(Credential).filter(Credential.id == cred_id).first()
        if cred:
            for key, value in update_data.items():
                setattr(cred, key, value)
            cred.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(cred)
        return cred
    
    @staticmethod
    def deactivate_credential(session: Session, cred_id: int) -> bool:
        """
        Desativa uma credencial
        """
        cred = session.query(Credential).filter(Credential.id == cred_id).first()
        if cred:
            cred.is_active = False
            cred.updated_at = datetime.utcnow()
            session.commit()
            return True
        return False
    
    @staticmethod
    def rotate_credential(session: Session, cred_id: int, new_data: Dict[str, Any]) -> Optional[Credential]:
        """
        Rotaciona uma credencial (atualiza certificado/chave)
        """
        cred = session.query(Credential).filter(Credential.id == cred_id).first()
        if cred:
            cred.rotation_count += 1
            for key, value in new_data.items():
                setattr(cred, key, value)
            cred.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(cred)
        return cred
    
    @staticmethod
    def create(name: str, credential_type: str, **kwargs) -> Credential:
        """
        Cria nova credencial (sem precisar de session)
        """
        from database import get_session
        session = get_session()
        try:
            credential = Credential(
                name=name,
                credential_type=credential_type,
                **kwargs
            )
            session.add(credential)
            session.commit()
            session.refresh(credential)
            session.expunge(credential)  # Desanexa o objeto da sessão
            return credential
        finally:
            session.close()
    
    @staticmethod
    def get_by_id(cred_id: int) -> Optional[Credential]:
        """
        Busca credencial por ID (sem precisar de session)
        """
        from database import get_session
        session = get_session()
        try:
            cred = session.query(Credential).filter(Credential.id == cred_id).first()
            if cred:
                session.expunge(cred)  # Desanexa o objeto da sessão
            return cred
        finally:
            session.close()
    
    @staticmethod
    def get_all(credential_type: str = None) -> List[Credential]:
        """
        Retorna todas as credenciais (sem precisar de session)
        """
        from database import get_session
        session = get_session()
        try:
            q = session.query(Credential)
            if credential_type:
                q = q.filter(Credential.credential_type == credential_type)
            items = q.order_by(desc(Credential.created_at)).all()
            for item in items:
                session.expunge(item)  # Desanexa cada objeto
            return items
        finally:
            session.close()
    
    @staticmethod
    def delete(cred_id: int) -> bool:
        """
        Remove uma credencial (sem precisar de session)
        """
        from database import get_session
        session = get_session()
        try:
            cred = session.query(Credential).filter(Credential.id == cred_id).first()
            if cred:
                session.delete(cred)
                session.commit()
                return True
            return False
        finally:
            session.close()
