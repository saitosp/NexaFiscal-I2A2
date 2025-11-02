"""
Document service - Business logic for document processing and persistence
"""
from typing import Dict, Any, List, Optional, cast
from datetime import datetime
from database import (
    get_session,
    Document,
    AgentLog,
    DocumentRepository,
    AgentLogRepository
)


class DocumentService:
    """
    Serviço para gerenciar documentos e integrar com o banco de dados
    """
    
    @staticmethod
    def save_processed_document(result: Dict[str, Any]) -> int:
        """
        Salva documento processado no banco de dados
        
        Args:
            result: Resultado do processamento do workflow
            
        Returns:
            Document salvo no banco
        """
        session = get_session()
        
        try:
            extracted_data = result.get('extracted_data', {})
            classification = result.get('classification', {})
            validation = result.get('validation', {})
            
            emitente = extracted_data.get('emitente', {})
            destinatario = extracted_data.get('destinatario', {})
            totais = extracted_data.get('totais', {})
            info_adicional = extracted_data.get('info_adicional', {})
            
            issue_date = None
            if info_adicional.get('data_emissao'):
                try:
                    issue_date = datetime.fromisoformat(info_adicional['data_emissao'])
                except:
                    pass
            
            document_data = {
                'filename': result.get('filename', ''),
                'file_path': result.get('file_path', ''),
                'file_type': classification.get('file_type', ''),
                'document_type': classification.get('document_type', ''),
                'document_number': info_adicional.get('numero', ''),
                'access_key': info_adicional.get('chave_acesso', ''),
                'issuer_cnpj': emitente.get('cnpj', ''),
                'issuer_name': emitente.get('razao_social', ''),
                'recipient_cnpj': destinatario.get('cnpj', ''),
                'recipient_cpf': destinatario.get('cpf', ''),
                'recipient_name': destinatario.get('nome', ''),
                'total_value': float(totais.get('valor_total', 0)) if totais.get('valor_total') else None,
                'tax_total': float(totais.get('total_impostos', 0)) if totais.get('total_impostos') else None,
                'issue_date': issue_date,
                'extracted_data': extracted_data,
                'classification_data': classification,
                'validation_data': validation,
                'is_valid': validation.get('is_valid', False),
                'has_errors': len(result.get('errors', [])) > 0 or len(validation.get('errors', [])) > 0,
                'processing_status': 'completed' if not result.get('errors') else 'failed',
                'batch_id': result.get('batch_id'),
                'batch_name': result.get('batch_name')
            }
            
            doc = DocumentRepository.create_document(session, document_data)
            # Guarda o ID antes de fechar a sessão (type casting para o LSP)
            doc_id: int = cast(int, doc.id)
            
            DocumentService._save_agent_logs(session, doc_id, result)
            
            return doc_id  # Retorna apenas o ID, não o objeto
            
        finally:
            session.close()
    
    @staticmethod
    def _save_agent_logs(session, document_id: int, result: Dict[str, Any]):
        """
        Salva logs de execução dos agentes
        """
        processed_data = result.get('processed_data', {})
        if processed_data.get('success'):
            AgentLogRepository.create_log(session, {
                'document_id': document_id,
                'agent_name': 'ProcessingAgent',
                'agent_status': 'completed',
                'output_data': {
                    'file_type': processed_data.get('file_type'),
                    'text_length': len(processed_data.get('text', ''))
                }
            })
        
        classification = result.get('classification', {})
        if classification:
            AgentLogRepository.create_log(session, {
                'document_id': document_id,
                'agent_name': 'ClassificationAgent',
                'agent_status': 'completed',
                'output_data': classification
            })
        
        extracted_data = result.get('extracted_data', {})
        if extracted_data:
            AgentLogRepository.create_log(session, {
                'document_id': document_id,
                'agent_name': 'ExtractionAgent',
                'agent_status': 'completed',
                'output_data': {
                    'items_count': len(extracted_data.get('itens', [])),
                    'has_emitente': bool(extracted_data.get('emitente')),
                    'has_destinatario': bool(extracted_data.get('destinatario'))
                }
            })
        
        validation = result.get('validation', {})
        if validation:
            AgentLogRepository.create_log(session, {
                'document_id': document_id,
                'agent_name': 'ValidationAgent',
                'agent_status': 'completed',
                'output_data': {
                    'is_valid': validation.get('is_valid'),
                    'errors_count': len(validation.get('errors', [])),
                    'warnings_count': len(validation.get('warnings', []))
                }
            })
    
    @staticmethod
    def get_all_documents(limit: int = 100, offset: int = 0) -> List[Document]:
        """
        Retorna todos os documentos processados
        """
        session = get_session()
        try:
            return DocumentRepository.get_all_documents(session, limit, offset)
        finally:
            session.close()
    
    @staticmethod
    def get_documents_by_batch_ids(batch_ids: List[str]) -> List[Document]:
        """
        Retorna documentos filtrados por IDs de lotes
        
        Args:
            batch_ids: Lista de IDs de lotes
        
        Returns:
            Lista de documentos dos lotes especificados
        """
        session = get_session()
        try:
            return DocumentRepository.get_documents_by_batch_ids(session, batch_ids)
        finally:
            session.close()
    
    @staticmethod
    def search_documents(query: str, document_type: Optional[str] = None) -> List[Document]:
        """
        Busca documentos por texto ou tipo
        """
        session = get_session()
        try:
            return DocumentRepository.search_documents(session, query, document_type)
        finally:
            session.close()
    
    @staticmethod
    def get_document_by_id(doc_id: int) -> Optional[Document]:
        """
        Retorna documento por ID
        """
        session = get_session()
        try:
            return DocumentRepository.get_document_by_id(session, doc_id)
        finally:
            session.close()
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """
        Retorna estatísticas gerais
        """
        session = get_session()
        try:
            return DocumentRepository.get_statistics(session)
        finally:
            session.close()
    
    @staticmethod
    def document_to_result_format(doc: Document) -> Dict[str, Any]:
        """
        Converte Document do banco para formato de resultado do workflow
        """
        return {
            'filename': doc.filename,
            'file_path': doc.file_path,
            'timestamp': doc.created_at.isoformat(),
            'processed_data': {
                'success': doc.processing_status == 'completed',
                'file_type': doc.file_type
            },
            'classification': doc.classification_data if doc.classification_data is not None else {},
            'extracted_data': doc.extracted_data if doc.extracted_data is not None else {},
            'validation': doc.validation_data if doc.validation_data is not None else {},
            'errors': [] if not bool(doc.has_errors) else ['Documento processado com erros'],
            'status': doc.processing_status,
            'db_id': doc.id
        }
    
    @staticmethod
    def delete_all_documents() -> int:
        """
        Deleta todos os documentos do banco de dados
        
        Returns:
            Número de documentos deletados
        """
        session = get_session()
        try:
            count = DocumentRepository.delete_all_documents(session)
            return count
        finally:
            session.close()
