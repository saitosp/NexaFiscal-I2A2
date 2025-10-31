"""
Agente de Classificação - Identifica o tipo de nota fiscal e formato do arquivo
"""
import os
from groq import Groq
from typing import Dict, Any
from utils.file_processor import get_file_type


class ClassificationAgent:
    """
    Agente responsável por classificar documentos fiscais
    """
    
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY não configurada. Configure a chave de API do Groq nas variáveis de ambiente.")
        
        self.client = Groq(api_key=api_key)
        # Usando Llama 4 Scout (modelo mais recente com capacidades multimodais)
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    def classify(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifica o tipo de nota fiscal e formato
        
        Args:
            state: Estado contendo informações do arquivo
            
        Returns:
            Estado atualizado com classificação
        """
        file_path = state.get('file_path')
        filename = state.get('filename')
        
        # Determina formato do arquivo
        file_format = get_file_type(filename)
        
        # Classificação inicial baseada no formato
        if file_format == 'xml':
            doc_type = self._classify_xml(state)
        elif file_format in ['pdf', 'image']:
            doc_type = self._classify_visual(state)
        else:
            doc_type = 'unknown'
        
        state['classification'] = {
            'file_format': file_format,
            'document_type': doc_type,
            'agent': 'ClassificationAgent'
        }
        
        state['status'] = 'classified'
        
        return state
    
    def _classify_xml(self, state: Dict[str, Any]) -> str:
        """
        Classifica um arquivo XML
        """
        xml_data = state.get('processed_data', {}).get('data', {})
        
        # Verifica estrutura do XML para identificar tipo
        if 'nfeProc' in xml_data or 'NFe' in xml_data:
            return 'NFe'
        elif 'cteProc' in xml_data or 'CTe' in xml_data:
            return 'CTe'
        elif 'nfse' in str(xml_data).lower():
            return 'NFSe'
        else:
            return 'XML Fiscal'
    
    def _classify_visual(self, state: Dict[str, Any]) -> str:
        """
        Classifica um documento visual (PDF ou imagem) usando IA
        """
        try:
            processed_data = state.get('processed_data', {})
            text = processed_data.get('text', '')
            image_base64 = processed_data.get('image_base64')
            
            # Monta prompt para classificação
            prompt = f"""Analise este documento fiscal brasileiro e identifique o tipo.

Tipos possíveis:
- NFe (Nota Fiscal Eletrônica)
- NFCe (Nota Fiscal ao Consumidor Eletrônica)
- SAT (Sistema Autenticador e Transmissor)
- CTe (Conhecimento de Transporte Eletrônico)
- NFSe (Nota Fiscal de Serviço Eletrônica)
- Cupom Fiscal
- Outro

Texto extraído (OCR):
{text[:1000]}

Responda APENAS com o tipo do documento (NFe, NFCe, SAT, CTe, NFSe, Cupom Fiscal ou Outro)."""

            # Se tiver imagem, usa análise visual
            if image_base64:
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        }
                    ]
                }]
            else:
                messages = [{"role": "user", "content": prompt}]
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=50,
                temperature=0.3
            )
            
            doc_type = completion.choices[0].message.content.strip()
            
            # Normaliza resposta
            doc_type_lower = doc_type.lower()
            if 'nfe' in doc_type_lower and 'nfce' not in doc_type_lower:
                return 'NFe'
            elif 'nfce' in doc_type_lower or 'consumidor' in doc_type_lower:
                return 'NFCe'
            elif 'sat' in doc_type_lower:
                return 'SAT'
            elif 'cte' in doc_type_lower or 'transporte' in doc_type_lower:
                return 'CTe'
            elif 'nfse' in doc_type_lower or 'serviço' in doc_type_lower:
                return 'NFSe'
            elif 'cupom' in doc_type_lower:
                return 'Cupom Fiscal'
            else:
                return doc_type
                
        except Exception as e:
            return f'Erro na classificação: {str(e)}'
