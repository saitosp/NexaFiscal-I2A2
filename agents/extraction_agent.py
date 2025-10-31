"""
Agente de Extração - Extrai dados estruturados de notas fiscais
"""
import os
import json
from groq import Groq
from typing import Dict, Any
import xmltodict
from utils.tax_config_loader import get_tax_config, get_enabled_tax_ids


class ExtractionAgent:
    """
    Agente responsável por extrair dados estruturados de notas fiscais
    """
    
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY não configurada. Configure a chave de API do Groq nas variáveis de ambiente.")
        
        self.client = Groq(api_key=api_key)
        # Usando Llama 4 Scout (modelo mais recente)
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    def extract(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai dados estruturados da nota fiscal
        
        Args:
            state: Estado contendo informações do documento
            
        Returns:
            Estado atualizado com dados extraídos
        """
        classification = state.get('classification', {})
        file_format = classification.get('file_format')
        
        # Estratégia de extração baseada no formato
        if file_format == 'xml':
            extracted_data = self._extract_from_xml(state)
        elif file_format in ['pdf', 'image']:
            extracted_data = self._extract_from_visual(state)
        else:
            extracted_data = {'error': 'Formato não suportado'}
        
        state['extracted_data'] = extracted_data
        state['status'] = 'extracted'
        
        return state
    
    def _extract_from_xml(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai dados de um arquivo XML de NFe
        """
        try:
            xml_data = state.get('processed_data', {}).get('data', {})
            
            # Extrai dados estruturados do XML
            extracted = {
                'fonte': 'XML',
                'emitente': {},
                'destinatario': {},
                'itens': [],
                'totais': {},
                'impostos': {},
                'informacoes_adicionais': {}
            }
            
            # Navega pela estrutura do XML (NFe)
            if 'nfeProc' in xml_data:
                nfe = xml_data['nfeProc']['NFe']['infNFe']
            elif 'NFe' in xml_data:
                nfe = xml_data['NFe']['infNFe']
            else:
                return extracted
            
            # Dados do emitente
            if 'emit' in nfe:
                emit = nfe['emit']
                extracted['emitente'] = {
                    'cnpj': emit.get('CNPJ', ''),
                    'razao_social': emit.get('xNome', ''),
                    'nome_fantasia': emit.get('xFant', ''),
                    'endereco': self._format_endereco(emit.get('enderEmit', {})),
                    'ie': emit.get('IE', ''),
                    'im': emit.get('IM', '')
                }
            
            # Dados do destinatário
            if 'dest' in nfe:
                dest = nfe['dest']
                extracted['destinatario'] = {
                    'cnpj': dest.get('CNPJ', ''),
                    'cpf': dest.get('CPF', ''),
                    'nome': dest.get('xNome', ''),
                    'endereco': self._format_endereco(dest.get('enderDest', {})),
                    'ie': dest.get('IE', '')
                }
            
            # Itens da nota
            if 'det' in nfe:
                itens = nfe['det'] if isinstance(nfe['det'], list) else [nfe['det']]
                for item in itens:
                    prod = item.get('prod', {})
                    imposto = item.get('imposto', {})
                    
                    # Extrai CST dos impostos
                    cst_icms = self._extract_cst_icms(imposto)
                    cst_ipi = self._extract_cst_from_tax(imposto.get('IPI', {}))
                    cst_pis = self._extract_cst_from_tax(imposto.get('PIS', {}))
                    cst_cofins = self._extract_cst_from_tax(imposto.get('COFINS', {}))
                    
                    extracted['itens'].append({
                        'codigo': prod.get('cProd', ''),
                        'descricao': prod.get('xProd', ''),
                        'ncm': prod.get('NCM', ''),
                        'cfop': prod.get('CFOP', ''),
                        'cst_icms': cst_icms,
                        'cst_ipi': cst_ipi,
                        'cst_pis': cst_pis,
                        'cst_cofins': cst_cofins,
                        'unidade': prod.get('uCom', ''),
                        'quantidade': float(prod.get('qCom', 0)),
                        'valor_unitario': float(prod.get('vUnCom', 0)),
                        'valor_total': float(prod.get('vProd', 0))
                    })
            
            # Totais
            if 'total' in nfe:
                icms_tot = nfe['total'].get('ICMSTot', {})
                extracted['totais'] = {
                    'valor_produtos': float(icms_tot.get('vProd', 0)),
                    'valor_frete': float(icms_tot.get('vFrete', 0)),
                    'valor_seguro': float(icms_tot.get('vSeg', 0)),
                    'valor_desconto': float(icms_tot.get('vDesc', 0)),
                    'valor_total': float(icms_tot.get('vNF', 0))
                }
                
                # Impostos - Extração dinâmica baseada na configuração
                extracted['impostos'] = self._extract_taxes_from_xml(icms_tot)
            
            # Informações da NFe
            if 'ide' in nfe:
                ide = nfe['ide']
                extracted['informacoes_adicionais'] = {
                    'numero': ide.get('nNF', ''),
                    'serie': ide.get('serie', ''),
                    'data_emissao': ide.get('dhEmi', ''),
                    'chave_acesso': nfe.get('@Id', '').replace('NFe', '')
                }
            
            return extracted
            
        except Exception as e:
            return {'error': f'Erro ao extrair XML: {str(e)}'}
    
    def _extract_from_visual(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai dados de documentos visuais usando IA
        """
        try:
            processed_data = state.get('processed_data', {})
            text = processed_data.get('text', '')
            image_base64 = processed_data.get('image_base64')
            
            # Prompt estruturado para extração (dinâmico baseado em configuração)
            prompt = self._build_extraction_prompt(text)

            # Monta mensagem com imagem se disponível
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
                max_tokens=2048,
                temperature=0.3
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            # Tenta extrair JSON da resposta
            try:
                # Remove markdown code blocks se existirem
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()
                
                extracted_data = json.loads(response_text)
                extracted_data['fonte'] = 'IA + OCR'
                return extracted_data
            except json.JSONDecodeError:
                return {
                    'error': 'Falha ao extrair JSON',
                    'raw_response': response_text,
                    'fonte': 'IA + OCR'
                }
                
        except Exception as e:
            return {'error': f'Erro na extração visual: {str(e)}'}
    
    def _format_endereco(self, endereco: Dict) -> str:
        """
        Formata endereço a partir do dicionário
        """
        if not endereco:
            return ''
        
        partes = [
            endereco.get('xLgr', ''),
            endereco.get('nro', ''),
            endereco.get('xCpl', ''),
            endereco.get('xBairro', ''),
            endereco.get('xMun', ''),
            endereco.get('UF', ''),
            endereco.get('CEP', '')
        ]
        
        return ', '.join([p for p in partes if p])
    
    def _extract_cst_icms(self, imposto: Dict) -> str:
        """
        Extrai CST do ICMS (pode ser CST ou CSOSN para Simples Nacional)
        """
        if not imposto or 'ICMS' not in imposto:
            return ''
        
        icms = imposto['ICMS']
        
        # Tenta todas as variações possíveis de ICMS
        # ICMS00, ICMS10, ICMS20, ICMS30, ICMS40, ICMS51, ICMS60, ICMS70, ICMS90
        for key in icms.keys():
            if key.startswith('ICMS'):
                icms_data = icms[key]
                # Regime Normal: CST
                if 'CST' in icms_data:
                    return icms_data['CST']
                # Simples Nacional: CSOSN
                elif 'CSOSN' in icms_data:
                    return icms_data['CSOSN']
        
        return ''
    
    def _extract_cst_from_tax(self, tax_data: Dict) -> str:
        """
        Extrai CST de um imposto genérico (IPI, PIS, COFINS)
        """
        if not tax_data:
            return ''
        
        # Navega pelas chaves do imposto para encontrar CST
        for key, value in tax_data.items():
            if isinstance(value, dict) and 'CST' in value:
                return value['CST']
        
        return ''
    
    def _extract_taxes_from_xml(self, icms_tot: Dict) -> Dict[str, float]:
        """
        Extrai impostos do XML usando configuração dinâmica
        
        Args:
            icms_tot: Dicionário com totais do ICMS do XML
        
        Returns:
            Dicionário com valores dos impostos configurados
        """
        tax_config = get_tax_config()
        taxes = {}
        
        for tax in tax_config.get_all_taxes(enabled_only=True):
            tax_id = tax['id']
            xml_fields = tax.get('xml_fields', [])
            
            # Soma valores de todos os campos XML do imposto
            total_value = 0.0
            for field in xml_fields:
                total_value += float(icms_tot.get(field, 0))
            
            taxes[tax_id] = total_value
        
        return taxes
    
    def _build_extraction_prompt(self, text: str) -> str:
        """
        Constrói prompt de extração dinamicamente baseado na configuração de impostos
        
        Args:
            text: Texto extraído por OCR
        
        Returns:
            Prompt formatado para o modelo de IA
        """
        tax_config = get_tax_config()
        
        # Gera campos de impostos dinamicamente
        tax_fields = []
        for tax in tax_config.get_all_taxes(enabled_only=True):
            tax_id = tax['id']
            tax_name = tax['name']
            tax_desc = tax.get('full_name', tax_name)
            tax_fields.append(f'    "{tax_id}": número  // {tax_desc}')
        
        taxes_json = ',\n'.join(tax_fields)
        
        prompt = f"""Extraia as seguintes informações desta nota fiscal brasileira e retorne em formato JSON:

{{
  "emitente": {{
    "cnpj": "CNPJ do emitente",
    "razao_social": "Razão social",
    "nome_fantasia": "Nome fantasia (se houver)",
    "endereco": "Endereço completo",
    "ie": "Inscrição Estadual"
  }},
  "destinatario": {{
    "cnpj": "CNPJ do destinatário",
    "cpf": "CPF (se for pessoa física)",
    "nome": "Nome/Razão social",
    "endereco": "Endereço"
  }},
  "itens": [
    {{
      "descricao": "Descrição do produto/serviço",
      "quantidade": número,
      "valor_unitario": número,
      "valor_total": número,
      "cfop": "CFOP do item",
      "cst_icms": "CST ou CSOSN do ICMS",
      "cst_ipi": "CST do IPI (se houver)",
      "cst_pis": "CST do PIS (se houver)",
      "cst_cofins": "CST do COFINS (se houver)"
    }}
  ],
  "totais": {{
    "valor_produtos": número,
    "valor_total": número,
    "valor_desconto": número
  }},
  "impostos": {{
{taxes_json}
  }},
  "informacoes_adicionais": {{
    "numero": "Número da nota",
    "serie": "Série",
    "data_emissao": "Data de emissão",
    "chave_acesso": "Chave de acesso de 44 dígitos"
  }}
}}

Texto OCR:
{text[:2000]}

Retorne APENAS o JSON válido, sem texto adicional."""

        return prompt
