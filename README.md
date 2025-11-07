# ⛏️ Dashboard CFEM-CRM

Sistema de análise integrada de dados **CFEM 2024** (Compensação Financeira pela Exploração Mineral) com informações de **CRM Comercial** para mapeamento estratégico do mercado de mineração brasileiro.

## 📋 Sobre o Projeto

Este dashboard foi desenvolvido para a diretoria comercial realizar análises estratégicas combinando:

- **Dados públicos de CFEM 2024**: Arrecadação por empresa, localização e substância mineral (fonte: ANM/Governo)
- **Dados de CRM (Salesforce)**: Contratos mapeados, escopos comerciais e estratégias de prospecção (TEC)

### Objetivos Principais

1. **Mapear o mercado**: Identificar potencial de arrecadação CFEM por empresa e região
2. **Avaliar efetividade comercial**: Comparar contratos mapeados vs. potencial de mercado
3. **Identificar oportunidades**: Encontrar gaps de prospecção e áreas de expansão

---

## 🔒 Requisitos de Segurança

**⚠️ IMPORTANTE**: Por questões de confidencialidade:

- Os dados ficam **APENAS em memória** (`st.session_state`)
- **NÃO há persistência** em banco de dados ou arquivos
- Ao recarregar a página, os dados são **perdidos**
- Recomenda-se uso em ambiente controlado com acesso restrito

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Instalação

1. **Clone ou baixe o projeto**:
   ```bash
   cd dashboard-cfem-crm
   ```

2. **Crie um ambiente virtual (recomendado)**:
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual**:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **Linux/Mac**:
     ```bash
     source venv/bin/activate
     ```

4. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

### Execução

Para iniciar o dashboard:

```bash
streamlit run src/app.py
```

O dashboard abrirá automaticamente no navegador em `http://localhost:8501`

---

## 📂 Estrutura do Projeto

```
dashboard-cfem-crm/
├── src/
│   ├── app.py                 # Aplicação principal Streamlit
│   ├── data_processing.py     # Funções de limpeza e transformação de dados
│   └── visualizations.py      # Funções para KPIs e visualizações
├── requirements.txt           # Dependências do projeto
└── README.md                  # Este arquivo
```

### Descrição dos Módulos

- **`app.py`**: Ponto de entrada da aplicação. Gerencia interface, tabs, upload de dados e session state.
- **`data_processing.py`**: Processamento de dados CSV (conversões, limpeza, cálculos derivados).
- **`visualizations.py`**: Renderização de KPIs, filtros e formatação de tabelas.

---

## 📊 Funcionalidades

### Guia 1: Upload de Dados

- Upload de arquivo CSV com delimitador ponto-e-vírgula (`;`)
- Preview dos dados (primeiras 10 linhas)
- Validação e estatísticas do arquivo
- Processamento automático com feedback de progresso

### Guia 2: Visão Geral

#### 🌍 Panorama do Mercado
- **Total de Minas**: Quantidade de minas cadastradas
- **CFEM Total 2024**: Arrecadação total (em bilhões)
- **Ticket Médio CFEM**: Arrecadação média por mina (em milhões)

#### 🏢 Estrutura de Mercado
- **Total de Grupos**: Quantidade de holdings/grupos mineradores
- **TOP 5 Grupos**: Gráfico de barras com maiores arrecadadores CFEM

#### 🎯 Mapeamento Comercial
- **Minas Mapeadas**: Quantidade e percentual de minas com contratos
- **Valor Mensal Mapeado**: Receita mensal dos contratos
- **Valor Anual Mapeado**: Receita anual projetada (destaque principal)

#### 📈 Efetividade
- **Índice Valor/CFEM**: Relação entre valor contratual e CFEM das minas mapeadas
- **Substâncias Mapeadas**: Diversidade de minerais nos contratos

#### 📋 Tabela Detalhada
Listagem completa com 12 colunas principais:
- Grupo/Holding
- Empresa
- Município e UF
- Substância Mineral
- CFEM 2024 (R$)
- Volume comercializado (toneladas)
- TEC (Estratégia comercial)
- Status de Mapeamento
- Valor Anual Mapeado (R$)
- Código do Escopo
- Terceirização de Lavra

**Recursos**:
- Ordenação por qualquer coluna
- Formatação monetária brasileira
- Exportação em CSV

#### 🔍 Filtros Interativos (Sidebar)
- **TEC**: Estratégia comercial (TEC01 a TEC04+)
- **Status Mapeamento**: Todos / Mapeados / Não Mapeados
- **Substância Mineral**: Multi-seleção
- **Estado (UF)**: Multi-seleção
- **Grupo/Holding**: Multi-seleção (excluindo "NA" e "FORA")
- **Faixa CFEM**: Slider com valor mínimo e máximo
- **Terceiriza Lavra**: SIM / NÃO

Todos os KPIs e tabelas reagem aos filtros em tempo real.

