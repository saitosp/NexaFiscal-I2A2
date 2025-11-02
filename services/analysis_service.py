"""
Analysis Service - Serviço de análise e geração de insights
"""
from typing import Dict, Any, List
from agents.analysis_agent import AnalysisAgent
from services.document_service import DocumentService
from utils.tax_config_loader import get_tax_config, get_enabled_tax_ids


class AnalysisService:
    """
    Serviço para análise de documentos e geração de insights
    """
    
    @staticmethod
    def analyze_document(document_id: int) -> Dict[str, Any]:
        """
        Analisa um documento específico
        
        Args:
            document_id: ID do documento
            
        Returns:
            Análise completa do documento
        """
        doc = DocumentService.get_document_by_id(document_id)
        
        if not doc:
            return {'error': 'Documento não encontrado'}
        
        document_data = {
            'extracted_data': doc.extracted_data or {},
            'validation_data': doc.validation_data or {},
            'classification_data': doc.classification_data or {}
        }
        
        try:
            agent = AnalysisAgent()
            analysis = agent.analyze_document(document_data)
            return analysis
        except ValueError as e:
            return {'error': str(e), 'note': 'Configure GROQ_API_KEY para habilitar análise com IA'}
        except Exception as e:
            return {'error': f'Erro na análise: {str(e)}'}
    
    @staticmethod
    def get_dashboard_data(batch_ids: List[str] = None) -> Dict[str, Any]:
        """
        Obtém dados agregados para o dashboard
        
        Args:
            batch_ids: Lista de IDs de lotes para filtrar (None = todos os documentos)
        
        Returns:
            Dados consolidados para visualização
        """
        try:
            if batch_ids:
                documents = DocumentService.get_documents_by_batch_ids(batch_ids)
            else:
                documents = DocumentService.get_all_documents(limit=1000)
            
            if not documents:
                return {
                    'overview': {
                        'total_documents': 0,
                        'total_value': 0,
                        'total_taxes': 0,
                        'average_value': 0,
                        'tax_burden_percent': 0
                    },
                    'by_type': {},
                    'top_issuers': [],
                    'monthly_trend': {},
                    'insights': ['📭 Nenhum documento processado ainda']
                }
            
            docs_data = [
                {
                    'document_type': doc.document_type,
                    'issuer_name': doc.issuer_name,
                    'total_value': doc.total_value,
                    'tax_total': doc.tax_total,
                    'is_valid': doc.is_valid,
                    'created_at': doc.created_at
                }
                for doc in documents
            ]
            
            agent = AnalysisAgent()
            analysis = agent.analyze_multiple_documents(docs_data)
            
            return analysis
            
        except ValueError as e:
            return {
                'error': str(e),
                'note': 'Configure GROQ_API_KEY para análise completa',
                'overview': {'total_documents': 0}
            }
        except Exception as e:
            return {
                'error': f'Erro ao gerar dashboard: {str(e)}',
                'overview': {'total_documents': 0}
            }
    
    @staticmethod
    def get_tax_analysis(batch_ids: List[str] = None) -> Dict[str, Any]:
        """
        Análise específica de impostos de todos os documentos
        Usa configuração dinâmica para suportar qualquer conjunto de impostos
        
        Args:
            batch_ids: Lista de IDs de lotes para filtrar (None = todos os documentos)
        
        Returns:
            Análise agregada de impostos (dinâmica baseada em tax_config.json)
        """
        if batch_ids:
            documents = DocumentService.get_documents_by_batch_ids(batch_ids)
        else:
            documents = DocumentService.get_all_documents(limit=1000)
        
        # Inicializa totais baseado na configuração de impostos
        tax_config = get_tax_config()
        tax_totals = {}
        for tax in tax_config.get_all_taxes(enabled_only=True):
            tax_id = tax['id']
            tax_totals[f'total_{tax_id}'] = 0.0
        
        if not documents:
            return tax_totals
        
        # Agrega valores de impostos dinamicamente
        for doc in documents:
            if doc.extracted_data:
                impostos = doc.extracted_data.get('impostos', {})
                for tax_id in tax_totals.keys():
                    # Remove o prefixo 'total_' para obter o ID do imposto
                    tax_key = tax_id.replace('total_', '')
                    tax_totals[tax_id] += float(impostos.get(tax_key, 0))
        
        return tax_totals
    
    @staticmethod
    def get_top_products(limit: int = 10, batch_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna os produtos mais frequentes
        
        Args:
            limit: Número máximo de produtos
            batch_ids: Lista de IDs de lotes para filtrar (None = todos os documentos)
            
        Returns:
            Lista de produtos ordenados por frequência
        """
        if batch_ids:
            documents = DocumentService.get_documents_by_batch_ids(batch_ids)
        else:
            documents = DocumentService.get_all_documents(limit=1000)
        
        product_counter = {}
        
        for doc in documents:
            if doc.extracted_data:
                itens = doc.extracted_data.get('itens', [])
                for item in itens:
                    descricao = item.get('descricao', '').strip()
                    if descricao:
                        if descricao not in product_counter:
                            product_counter[descricao] = {
                                'descricao': descricao,
                                'count': 0,
                                'total_value': 0,
                                'total_quantity': 0
                            }
                        
                        product_counter[descricao]['count'] += 1
                        product_counter[descricao]['total_value'] += float(item.get('valor_total', 0))
                        product_counter[descricao]['total_quantity'] += float(item.get('quantidade', 0))
        
        sorted_products = sorted(
            product_counter.values(),
            key=lambda x: x['count'],
            reverse=True
        )
        
        return sorted_products[:limit]
