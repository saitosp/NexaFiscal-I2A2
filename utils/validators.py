"""
Validadores para documentos fiscais brasileiros
"""
import re
from pycpfcnpj import cpfcnpj


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida um CNPJ brasileiro
    
    Args:
        cnpj: CNPJ para validar (com ou sem formatação)
        
    Returns:
        True se o CNPJ é válido, False caso contrário
    """
    if not cnpj:
        return False
    
    # Remove formatação
    cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
    
    return cpfcnpj.validate(cnpj_clean) and len(cnpj_clean) == 14


def validate_cpf(cpf: str) -> bool:
    """
    Valida um CPF brasileiro
    
    Args:
        cpf: CPF para validar (com ou sem formatação)
        
    Returns:
        True se o CPF é válido, False caso contrário
    """
    if not cpf:
        return False
    
    # Remove formatação
    cpf_clean = re.sub(r'[^0-9]', '', cpf)
    
    return cpfcnpj.validate(cpf_clean) and len(cpf_clean) == 11


def validate_nfe_key(key: str) -> bool:
    """
    Valida uma chave de acesso de NFe (44 dígitos)
    
    Args:
        key: Chave de acesso da NFe
        
    Returns:
        True se a chave é válida, False caso contrário
    """
    if not key:
        return False
    
    # Remove formatação
    key_clean = re.sub(r'[^0-9]', '', key)
    
    # Chave de NFe deve ter 44 dígitos
    if len(key_clean) != 44:
        return False
    
    # Validação do dígito verificador
    try:
        # Extrai os 43 primeiros dígitos e o dígito verificador
        base = key_clean[:43]
        dv = int(key_clean[43])
        
        # Calcula o dígito verificador
        soma = 0
        multiplicador = 2
        
        for i in range(42, -1, -1):
            soma += int(base[i]) * multiplicador
            multiplicador = 3 if multiplicador == 2 else 2 if multiplicador == 9 else multiplicador + 1
        
        resto = soma % 11
        dv_calculado = 0 if resto in [0, 1] else 11 - resto
        
        return dv == dv_calculado
    except:
        return False


def format_cnpj(cnpj: str) -> str:
    """
    Formata um CNPJ brasileiro
    
    Args:
        cnpj: CNPJ sem formatação
        
    Returns:
        CNPJ formatado (XX.XXX.XXX/XXXX-XX)
    """
    cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj_clean) != 14:
        return cnpj
    
    return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"


def format_cpf(cpf: str) -> str:
    """
    Formata um CPF brasileiro
    
    Args:
        cpf: CPF sem formatação
        
    Returns:
        CPF formatado (XXX.XXX.XXX-XX)
    """
    cpf_clean = re.sub(r'[^0-9]', '', cpf)
    if len(cpf_clean) != 11:
        return cpf
    
    return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
