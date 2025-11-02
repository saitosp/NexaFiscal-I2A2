"""
Módulo para carregar e gerenciar configuração de impostos

Este módulo permite que o sistema seja facilmente adaptável a mudanças 
legais no sistema tributário brasileiro (ex: implementação do IVA).
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from functools import lru_cache


class TaxConfig:
    """
    Gerenciador de configuração de impostos
    
    Carrega configuração do arquivo tax_config.json e fornece
    métodos para acessar informações sobre impostos de forma dinâmica.
    """
    
    def __init__(self, config_path: str = 'config/tax_config.json'):
        """
        Inicializa o gerenciador de configuração
        
        Args:
            config_path: Caminho para o arquivo de configuração
        """
        self.config_path = config_path
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Carrega configuração do arquivo JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Arquivo de configuração não encontrado: {self.config_path}. "
                "Execute o sistema de inicialização."
            )
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Erro ao decodificar JSON em {self.config_path}: {str(e)}"
            )
    
    def get_all_taxes(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Retorna lista de todos os impostos configurados
        
        Args:
            enabled_only: Se True, retorna apenas impostos habilitados
        
        Returns:
            Lista de dicionários com dados dos impostos
        """
        taxes = self._config.get('taxes', [])
        
        if enabled_only:
            return [tax for tax in taxes if tax.get('enabled', True)]
        
        return taxes
    
    def get_tax_by_id(self, tax_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca imposto por ID
        
        Args:
            tax_id: ID do imposto (ex: 'icms', 'ipi', 'pis')
        
        Returns:
            Dicionário com dados do imposto ou None se não encontrado
        """
        for tax in self.get_all_taxes(enabled_only=False):
            if tax['id'] == tax_id:
                return tax
        return None
    
    def get_tax_ids(self, enabled_only: bool = True) -> List[str]:
        """
        Retorna lista de IDs dos impostos
        
        Args:
            enabled_only: Se True, retorna apenas IDs de impostos habilitados
        
        Returns:
            Lista de IDs (ex: ['icms', 'ipi', 'pis', 'cofins'])
        """
        return [tax['id'] for tax in self.get_all_taxes(enabled_only)]
    
    def get_tax_names(self, enabled_only: bool = True) -> Dict[str, str]:
        """
        Retorna mapeamento de IDs para nomes dos impostos
        
        Args:
            enabled_only: Se True, retorna apenas impostos habilitados
        
        Returns:
            Dicionário {id: name} (ex: {'icms': 'ICMS', 'ipi': 'IPI'})
        """
        return {
            tax['id']: tax['name'] 
            for tax in self.get_all_taxes(enabled_only)
        }
    
    def get_tax_colors(self, enabled_only: bool = True) -> Dict[str, str]:
        """
        Retorna mapeamento de IDs para cores dos impostos (para gráficos)
        
        Args:
            enabled_only: Se True, retorna apenas impostos habilitados
        
        Returns:
            Dicionário {id: color} (ex: {'icms': '#1f77b4', 'ipi': '#ff7f0e'})
        """
        return {
            tax['id']: tax.get('color', '#808080') 
            for tax in self.get_all_taxes(enabled_only)
        }
    
    def get_xml_fields_for_tax(self, tax_id: str) -> List[str]:
        """
        Retorna lista de campos XML para um imposto específico
        
        Args:
            tax_id: ID do imposto
        
        Returns:
            Lista de nomes de campos XML (ex: ['vICMS', 'vICMSST'])
        """
        tax = self.get_tax_by_id(tax_id)
        return tax.get('xml_fields', []) if tax else []
    
    def get_taxes_for_document_type(self, doc_type: str) -> List[Dict[str, Any]]:
        """
        Retorna impostos aplicáveis a um tipo de documento
        
        Args:
            doc_type: Tipo do documento (ex: 'NFe', 'NFCe', 'NFSe')
        
        Returns:
            Lista de impostos aplicáveis
        """
        return [
            tax for tax in self.get_all_taxes()
            if doc_type in tax.get('applies_to', [])
        ]
    
    def reload(self) -> None:
        """Recarrega configuração do arquivo (útil após edições)"""
        self._load_config()
    
    def _create_backup(self) -> str:
        """
        Cria backup do arquivo de configuração
        
        Returns:
            Caminho do arquivo de backup criado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.config_path}.backup_{timestamp}"
        shutil.copy2(self.config_path, backup_path)
        return backup_path
    
    def _save_config(self) -> None:
        """Salva configuração atual no arquivo JSON"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    def _add_change_to_history(self, change_description: str, author: str = 'user') -> None:
        """
        Adiciona registro ao histórico de mudanças
        
        Args:
            change_description: Descrição da mudança
            author: Autor da mudança
        """
        if 'metadata' not in self._config:
            self._config['metadata'] = {}
        
        if 'change_history' not in self._config['metadata']:
            self._config['metadata']['change_history'] = []
        
        self._config['metadata']['change_history'].append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'change': change_description,
            'author': author
        })
        
        self._config['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    def add_tax(self, tax_data: Dict[str, Any]) -> bool:
        """
        Adiciona novo imposto à configuração
        
        Args:
            tax_data: Dicionário com dados do imposto
        
        Returns:
            True se adicionado com sucesso, False caso contrário
        """
        if self.get_tax_by_id(tax_data['id']):
            return False
        
        self._create_backup()
        self._config['taxes'].append(tax_data)
        self._add_change_to_history(f"Imposto '{tax_data['name']}' adicionado")
        self._save_config()
        self.reload()
        
        get_tax_config.cache_clear()
        return True
    
    def update_tax(self, tax_id: str, updated_data: Dict[str, Any]) -> bool:
        """
        Atualiza dados de um imposto existente
        
        Args:
            tax_id: ID do imposto a atualizar
            updated_data: Novos dados do imposto
        
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        for i, tax in enumerate(self._config['taxes']):
            if tax['id'] == tax_id:
                self._create_backup()
                self._config['taxes'][i] = updated_data
                self._add_change_to_history(f"Imposto '{updated_data['name']}' atualizado")
                self._save_config()
                self.reload()
                get_tax_config.cache_clear()
                return True
        return False
    
    def delete_tax(self, tax_id: str) -> bool:
        """
        Remove um imposto da configuração
        
        Args:
            tax_id: ID do imposto a remover
        
        Returns:
            True se removido com sucesso, False caso contrário
        """
        tax = self.get_tax_by_id(tax_id)
        if not tax:
            return False
        
        self._create_backup()
        self._config['taxes'] = [t for t in self._config['taxes'] if t['id'] != tax_id]
        self._add_change_to_history(f"Imposto '{tax['name']}' removido")
        self._save_config()
        self.reload()
        get_tax_config.cache_clear()
        return True
    
    def toggle_tax_status(self, tax_id: str) -> Optional[bool]:
        """
        Ativa/desativa um imposto
        
        Args:
            tax_id: ID do imposto
        
        Returns:
            Novo status (True=ativo, False=inativo) ou None se não encontrado
        """
        for tax in self._config['taxes']:
            if tax['id'] == tax_id:
                self._create_backup()
                new_status = not tax.get('enabled', True)
                tax['enabled'] = new_status
                status_str = 'ativado' if new_status else 'desativado'
                self._add_change_to_history(f"Imposto '{tax['name']}' {status_str}")
                self._save_config()
                self.reload()
                get_tax_config.cache_clear()
                return new_status
        return None


# Singleton para evitar múltiplas leituras do arquivo
@lru_cache(maxsize=1)
def get_tax_config() -> TaxConfig:
    """
    Retorna instância singleton do TaxConfig
    
    Returns:
        Instância de TaxConfig
    """
    return TaxConfig()


# Funções de conveniência para acesso rápido
def get_enabled_tax_ids() -> List[str]:
    """Retorna lista de IDs dos impostos habilitados"""
    return get_tax_config().get_tax_ids(enabled_only=True)


def get_tax_name(tax_id: str) -> str:
    """Retorna nome do imposto por ID"""
    tax = get_tax_config().get_tax_by_id(tax_id)
    return tax['name'] if tax else tax_id.upper()


def get_all_tax_names() -> Dict[str, str]:
    """Retorna mapeamento de IDs para nomes"""
    return get_tax_config().get_tax_names(enabled_only=True)


def get_all_tax_colors() -> Dict[str, str]:
    """Retorna mapeamento de IDs para cores"""
    return get_tax_config().get_tax_colors(enabled_only=True)
