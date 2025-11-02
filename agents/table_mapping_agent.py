"""
Table Mapping Agent - Detecta automaticamente mapeamento de colunas usando LLM
"""
import os
import json
from typing import Dict, List, Any
from groq import Groq


class TableMappingAgent:
    """
    Agente que usa LLM para detectar automaticamente o mapeamento
    entre colunas da tabela e campos de nota fiscal
    """
    
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        self.is_available = bool(api_key)
        
        if not self.is_available:
            print("⚠️ GROQ_API_KEY não configurada. Usando mapeamento básico por padrões.")
            self.client = None
            self.model = None
        else:
            self.client = Groq(api_key=api_key)
            self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
        
        # Campos esperados em uma nota fiscal
        self.fiscal_fields = {
            'emitente_nome': 'Nome ou razão social do emitente/fornecedor',
            'emitente_cnpj': 'CNPJ ou CPF do emitente/fornecedor',
            'destinatario_nome': 'Nome ou razão social do destinatário/cliente',
            'destinatario_cnpj': 'CNPJ ou CPF do destinatário/cliente',
            'numero_nota': 'Número da nota fiscal',
            'serie': 'Série da nota fiscal',
            'data_emissao': 'Data de emissão da nota',
            'valor_total': 'Valor total da nota fiscal',
            'valor_produtos': 'Valor dos produtos/serviços',
            'icms': 'Valor do ICMS',
            'pis': 'Valor do PIS',
            'cofins': 'Valor do COFINS',
            'ipi': 'Valor do IPI',
            'chave_acesso': 'Chave de acesso da NFe (44 dígitos)',
            'tipo_documento': 'Tipo do documento fiscal (NFe, NFCe, SAT, etc)'
        }
    
    def auto_map_columns(
        self, 
        columns: List[str],
        sample_data: List[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Mapeia automaticamente colunas usando LLM
        
        Args:
            columns: Lista de nomes de colunas
            sample_data: Amostra de dados (opcional, melhora precisão)
            
        Returns:
            Dict com mapeamento {campo_fiscal: coluna_tabela}
        """
        
        # Fallback se Groq não disponível
        if not self.is_available or not self.client:
            return self._basic_mapping(columns)
        
        # Monta contexto com dados de exemplo se disponível
        sample_context = ""
        if sample_data and len(sample_data) > 0:
            sample_context = "\n\nEXEMPLO DE DADOS (primeiras 3 linhas):\n"
            for i, row in enumerate(sample_data[:3], 1):
                sample_context += f"\nLinha {i}:\n"
                for col in columns:
                    value = row.get(col, '')
                    sample_context += f"  {col}: {value}\n"
        
        system_prompt = f"""Você é um especialista em análise de planilhas de notas fiscais brasileiras.

CAMPOS FISCAIS ESPERADOS:
{json.dumps(self.fiscal_fields, indent=2, ensure_ascii=False)}

TAREFA:
Analise os nomes das colunas fornecidas e mapeie para os campos fiscais correspondentes.
Considere variações de nomes, abreviações e sinônimos comuns em português brasileiro.

Retorne APENAS um JSON no formato:
{{
    "emitente_nome": "nome_da_coluna_correspondente",
    "emitente_cnpj": "nome_da_coluna_correspondente",
    ...
}}

Se uma coluna não tiver correspondência, use null.
"""

        user_prompt = f"""COLUNAS DA PLANILHA:
{json.dumps(columns, indent=2, ensure_ascii=False)}
{sample_context}

Retorne o mapeamento em JSON:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extrai JSON da resposta
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            mapping = json.loads(content)
            
            # Remove valores null
            mapping = {k: v for k, v in mapping.items() if v is not None}
            
            # Valida que colunas mapeadas existem
            valid_mapping = {}
            for field, column in mapping.items():
                if column in columns:
                    valid_mapping[field] = column
            
            return valid_mapping
            
        except Exception as e:
            print(f"Erro ao mapear colunas com LLM: {e}")
            return self._basic_mapping(columns)
    
    def _basic_mapping(self, columns: List[str]) -> Dict[str, str]:
        """
        Mapeamento básico baseado em padrões comuns (fallback)
        
        Args:
            columns: Lista de colunas
            
        Returns:
            Dict com mapeamento básico
        """
        mapping = {}
        
        # Padrões de busca (case-insensitive)
        patterns = {
            'emitente_nome': ['emitente', 'fornecedor', 'razao_social_emitente', 'nome_emitente', 'remetente'],
            'emitente_cnpj': ['cnpj_emitente', 'cnpj_fornecedor', 'cpf_emitente', 'doc_emitente'],
            'destinatario_nome': ['destinatario', 'cliente', 'razao_social_destinatario', 'nome_destinatario'],
            'destinatario_cnpj': ['cnpj_destinatario', 'cnpj_cliente', 'cpf_destinatario', 'doc_destinatario'],
            'numero_nota': ['numero', 'nf', 'numero_nf', 'nota', 'numero_nota', 'num_nf'],
            'serie': ['serie', 'serie_nf'],
            'data_emissao': ['data', 'data_emissao', 'dt_emissao', 'emissao', 'data_nf'],
            'valor_total': ['valor_total', 'total', 'valor_nf', 'vl_total', 'vlr_total'],
            'valor_produtos': ['valor_produtos', 'produtos', 'vl_produtos', 'vlr_produtos'],
            'icms': ['icms', 'valor_icms', 'vl_icms', 'vlr_icms'],
            'pis': ['pis', 'valor_pis', 'vl_pis', 'vlr_pis'],
            'cofins': ['cofins', 'valor_cofins', 'vl_cofins', 'vlr_cofins'],
            'ipi': ['ipi', 'valor_ipi', 'vl_ipi', 'vlr_ipi'],
            'chave_acesso': ['chave', 'chave_acesso', 'chave_nfe', 'access_key', 'chave_nota'],
            'tipo_documento': ['tipo', 'tipo_documento', 'tipo_nf', 'modelo', 'tipo_nota']
        }
        
        # Faz matching de colunas
        for field, possible_names in patterns.items():
            for col in columns:
                col_lower = col.lower().replace(' ', '_').replace('-', '_')
                for pattern in possible_names:
                    if pattern in col_lower or col_lower in pattern:
                        mapping[field] = col
                        break
                if field in mapping:
                    break
        
        return mapping
    
    def validate_mapping(
        self, 
        mapping: Dict[str, str],
        required_fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Valida se o mapeamento contém campos obrigatórios
        
        Args:
            mapping: Mapeamento atual
            required_fields: Campos obrigatórios (None = lista padrão)
            
        Returns:
            Dict com resultado da validação
        """
        if required_fields is None:
            required_fields = ['valor_total']  # Mínimo: valor total
        
        missing = []
        for field in required_fields:
            if field not in mapping or not mapping[field]:
                missing.append(field)
        
        is_valid = len(missing) == 0
        
        return {
            'is_valid': is_valid,
            'missing_fields': missing,
            'mapped_fields': list(mapping.keys()),
            'mapping_count': len(mapping)
        }
    
    def suggest_improvements(
        self,
        mapping: Dict[str, str],
        columns: List[str]
    ) -> List[str]:
        """
        Sugere melhorias no mapeamento
        
        Args:
            mapping: Mapeamento atual
            columns: Colunas disponíveis
            
        Returns:
            Lista de sugestões
        """
        suggestions = []
        
        # Verifica campos importantes não mapeados
        important_fields = [
            'emitente_nome', 'emitente_cnpj',
            'destinatario_nome', 'destinatario_cnpj',
            'valor_total', 'numero_nota'
        ]
        
        for field in important_fields:
            if field not in mapping:
                suggestions.append(
                    f"Campo '{field}' não foi mapeado. "
                    f"Verifique se existe coluna correspondente."
                )
        
        # Verifica colunas não utilizadas
        used_columns = set(mapping.values())
        unused_columns = [col for col in columns if col not in used_columns]
        
        if len(unused_columns) > 0:
            suggestions.append(
                f"{len(unused_columns)} coluna(s) não foram utilizadas: "
                f"{', '.join(unused_columns[:5])}"
            )
        
        return suggestions
