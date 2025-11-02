"""
Analysis Agent - Gera insights e análises fiscais a partir dos dados extraídos
"""
from typing import Dict, Any, List
from collections import Counter
from datetime import datetime, timedelta
import os


class AnalysisAgent:
    """
    Agente especializado em análise de dados fiscais
    Gera insights, estatísticas e relatórios automatizados
    """
    
    def __init__(self):
        pass
    
    def analyze_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa um documento individual e gera insights
        
        Args:
            document_data: Dados completos do documento
            
        Returns:
            Dict com insights e análises
        """
        extracted = document_data.get('extracted_data', {})
        
        analysis = {
            'summary': self._generate_summary(extracted),
            'tax_analysis': self._analyze_taxes(extracted),
            'items_analysis': self._analyze_items(extracted),
            'financial_summary': self._financial_summary(extracted),
            'compliance_check': self._check_compliance(document_data),
            'recommendations': self._generate_recommendations(extracted)
        }
        
        return analysis
    
    def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera resumo executivo do documento
        """
        emitente = data.get('emitente', {})
        destinatario = data.get('destinatario', {})
        totais = data.get('totais', {})
        itens = data.get('itens', [])
        
        return {
            'emitente': emitente.get('razao_social', 'N/A'),
            'destinatario': destinatario.get('nome', 'N/A'),
            'num_itens': len(itens),
            'valor_total': totais.get('total', 0),
            'impostos_totais': totais.get('impostos_totais', 0),
            'margem_impostos': self._calculate_tax_margin(totais)
        }
    
    def _analyze_taxes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análise detalhada de impostos
        """
        impostos = data.get('impostos', {})
        totais = data.get('totais', {})
        
        total_produtos = float(totais.get('produtos', 0)) or 1
        
        tax_breakdown = {
            'icms': {
                'valor': float(impostos.get('icms', 0)),
                'percentual': (float(impostos.get('icms', 0)) / total_produtos) * 100
            },
            'ipi': {
                'valor': float(impostos.get('ipi', 0)),
                'percentual': (float(impostos.get('ipi', 0)) / total_produtos) * 100
            },
            'pis': {
                'valor': float(impostos.get('pis', 0)),
                'percentual': (float(impostos.get('pis', 0)) / total_produtos) * 100
            },
            'cofins': {
                'valor': float(impostos.get('cofins', 0)),
                'percentual': (float(impostos.get('cofins', 0)) / total_produtos) * 100
            }
        }
        
        total_impostos = sum(t['valor'] for t in tax_breakdown.values())
        carga_tributaria = (total_impostos / total_produtos) * 100 if total_produtos > 0 else 0
        
        return {
            'breakdown': tax_breakdown,
            'total_impostos': total_impostos,
            'carga_tributaria_percent': round(carga_tributaria, 2),
            'maior_imposto': max(tax_breakdown.items(), key=lambda x: x[1]['valor'])[0] if tax_breakdown else None
        }
    
    def _analyze_items(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análise de produtos/itens
        """
        itens = data.get('itens', [])
        
        if not itens:
            return {'total_itens': 0}
        
        valores = [float(item.get('valor_total', 0)) for item in itens]
        quantidades = [float(item.get('quantidade', 0)) for item in itens]
        
        item_mais_caro = max(itens, key=lambda x: float(x.get('valor_total', 0))) if itens else None
        item_maior_quantidade = max(itens, key=lambda x: float(x.get('quantidade', 0))) if itens else None
        
        return {
            'total_itens': len(itens),
            'valor_medio_item': sum(valores) / len(valores) if valores else 0,
            'quantidade_total': sum(quantidades),
            'item_mais_caro': {
                'descricao': item_mais_caro.get('descricao', 'N/A') if item_mais_caro else None,
                'valor': item_mais_caro.get('valor_total', 0) if item_mais_caro else 0
            },
            'item_maior_quantidade': {
                'descricao': item_maior_quantidade.get('descricao', 'N/A') if item_maior_quantidade else None,
                'quantidade': item_maior_quantidade.get('quantidade', 0) if item_maior_quantidade else 0
            }
        }
    
    def _financial_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resumo financeiro
        """
        totais = data.get('totais', {})
        
        valor_produtos = float(totais.get('produtos', 0))
        desconto = float(totais.get('desconto', 0))
        frete = float(totais.get('frete', 0))
        seguro = float(totais.get('seguro', 0))
        outras_despesas = float(totais.get('outras_despesas', 0))
        impostos = float(totais.get('impostos_totais', 0))
        valor_total = float(totais.get('total', 0))
        
        return {
            'valor_bruto': valor_produtos,
            'descontos': desconto,
            'acrescimos': frete + seguro + outras_despesas,
            'impostos': impostos,
            'valor_liquido': valor_total - impostos,
            'margem_liquida_percent': ((valor_total - impostos) / valor_total * 100) if valor_total > 0 else 0
        }
    
    def _check_compliance(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica conformidade fiscal
        """
        validation = document_data.get('validation_data', {})
        
        return {
            'is_compliant': validation.get('is_valid', False),
            'num_issues': len(validation.get('errors', [])) + len(validation.get('warnings', [])),
            'errors': validation.get('errors', []),
            'warnings': validation.get('warnings', [])
        }
    
    def _generate_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """
        Gera recomendações baseadas na análise
        """
        recommendations = []
        
        totais = data.get('totais', {})
        impostos = data.get('impostos', {})
        
        total_produtos = float(totais.get('produtos', 0))
        total_impostos = sum(float(impostos.get(k, 0)) for k in ['icms', 'ipi', 'pis', 'cofins'])
        
        if total_produtos > 0:
            carga_tributaria = (total_impostos / total_produtos) * 100
            
            if carga_tributaria > 30:
                recommendations.append("⚠️ Carga tributária acima de 30% - Considere revisar o regime tributário")
            
            if carga_tributaria > 40:
                recommendations.append("🔴 Carga tributária muito alta (>40%) - Recomenda-se consultoria fiscal")
        
        desconto = float(totais.get('desconto', 0))
        if desconto > total_produtos * 0.15:
            recommendations.append("💡 Desconto significativo aplicado (>15%) - Verifique margem de lucro")
        
        itens = data.get('itens', [])
        if len(itens) > 50:
            recommendations.append("📊 Nota fiscal com muitos itens - Considere uso de sistema ERP para gestão")
        
        if not recommendations:
            recommendations.append("✅ Documento dentro dos padrões normais")
        
        return recommendations
    
    def _calculate_tax_margin(self, totais: Dict[str, Any]) -> float:
        """
        Calcula margem de impostos
        """
        total = float(totais.get('total', 0))
        impostos = float(totais.get('impostos_totais', 0))
        
        if total > 0:
            return round((impostos / total) * 100, 2)
        return 0.0
    
    def analyze_multiple_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Análise agregada de múltiplos documentos
        
        Args:
            documents: Lista de documentos completos do banco
            
        Returns:
            Análise consolidada
        """
        if not documents:
            return {'error': 'Nenhum documento para analisar'}
        
        total_documents = len(documents)
        total_value = sum(float(doc.get('total_value', 0) or 0) for doc in documents)
        total_taxes = sum(float(doc.get('tax_total', 0) or 0) for doc in documents)
        
        document_types = Counter(doc.get('document_type') for doc in documents if doc.get('document_type'))
        
        issuers = Counter(doc.get('issuer_name') for doc in documents if doc.get('issuer_name'))
        top_issuers = issuers.most_common(5)
        
        monthly_data = self._group_by_month(documents)
        
        return {
            'overview': {
                'total_documents': total_documents,
                'total_value': total_value,
                'total_taxes': total_taxes,
                'average_value': total_value / total_documents if total_documents > 0 else 0,
                'tax_burden_percent': (total_taxes / total_value * 100) if total_value > 0 else 0
            },
            'by_type': dict(document_types),
            'top_issuers': [{'name': name, 'count': count} for name, count in top_issuers],
            'monthly_trend': monthly_data,
            'insights': self._generate_aggregate_insights(documents)
        }
    
    def _group_by_month(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Agrupa documentos por mês
        """
        monthly = {}
        
        for doc in documents:
            created_at = doc.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    month_key = created_at[:7]
                else:
                    month_key = created_at.strftime('%Y-%m')
                
                if month_key not in monthly:
                    monthly[month_key] = {'count': 0, 'total_value': 0, 'total_taxes': 0}
                
                monthly[month_key]['count'] += 1
                monthly[month_key]['total_value'] += float(doc.get('total_value', 0) or 0)
                monthly[month_key]['total_taxes'] += float(doc.get('tax_total', 0) or 0)
        
        return dict(sorted(monthly.items()))
    
    def _generate_aggregate_insights(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Gera insights da análise agregada
        """
        insights = []
        
        total_value = sum(float(doc.get('total_value', 0) or 0) for doc in documents)
        total_taxes = sum(float(doc.get('tax_total', 0) or 0) for doc in documents)
        
        if total_value > 0:
            avg_tax_burden = (total_taxes / total_value) * 100
            insights.append(f"📊 Carga tributária média: {avg_tax_burden:.1f}%")
        
        valid_count = sum(1 for doc in documents if doc.get('is_valid'))
        if valid_count < len(documents):
            error_rate = ((len(documents) - valid_count) / len(documents)) * 100
            insights.append(f"⚠️ Taxa de documentos com erros: {error_rate:.1f}%")
        
        document_types = Counter(doc.get('document_type') for doc in documents if doc.get('document_type'))
        if document_types:
            most_common = document_types.most_common(1)[0]
            insights.append(f"📄 Tipo mais comum: {most_common[0]} ({most_common[1]} documentos)")
        
        return insights
