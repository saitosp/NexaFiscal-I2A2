"""
Table Processor - Processa arquivos CSV e XLSX para importação de notas fiscais
"""
import pandas as pd
import os
from typing import Dict, List, Any, Optional, Tuple


def get_file_type(filename: str) -> str:
    """
    Determina o tipo de arquivo baseado na extensão
    
    Args:
        filename: Nome do arquivo
        
    Returns:
        Tipo do arquivo ('csv', 'xlsx', 'unknown')
    """
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.csv':
        return 'csv'
    elif ext in ['.xlsx', '.xls']:
        return 'xlsx'
    else:
        return 'unknown'


def read_csv(file_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
    """
    Lê arquivo CSV e retorna DataFrame
    
    Args:
        file_path: Caminho do arquivo CSV
        encoding: Encoding do arquivo (padrão: utf-8)
        
    Returns:
        DataFrame com os dados
    """
    try:
        # Tenta com encoding UTF-8
        df = pd.read_csv(file_path, encoding=encoding)
        return df
    except UnicodeDecodeError:
        # Se falhar, tenta com latin1 (comum em arquivos brasileiros)
        df = pd.read_csv(file_path, encoding='latin1')
        return df
    except Exception as e:
        raise Exception(f"Erro ao ler arquivo CSV: {str(e)}")


def read_excel(file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Lê arquivo Excel e retorna DataFrame
    
    Args:
        file_path: Caminho do arquivo Excel
        sheet_name: Nome da aba (None = primeira aba)
        
    Returns:
        DataFrame com os dados
    """
    try:
        # Se não especificar aba, usa a primeira
        if sheet_name is None:
            df = pd.read_excel(file_path, sheet_name=0)
        else:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df
    except Exception as e:
        raise Exception(f"Erro ao ler arquivo Excel: {str(e)}")


def get_excel_sheets(file_path: str) -> List[str]:
    """
    Retorna lista de abas de um arquivo Excel
    
    Args:
        file_path: Caminho do arquivo Excel
        
    Returns:
        Lista com nomes das abas
    """
    try:
        xl_file = pd.ExcelFile(file_path)
        return xl_file.sheet_names
    except Exception as e:
        raise Exception(f"Erro ao ler abas do Excel: {str(e)}")


def detect_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Detecta e sugere mapeamento de colunas baseado em nomes comuns
    
    Args:
        df: DataFrame com os dados
        
    Returns:
        Dict com sugestões de mapeamento
    """
    columns = df.columns.tolist()
    
    # Mapeamentos comuns de colunas
    mappings = {
        'emitente_nome': [],
        'emitente_cnpj': [],
        'destinatario_nome': [],
        'destinatario_cnpj': [],
        'numero_nota': [],
        'serie': [],
        'data_emissao': [],
        'valor_total': [],
        'valor_produtos': [],
        'icms': [],
        'pis': [],
        'cofins': [],
        'ipi': [],
        'chave_acesso': [],
        'tipo_documento': []
    }
    
    # Padrões de busca (case-insensitive)
    patterns = {
        'emitente_nome': ['emitente', 'fornecedor', 'razao_social_emitente', 'nome_emitente'],
        'emitente_cnpj': ['cnpj_emitente', 'cnpj_fornecedor', 'cpf_emitente'],
        'destinatario_nome': ['destinatario', 'cliente', 'razao_social_destinatario', 'nome_destinatario'],
        'destinatario_cnpj': ['cnpj_destinatario', 'cnpj_cliente', 'cpf_destinatario'],
        'numero_nota': ['numero', 'nf', 'numero_nf', 'nota', 'numero_nota'],
        'serie': ['serie', 'serie_nf'],
        'data_emissao': ['data', 'data_emissao', 'dt_emissao', 'emissao'],
        'valor_total': ['valor_total', 'total', 'valor_nf', 'vl_total'],
        'valor_produtos': ['valor_produtos', 'produtos', 'vl_produtos'],
        'icms': ['icms', 'valor_icms', 'vl_icms'],
        'pis': ['pis', 'valor_pis', 'vl_pis'],
        'cofins': ['cofins', 'valor_cofins', 'vl_cofins'],
        'ipi': ['ipi', 'valor_ipi', 'vl_ipi'],
        'chave_acesso': ['chave', 'chave_acesso', 'chave_nfe', 'access_key'],
        'tipo_documento': ['tipo', 'tipo_documento', 'tipo_nf', 'modelo']
    }
    
    # Faz matching de colunas
    for field, possible_names in patterns.items():
        for col in columns:
            col_lower = col.lower().replace(' ', '_').replace('-', '_')
            for pattern in possible_names:
                if pattern in col_lower:
                    mappings[field].append(col)
                    break
    
    return mappings


def preview_table(df: pd.DataFrame, max_rows: int = 10) -> Dict[str, Any]:
    """
    Gera preview da tabela com estatísticas
    
    Args:
        df: DataFrame com os dados
        max_rows: Número máximo de linhas para preview
        
    Returns:
        Dict com informações do preview
    """
    preview = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': df.columns.tolist(),
        'column_types': df.dtypes.astype(str).to_dict(),
        'sample_rows': df.head(max_rows).to_dict('records'),
        'missing_values': df.isnull().sum().to_dict(),
        'statistics': {}
    }
    
    # Estatísticas para colunas numéricas
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    for col in numeric_cols:
        preview['statistics'][col] = {
            'min': float(df[col].min()) if not pd.isna(df[col].min()) else None,
            'max': float(df[col].max()) if not pd.isna(df[col].max()) else None,
            'mean': float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
            'median': float(df[col].median()) if not pd.isna(df[col].median()) else None
        }
    
    return preview


def validate_table_structure(df: pd.DataFrame, required_fields: List[str]) -> Tuple[bool, List[str]]:
    """
    Valida se a tabela tem estrutura mínima necessária
    
    Args:
        df: DataFrame com os dados
        required_fields: Lista de campos obrigatórios
        
    Returns:
        Tuple (is_valid, missing_fields)
    """
    columns = [col.lower() for col in df.columns]
    missing = []
    
    for field in required_fields:
        field_lower = field.lower()
        found = False
        for col in columns:
            if field_lower in col:
                found = True
                break
        if not found:
            missing.append(field)
    
    is_valid = len(missing) == 0
    return is_valid, missing


def clean_numeric_column(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Limpa e converte coluna numérica (remove símbolos de moeda, etc)
    
    Args:
        df: DataFrame
        column: Nome da coluna
        
    Returns:
        Series com valores limpos
    """
    if column not in df.columns:
        return pd.Series()
    
    # Remove símbolos comuns
    cleaned = df[column].astype(str).str.replace('R$', '', regex=False)
    cleaned = cleaned.str.replace('$', '', regex=False)
    cleaned = cleaned.str.replace(' ', '', regex=False)
    cleaned = cleaned.str.replace('.', '', regex=False)  # Remove separador de milhar
    cleaned = cleaned.str.replace(',', '.', regex=False)  # Converte vírgula para ponto
    
    # Converte para float
    try:
        return pd.to_numeric(cleaned, errors='coerce')
    except:
        return pd.Series()


def clean_cnpj_cpf(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Limpa coluna de CNPJ/CPF (remove pontos, traços, barras)
    
    Args:
        df: DataFrame
        column: Nome da coluna
        
    Returns:
        Series com valores limpos
    """
    if column not in df.columns:
        return pd.Series()
    
    cleaned = df[column].astype(str).str.replace('.', '', regex=False)
    cleaned = cleaned.str.replace('-', '', regex=False)
    cleaned = cleaned.str.replace('/', '', regex=False)
    cleaned = cleaned.str.replace(' ', '', regex=False)
    
    return cleaned


def convert_to_fiscal_documents(
    df: pd.DataFrame, 
    column_mapping: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Converte linhas da tabela em documentos fiscais estruturados
    
    Args:
        df: DataFrame com os dados
        column_mapping: Mapeamento de colunas (campo -> coluna_tabela)
        
    Returns:
        Lista de documentos fiscais
    """
    documents = []
    
    # Limpa colunas numéricas uma vez antes do loop
    cleaned_cols = {}
    numeric_fields = ['valor_total', 'valor_produtos', 'icms', 'pis', 'cofins', 'ipi', 'iss_total', 'valor_desconto', 'valor_frete', 'valor_seguro']
    
    for field in numeric_fields:
        if field in column_mapping and column_mapping[field]:
            cleaned_cols[field] = clean_numeric_column(df, column_mapping[field])
    
    for row_idx_enum, (idx, row) in enumerate(df.iterrows()):
        # Usa enumerate para ter um índice numérico sempre
        row_num = row_idx_enum + 1
        
        doc = {
            'row_number': row_num,
            'emitente': {},
            'destinatario': {},
            'totais': {},
            'impostos': {},
            'metadata': {}
        }
        
        # Emitente
        if 'emitente_nome' in column_mapping and column_mapping['emitente_nome']:
            doc['emitente']['nome'] = str(row[column_mapping['emitente_nome']])
        if 'emitente_cnpj' in column_mapping and column_mapping['emitente_cnpj']:
            cnpj_col = column_mapping['emitente_cnpj']
            doc['emitente']['cnpj'] = str(row[cnpj_col]).replace('.', '').replace('-', '').replace('/', '')
        
        # Destinatário
        if 'destinatario_nome' in column_mapping and column_mapping['destinatario_nome']:
            doc['destinatario']['nome'] = str(row[column_mapping['destinatario_nome']])
        if 'destinatario_cnpj' in column_mapping and column_mapping['destinatario_cnpj']:
            cnpj_col = column_mapping['destinatario_cnpj']
            doc['destinatario']['cnpj'] = str(row[cnpj_col]).replace('.', '').replace('-', '').replace('/', '')
        
        # Totais - usa valores já limpos com row_idx_enum
        if 'valor_total' in cleaned_cols and not pd.isna(cleaned_cols['valor_total'].iloc[row_idx_enum]):
            doc['totais']['valor_total'] = float(cleaned_cols['valor_total'].iloc[row_idx_enum])
        else:
            doc['totais']['valor_total'] = 0.0
                
        if 'valor_produtos' in cleaned_cols and not pd.isna(cleaned_cols['valor_produtos'].iloc[row_idx_enum]):
            doc['totais']['valor_produtos'] = float(cleaned_cols['valor_produtos'].iloc[row_idx_enum])
        else:
            doc['totais']['valor_produtos'] = 0.0
        
        # Impostos - usa valores já limpos com row_idx_enum
        if 'icms' in cleaned_cols and not pd.isna(cleaned_cols['icms'].iloc[row_idx_enum]):
            doc['impostos']['icms'] = float(cleaned_cols['icms'].iloc[row_idx_enum])
        else:
            doc['impostos']['icms'] = 0.0
                
        if 'pis' in cleaned_cols and not pd.isna(cleaned_cols['pis'].iloc[row_idx_enum]):
            doc['impostos']['pis'] = float(cleaned_cols['pis'].iloc[row_idx_enum])
        else:
            doc['impostos']['pis'] = 0.0
                
        if 'cofins' in cleaned_cols and not pd.isna(cleaned_cols['cofins'].iloc[row_idx_enum]):
            doc['impostos']['cofins'] = float(cleaned_cols['cofins'].iloc[row_idx_enum])
        else:
            doc['impostos']['cofins'] = 0.0
                
        if 'ipi' in cleaned_cols and not pd.isna(cleaned_cols['ipi'].iloc[row_idx_enum]):
            doc['impostos']['ipi'] = float(cleaned_cols['ipi'].iloc[row_idx_enum])
        else:
            doc['impostos']['ipi'] = 0.0
        
        # Metadata
        if 'numero_nota' in column_mapping and column_mapping['numero_nota']:
            doc['metadata']['numero'] = str(row[column_mapping['numero_nota']])
        if 'serie' in column_mapping and column_mapping['serie']:
            doc['metadata']['serie'] = str(row[column_mapping['serie']])
        if 'data_emissao' in column_mapping and column_mapping['data_emissao']:
            doc['metadata']['data_emissao'] = str(row[column_mapping['data_emissao']])
        if 'chave_acesso' in column_mapping and column_mapping['chave_acesso']:
            doc['metadata']['chave_acesso'] = str(row[column_mapping['chave_acesso']])
        if 'tipo_documento' in column_mapping and column_mapping['tipo_documento']:
            doc['metadata']['tipo'] = str(row[column_mapping['tipo_documento']])
        else:
            doc['metadata']['tipo'] = 'NFe'  # Padrão
        
        documents.append(doc)
    
    return documents
