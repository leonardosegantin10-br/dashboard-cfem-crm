"""
Módulo de visualizações e KPIs do dashboard CFEM-CRM
Responsável por renderizar cards, filtros e tabelas
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
from src.data_processing import format_currency, format_number, format_cpf_cnpj_display


def format_currency_abbreviated(value: float) -> str:
    """
    Formata valor monetário de forma abreviada (Mi/Bi)

    Args:
        value: Valor numérico

    Returns:
        String formatada (ex: "R$ 1.5 Mi", "R$ 2.3 Bi")
    """
    if pd.isna(value):
        return "R$ 0,00"

    try:
        if value >= 1_000_000_000:
            # Bilhões
            valor_bi = value / 1_000_000_000
            return f"R$ {valor_bi:.2f} Bi"
        elif value >= 1_000_000:
            # Milhões
            valor_mi = value / 1_000_000
            return f"R$ {valor_mi:.2f} Mi"
        else:
            # Valores menores que 1 milhão - formato completo
            return f"R$ {value:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    except:
        return "R$ 0,00"


def render_kpi_section(df: pd.DataFrame, filters_applied: bool = False) -> None:
    """
    Renderiza seção de KPIs com 4 cards principais

    Args:
        df: DataFrame filtrado
        filters_applied: Se há filtros ativos (para mostrar aviso)
    """
    st.header("📊 Visão Geral")

    if filters_applied:
        st.markdown("""
        <div style="background-color: #FFF3E0; border-left: 4px solid #FF6B35; padding: 12px; border-radius: 4px; margin-bottom: 1rem;">
            <p style="margin: 0; color: #2D3142; font-size: 0.95em;">
                🔍 Filtros aplicados - KPIs refletem apenas os dados filtrados
            </p>
        </div>
        """, unsafe_allow_html=True)

    # === CARD 1: Panorama do Mercado ===
    st.subheader("🌍 Panorama do Mercado")
    col1, col2, col3 = st.columns(3)

    # Total de Minas
    total_minas = len(df) if 'chaveprimaria' not in df.columns else df['chaveprimaria'].nunique()

    # CFEM Total Coletado 2024
    cfem_total = df['totalvalorrecolhido'].sum() if 'totalvalorrecolhido' in df.columns else 0
    cfem_bilhoes = cfem_total / 1_000_000_000

    # Ticket Médio CFEM
    ticket_medio = cfem_total / total_minas if total_minas > 0 else 0
    ticket_medio_milhoes = ticket_medio / 1_000_000

    col1.metric("Total de Minas", f"{total_minas:,}".replace(',', '.'))
    col2.metric("CFEM Total 2024", f"R$ {cfem_bilhoes:.2f} Bi")
    col3.metric("Ticket Médio CFEM", f"R$ {ticket_medio_milhoes:.2f} Mi")

    # === CARD 2: Estrutura de Mercado ===
    st.subheader("🏢 Estrutura de Mercado")

    # Total de Grupos (excluindo NA e FORA)
    if 'pai' in df.columns:
        # Filtra minas com grupo (exclui NA, FORA e vazios)
        df_com_grupo = df[~df['pai'].isin(['NA', 'FORA', 'na', 'fora', '']) & df['pai'].notna()]
        grupos = df_com_grupo['pai'].dropna()
        total_grupos = grupos.nunique()

        # CFEM Total dos grupos (excluindo NA/FORA)
        cfem_grupos = df_com_grupo['totalvalorrecolhido'].sum() if 'totalvalorrecolhido' in df.columns else 0

        # Ticket Médio por Grupo
        ticket_medio_grupo = cfem_grupos / total_grupos if total_grupos > 0 else 0
        ticket_medio_grupo_milhoes = ticket_medio_grupo / 1_000_000

        # TOP 5 Grupos por CFEM
        if 'totalvalorrecolhido' in df.columns:
            top5_grupos = (
                df_com_grupo
                .groupby('pai')['totalvalorrecolhido']
                .sum()
                .sort_values(ascending=False)
                .head(5)
                .iloc[::-1]  # Inverte ordem para exibição (maior no topo)
            )

            # TOP 5 Substâncias por CFEM
            top5_substancias = (
                df[df['substanciamaiscomercializada'].notna() &
                   (df['substanciamaiscomercializada'] != '')]
                .groupby('substanciamaiscomercializada')['totalvalorrecolhido']
                .sum()
                .sort_values(ascending=False)
                .head(5)
                .iloc[::-1]  # Inverte ordem para exibição (maior no topo)
            )

            # TOP 5 Estados por CFEM
            top5_estados = (
                df[df['uf'].notna() & (df['uf'] != '')]
                .groupby('uf')['totalvalorrecolhido']
                .sum()
                .sort_values(ascending=False)
                .head(5)
                .iloc[::-1]  # Inverte ordem para exibição (maior no topo)
            )

            # Cards com métricas
            col_card1, col_card2 = st.columns(2)

            with col_card1:
                st.metric("Total de Grupos", total_grupos)
                st.caption("(Excluindo NA e FORA)")

            with col_card2:
                st.metric("Ticket Médio por Grupo", f"R$ {ticket_medio_grupo_milhoes:.2f} Mi")

            # 3 Gráficos lado a lado
            col1, col2, col3 = st.columns(3)

            # GRÁFICO 1: TOP 5 Grupos
            with col1:
                fig_grupos = go.Figure(go.Bar(
                    x=top5_grupos.values,
                    y=top5_grupos.index,
                    orientation='h',
                    marker=dict(color='#95A3B3'),
                    text=[format_currency_abbreviated(v) for v in top5_grupos.values],
                    textposition='auto',
                    hovertemplate='<b>%{y}</b><br>CFEM: %{text}<extra></extra>'
                ))

                fig_grupos.update_layout(
                    title="TOP 5 Grupos por CFEM",
                    xaxis_title="",
                    yaxis_title="",
                    height=240,
                    margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )

                st.plotly_chart(fig_grupos, use_container_width=True)

            # GRÁFICO 2: TOP 5 Substâncias
            with col2:
                fig_substancias = go.Figure(go.Bar(
                    x=top5_substancias.values,
                    y=top5_substancias.index,
                    orientation='h',
                    marker=dict(color='#95A3B3'),
                    text=[format_currency_abbreviated(v) for v in top5_substancias.values],
                    textposition='auto',
                    hovertemplate='<b>%{y}</b><br>CFEM: %{text}<extra></extra>'
                ))

                fig_substancias.update_layout(
                    title="TOP 5 Substâncias por CFEM",
                    xaxis_title="",
                    yaxis_title="",
                    height=240,
                    margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )

                st.plotly_chart(fig_substancias, use_container_width=True)

            # GRÁFICO 3: TOP 5 Estados
            with col3:
                fig_estados = go.Figure(go.Bar(
                    x=top5_estados.values,
                    y=top5_estados.index,
                    orientation='h',
                    marker=dict(color='#95A3B3'),
                    text=[format_currency_abbreviated(v) for v in top5_estados.values],
                    textposition='auto',
                    hovertemplate='<b>%{y}</b><br>CFEM: %{text}<extra></extra>'
                ))

                fig_estados.update_layout(
                    title="TOP 5 Estados por CFEM",
                    xaxis_title="",
                    yaxis_title="",
                    height=240,
                    margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=False
                )

                st.plotly_chart(fig_estados, use_container_width=True)
        else:
            st.metric("Total de Grupos", total_grupos)
            st.metric("Ticket Médio por Grupo", "R$ 0,00")
    else:
        st.warning("Coluna 'pai' não encontrada nos dados")

    st.markdown("---")

    # === CARD 3: Mapeamento Comercial ===
    st.subheader("🎯 Mapeamento Comercial")

    # Calcula quantas minas têm grupo (excluindo NA/FORA)
    if 'pai' in df.columns:
        minas_com_grupo = len(df[~df['pai'].isin(['NA', 'FORA', 'na', 'fora', '']) & df['pai'].notna()])
    else:
        minas_com_grupo = total_minas

    # Minas Mapeadas
    if 'status_mapeamento' in df.columns:
        minas_mapeadas = len(df[df['status_mapeamento'] == 'Sim'])
        perc_mapeadas_total = (minas_mapeadas / total_minas * 100) if total_minas > 0 else 0
        perc_mapeadas_com_grupo = (minas_mapeadas / minas_com_grupo * 100) if minas_com_grupo > 0 else 0
    else:
        minas_mapeadas = 0
        perc_mapeadas_total = 0
        perc_mapeadas_com_grupo = 0

    # Valor Mensal Mapeado
    if 'valor_total_mensal' in df.columns and 'status_mapeamento' in df.columns:
        valor_mensal = df[df['status_mapeamento'] == 'Sim']['valor_total_mensal'].sum()
    else:
        valor_mensal = 0

    # Valor Anual Mapeado
    if 'valor_anual_mapeado' in df.columns and 'status_mapeamento' in df.columns:
        valor_anual = df[df['status_mapeamento'] == 'Sim']['valor_anual_mapeado'].sum()
    else:
        valor_anual = valor_mensal * 12

    # === CÁLCULOS PARA NOVOS CARDS (LINHA 2) ===

    # Cálculo: Índice Valor/CFEM (movido da seção Efetividade)
    if 'status_mapeamento' in df.columns and 'totalvalorrecolhido' in df.columns:
        df_mapeadas = df[df['status_mapeamento'] == 'Sim']
        cfem_mapeadas = df_mapeadas['totalvalorrecolhido'].sum()
        indice_valor_cfem = (valor_anual / cfem_mapeadas * 100) if cfem_mapeadas > 0 else 0
    else:
        indice_valor_cfem = 0
        df_mapeadas = df

    # Cálculo: Empresas por TEC
    empresas_por_tec = {}
    if 'tec' in df_mapeadas.columns and 'pai' in df_mapeadas.columns:
        for tec in ['TEC01', 'TEC02', 'TEC03', 'TEC04', 'TEC05']:
            qtd_empresas = df_mapeadas[df_mapeadas['tec'] == tec]['pai'].nunique()
            if qtd_empresas > 0:
                empresas_por_tec[tec] = qtd_empresas
    texto_empresas_tec = " | ".join([f"{tec}: {qtd}" for tec, qtd in empresas_por_tec.items()])

    # Cálculo: Ticket Médio
    if len(df_mapeadas) > 0:
        ticket_medio_cfem = df_mapeadas['totalvalorrecolhido'].mean()
        ticket_medio_valor_anual = df_mapeadas['valor_anual_mapeado'].mean() if 'valor_anual_mapeado' in df_mapeadas.columns else 0
        qtd_mapeadas = len(df_mapeadas)
    else:
        ticket_medio_cfem = 0
        ticket_medio_valor_anual = 0
        qtd_mapeadas = 0

    # Layout em 3 colunas (LINHA 1)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Minas Mapeadas",
            f"{minas_mapeadas:,}".replace(',', '.'),
            delta=f"{perc_mapeadas_total:.1f}% do total | {perc_mapeadas_com_grupo:.1f}% de minas com grupo"
        )

    with col2:
        st.metric(
            "Valor Mensal Mapeado",
            format_currency_abbreviated(valor_mensal)
        )

    with col3:
        st.metric(
            "Valor Anual Mapeado",
            format_currency_abbreviated(valor_anual)
        )

    # LINHA 2: Novos cards
    col4, col5, col6 = st.columns(3)

    # Card 4: Índice Valor/CFEM (movido da Efetividade)
    with col4:
        st.metric(
            "Índice Valor/CFEM",
            f"{indice_valor_cfem:.2f}%",
            help="(Valor Anual Mapeado / CFEM das minas mapeadas) × 100"
        )
        st.markdown(
            f'<p style="color: #2D3142; font-size: 0.95rem; margin: 0;">Eficiência do mapeamento comercial</p>',
            unsafe_allow_html=True
        )

    # Card 5: Empresas por TEC (NOVO)
    with col5:
        st.metric(
            "🎯 Empresas por TEC",
            texto_empresas_tec if texto_empresas_tec else "Nenhuma",
            help="Quantidade de empresas/grupos únicos mapeados por nível de prioridade comercial (TEC)"
        )
        st.markdown(
            f'<p style="color: #2D3142; font-size: 0.95rem; margin: 0;">Quantidade de empresas mapeadas por estratégia</p>',
            unsafe_allow_html=True
        )

    # Card 6: Ticket Médio (NOVO)
    with col6:
        st.metric(
            "💰 Ticket Médio",
            format_currency_abbreviated(ticket_medio_cfem),
            help="Ticket médio de CFEM e Valor Anual das minas mapeadas. Indica o perfil das minas na carteira."
        )
        st.markdown(
            f'<p style="color: #2D3142; font-size: 0.95rem; margin: 0;">'
            f'CFEM médio: {format_currency_abbreviated(ticket_medio_cfem)} por mina<br>'
            f'Valor Anual médio: {format_currency_abbreviated(ticket_medio_valor_anual)} por mina'
            f'</p>',
            unsafe_allow_html=True
        )


def build_filter_sidebar(df: pd.DataFrame) -> Dict:
    """
    Constrói filtros interativos na sidebar

    Args:
        df: DataFrame completo

    Returns:
        Dicionário com valores selecionados
    """
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros")

    filters = {}

    # ===== FILTROS GEOGRÁFICOS =====
    with st.sidebar.expander("📍 Filtros Geográficos", expanded=True):
        # Filtro: UF
        if 'uf' in df.columns:
            ufs = sorted(df['uf'].dropna().unique())
            filters['uf'] = st.multiselect(
                "Estado (UF)",
                options=ufs,
                default=[],
                key="filter_uf"
            )
        else:
            filters['uf'] = []

    # ===== FILTROS DE NEGÓCIO =====
    with st.sidebar.expander("🏢 Filtros de Negócio", expanded=True):
        # Filtro: TEC
        if 'tec' in df.columns:
            tec_options = sorted(df['tec'].dropna().unique())
            filters['tec'] = st.multiselect(
                "TEC (Estratégia)",
                options=tec_options,
                default=[],
                help="TEC01=cliente atual, TEC02=foco alto, TEC03=foco médio",
                key="filter_tec"
            )
        else:
            filters['tec'] = []

        # Filtro: Grupo/PAI (excluindo NA e FORA)
        if 'pai' in df.columns:
            grupos = sorted(
                df[~df['pai'].isin(['NA', 'FORA', 'na', 'fora', ''])]['pai'].dropna().unique()
            )
            filters['pai'] = st.multiselect(
                "Grupo/Holding",
                options=grupos,
                default=[],
                help="Grupos NA e FORA excluídos das opções",
                key="filter_pai"
            )
        else:
            filters['pai'] = []

        # Filtro: Terceiriza Lavra
        if 'terceiriza_lavra?' in df.columns:
            terceiriza_options = sorted(df['terceiriza_lavra?'].dropna().unique())
            filters['Terceiriza'] = st.multiselect(
                "Terceiriza Lavra?",
                options=terceiriza_options,
                default=[],
                key="filter_terceiriza"
            )
        else:
            filters['Terceiriza'] = []

    # ===== FILTROS TÉCNICOS =====
    with st.sidebar.expander("⛏️ Filtros Técnicos", expanded=True):
        # Filtro: Substância
        if 'substanciamaiscomercializada' in df.columns:
            substancias = sorted(df['substanciamaiscomercializada'].dropna().unique())
            filters['substancia'] = st.multiselect(
                "Substância Mineral",
                options=substancias,
                default=[],
                key="filter_substancia"
            )
        else:
            filters['substancia'] = []

        # Filtro: Status Mapeamento
        if 'status_mapeamento' in df.columns:
            status_option = st.radio(
                "Status Mapeamento",
                options=['Todos', 'Mapeados', 'Não Mapeados'],
                index=0,
                key="filter_status"
            )
            if status_option == 'Mapeados':
                filters['status_mapeamento'] = ['Sim']
            elif status_option == 'Não Mapeados':
                filters['status_mapeamento'] = ['Não']
            else:
                filters['status_mapeamento'] = ['Sim', 'Não']
        else:
            filters['status_mapeamento'] = []

        # Filtro: Faixa CFEM
        if 'totalvalorrecolhido' in df.columns:
            cfem_min = float(df['totalvalorrecolhido'].min())
            cfem_max = float(df['totalvalorrecolhido'].max())

            if cfem_min < cfem_max:
                filters['CFEM_range'] = st.slider(
                    "Faixa CFEM (R$)",
                    min_value=cfem_min,
                    max_value=cfem_max,
                    value=(cfem_min, cfem_max),
                    format="R$ %.0f",
                    key="filter_cfem"
                )
            else:
                filters['CFEM_range'] = (cfem_min, cfem_max)
        else:
            filters['CFEM_range'] = (0, 0)

    # Botões de controle (fora dos expanders)
    st.sidebar.markdown("---")

    # Botão para selecionar todos os filtros
    if st.sidebar.button("✅ Selecionar Todos nos Filtros", use_container_width=True):
        # Preenche todos os filtros multiselect com todas as opções
        if 'uf' in df.columns:
            st.session_state.filter_uf = sorted(df['uf'].dropna().unique())
        if 'tec' in df.columns:
            st.session_state.filter_tec = sorted(df['tec'].dropna().unique())
        if 'pai' in df.columns:
            st.session_state.filter_pai = sorted(
                df[~df['pai'].isin(['NA', 'FORA', 'na', 'fora', ''])]['pai'].dropna().unique()
            )
        if 'terceiriza_lavra?' in df.columns:
            st.session_state.filter_terceiriza = sorted(df['terceiriza_lavra?'].dropna().unique())
        if 'substanciamaiscomercializada' in df.columns:
            st.session_state.filter_substancia = sorted(df['substanciamaiscomercializada'].dropna().unique())
        st.rerun()

    # Botão para resetar filtros
    if st.sidebar.button("🔄 Resetar Filtros", use_container_width=True):
        # Deletar as keys do session_state ao invés de modificar
        keys_to_delete = [
            'filter_uf',
            'filter_tec',
            'filter_pai',
            'filter_terceiriza',
            'filter_substancia',
            'filter_status',
            'filter_cfem'
        ]

        for key in keys_to_delete:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()

    return filters


def apply_filters(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    """
    Aplica filtros ao DataFrame

    Args:
        df: DataFrame completo
        filters: Dicionário com valores dos filtros

    Returns:
        DataFrame filtrado
    """
    result = df.copy()

    # Filtro TEC
    if filters.get('tec') and len(filters['tec']) > 0:
        result = result[result['tec'].isin(filters['tec'])]

    # Filtro Status Mapeamento
    if filters.get('status_mapeamento') and len(filters['status_mapeamento']) > 0:
        result = result[result['status_mapeamento'].isin(filters['status_mapeamento'])]

    # Filtro Substância
    if filters.get('substancia') and len(filters['substancia']) > 0:
        result = result[result['substanciamaiscomercializada'].isin(filters['substancia'])]

    # Filtro UF
    if filters.get('uf') and len(filters['uf']) > 0:
        result = result[result['uf'].isin(filters['uf'])]

    # Filtro PAI (sempre mantém NA/FORA independente do filtro)
    if filters.get('pai') and len(filters['pai']) > 0:
        # Inclui os grupos selecionados + variações de NA/FORA (case-insensitive)
        grupos_permitidos = filters['pai'] + ['NA', 'FORA', 'na', 'fora', 'Na', 'Fora']
        # Também mantém registros com PAI vazio ou None
        result = result[
            result['pai'].isin(grupos_permitidos) |
            result['pai'].isna() |
            (result['pai'] == '')
        ]

    # Filtro Faixa CFEM
    if filters.get('CFEM_range') and 'totalvalorrecolhido' in result.columns:
        cfem_min, cfem_max = filters['CFEM_range']
        result = result[
            (result['totalvalorrecolhido'] >= cfem_min) &
            (result['totalvalorrecolhido'] <= cfem_max)
        ]

    # Filtro Terceiriza
    if filters.get('Terceiriza') and len(filters['Terceiriza']) > 0:
        result = result[result['terceiriza_lavra?'].isin(filters['Terceiriza'])]

    return result


def format_display_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Formata DataFrame para exibição na tabela detalhada
    Seleciona e formata as 12 colunas principais

    Args:
        df: DataFrame filtrado

    Returns:
        DataFrame formatado para exibição
    """
    # Colunas a exibir (na ordem especificada)
    display_columns = [
        'pai',
        'empresa_por_cnpj',
        'município',
        'uf',
        'substanciamaiscomercializada',
        'totalvalorrecolhido',
        'totalquantidadecomercializada',
        'tec',
        'status_mapeamento',
        'valor_anual_mapeado',
        'primeiro_escopo',
        'terceiriza_lavra?'
    ]

    # Seleciona apenas colunas que existem
    available_columns = [col for col in display_columns if col in df.columns]
    result = df[available_columns].copy()

    # Renomeia colunas para exibição mais amigável
    column_names = {
        'pai': 'Grupo',
        'empresa_por_cnpj': 'Empresa',
        'município': 'município',
        'uf': 'uf',
        'substanciamaiscomercializada': 'Substância',
        'totalvalorrecolhido': 'CFEM 2024 (R$)',
        'totalquantidadecomercializada': 'Volume (t)',
        'tec': 'tec',
        'status_mapeamento': 'Mapeado?',
        'valor_anual_mapeado': 'Valor Anual (R$)',
        'primeiro_escopo': 'Escopo',
        'terceiriza_lavra?': 'Terceiriza?'
    }

    result = result.rename(columns=column_names)

    # Formata valores numéricos para exibição
    if 'CFEM 2024 (R$)' in result.columns:
        result['CFEM 2024 (R$)'] = result['CFEM 2024 (R$)'].apply(
            lambda x: format_currency(x) if pd.notna(x) else 'R$ 0,00'
        )

    if 'Volume (t)' in result.columns:
        result['Volume (t)'] = result['Volume (t)'].apply(
            lambda x: format_number(x, decimals=2) if pd.notna(x) else '0'
        )

    if 'Valor Anual (R$)' in result.columns:
        result['Valor Anual (R$)'] = result['Valor Anual (R$)'].apply(
            lambda x: format_currency(x) if pd.notna(x) else 'R$ 0,00'
        )

    # Ordena por CFEM decrescente (se coluna existe e tem dados numéricos originais)
    # Como formatamos as strings, precisamos ordenar antes da formatação
    # Vamos reordenar usando o DataFrame original
    if 'totalvalorrecolhido' in df.columns:
        # Pega os índices ordenados
        sorted_indices = df[available_columns].sort_values(
            'totalvalorrecolhido',
            ascending=False
        ).index
        result = result.loc[sorted_indices]

    return result


