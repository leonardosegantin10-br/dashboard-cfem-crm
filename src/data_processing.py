"""
Módulo de processamento de dados CFEM-CRM
Responsável por carregar, limpar e transformar dados CSV
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional


def load_and_validate_csv(file_object, delimiter: str = ';') -> pd.DataFrame:
    """
    Carrega arquivo CSV com tratamento de encoding

    Args:
        file_object: Objeto de arquivo do Streamlit
        delimiter: Delimitador do CSV (padrão: ';')

    Returns:
        DataFrame bruto
    """
    try:
        # Tenta UTF-8 com BOM primeiro
        df = pd.read_csv(file_object, delimiter=delimiter, encoding='utf-8-sig')
    except UnicodeDecodeError:
        # Fallback para latin-1
        file_object.seek(0)
        df = pd.read_csv(file_object, delimiter=delimiter, encoding='latin-1')

    # Remove linhas completamente vazias
    df = df.dropna(how='all')

    return df


def transform_cpf_cnpj(value) -> str:
    """
    Converte CPF/CNPJ de notação científica para string de 14 dígitos

    Args:
        value: Valor em notação científica (ex: 3.36E+13) ou string

    Returns:
        String formatada com 14 dígitos (ex: "03360000000191")
    """
    if pd.isna(value) or value == "":
        return ""

    try:
        # Converte notação científica para número
        if isinstance(value, str):
            # Remove espaços
            value = value.strip()
            # Se contém E (científico), converte
            if 'E' in value.upper() or 'e' in value:
                num = int(float(value))
            else:
                # Remove pontos e vírgulas para converter
                num = int(float(value.replace('.', '').replace(',', '')))
        else:
            num = int(float(value))

        # Formata com 14 dígitos (padding com zeros à esquerda)
        return f"{num:014d}"

    except (ValueError, TypeError):
        # Se falhar, retorna o valor original como string
        return str(value)


def convert_brazilian_decimal(value) -> float:
    """
    Converte formato brasileiro de decimal para float
    Formato brasileiro: 1.234,56 → 1234.56

    Args:
        value: Valor em formato brasileiro ou número

    Returns:
        Float ou NaN se inválido
    """
    if pd.isna(value) or value == "" or value == "#N/D":
        return np.nan

    try:
        # Se já é número, retorna
        if isinstance(value, (int, float)):
            return float(value)

        # Converte string
        str_val = str(value).strip()

        # Remove pontos (separador de milhares) e troca vírgula por ponto
        str_val = str_val.replace('.', '').replace(',', '.')

        return float(str_val)

    except (ValueError, TypeError):
        return np.nan


def clean_and_transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e transforma os dados do CSV

    Args:
        df: DataFrame bruto

    Returns:
        DataFrame limpo e transformado
    """
    # Criar cópia para não modificar original
    df = df.copy()

    # Normalizar nomes de colunas: remove espaços extras, padroniza para lowercase e substitui espaços por underscores
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    # 1. Substituir #N/D por NaN
    df = df.replace('#N/D', np.nan)
    df = df.replace('#N/A', np.nan)

    # 2. Remover colunas CHECK* e duplicatas
    columns_to_drop = [col for col in df.columns if col.startswith('check')]
    columns_to_drop.extend(['empresa_cpf_cnpj', 'cfem (porte)'])

    # Remove apenas se existirem
    columns_to_drop = [col for col in columns_to_drop if col in df.columns]
    df = df.drop(columns=columns_to_drop, errors='ignore')

    # 3. Transformar CPF_CNPJ
    if 'cpf_cnpj' in df.columns:
        df['cpf_cnpj'] = df['cpf_cnpj'].apply(transform_cpf_cnpj)

    # 4. Converter campos numéricos com formato brasileiro
    numeric_columns = [
        'totalvalorrecolhido',
        'totalquantidadecomercializada',
        'valor',
        'valor_total_mensal'
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].apply(convert_brazilian_decimal)

    # 5. Converter campos inteiros
    int_columns = ['duração', 'total_escopos']
    for col in int_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # 6. Limpar espaços em strings
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    return df


def calculate_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula campos derivados

    Args:
        df: DataFrame limpo

    Returns:
        DataFrame com campos calculados adicionados
    """
    df = df.copy()

    # 1. Valor Anual Mapeado = Valor Total Mensal * 12
    if 'valor_total_mensal' in df.columns:
        df['valor_anual_mapeado'] = df['valor_total_mensal'] * 12
        # Substitui NaN por 0 para facilitar análises
        df['valor_anual_mapeado'] = df['valor_anual_mapeado'].fillna(0)
    else:
        df['valor_anual_mapeado'] = 0

    # 2. Status Mapeamento (case-insensitive e robusto)
    if 'primeiro_escopo' in df.columns:
        def determine_status(x):
            # Se é NaN ou None, não está mapeado
            if pd.isna(x):
                return 'Não'
            # Converte para string e remove espaços
            x_str = str(x).strip()
            # Se vazio após strip, não está mapeado
            if x_str == '':
                return 'Não'
            # Se é "NÃO" (case-insensitive), não está mapeado
            if x_str.upper() == 'NÃO':
                return 'Não'
            # Caso contrário, está mapeado
            return 'Sim'

        df['status_mapeamento'] = df['primeiro_escopo'].apply(determine_status)
    else:
        df['status_mapeamento'] = 'Não'

    return df


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Retorna resumo dos dados carregados

    Args:
        df: DataFrame processado

    Returns:
        Dicionário com metadados
    """
    return {
        'row_count': len(df),
        'column_count': len(df.columns),
        'date_processed': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
    }


def format_cpf_cnpj_display(cnpj: str) -> str:
    """
    Formata CNPJ para exibição: 12.345.678/9012-34

    Args:
        cnpj: String de 14 dígitos

    Returns:
        CNPJ formatado
    """
    if not cnpj or len(cnpj) != 14:
        return cnpj

    try:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"
    except:
        return cnpj


def format_currency(value: float) -> str:
    """
    Formata valor monetário em formato brasileiro

    Args:
        value: Valor numérico

    Returns:
        String formatada (ex: "R$ 1.234.567,89")
    """
    if pd.isna(value):
        return "R$ 0,00"

    try:
        # Formata com separador de milhares e vírgula decimal
        return f"R$ {value:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    except:
        return "R$ 0,00"


def format_number(value: float, decimals: int = 0) -> str:
    """
    Formata número com separador de milhares brasileiro

    Args:
        value: Valor numérico
        decimals: Número de casas decimais

    Returns:
        String formatada (ex: "1.234.567")
    """
    if pd.isna(value):
        return "0"

    try:
        if decimals > 0:
            formatted = f"{value:,.{decimals}f}"
        else:
            formatted = f"{int(value):,}"

        # Troca . por , e , por .
        return formatted.replace(',', '_').replace('.', ',').replace('_', '.')
    except:
        return "0"
