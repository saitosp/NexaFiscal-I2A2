"""
SEFAZ Integration Service
Gerencia integração com portais da SEFAZ usando certificado digital
"""

import os
import base64
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hashlib

from database.repository import CredentialRepository


class SefazService:
    """
    Serviço para integração com SEFAZ
    Gerencia certificados digitais e comunicação com portais
    """
    
    @staticmethod
    def _get_encryption_key() -> bytes:
        """
        Obtém chave mestra para criptografia de certificados
        Deriva da variável de ambiente SEFAZ_CERT_MASTER_KEY
        
        Raises:
            ValueError: Se SEFAZ_CERT_MASTER_KEY não estiver configurada
        """
        master_key = os.getenv('SEFAZ_CERT_MASTER_KEY')
        
        if not master_key:
            raise ValueError(
                "SEFAZ_CERT_MASTER_KEY environment variable is required for certificate encryption. "
                "Please set it in Replit Secrets with a strong random key (minimum 32 characters)."
            )
        
        # Deriva chave usando PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'sefaz-nfe-salt-2025',  # Salt fixo (em produção, usar salt por certificado)
            iterations=100000,
            backend=default_backend()
        )
        
        return kdf.derive(master_key.encode())
    
    @staticmethod
    def _encrypt_data(data: bytes) -> bytes:
        """
        Criptografa dados usando AES-256-GCM
        """
        key = SefazService._get_encryption_key()
        
        # Gera IV aleatório
        iv = os.urandom(16)
        
        # Criptografa
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Retorna IV + tag + ciphertext
        return iv + encryptor.tag + ciphertext
    
    @staticmethod
    def _decrypt_data(encrypted_data: bytes) -> bytes:
        """
        Descriptografa dados usando AES-256-GCM
        """
        key = SefazService._get_encryption_key()
        
        # Extrai IV, tag e ciphertext
        iv = encrypted_data[:16]
        tag = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]
        
        # Descriptografa
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    @staticmethod
    def process_certificate(
        certificate_file: bytes,
        password: str,
        name: str,
        environment: str = 'homologation'
    ) -> Dict[str, Any]:
        """
        Processa e armazena certificado digital A1 (PKCS#12)
        
        Args:
            certificate_file: Arquivo .pfx/.p12 em bytes
            password: Senha do certificado
            name: Nome identificador do certificado
            environment: 'production' ou 'homologation'
        
        Returns:
            {
                'credential_id': int,
                'name': str,
                'subject': str,
                'issuer': str,
                'valid_from': str,
                'valid_until': str,
                'environment': str
            }
        """
        try:
            # Carrega o certificado PKCS#12
            from cryptography.hazmat.primitives.serialization import pkcs12
            
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                certificate_file,
                password.encode(),
                backend=default_backend()
            )
            
            # Extrai informações do certificado
            subject = certificate.subject.rfc4514_string()
            issuer = certificate.issuer.rfc4514_string()
            valid_from = certificate.not_valid_before_utc
            valid_until = certificate.not_valid_after_utc
            
            # Verifica se o certificado ainda é válido
            now = datetime.now(valid_until.tzinfo)
            if now > valid_until:
                raise ValueError("Certificado expirado")
            
            # Serializa chave privada
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Serializa certificado
            cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
            
            # Criptografa chave privada e certificado
            encrypted_private_key = SefazService._encrypt_data(private_key_pem)
            encrypted_certificate = SefazService._encrypt_data(cert_pem)
            
            # Hash da senha para validação futura (sem armazenar plaintext)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Salva no banco de dados
            credential = CredentialRepository.create(
                name=name,
                credential_type='sefaz_certificate_a1',
                certificate_data=base64.b64encode(encrypted_certificate).decode(),
                private_key_data=base64.b64encode(encrypted_private_key).decode(),
                password_hash=password_hash,
                expires_at=valid_until,
                environment=environment,
                metadata={
                    'subject': subject,
                    'issuer': issuer,
                    'valid_from': valid_from.isoformat(),
                    'valid_until': valid_until.isoformat(),
                    'serial_number': str(certificate.serial_number)
                }
            )
            
            return {
                'credential_id': credential.id,
                'name': name,
                'subject': subject,
                'issuer': issuer,
                'valid_from': valid_from.isoformat(),
                'valid_until': valid_until.isoformat(),
                'environment': environment
            }
        
        except Exception as e:
            raise ValueError(f"Erro ao processar certificado: {str(e)}")
    
    @staticmethod
    def get_certificate_data(credential_id: int, password: str) -> Tuple[bytes, bytes]:
        """
        Recupera certificado e chave privada descriptografados
        
        Args:
            credential_id: ID da credencial
            password: Senha para validação
        
        Returns:
            (certificate_pem, private_key_pem)
        """
        credential = CredentialRepository.get_by_id(credential_id)
        
        if not credential:
            raise ValueError("Credencial não encontrada")
        
        # Valida senha
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash != credential.password_hash:
            raise ValueError("Senha incorreta")
        
        # Verifica expiração
        if credential.expires_at and datetime.now(credential.expires_at.tzinfo) > credential.expires_at:
            raise ValueError("Certificado expirado")
        
        # Descriptografa
        encrypted_cert = base64.b64decode(credential.certificate_data)
        encrypted_key = base64.b64decode(credential.private_key_data)
        
        certificate_pem = SefazService._decrypt_data(encrypted_cert)
        private_key_pem = SefazService._decrypt_data(encrypted_key)
        
        return certificate_pem, private_key_pem
    
    @staticmethod
    def list_certificates() -> list:
        """
        Lista todos os certificados cadastrados
        
        Returns:
            Lista de certificados com metadados
        """
        credentials = CredentialRepository.get_all(credential_type='sefaz_certificate_a1')
        
        result = []
        for cred in credentials:
            result.append({
                'id': cred.id,
                'name': cred.name,
                'environment': cred.environment,
                'is_active': cred.is_active,
                'valid_from': cred.metadata.get('valid_from') if cred.metadata else None,
                'valid_until': cred.metadata.get('valid_until') if cred.metadata else None,
                'subject': cred.metadata.get('subject') if cred.metadata else None,
                'created_at': cred.created_at.isoformat() if cred.created_at else None
            })
        
        return result
    
    @staticmethod
    def delete_certificate(credential_id: int) -> bool:
        """
        Remove um certificado
        """
        return CredentialRepository.delete(credential_id)
    
    @staticmethod
    def test_certificate(credential_id: int, password: str) -> Dict[str, Any]:
        """
        Testa se um certificado pode ser carregado e usado
        
        Returns:
            {
                'valid': bool,
                'message': str,
                'details': Dict
            }
        """
        try:
            cert_pem, key_pem = SefazService.get_certificate_data(credential_id, password)
            
            # Carrega certificado para validar
            cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
            
            # Verifica validade
            now = datetime.now(cert.not_valid_after_utc.tzinfo)
            days_until_expiry = (cert.not_valid_after_utc - now).days
            
            return {
                'valid': True,
                'message': 'Certificado válido e carregado com sucesso',
                'details': {
                    'subject': cert.subject.rfc4514_string(),
                    'issuer': cert.issuer.rfc4514_string(),
                    'serial_number': cert.serial_number,
                    'valid_from': cert.not_valid_before_utc.isoformat(),
                    'valid_until': cert.not_valid_after_utc.isoformat(),
                    'days_until_expiry': days_until_expiry
                }
            }
        
        except ValueError as e:
            return {
                'valid': False,
                'message': str(e),
                'details': {}
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f"Erro ao testar certificado: {str(e)}",
                'details': {}
            }