# =====================================================================
# FUNÇÕES AUXILIARES - ANÁLISE ESTRATÉGICA
# =====================================================================

def calculate_pareto_80(df: pd.DataFrame, group_column: str = None, value_column: str = 'totalvalorrecolhido') -> pd.DataFrame:
    """
    Calcula Pareto: identifica registros que somam 80% do valor total

    Args:
        df: DataFrame completo
        group_column: Nome da coluna para agrupar (opcional). Se None, usa linhas individuais
        value_column: Nome da coluna de valor para somar

    Returns:
        DataFrame contendo apenas os registros que somam 80% do total
    """
    if group_column:
        # Agrupa e soma
        df_grouped = df.groupby(group_column)[value_column].sum().reset_index()
        df_grouped = df_grouped.sort_values(value_column, ascending=False)

        # Calcula % acumulado
        total = df_grouped[value_column].sum()
        df_grouped['percent_acum'] = (df_grouped[value_column].cumsum() / total * 100)

        # Filtra até 80%
        df_pareto = df_grouped[df_grouped['percent_acum'] <= 80].copy()

        return df_pareto
    else:
        # Trabalha com registros individuais
        df_sorted = df.sort_values(value_column, ascending=False).copy()

        # Calcula % acumulado
        total = df_sorted[value_column].sum()
        df_sorted['percent_acum'] = (df_sorted[value_column].cumsum() / total * 100)

        # Filtra até 80%
        df_pareto = df_sorted[df_sorted['percent_acum'] <= 80].copy()

        return df_pareto