---

## 📝 Formato dos Dados CSV

### Requisitos do Arquivo

- **Delimitador**: Ponto-e-vírgula (`;`)
- **Encoding**: UTF-8 com ou sem BOM (ou latin-1 como fallback)
- **Formato de decimais**: Brasileiro (vírgula como separador decimal: `1.234,56`)

### Campos Principais

| Campo | Descrição | Formato/Observações |
|-------|-----------|---------------------|
| `ChavePrimaria` | Identificador único da mina | CNPJ + Município |
| `CPF_CNPJ` | CNPJ da empresa | Notação científica (ex: `3,36E+13`) - será convertido |
| `EMPRESA_POR_CNPJ` | Razão social | Texto |
| `Município` | Município da mina | Texto |
| `UF` | Estado | Sigla (ex: MG, PA) |
| `TotalValorRecolhido` | CFEM arrecadado em 2024 | Decimal brasileiro (ex: `1.234,56`) |
| `TotalQuantidadeComercializada` | Volume em toneladas | Decimal brasileiro |
| `SubstanciaMaisComercializada` | Mineral principal | Texto (FERRO, OURO, COBRE, etc) |
| `SetorMineral` | Categoria do mineral | "Minerais Infraestrutura" ou "Minerais Estratégicos" |
| `PAI` | Grupo/Holding controlador | Texto (VALE, CSN, ANGLO AMERICAN, etc) |
| `TEC` | Estratégia comercial | TEC01, TEC02, TEC03, TEC04+ |
| `primeiro_escopo` | Código do contrato | Ex: ECP-14296 ou "NÃO" (não mapeado) |
| `Duração` | Duração do contrato (meses) | Inteiro |
| `valor` | Valor do escopo | Decimal brasileiro |
| `Valor Total Mensal` | Valor mensal do contrato | Decimal brasileiro |
| `Terceiriza Lavra?` | Terceiriza lavra? | "SIM" ou "NÃO" |

### Campos Ignorados (serão removidos)

- `CHECK2`, `CHECK3`, `CHECK4`, `CHECK5`
- `Empresa_CPF_CNPJ` (duplicado)
- `CFEM (Porte)` (duplicado de TotalValorRecolhido)

### Tratamentos Aplicados Automaticamente

1. **CPF_CNPJ**: Notação científica → String de 14 dígitos com zeros à esquerda
2. **Decimais brasileiros**: `1.234,56` → `1234.56` (float)
3. **Valores ausentes**: `#N/D` → `NaN`
4. **Campos calculados**:
   - `Valor Anual Mapeado = Valor Total Mensal × 12`
   - `Status Mapeamento = "Sim"` se `primeiro_escopo ≠ "NÃO"`, senão `"Não"`

---

## 🛠️ Tecnologias Utilizadas

- **[Streamlit](https://streamlit.io/)**: Framework web para Python
- **[Pandas](https://pandas.pydata.org/)**: Manipulação e análise de dados
- **[Plotly](https://plotly.com/)**: Visualizações interativas
- **[NumPy](https://numpy.org/)**: Computação numérica
- **[OpenPyXL](https://openpyxl.readthedocs.io/)**: Suporte a arquivos Excel (exportação futura)

---

## 📖 Glossário

- **CFEM**: Compensação Financeira pela Exploração Mineral - tributo sobre a exploração de recursos minerais no Brasil
- **ANM**: Agência Nacional de Mineração
- **TEC**: Estratégia comercial de prospecção
  - `TEC01`: Cliente atual (alta prioridade)
  - `TEC02`: Foco alto (prospecção ativa)
  - `TEC03`: Foco médio (acompanhamento)
  - `TEC04+`: Sem foco comercial
- **PAI**: Grupo controlador ou holding da empresa mineradora
- **Escopo**: Contrato ou projeto comercial cadastrado no CRM

---

## ⚠️ Limitações Conhecidas

1. **Sem persistência**: Dados são perdidos ao recarregar a página
2. **Processamento em memória**: Pode ter limitações com arquivos muito grandes (>500MB)
3. **Sem autenticação**: Não há controle de acesso embutido (use proteção externa se necessário)

---

## 🔮 Melhorias Futuras

- [ ] Exportação para Excel (XLSX) com formatação
- [ ] Gráficos adicionais (mapas geográficos, série temporal)
- [ ] Comparativo entre períodos (CFEM 2023 vs 2024)
- [ ] Dashboard de prospecção (leads por TEC)
- [ ] Análise de correlação (CFEM vs. Valor Contratual)
- [ ] Relatórios automatizados em PDF

---

## 📞 Suporte

Para dúvidas ou sugestões sobre o dashboard, entre em contato com a equipe de Analytics.

---

## 📄 Licença

Este projeto é de uso interno e confidencial. Distribuição não autorizada é proibida.

---

**Desenvolvido com ❤️ para o setor de mineração brasileiro**
