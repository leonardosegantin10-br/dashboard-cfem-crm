"""
Dashboard CFEM-CRM
Sistema de análise de dados de mineração integrado com CRM comercial

Autor: Dashboard Analytics Team
Data: 2024
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path))

from src.data_processing import (
    load_and_validate_csv,
    clean_and_transform_data,
    calculate_derived_fields,
    get_data_summary
)
from src.visualizations import (
    render_kpi_section,
    build_filter_sidebar,
    apply_filters,
    format_display_table,
    render_analise_estrategica_section,
    render_simulacao_section
)


# =====================================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================================

st.set_page_config(
    page_title="Dashboard CFEM-CRM",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# CSS CUSTOMIZADO PARA LAYOUT COMPACTO
# =====================================================================

st.markdown("""
<style>
    /* Reduz padding geral dos containers */
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* Reduz espaçamento entre elementos */
    .element-container {
        margin-bottom: 0.3rem !important;
    }

    /* Compacta headers e subheaders */
    h1 {
        padding-top: 0rem !important;
        padding-bottom: 0.5rem !important;
        margin-top: 0rem !important;
    }

    h2 {
        padding-top: 0.5rem !important;
        padding-bottom: 0.3rem !important;
        margin-top: 0.5rem !important;
    }

    h3 {
        padding-top: 0.3rem !important;
        padding-bottom: 0.2rem !important;
        margin-top: 0.3rem !important;
    }

    /* Compacta metrics (KPI cards) */
    [data-testid="stMetricValue"] {
        padding-top: 0rem !important;
    }

    [data-testid="metric-container"] {
        padding: 0.3rem 0rem !important;
    }

    /* Reduz gap entre colunas */
    [data-testid="column"] {
        padding: 0rem 0.3rem !important;
    }

    /* Compacta markdown e texto */
    .stMarkdown {
        margin-bottom: 0.3rem !important;
    }

    /* Reduz espaçamento de separadores horizontais */
    hr {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Compacta expanders */
    .streamlit-expanderHeader {
        padding: 0.3rem 0.5rem !important;
    }

    /* Compacta dataframes */
    [data-testid="stDataFrame"] {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* ===== PALETA DE CORES CORPORATIVA (LARANJA/CINZA) ===== */

    /* Botões Primários - Laranja */
    .stButton > button[kind="primary"],
    button[data-testid="baseButton-primary"] {
        background-color: #FF6B35 !important;
        border-color: #FF6B35 !important;
        color: white !important;
    }

    .stButton > button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background-color: #E5602F !important;
        border-color: #E5602F !important;
    }

    /* Botões Secundários - Cinza */
    .stButton > button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {
        background-color: #95A3B3 !important;
        border-color: #95A3B3 !important;
        color: white !important;
    }

    .stButton > button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #7A8999 !important;
        border-color: #7A8999 !important;
    }

    /* Estilização de Tabelas */
    [data-testid="stDataFrame"] thead tr th {
        background-color: #F0F1F3 !important;
        color: #2D3142 !important;
        font-weight: 600 !important;
    }

    [data-testid="stDataFrame"] tbody tr:hover {
        background-color: #F8F9FA !important;
    }

    /* Bordas de cards e containers */
    [data-testid="stMetricValue"] {
        color: #2D3142 !important;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# INICIALIZAÇÃO DO SESSION STATE
# =====================================================================

if 'data' not in st.session_state:
    st.session_state.data = None

if 'filters' not in st.session_state:
    st.session_state.filters = {}

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'upload'


# =====================================================================
# SIDEBAR - INFORMAÇÕES DO SISTEMA
# =====================================================================

st.sidebar.title("⛏️ Dashboard CFEM-CRM")
st.sidebar.markdown("### Análise do Setor de Mineração")
st.sidebar.caption("Versão 1.0 | 2024")

# Navegação entre páginas
st.sidebar.markdown("---")
st.sidebar.markdown("### 📑 Navegação")

# 3 botões empilhados verticalmente
if st.sidebar.button("📤 Upload de Dados", use_container_width=True, type="primary" if st.session_state.current_page == 'upload' else "secondary"):
    st.session_state.current_page = 'upload'
    st.rerun()

if st.sidebar.button("📊 Visão Geral", use_container_width=True, type="primary" if st.session_state.current_page == 'visao_geral' else "secondary"):
    st.session_state.current_page = 'visao_geral'
    st.rerun()

if st.sidebar.button("📈 Análise Estratégica", use_container_width=True, type="primary" if st.session_state.current_page == 'analise_estrategica' else "secondary"):
    st.session_state.current_page = 'analise_estrategica'
    st.rerun()

if st.sidebar.button("📊 Simulação", use_container_width=True, type="primary" if st.session_state.current_page == 'simulacao' else "secondary"):
    st.session_state.current_page = 'simulacao'
    st.rerun()

st.sidebar.markdown("---")

if st.session_state.data is not None:
    st.sidebar.success("✅ Dados carregados")
    summary = get_data_summary(st.session_state.data)

    st.sidebar.metric("📊 Linhas", f"{summary['row_count']:,}".replace(',', '.'))
    st.sidebar.metric("📋 Colunas", summary['column_count'])
    st.sidebar.caption(f"Última atualização: {summary['date_processed']}")
    st.sidebar.caption(f"Memória: {summary['memory_usage_mb']:.2f} MB")
else:
    st.sidebar.warning("⚠️ Nenhum dado carregado")
    st.sidebar.info("👉 Faça upload na aba 'Upload de Dados'")


# =====================================================================
# NAVEGAÇÃO ENTRE PÁGINAS
# =====================================================================

# Página de Upload
if st.session_state.current_page == 'upload':
    st.title("⛏️ Dashboard CFEM-CRM")
    st.header("📤 Upload de Arquivo CSV")

    st.markdown("""
    Selecione o arquivo CSV com dados CFEM-CRM (delimitador: ponto-e-vírgula).
    Os dados serão processados automaticamente após o upload.
    """)

    # File uploader
    uploaded_file = st.file_uploader(
        "Selecione o arquivo CSV",
        type=['csv'],
        help="Arquivo CSV com delimitador ';'"
    )

    if uploaded_file is not None:
        try:
            # Carrega e processa automaticamente
            with st.spinner("⚙️ Carregando e processando dados..."):
                # Carrega o CSV
                raw_data = load_and_validate_csv(uploaded_file, delimiter=';')

                # Processa os dados automaticamente
                processed_data = clean_and_transform_data(raw_data)
                processed_data = calculate_derived_fields(processed_data)

                # Armazena no session state
                st.session_state.data = processed_data
                st.session_state.data_loaded = True

            # Mensagem de sucesso
            st.success("✅ Dados carregados e processados com sucesso!")

            # Card com métricas essenciais
            st.subheader("📊 Resumo dos Dados")
            col1, col2 = st.columns(2)

            col1.metric("Total de Registros", f"{len(processed_data):,}".replace(',', '.'))
            col2.metric("Total de Colunas", len(processed_data.columns))

            # Botão para navegar à Visão Geral
            st.markdown("### 👉 Próximo Passo")
            st.markdown("Clique no botão abaixo para visualizar e analisar os dados.")

            if st.button("🔍 Ir para Visão Geral", type="primary", use_container_width=True):
                st.session_state.current_page = 'visao_geral'
                st.rerun()

        except Exception as e:
            st.error(f"❌ Erro ao carregar arquivo: {str(e)}")
            st.exception(e)

    else:
        # Mensagem quando nenhum arquivo foi carregado
        st.info("👆 Aguardando upload do arquivo CSV...")


# Página de Visão Geral
if st.session_state.current_page == 'visao_geral':
    if st.session_state.data is None:
        # Nenhum dado carregado
        st.warning("⚠️ Nenhum dado carregado")
        st.info("👉 Por favor, faça o upload dos dados usando o botão **'📤 Upload'** na barra lateral")

        st.markdown("""
        ### 📋 O que você verá nesta aba após o upload:

        1. **🌍 Panorama do Mercado**
           - Total de minas
           - CFEM total arrecadado
           - Ticket médio por mina

        2. **🏢 Estrutura de Mercado**
           - Total de grupos mineradores
           - TOP 5 grupos por CFEM (gráfico)

        3. **🎯 Mapeamento Comercial**
           - Minas mapeadas no CRM
           - Valor mensal e anual mapeado
           - Percentual de cobertura

        4. **📈 Efetividade**
           - Índice Valor/CFEM
           - Substâncias mapeadas

        5. **📊 Tabela Detalhada**
           - Listagem completa com 12 colunas
           - Ordenável e filtrável
           - Exportação disponível
        """)

    else:
        # Dados carregados - Mostra os filtros e análises
        df = st.session_state.data

        # ===== FILTROS NA SIDEBAR =====
        filters = build_filter_sidebar(df)
        st.session_state.filters = filters

        # ===== APLICA FILTROS =====
        filtered_df = apply_filters(df, filters)

        # Verifica se há filtros ativos
        filters_active = (
            len(filters.get('tec', [])) < df['tec'].nunique() if 'tec' in df.columns else False
        ) or (
            len(filters.get('status_mapeamento', [])) < 2
        )

        # Mostra aviso se dataset filtrado está vazio
        if len(filtered_df) == 0:
            st.error("❌ Nenhum registro encontrado com os filtros aplicados")
            st.info("💡 Ajuste os filtros na barra lateral ou clique em 'Resetar Filtros'")
        else:
            # Mostra contador de registros
            if filters_active:
                st.markdown(f"""
                <div style="background-color: #FFF3E0; border-left: 4px solid #FF6B35; padding: 12px; border-radius: 4px; margin-bottom: 1rem;">
                    <p style="margin: 0; color: #2D3142; font-size: 0.95em;">
                        🔍 Exibindo <strong>{len(filtered_df):,}</strong> de <strong>{len(df):,}</strong> registros (filtros aplicados)
                    </p>
                </div>
                """.replace(',', '.'), unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #F0F1F3; border-left: 4px solid #95A3B3; padding: 12px; border-radius: 4px; margin-bottom: 1rem;">
                    <p style="margin: 0; color: #2D3142; font-size: 0.95em;">
                        📊 Exibindo <strong>{len(filtered_df):,}</strong> registros (sem filtros)
                    </p>
                </div>
                """.replace(',', '.'), unsafe_allow_html=True)

            # ===== SEÇÃO 1: KPIs =====
            render_kpi_section(filtered_df, filters_active)

            st.markdown("---")

            # ===== SEÇÃO 2: TABELA DETALHADA =====
            st.header("📋 Detalhamento das Minas")

            # Formata a tabela
            display_df = format_display_table(filtered_df)

            # Mostra a tabela
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )

            # ===== EXPORTAÇÃO =====
            st.markdown("---")
            col1, col2, col3 = st.columns([2, 1, 1])

            with col2:
                # Botão de download CSV
                csv_data = filtered_df.to_csv(sep=';', index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Exportar CSV",
                    data=csv_data,
                    file_name="cfem_crm_export.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with col3:
                # Botão de limpar dados
                if st.button("🗑️ Limpar Dados", use_container_width=True):
                    st.session_state.data = None
                    st.session_state.data_loaded = False
                    st.session_state.filters = {}
                    st.rerun()


# Página de Análise Estratégica
if st.session_state.current_page == 'analise_estrategica':
    if st.session_state.data is None:
        # Nenhum dado carregado
        st.warning("⚠️ Nenhum dado carregado")
        st.info("👉 Por favor, faça o upload dos dados usando o botão **'📤 Upload de Dados'** na barra lateral")

        st.markdown("""
        ### 📋 O que você verá nesta aba após o upload:

        **1. 📊 Análise de Pareto - Concentração de Mercado**
           - Identificação das minas que representam 80% do CFEM
           - Gráfico interativo de Pareto (barras + linha acumulada)
           - 4 Cards KPI: Concentração, Mapeamento, Valor Capturado, Distribuição TEC

        **2. 🏢 Análise de Grupos/Holdings**
           - Concentração por grupos empresariais
           - Gráfico Pareto TOP 15 grupos
           - 3 Cards KPI: TOP Grupos, Cobertura Comercial, Oportunidades
           - Tabela TOP 10 Grupos detalhada

        **3. 🎯 GAP de Oportunidades**
           - Priorização de minas não mapeadas
           - 4 Cards: Potencial Total, Maior Oportunidade, TEC01/02, Concentração
           - Tabela TOP 20 Oportunidades com score de prioridade
        """)

    else:
        # Dados carregados - Renderiza análise estratégica
        df = st.session_state.data

        # Header da página
        st.title("📈 Análise Estratégica")
        st.markdown("**Insights para priorização comercial e mapeamento de oportunidades**")
        st.markdown("---")

        # Renderiza as 3 seções
        render_analise_estrategica_section(df)


# Página de Simulação de Potencial
if st.session_state.current_page == 'simulacao':
    if st.session_state.data is None:
        # Nenhum dado carregado
        st.warning("⚠️ Nenhum dado carregado")
        st.info("👉 Por favor, faça o upload dos dados usando o botão **'📤 Upload de Dados'** na barra lateral")

        st.markdown("""
        ### 📋 O que você verá nesta aba após o upload:

        1. **📊 Cards de Referência**
           - Visão geral da base filtrada
           - Indicadores de desempenho atual

        2. **🎯 Configuração da Simulação**
           - Defina o percentual de captura desejado
           - Simule diferentes cenários

        3. **💰 Resultados Projetados**
           - Potencial de receita anual e mensal
           - Crescimento sobre o atual

        4. **📋 TOP 50 Minas Prioritárias**
           - Ranking por score de prioridade
           - Exportação disponível
        """)
    else:
        df = st.session_state.data
        render_simulacao_section(df)


# =====================================================================
# FOOTER
# =====================================================================

st.markdown("---")
st.caption("Dashboard CFEM-CRM | Desenvolvido para análise estratégica do setor de mineração brasileiro")
st.caption("⚠️ Dados confidenciais - Uso restrito interno")