def calculate_tec_weight(tec_value: str) -> int:
    """
    Retorna peso numérico para cada TEC (usado em score de prioridade)

    Args:
        tec_value: Valor do TEC (ex: 'TEC01', 'TEC02', etc)

    Returns:
        Peso de 1 a 5
    """
    if pd.isna(tec_value):
        return 0

    tec_str = str(tec_value).upper().strip()

    weights = {
        'TEC01': 5,
        'TEC02': 4,
        'TEC03': 3,
        'TEC04': 2,
        'TEC05': 1
    }

    return weights.get(tec_str, 0)


# =====================================================================
# SEÇÃO 1: ANÁLISE DE PARETO DE MINAS
# =====================================================================

def render_secao1_pareto_minas(df: pd.DataFrame) -> None:
    """
    Renderiza Seção 1: Análise de Pareto de Minas
    - Gráfico de Pareto das ~50 minas que representam 80% do CFEM
    - 4 Cards KPI
    """
    st.header("📊 Análise de Pareto - Concentração de Mercado")
    st.caption("Identificação das minas que representam 80% do CFEM total")

    # Calcula Pareto (minas que somam 80%)
    df_pareto = calculate_pareto_80(df, group_column=None, value_column='totalvalorrecolhido')

    # Total geral
    total_minas = len(df)
    cfem_total = df['totalvalorrecolhido'].sum()

    # Métricas do Pareto
    qtd_minas_pareto = len(df_pareto)
    perc_minas_pareto = (qtd_minas_pareto / total_minas * 100) if total_minas > 0 else 0
    cfem_pareto = df_pareto['totalvalorrecolhido'].sum()

    # === A) GRÁFICO DE PARETO INTERATIVO ===
    st.subheader("Gráfico de Pareto das Minas")

    # Prepara dados para o gráfico
    df_pareto_chart = df_pareto.copy()
    df_pareto_chart['index'] = range(1, len(df_pareto_chart) + 1)

    # Cria figura com eixo Y secundário
    fig = go.Figure()

    # Barras: CFEM individual
    fig.add_trace(go.Bar(
        x=df_pareto_chart['index'],
        y=df_pareto_chart['totalvalorrecolhido'],
        name='CFEM Individual',
        marker=dict(
            color='#95A3B3',
            showscale=False
        ),
        customdata=df_pareto_chart[[
            'chaveprimaria' if 'chaveprimaria' in df_pareto_chart.columns else 'empresa_por_cnpj',
            'pai',
            'município',
            'uf',
            'substanciamaiscomercializada',
            'totalvalorrecolhido',
            'status_mapeamento',
            'primeiro_escopo',
            'valor_total_mensal',
            'valor_anual_mapeado',
            'tec'
        ]].values if all(col in df_pareto_chart.columns for col in ['pai', 'município', 'uf', 'substanciamaiscomercializada', 'status_mapeamento']) else None,
        hovertemplate="<b>%{customdata[0]}</b><br>" +
                      "🏢 Grupo: %{customdata[1]}<br>" +
                      "📍 Localização: %{customdata[2]} - %{customdata[3]}<br>" +
                      "⛏️ Substância: %{customdata[4]}<br>" +
                      "💰 CFEM 2024: R$ %{customdata[5]:,.2f}<br>" +
                      "📊 Status: %{customdata[6]}<br>" +
                      "📋 Escopo: %{customdata[7]}<br>" +
                      "💵 Valor Mensal: R$ %{customdata[8]:,.2f}<br>" +
                      "💰 Valor Anual: R$ %{customdata[9]:,.2f}<br>" +
                      "🎯 TEC: %{customdata[10]}<br>" +
                      "<extra></extra>"
    ))

    # Linha: % acumulado
    fig.add_trace(go.Scatter(
        x=df_pareto_chart['index'],
        y=df_pareto_chart['percent_acum'],
        name='% Acumulado',
        yaxis='y2',
        line=dict(color='#FF6B35', width=3),
        mode='lines+markers',
        marker=dict(size=4),
        hovertemplate="Acumulado: %{y:.1f}%<extra></extra>"
    ))

    # Linha vertical no ponto de 80%
    fig.add_hline(
        y=80,
        line_dash="dash",
        line_color="#FF6B35",
        annotation_text="80%",
        annotation_position="right",
        yref='y2'
    )

    # Layout
    fig.update_layout(
        title=f"Pareto: {qtd_minas_pareto} minas representam 80% do CFEM",
        xaxis=dict(
            title="Índice das Minas (ordenadas por CFEM decrescente)",
            showticklabels=True
        ),
        yaxis=dict(
            title="CFEM Individual (R$)",
            side='left'
        ),
        yaxis2=dict(
            title="% CFEM Acumulado",
            overlaying='y',
            side='right',
            range=[0, 105]
        ),
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode='closest',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # === B) 4 CARDS KPI ===
    col1, col2, col3, col4 = st.columns(4)

    # Card 1: Concentração 80%
    with col1:
        st.metric(
            "🎯 Concentração 80%",
            f"{qtd_minas_pareto:,}".replace(',', '.') + " minas",
            delta=f"{perc_minas_pareto:.1f}% do total de {total_minas:,}".replace(',', '.')
        )
        st.markdown(f'<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">{format_currency_abbreviated(cfem_pareto)} em CFEM</p>', unsafe_allow_html=True)

    # Card 2: Mapeamento
    minas_mapeadas_pareto = len(df_pareto[df_pareto['status_mapeamento'] == 'Sim']) if 'status_mapeamento' in df_pareto.columns else 0
    perc_mapeadas_pareto = (minas_mapeadas_pareto / qtd_minas_pareto * 100) if qtd_minas_pareto > 0 else 0
    gap_pareto = qtd_minas_pareto - minas_mapeadas_pareto

    with col2:
        st.metric(
            "📊 Minas Mapeadas no Pareto",
            f"{minas_mapeadas_pareto} de {qtd_minas_pareto}",
            delta=f"{perc_mapeadas_pareto:.1f}% do pareto mapeado"
        )
        st.markdown(f'<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Gap: {gap_pareto} minas prioritárias</p>', unsafe_allow_html=True)

    # Card 3: Valor Capturado
    valor_anual_pareto = df_pareto[df_pareto['status_mapeamento'] == 'Sim']['valor_anual_mapeado'].sum() if 'valor_anual_mapeado' in df_pareto.columns else 0
    valor_anual_pareto_bi = valor_anual_pareto / 1_000_000_000
    cfem_pareto_bi = cfem_pareto / 1_000_000_000
    taxa_captura = (valor_anual_pareto / cfem_pareto * 100) if cfem_pareto > 0 else 0

    with col3:
        st.metric(
            "💰 Valor Anual Capturado",
            f"R$ {valor_anual_pareto_bi:.2f} Bi mapeado"
        )
        st.markdown(f'<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Potencial: R$ {cfem_pareto_bi:.2f} Bi | Captura: {taxa_captura:.1f}%</p>', unsafe_allow_html=True)

    # Card 4: Distribuição por TEC
    tec_counts = df_pareto['tec'].value_counts() if 'tec' in df_pareto.columns else pd.Series()
    tec01 = tec_counts.get('TEC01', 0)
    tec02 = tec_counts.get('TEC02', 0)
    tec03 = tec_counts.get('TEC03', 0)
    tec04 = tec_counts.get('TEC04', 0)
    tec05 = tec_counts.get('TEC05', 0)

    with col4:
        st.metric(
            "🎯 Distribuição por TEC",
            f"TEC01: {tec01} | TEC02: {tec02}"
        )
        st.markdown(f'<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">TEC03: {tec03} | TEC04: {tec04} | TEC05: {tec05}</p>', unsafe_allow_html=True)


# =====================================================================
# SEÇÃO 2: ANÁLISE DE GRUPOS/HOLDINGS
# =====================================================================

def render_secao2_analise_grupos(df: pd.DataFrame) -> None:
    """
    Renderiza Seção 2: Análise de Grupos/Holdings
    - Gráfico Pareto por Grupo (TOP 15)
    - 3 Cards KPI
    - Tabela TOP 10 Grupos
    """
    st.markdown("---")
    st.header("🏢 Análise de Grupos/Holdings")
    st.caption("Concentração por grupos empresariais e oportunidades")

    # Filtra grupos (excluindo NA/FORA)
    df_com_grupo = df[~df['pai'].isin(['NA', 'FORA', 'na', 'fora', '']) & df['pai'].notna()].copy()

    # === A) GRÁFICO: PARETO POR GRUPO ===
    st.subheader("Pareto por Grupo Empresarial")

    # Calcula Pareto por grupo
    df_grupos_pareto = calculate_pareto_80(df_com_grupo, group_column='pai', value_column='totalvalorrecolhido')

    # Pega TOP 15 grupos para o gráfico
    top15_grupos = df_grupos_pareto.head(15).copy()

    # Prepara informações adicionais para tooltip (7 campos focados em análise de grupos)
    cfem_total_geral = df_com_grupo['totalvalorrecolhido'].sum()
    grupos_info = []
    for grupo in top15_grupos['pai']:
        df_grupo = df_com_grupo[df_com_grupo['pai'] == grupo]
        qtd_minas = len(df_grupo)
        cfem_grupo = df_grupo['totalvalorrecolhido'].sum()
        perc_cfem_total = (cfem_grupo / cfem_total_geral * 100) if cfem_total_geral > 0 else 0

        qtd_mapeadas = len(df_grupo[df_grupo['status_mapeamento'] == 'Sim']) if 'status_mapeamento' in df_grupo.columns else 0
        perc_mapeadas = (qtd_mapeadas / qtd_minas * 100) if qtd_minas > 0 else 0
        valor_mensal = df_grupo[df_grupo['status_mapeamento'] == 'Sim']['valor_total_mensal'].sum() if 'valor_total_mensal' in df_grupo.columns else 0
        valor_anual = df_grupo[df_grupo['status_mapeamento'] == 'Sim']['valor_anual_mapeado'].sum() if 'valor_anual_mapeado' in df_grupo.columns else 0

        grupos_info.append({
            'grupo': grupo,
            'qtd_minas': qtd_minas,
            'cfem_total': cfem_grupo,
            'perc_cfem_total': perc_cfem_total,
            'qtd_mapeadas': qtd_mapeadas,
            'perc_mapeadas': perc_mapeadas,
            'valor_mensal': valor_mensal,
            'valor_anual': valor_anual
        })

    # Gráfico de barras verticais + linha (padronizado com gráfico de Minas)
    fig = go.Figure()

    # Prepara índice para eixo X
    top15_grupos['index'] = range(1, len(top15_grupos) + 1)

    # Barras verticais
    fig.add_trace(go.Bar(
        x=top15_grupos['index'],
        y=top15_grupos['totalvalorrecolhido'],
        name='CFEM por Grupo',
        marker=dict(
            color='#95A3B3',
            showscale=False
        ),
        customdata=[[
            info['grupo'],
            info['qtd_minas'],
            info['cfem_total'],
            info['perc_cfem_total'],
            info['qtd_mapeadas'],
            info['perc_mapeadas'],
            info['valor_mensal'],
            info['valor_anual']
        ] for info in grupos_info],
        hovertemplate="<b>Grupo: %{customdata[0]}</b><br>" +
                      "🏭 Minas: %{customdata[1]} minas<br>" +
                      "💰 CFEM: R$ %{customdata[2]:,.2f}<br>" +
                      "📊 Representa: %{customdata[3]:.1f}% do CFEM total<br>" +
                      "✅ Mapeadas: %{customdata[4]} de %{customdata[1]} (%{customdata[5]:.1f}%)<br>" +
                      "💵 Valor Mensal: R$ %{customdata[6]:,.2f}<br>" +
                      "💰 Valor Anual: R$ %{customdata[7]:,.2f}<br>" +
                      "<extra></extra>"
    ))

    # Linha de % acumulado (no eixo Y secundário direito)
    fig.add_trace(go.Scatter(
        x=top15_grupos['index'],
        y=top15_grupos['percent_acum'],
        name='% Acumulado',
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#FF6B35', width=3),
        marker=dict(size=4),
        hovertemplate="Acumulado: %{y:.1f}%<extra></extra>"
    ))

    # Linha horizontal no ponto de 80%
    fig.add_hline(
        y=80,
        line_dash="dash",
        line_color="#FF6B35",
        annotation_text="80%",
        annotation_position="right",
        yref='y2'
    )

    # Layout
    fig.update_layout(
        title=f"TOP 15 Grupos por CFEM",
        xaxis=dict(
            title="Índice dos Grupos (ordenados por CFEM decrescente)",
            showticklabels=True
        ),
        yaxis=dict(
            title="CFEM Total (R$)",
            side='left'
        ),
        yaxis2=dict(
            title="% CFEM Acumulado",
            overlaying='y',
            side='right',
            range=[0, 105]
        ),
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode='closest',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # === B) 4 CARDS KPI ===
    col1, col2, col3, col4 = st.columns(4)

    # Card 1: Concentração por Grupos (MANTÉM)
    qtd_grupos_pareto = len(df_grupos_pareto)
    qtd_minas_grupos_pareto = len(df_com_grupo[df_com_grupo['pai'].isin(df_grupos_pareto['pai'])])
    cfem_grupos_pareto = df_grupos_pareto['totalvalorrecolhido'].sum()

    with col1:
        st.metric(
            "🏢 Concentração por Grupos",
            f"{qtd_grupos_pareto} grupos = 80% CFEM"
        )
        st.markdown(f'<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Controlam {qtd_minas_grupos_pareto:,}'.replace(',', '.') + f' minas | {format_currency_abbreviated(cfem_grupos_pareto)}</p>', unsafe_allow_html=True)

    # Card 2: TOP 3 Substâncias nos Grupos Pareto (NOVO)
    df_grupos_top = df_com_grupo[df_com_grupo['pai'].isin(df_grupos_pareto['pai'])]

    if 'substanciamaiscomercializada' in df_grupos_top.columns:
        top3_substancias = df_grupos_top.groupby('substanciamaiscomercializada')['totalvalorrecolhido'].sum().nlargest(3)
        cfem_total_pareto = df_grupos_top['totalvalorrecolhido'].sum()

        with col2:
            st.metric(
                "⛏️ Substâncias Prioritárias",
                f"{top3_substancias.index[0]}: {format_currency_abbreviated(top3_substancias.iloc[0])}" if len(top3_substancias) > 0 else "N/A"
            )
            linhas_substancias = []
            for idx, (substancia, cfem) in enumerate(top3_substancias.items()):
                perc = (cfem / cfem_total_pareto * 100) if cfem_total_pareto > 0 else 0
                if idx == 0:
                    linhas_substancias.append(f"({perc:.0f}%)")
                else:
                    linhas_substancias.append(f"{substancia}: {format_currency_abbreviated(cfem)} ({perc:.0f}%)")
            st.markdown(f'<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">{" | ".join(linhas_substancias)}</p>', unsafe_allow_html=True)
    else:
        with col2:
            st.metric("⛏️ Substâncias Prioritárias", "N/A")

    # Card 3: TOP 3 Estados nos Grupos Pareto (NOVO)
    if 'uf' in df_grupos_top.columns:
        top3_estados = df_grupos_top.groupby('uf').agg({
            'chaveprimaria': 'count',  # Conta minas
            'totalvalorrecolhido': 'sum'  # Soma CFEM
        }).rename(columns={'chaveprimaria': 'qtd_minas', 'totalvalorrecolhido': 'cfem'})
        top3_estados = top3_estados.sort_values('qtd_minas', ascending=False).head(3)

        with col3:
            st.metric(
                "📍 Concentração Geográfica",
                f"{top3_estados.index[0]}: {int(top3_estados.iloc[0]['qtd_minas'])} minas" if len(top3_estados) > 0 else "N/A"
            )
            linhas_estados = []
            for idx, (uf, row) in enumerate(top3_estados.iterrows()):
                if idx == 0:
                    linhas_estados.append(f"({format_currency_abbreviated(row['cfem'])})")
                else:
                    linhas_estados.append(f"{uf}: {int(row['qtd_minas'])} minas ({format_currency_abbreviated(row['cfem'])})")
            st.markdown(f'<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">{" | ".join(linhas_estados)}</p>', unsafe_allow_html=True)
    else:
        with col3:
            st.metric("📍 Concentração Geográfica", "N/A")

    # Card 4: Grupos com Oportunidades (ADAPTADO)
    # Identifica grupos que TÊM pelo menos 1 mina não mapeada
    grupos_com_gap = df_grupos_top[df_grupos_top['status_mapeamento'] == 'Não']['pai'].nunique() if 'status_mapeamento' in df_grupos_top.columns else 0

    # CFEM e minas não mapeadas nos grupos TOP
    df_minas_nao_mapeadas = df_grupos_top[df_grupos_top['status_mapeamento'] == 'Não'] if 'status_mapeamento' in df_grupos_top.columns else df_grupos_top
    cfem_gap_grupos = df_minas_nao_mapeadas['totalvalorrecolhido'].sum()
    qtd_minas_gap_grupos = len(df_minas_nao_mapeadas)

    with col4:
        st.metric(
            "💼 Grupos com Oportunidades",
            f"{grupos_com_gap} grupos têm GAP"
        )
        st.markdown(f'<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Potencial: {format_currency_abbreviated(cfem_gap_grupos)} | {qtd_minas_gap_grupos} minas</p>', unsafe_allow_html=True)

    # === C) TABELA ESTRATÉGICA: MINAS NÃO MAPEADAS NOS GRUPOS PRIORITÁRIOS ===
    st.subheader("Minas Não Mapeadas nos Grupos Prioritários")

    # 1. Pega TOP 10 grupos do Pareto
    top10_grupos = df_grupos_pareto.head(10)['pai'].tolist()

    # 2. Filtra minas NÃO MAPEADAS desses grupos
    df_minas_top_grupos = df_com_grupo[df_com_grupo['pai'].isin(top10_grupos)]
    df_minas_nao_mapeadas_top = df_minas_top_grupos[df_minas_top_grupos['status_mapeamento'] == 'Não'].copy() if 'status_mapeamento' in df_minas_top_grupos.columns else df_minas_top_grupos.copy()

    if len(df_minas_nao_mapeadas_top) > 0:
        # 3. Calcula score de prioridade (CFEM × Peso TEC)
        df_minas_nao_mapeadas_top['tec_weight'] = df_minas_nao_mapeadas_top['tec'].apply(calculate_tec_weight) if 'tec' in df_minas_nao_mapeadas_top.columns else 0
        df_minas_nao_mapeadas_top['score_prioridade'] = df_minas_nao_mapeadas_top['totalvalorrecolhido'] * df_minas_nao_mapeadas_top['tec_weight']

        # 4. Ordena por score decrescente
        df_minas_nao_mapeadas_top = df_minas_nao_mapeadas_top.sort_values('score_prioridade', ascending=False)

        # 5. Pega TOP 20 minas
        df_top20_minas = df_minas_nao_mapeadas_top.head(20)

        # 6. Prepara dados para exibição (8 colunas)
        tabela_minas = []
        for idx, row in enumerate(df_top20_minas.itertuples(), 1):
            tabela_minas.append({
                '#': idx,
                'Mina': str(getattr(row, 'chaveprimaria', getattr(row, 'empresa_por_cnpj', 'N/A')))[:40],
                'Grupo': str(getattr(row, 'pai', 'N/A'))[:25],
                'UF': getattr(row, 'uf', 'N/A'),
                'Município': str(getattr(row, 'município', 'N/A'))[:25],
                'Substância': str(getattr(row, 'substanciamaiscomercializada', 'N/A'))[:20],
                'CFEM 2024': format_currency_abbreviated(getattr(row, 'totalvalorrecolhido', 0)),
                'TEC': getattr(row, 'tec', 'N/A'),
                'Score': f"{getattr(row, 'score_prioridade', 0):,.0f}".replace(',', '.')
            })

        df_tabela_minas = pd.DataFrame(tabela_minas)

        # 7. Exibe tabela simples (sem styling complexo)
        st.dataframe(df_tabela_minas, use_container_width=True, height=450)

        # 8. Nota explicativa
        st.caption("💡 **Score de Prioridade** = CFEM × Peso TEC (TEC01=5, TEC02=4, TEC03=3, TEC04=2, TEC05=1)")
    else:
        st.info("✅ Todas as minas dos grupos prioritários estão mapeadas!")


# =====================================================================
# SEÇÃO 3: GAP DE OPORTUNIDADES
# =====================================================================

def render_secao3_gap_oportunidades(df: pd.DataFrame) -> None:
    """
    Renderiza Seção 3: GAP de Oportunidades
    - 4 Cards de GAP
    - Tabela TOP 20 Oportunidades Não Mapeadas
    """
    st.markdown("---")
    st.header("🎯 GAP de Oportunidades - Minas Não Mapeadas")
    st.caption("Priorização de ações comerciais em minas de alto valor não mapeadas")

    # Filtra minas não mapeadas
    df_gap = df[df['status_mapeamento'] == 'Não'].copy() if 'status_mapeamento' in df.columns else df.copy()

    # === A) 4 CARDS DE GAP ===
    col1, col2, col3, col4 = st.columns(4)

    # Card 1: Potencial Total Não Mapeado
    qtd_nao_mapeadas = len(df_gap)
    cfem_gap = df_gap['totalvalorrecolhido'].sum()
    cfem_gap_bi = cfem_gap / 1_000_000_000
    grupos_gap = df_gap['pai'].nunique() if 'pai' in df_gap.columns else 0

    with col1:
        st.metric(
            "🎯 Potencial Não Mapeado",
            f"R$ {cfem_gap_bi:.2f} Bi CFEM"
        )
        st.caption(f"{qtd_nao_mapeadas:,}".replace(',', '.') + f" minas | {grupos_gap} grupos")

    # Card 2: Maior Oportunidade Individual
    if len(df_gap) > 0:
        maior_opp = df_gap.nlargest(1, 'totalvalorrecolhido').iloc[0]
        nome_maior_opp = maior_opp.get('empresa_por_cnpj', maior_opp.get('chaveprimaria', 'N/A'))
        if len(str(nome_maior_opp)) > 30:
            nome_maior_opp = str(nome_maior_opp)[:27] + "..."
        cfem_maior_opp = maior_opp['totalvalorrecolhido'] / 1_000_000  # Em milhões
        uf_maior_opp = maior_opp.get('uf', 'N/A')
        tec_maior_opp = maior_opp.get('tec', 'N/A')
        substancia_maior_opp = maior_opp.get('substanciamaiscomercializada', 'N/A')

        with col2:
            st.metric(
                "🏆 Maior Oportunidade",
                nome_maior_opp
            )
            st.caption(f"{uf_maior_opp} - R$ {cfem_maior_opp:.2f} Mi | TEC: {tec_maior_opp} | {substancia_maior_opp}")
    else:
        with col2:
            st.metric("🏆 Maior Oportunidade", "N/A")

    # Card 3: Alto Potencial (TEC01 + TEC02)
    df_tec_prioritarias = df_gap[df_gap['tec'].isin(['TEC01', 'TEC02'])] if 'tec' in df_gap.columns else pd.DataFrame()
    qtd_tec_prioritarias = len(df_tec_prioritarias)
    cfem_tec_prioritarias = df_tec_prioritarias['totalvalorrecolhido'].sum() if len(df_tec_prioritarias) > 0 else 0
    cfem_tec_prioritarias_bi = cfem_tec_prioritarias / 1_000_000_000
    perc_gap_tec = (cfem_tec_prioritarias / cfem_gap * 100) if cfem_gap > 0 else 0

    with col3:
        st.metric(
            "⚡ Oportunidades Prioritárias",
            f"{qtd_tec_prioritarias} minas TEC01/02"
        )
        st.caption(f"R$ {cfem_tec_prioritarias_bi:.2f} Bi | {perc_gap_tec:.1f}% do gap")

    # Card 4: Concentração do GAP
    if len(df_gap) > 0 and 'uf' in df_gap.columns:
        top_ufs_gap = df_gap.groupby('uf')['totalvalorrecolhido'].sum().nlargest(3)
        top3_ufs = ", ".join(top_ufs_gap.index[:3])
    else:
        top3_ufs = "N/A"

    if len(df_gap) > 0 and 'pai' in df_gap.columns:
        df_gap_grupos = df_gap[~df_gap['pai'].isin(['NA', 'FORA', 'na', 'fora', '']) & df_gap['pai'].notna()]
        top_grupos_gap = df_gap_grupos.groupby('pai')['totalvalorrecolhido'].sum().nlargest(3)
        top3_grupos = ", ".join(top_grupos_gap.index[:3])
    else:
        top3_grupos = "N/A"

    with col4:
        st.metric(
            "📍 Onde Está o GAP",
            "80% concentrado em:"
        )
        st.caption(f"Estados: {top3_ufs}")
        st.caption(f"Grupos: {top3_grupos}")

    # === B) TABELA TOP 20 OPORTUNIDADES ===
    st.subheader("TOP 20 Oportunidades Não Mapeadas - Score de Prioridade")

    if len(df_gap) > 0:
        # Calcula score de prioridade
        df_gap['tec_weight'] = df_gap['tec'].apply(calculate_tec_weight) if 'tec' in df_gap.columns else 0
        df_gap['score_prioridade'] = df_gap['totalvalorrecolhido'] * df_gap['tec_weight']

        # Ordena e pega TOP 20
        df_top20_opp = df_gap.nlargest(20, 'score_prioridade').copy()

        # Prepara dados para exibição
        tabela_opp = []
        for idx, row in enumerate(df_top20_opp.itertuples(), 1):
            tabela_opp.append({
                '#': idx,
                'Mina/Chave': str(getattr(row, 'chaveprimaria', getattr(row, 'empresa_por_cnpj', 'N/A')))[:40],
                'Grupo': str(getattr(row, 'pai', 'N/A'))[:25],
                'UF': getattr(row, 'uf', 'N/A'),
                'Substância': str(getattr(row, 'substanciamaiscomercializada', 'N/A'))[:20],
                'CFEM (R$)': format_currency_abbreviated(getattr(row, 'totalvalorrecolhido', 0)),
                'TEC': getattr(row, 'tec', 'N/A'),
                'Score': f"{getattr(row, 'score_prioridade', 0):,.0f}".replace(',', '.')
            })

        df_tabela_opp = pd.DataFrame(tabela_opp)

        st.dataframe(df_tabela_opp, use_container_width=True, height=450)

        st.caption("💡 **Score de Prioridade** = CFEM × Peso TEC (TEC01=5, TEC02=4, TEC03=3, TEC04=2, TEC05=1)")
    else:
        st.info("✅ Todas as minas estão mapeadas! Não há GAP de oportunidades.")


# =====================================================================
# FUNÇÃO PRINCIPAL: RENDERIZA ANÁLISE ESTRATÉGICA COMPLETA
# =====================================================================

def render_analise_estrategica_section(df: pd.DataFrame) -> None:
    """
    Renderiza a página completa de Análise Estratégica
    Integra as 3 seções principais

    Args:
        df: DataFrame completo (sem filtros na Fase 1)
    """
    # SEÇÃO 1: Análise de Pareto de Minas
    render_secao1_pareto_minas(df)

    # SEÇÃO 2: Análise de Grupos/Holdings
    render_secao2_analise_grupos(df)

    # SEÇÃO 3: GAP de Oportunidades
    render_secao3_gap_oportunidades(df)


# =====================================================================
# SIMULAÇÃO DE POTENCIAL
# =====================================================================

def create_simulacao_filters(df: pd.DataFrame) -> Dict:
    """
    Constrói filtros específicos para simulação (10 filtros)

    Args:
        df: DataFrame completo

    Returns:
        Dicionário com valores dos filtros selecionados
    """
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtros de Simulação")

    filters = {}

    # ===== FILTROS GEOGRÁFICOS =====
    with st.sidebar.expander("📍 Filtros Geográficos", expanded=True):
        # Filtro: UF
        if 'uf' in df.columns:
            ufs = sorted(df['uf'].dropna().unique())
            filters['uf'] = st.multiselect(
                "Estado (UF)",
                options=ufs,
                default=[],
                key="sim_filter_uf"
            )
        else:
            filters['uf'] = []

    # ===== FILTROS DE NEGÓCIO =====
    with st.sidebar.expander("🏢 Filtros de Negócio", expanded=True):
        # Filtro: TEC
        if 'tec' in df.columns:
            tec_options = sorted(df['tec'].dropna().unique())
            filters['tec'] = st.multiselect(
                "TEC (Estratégia)",
                options=tec_options,
                default=[],
                help="TEC01=cliente atual, TEC02=foco alto, TEC03=foco médio",
                key="sim_filter_tec"
            )
        else:
            filters['tec'] = []

        # Filtro: Grupo (excluindo NA/FORA)
        if 'pai' in df.columns:
            grupos = sorted(
                df[~df['pai'].isin(['NA', 'FORA', 'na', 'fora', ''])]['pai'].dropna().unique()
            )
            filters['pai'] = st.multiselect(
                "Grupo/Holding",
                options=grupos,
                default=[],
                help="Grupos NA e FORA excluídos das opções",
                key="sim_filter_pai"
            )
        else:
            filters['pai'] = []

        # Filtro: Possui Grupo? (NOVO)
        filters['possui_grupo'] = st.multiselect(
            "Possui Grupo?",
            options=['Com Grupo', 'Sem Grupo'],
            default=[],
            help="Com Grupo = minas que pertencem a holdings",
            key="sim_filter_possui_grupo"
        )

        # Filtro: Status Mapeamento
        if 'status_mapeamento' in df.columns:
            status_option = st.radio(
                "Status Mapeamento",
                options=['Todos', 'Mapeados', 'Não Mapeados'],
                index=0,
                key="sim_filter_status"
            )
            if status_option == 'Mapeados':
                filters['status_mapeamento'] = ['Sim']
            elif status_option == 'Não Mapeados':
                filters['status_mapeamento'] = ['Não']
            else:
                filters['status_mapeamento'] = ['Sim', 'Não']
        else:
            filters['status_mapeamento'] = []

        # Filtro: Terceiriza Lavra
        if 'terceiriza_lavra?' in df.columns:
            terceiriza_options = sorted(df['terceiriza_lavra?'].dropna().unique())
            filters['terceiriza'] = st.multiselect(
                "Terceiriza Lavra?",
                options=terceiriza_options,
                default=[],
                key="sim_filter_terceiriza"
            )
        else:
            filters['terceiriza'] = []

    # ===== FILTROS TÉCNICOS =====
    with st.sidebar.expander("⛏️ Filtros Técnicos", expanded=True):
        # Filtro: Substância
        if 'substanciamaiscomercializada' in df.columns:
            substancias = sorted(df['substanciamaiscomercializada'].dropna().unique())
            filters['substancia'] = st.multiselect(
                "Substância Mineral",
                options=substancias,
                default=[],
                key="sim_filter_substancia"
            )
        else:
            filters['substancia'] = []

        # Filtro: Porte da Mina por Quartis (NOVO)
        if 'totalvalorrecolhido' in df.columns:
            # Calcula quartis (apenas valores > 0)
            df_valores_positivos = df[df['totalvalorrecolhido'] > 0]
            if len(df_valores_positivos) > 0:
                q25 = df_valores_positivos['totalvalorrecolhido'].quantile(0.25)
                q50 = df_valores_positivos['totalvalorrecolhido'].quantile(0.50)
                q75 = df_valores_positivos['totalvalorrecolhido'].quantile(0.75)

                porte_options = [
                    f"🟢 Pequeno (até {format_currency_abbreviated(q25)})",
                    f"🟡 Médio-Baixo ({format_currency_abbreviated(q25)} - {format_currency_abbreviated(q50)})",
                    f"🟠 Médio-Alto ({format_currency_abbreviated(q50)} - {format_currency_abbreviated(q75)})",
                    f"🔴 Grande (acima de {format_currency_abbreviated(q75)})"
                ]

                filters['porte'] = st.multiselect(
                    "Porte da Mina (por CFEM)",
                    options=porte_options,
                    default=[],
                    help="Classificação baseada em quartis do CFEM",
                    key="sim_filter_porte"
                )
                # Guarda quartis para uso posterior
                filters['quartis'] = (q25, q50, q75)
            else:
                filters['porte'] = []
                filters['quartis'] = None

        # Filtro: Faixa CFEM
        if 'totalvalorrecolhido' in df.columns:
            cfem_min = float(df['totalvalorrecolhido'].min())
            cfem_max = float(df['totalvalorrecolhido'].max())

            if cfem_min < cfem_max:
                filters['cfem_range'] = st.slider(
                    "Faixa CFEM (R$)",
                    min_value=cfem_min,
                    max_value=cfem_max,
                    value=(cfem_min, cfem_max),
                    format="R$ %.0f",
                    key="sim_filter_cfem"
                )
            else:
                filters['cfem_range'] = (cfem_min, cfem_max)
        else:
            filters['cfem_range'] = (0, 0)

    # Botões de controle
    st.sidebar.markdown("---")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("✅ Todos", use_container_width=True, key="sim_btn_todos"):
            # Preenche todos os filtros
            if 'uf' in df.columns:
                st.session_state.sim_filter_uf = sorted(df['uf'].dropna().unique())
            if 'tec' in df.columns:
                st.session_state.sim_filter_tec = sorted(df['tec'].dropna().unique())
            if 'pai' in df.columns:
                st.session_state.sim_filter_pai = sorted(
                    df[~df['pai'].isin(['NA', 'FORA', 'na', 'fora', ''])]['pai'].dropna().unique()
                )
            if 'terceiriza_lavra?' in df.columns:
                st.session_state.sim_filter_terceiriza = sorted(df['terceiriza_lavra?'].dropna().unique())
            if 'substanciamaiscomercializada' in df.columns:
                st.session_state.sim_filter_substancia = sorted(df['substanciamaiscomercializada'].dropna().unique())
            st.rerun()

    with col2:
        if st.button("🔄 Resetar", use_container_width=True, key="sim_btn_resetar"):
            # Remove keys do session_state
            keys_to_delete = [k for k in st.session_state.keys() if k.startswith('sim_filter_')]
            for key in keys_to_delete:
                del st.session_state[key]
            st.rerun()

    return filters


def apply_simulacao_filters(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    """
    Aplica filtros ao DataFrame para simulação

    Args:
        df: DataFrame completo
        filters: Dicionário com valores dos filtros

    Returns:
        DataFrame filtrado
    """
    result = df.copy()

    # Filtro TEC
    if filters.get('tec') and len(filters['tec']) > 0:
        result = result[result['tec'].isin(filters['tec'])]

    # Filtro UF
    if filters.get('uf') and len(filters['uf']) > 0:
        result = result[result['uf'].isin(filters['uf'])]

    # Filtro Grupo (sempre mantém NA/FORA independente do filtro)
    if filters.get('pai') and len(filters['pai']) > 0:
        grupos_permitidos = filters['pai'] + ['NA', 'FORA', 'na', 'fora', 'Na', 'Fora']
        result = result[
            result['pai'].isin(grupos_permitidos) |
            result['pai'].isna() |
            (result['pai'] == '')
        ]

    # Filtro Possui Grupo (NOVO)
    if filters.get('possui_grupo') and len(filters['possui_grupo']) > 0:
        if 'Com Grupo' in filters['possui_grupo'] and 'Sem Grupo' not in filters['possui_grupo']:
            # Apenas com grupo
            result = result[
                ~result['pai'].isin(['NA', 'FORA', 'na', 'fora', '']) &
                result['pai'].notna()
            ]
        elif 'Sem Grupo' in filters['possui_grupo'] and 'Com Grupo' not in filters['possui_grupo']:
            # Apenas sem grupo
            result = result[
                result['pai'].isin(['NA', 'FORA', 'na', 'fora', '']) |
                result['pai'].isna()
            ]

    # Filtro Status Mapeamento
    if filters.get('status_mapeamento') and len(filters['status_mapeamento']) > 0:
        result = result[result['status_mapeamento'].isin(filters['status_mapeamento'])]

    # Filtro Substância
    if filters.get('substancia') and len(filters['substancia']) > 0:
        result = result[result['substanciamaiscomercializada'].isin(filters['substancia'])]

    # Filtro Terceiriza
    if filters.get('terceiriza') and len(filters['terceiriza']) > 0:
        result = result[result['terceiriza_lavra?'].isin(filters['terceiriza'])]

    # Filtro Porte (NOVO)
    if filters.get('porte') and len(filters['porte']) > 0 and filters.get('quartis'):
        q25, q50, q75 = filters['quartis']
        porte_masks = []

        for porte_label in filters['porte']:
            if '🟢 Pequeno' in porte_label:
                porte_masks.append(result['totalvalorrecolhido'] <= q25)
            elif '🟡 Médio-Baixo' in porte_label:
                porte_masks.append(
                    (result['totalvalorrecolhido'] > q25) &
                    (result['totalvalorrecolhido'] <= q50)
                )
            elif '🟠 Médio-Alto' in porte_label:
                porte_masks.append(
                    (result['totalvalorrecolhido'] > q50) &
                    (result['totalvalorrecolhido'] <= q75)
                )
            elif '🔴 Grande' in porte_label:
                porte_masks.append(result['totalvalorrecolhido'] > q75)

        if porte_masks:
            combined_mask = porte_masks[0]
            for mask in porte_masks[1:]:
                combined_mask = combined_mask | mask
            result = result[combined_mask]

    # Filtro Faixa CFEM
    if filters.get('cfem_range') and 'totalvalorrecolhido' in result.columns:
        cfem_min, cfem_max = filters['cfem_range']
        result = result[
            (result['totalvalorrecolhido'] >= cfem_min) &
            (result['totalvalorrecolhido'] <= cfem_max)
        ]

    return result


def render_cards_referencia_simulacao(df_total: pd.DataFrame, df_filtered: pd.DataFrame) -> None:
    """
    Renderiza 7 cards de referência (2 linhas)

    Args:
        df_total: DataFrame completo (sem filtros)
        df_filtered: DataFrame após aplicação dos filtros
    """
    st.subheader("📊 Base de Referência")

    # LINHA 1: 4 cards
    col1, col2, col3, col4 = st.columns(4)

    # Card 1: Total de Minas
    total_minas = len(df_filtered)
    perc_mercado = (total_minas / len(df_total) * 100) if len(df_total) > 0 else 0

    with col1:
        st.metric(
            "📊 Total de Minas",
            f"{total_minas:,}".replace(',', '.'),
            delta=f"{perc_mercado:.1f}% do mercado"
        )
        st.markdown(f'<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">({len(df_total):,} minas totais)</p>'.replace(',', '.'), unsafe_allow_html=True)

    # Card 2: CFEM Total da Base
    cfem_total = df_filtered['totalvalorrecolhido'].sum() if 'totalvalorrecolhido' in df_filtered.columns else 0
    cfem_mercado_total = df_total['totalvalorrecolhido'].sum() if 'totalvalorrecolhido' in df_total.columns else 0
    perc_cfem = (cfem_total / cfem_mercado_total * 100) if cfem_mercado_total > 0 else 0

    with col2:
        st.metric(
            "💰 CFEM Total da Base",
            format_currency_abbreviated(cfem_total),
            delta=f"{perc_cfem:.1f}% do CFEM total"
        )

    # Card 3: Distribuição por TEC
    if 'tec' in df_filtered.columns:
        # Filtrar apenas TEC01, TEC02, TEC03 e ordenar corretamente
        tecs_prioritarios = ['TEC01', 'TEC02', 'TEC03']
        df_tec_filtrado = df_filtered[df_filtered['tec'].isin(tecs_prioritarios)]
        tec_counts = df_tec_filtrado['tec'].value_counts().reindex(tecs_prioritarios, fill_value=0)
        tec_text = " | ".join([f"{tec}: {count}" for tec, count in tec_counts.items()])
    else:
        tec_text = "N/A"

    with col3:
        st.metric(
            "🎯 Distribuição por TEC",
            tec_text if tec_text else "N/A"
        )
        st.markdown('<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Quantidade de minas por estratégia</p>', unsafe_allow_html=True)

    # Card 4: Minas Mapeadas
    if 'status_mapeamento' in df_filtered.columns:
        minas_mapeadas = len(df_filtered[df_filtered['status_mapeamento'] == 'Sim'])
        perc_mapeadas = (minas_mapeadas / total_minas * 100) if total_minas > 0 else 0
    else:
        minas_mapeadas = 0
        perc_mapeadas = 0

    with col4:
        st.metric(
            "✅ Minas Mapeadas",
            f"{minas_mapeadas:,}".replace(',', '.'),
            delta=f"{perc_mapeadas:.1f}% da base selecionada"
        )

    # LINHA 2: 4 cards
    col1, col2, col3, col4 = st.columns(4)

    # Card 5: Valor Anual Mapeado
    if 'valor_anual_mapeado' in df_filtered.columns and 'status_mapeamento' in df_filtered.columns:
        valor_anual_mapeado = df_filtered[df_filtered['status_mapeamento'] == 'Sim']['valor_anual_mapeado'].sum()
    else:
        valor_anual_mapeado = 0

    # Cálculo do Ticket Médio de Valor Anual das Mapeadas
    df_mapeadas_base = df_filtered[df_filtered['status_mapeamento'] == 'Sim'] if 'status_mapeamento' in df_filtered.columns else pd.DataFrame()
    ticket_medio_valor_anual_ref = df_mapeadas_base['valor_anual_mapeado'].mean() if len(df_mapeadas_base) > 0 and 'valor_anual_mapeado' in df_mapeadas_base.columns else 0

    with col1:
        st.metric(
            "💵 Valor Anual Mapeado",
            format_currency_abbreviated(valor_anual_mapeado)
        )
        st.markdown('<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Receita atual das minas mapeadas</p>', unsafe_allow_html=True)

    # Card 6: Ticket Médio Valor Anual (NOVO)
    with col2:
        st.metric(
            "💰 Ticket Médio Valor Anual",
            format_currency_abbreviated(ticket_medio_valor_anual_ref),
            help="Valor anual médio por mina mapeada na base filtrada"
        )
        st.markdown('<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Valor anual médio por mina</p>', unsafe_allow_html=True)

    # Card 7: Taxa de Valor Mapeado (Indicador 4)
    if 'status_mapeamento' in df_filtered.columns and 'totalvalorrecolhido' in df_filtered.columns:
        cfem_mapeadas = df_filtered[df_filtered['status_mapeamento'] == 'Sim']['totalvalorrecolhido'].sum()
        taxa_valor = (valor_anual_mapeado / cfem_mapeadas * 100) if cfem_mapeadas > 0 else 0
    else:
        taxa_valor = 0

    with col3:
        st.metric(
            "📈 Taxa de Valor Mapeado",
            f"{taxa_valor:.2f}%",
            help="Quanto de valor anual foi mapeado em relação ao CFEM das minas já prospectadas"
        )
        st.markdown('<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Relação Valor/CFEM nas mapeadas</p>', unsafe_allow_html=True)

    # Card 7: Taxa TEC01 (Indicador 5)
    if 'tec' in df_filtered.columns and 'status_mapeamento' in df_filtered.columns:
        df_tec01 = df_filtered[
            (df_filtered['tec'] == 'TEC01') &
            (df_filtered['status_mapeamento'] == 'Sim')
        ]
        if len(df_tec01) > 0:
            cfem_tec01 = df_tec01['totalvalorrecolhido'].sum() if 'totalvalorrecolhido' in df_tec01.columns else 0
            valor_tec01 = df_tec01['valor_anual_mapeado'].sum() if 'valor_anual_mapeado' in df_tec01.columns else 0
            taxa_tec01 = (valor_tec01 / cfem_tec01 * 100) if cfem_tec01 > 0 else 0
        else:
            taxa_tec01 = 0
    else:
        taxa_tec01 = 0

    # Validações para display
    if 'tec' in df_filtered.columns and 'status_mapeamento' in df_filtered.columns:
        df_tec01_count = df_filtered[
            (df_filtered['tec'] == 'TEC01') &
            (df_filtered['status_mapeamento'] == 'Sim')
        ]
        num_minas_tec01 = len(df_tec01_count)

        if num_minas_tec01 < 5:
            taxa_tec01_display = "N/A"
            taxa_tec01_help = f"Amostra pequena ({num_minas_tec01} minas TEC01). Mínimo recomendado: 5 minas"
        else:
            taxa_tec01_display = f"{taxa_tec01:.2f}%"
            if taxa_tec01 > 500:
                taxa_tec01_help = f"Relação Valor/CFEM em minas TEC01 ({num_minas_tec01} minas). Taxa alta - verificar dados."
            else:
                taxa_tec01_help = f"Relação Valor/CFEM em minas TEC01 ({num_minas_tec01} minas)"
    else:
        taxa_tec01_display = "N/A"
        taxa_tec01_help = "Dados de TEC ou status de mapeamento não disponíveis"

    with col4:
        st.metric(
            "🎯 Taxa TEC01",
            taxa_tec01_display,
            help=taxa_tec01_help
        )
        st.markdown('<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Relação Valor/CFEM em minas TEC01</p>', unsafe_allow_html=True)


def render_configuracao_simulacao() -> None:
    """
    Renderiza seção de configuração da simulação
    """
    st.subheader("🎯 Configurar Simulação")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        percentual = st.number_input(
            "% do CFEM a Capturar",
            min_value=0.0,
            max_value=1000.0,
            value=30.0,
            step=1.0,
            key="percentual_simulacao",
            help="Percentual do CFEM a capturar. Pode ser > 100% se a taxa de conversão for alta (ex: 973% da Taxa TEC01)."
        )

    with col2:
        if st.button("🚀 Simular", type="primary", use_container_width=True, key="btn_simular"):
            st.session_state.simulacao_executada = True
            st.rerun()

    with col3:
        if st.button("🔄 Resetar", use_container_width=True, key="btn_resetar_sim"):
            st.session_state.simulacao_executada = False
            if 'percentual_simulacao' in st.session_state:
                del st.session_state.percentual_simulacao
            st.rerun()


def render_resultados_simulacao(df_filtered: pd.DataFrame) -> None:
    """
    Renderiza resultados da simulação (4 cards)

    Args:
        df_filtered: DataFrame filtrado
    """
    st.subheader("💰 Resultados da Simulação")

    # Cálculos
    percentual = st.session_state.get('percentual_simulacao', 30.0) / 100
    cfem_base = df_filtered['totalvalorrecolhido'].sum() if 'totalvalorrecolhido' in df_filtered.columns else 0
    valor_anual_simulado = cfem_base * percentual
    valor_mensal_simulado = valor_anual_simulado / 12

    # Ticket Médio do Potencial Anual Simulado (TOP 50 por Score)
    df_nao_mapeadas = df_filtered[df_filtered['status_mapeamento'] == 'Não'].copy() if 'status_mapeamento' in df_filtered.columns else df_filtered.copy()

    if len(df_nao_mapeadas) > 0:
        # Calcular score de prioridade (CFEM × Peso TEC)
        if 'tec' in df_nao_mapeadas.columns:
            df_nao_mapeadas['tec_weight'] = df_nao_mapeadas['tec'].apply(calculate_tec_weight)
        else:
            df_nao_mapeadas['tec_weight'] = 1

        if 'totalvalorrecolhido' in df_nao_mapeadas.columns:
            df_nao_mapeadas['score_prioridade'] = df_nao_mapeadas['totalvalorrecolhido'] * df_nao_mapeadas['tec_weight']
        else:
            df_nao_mapeadas['score_prioridade'] = 0

        # Pegar TOP 50 (ou todas se < 50)
        num_top = min(50, len(df_nao_mapeadas))
        df_top_prioridade = df_nao_mapeadas.nlargest(num_top, 'score_prioridade')

        # Calcular potencial das TOP minas prioritárias
        if 'totalvalorrecolhido' in df_top_prioridade.columns:
            cfem_top = df_top_prioridade['totalvalorrecolhido'].sum()
            potencial_top = cfem_top * percentual
            ticket_medio_potencial = potencial_top / num_top
        else:
            ticket_medio_potencial = 0
            num_top = 0
    else:
        ticket_medio_potencial = 0
        num_top = 0

    # Container destacado
    st.markdown("""
    <div style="background-color: #F8F9FA; border-radius: 8px; padding: 20px; margin-bottom: 1rem;">
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    # Card 1: Potencial Valor Anual
    with col1:
        st.metric(
            "💰 Potencial Valor Anual",
            format_currency_abbreviated(valor_anual_simulado),
            help="Potencial total de valor anual baseado no percentual de captura simulado"
        )
        st.markdown('<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Valor total anual projetado</p>', unsafe_allow_html=True)

    # Card 2: Potencial Valor Mensal
    with col2:
        st.metric(
            "💵 Potencial Valor Mensal",
            format_currency_abbreviated(valor_mensal_simulado)
        )
        st.markdown('<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Média mensal (÷12 meses)</p>', unsafe_allow_html=True)

    # Card 3: Base de Minas
    with col3:
        st.metric(
            "🎯 Base de Minas",
            f"{len(df_filtered):,}".replace(',', '.')
        )
        st.markdown('<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Minas disponíveis para mapeamento</p>', unsafe_allow_html=True)

    # Card 4: Ticket Médio Potencial
    with col4:
        st.metric(
            "💰 Ticket Médio Potencial",
            format_currency_abbreviated(ticket_medio_potencial),
            help=f"Valor anual médio estimado por mina nas TOP {num_top} minas prioritárias (ordenadas por Score = CFEM × Peso TEC)"
        )
        st.markdown(f'<p style="margin: 0; color: #2D3142; font-size: 0.95rem;">Potencial médio nas TOP {num_top} minas prioritárias</p>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_tabela_simulacao(df_filtered: pd.DataFrame) -> None:
    """
    Renderiza tabela TOP 50 minas prioritárias não mapeadas

    Args:
        df_filtered: DataFrame filtrado
    """
    from datetime import datetime

    st.subheader("📋 TOP 50 Minas Prioritárias - Potencial Simulado")

    # Filtra apenas NÃO MAPEADAS
    if 'status_mapeamento' in df_filtered.columns:
        df_nao_mapeadas = df_filtered[df_filtered['status_mapeamento'] == 'Não'].copy()
    else:
        df_nao_mapeadas = df_filtered.copy()

    if len(df_nao_mapeadas) == 0:
        st.info("✅ Todas as minas da base filtrada estão mapeadas!")
        return

    # Calcula score de prioridade
    if 'tec' in df_nao_mapeadas.columns:
        df_nao_mapeadas['tec_weight'] = df_nao_mapeadas['tec'].apply(calculate_tec_weight)
    else:
        df_nao_mapeadas['tec_weight'] = 0

    if 'totalvalorrecolhido' in df_nao_mapeadas.columns:
        df_nao_mapeadas['score_prioridade'] = df_nao_mapeadas['totalvalorrecolhido'] * df_nao_mapeadas['tec_weight']
    else:
        df_nao_mapeadas['score_prioridade'] = 0

    # Ordena e pega TOP 50
    df_top50 = df_nao_mapeadas.nlargest(50, 'score_prioridade').copy()

    # Calcula potencial
    percentual = st.session_state.get('percentual_simulacao', 30.0) / 100
    if 'totalvalorrecolhido' in df_top50.columns:
        df_top50['potencial_anual'] = df_top50['totalvalorrecolhido'] * percentual
        df_top50['potencial_mensal'] = df_top50['potencial_anual'] / 12
    else:
        df_top50['potencial_anual'] = 0
        df_top50['potencial_mensal'] = 0

    # Subtotal no topo
    potencial_total = df_top50['potencial_anual'].sum()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📊 Total de Minas", f"{len(df_top50)} minas")
    with col2:
        st.metric("💰 Potencial Total", format_currency_abbreviated(potencial_total))

    st.markdown("---")

    # Prepara tabela (10 colunas)
    tabela_data = []
    for idx, row in enumerate(df_top50.itertuples(), 1):
        # Identifica nome da mina
        if hasattr(row, 'chaveprimaria'):
            nome_mina = str(row.chaveprimaria)[:40]
        elif hasattr(row, 'empresa_por_cnpj'):
            nome_mina = str(row.empresa_por_cnpj)[:40]
        else:
            nome_mina = 'N/A'

        tabela_data.append({
            '#': idx,
            'Mina': nome_mina,
            'Grupo': str(getattr(row, 'pai', 'N/A'))[:25],
            'UF': getattr(row, 'uf', 'N/A'),
            'Município': str(getattr(row, 'município', 'N/A'))[:25],
            'Substância': str(getattr(row, 'substanciamaiscomercializada', 'N/A'))[:20],
            'CFEM 2024': format_currency_abbreviated(getattr(row, 'totalvalorrecolhido', 0)),
            'TEC': getattr(row, 'tec', 'N/A'),
            'Score': f"{getattr(row, 'score_prioridade', 0):,.0f}".replace(',', '.'),
            'Pot. Mensal': format_currency_abbreviated(getattr(row, 'potencial_mensal', 0)),
            'Pot. Anual': format_currency_abbreviated(getattr(row, 'potencial_anual', 0))
        })

    df_tabela = pd.DataFrame(tabela_data)

    # Exibe tabela
    st.dataframe(df_tabela, use_container_width=True, height=500)

    # Botão de exportação
    csv_data = df_top50.to_csv(sep=';', index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Exportar Simulação (CSV)",
        data=csv_data,
        file_name=f"simulacao_potencial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=False
    )

    # Caption explicativa
    percentual_display = st.session_state.get('percentual_simulacao', 30.0)
    st.caption(f"""
    💡 **Score de Prioridade** = CFEM × Peso TEC (TEC01=5, TEC02=4, TEC03=3, TEC04=2, TEC05=1)
    📊 **Potencial calculado** aplicando {percentual_display:.0f}% sobre o CFEM individual de cada mina
    """)


def render_simulacao_section(df: pd.DataFrame) -> None:
    """
    Renderiza página completa de Simulação de Potencial

    Args:
        df: DataFrame completo
    """
    st.title("📊 Simulação de Potencial")
    st.markdown("Projete cenários de captura de mercado e estime o potencial de receita")
    st.markdown("---")

    # Aplica filtros da sidebar
    filters = create_simulacao_filters(df)
    df_filtered = apply_simulacao_filters(df, filters)

    # Validação
    if len(df_filtered) == 0:
        st.warning("⚠️ Nenhuma mina corresponde aos filtros selecionados.")
        st.info("💡 Ajuste os filtros na barra lateral ou clique em 'Resetar'")
        return

    # Mostra contador de registros filtrados
    st.markdown(f"""
    <div style="background-color: #FFF3E0; border-left: 4px solid #FF6B35; padding: 12px; border-radius: 4px; margin-bottom: 1rem;">
        <p style="margin: 0; color: #2D3142; font-size: 0.95em;">
            🔍 Base de simulação: <strong>{len(df_filtered):,}</strong> minas (de {len(df):,} totais)
        </p>
    </div>
    """.replace(',', '.'), unsafe_allow_html=True)

    # Seção 1: Cards de Referência
    render_cards_referencia_simulacao(df, df_filtered)

    st.markdown("---")

    # Seção 2: Configuração da Simulação
    render_configuracao_simulacao()

    # Seção 3 e 4: Resultados (apenas se simulação executada)
    if st.session_state.get('simulacao_executada', False):
        st.markdown("---")
        render_resultados_simulacao(df_filtered)
        st.markdown("---")
        render_tabela_simulacao(df_filtered)
