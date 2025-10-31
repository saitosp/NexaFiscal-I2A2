"""
Integration Agent
Coordena integração com portais externos (SEFAZ) para download de XMLs
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
from zeep import Client
from zeep.transports import Transport
from requests import Session
import tempfile

from services.sefaz_service import SefazService


class IntegrationAgent:
    """
    Agente de Integração com Portais Externos
    Gerencia conexão com SEFAZ para download de XMLs oficiais
    """
    
    def __init__(self):
        """
        Inicializa o agente
        """
        self.sefaz_service = SefazService()
    
    def get_nfe_distribution_service_url(self, uf: str, environment: str = 'homologation') -> str:
        """
        Retorna URL do serviço de distribuição DFe por UF
        
        Args:
            uf: Sigla do estado (SP, RJ, MG, etc)
            environment: 'production' ou 'homologation'
        """
        # URLs do serviço NFeDistribuicaoDFe (Portal Nacional)
        if environment == 'production':
            return "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl"
        else:
            return "https://hom1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl"
    
    def consultar_nfe_destinadas(
        self,
        credential_id: int,
        password: str,
        cnpj: str,
        uf: str = 'SP',
        environment: str = 'homologation',
        ultimo_nsu: str = '0'
    ) -> Dict[str, Any]:
        """
        Consulta notas fiscais destinadas a um CNPJ
        
        Args:
            credential_id: ID da credencial do certificado
            password: Senha do certificado
            cnpj: CNPJ do destinatário (apenas números)
            uf: Sigla do estado
            environment: Ambiente (production/homologation)
            ultimo_nsu: Último NSU consultado (0 para buscar desde o início)
        
        Returns:
            {
                'success': bool,
                'message': str,
                'documents': List[Dict],
                'ultimo_nsu': str
            }
        """
        try:
            # Recupera certificado
            cert_pem, key_pem = self.sefaz_service.get_certificate_data(credential_id, password)
            
            # Cria arquivos temporários para certificado e chave
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as cert_file:
                cert_file.write(cert_pem)
                cert_path = cert_file.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as key_file:
                key_file.write(key_pem)
                key_path = key_file.name
            
            try:
                # Configura sessão com certificado
                session = Session()
                session.cert = (cert_path, key_path)
                session.verify = True  # Verifica SSL
                
                transport = Transport(session=session)
                
                # URL do serviço
                wsdl_url = self.get_nfe_distribution_service_url(uf, environment)
                
                # Cliente SOAP
                client = Client(wsdl_url, transport=transport)
                
                # Monta requisição de distribuição DFe
                # Nota: Esta é uma implementação simplificada
                # Em produção, seria necessário implementar assinatura digital do XML
                
                # Por enquanto, retorna mock para demonstração
                return {
                    'success': False,
                    'message': 'Funcionalidade em desenvolvimento. Requer implementação completa de assinatura digital XML e integração SOAP com SEFAZ.',
                    'documents': [],
                    'ultimo_nsu': ultimo_nsu,
                    'info': {
                        'service_url': wsdl_url,
                        'cnpj': cnpj,
                        'uf': uf,
                        'environment': environment
                    }
                }
            
            finally:
                # Remove arquivos temporários
                if os.path.exists(cert_path):
                    os.unlink(cert_path)
                if os.path.exists(key_path):
                    os.unlink(key_path)
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro na consulta: {str(e)}',
                'documents': [],
                'ultimo_nsu': ultimo_nsu
            }
    
    def manifestar_ciencia(
        self,
        credential_id: int,
        password: str,
        chave_nfe: str,
        tipo_evento: str = 'ciencia',
        environment: str = 'homologation'
    ) -> Dict[str, Any]:
        """
        Manifesta ciência da operação (confirma recebimento da NFe)
        
        Args:
            credential_id: ID da credencial
            password: Senha do certificado
            chave_nfe: Chave de acesso da NFe (44 dígitos)
            tipo_evento: Tipo de manifestação (ciencia, confirmacao, desconhecimento, nao_realizada)
            environment: Ambiente
        
        Returns:
            {
                'success': bool,
                'message': str,
                'protocol': str
            }
        """
        eventos = {
            'ciencia': '210210',  # Ciência da Operação
            'confirmacao': '210200',  # Confirmação da Operação
            'desconhecimento': '210220',  # Desconhecimento da Operação
            'nao_realizada': '210240'  # Operação não Realizada
        }
        
        codigo_evento = eventos.get(tipo_evento, '210210')
        
        # Implementação simplificada
        return {
            'success': False,
            'message': f'Funcionalidade em desenvolvimento. Manifestação do Destinatário requer assinatura digital XML.',
            'protocol': None,
            'info': {
                'chave_nfe': chave_nfe,
                'tipo_evento': tipo_evento,
                'codigo_evento': codigo_evento,
                'environment': environment
            }
        }
    
    def download_nfe_xml(
        self,
        credential_id: int,
        password: str,
        chave_nfe: str,
        environment: str = 'homologation'
    ) -> Dict[str, Any]:
        """
        Faz download do XML de uma NFe específica
        
        Args:
            credential_id: ID da credencial
            password: Senha do certificado
            chave_nfe: Chave de acesso da NFe
            environment: Ambiente
        
        Returns:
            {
                'success': bool,
                'message': str,
                'xml_content': str,
                'file_path': str
            }
        """
        # Implementação simplificada
        return {
            'success': False,
            'message': 'Funcionalidade em desenvolvimento. Download de XML requer integração completa com SOAP e assinatura digital.',
            'xml_content': None,
            'file_path': None,
            'info': {
                'chave_nfe': chave_nfe,
                'environment': environment
            }
        }
    
    def get_integration_status(self, credential_id: int, password: str) -> Dict[str, Any]:
        """
        Testa status da integração com SEFAZ
        
        Returns:
            {
                'certificate_valid': bool,
                'can_connect': bool,
                'services_available': List[str],
                'message': str
            }
        """
        # Testa certificado
        cert_test = self.sefaz_service.test_certificate(credential_id, password)
        
        if not cert_test['valid']:
            return {
                'certificate_valid': False,
                'can_connect': False,
                'services_available': [],
                'message': cert_test['message']
            }
        
        return {
            'certificate_valid': True,
            'can_connect': True,
            'services_available': [
                'NFeDistribuicaoDFe (Consulta NFe Destinadas)',
                'ManifestacaoDestinatario (Em desenvolvimento)',
                'DownloadNFe (Em desenvolvimento)'
            ],
            'message': 'Certificado válido. Integração com SEFAZ em desenvolvimento.',
            'certificate_details': cert_test['details']
        }
