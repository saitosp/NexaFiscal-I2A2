"""
Batch Processing Service
Gerencia processamento em lote de múltiplos documentos
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from database.repository import DocumentRepository, ProcessingQueueRepository, BatchRepository
from database.session import get_session


class BatchService:
    """
    Serviço para gerenciar processamento em lote
    """
    
    @staticmethod
    def create_batch(files_data: List[Dict[str, Any]]) -> str:
        """
        Cria um novo lote de documentos para processamento
        
        Args:
            files_data: Lista de dicionários com informações dos arquivos
                       [{'filename': str, 'file_path': str, 'file_content': bytes}]
        
        Returns:
            batch_id: ID único do lote criado
        """
        batch_id = str(uuid.uuid4())
        
        for file_info in files_data:
            queue_item = ProcessingQueueRepository.create(
                batch_id=batch_id,
                filename=file_info['filename'],
                file_path=file_info.get('file_path'),
                priority=1,
                meta_data={
                    'file_size': len(file_info.get('file_content', b'')),
                    'created_at': datetime.now().isoformat()
                }
            )
        
        return batch_id
    
    @staticmethod
    def get_batch_status(batch_id: str) -> Dict[str, Any]:
        """
        Obtém status completo de um lote
        
        Returns:
            {
                'batch_id': str,
                'total': int,
                'pending': int,
                'processing': int,
                'completed': int,
                'failed': int,
                'items': List[Dict]
            }
        """
        items = ProcessingQueueRepository.get_by_batch(batch_id)
        
        stats = {
            'batch_id': batch_id,
            'total': len(items),
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'items': []
        }
        
        for item in items:
            stats[item.status] += 1
            
            stats['items'].append({
                'id': item.id,
                'filename': item.filename,
                'status': item.status,
                'document_id': item.document_id,
                'error_message': item.error_message,
                'attempts': item.attempts,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'started_at': item.started_at.isoformat() if item.started_at else None,
                'completed_at': item.completed_at.isoformat() if item.completed_at else None
            })
        
        return stats
    
    @staticmethod
    def get_next_pending(limit: int = 10) -> List[Any]:
        """
        Busca próximos documentos pendentes para processar
        
        Args:
            limit: Número máximo de itens a retornar
        
        Returns:
            Lista de items da fila
        """
        return ProcessingQueueRepository.get_pending(limit)
    
    @staticmethod
    def mark_processing(queue_id: int) -> None:
        """
        Marca item como em processamento
        """
        ProcessingQueueRepository.update_status(
            queue_id,
            'processing',
            started_at=datetime.now()
        )
    
    @staticmethod
    def mark_completed(queue_id: int, document_id: int) -> None:
        """
        Marca item como concluído
        """
        ProcessingQueueRepository.update_status(
            queue_id,
            'completed',
            document_id=document_id,
            completed_at=datetime.now()
        )
    
    @staticmethod
    def mark_failed(queue_id: int, error_message: str) -> None:
        """
        Marca item como falho
        """
        ProcessingQueueRepository.update_status(
            queue_id,
            'failed',
            error_message=error_message,
            completed_at=datetime.now()
        )
    
    @staticmethod
    def retry_failed(batch_id: str) -> int:
        """
        Reprocessa todos os itens com falha de um lote
        
        Returns:
            Número de itens resetados para pendente
        """
        items = ProcessingQueueRepository.get_by_batch(batch_id)
        count = 0
        
        for item in items:
            if item.status == 'failed' and item.attempts < 3:
                ProcessingQueueRepository.update_status(
                    item.id,
                    'pending',
                    error_message=None
                )
                count += 1
        
        return count
    
    @staticmethod
    def get_all_batches(limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lista todos os lotes criados
        
        Returns:
            Lista de lotes com estatísticas
        """
        all_items = ProcessingQueueRepository.get_all(limit=1000)
        
        batches_dict = {}
        
        for item in all_items:
            batch_id = item.batch_id
            
            if batch_id not in batches_dict:
                batches_dict[batch_id] = {
                    'batch_id': batch_id,
                    'total': 0,
                    'pending': 0,
                    'processing': 0,
                    'completed': 0,
                    'failed': 0,
                    'created_at': item.created_at
                }
            
            batches_dict[batch_id]['total'] += 1
            batches_dict[batch_id][item.status] += 1
            
            if item.created_at and item.created_at < batches_dict[batch_id]['created_at']:
                batches_dict[batch_id]['created_at'] = item.created_at
        
        batches = list(batches_dict.values())
        batches.sort(key=lambda x: x['created_at'], reverse=True)
        
        return batches[:limit]
    
    @staticmethod
    def create_batch_metadata(batch_name: str, origin: str = 'manual_upload') -> str:
        """
        Cria metadados de um novo lote na tabela batches
        
        Args:
            batch_name: Nome descritivo do lote
            origin: Origem do lote ('csv_import', 'manual_upload', 'api')
        
        Returns:
            batch_id: ID único do lote criado
        """
        session = get_session()
        try:
            batch_id = str(uuid.uuid4())
            
            batch_data = {
                'batch_id': batch_id,
                'batch_name': batch_name,
                'origin': origin,
                'document_count': 0,
                'total_value': 0.0
            }
            
            BatchRepository.create_batch(session, batch_data)
            return batch_id
        finally:
            session.close()
    
    @staticmethod
    def get_all_batch_metadata(limit: int = 100) -> List[Dict[str, Any]]:
        """
        Lista todos os lotes com metadados completos
        
        Returns:
            Lista de lotes ordenados por data de criação
        """
        session = get_session()
        try:
            batches = BatchRepository.get_all_batches(session, limit=limit)
            
            result = []
            for batch in batches:
                result.append({
                    'batch_id': batch.batch_id,
                    'batch_name': batch.batch_name,
                    'origin': batch.origin,
                    'document_count': batch.document_count,
                    'total_value': batch.total_value,
                    'created_at': batch.created_at.isoformat() if batch.created_at else None
                })
            
            return result
        finally:
            session.close()
    
    @staticmethod
    def update_batch_statistics(batch_id: str) -> bool:
        """
        Atualiza estatísticas de um lote (document_count e total_value)
        baseado nos documentos associados
        
        Args:
            batch_id: ID do lote
        
        Returns:
            True se atualizou com sucesso, False caso contrário
        """
        session = get_session()
        try:
            batch = BatchRepository.update_batch_stats(session, batch_id)
            return batch is not None
        finally:
            session.close()
    
    @staticmethod
    def get_batch_summary(batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Retorna resumo completo de um lote
        
        Returns:
            Dicionário com informações do lote ou None se não encontrado
        """
        session = get_session()
        try:
            batch = BatchRepository.get_batch_by_id(session, batch_id)
            
            if not batch:
                return None
            
            return {
                'batch_id': batch.batch_id,
                'batch_name': batch.batch_name,
                'origin': batch.origin,
                'document_count': batch.document_count,
                'total_value': batch.total_value,
                'created_at': batch.created_at.isoformat() if batch.created_at else None,
                'updated_at': batch.updated_at.isoformat() if batch.updated_at else None
            }
        finally:
            session.close()
