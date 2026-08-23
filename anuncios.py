import streamlit as st
import pandas as pd
import re
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
URL_LOGO = "https://raw.githubusercontent.com/Adatech-hub/calculadora-mkt/main/Logo.png"

st.set_page_config(
    page_title="Sistema ADATECH",
    page_icon=URL_LOGO,
    layout="wide"
)

# 2. CSS PARA ESTILIZAÇÃO - PALETA ADATECH
st.markdown("""
    <style>
    /* Fundo da aplicação e da barra superior */
    .stApp { background-color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #FFFFFF !important; }
    
    /* Menu Lateral - Fundo cinza suave e borda Sky Blue */
    [data-testid="stSidebar"] { 
        background-color: #F4F6F9 !important; 
        border-right: 2px solid #74D1EA !important; 
    }
    
    /* Títulos principais na cor DEEP VIOLET da Adatech */
    h1, h2, h3 { color: #250E62 !important; }
    p, span, label { color: #1E1E1E !important; }
    
    /* Campos de Entrada (Inputs e Text Area) */
    div[data-testid="stTextInput"] input, 
    div[data-testid="stNumberInput"] input, 
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #F8F9FA !important;
        color: #250E62 !important; 
        border: 1px solid #D1D5DB !important;
    }
    
    /* Comportamento ao focar no campo - Brilho na cor VIVID CERISE da Adatech */
    div[data-testid="stTextInput"] input:focus, 
    div[data-testid="stNumberInput"] input:focus, 
    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus {
        border-color: #DA1984 !important; 
        box-shadow: 0 0 0 0.2rem rgba(218, 25, 132, 0.25) !important;
    }
    
    /* Botões de +/- do Number Input (Cinza Escuro) */
    [data-testid="stNumberInputStepDown"],
    [data-testid="stNumberInputStepUp"] {
        background-color: #5A5A5A !important;
        color: #FFFFFF !important;
    }
    [data-testid="stNumberInputStepDown"] svg,
    [data-testid="stNumberInputStepUp"] svg {
        fill: #FFFFFF !important;
    }
    [data-testid="stNumberInputStepDown"]:hover,
    [data-testid="stNumberInputStepUp"]:hover {
        background-color: #333333 !important;
    }
    
    /* Campos Desabilitados - Cor Sky Blue ADATECH (#74D1EA) */
    [data-baseweb="input"]:has(input[disabled]),
    [data-baseweb="base-input"]:has(input[disabled]),
    div[data-testid="stTextInput"] input[disabled], 
    div[data-testid="stNumberInput"] input[disabled],
    div[data-testid="stTextArea"] textarea[disabled] {
        background-color: #74D1EA !important; 
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important; 
        font-weight: bold !important;
        border: 1px solid #74D1EA !important;
    }
    
    /* Botões Padrão e Botões de Formulário */
    div.stButton > button,
    [data-testid="stFormSubmitButton"] > button {
        color: #250E62 !important; 
        background-color: rgba(116, 209, 234, 0.6) !important; 
        border: 1px solid #74D1EA !important; 
        border-radius: 5px; 
        width: 100%; 
        font-weight: bold;
    }
    
    /* Botões Hover - Fundo SKY BLUE 100% de intensidade */
    div.stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover { 
        background-color: #74D1EA !important; 
        color: #250E62 !important; 
        border: 1px solid #250E62 !important; 
    }
    
    /* Métricas e Tabelas */
    [data-testid="stMetricValue"] { color: #250E62 !important; }
    .stTable { background-color: #F8F9FA; color: #1E1E1E; }
    
    /* ========================================================= */
    /* Estilização da Lista Suspensa (Dropdown) Selectbox        */
    /* ========================================================= */
    [data-baseweb="popover"] div[data-baseweb="menu"],
    ul[role="listbox"] {
        background-color: #74D1EA !important; 
    }
    
    ul[role="listbox"] li {
        color: #250E62 !important; 
        font-weight: bold !important;
        background-color: transparent !important;
    }
    
    ul[role="listbox"] li:hover,
    ul[role="listbox"] li[aria-selected="true"],
    ul[role="listbox"] li[aria-highlighted="true"] {
        background-color: rgba(37, 14, 98, 0.15) !important; 
        color: #250E62 !important;
    }
    
    /* ========================================================= */
    /* Ajustes visuais para Componentes do ChatBot (Sem Preto)   */
    /* ========================================================= */
    [data-testid="stExpander"] {
        background-color: #F8F9FA !important;
        border: 1px solid #74D1EA !important;
        border-radius: 8px !important;
    }
    [data-testid="stExpander"] summary {
        background-color: rgba(116, 209, 234, 0.2) !important;
        border-radius: 8px !important;
    }
    [data-testid="stExpander"] summary:hover {
        background-color: rgba(116, 209, 234, 0.4) !important;
    }
    [data-testid="stExpander"] summary p {
        color: #250E62 !important;
        font-weight: bold !important;
    }
    
    /* Blocos de Código (Onde ficam as frases prontas) */
    div[data-testid="stCodeBlock"] > div, 
    div[data-testid="stCodeBlock"] pre {
        background-color: #F8F9FA !important;
        border-radius: 5px !important;
    }
    div[data-testid="stCodeBlock"] {
        border: 1px solid #D1D5DB !important;
        border-radius: 5px !important;
    }
    div[data-testid="stCodeBlock"] code {
        color: #1E1E1E !important;
        text-shadow: none !important;
        font-family: Arial, sans-serif !important;
        font-size: 15px !important;
        white-space: pre-wrap !important;
    }
    
    /* Forçar o botão de COPIAR a ficar SEMPRE VISÍVEL e nas cores da ADATECH */
    div[data-testid="stCodeBlock"] button {
        opacity: 1 !important; 
        visibility: visible !important;
        transform: none !important;
        background-color: #74D1EA !important;
        border: 1px solid #250E62 !important;
        border-radius: 4px !important;
        right: 10px !important;
        top: 10px !important;
    }
    div[data-testid="stCodeBlock"] button:hover {
        background-color: #250E62 !important;
    }
    div[data-testid="stCodeBlock"] button svg {
        stroke: #250E62 !important; 
        fill: transparent !important;
    }
    div[data-testid="stCodeBlock"] button:hover svg {
        stroke: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. MENU LATERAL
st.sidebar.image(URL_LOGO, width=150)
st.sidebar.title("Navegação")
menu_selecionado = st.sidebar.radio("Selecione a ferramenta:", [
    "Cadastro de Anúncios", 
    "Cadastro de Produto", 
    "Cadastro de Fornecedor", 
    "Despesas a pagar", 
    "Curva ABC Meli",
    "Product ADS",
    "Pós Venda",
    "Calculadora Simples",
    "ChatBot",
    "Fulfillment"
])
st.sidebar.markdown("---")

# =====================================================================
# FUNÇÕES DE SUPORTE E CONVERSÃO
# =====================================================================
@st.cache_resource(ttl=3600)
def get_sheets_client():
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    credenciais_dict = json.loads(st.secrets["google_credentials"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credenciais_dict, scope)
    return gspread.authorize(creds)

def converter_valor(valor):
    if pd.isna(valor) or valor == "": return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    v_str = str(valor).strip().replace('.', '').replace(',', '.')
    return float(re.sub(r'[^\d\.\-]', '', v_str) or 0)

def formatar_moeda_ui(valor):
    numero = converter_valor(valor)
    return f"{numero:.2f}".replace('.', ',')

def arredondar_customizado(valor):
    try: return float(Decimal(str(valor)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    except: return 0.0

def converter_data_sheets(valor):
    if pd.isna(valor) or str(valor).strip().lower() in ["nan", ""]: return ""
    try:
        if isinstance(valor, (int, float)) or str(valor).isdigit():
            return pd.to_datetime(float(valor), unit='D', origin='1899-12-30').strftime("%d/%m/%Y")
        return str(valor).strip()
    except: return str(valor).strip()

def formatar_data_hora(valor):
    if pd.isna(valor) or str(valor).strip().lower() in ["nan", ""]: return ""
    try:
        if isinstance(valor, (int, float)) or str(valor).isdigit():
            dt = pd.to_datetime(float(valor), unit='D', origin='1899-12-30')
            return dt.strftime("%d/%m/%Y")
        if " " in str(valor):
            return str(valor).split(" ")[0].strip()
        return str(valor).strip()
    except: return str(valor).strip()

def normalizar_nf(nf):
    n = re.sub(r'[^a-zA-Z0-9]', '', str(nf)).upper()
    return n.lstrip('0') if n.lstrip('0') else n

def corrigir_parcela_data(valor):
    if pd.isna(valor) or valor == "": return ""
    try:
        v_float = float(valor)
        if v_float > 40000:
            data = pd.to_datetime(v_float, unit='D', origin='1899-12-30')
            return f"{data.day} de {data.month}"
    except:
        pass
    v_str = str(valor).strip()
    if re.match(r'^\d{1,2}/\d{1,2}$', v_str):
        return v_str.replace("/", " de ")
    return v_str

def avaliar_expressao_matematica(texto):
    texto_limpo = str(texto).strip().replace('=', '').replace(',', '.')
    expr = re.sub(r'[^\d\.\+\-\*\/\(\)\%]', '', texto_limpo)
    try:
        while '%' in expr:
            match = re.search(r'([\d\.]+)([\+\-])([\d\.]+)%', expr)
            if match:
                base, operador, percentual = match.group(1), match.group(2), match.group(3)
                subst = f"({base}*(1+{percentual}/100))" if operador == '+' else f"({base}*(1-{percentual}/100))"
                expr = expr[:match.start()] + subst + expr[match.end():]
            else:
                match_mult = re.search(r'([\d\.]+)%', expr)
                if match_mult:
                    val = match_mult.group(1)
                    expr = expr[:match_mult.start()] + f"({val}/100)" + expr[match.end():]
                else:
                    expr = expr.replace('%', '')
        if expr: return float(eval(expr))
        return 0.0
    except: return None

# =====================================================================
# CACHE DE DADOS
# =====================================================================
@st.cache_data(ttl=15)
def cached_produtos_data():
    try:
        client = get_sheets_client()
        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
        try: sheet = doc.worksheet("Produtos")
        except:
            sheet = doc.add_worksheet(title="Produtos", rows="1000", cols="13")
            sheet.append_row(["SKU", "Produto", "Custo", "Fornecedor", "Data de Referência", "EAN", "NCM", "CST", "Medida", "Peso", "Campo Semântico", "Características/Descrição", "Historico_Precos"], value_input_option="USER_ENTERED")
        data = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
        if data: return pd.DataFrame(data)
    except: pass
    return None

@st.cache_data(ttl=15)
def cached_kits_composicao():
    try:
        client = get_sheets_client()
        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
        try: sheet = doc.worksheet("Kits_Composicao")
        except: return None
        data = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
        if data: return pd.DataFrame(data)
    except: pass
    return None

@st.cache_data(ttl=15)
def cached_campanhas_ads():
    try:
        client = get_sheets_client()
        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
        try: sheet = doc.worksheet("Campanhas_ADS")
        except: return None
        data = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
        if data: return pd.DataFrame(data)
    except: pass
    return None

@st.cache_data(ttl=15)
def cached_analises_ads():
    try:
        client = get_sheets_client()
        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
        try: sheet = doc.worksheet("Analises_ADS")
        except: return None
        data = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
        if data: return pd.DataFrame(data)
    except: pass
    return None

@st.cache_data(ttl=15)
def cached_ocorrencias():
    try:
        client = get_sheets_client()
        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
        try: sheet = doc.worksheet("Pos_Venda")
        except: return None
        data = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
        if data: return pd.DataFrame(data)
    except: pass
    return None

@st.cache_data(ttl=15)
def cached_chatbot_frases():
    try:
        client = get_sheets_client()
        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
        try: sheet = doc.worksheet("ChatBot")
        except: return None
        data = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
        if data: return pd.DataFrame(data)
    except: pass
    return None

@st.cache_data(ttl=60)
def get_lista_fornecedores():
    try:
        client = get_sheets_client()
        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
        try: sheet = doc.worksheet("Fornecedores")
        except: return [] 
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            if not df.empty and "Nome do Fornecedor" in df.columns:
                lista = df["Nome do Fornecedor"].dropna().astype(str).str.strip()
                return sorted(lista[lista != ""].unique().tolist())
    except: pass
    return []

@st.cache_data(ttl=60)
def get_lista_anuncios():
    try:
        client = get_sheets_client()
        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
        sheet = doc.sheet1
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            if not df.empty and "ID do Anúncio" in df.columns and "Título" in df.columns:
                lista = []
                for _, row in df.iterrows():
                    id_an = str(row.get("ID do Anúncio", "")).strip()
                    tit = str(row.get("Título", "")).strip()
                    if id_an and tit:
                        lista.append(f"{id_an} - {tit}")
                return sorted(list(set(lista)))
    except: pass
    return []

def buscar_produto_por_sku(sku_busca):
    if not sku_busca: return None
    df_p = cached_produtos_data()
    if df_p is not None and not df_p.empty and "SKU" in df_p.columns:
        df_p["SKU"] = df_p["SKU"].astype(str).str.strip()
        sku_limpo = str(sku_busca).strip()
        res = df_p[df_p["SKU"] == sku_limpo]
        
        if not res.empty:
            info_prod = res.iloc[0].to_dict()
            
            # Recálculo de Kits em Tempo Real
            df_kits = cached_kits_composicao()
            if df_kits is not None and not df_kits.empty and "SKU do Kit" in df_kits.columns:
                df_kits["SKU do Kit"] = df_kits["SKU do Kit"].astype(str).str.strip()
                componentes = df_kits[df_kits["SKU do Kit"] == sku_limpo]
                
                if not componentes.empty:
                    custo_recalculado = 0.0
                    for _, row_comp in componentes.iterrows():
                        sku_c = str(row_comp.get("SKU Componente", "")).strip()
                        qtd_c = converter_valor(row_comp.get("Qtd", 1))
                        
                        comp_res = df_p[df_p["SKU"] == sku_c]
                        if not comp_res.empty:
                            custo_unit_atual = converter_valor(comp_res.iloc[0].get("Custo", 0))
                            custo_recalculado += custo_unit_atual * qtd_c
                            
                    if custo_recalculado > 0:
                        info_prod["Custo"] = custo_recalculado
                        
            return info_prod
    return None
# =====================================================================
# MÓDULO: CADASTRO DE FORNECEDOR
# =====================================================================
if menu_selecionado == "Cadastro de Fornecedor":
    
    if "forn_original" not in st.session_state: st.session_state.forn_original = ""
    if "forn_nome" not in st.session_state: st.session_state.forn_nome = ""
    if "forn_cnpj" not in st.session_state: st.session_state.forn_cnpj = ""
    if "forn_razao" not in st.session_state: st.session_state.forn_razao = ""
    if "forn_end" not in st.session_state: st.session_state.forn_end = ""
    if "forn_vend" not in st.session_state: st.session_state.forn_vend = ""
    if "forn_tel" not in st.session_state: st.session_state.forn_tel = ""
    
    def puxar_dados_fornecedor():
        pesquisa = st.session_state.get("forn_pesquisa", "")
        if pesquisa:
            try:
                client = get_sheets_client()
                doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                sheet = doc.worksheet("Fornecedores")
                df = pd.DataFrame(sheet.get_all_records())
                if not df.empty and "Nome do Fornecedor" in df.columns:
                    df["Nome_Match"] = df["Nome do Fornecedor"].astype(str).str.strip()
                    res = df[df["Nome_Match"] == pesquisa.strip()]
                    if not res.empty:
                        row = res.iloc[0]
                        st.session_state.forn_original = str(row.get("Nome do Fornecedor", ""))
                        st.session_state.forn_nome = str(row.get("Nome do Fornecedor", ""))
                        st.session_state.forn_cnpj = str(row.get("CNPJ", ""))
                        st.session_state.forn_razao = str(row.get("Razão Social", "")) if "Razão Social" in row else ""
                        st.session_state.forn_end = str(row.get("Endereço", ""))
                        st.session_state.forn_vend = str(row.get("Vendedor", ""))
                        # O replace tira o apóstrofo da visualização na sua tela
                        st.session_state.forn_tel = str(row.get("Telefone", "")).replace("'", "")
            except: pass
        else:
            st.session_state.forn_original = ""
            st.session_state.forn_nome = ""
            st.session_state.forn_cnpj = ""
            st.session_state.forn_razao = ""
            st.session_state.forn_end = ""
            st.session_state.forn_vend = ""
            st.session_state.forn_tel = ""

    def limpar_fornecedor():
        for k in ["forn_nome", "forn_cnpj", "forn_razao", "forn_end", "forn_vend", "forn_tel", "forn_original", "forn_pesquisa"]:
            if k in st.session_state:
                del st.session_state[k]

    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.2, 4, 0.2])
    with col_conteudo:
        st.title("🏭 Cadastro de Fornecedor")
        st.markdown("Registre novos fornecedores ou edite os existentes para utilizá-los no Cadastro de Produtos e Despesas.")
        
        st.subheader("🔍 Pesquisar Fornecedor")
        lista_pesquisa_forn = [""] + get_lista_fornecedores()
        
        c_pesq, c_limp = st.columns([4, 1])
        with c_pesq:
            st.selectbox("Selecione um fornecedor para editar os dados:", options=lista_pesquisa_forn, key="forn_pesquisa", on_change=puxar_dados_fornecedor)
        with c_limp:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🧹 Limpar Campos", key="btn_limpar_forn"):
                limpar_fornecedor()
                st.rerun()
                
        st.markdown("---")
        st.subheader("Dados do Fornecedor")
        
        # Linha 1: Nome Fantasia
        nome_forn = st.text_input("Nome do Fornecedor (Fantasia) *", key="forn_nome")
        
        # Linha 2: Razão Social e CNPJ
        c1, c2 = st.columns(2)
        with c1: razao_forn = st.text_input("Razão Social", key="forn_razao")
        with c2: cnpj_forn = st.text_input("CNPJ", key="forn_cnpj")
        
        # Linha 3: Endereço
        end_forn = st.text_input("Endereço Completo", key="forn_end")
        
        # Linha 4: Vendedor e Telefone
        c3, c4 = st.columns(2)
        with c3: vend_forn = st.text_input("Nome do Vendedor / Contato", key="forn_vend")
        with c4: tel_forn = st.text_input("Telefone", key="forn_tel", placeholder="Ex: 85 996581537")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2, col_vazio = st.columns([2, 2, 4])
        
        with col_btn1:
            btn_salvar_forn = st.button("💾 Salvar Fornecedor")
        with col_btn2:
            btn_excluir_forn = st.button("🗑️ Excluir Fornecedor")
        
        if btn_salvar_forn:
            if nome_forn.strip():
                try:
                    client = get_sheets_client()
                    doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                    
                    try: 
                        sheet = doc.worksheet("Fornecedores")
                        if sheet.col_count < 6:
                            sheet.add_cols(6 - sheet.col_count)
                        header = sheet.row_values(1)
                        if len(header) < 6 or header[5] != "Razão Social":
                            sheet.update_cell(1, 6, "Razão Social")
                    except:
                        sheet = doc.add_worksheet(title="Fornecedores", rows="1000", cols="6")
                        sheet.append_row(["Nome do Fornecedor", "CNPJ", "Endereço", "Vendedor", "Telefone", "Razão Social"])
                    
                    nome_busca = st.session_state.get("forn_original", "").strip()
                    if not nome_busca:
                        nome_busca = nome_forn.strip()
                        
                    # --- NOVA LÓGICA DE FORMATAÇÃO DE TELEFONE ---
                    tel_raw = tel_forn.strip()
                    nums_tel = re.sub(r'\D', '', tel_raw)
                    
                    if nums_tel:
                        # Remove o 55 inicial se a pessoa já o tiver digitado, para não duplicar
                        if nums_tel.startswith("55") and len(nums_tel) > 10:
                            nums_tel = nums_tel[2:]
                            
                        # Aplica a máscara +55 (DD) XXXXXXXX
                        if len(nums_tel) >= 10:
                            # O apóstrofo (') no início impede que o Google Sheets leia o + como fórmula!
                            tel_formatado = f"'+55 ({nums_tel[:2]}) {nums_tel[2:]}"
                        else:
                            tel_formatado = f"'+55 {nums_tel}"
                    else:
                        # Se não tiver números, envia o texto que estava (com o apóstrofo por segurança)
                        tel_formatado = f"'{tel_raw}" if tel_raw else ""
                    # ---------------------------------------------
                        
                    valores = [
                        nome_forn.strip(), cnpj_forn.strip(), end_forn.strip(), 
                        vend_forn.strip(), tel_formatado, razao_forn.strip()
                    ]
                    
                    df = pd.DataFrame(sheet.get_all_records())
                    atualizado = False
                    
                    if not df.empty and "Nome do Fornecedor" in df.columns:
                        df["Nome_Match"] = df["Nome do Fornecedor"].astype(str).str.strip()
                        if nome_busca in df["Nome_Match"].values:
                            idx = df[df["Nome_Match"] == nome_busca].index[0]
                            sheet.update(range_name=f'A{idx+2}:F{idx+2}', values=[valores], value_input_option="USER_ENTERED")
                            atualizado = True
                            
                    if not atualizado:
                        sheet.append_row(valores, value_input_option="USER_ENTERED")
                        
                    st.success(f"✅ Fornecedor '{nome_forn}' salvo com sucesso!")
                    get_lista_fornecedores.clear() 
                    limpar_fornecedor()
                    st.rerun()
                except Exception as e: st.error(f"❌ Erro ao salvar fornecedor: {e}")
            else: st.error("❌ O campo 'Nome do Fornecedor' é obrigatório.")
            
        if btn_excluir_forn:
            nome_busca = st.session_state.get("forn_original", "").strip()
            nome_alvo = nome_busca if nome_busca else nome_forn.strip()
            
            if nome_alvo:
                try:
                    client = get_sheets_client()
                    doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                    sheet = doc.worksheet("Fornecedores")
                    
                    df = pd.DataFrame(sheet.get_all_records())
                    if not df.empty and "Nome do Fornecedor" in df.columns:
                        df["Nome_Match"] = df["Nome do Fornecedor"].astype(str).str.strip()
                        
                        mask = df["Nome_Match"] == nome_alvo
                        indices = df[mask].index.tolist()
                        
                        if indices:
                            linhas_sheet = [i + 2 for i in indices]
                            for linha in sorted(linhas_sheet, reverse=True):
                                sheet.delete_rows(linha)
                                
                            st.success(f"✅ Fornecedor '{nome_alvo}' excluído com sucesso!")
                            get_lista_fornecedores.clear()
                            limpar_fornecedor()
                            st.rerun()
                        else:
                            st.warning("⚠️ Fornecedor não encontrado na base de dados para exclusão.")
                except Exception as e:
                    st.error(f"❌ Erro ao excluir fornecedor: {e}")
            else:
                st.error("❌ Selecione no menu superior ou digite o nome de um fornecedor válido para excluir.")
                
        st.markdown("---")
        st.subheader("Fornecedores Cadastrados")
        try:
            client = get_sheets_client()
            doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
            sheet_forn = doc.worksheet("Fornecedores")
            df_forn = pd.DataFrame(sheet_forn.get_all_records())
            
            if not df_forn.empty:
               # Reorganiza a ordem das colunas para exibição na tabela
                ordem_colunas = ["Nome do Fornecedor", "Vendedor", "Telefone", "Endereço", "Razão Social", "CNPJ"]
                
                # Garante que só puxa as colunas que realmente existem para evitar erros
                colunas_finais = [col for col in ordem_colunas if col in df_forn.columns]
                df_forn = df_forn[colunas_finais]
                
                st.dataframe(df_forn, use_container_width=True, hide_index=True)
            else: 
                st.info("Nenhum fornecedor registrado ainda.")
        except: 
            st.info("Nenhum fornecedor registrado ainda.")
# =====================================================================
# MÓDULO 1: CADASTRO DE ANÚNCIOS
# =====================================================================
elif menu_selecionado == "Cadastro de Anúncios":
    import json
    
    # ==========================================================
    # CACHE INTELIGENTE DOS ANÚNCIOS (Para a barra de pesquisa)
    # ==========================================================
    def limpar_cache_anuncios():
        if "anuncios_opcoes" in st.session_state: del st.session_state["anuncios_opcoes"]
        if "df_anuncios_cache" in st.session_state: del st.session_state["df_anuncios_cache"]

    if "anuncios_opcoes" not in st.session_state:
        st.session_state.anuncios_opcoes = [""]
        st.session_state.df_anuncios_cache = pd.DataFrame()
        try:
            client = get_sheets_client()
            doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
            sheet_anuncios = doc.sheet1
            df_a = pd.DataFrame(sheet_anuncios.get_all_records(value_render_option="UNFORMATTED_VALUE"))
            st.session_state.df_anuncios_cache = df_a
            
            if not df_a.empty and "ID do Anúncio" in df_a.columns:
                ops = [""]
                for _, row in df_a.iterrows():
                    c = str(row.get("ID do Anúncio", "")).strip()
                    n = str(row.get("Título", "")).strip()
                    if c: ops.append(f"{c} | {n}")
                st.session_state.anuncios_opcoes = ops
        except:
            pass

    def carregar_repositorio():
        try:
            client = get_sheets_client()
            sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").sheet1
            data = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
            if not data: return pd.DataFrame(columns=["ID do Anúncio", "SKU", "Produto", "Título", "Custo", "Preço Original", "Desconto", "Frete", "Comissão", "Taxa Fixa", "Estorno", "TACOS", "Imposto", "Última Atualização", "Link do Anúncio", "Estrategias_Atacado", "Historico_Alteracoes", "Otimizacoes", "Tarefas Agendadas", "Link do Catálogo"])
            return pd.DataFrame(data)
        except: return pd.DataFrame(columns=["ID do Anúncio", "SKU", "Produto", "Título", "Custo", "Preço Original", "Desconto", "Frete", "Comissão", "Taxa Fixa", "Estorno", "TACOS", "Imposto", "Última Atualização", "Link do Anúncio", "Estrategias_Atacado", "Historico_Alteracoes", "Otimizacoes", "Tarefas Agendadas", "Link do Catálogo"])

    def salvar_no_repositorio(dados):
        client = get_sheets_client()
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").sheet1
        
        header = ["ID do Anúncio", "SKU", "Produto", "Título", "Custo", "Preço Original", "Desconto", "Frete", "Comissão", "Taxa Fixa", "Estorno", "TACOS", "Imposto", "Última Atualização", "Link do Anúncio", "Estrategias_Atacado", "Historico_Alteracoes", "Otimizacoes", "Tarefas Agendadas", "Link do Catálogo"]
        if sheet.col_count < 20: sheet.add_cols(20 - sheet.col_count)
        if sheet.row_values(1) != header: sheet.update(range_name='A1:T1', values=[header], value_input_option="USER_ENTERED")

        df = carregar_repositorio()
        valores_formatados = [f"{v:.2f}".replace('.', ',') if isinstance(v, float) else str(v) for v in dados.values()]
        if not df.empty and "ID do Anúncio" in df.columns and dados["ID do Anúncio"] in df["ID do Anúncio"].values:
            idx = df[df["ID do Anúncio"] == dados["ID do Anúncio"]].index[0]
            sheet.update(range_name=f'A{idx+2}:T{idx+2}', values=[valores_formatados], value_input_option="USER_ENTERED")
        else: sheet.append_row(valores_formatados, value_input_option="USER_ENTERED")

    def processar_calculo_custo():
        val = avaliar_expressao_matematica(st.session_state.custo)
        if val is not None: st.session_state.custo = f"{val:.2f}".replace('.', ',')

    def puxar_dados_produto_por_sku_trigger():
        sku_digitado = st.session_state.get("sku", "").strip()
        if sku_digitado:
            info_prod = buscar_produto_por_sku(sku_digitado)
            if info_prod is not None:
                st.session_state.nome_produto = str(info_prod.get("Produto", ""))
                st.session_state.custo = formatar_moeda_ui(info_prod.get("Custo", 0))
                st.session_state.medida = str(info_prod.get("Medida", ""))
                st.session_state.peso = str(info_prod.get("Peso", ""))
                st.session_state.fornecedor_produto = str(info_prod.get("Fornecedor", ""))

    def resetar_campos():
        campos = ["id_anuncio", "sku", "nome_produto", "titulo", "ultima_atualizacao", "link_anuncio", "link_catalogo", "medida", "peso", "fornecedor_produto"]
        for c in campos: st.session_state[c] = ""
        st.session_state.custo = "0,00"
        st.session_state.preco = "0,00"
        st.session_state.desconto = 0.0
        st.session_state.frete = "0,00"
        st.session_state.comissao = 16.5
        st.session_state.taxa = "6,00"
        st.session_state.estorno = "0,00"
        st.session_state.tacos = 0.0
        st.session_state.imposto = 7.3  
        st.session_state.otimizacoes = ""
        
        if "pesquisa_anuncio" in st.session_state: del st.session_state["pesquisa_anuncio"]
        
        if "num_atacado" in st.session_state: st.session_state.num_atacado = 0
        for k in list(st.session_state.keys()):
            if k.startswith("atac_"): del st.session_state[k]
            
        if "ultimo_id_carregado" in st.session_state: del st.session_state.ultimo_id_carregado
        if "mostrar_sucesso" in st.session_state: del st.session_state.mostrar_sucesso
        if "msg_salvo_anuncio" in st.session_state: del st.session_state.msg_salvo_anuncio
        if "id_anuncio_salvo" in st.session_state: del st.session_state.id_anuncio_salvo
        if "historico_anuncio" in st.session_state: st.session_state.historico_anuncio = []
        if "tarefas_anuncio" in st.session_state: st.session_state.tarefas_anuncio = []
        if "estado_original_anuncio" in st.session_state: st.session_state.estado_original_anuncio = {}

    if "custo" not in st.session_state: st.session_state.custo = "0,00"
    if "preco" not in st.session_state: st.session_state.preco = "0,00"
    if "ultima_atualizacao" not in st.session_state: st.session_state.ultima_atualizacao = ""
    if "nome_produto" not in st.session_state: st.session_state.nome_produto = ""
    if "sku" not in st.session_state: st.session_state.sku = ""
    if "link_anuncio" not in st.session_state: st.session_state.link_anuncio = ""
    if "link_catalogo" not in st.session_state: st.session_state.link_catalogo = ""
    if "medida" not in st.session_state: st.session_state.medida = ""
    if "peso" not in st.session_state: st.session_state.peso = ""
    if "fornecedor_produto" not in st.session_state: st.session_state.fornecedor_produto = ""
    if "otimizacoes" not in st.session_state: st.session_state.otimizacoes = ""
    if "tarefas_anuncio" not in st.session_state: st.session_state.tarefas_anuncio = []

    id_atual = st.session_state.get("id_anuncio", "")
    if id_atual and st.session_state.get("ultimo_id_carregado") != id_atual:
        repo = carregar_repositorio()
        if not repo.empty and "ID do Anúncio" in repo.columns:
            dados_existentes = repo[repo["ID do Anúncio"] == id_atual]
            if not dados_existentes.empty:
                row = dados_existentes.iloc[0]
                st.session_state.sku = str(row.get("SKU", "")) if pd.notna(row.get("SKU")) else ""
                st.session_state.nome_produto = str(row.get("Produto", "")) if pd.notna(row.get("Produto")) else ""
                st.session_state.titulo = str(row.get("Título", ""))
                st.session_state.link_anuncio = str(row.get("Link do Anúncio", "")) if pd.notna(row.get("Link do Anúncio")) else ""
                st.session_state.link_catalogo = str(row.get("Link do Catálogo", "")) if pd.notna(row.get("Link do Catálogo")) else ""
                st.session_state.custo = formatar_moeda_ui(row.get("Custo", 0))
                st.session_state.preco = formatar_moeda_ui(row.get("Preço Original", 0))
                st.session_state.frete = formatar_moeda_ui(row.get("Frete", 0))
                st.session_state.taxa = formatar_moeda_ui(row.get("Taxa Fixa", 0))
                st.session_state.estorno = formatar_moeda_ui(row.get("Estorno", 0))
                st.session_state.desconto = float(converter_valor(row.get("Desconto", 0)))
                st.session_state.comissao = float(converter_valor(row.get("Comissão", 16.5)))
                st.session_state.tacos = float(converter_valor(row.get("TACOS", 0)))
                st.session_state.imposto = float(converter_valor(row.get("Imposto", 7.3)))
                st.session_state.ultima_atualizacao = converter_data_sheets(row.get("Última Atualização", ""))
                st.session_state.otimizacoes = str(row.get("Otimizacoes", "")) if pd.notna(row.get("Otimizacoes")) else ""
                
                raw_atacado = row.get("Estrategias_Atacado", "[]")
                atacado_json = str(raw_atacado) if pd.notna(raw_atacado) else "[]"
                try:
                    atacado_data = json.loads(atacado_json) if atacado_json.strip() else []
                except:
                    atacado_data = []

                if atacado_data:
                    st.session_state.num_atacado = len(atacado_data)
                    for i, opt in enumerate(atacado_data):
                        st.session_state[f"atac_desc_{i}"] = float(opt.get("desconto", 0.0))
                        st.session_state[f"atac_unid_{i}"] = int(opt.get("unidades", 1))
                        st.session_state[f"atac_frete_{i}"] = str(opt.get("frete", "0,00"))
                        st.session_state[f"atac_del_{i}"] = False
                else:
                    st.session_state.num_atacado = 0
                    for k in list(st.session_state.keys()):
                        if k.startswith("atac_"): del st.session_state[k]
                        
                raw_hist = row.get("Historico_Alteracoes", "[]")
                try:
                    st.session_state.historico_anuncio = json.loads(str(raw_hist)) if pd.notna(raw_hist) and str(raw_hist).strip() else []
                except:
                    st.session_state.historico_anuncio = []
                    
                raw_tarefas = row.get("Tarefas Agendadas", "[]")
                try:
                    st.session_state.tarefas_anuncio = json.loads(str(raw_tarefas)) if pd.notna(raw_tarefas) and str(raw_tarefas).strip() else []
                except:
                    st.session_state.tarefas_anuncio = []
                    
                st.session_state.estado_original_anuncio = {
                    "SKU": st.session_state.sku,
                    "Título": st.session_state.titulo,
                    "Custo": float(converter_valor(row.get("Custo", 0))),
                    "Preço Original": float(converter_valor(row.get("Preço Original", 0))),
                    "Desconto": st.session_state.desconto,
                    "Frete": float(converter_valor(row.get("Frete", 0))),
                    "Comissão": st.session_state.comissao,
                    "Custo Full": float(converter_valor(row.get("Taxa Fixa", 0))),
                    "Estorno": float(converter_valor(row.get("Estorno", 0))),
                    "ACOS OBJ.": st.session_state.tacos,
                    "Imposto": st.session_state.imposto,
                    "Link": st.session_state.link_anuncio,
                    "Link Catálogo": st.session_state.link_catalogo,
                    "Estratégias Atacado": atacado_json,
                    "Otimizações": st.session_state.otimizacoes
                }
                
                # BUSCA EM TEMPO REAL NO CADASTRO DE PRODUTOS
                if st.session_state.sku:
                    prod_mestre = buscar_produto_por_sku(st.session_state.sku)
                    if prod_mestre is not None:
                        st.session_state.nome_produto = str(prod_mestre.get("Produto", ""))
                        st.session_state.custo = formatar_moeda_ui(prod_mestre.get("Custo", 0))
                        st.session_state.medida = str(prod_mestre.get("Medida", ""))
                        st.session_state.peso = str(prod_mestre.get("Peso", ""))
                        st.session_state.fornecedor_produto = str(prod_mestre.get("Fornecedor", ""))
                    else:
                        st.session_state.medida = ""
                        st.session_state.peso = ""
                        st.session_state.fornecedor_produto = ""

                st.session_state.ultimo_id_carregado = id_atual
                st.session_state.mostrar_sucesso = True
            else: st.session_state.ultimo_id_carregado = id_atual
        else: st.session_state.ultimo_id_carregado = id_atual

    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.5, 3, 0.5])
    with col_conteudo:
        st.title("Cadastro e Gestão de Anúncios")
        
        tab_cadastro, tab_tarefas = st.tabs(["📝 Cadastro / Edição", "📋 Tarefas Pendentes e Alertas"])
        
        with tab_cadastro:
            if st.button("🧹 Limpar Dados"):
                resetar_campos()
                st.rerun()

            st.markdown("---")
            
            # --- CAMPO DE PESQUISA INTELIGENTE ---
            def on_change_pesquisa_anuncio():
                val = st.session_state.get("pesquisa_anuncio", "")
                if val and " | " in val:
                    id_buscado = val.split(" | ")[0].strip()
                    st.session_state.id_anuncio = id_buscado
                    st.session_state.ultimo_id_carregado = "" # Força recarregamento

            st.selectbox("🔍 Pesquisar Anúncio Salvo (MLB ou Título)", st.session_state.anuncios_opcoes, key="pesquisa_anuncio", on_change=on_change_pesquisa_anuncio)
            st.markdown("<br>", unsafe_allow_html=True)
            # -------------------------------------

            st.subheader("📢 Dados do Anúncio")
            col1, col2, col3 = st.columns([1.5, 3, 1.5])
            with col1: id_input = st.text_input("ID do Anúncio (MLB)", placeholder="Ex: MLB123456789", key="id_anuncio")
            with col2:
                titulo_anuncio = st.text_input("Título do Anúncio", key="titulo")
                if titulo_anuncio: 
                    if len(titulo_anuncio) > 60: st.caption(f"⚠️ Caracteres: {len(titulo_anuncio)} (Acima do limite de 60 do ML)")
                    else: st.caption(f"Caracteres: {len(titulo_anuncio)}/60") 
            with col3: st.text_input("Última Atualização", value=st.session_state.ultima_atualizacao, disabled=True)
            
            # --- LINKS DO ANÚNCIO E DO CATÁLOGO ---
            c_link1, c_link2 = st.columns([4, 1])
            with c_link1:
                link_anuncio_input = st.text_input("🔗 Link do Anúncio", placeholder="Ex: https://produto.mercadolivre.com.br/MLB-...", key="link_anuncio")
            with c_link2:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                link_atual = st.session_state.get("link_anuncio", "").strip()
                if link_atual.startswith("http"):
                    st.markdown(f'''
                        <a href="{link_atual}" target="_blank" style="display: block; text-align: center; background-color: rgba(116, 209, 234, 0.6); color: #250E62; padding: 7px 0; border-radius: 5px; text-decoration: none; font-weight: bold; border: 1px solid #74D1EA;">
                            Acessar Anúncio 🔗
                        </a>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('''
                        <div style="display: block; text-align: center; background-color: #E5E7EB; color: #9CA3AF; padding: 7px 0; border-radius: 5px; font-weight: bold; border: 1px solid #D1D5DB; cursor: not-allowed;">
                            Acessar Anúncio 🔗
                        </div>
                    ''', unsafe_allow_html=True)
                    
            c_cat1, c_cat2 = st.columns([4, 1])
            with c_cat1:
                link_catalogo_input = st.text_input("🔗 Link do Catálogo", placeholder="Ex: https://produto.mercadolivre.com.br/MLB-...-catalogo", key="link_catalogo")
            with c_cat2:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                link_cat_atual = st.session_state.get("link_catalogo", "").strip()
                if link_cat_atual.startswith("http"):
                    st.markdown(f'''
                        <a href="{link_cat_atual}" target="_blank" style="display: block; text-align: center; background-color: rgba(116, 209, 234, 0.6); color: #250E62; padding: 7px 0; border-radius: 5px; text-decoration: none; font-weight: bold; border: 1px solid #74D1EA;">
                            Acessar Catálogo 🔗
                        </a>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('''
                        <div style="display: block; text-align: center; background-color: #E5E7EB; color: #9CA3AF; padding: 7px 0; border-radius: 5px; font-weight: bold; border: 1px solid #D1D5DB; cursor: not-allowed;">
                            Acessar Catálogo 🔗
                        </div>
                    ''', unsafe_allow_html=True)
            # ----------------------------------------

            if st.session_state.get("mostrar_sucesso") and id_input == st.session_state.get("ultimo_id_carregado"):
                st.info("ℹ️ Dados recuperados da nuvem.")

            st.markdown("---")
            st.subheader("📦 Dados do Produto")
            col_sku, col_prod, col_custo = st.columns([1, 2, 1])
            with col_sku: sku_anuncio = st.text_input("SKU do Produto", placeholder="Ex: SKU-12345-X", key="sku", on_change=puxar_dados_produto_por_sku_trigger)
            with col_prod: nome_produto = st.text_input("Produto", placeholder="Ex: Camiseta Térmica", key="nome_produto")
            with col_custo: st.text_input("Preço de Custo (R$)", key="custo", on_change=processar_calculo_custo)
            
            c_medida, c_peso, c_forn = st.columns([1, 1, 2])
            with c_medida: st.text_input("Medidas (A x L x C)", key="medida", disabled=True)
            with c_peso: st.text_input("Peso (kg)", key="peso", disabled=True)
            with c_forn: st.text_input("Fornecedor", key="fornecedor_produto", disabled=True)

            custo_produto = converter_valor(st.session_state.custo)
            st.markdown("---")

            st.subheader("💸 Dados da Venda")
            col_preco, col_desc, col_final = st.columns(3)
            with col_preco: preco_original_str = st.text_input("Preço Original (R$)", key="preco")
            with col_desc: porcentagem_desconto = st.number_input("Desconto (%)", min_value=0.0, max_value=100.0, step=0.1, key="desconto")
            
            preco_original = converter_valor(preco_original_str)
            preco_final = preco_original * (1 - (porcentagem_desconto / 100))
            with col_final: st.text_input("Venda Real (R$)", value=f"{preco_final:.2f}".replace('.', ','), disabled=True)

            col_comissao, col_frete, col_taxa = st.columns(3)
            with col_comissao: comissao_mkt_porcentagem = st.number_input("Comissão Marketplace (%)", min_value=0.0, step=0.1, key="comissao")
            with col_frete: custo_frete_str = st.text_input("Custo de Frete (R$)", key="frete")
            with col_taxa: taxa_fixa_venda_str = st.text_input("Custo Full (R$)", key="taxa")

            col_estorno, col_tacos, col_imposto = st.columns(3)
            with col_estorno: estorno_ml_str = st.text_input("Estorno/Bonificação ML (R$)", key="estorno")
            with col_tacos: porcentagem_tacos = st.number_input("Custo de Publicidade ACOS OBJ. (%)", min_value=0.0, max_value=100.0, step=0.1, key="tacos")
            with col_imposto: imposto_porcentagem = st.number_input("Imposto sobre NF (%)", min_value=0.0, value=7.3, step=0.1, key="imposto")

            custo_frete = converter_valor(custo_frete_str)
            taxa_fixa_venda = converter_valor(taxa_fixa_venda_str)
            estorno_ml = converter_valor(estorno_ml_str)

            valor_comissao = preco_final * (comissao_mkt_porcentagem / 100)
            valor_imposto = preco_final * (imposto_porcentagem / 100)
            valor_tacos = preco_final * (porcentagem_tacos / 100)

            custo_total_saidas = custo_produto + custo_frete + valor_comissao + valor_imposto + taxa_fixa_venda + valor_tacos
            lucro_liquido = (preco_final + estorno_ml) - custo_total_saidas
            margem_contribuicao = arredondar_customizado((lucro_liquido / preco_final) * 100) if preco_final > 0 else 0.0

            st.divider()
            st.subheader("📈 Resultados")
            if titulo_anuncio:
                st.markdown(f"**Anúncio:** {titulo_anuncio}" + (f" | **SKU:** {sku_anuncio}" if sku_anuncio else ""))

            col_res_custo, col_res_lucro, col_res_margem = st.columns(3)
            with col_res_custo: st.metric("Custo Total", f"R$ {custo_total_saidas:.2f}".replace('.', ','))
            with col_res_lucro: st.metric("Lucro Líquido", f"R$ {lucro_liquido:.2f}".replace('.', ','))
            with col_res_margem: st.metric("Margem", f"{margem_contribuicao:.2f}%".replace('.', ','))

            if margem_contribuicao < 15: st.error("⚠️ Margem baixa! Verifique o desconto ou os custos.")
            elif 15 <= margem_contribuicao <= 25: st.warning("⚖️ Margem aceitável para giro.")
            else: st.success("✅ Margem excelente para o seu produto!")

            st.write("### Detalhamento Financeiro")
            denominador = preco_final if preco_final > 0 else 1.0
            valor_desconto = preco_original - preco_final

            descricoes = ["Preço Original", "Desconto", "Preço Final", "Custo Produto", "Comissão", "Frete", "Imposto", "Custo Full", "ACOS OBJ.", "Estorno", "LUCRO LÍQUIDO"]
            tipos = ["positivo", "negativo", "positivo", "negativo", "negativo", "negativo", "negativo", "negativo", "negativo", "positivo", "positivo"]
            valores = [preco_original, valor_desconto, preco_final, custo_produto, valor_comissao, custo_frete, valor_imposto, taxa_fixa_venda, valor_tacos, estorno_ml, lucro_liquido]

            html_table = "<table style='width: 100%; border-collapse: collapse; text-align: left; background-color: #F8F9FA; color: #1E1E1E; font-size: 14px; margin-bottom: 1rem;'>"
            html_table += "<tr><th style='padding: 4px 8px; border-bottom: 1px solid #D1D5DB; font-weight: 600;'>Descrição</th><th style='padding: 4px 8px; border-bottom: 1px solid #D1D5DB; font-weight: 600;'>Valor</th><th style='padding: 4px 8px; border-bottom: 1px solid #D1D5DB; font-weight: 600;'>Percentual (%)</th></tr>"

            for desc, val, tipo in zip(descricoes, valores, tipos):
                cor_hex = "#198754" if tipo == "positivo" else "#DC3545"
                sinal = "-" if tipo == "negativo" and val > 0 else ""
                
                pct = (val / denominador) * 100 
                
                val_fmt = f"{sinal}R$ {val:.2f}".replace('.', ',')
                pct_fmt = f"{sinal}{pct:.2f}%".replace('.', ',')
                
                peso_fonte = "bold" if desc == "LUCRO LÍQUIDO" else "normal"
                borda = "border-top: 1px solid #D1D5DB;" if desc == "LUCRO LÍQUIDO" else "border: none;"
                
                html_table += f"<tr style='{borda}'><td style='padding: 2px 8px; font-weight: {peso_fonte};'>{desc}</td>"
                html_table += f"<td style='padding: 2px 8px; color: {cor_hex}; font-weight: {peso_fonte};'>{val_fmt}</td>"
                html_table += f"<td style='padding: 2px 8px; color: {cor_hex}; font-weight: {peso_fonte};'>{pct_fmt}</td></tr>"

            html_table += "</table>"
            
            st.markdown(html_table, unsafe_allow_html=True)

            # =========================================================
            # SECÇÃO: VENDA ATACADO
            # =========================================================
            st.markdown("---")
            
            col_tit_atac, col_del_atac = st.columns([3, 1])
            with col_tit_atac:
                st.subheader("📦 Estratégias de Venda no Atacado")
                
            if "num_atacado" not in st.session_state:
                st.session_state.num_atacado = 1
                
            def remover_selecionados():
                to_delete = [i for i in range(st.session_state.num_atacado) if st.session_state.get(f"atac_del_{i}", False)]
                if not to_delete: return
                
                remaining = []
                for i in range(st.session_state.num_atacado):
                    if i not in to_delete:
                        remaining.append({
                            "desc": st.session_state.get(f"atac_desc_{i}", 0.0),
                            "unid": st.session_state.get(f"atac_unid_{i}", 1),
                            "frete": st.session_state.get(f"atac_frete_{i}", "0,00")
                        })
                
                for i in range(st.session_state.num_atacado):
                    for k in ["atac_desc_", "atac_unid_", "atac_frete_", "atac_del_"]:
                        if f"{k}{i}" in st.session_state: del st.session_state[f"{k}{i}"]
                            
                st.session_state.num_atacado = len(remaining)
                for i, data in enumerate(remaining):
                    st.session_state[f"atac_desc_{i}"] = data["desc"]
                    st.session_state[f"atac_unid_{i}"] = data["unid"]
                    st.session_state[f"atac_frete_{i}"] = data["frete"]
                    st.session_state[f"atac_del_{i}"] = False

            with col_del_atac:
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                if st.session_state.num_atacado > 0:
                    if st.button("🗑️ Excluir Selecionadas"):
                        remover_selecionados()
                        st.rerun()
                        
            for i in range(st.session_state.num_atacado):
                st.markdown(f"**Opção {i+1}**")
                
                c_chk, c_desc, c_unid, c_frete, c_pu, c_vt, c_lucro = st.columns([0.5, 2, 2, 2, 2, 2, 2.5])
                
                with c_chk:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    st.checkbox(" ", key=f"atac_del_{i}", label_visibility="collapsed")
                    
                with c_desc:
                    desc_atac = st.number_input("Desconto (%)", min_value=0.0, max_value=100.0, step=0.1, key=f"atac_desc_{i}")
                with c_unid:
                    unid_atac = st.number_input("Unidades", min_value=1, step=1, key=f"atac_unid_{i}")
                with c_frete:
                    if f"atac_frete_{i}" not in st.session_state:
                        st.session_state[f"atac_frete_{i}"] = "0,00"
                    frete_atac_str = st.text_input("Frete (R$)", key=f"atac_frete_{i}")
                    frete_atac = converter_valor(frete_atac_str)
                    
                # Cálculos Atacado
                preco_unit_atac = preco_original * (1 - (desc_atac / 100))
                valor_total_atac = preco_unit_atac * unid_atac
                
                comissao_atac = valor_total_atac * (comissao_mkt_porcentagem / 100)
                imposto_atac = valor_total_atac * (imposto_porcentagem / 100)
                tacos_atac = valor_total_atac * (porcentagem_tacos / 100)
                custo_total_atac = custo_produto * unid_atac
                
                lucro_atac = valor_total_atac - frete_atac - comissao_atac - imposto_atac - tacos_atac - custo_total_atac
                margem_atac = (lucro_atac / valor_total_atac * 100) if valor_total_atac > 0 else 0.0
                
                spc = "\u200B" * i
                with c_pu:
                    st.text_input(f"Preço Unitário (R$){spc}", value=f"{preco_unit_atac:.2f}".replace('.', ','), disabled=True)
                with c_vt:
                    st.text_input(f"Valor Total (R$){spc}", value=f"{valor_total_atac:.2f}".replace('.', ','), disabled=True)
                with c_lucro:
                    st.text_input(f"Lucro Líquido / Margem{spc}", value=f"R$ {lucro_atac:.2f} ({margem_atac:.2f}%)".replace('.', ','), disabled=True)
                    
            if st.button("➕ Acrescentar outra linha de estratégia para venda em atacado"):
                st.session_state.num_atacado += 1
                st.rerun()

            # =========================================================
            # SECÇÃO: OTIMIZAÇÕES
            # =========================================================
            st.markdown("---")
            st.subheader("💡 Otimizações")
            otimizacoes_texto = st.text_area("Observações e testes aplicados no anúncio:", key="otimizacoes", height=100)

            # ==========================================================
            # SEÇÃO: AGENDAMENTO DE TAREFAS
            # ==========================================================
            st.markdown("---")
            st.subheader("📅 Agendamento de Tarefas")
            st.markdown("Crie tarefas para serem acompanhadas na aba de **Tarefas Pendentes**.")
            
            c_t1, c_t2, c_t3 = st.columns([3, 1.5, 1.5])
            with c_t1: nova_desc_tarefa = st.text_input("Descrição da Tarefa", key="nova_desc_tarefa", placeholder="Ex: Ajustar título SEO após testes")
            with c_t2: nova_data_tarefa = st.text_input("Data de Vencimento", key="nova_data_tarefa", placeholder="DD/MM/AAAA")
            with c_t3: 
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Adicionar Tarefa"):
                    if nova_desc_tarefa.strip():
                        st.session_state.tarefas_anuncio.append({
                            "descricao": nova_desc_tarefa.strip(),
                            "vencimento": nova_data_tarefa.strip(),
                            "status": "Pendente"
                        })
                        
                        if "nova_desc_tarefa" in st.session_state: del st.session_state["nova_desc_tarefa"]
                        if "nova_data_tarefa" in st.session_state: del st.session_state["nova_data_tarefa"]
                        st.rerun()
                    else:
                        st.warning("Preencha a descrição da tarefa.")

            if st.session_state.tarefas_anuncio:
                st.markdown("<br><b>Tarefas para este anúncio:</b>", unsafe_allow_html=True)
                for i, tar in enumerate(st.session_state.tarefas_anuncio):
                    c_tdesc, c_tvenc, c_tdel = st.columns([4, 2, 1])
                    c_tdesc.markdown(f"📌 {tar.get('descricao', '')}")
                    c_tvenc.markdown(f"📅 {tar.get('vencimento', '')}")
                    if c_tdel.button("🗑️ Excluir", key=f"del_tar_{i}"):
                        st.session_state.tarefas_anuncio.pop(i)
                        st.rerun()
            else:
                st.info("Nenhuma tarefa manual agendada para este anúncio.")
            # ==========================================================

            # =========================================================
            # SECÇÃO: HISTÓRICO DE ALTERAÇÕES
            # =========================================================
            st.markdown("---")
            st.subheader("🕒 Histórico de Alterações")
            
            historico_atual = st.session_state.get("historico_anuncio", [])
            if historico_atual:
                df_hist = pd.DataFrame(historico_atual)
                if "Otimizações" not in df_hist.columns:
                    df_hist["Otimizações"] = "-"
                df_hist["Otimizações"] = df_hist["Otimizações"].fillna("-")
                
                st.dataframe(
                    df_hist.style.set_properties(**{
                        'background-color': '#F4F6F9',
                        'color': '#1E1E1E',
                        'border-color': '#E5E7EB'
                    }),
                    use_container_width=True,
                    hide_index=True 
                )
            else:
                st.info("Nenhuma alteração registada para este anúncio.")

            st.markdown("---")
            if st.session_state.get("msg_salvo_anuncio"):
                if id_input == st.session_state.get("id_anuncio_salvo"):
                    st.success(st.session_state.msg_salvo_anuncio)
                else:
                    st.session_state.msg_salvo_anuncio = ""

            if st.button("💾 Salvar Anúncio na Nuvem"):
                faltantes = [f for f, v in [("ID do Anúncio", id_input), ("Título", titulo_anuncio), ("Preço de Custo", custo_produto)] if not v or (isinstance(v, float) and v <= 0)]
                if not faltantes:
                    data_apenas = datetime.now().strftime("%d/%m/%Y")
                    data_hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    st.session_state.ultima_atualizacao = data_apenas
                    
                    # Agrupando atacado
                    atacado_data = []
                    for i in range(st.session_state.get("num_atacado", 0)):
                        atacado_data.append({
                            "desconto": st.session_state.get(f"atac_desc_{i}", 0.0),
                            "unidades": st.session_state.get(f"atac_unid_{i}", 1),
                            "frete": st.session_state.get(f"atac_frete_{i}", "0,00")
                        })
                    estrategias_json = json.dumps(atacado_data)
                    tarefas_json = json.dumps(st.session_state.get("tarefas_anuncio", []))
                    
                    # --- LÓGICA DE AUDITORIA E HISTÓRICO ---
                    campos_rastreados = {
                        "SKU": sku_anuncio,
                        "Título": titulo_anuncio,
                        "Custo": custo_produto,
                        "Preço Original": preco_original,
                        "Desconto": porcentagem_desconto,
                        "Frete": custo_frete,
                        "Comissão": comissao_mkt_porcentagem,
                        "Custo Full": taxa_fixa_venda,
                        "Estorno": estorno_ml,
                        "ACOS OBJ.": porcentagem_tacos,
                        "Imposto": imposto_porcentagem,
                        "Link": link_anuncio_input,
                        "Link Catálogo": link_catalogo_input,
                        "Estratégias Atacado": estrategias_json
                    }
                    
                    estado_orig = st.session_state.get("estado_original_anuncio", {})
                    mudancas = []
                    
                    def fmt_val(v):
                        if isinstance(v, float):
                            return f"{v:.2f}".replace('.', ',')
                        return str(v).strip()
                    
                    if not estado_orig:
                        mudancas.append("Novo anúncio cadastrado no sistema.")
                    else:
                        for k, v in campos_rastreados.items():
                            v_orig = estado_orig.get(k, "")
                            
                            if isinstance(v, float) and isinstance(v_orig, float):
                                if abs(v - v_orig) > 0.001: 
                                    mudancas.append(f"{k} (de {fmt_val(v_orig)} para {fmt_val(v)})")
                                    
                            elif k == "Estratégias Atacado":
                                try:
                                    j_v = json.loads(str(v)) if str(v).strip() else []
                                    j_orig = json.loads(str(v_orig)) if str(v_orig).strip() else []
                                    if j_v != j_orig:
                                        mudancas.append("Estratégias de Atacado alteradas")
                                except:
                                    if str(v).strip() != str(v_orig).strip():
                                        mudancas.append("Estratégias de Atacado alteradas")
                                        
                            elif str(v).strip() != str(v_orig).strip():
                                mudancas.append(f"{k} (de '{fmt_val(v_orig)}' para '{fmt_val(v)}')")

                    if mudancas:
                        if mudancas[0] == "Novo anúncio cadastrado no sistema.":
                            texto_mudancas = "Novo anúncio cadastrado no sistema."
                        else:
                            texto_mudancas = " | ".join(mudancas)
                    else:
                        texto_mudancas = "Anúncio guardado sem alterações nos valores principais."

                    otimizacoes_atuais = otimizacoes_texto.strip() if otimizacoes_texto.strip() else "-"

                    # Atualiza a lista do histórico
                    hist_list = st.session_state.get("historico_anuncio", [])
                    hist_list.insert(0, {
                        "Data da Alteração": data_hora_atual, 
                        "Detalhes das Alterações": texto_mudancas,
                        "Otimizações": otimizacoes_atuais
                    })
                    st.session_state.historico_anuncio = hist_list
                    historico_json = json.dumps(hist_list)
                    # ---------------------------------------
                    
                    dados_salvar = {
                        "ID do Anúncio": id_input, "SKU": sku_anuncio, "Produto": st.session_state.nome_produto, "Título": titulo_anuncio, 
                        "Custo": custo_produto, "Preço Original": preco_original, "Desconto": porcentagem_desconto, 
                        "Frete": custo_frete, "Comissão": comissao_mkt_porcentagem, "Taxa Fixa": taxa_fixa_venda, 
                        "Estorno": estorno_ml, "TACOS": porcentagem_tacos, "Imposto": imposto_porcentagem, "Última Atualização": data_apenas,
                        "Link do Anúncio": link_anuncio_input,
                        "Estrategias_Atacado": estrategias_json,
                        "Historico_Alteracoes": historico_json,
                        "Otimizacoes": otimizacoes_texto,
                        "Tarefas Agendadas": tarefas_json,
                        "Link do Catálogo": link_catalogo_input
                    }
                    
                    try:
                        salvar_no_repositorio(dados_salvar)
                        st.session_state.msg_salvo_anuncio = f"✅ Dados do anúncio '{id_input}' salvos com sucesso na nuvem! ({data_apenas})"
                        st.session_state.id_anuncio_salvo = id_input
                        
                        estado_novo = campos_rastreados.copy()
                        estado_novo["Otimizações"] = otimizacoes_texto
                        st.session_state.estado_original_anuncio = estado_novo
                        
                        limpar_cache_anuncios() # Atualiza o cache da pesquisa após salvar
                        st.rerun()
                    except Exception as e: st.error(f"❌ Erro ao salvar na planilha: {e}")
                else: st.error(f"❌ Erro ao salvar: Preencha os campos obrigatórios: {', '.join(faltantes)}")

        # ==========================================================
        # ABA: TAREFAS PENDENTES E ALERTAS
        # ==========================================================
        with tab_tarefas:
            st.markdown("<br>", unsafe_allow_html=True)
            st.write("Acompanhe aqui os alertas de verificação de anúncios estagnados e as tarefas manuais agendadas.")
            
            repo_dados = carregar_repositorio()
            
            alertas_auto = []
            tarefas_manuais = []
            hoje = datetime.now()
            
            if not repo_dados.empty and "ID do Anúncio" in repo_dados.columns:
                for idx, row in repo_dados.iterrows():
                    id_an_lista = str(row.get("ID do Anúncio", ""))
                    tit_an_lista = str(row.get("Título", ""))
                    anuncio_ref = f"{id_an_lista} - {tit_an_lista}"
                    
                    # 1. Varredura Automática (> 7 dias sem atualização)
                    data_att_str = str(row.get("Última Atualização", ""))
                    if data_att_str:
                        try:
                            # Tenta converter a data da planilha
                            data_att = datetime.strptime(data_att_str.strip(), "%d/%m/%Y")
                            dias_passados = (hoje - data_att).days
                            if dias_passados > 7:
                                alertas_auto.append({
                                    "Anúncio": anuncio_ref,
                                    "Última Atualização": data_att_str,
                                    "Dias S/ Atualizar": dias_passados,
                                    "Tarefa Automática": "⚠️ Verificar Anúncio"
                                })
                        except:
                            pass
                    
                    # 2. Varredura de Tarefas Manuais Agendadas
                    raw_tarefas_lista = str(row.get("Tarefas Agendadas", "[]"))
                    try:
                        tar_list = json.loads(raw_tarefas_lista) if pd.notna(raw_tarefas_lista) and raw_tarefas_lista.strip() else []
                        for t in tar_list:
                            tarefas_manuais.append({
                                "Anúncio": anuncio_ref,
                                "Tarefa": t.get("descricao", ""),
                                "Vencimento": t.get("vencimento", "")
                            })
                    except:
                        pass
                        
            st.markdown("#### 🚨 Alertas de Atualização (> 7 dias)")
            if alertas_auto:
                df_alertas = pd.DataFrame(alertas_auto)
                st.dataframe(
                    df_alertas.style.set_properties(**{
                        'background-color': '#FFF3CD',
                        'color': '#856404',
                        'font-weight': 'bold'
                    }),
                    use_container_width=True, hide_index=True
                )
            else:
                st.success("✅ Excelente! Todos os anúncios registados foram atualizados nos últimos 7 dias.")
                
            st.markdown("---")
            st.markdown("#### 📅 Tarefas Manuais Agendadas")
            if tarefas_manuais:
                df_manuais = pd.DataFrame(tarefas_manuais)
                
                # --- LÓGICA DE ORDENAÇÃO POR DATA DE VENCIMENTO ---
                # 1. Cria uma coluna temporária transformando o texto em formato de Data real do Python
                df_manuais['Data_Sort'] = pd.to_datetime(df_manuais['Vencimento'], format='%d/%m/%Y', errors='coerce')
                
                # 2. Ordena a tabela pela data mais próxima e remove a coluna temporária
                df_manuais = df_manuais.sort_values(by='Data_Sort', ascending=True).drop(columns=['Data_Sort'])
                # --------------------------------------------------
                
                st.dataframe(
                    df_manuais.style.set_properties(**{
                        'background-color': '#F4F6F9',
                        'color': '#1E1E1E'
                    }),
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("Nenhuma tarefa manual agendada nos anúncios.")
# =====================================================================
# MÓDULO 2: CADASTRO DE PRODUTO & KITS
# =====================================================================
elif menu_selecionado == "Cadastro de Produto":
    
    if "limpar_produto" not in st.session_state: st.session_state.limpar_produto = False
    if "sucesso_produto" not in st.session_state: st.session_state.sucesso_produto = ""
    if "num_componentes_kit" not in st.session_state: st.session_state.num_componentes_kit = 1
    if "pesquisa_produto" not in st.session_state: st.session_state.pesquisa_produto = ""
    if "pesquisa_kit" not in st.session_state: st.session_state.pesquisa_kit = ""
    if "sku_original_p" not in st.session_state: st.session_state.sku_original_p = ""
    if "sku_original_kit" not in st.session_state: st.session_state.sku_original_kit = ""

    if "sku_p" not in st.session_state: st.session_state.sku_p = ""
    if "nome_p" not in st.session_state: st.session_state.nome_p = ""
    if "custo_p" not in st.session_state: st.session_state.custo_p = "0,00"
    if "forn_p" not in st.session_state: st.session_state.forn_p = ""
    if "data_ref_p" not in st.session_state: st.session_state.data_ref_p = ""
    if "ean_p" not in st.session_state: st.session_state.ean_p = ""
    if "ncm_p" not in st.session_state: st.session_state.ncm_p = ""
    if "cst_p" not in st.session_state: st.session_state.cst_p = ""
    if "medida_p" not in st.session_state: st.session_state.medida_p = ""
    if "peso_p" not in st.session_state: st.session_state.peso_p = ""
    if "campo_sem_p" not in st.session_state: st.session_state.campo_sem_p = ""
    if "desc_p" not in st.session_state: st.session_state.desc_p = ""
    if "historico_precos_p" not in st.session_state: st.session_state.historico_precos_p = []

    if st.session_state.limpar_produto:
        st.session_state.sku_p = ""
        st.session_state.nome_p = ""
        st.session_state.pesquisa_produto = ""
        st.session_state.sku_original_p = ""
        st.session_state.custo_p = "0,00"
        st.session_state.forn_p = ""
        st.session_state.data_ref_p = ""
        st.session_state.ean_p = ""
        st.session_state.ncm_p = ""
        st.session_state.cst_p = ""
        st.session_state.medida_p = ""
        st.session_state.peso_p = ""
        st.session_state.campo_sem_p = ""
        st.session_state.desc_p = ""
        st.session_state.historico_precos_p = []
        
        st.session_state.sku_kit = ""
        st.session_state.nome_kit = ""
        st.session_state.pesquisa_kit = ""
        st.session_state.sku_original_kit = ""
        st.session_state.num_componentes_kit = 1
        for k in list(st.session_state.keys()):
            if k.startswith("kit_sku_") or k.startswith("kit_qtd_") or k.startswith("kit_nome_") or k.startswith("kit_unit_") or k.startswith("kit_tot_"): 
                del st.session_state[k]
        st.session_state.limpar_produto = False

    def salvar_produto_completo(dados, sku_orig=""):
        df = cached_produtos_data()
        if df is None: df = pd.DataFrame(columns=["SKU", "Produto", "Custo", "Fornecedor", "Data de Referência", "EAN", "NCM", "CST", "Medida", "Peso", "Campo Semântico", "Características/Descrição", "Historico_Precos"])
        client = get_sheets_client()
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").worksheet("Produtos")
        
        header = ["SKU", "Produto", "Custo", "Fornecedor", "Data de Referência", "EAN", "NCM", "CST", "Medida", "Peso", "Campo Semântico", "Características/Descrição", "Historico_Precos"]
        
        if sheet.col_count < 13: sheet.add_cols(13 - sheet.col_count)
        if sheet.row_values(1) != header: sheet.update(range_name='A1:M1', values=[header], value_input_option="USER_ENTERED")
            
        valores_formatados = [
            str(dados.get("SKU", "")).strip(), str(dados.get("Produto", "")).strip(), f"{dados.get('Custo', 0):.2f}".replace('.', ','),
            str(dados.get("Fornecedor", "")).strip(), str(dados.get("Data Ref", "")).strip(), str(dados.get("EAN", "")).strip(),
            str(dados.get("NCM", "")).strip(), str(dados.get("CST", "")).strip(), str(dados.get("Medida", "")).strip(),
            str(dados.get("Peso", "")).strip(), str(dados.get("Campo_Semantico", "")).strip(), str(dados.get("Descricao", "")).strip(),
            str(dados.get("Historico_Precos", "")).strip()
        ]
        
        if not df.empty and "SKU" in df.columns:
            df["SKU"] = df["SKU"].astype(str).str.strip()
            sku_novo = str(dados.get("SKU", "")).strip()
            sku_busca = str(sku_orig).strip() if str(sku_orig).strip() else sku_novo
            
            if sku_busca in df["SKU"].values:
                idx = df[df["SKU"] == sku_busca].index[0]
                
                if sku_busca != sku_novo and sku_novo in df["SKU"].values:
                    st.error(f"❌ O SKU '{sku_novo}' já está em uso por outro produto! Escolha um código diferente.")
                    return False
                    
                sheet.update(range_name=f'A{idx+2}:M{idx+2}', values=[valores_formatados], value_input_option="USER_ENTERED")
                cached_produtos_data.clear() 
                return True
                
        if not df.empty and "SKU" in df.columns and str(dados.get("SKU", "")).strip() in df["SKU"].values:
            st.error(f"❌ O SKU '{str(dados.get('SKU', '')).strip()}' já está cadastrado!")
            return False

        sheet.append_row(valores_formatados, value_input_option="USER_ENTERED")
        cached_produtos_data.clear()
        return True

    def excluir_produto_banco(sku_para_excluir):
        client = get_sheets_client()
        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
        
        sheet_prod = doc.worksheet("Produtos")
        df_p = cached_produtos_data()
        if df_p is not None and not df_p.empty and "SKU" in df_p.columns:
            df_p["SKU_Match"] = df_p["SKU"].astype(str).str.strip()
            mask = df_p["SKU_Match"] == str(sku_para_excluir).strip()
            indices = df_p[mask].index.tolist()
            if indices:
                linhas_sheet = [i + 2 for i in indices]
                for linha in sorted(linhas_sheet, reverse=True):
                    sheet_prod.delete_rows(linha)
                    
        try:
            sheet_kits = doc.worksheet("Kits_Composicao")
            df_k = cached_kits_composicao()
            if df_k is not None and not df_k.empty and "SKU do Kit" in df_k.columns:
                df_k["SKU_Match"] = df_k["SKU do Kit"].astype(str).str.strip()
                mask_k = df_k["SKU_Match"] == str(sku_para_excluir).strip()
                indices_k = df_k[mask_k].index.tolist()
                if indices_k:
                    linhas_sheet_k = [i + 2 for i in indices_k]
                    for linha in sorted(linhas_sheet_k, reverse=True):
                        sheet_kits.delete_rows(linha)
        except:
            pass 

        cached_produtos_data.clear()
        cached_kits_composicao.clear()
        return True

    def processar_calculo_custo_produto():
        val = avaliar_expressao_matematica(st.session_state.custo_p)
        if val is not None: st.session_state.custo_p = f"{val:.2f}".replace('.', ',')

    def get_lista_pesquisa_produtos():
        df = cached_produtos_data()
        if df is not None and not df.empty and "Produto" in df.columns and "SKU" in df.columns:
            df_validos = df.dropna(subset=["SKU", "Produto"])
            lista = df_validos["SKU"].astype(str) + " - " + df_validos["Produto"].astype(str)
            return sorted(lista.unique().tolist())
        return []

    def puxar_dados_pesquisa_trigger():
        pesquisa = st.session_state.get("pesquisa_produto", "")
        if pesquisa and " - " in pesquisa:
            sku_busca = pesquisa.split(" - ")[0].strip()
            info_prod = buscar_produto_por_sku(sku_busca)
            if info_prod is not None:
                st.session_state.sku_original_p = str(info_prod.get("SKU", ""))
                st.session_state.sku_p = str(info_prod.get("SKU", ""))
                st.session_state.nome_p = str(info_prod.get("Produto", ""))
                st.session_state.custo_p = formatar_moeda_ui(info_prod.get("Custo", 0))
                st.session_state.forn_p = str(info_prod.get("Fornecedor", ""))
                st.session_state.data_ref_p = converter_data_sheets(info_prod.get("Data de Referência", ""))
                st.session_state.ean_p = str(info_prod.get("EAN", ""))
                st.session_state.ncm_p = str(info_prod.get("NCM", ""))
                st.session_state.cst_p = str(info_prod.get("CST", ""))
                st.session_state.medida_p = str(info_prod.get("Medida", ""))
                st.session_state.peso_p = str(info_prod.get("Peso", ""))
                st.session_state.campo_sem_p = str(info_prod.get("Campo Semântico", ""))
                st.session_state.desc_p = str(info_prod.get("Características/Descrição", ""))
                
                raw_hist = info_prod.get("Historico_Precos", "[]")
                try:
                    st.session_state.historico_precos_p = json.loads(str(raw_hist)) if pd.notna(raw_hist) and str(raw_hist).strip() else []
                except:
                    st.session_state.historico_precos_p = []
        else:
            st.session_state.sku_original_p = ""

    def puxar_dados_pesquisa_kit_trigger():
        pesquisa = st.session_state.get("pesquisa_kit", "")
        if pesquisa and " - " in pesquisa:
            sku_busca = pesquisa.split(" - ")[0].strip()
            
            info_prod = buscar_produto_por_sku(sku_busca)
            if info_prod is not None:
                st.session_state.sku_original_kit = str(info_prod.get("SKU", ""))
                st.session_state.sku_kit = str(info_prod.get("SKU", ""))
                st.session_state.nome_kit = str(info_prod.get("Produto", ""))
            
            df_kits = cached_kits_composicao()
            if df_kits is not None and not df_kits.empty and "SKU do Kit" in df_kits.columns:
                df_kits["SKU do Kit"] = df_kits["SKU do Kit"].astype(str).str.strip()
                componentes = df_kits[df_kits["SKU do Kit"] == sku_busca]
                
                if not componentes.empty:
                    st.session_state.num_componentes_kit = len(componentes)
                    for k in list(st.session_state.keys()):
                        if k.startswith("kit_sku_") or k.startswith("kit_qtd_"):
                            del st.session_state[k]
                            
                    for i, (_, row) in enumerate(componentes.iterrows()):
                        st.session_state[f"kit_sku_{i}"] = str(row.get("SKU Componente", ""))
                        st.session_state[f"kit_qtd_{i}"] = int(converter_valor(row.get("Qtd", 1)))
                else:
                    st.session_state.num_componentes_kit = 1
                    for k in list(st.session_state.keys()):
                        if k.startswith("kit_sku_") or k.startswith("kit_qtd_"):
                            del st.session_state[k]
        else:
            st.session_state.sku_original_kit = ""

    def puxar_dados_kit_por_sku_trigger():
        sku_kit_digitado = st.session_state.get("sku_kit", "").strip()
        if sku_kit_digitado:
            info_prod = buscar_produto_por_sku(sku_kit_digitado)
            if info_prod is not None:
                st.session_state.sku_original_kit = str(info_prod.get("SKU", ""))
                st.session_state.nome_kit = str(info_prod.get("Produto", ""))
            
            df_kits = cached_kits_composicao()
            if df_kits is not None and not df_kits.empty and "SKU do Kit" in df_kits.columns:
                df_kits["SKU do Kit"] = df_kits["SKU do Kit"].astype(str).str.strip()
                componentes = df_kits[df_kits["SKU do Kit"] == sku_kit_digitado]
                
                if not componentes.empty:
                    st.session_state.num_componentes_kit = len(componentes)
                    
                    # Limpa componentes antigos da memória
                    for k in list(st.session_state.keys()):
                        if k.startswith("kit_sku_") or k.startswith("kit_qtd_"):
                            del st.session_state[k]
                            
                    # Carrega os componentes do banco para os campos
                    for i, (_, row) in enumerate(componentes.iterrows()):
                        st.session_state[f"kit_sku_{i}"] = str(row.get("SKU Componente", ""))
                        st.session_state[f"kit_qtd_{i}"] = int(converter_valor(row.get("Qtd", 1)))

    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.2, 4, 0.2])
    with col_conteudo:
        st.title("Cadastro de Mestre de Produtos")
        
        if st.session_state.sucesso_produto:
            st.success(st.session_state.sucesso_produto)
            st.session_state.sucesso_produto = ""
            
        tab_simples, tab_kit, tab_lista = st.tabs(["📦 Produto Simples", "🔗 Kit (Produto Composto)", "📋 Produtos Cadastrados"])
        
        # ABA 1: PRODUTO SIMPLES
        with tab_simples:
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.subheader("🔍 Pesquisar Produto")
            lista_pesquisa = [""] + get_lista_pesquisa_produtos()
            
            c_pesq, c_limp = st.columns([4, 1])
            with c_pesq:
                st.selectbox("Selecione um produto cadastrado para editar os dados:", options=lista_pesquisa, key="pesquisa_produto", on_change=puxar_dados_pesquisa_trigger)
            with c_limp:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🧹 Limpar Campos", key="btn_limpar_p"):
                    st.session_state.limpar_produto = True
                    st.rerun()
            
            st.markdown("---")
            st.subheader("📦 Dados do Produto")
            
            c1, c2 = st.columns([1.5, 3])
            with c1: 
                sku_p = st.text_input("SKU do Produto", key="sku_p")
            with c2: 
                nome_p = st.text_input("Nome do Produto", key="nome_p")
            
            c4, c5, c6 = st.columns(3)
            with c4: ean_produto = st.text_input("EAN do Produto", key="ean_p")
            with c5: ncm_produto = st.text_input("NCM", key="ncm_p")
            with c6: cst_produto = st.text_input("CST", key="cst_p")
            
            c7, c8 = st.columns(2)
            with c7: medida_produto = st.text_input("Medida (Ex: 10x10x10)", key="medida_p")
            with c8: peso_produto = st.text_input("Peso do produto (kg)", key="peso_p")
            
            c9, c10, c11 = st.columns(3)
            with c9: 
                lista_forns = get_lista_fornecedores()
                if not lista_forns: 
                    lista_forns = ["⚠️ Cadastre um fornecedor primeiro no menu lateral"]
                else:
                    lista_forns = [""] + lista_forns  # Adiciona a opção em branco no topo da lista
                    
                forn_atual = st.session_state.get("forn_p", "")
                idx_forn = lista_forns.index(forn_atual) if forn_atual in lista_forns else 0
                nome_fornecedor = st.selectbox("Nome do Fornecedor", options=lista_forns, index=idx_forn, key="forn_p")
            with c10: 
                custo_p_str = st.text_input("Preço de Custo Padrão (R$)", key="custo_p", on_change=processar_calculo_custo_produto, help="Aceita cálculos! Ex: 10+5*2 ou 21,12-2,5%")
                v_custo_p = converter_valor(st.session_state.custo_p)
            with c11: 
                data_ref_preco = st.text_input("Data de Referência do Preço de Custo", placeholder="Ex: 03/07/2026", key="data_ref_p")
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            campo_semantico = st.text_area("Campo Semântico (Palavras-chave SEO para buscas)", key="campo_sem_p", height=100)
            desc_produto = st.text_area("Características, Benefícios e Informações do Produto (Para Anúncios)", key="desc_p", height=400)
            
            st.markdown("---")
            st.subheader("📉 Histórico de Preços")
            
            if st.session_state.historico_precos_p:
                df_hist_precos = pd.DataFrame(st.session_state.historico_precos_p)
                
                # Inverte a ordem do DataFrame para exibir a alteração mais recente primeiro
                df_hist_precos = df_hist_precos.iloc[::-1].reset_index(drop=True)
                
                df_hist_precos["Custo"] = df_hist_precos["Custo"].apply(lambda x: f"R$ {float(x):.2f}".replace('.', ','))
                st.dataframe(
                        df_hist_precos.style.set_properties(**{
                        'background-color': '#F4F6F9',
                        'color': '#1E1E1E',
                        'border-color': '#E5E7EB'
                    }),
                    use_container_width=True,
                    hide_index=True 
                )
            else:
                st.info("Nenhum histórico de preço registado para este produto.")
                
            st.markdown("---")
            
            col_btn1, col_btn2, col_vazio = st.columns([2, 2, 6])
            with col_btn1:
                btn_salvar = st.button("💾 Gravar Ficha do Produto", key="btn_prod_simples")
            with col_btn2:
                btn_excluir = st.button("🗑️ Excluir Produto", key="btn_excluir_simples")
                
            if btn_salvar:
                if sku_p.strip() and nome_p.strip() and v_custo_p > 0:
                    
                    hist_list = st.session_state.get("historico_precos_p", []).copy()
                    novo_forn = nome_fornecedor if "⚠️" not in nome_fornecedor else ""
                    
                    if not hist_list:
                        hist_list.append({"Data": data_ref_preco, "Fornecedor": novo_forn, "Custo": v_custo_p, "Variação": "0,00%"})
                    else:
                        last_record = hist_list[-1]
                        if last_record.get("Custo") != v_custo_p or last_record.get("Fornecedor") != novo_forn or last_record.get("Data") != data_ref_preco:
                            old_custo = float(last_record.get("Custo", 0))
                            if old_custo > 0:
                                var_pct = ((v_custo_p - old_custo) / old_custo) * 100
                                var_str = f"🔺 +{var_pct:.2f}%" if var_pct > 0 else (f"🔻 {var_pct:.2f}%" if var_pct < 0 else "0,00%")
                            else:
                                var_str = "0,00%"
                            hist_list.append({"Data": data_ref_preco, "Fornecedor": novo_forn, "Custo": v_custo_p, "Variação": var_str.replace('.', ',')})
                    
                    historico_json = json.dumps(hist_list)
                    
                    dados_prod = {
                        "SKU": sku_p, "Produto": nome_p, "Custo": v_custo_p,
                        "Fornecedor": novo_forn, 
                        "Data Ref": data_ref_preco, "EAN": ean_produto, "NCM": ncm_produto, 
                        "CST": cst_produto, "Medida": medida_produto, "Peso": peso_produto,
                        "Campo_Semantico": campo_semantico,
                        "Descricao": desc_produto,
                        "Historico_Precos": historico_json
                    }
                    try:
                        sku_original = st.session_state.get("sku_original_p", "")
                        if salvar_produto_completo(dados_prod, sku_orig=sku_original):
                            st.session_state.sucesso_produto = f"✅ Produto '{sku_p}' registrado/atualizado com sucesso!"
                            st.session_state.limpar_produto = True
                            st.rerun() 
                    except Exception as e: st.error(f"❌ Erro ao gravar produto: {e}")
                else: st.error("❌ Por favor, preencha os campos obrigatórios (SKU, Nome, Preço de Custo).")
                
            if btn_excluir:
                sku_original = st.session_state.get("sku_original_p", "")
                sku_alvo = sku_original if sku_original else sku_p
                if sku_alvo.strip():
                    try:
                        excluir_produto_banco(sku_alvo)
                        st.session_state.sucesso_produto = f"✅ Produto '{sku_alvo}' excluído com sucesso!"
                        st.session_state.limpar_produto = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao excluir produto: {e}")
                else:
                    st.error("❌ Selecione ou preencha um SKU válido para excluir.")

        # ABA 2: KIT (PRODUTO COMPOSTO)
        with tab_kit:
            st.markdown("<br>", unsafe_allow_html=True)
            st.write("Crie ou edite um produto composto.")
            
            st.subheader("🔍 Pesquisar Kit")
            lista_pesquisa_kit = [""] + get_lista_pesquisa_produtos()
            
            c_pesq_kit, c_limp_kit = st.columns([4, 1])
            with c_pesq_kit:
                st.selectbox("Selecione um kit cadastrado para editar os dados:", options=lista_pesquisa_kit, key="pesquisa_kit", on_change=puxar_dados_pesquisa_kit_trigger)
            with c_limp_kit:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🧹 Limpar Campos", key="btn_limpar_kit"):
                    st.session_state.limpar_produto = True
                    st.rerun()
            
            st.markdown("---")
            st.subheader("📦 Dados do Kit")
            
            c1, c2 = st.columns([1, 2])
            with c1: sku_kit = st.text_input("SKU do Kit", key="sku_kit", on_change=puxar_dados_kit_por_sku_trigger)
            with c2: nome_kit = st.text_input("Nome do Kit", key="nome_kit")
            
            st.markdown("#### Componentes do Kit")
            custo_total_kit = 0.0
            
            c_sku, c_nome, c_qtd, c_unit, c_tot = st.columns([1.5, 2.5, 1, 1.2, 1.2])
            c_sku.write("**SKU Componente**")
            c_nome.write("**Nome do Produto**")
            c_qtd.write("**Qtd**")
            c_unit.write("**Valor Unit.**")
            c_tot.write("**Valor Total**")
            
            for i in range(st.session_state.num_componentes_kit):
                c_sku, c_nome, c_qtd, c_unit, c_tot = st.columns([1.5, 2.5, 1, 1.2, 1.2])
                with c_sku:
                    sku_comp = st.text_input(f"sku_{i}", key=f"kit_sku_{i}", label_visibility="collapsed")
                
                with c_qtd:
                    qtd_comp = st.number_input(f"qtd_{i}", min_value=1, value=1, step=1, key=f"kit_qtd_{i}", label_visibility="collapsed")
                
                nome_comp = ""
                custo_unit_comp = 0.0
                
                if sku_comp.strip():
                    prod_data = buscar_produto_por_sku(sku_comp.strip())
                    if prod_data is not None:
                        nome_comp = str(prod_data.get("Produto", ""))
                        custo_unit_comp = converter_valor(prod_data.get("Custo", 0))
                    else:
                        nome_comp = "⚠️ Produto não encontrado"
                
                total_comp = custo_unit_comp * qtd_comp
                custo_total_kit += total_comp
                
                st.session_state[f"kit_nome_comp_{i}"] = nome_comp
                st.session_state[f"kit_unit_comp_{i}"] = f"R$ {custo_unit_comp:.2f}".replace('.', ',')
                st.session_state[f"kit_tot_comp_{i}"] = f"R$ {total_comp:.2f}".replace('.', ',')
                        
                with c_nome:
                    st.text_input(f"nome_{i}", disabled=True, key=f"kit_nome_comp_{i}", label_visibility="collapsed")
                with c_unit:
                    st.text_input(f"unit_{i}", disabled=True, key=f"kit_unit_comp_{i}", label_visibility="collapsed")
                with c_tot:
                    st.text_input(f"tot_{i}", disabled=True, key=f"kit_tot_comp_{i}", label_visibility="collapsed")
            
            if st.button("➕ Adicionar outro produto ao kit"):
                st.session_state.num_componentes_kit += 1
                st.rerun()
                
            st.markdown("---")
            st.metric("Custo Total do Kit", f"R$ {custo_total_kit:.2f}".replace('.', ','))
            
            col_btn1_k, col_btn2_k, col_vazio_k = st.columns([2, 2, 6])
            with col_btn1_k:
                btn_salvar_kit = st.button("💾 Gravar Kit", key="btn_salvar_kit")
            with col_btn2_k:
                btn_excluir_kit = st.button("🗑️ Excluir Kit", key="btn_excluir_kit")
                
            if btn_salvar_kit:
                if sku_kit.strip() and nome_kit.strip() and custo_total_kit > 0:
                    dados_kit_prod = {
                        "SKU": sku_kit.strip(), "Produto": nome_kit.strip(), "Custo": custo_total_kit,
                        "Fornecedor": "", "Data Ref": "", "EAN": "", "NCM": "", "CST": "", "Medida": "", "Peso": "", "Campo_Semantico": "", "Descricao": "", "Historico_Precos": "[]"
                    }
                    try:
                        sku_orig_kit = st.session_state.get("sku_original_kit", "")
                        
                        if salvar_produto_completo(dados_kit_prod, sku_orig=sku_orig_kit):
                            client = get_sheets_client()
                            doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                            try: sheet_kits = doc.worksheet("Kits_Composicao")
                            except:
                                sheet_kits = doc.add_worksheet(title="Kits_Composicao", rows="1000", cols="6")
                                sheet_kits.append_row(["SKU do Kit", "Nome do Kit", "SKU Componente", "Qtd", "Custo Unitário", "Custo Total"], value_input_option="USER_ENTERED")
                            
                            df_k = cached_kits_composicao()
                            if df_k is not None and not df_k.empty and "SKU do Kit" in df_k.columns:
                                df_k["SKU_Match"] = df_k["SKU do Kit"].astype(str).str.strip()
                                sku_para_deletar = sku_orig_kit if sku_orig_kit else sku_kit.strip()
                                mask = df_k["SKU_Match"] == sku_para_deletar
                                indices_para_deletar = df_k[mask].index.tolist()
                                if indices_para_deletar:
                                    linhas_sheet = [idx + 2 for idx in indices_para_deletar]
                                    for linha in sorted(linhas_sheet, reverse=True):
                                        sheet_kits.delete_rows(linha)

                            linhas_composicao = []
                            for i in range(st.session_state.num_componentes_kit):
                                sku_c = st.session_state.get(f"kit_sku_{i}", "").strip()
                                qtd_c = st.session_state.get(f"kit_qtd_{i}", 1)
                                if sku_c:
                                    prod_data = buscar_produto_por_sku(sku_c)
                                    if prod_data is not None:
                                        unit_c = converter_valor(prod_data.get("Custo", 0))
                                        tot_c = unit_c * qtd_c
                                        linhas_composicao.append([sku_kit.strip(), nome_kit.strip(), sku_c, qtd_c, f"{unit_c:.2f}".replace('.', ','), f"{tot_c:.2f}".replace('.', ',')])
                            
                            if linhas_composicao: sheet_kits.append_rows(linhas_composicao, value_input_option="USER_ENTERED")
                            
                            cached_kits_composicao.clear()
                            st.session_state.sucesso_produto = f"✅ Kit '{sku_kit}' registado/atualizado com sucesso no banco de Produtos!"
                            st.session_state.limpar_produto = True
                            st.rerun() 
                    except Exception as e: st.error(f"❌ Erro ao gravar kit: {e}")
                else:
                    st.error("❌ Preencha o SKU do Kit, Nome, e garanta que digitou pelo menos 1 componente válido.")
                    
            if btn_excluir_kit:
                sku_orig_kit = st.session_state.get("sku_original_kit", "")
                sku_alvo_kit = sku_orig_kit if sku_orig_kit else sku_kit
                if sku_alvo_kit.strip():
                    try:
                        excluir_produto_banco(sku_alvo_kit)
                        st.session_state.sucesso_produto = f"✅ Kit '{sku_alvo_kit}' excluído com sucesso!"
                        st.session_state.limpar_produto = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao excluir kit: {e}")
                else:
                    st.error("❌ Selecione ou preencha um SKU válido para excluir.")

        # ABA 3: PRODUTOS CADASTRADOS (NOVA ABA)
        with tab_lista:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📋 Lista de Produtos Cadastrados")
            
            df_prods = cached_produtos_data()
            if df_prods is not None and not df_prods.empty:
                df_prods_sorted = df_prods.sort_values(by="SKU", ascending=True).reset_index(drop=True)
                
                st.dataframe(
                    df_prods_sorted.style.set_properties(**{
                        'background-color': '#F4F6F9',
                        'color': '#1E1E1E',
                        'border-color': '#E5E7EB'
                    }), 
                    use_container_width=True,
                    hide_index=True 
                )
            else:
                st.info("Nenhum produto cadastrado até o momento.")

# =====================================================================
# MÓDULO 3: DESPESAS A PAGAR 
# =====================================================================
elif menu_selecionado == "Despesas a pagar":
    
    if "limpar_despesas" not in st.session_state: st.session_state.limpar_despesas = False
    if "sucesso_despesas" not in st.session_state: st.session_state.sucesso_despesas = ""
    if "sucesso_pagamento" not in st.session_state: st.session_state.sucesso_pagamento = ""
    if "sucesso_historico" not in st.session_state: st.session_state.sucesso_historico = ""
    if "num_parcelas_p" not in st.session_state: st.session_state.num_parcelas_p = 1
    if "exibir_grid_despesas" not in st.session_state: st.session_state.exibir_grid_despesas = False
    if "valor_total_despesa" not in st.session_state: st.session_state.valor_total_despesa = "0,00"
    if "nota_existente" not in st.session_state: st.session_state.nota_existente = False
    if "pagando_id" not in st.session_state: st.session_state.pagando_id = None

    if st.session_state.limpar_despesas:
        st.session_state.forn_p = ""
        st.session_state.nf_p = ""
        st.session_state.valor_total_despesa = "0,00"
        st.session_state.num_parcelas_p = 1
        st.session_state.exibir_grid_despesas = False
        st.session_state.nota_existente = False
        st.session_state.pagando_id = None
        for k in list(st.session_state.keys()):
            if k.startswith("d_val_") or k.startswith("d_venc_"): del st.session_state[k]
        st.session_state.limpar_despesas = False

    def carregar_repositorio_despesas():
        try:
            client = get_sheets_client()
            doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
            try: sheet = doc.worksheet("Despesas")
            except:
                sheet = doc.add_worksheet(title="Despesas", rows="1000", cols="9")
                sheet.append_row(["Nome do Fornecedor", "Número da Nota Fiscal", "Valor Total da Nota", "Parcela", "Valor da Parcela", "Data de Vencimento", "Data de Registro", "Status", "Forma de Pagamento"], value_input_option="USER_ENTERED")
            data = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
            
            df = pd.DataFrame(data) if data else pd.DataFrame(columns=["Nome do Fornecedor", "Número da Nota Fiscal", "Valor Total da Nota", "Parcela", "Valor da Parcela", "Data de Vencimento", "Data de Registro", "Status", "Forma de Pagamento"])
            
            if not df.empty and "Parcela" in df.columns:
                df["Parcela"] = df["Parcela"].apply(corrigir_parcela_data)
                
            return df
        except: 
            return pd.DataFrame(columns=["Nome do Fornecedor", "Número da Nota Fiscal", "Valor Total da Nota", "Parcela", "Valor da Parcela", "Data de Vencimento", "Data de Registro", "Status", "Forma de Pagamento"])

    def salvar_despesas_no_repositorio(lista_parcelas, fornecedor, num_nf):
        df = carregar_repositorio_despesas()
        client = get_sheets_client()
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").worksheet("Despesas")
        
        if sheet.col_count < 9: sheet.add_cols(9 - sheet.col_count)
        if len(sheet.row_values(1)) < 8 or sheet.row_values(1)[7] != "Status": sheet.update_cell(1, 8, "Status")
        if len(sheet.row_values(1)) < 9 or sheet.row_values(1)[8] != "Forma de Pagamento": sheet.update_cell(1, 9, "Forma de Pagamento")

        if not df.empty:
            df["Fornecedor_Match"] = df["Nome do Fornecedor"].astype(str).str.strip().str.upper()
            df["NF_Match"] = df["Número da Nota Fiscal"].apply(normalizar_nf)
            
            forn_str = str(fornecedor).strip().upper()
            nf_str = normalizar_nf(num_nf)
            mask = (df["Fornecedor_Match"] == forn_str) & (df["NF_Match"] == nf_str)
            indices_para_deletar = df[mask].index.tolist()
            
            linhas_sheet = [i + 2 for i in indices_para_deletar]
            for linha in sorted(linhas_sheet, reverse=True):
                sheet.delete_rows(linha) 
                
        valores_inserir = []
        for dados in lista_parcelas:
            valores_formatados = [f"{v:.2f}".replace('.', ',') if isinstance(v, float) else str(v) for v in dados.values()]
            valores_inserir.append(valores_formatados)
            
        if valores_inserir:
            sheet.append_rows(valores_inserir, value_input_option="USER_ENTERED")

    def marcar_como_pago(forn, nf, parc, forma_pag):
        df = carregar_repositorio_despesas()
        if not df.empty:
            df["F_Match"] = df["Nome do Fornecedor"].astype(str).str.strip().str.upper()
            df["NF_Match"] = df["Número da Nota Fiscal"].apply(normalizar_nf)
            df["P_Match"] = df["Parcela"].astype(str).str.strip()
            
            mask = (df["F_Match"] == str(forn).strip().upper()) & (df["NF_Match"] == normalizar_nf(nf)) & (df["P_Match"] == str(parc).strip())
            indices = df[mask].index.tolist()
            
            if indices:
                linha_real = indices[0] + 2 
                client = get_sheets_client()
                sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").worksheet("Despesas")
                
                if sheet.col_count < 9: sheet.add_cols(9 - sheet.col_count)
                row_1 = sheet.row_values(1)
                if len(row_1) < 8 or row_1[7] != "Status": sheet.update_cell(1, 8, "Status")
                if len(row_1) < 9 or row_1[8] != "Forma de Pagamento": sheet.update_cell(1, 9, "Forma de Pagamento")
                
                sheet.update_cell(linha_real, 8, "Pago")
                sheet.update_cell(linha_real, 9, forma_pag)
                return True
        return False
        
    def atualizar_forma_pagamento(forn, nf, parc, select_key):
        nova_forma = st.session_state[select_key]
        if nova_forma == "-":
            nova_forma = "" 
            
        df = carregar_repositorio_despesas()
        if not df.empty:
            df["F_Match"] = df["Nome do Fornecedor"].astype(str).str.strip().str.upper()
            df["NF_Match"] = df["Número da Nota Fiscal"].apply(normalizar_nf)
            df["P_Match"] = df["Parcela"].astype(str).str.strip()
            
            mask = (df["F_Match"] == str(forn).strip().upper()) & (df["NF_Match"] == normalizar_nf(nf)) & (df["P_Match"] == str(parc).strip())
            indices = df[mask].index.tolist()
            
            if indices:
                linha_real = indices[0] + 2 
                client = get_sheets_client()
                sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").worksheet("Despesas")
                if sheet.col_count < 9: sheet.add_cols(9 - sheet.col_count)
                sheet.update_cell(linha_real, 9, nova_forma)
                st.session_state.sucesso_historico = f"✅ Forma de pagamento atualizada para '{nova_forma}' com sucesso!"

    def checar_nota_cadastrada():
        f = st.session_state.get("forn_p", "").strip()
        nf = st.session_state.get("nf_p", "").strip()
        
        if f and nf:
            df_desp = carregar_repositorio_despesas()
            if not df_desp.empty:
                df_desp["F_Match"] = df_desp["Nome do Fornecedor"].astype(str).str.strip().str.upper()
                df_desp["NF_Match"] = df_desp["Número da Nota Fiscal"].apply(normalizar_nf)
                
                f_upper = f.upper()
                nf_norm = normalizar_nf(nf)
                df_enc = df_desp[(df_desp["F_Match"] == f_upper) & (df_desp["NF_Match"] == nf_norm)]
                
                if not df_enc.empty:
                    st.session_state.nota_existente = True
                    st.session_state.valor_total_despesa = formatar_moeda_ui(df_enc.iloc[0]["Valor Total da Nota"])
                    st.session_state.num_parcelas_p = len(df_enc)
                    st.session_state.exibir_grid_despesas = True
                    
                    for k in list(st.session_state.keys()):
                        if k.startswith("d_val_") or k.startswith("d_venc_"): del st.session_state[k]
                        
                    for i, (_, row) in enumerate(df_enc.iterrows()):
                        st.session_state[f"d_val_{i}"] = formatar_moeda_ui(row["Valor da Parcela"])
                        st.session_state[f"d_venc_{i}"] = converter_data_sheets(row["Data de Vencimento"])
                else:
                    st.session_state.nota_existente = False
                    st.session_state.exibir_grid_despesas = False
            else:
                st.session_state.nota_existente = False
                st.session_state.exibir_grid_despesas = False
        else:
            st.session_state.nota_existente = False
            st.session_state.exibir_grid_despesas = False

    def processar_calculo_total_despesa():
        texto_atual = str(st.session_state.valor_total_despesa)
        if texto_atual.startswith("="): st.session_state.valor_total_despesa = formatar_moeda_ui(texto_atual.replace("=", ""))

    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.2, 4, 0.2])
    with col_conteudo:
        st.title("Controle de Despesas a Pagar")
        
        tab_lista, tab_lancamento, tab_historico = st.tabs(["📋 Títulos a Pagar (Pendentes)", "➕ Novo Lançamento / Edição", "📂 Histórico de Contas"])
        
        df_todas_geral = carregar_repositorio_despesas()

        with tab_lista:
            if st.session_state.sucesso_pagamento:
                st.success(st.session_state.sucesso_pagamento)
                st.session_state.sucesso_pagamento = ""

            st.write("Abaixo estão todas as contas pendentes organizadas pela data de vencimento.")
            
            if not df_todas_geral.empty:
                if "Status" not in df_todas_geral.columns: df_todas_geral["Status"] = "Pendente"
                df_pendentes = df_todas_geral[df_todas_geral["Status"] != "Pago"].copy()
                
                if not df_pendentes.empty:
                    df_pendentes["Venc_Fmt"] = df_pendentes["Data de Vencimento"].apply(converter_data_sheets)
                    df_pendentes["Data_Sort"] = pd.to_datetime(df_pendentes["Venc_Fmt"], format="%d/%m/%Y", errors="coerce")
                    df_pendentes = df_pendentes.sort_values(by="Data_Sort", ascending=True)
                    
                    st.markdown("---")
                    c1, c2, c3, c4, c5, c6 = st.columns([2.5, 2, 1, 1.5, 2, 3])
                    c1.write("**Fornecedor**")
                    c2.write("**Nota Fiscal**")
                    c3.write("**Parcela**")
                    c4.write("**Valor (R$)**")
                    c5.write("**Vencimento**")
                    c6.write("**Ação**")
                    st.markdown("---")
                    
                    for idx, row in df_pendentes.iterrows():
                        c1, c2, c3, c4, c5, c6 = st.columns([2.5, 2, 1, 1.5, 2, 3])
                        c1.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row['Nome do Fornecedor'])}</div>", unsafe_allow_html=True)
                        c2.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row['Número da Nota Fiscal'])}</div>", unsafe_allow_html=True)
                        c3.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row['Parcela'])}</div>", unsafe_allow_html=True)
                        val_fmt = f"R$ {float(converter_valor(row['Valor da Parcela'])):.2f}".replace('.', ',')
                        c4.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{val_fmt}</div>", unsafe_allow_html=True)
                        c5.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row['Venc_Fmt'])}</div>", unsafe_allow_html=True)
                        
                        btn_key = f"pagar_{idx}_{row['Número da Nota Fiscal']}_{row['Parcela']}"
                        
                        if st.session_state.pagando_id == btn_key:
                            forma_escolhida = c6.selectbox("Forma de Pagamento", ["Pix", "Boleto", "Cartão"], key=f"sel_{btn_key}", label_visibility="collapsed")
                            
                            col_conf, col_canc = c6.columns(2)
                            if col_conf.button("✔ Conf.", key=f"conf_{btn_key}", help="Confirmar Pagamento"):
                                if marcar_como_pago(row["Nome do Fornecedor"], row["Número da Nota Fiscal"], row["Parcela"], forma_escolhida):
                                    st.session_state.sucesso_pagamento = f"✅ Pagamento da parcela {row['Parcela']} via {forma_escolhida} confirmado!"
                                    st.session_state.pagando_id = None
                                    st.rerun()
                                else:
                                    st.error("Erro ao baixar.")
                                    
                            if col_canc.button("✖ Canc.", key=f"canc_{btn_key}", help="Cancelar Ação"):
                                st.session_state.pagando_id = None
                                st.rerun()
                        else:
                            if c6.button("✅ Pagar", key=btn_key):
                                st.session_state.pagando_id = btn_key
                                st.rerun()
                else:
                    st.info("🎉 Fantástico! Não há despesas pendentes no momento.")
            else:
                st.info("Nenhuma despesa lançada ainda.")

        with tab_lancamento:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.session_state.sucesso_despesas:
                st.success(st.session_state.sucesso_despesas)
                st.session_state.sucesso_despesas = ""
            
            c_forn, c_nf = st.columns(2)
            
            lista_forns_despesa = [""] + get_lista_fornecedores()
            forn_atual_desp = st.session_state.get("forn_p", "")
            idx_forn_desp = lista_forns_despesa.index(forn_atual_desp) if forn_atual_desp in lista_forns_despesa else 0
            fornecedor = c_forn.selectbox("Nome do Fornecedor", options=lista_forns_despesa, index=idx_forn_desp, key="forn_p", on_change=checar_nota_cadastrada)
            
            num_nf = c_nf.text_input("Número da Nota Fiscal", key="nf_p", on_change=checar_nota_cadastrada)
            
            if fornecedor.strip() and num_nf.strip():
                if st.session_state.nota_existente:
                    st.info("ℹ️ Esta nota fiscal já foi lançada no sistema! As informações e parcelas foram recuperadas abaixo.")
                else:
                    st.success("✨ Novo lançamento. Siga para gerar parcelas.")

            c_val, c_parc = st.columns(2)
            with c_val: st.text_input("Valor Total da Nota (R$)", key="valor_total_despesa", on_change=processar_calculo_total_despesa)
            with c_parc: num_parcelas = st.number_input("Número de Parcelas", min_value=1, max_value=72, step=1, key="num_parcelas_p")
            
            v_total_nota = converter_valor(st.session_state.valor_total_despesa)
            st.markdown("<br>", unsafe_allow_html=True)
            
            if not st.session_state.nota_existente:
                if st.button("🔄 Gerar Parcelas"):
                    if fornecedor.strip() and num_nf.strip() and v_total_nota > 0:
                        st.session_state.exibir_grid_despesas = True
                        for k in list(st.session_state.keys()):
                            if k.startswith("d_val_") or k.startswith("d_venc_"): del st.session_state[k]
                    else: st.error("❌ Preencha todos os dados obrigatórios e certifique-se de que o valor é maior que zero.")
            else:
                if st.button("🔄 Recalcular / Alterar Parcelas"):
                    if v_total_nota > 0:
                        st.session_state.exibir_grid_despesas = True
                        for k in list(st.session_state.keys()):
                            if k.startswith("d_val_") or k.startswith("d_venc_"): del st.session_state[k]
                    else: st.error("❌ Valor total inválido.")
                
            if st.session_state.exibir_grid_despesas:
                st.markdown("---")
                val_calculado_parcela = v_total_nota / num_parcelas
                lista_dados_salvamento = []
                
                for i in range(int(num_parcelas)):
                    col_label, col_v_parc, col_venc = st.columns([1.5, 2.5, 2.5])
                    with col_label: st.markdown(f"<p style='margin-top:35px;'><b>Parcela {i+1} de {int(num_parcelas)}</b></p>", unsafe_allow_html=True)
                    with col_v_parc:
                        k_val = f"d_val_{i}"
                        if k_val not in st.session_state: st.session_state[k_val] = f"{val_calculado_parcela:.2f}".replace('.', ',')
                        val_digitado = st.text_input(f"Valor da Parcela {i+1} (R$)", key=k_val)
                    with col_venc:
                        k_venc = f"d_venc_{i}"
                        if k_venc not in st.session_state: st.session_state[k_venc] = datetime.now().strftime("%d/%m/%Y")
                        venc_digitado = st.text_input(f"Vencimento {i+1} (DD/MM/AAAA)", key=k_venc)
                    
                    lista_dados_salvamento.append({
                        "Fornecedor": fornecedor.strip(), "NF": num_nf.strip(), "Total": v_total_nota,
                        "Parcela": f"{i+1} de {int(num_parcelas)}", "Valor_Parc": val_digitado,
                        "Vencimento": venc_digitado, "Registro": datetime.now().strftime("%d/%m/%Y"),
                        "Status": "Pendente",
                        "Forma de Pagamento": "" 
                    })
                    
                st.markdown("---")
                if st.button("💾 Salvar Despesas"):
                    try:
                        for item in lista_dados_salvamento: item["Valor_Parc"] = converter_valor(item["Valor_Parc"])
                        salvar_despesas_no_repositorio(lista_dados_salvamento, fornecedor, num_nf)
                        st.session_state.sucesso_despesas = "✅ Despesas salvas com sucesso!"
                        st.session_state.limpar_despesas = True
                        st.rerun() 
                    except Exception as e: st.error(f"❌ Erro ao salvar: {e}")

        with tab_historico:
            if st.session_state.sucesso_historico:
                st.success(st.session_state.sucesso_historico)
                st.session_state.sucesso_historico = ""

            st.write("Abaixo estão todas as contas já pagas e o seu respetivo histórico de liquidação.")
            
            if not df_todas_geral.empty and "Status" in df_todas_geral.columns:
                df_pagas = df_todas_geral[df_todas_geral["Status"] == "Pago"].copy()
                
                if not df_pagas.empty:
                    df_pagas["Venc_Fmt"] = df_pagas["Data de Vencimento"].apply(converter_data_sheets)
                    df_pagas["Data_Sort"] = pd.to_datetime(df_pagas["Venc_Fmt"], format="%d/%m/%Y", errors="coerce")
                    df_pagas = df_pagas.sort_values(by="Data_Sort", ascending=False)
                    
                    st.markdown("---")
                    c1, c2, c3, c4, c5, c6 = st.columns([2.5, 2, 1, 1.5, 2, 2])
                    c1.write("**Fornecedor**")
                    c2.write("**Nota Fiscal**")
                    c3.write("**Parcela**")
                    c4.write("**Valor (R$)**")
                    c5.write("**Vencimento**")
                    c6.write("**Forma Pag.**")
                    st.markdown("---")
                    
                    for idx, row in df_pagas.iterrows():
                        c1, c2, c3, c4, c5, c6 = st.columns([2.5, 2, 1, 1.5, 2, 2])
                        c1.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row['Nome do Fornecedor'])}</div>", unsafe_allow_html=True)
                        c2.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row['Número da Nota Fiscal'])}</div>", unsafe_allow_html=True)
                        c3.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row['Parcela'])}</div>", unsafe_allow_html=True)
                        val_fmt = f"R$ {float(converter_valor(row['Valor da Parcela'])):.2f}".replace('.', ',')
                        c4.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{val_fmt}</div>", unsafe_allow_html=True)
                        c5.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row['Venc_Fmt'])}</div>", unsafe_allow_html=True)
                        
                        forma_atual = str(row.get("Forma de Pagamento", "")).strip()
                        if not forma_atual or forma_atual == "nan" or forma_atual == "-":
                            forma_atual = "-"
                            
                        opcoes_pag = ["-", "Pix", "Boleto", "Cartão"]
                        if forma_atual not in opcoes_pag:
                            opcoes_pag.append(forma_atual)
                            
                        idx_forma = opcoes_pag.index(forma_atual)
                        select_key = f"edit_pag_{idx}_{row['Número da Nota Fiscal']}_{row['Parcela']}"
                        
                        c6.selectbox(
                            "Forma Pag.", 
                            options=opcoes_pag, 
                            index=idx_forma, 
                            key=select_key, 
                            label_visibility="collapsed",
                            on_change=atualizar_forma_pagamento,
                            args=(row["Nome do Fornecedor"], row["Número da Nota Fiscal"], row["Parcela"], select_key)
                        )
                else:
                    st.info("Nenhuma conta foi marcada como paga até o momento.")
            else:
                st.info("Nenhuma conta paga encontrada no histórico.")

# =====================================================================
# MÓDULO 4: CURVA ABC MELI
# =====================================================================
elif menu_selecionado == "Curva ABC Meli":
    st.title("Análise de Curva ABC")
    arquivo_excel = st.file_uploader("Upload planilha Mercado Livre", type=["xlsx", "xls", "csv"])
    if arquivo_excel is not None:
        try:
            if arquivo_excel.name.endswith('.csv'): df_bruto = pd.read_csv(arquivo_excel, header=None, dtype=str)
            else:
                try: df_bruto = pd.read_excel(arquivo_excel, sheet_name="Relatório", header=None)
                except: df_bruto = pd.read_excel(arquivo_excel, header=None)
            
            linha_cabecalho = next(i for i in range(min(20, len(df_bruto))) if "ID do anúncio" in [str(val).strip() for val in df_bruto.iloc[i].tolist()] or "Vendas brutas (BRL)" in [str(val).strip() for val in df_bruto.iloc[i].tolist()])
            df = df_bruto.iloc[linha_cabecalho+1:].copy()
            df.columns = [str(col).strip() for col in df_bruto.iloc[linha_cabecalho].tolist()]
            
            def limpar_moeda(valor):
                if pd.isna(valor): return 0.0
                v_str = str(valor).strip().replace('.', '').replace(',', '.')
                try: return float(re.sub(r'[^\d\.\-]', '', v_str))
                except: return 0.0
            
            df["Vendas brutas (BRL)"] = df["Vendas brutas (BRL)"].apply(limpar_moeda)
            df_agrupado = df.groupby("ID do anúncio").agg({"Vendas brutas (BRL)": "sum"}).reset_index()
            df_vendas = df_agrupado[df_agrupado["Vendas brutas (BRL)"] > 0].sort_values(by="Vendas brutas (BRL)", ascending=False).reset_index(drop=True)
            
            total_vendas = df_vendas["Vendas brutas (BRL)"].sum()
            df_vendas["% do Total"] = (df_vendas["Vendas brutas (BRL)"] / total_vendas) * 100
            df_vendas["Curva"] = df_vendas["% do Total"].cumsum().apply(lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C'))
            
            st.metric("Total Faturado", f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.dataframe(
                df_vendas.style.set_properties(**{
                    'background-color': '#F4F6F9',
                    'color': '#1E1E1E',
                    'border-color': '#E5E7EB'
                }),
                use_container_width=True,
                hide_index=True 
            )
        except Exception as e: st.error(f"Erro: {e}")

# =====================================================================
# MÓDULO 5: PRODUCT ADS
# =====================================================================
elif menu_selecionado == "Product ADS":
    if "campanha_analise_selecionada" not in st.session_state:
        st.session_state.campanha_analise_selecionada = ""
    if "aba_ativa_ads" not in st.session_state:
        st.session_state.aba_ativa_ads = "🎯 Cadastro e Lista de Campanhas"

    def ativar_analise(nome):
        st.session_state.campanha_analise_selecionada = nome
        st.session_state.aba_ativa_ads = "📊 Análise de Campanha"

    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.2, 4, 0.2])
    with col_conteudo:
        st.title("📈 Product ADS")
        st.markdown("Crie e faça a gestão das suas campanhas de publicidade.")

        aba_selecionada = st.radio(
            "Navegação ADS", 
            ["🎯 Cadastro e Lista de Campanhas", "📊 Análise de Campanha"], 
            horizontal=True, 
            label_visibility="collapsed",
            key="aba_ativa_ads"
        )

        if aba_selecionada == "🎯 Cadastro e Lista de Campanhas":
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Nova Campanha ADS")

            c1, c2, c_data = st.columns([2, 1, 1])
            with c1:
                nome_campanha = st.text_input("Nome da Campanha")
            with c2:
                roas_objetivo = st.number_input("ROAS Objetivo", min_value=0.0, value=5.0, step=0.1)
            with c_data:
                data_criacao = st.text_input("Data da Criação", value=datetime.now().strftime("%d/%m/%Y"))

            c3, c4 = st.columns([1, 2])
            with c3:
                orcamento_str = st.text_input("Orçamento Diário (R$)", value="0,00", key="orcamento_ads")
                orcamento = converter_valor(orcamento_str)

            with c4:
                lista_anuncios = get_lista_anuncios()
                if not lista_anuncios:
                    st.info("⚠️ Nenhum anúncio cadastrado no sistema.")
                anuncios_selecionados = st.multiselect(
                    "Anúncios inseridos na campanha",
                    options=lista_anuncios,
                    placeholder="Selecione um ou mais anúncios"
                )

            st.markdown("---")
            if st.button("💾 Salvar Campanha"):
                if nome_campanha.strip() and orcamento > 0:
                    try:
                        client = get_sheets_client()
                        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                        try:
                            sheet_ads = doc.worksheet("Campanhas_ADS")
                            if sheet_ads.cell(1, 5).value == "Data de Registro":
                                sheet_ads.update_cell(1, 5, "Data da Criação")
                        except:
                            sheet_ads = doc.add_worksheet(title="Campanhas_ADS", rows="1000", cols="5")
                            sheet_ads.append_row(["Nome da Campanha", "ROAS Objetivo", "Orçamento Diário", "Anúncios", "Data da Criação"])

                        df_ads = cached_campanhas_ads()
                        anuncios_json = json.dumps(anuncios_selecionados)

                        valores = [
                            nome_campanha.strip(),
                            f"{roas_objetivo:.2f}".replace('.', ','),
                            f"{orcamento:.2f}".replace('.', ','),
                            anuncios_json,
                            data_criacao
                        ]

                        if df_ads is not None and not df_ads.empty and "Nome da Campanha" in df_ads.columns:
                            df_ads["Nome da Campanha"] = df_ads["Nome da Campanha"].astype(str).str.strip()
                            if nome_campanha.strip() in df_ads["Nome da Campanha"].values:
                                idx = df_ads[df_ads["Nome da Campanha"] == nome_campanha.strip()].index[0]
                                sheet_ads.update(range_name=f'A{idx+2}:E{idx+2}', values=[valores], value_input_option="USER_ENTERED")
                                cached_campanhas_ads.clear()
                                st.success(f"✅ Campanha '{nome_campanha}' atualizada com sucesso!")
                                st.rerun()

                        sheet_ads.append_row(valores, value_input_option="USER_ENTERED")
                        cached_campanhas_ads.clear()
                        st.success(f"✅ Campanha '{nome_campanha}' cadastrada com sucesso!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Erro ao salvar campanha: {e}")
                else:
                    st.error("❌ Preencha o Nome da Campanha e o Orçamento Diário (maior que zero).")

            st.markdown("<br><br>", unsafe_allow_html=True)
            st.subheader("📋 Campanhas Cadastradas")

            df_campanhas = cached_campanhas_ads()
            if df_campanhas is not None and not df_campanhas.empty:
                df_view = df_campanhas.copy()

                if "Data de Registro" in df_view.columns:
                    df_view = df_view.rename(columns={"Data de Registro": "Data da Criação"})
                    
                if "Data da Criação" in df_view.columns:
                    df_view["Data da Criação"] = df_view["Data da Criação"].apply(converter_data_sheets)

                def limpar_anuncios(json_str):
                    try:
                        lista = json.loads(str(json_str))
                        if isinstance(lista, list):
                            return f"{len(lista)} anúncio(s)"
                        return "0 anúncios"
                    except:
                        return str(json_str)

                if "Anúncios" in df_view.columns:
                    df_view["Qtd Anúncios"] = df_view["Anúncios"].apply(limpar_anuncios)
                    df_view = df_view.drop(columns=["Anúncios"])

                cols = df_view.columns.tolist()
                if "Qtd Anúncios" in cols:
                    cols.insert(3, cols.pop(cols.index("Qtd Anúncios")))
                    df_view = df_view[cols]

                st.markdown("---")
                c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1.5, 2, 1.5, 1.5, 1.5])
                c1.write("**Nome da Campanha**")
                c2.write("**ROAS Objetivo**")
                c3.write("**Orçamento Diário (R$)**")
                c4.write("**Qtd Anúncios**")
                c5.write("**Data da Criação**")
                c6.write("**Ação**")
                st.markdown("---")
                
                for idx, row in df_view.iterrows():
                    c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1.5, 2, 1.5, 1.5, 1.5])
                    nome_c = str(row.get('Nome da Campanha', ''))
                    
                    c1.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{nome_c}</div>", unsafe_allow_html=True)
                    c2.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row.get('ROAS Objetivo', ''))}</div>", unsafe_allow_html=True)
                    
                    orc_val = converter_valor(row.get('Orçamento Diário', 0))
                    c3.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>R$ {orc_val:.2f}</div>".replace('.', ','), unsafe_allow_html=True)
                    
                    c4.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row.get('Qtd Anúncios', ''))}</div>", unsafe_allow_html=True)
                    c5.markdown(f"<div style='margin-top: 10px; color: #1E1E1E;'>{str(row.get('Data da Criação', ''))}</div>", unsafe_allow_html=True)
                    
                    c6.button("📊 Analisar", key=f"btn_analise_{idx}", on_click=ativar_analise, args=(nome_c,))

            else:
                st.info("Nenhuma campanha de ADS cadastrada até o momento.")

        elif aba_selecionada == "📊 Análise de Campanha":
            st.markdown("<br>", unsafe_allow_html=True)
            
            lista_camps = []
            df_campanhas = cached_campanhas_ads()
            if df_campanhas is not None and not df_campanhas.empty:
                if "Nome da Campanha" in df_campanhas.columns:
                    lista_camps = df_campanhas["Nome da Campanha"].dropna().unique().tolist()
            
            if not lista_camps:
                st.info("Cadastre uma campanha primeiro para poder analisá-la.")
            else:
                idx_camp = 0
                if st.session_state.campanha_analise_selecionada in lista_camps:
                    idx_camp = lista_camps.index(st.session_state.campanha_analise_selecionada)
                    
                campanha_sel = st.selectbox("Selecione a Campanha para Análise", options=lista_camps, index=idx_camp)
                
                st.markdown("---")
                st.subheader(f"Métricas: {campanha_sel}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    data_analise = st.text_input("Data da Análise", value=datetime.now().strftime("%d/%m/%Y"), key="data_analise")
                with col2:
                    impressoes = st.number_input("Impressões", min_value=0, step=1)
                with col3:
                    cliques = st.number_input("Cliques", min_value=0, step=1)

                col4, col5 = st.columns(2)
                with col4:
                    vendas_ads = st.number_input("Vendas ADS", min_value=0, step=1)
                with col5:
                    vendas_org = st.number_input("Vendas ORG", min_value=0, step=1)

                col6, col7, col8 = st.columns(3)
                with col6:
                    inv_str = st.text_input("Investimento ADS (R$)", value="0,00", key="inv_ads")
                with col7:
                    fat_ads_str = st.text_input("Faturamento ADS (R$)", value="0,00", key="fat_ads")
                with col8:
                    fat_org_str = st.text_input("Faturamento ORG (R$)", value="0,00", key="fat_org")
                    
                val_inv = converter_valor(inv_str)
                val_fat_ads = converter_valor(fat_ads_str)
                val_fat_org = converter_valor(fat_org_str)
                
                # Cálculos
                ctr_calc = (cliques / impressoes) * 100 if impressoes > 0 else 0.0
                conv_ads_calc = (vendas_ads / cliques) * 100 if cliques > 0 else 0.0
                conv_tot_calc = ((vendas_ads + vendas_org) / cliques) * 100 if cliques > 0 else 0.0
                cpc_calc = (val_inv / cliques) if cliques > 0 else 0.0
                acos_calc = (val_inv / val_fat_ads) * 100 if val_fat_ads > 0 else 0.0
                roas_calc = (val_fat_ads / val_inv) if val_inv > 0 else 0.0
                
                fat_tot = val_fat_ads + val_fat_org
                tacos_calc = (val_inv / fat_tot) * 100 if fat_tot > 0 else 0.0
                cpa_calc = (val_inv / vendas_ads) if vendas_ads > 0 else 0.0
                
                st.write("**Resultados Apurados:**")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("CTR", f"{ctr_calc:.2f}%".replace('.', ','))
                r2.metric("CONV ADS", f"{conv_ads_calc:.2f}%".replace('.', ','))
                r3.metric("CONV TOT", f"{conv_tot_calc:.2f}%".replace('.', ','))
                r4.metric("CPC", f"R$ {cpc_calc:.2f}".replace('.', ','))

                r5, r6, r7, r8 = st.columns(4)
                r5.metric("ACOS", f"{acos_calc:.2f}%".replace('.', ','))
                r6.metric("ROAS", f"{roas_calc:.2f}".replace('.', ','))
                r7.metric("TACOS", f"{tacos_calc:.2f}%".replace('.', ','))
                r8.metric("CPA", f"R$ {cpa_calc:.2f}".replace('.', ','))
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Salvar Análise", key="btn_salvar_analise"):
                    if val_inv >= 0 and val_fat_ads >= 0:
                        try:
                            client = get_sheets_client()
                            doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                            try:
                                sheet_an = doc.worksheet("Analises_ADS")
                                if sheet_an.col_count < 16:
                                    sheet_an.add_cols(16 - sheet_an.col_count)
                                
                                header_an = ["Campanha", "Data da Análise", "Impressões", "Cliques", "Vendas ADS", "Vendas ORG", "Investimento ADS", "Faturamento ADS", "Faturamento ORG", "CTR", "CONV ADS", "CONV TOT", "CPC", "ACOS", "ROAS", "TACOS"]
                                if sheet_an.row_values(1) != header_an:
                                    sheet_an.update(range_name='A1:P1', values=[header_an], value_input_option="USER_ENTERED")
                            except:
                                sheet_an = doc.add_worksheet(title="Analises_ADS", rows="1000", cols="16")
                                sheet_an.append_row(["Campanha", "Data da Análise", "Impressões", "Cliques", "Vendas ADS", "Vendas ORG", "Investimento ADS", "Faturamento ADS", "Faturamento ORG", "CTR", "CONV ADS", "CONV TOT", "CPC", "ACOS", "ROAS", "TACOS"], value_input_option="USER_ENTERED")
                            
                            val_formatados = [
                                campanha_sel,
                                data_analise,
                                impressoes,
                                cliques,
                                vendas_ads,
                                vendas_org,
                                f"{val_inv:.2f}".replace('.', ','),
                                f"{val_fat_ads:.2f}".replace('.', ','),
                                f"{val_fat_org:.2f}".replace('.', ','),
                                f"{ctr_calc:.2f}%".replace('.', ','),
                                f"{conv_ads_calc:.2f}%".replace('.', ','),
                                f"{conv_tot_calc:.2f}%".replace('.', ','),
                                f"R$ {cpc_calc:.2f}".replace('.', ','),
                                f"{acos_calc:.2f}%".replace('.', ','),
                                f"{roas_calc:.2f}".replace('.', ','),
                                f"{tacos_calc:.2f}%".replace('.', ',')
                            ]
                            sheet_an.append_row(val_formatados, value_input_option="USER_ENTERED")
                            cached_analises_ads.clear()
                            st.success("✅ Análise salva com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar análise: {e}")
                            
                st.markdown("---")
                st.subheader("🕒 Histórico de Análises")
                df_analises = cached_analises_ads()
                if df_analises is not None and not df_analises.empty:
                    df_view_an = df_analises[df_analises["Campanha"] == campanha_sel].copy()
                    
                    if "Data da Análise" in df_view_an.columns:
                        df_view_an["Data da Análise"] = df_view_an["Data da Análise"].apply(formatar_data_hora)
                        
                    if not df_view_an.empty:
                        st.dataframe(
                            df_view_an.style.set_properties(**{
                                'background-color': '#F4F6F9',
                                'color': '#1E1E1E',
                                'border-color': '#E5E7EB'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("Nenhuma análise registada para esta campanha.")
                else:
                    st.info("Nenhuma análise registada no sistema.")

# =====================================================================
# MÓDULO 6: PÓS VENDA
# =====================================================================
elif menu_selecionado == "Pós Venda":
    
    def limpar_num_venda(valor):
        return re.sub(r'\D', '', str(valor).split('.')[0])
        
    if "num_venda" not in st.session_state: st.session_state.num_venda = ""
    if "id_an_oc" not in st.session_state: st.session_state.id_an_oc = ""
    if "sku_oc" not in st.session_state: st.session_state.sku_oc = ""
    if "custo_oc" not in st.session_state: st.session_state.custo_oc = "0,00"
    if "reputacao_oc" not in st.session_state: st.session_state.reputacao_oc = "Não"
    if "desc_oc" not in st.session_state: st.session_state.desc_oc = ""
    if "status_oc" not in st.session_state: st.session_state.status_oc = "Aberto"
    if "resolucao_oc" not in st.session_state: st.session_state.resolucao_oc = ""

    def puxar_dados_ocorrencia_trigger():
        venda_busca = limpar_num_venda(st.session_state.get("num_venda", ""))
        if venda_busca:
            df_oc = cached_ocorrencias()
            if df_oc is not None and not df_oc.empty and "Número da Venda" in df_oc.columns:
                df_oc["Número da Venda"] = df_oc["Número da Venda"].apply(limpar_num_venda)
                res = df_oc[df_oc["Número da Venda"] == venda_busca]
                if not res.empty:
                    st.session_state.id_an_oc = str(res.iloc[0].get("ID do Anúncio", ""))
                    st.session_state.sku_oc = str(res.iloc[0].get("SKU do Produto", ""))
                    st.session_state.custo_oc = formatar_moeda_ui(res.iloc[0].get("Custo da Ocorrência", 0))
                    st.session_state.reputacao_oc = str(res.iloc[0].get("Afetou Reputação", "Não"))
                    st.session_state.desc_oc = str(res.iloc[0].get("Descrição da Ocorrência", ""))
                    st.session_state.status_oc = str(res.iloc[0].get("Status", "Aberto"))
                    st.session_state.resolucao_oc = str(res.iloc[0].get("Resolução", ""))
                else:
                    st.session_state.id_an_oc = ""
                    st.session_state.sku_oc = ""
                    st.session_state.custo_oc = "0,00"
                    st.session_state.reputacao_oc = "Não"
                    st.session_state.desc_oc = ""
                    st.session_state.status_oc = "Aberto"
                    st.session_state.resolucao_oc = ""
        else:
            st.session_state.id_an_oc = ""
            st.session_state.sku_oc = ""
            st.session_state.custo_oc = "0,00"
            st.session_state.reputacao_oc = "Não"
            st.session_state.desc_oc = ""
            st.session_state.status_oc = "Aberto"
            st.session_state.resolucao_oc = ""

    def excluir_ocorrencia(num_venda):
        df = cached_ocorrencias()
        if not df.empty:
            df["Venda_Match"] = df["Número da Venda"].apply(limpar_num_venda)
            mask = df["Venda_Match"] == limpar_num_venda(num_venda)
            indices = df[mask].index.tolist()
            if indices:
                client = get_sheets_client()
                sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").worksheet("Pos_Venda")
                linhas_sheet = [i + 2 for i in indices]
                for linha in sorted(linhas_sheet, reverse=True):
                    sheet.delete_rows(linha)
                return True
        return False

    def encerrar_ocorrencia(num_venda):
        df = cached_ocorrencias()
        if not df.empty:
            df["Venda_Match"] = df["Número da Venda"].apply(limpar_num_venda)
            mask = (df["Venda_Match"] == limpar_num_venda(num_venda)) & (df["Status"] != "Encerrado")
                   
            indices = df[mask].index.tolist()
            if indices:
                linha_real = indices[0] + 2
                client = get_sheets_client()
                sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").worksheet("Pos_Venda")
                sheet.update_cell(linha_real, 5, "Encerrado")
                sheet.update_cell(linha_real, 4, datetime.now().strftime("%d/%m/%Y"))
                return True
        return False

    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.2, 4, 0.2])
    with col_conteudo:
        st.title("🛠️ Pós Venda e Ocorrências")
        st.markdown("Cadastre problemas, dúvidas ou devoluções referentes às suas vendas.")

        if "sucesso_ocorrencia" not in st.session_state:
            st.session_state.sucesso_ocorrencia = ""
            
        if st.session_state.sucesso_ocorrencia:
            st.success(st.session_state.sucesso_ocorrencia)
            st.session_state.sucesso_ocorrencia = ""

        tab_ativas, tab_historico = st.tabs(["🚨 Ocorrências Ativas", "📂 Histórico de Ocorrências"])

        with tab_ativas:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Nova Ocorrência")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                num_venda = st.text_input("Número da Venda", key="num_venda", on_change=puxar_dados_ocorrencia_trigger)
            with c2:
                id_an_oc = st.text_input("ID do Anúncio", key="id_an_oc")
            with c3:
                sku_oc = st.text_input("SKU do Produto", key="sku_oc")
                
            c4, c5, c6 = st.columns(3)
            with c4:
                status_opcoes = ["Aberto", "Em Tratativa", "Aguardando Cliente", "Devolução em Atraso", "Encerrado"]
                status_oc = st.selectbox("Status da Ocorrência", status_opcoes, key="status_oc")
            with c5:
                reputacao_oc = st.selectbox("Afetou a reputação da conta?", ["Não", "Sim"], key="reputacao_oc")
            with c6:
                custo_oc_str = st.text_input("Custo da Ocorrência (R$)", key="custo_oc")
                custo_oc = converter_valor(custo_oc_str)
                
            desc_oc = st.text_area("Descrição da Ocorrência", height=250, key="desc_oc")
            
            c_res, c_data = st.columns([3, 1])
            with c_res:
                resolucao_oc = st.text_area("Resolução (Como foi finalizado)", height=250, key="resolucao_oc", placeholder="Preencha este campo ao encerrar a ocorrência.")
            with c_data:
                data_oc = st.text_input("Data da Atualização", value=datetime.now().strftime("%d/%m/%Y"))
                
            st.markdown("---")
            
            col_btn1, col_btn2, col_btn3, col_vazio = st.columns([2, 2, 2, 4])
            
            with col_btn1:
                btn_registrar = st.button("💾 Salvar")
            with col_btn2:
                btn_excluir = st.button("🗑️ Excluir Ocorrência")
            with col_btn3:
                btn_limpar = st.button("🧹 Limpar Campos")
            
            campos_limpeza = ["num_venda", "id_an_oc", "sku_oc", "custo_oc", "reputacao_oc", "desc_oc", "status_oc", "resolucao_oc"]
            
            if btn_limpar:
                for k in campos_limpeza:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

            if btn_registrar:
                if num_venda.strip() and desc_oc.strip():
                    try:
                        client = get_sheets_client()
                        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                        
                        header_esperado = ["Número da Venda", "ID do Anúncio", "Descrição da Ocorrência", "Data da Atualização", "Status", "Resolução", "SKU do Produto", "Custo da Ocorrência", "Afetou Reputação"]
                        
                        try:
                            sheet_oc = doc.worksheet("Pos_Venda")
                            if sheet_oc.col_count < 9:
                                sheet_oc.add_cols(9 - sheet_oc.col_count)
                            
                            header_atual = sheet_oc.row_values(1)
                            if header_atual != header_esperado:
                                sheet_oc.update(range_name='A1:I1', values=[header_esperado], value_input_option="USER_ENTERED")
                        except:
                            sheet_oc = doc.add_worksheet(title="Pos_Venda", rows="1000", cols="9")
                            sheet_oc.append_row(header_esperado)
                        
                        df_oc = cached_ocorrencias()
                        
                        num_limpo = limpar_num_venda(num_venda)
                        
                        valores_oc = [
                            num_limpo,
                            id_an_oc.strip(),
                            desc_oc.strip(),
                            data_oc.strip(),
                            status_oc,
                            resolucao_oc.strip(),
                            sku_oc.strip(),
                            f"{custo_oc:.2f}".replace('.', ','),
                            reputacao_oc
                        ]
                        
                        if df_oc is not None and not df_oc.empty and "Número da Venda" in df_oc.columns:
                            df_oc["Venda_Match"] = df_oc["Número da Venda"].apply(limpar_num_venda)
                            if num_limpo in df_oc["Venda_Match"].values:
                                idx = df_oc[df_oc["Venda_Match"] == num_limpo].index[0]
                                sheet_oc.update(range_name=f'A{idx+2}:I{idx+2}', values=[valores_oc], value_input_option="USER_ENTERED")
                                cached_ocorrencias.clear()
                                st.session_state.sucesso_ocorrencia = f"✅ Ocorrência para a venda '{num_limpo}' atualizada com sucesso!"
                                for k in campos_limpeza:
                                    if k in st.session_state:
                                        del st.session_state[k]
                                st.rerun()

                        sheet_oc.append_row(valores_oc, value_input_option="USER_ENTERED")
                        cached_ocorrencias.clear()
                        st.session_state.sucesso_ocorrencia = f"✅ Ocorrência para a venda '{num_limpo}' registada com sucesso!"
                        for k in campos_limpeza:
                            if k in st.session_state:
                                del st.session_state[k]
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao registrar ocorrência: {e}")
                else:
                    st.error("❌ Os campos Número da Venda e Descrição são obrigatórios.")
                    
            if btn_excluir:
                if num_venda.strip():
                    if excluir_ocorrencia(num_venda):
                        st.session_state.sucesso_ocorrencia = f"✅ Ocorrência da venda '{num_venda}' excluída com sucesso!"
                        cached_ocorrencias.clear()
                        for k in campos_limpeza:
                            if k in st.session_state:
                                del st.session_state[k]
                        st.rerun()
                    else:
                        st.warning("⚠️ Ocorrência não encontrada para exclusão.")
                else:
                    st.error("❌ Informe o Número da Venda para a poder excluir.")
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.subheader("📋 Ocorrências em Andamento")
            st.caption("💡 Para inserir a Resolução de uma ocorrência, digite o Número da Venda acima, preencha o campo de Resolução, mude o status para 'Encerrado' e clique em Salvar.")
            
            df_oc = cached_ocorrencias()
            if df_oc is not None and not df_oc.empty and "Status" in df_oc.columns:
                df_ativas = df_oc[df_oc["Status"] != "Encerrado"].copy()
                if not df_ativas.empty:
                    st.markdown("---")
                    c_v, c_an, c_sku, c_dt, c_st, c_cus, c_ac = st.columns([1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
                    c_v.write("**Venda**")
                    c_an.write("**Anúncio**")
                    c_sku.write("**SKU**")
                    c_dt.write("**Atualização**")
                    c_st.write("**Status**")
                    c_cus.write("**Custo (R$)**")
                    c_ac.write("**Ação**")
                    st.markdown("---")
                    
                    for idx, row in df_ativas.iterrows():
                        c_v, c_an, c_sku, c_dt, c_st, c_cus, c_ac = st.columns([1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
                        
                        venda_num = limpar_num_venda(row.get('Número da Venda', ''))
                        custo_val = converter_valor(row.get('Custo da Ocorrência', 0))
                        
                        c_v.markdown(f"<div style='margin-top: 5px; color: #1E1E1E;'>{venda_num}</div>", unsafe_allow_html=True)
                        c_an.markdown(f"<div style='margin-top: 5px; color: #1E1E1E;'>{str(row.get('ID do Anúncio', ''))}</div>", unsafe_allow_html=True)
                        c_sku.markdown(f"<div style='margin-top: 5px; color: #1E1E1E;'>{str(row.get('SKU do Produto', ''))}</div>", unsafe_allow_html=True)
                        c_dt.markdown(f"<div style='margin-top: 5px; color: #1E1E1E;'>{formatar_data_hora(row.get('Data da Atualização', ''))}</div>", unsafe_allow_html=True)
                        c_st.markdown(f"<div style='margin-top: 5px; font-weight: bold; color: #DA1984;'>{str(row.get('Status', ''))}</div>", unsafe_allow_html=True)
                        c_cus.markdown(f"<div style='margin-top: 5px; color: #1E1E1E;'>R$ {custo_val:.2f}</div>".replace('.', ','), unsafe_allow_html=True)
                        
                        if c_ac.button("🔒 Encerrar", key=f"encerrar_{idx}", help="Encerra rapidamente sem detalhar a resolução"):
                            if encerrar_ocorrencia(venda_num):
                                st.session_state.sucesso_ocorrencia = "✅ Ocorrência encerrada e arquivada com sucesso!"
                                cached_ocorrencias.clear()
                                st.rerun()
                            else:
                                st.error("Erro ao encerrar a ocorrência.")
                else:
                    st.info("Fantástico! Não existem ocorrências pendentes de resolução.")
            else:
                st.info("Nenhuma ocorrência registrada no sistema.")

        with tab_historico:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📂 Histórico de Ocorrências (Encerradas)")
            
            if df_oc is not None and not df_oc.empty and "Status" in df_oc.columns:
                df_hist = df_oc[df_oc["Status"] == "Encerrado"].copy()
                if not df_hist.empty:
                    df_hist["Número da Venda"] = df_hist["Número da Venda"].apply(limpar_num_venda)
                    df_hist["Data da Atualização"] = df_hist["Data da Atualização"].apply(formatar_data_hora)
                    
                    st.dataframe(
                        df_hist.style.set_properties(**{
                            'background-color': '#F4F6F9',
                            'color': '#1E1E1E',
                            'border-color': '#E5E7EB'
                        }),
                        use_container_width=True,
                        hide_index=True 
                    )
                else:
                    st.info("Nenhuma ocorrência foi encerrada até ao momento.")
            else:
                st.info("Nenhuma ocorrência registrada no sistema.")

# =====================================================================
# MÓDULO 7: CALCULADORA SIMPLES
# =====================================================================
elif menu_selecionado == "Calculadora Simples":
    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.2, 4, 0.2])
    with col_conteudo:
        st.title("🧮 Calculadora Simples")
        st.markdown("Faça simulações rápidas para descobrir o **Preço de Venda ideal** com base na margem de lucro que deseja obter.")
        
        st.markdown("---")
        st.subheader("💸 Dados da Venda")
        
        # O campo de Venda Real foi removido daqui e substituído pela Margem
        col_custo, col_margem, col_desc = st.columns(3)
        with col_custo: custo_produto_str = st.text_input("Custo do Produto (R$)", value="0,00", key="custo_prod_calc")
        with col_margem: margem_desejada = st.number_input("Margem de Lucro Desejada (%)", min_value=0.0, max_value=99.9, value=20.0, step=0.1, key="margem_calc")
        with col_desc: porcentagem_desconto = st.number_input("Desconto de Campanha (%)", min_value=0.0, max_value=99.9, step=0.1, key="desc_calc")
        
        col_comissao, col_frete, col_taxa = st.columns(3)
        with col_comissao: comissao_mkt_porcentagem = st.number_input("Comissão Marketplace (%)", min_value=0.0, step=0.1, key="com_calc")
        with col_frete: custo_frete_str = st.text_input("Custo de Frete (R$)", value="0,00", key="frete_calc")
        with col_taxa: taxa_fixa_venda_str = st.text_input("Custo Full / Fixo (R$)", value="0,00", key="taxa_calc")

        col_estorno, col_tacos, col_imposto = st.columns(3)
        with col_estorno: estorno_ml_str = st.text_input("Estorno/Bonificação ML (R$)", value="0,00", key="estorno_calc")
        with col_tacos: porcentagem_tacos = st.number_input("Custo de Publicidade ACOS OBJ. (%)", min_value=0.0, max_value=100.0, step=0.1, key="tacos_calc")
        with col_imposto: imposto_porcentagem = st.number_input("Imposto sobre NF (%)", min_value=0.0, value=7.3, step=0.1, key="imposto_calc")

        custo_produto = converter_valor(custo_produto_str)
        custo_frete = converter_valor(custo_frete_str)
        taxa_fixa_venda = converter_valor(taxa_fixa_venda_str)
        estorno_ml = converter_valor(estorno_ml_str)

        # --- LÓGICA DE PRECIFICAÇÃO REVERSA (MARKUP) ---
        custos_fixos = custo_produto + custo_frete + taxa_fixa_venda - estorno_ml
        percentuais_variaveis = (comissao_mkt_porcentagem + imposto_porcentagem + porcentagem_tacos + margem_desejada) / 100.0

        preco_final = 0.0
        preco_original = 0.0
        lucro_liquido = 0.0
        custo_total_saidas = 0.0
        valor_comissao = 0.0
        valor_imposto = 0.0
        valor_tacos = 0.0

        # Bloqueio matemático: se os custos variáveis e a margem passarem de 100%, é impossível calcular
        if percentuais_variaveis >= 1.0:
            st.error("⚠️ A soma das porcentagens (Margem, Comissão, Imposto, TACOS) é igual ou maior que 100%. É matematicamente impossível definir um preço com estes parâmetros.")
        else:
            preco_final = custos_fixos / (1 - percentuais_variaveis)
            
            if preco_final < 0:
                preco_final = 0.0
                
            # Se houver desconto de campanha, o preço original tem de ser inflacionado
            if porcentagem_desconto > 0:
                preco_original = preco_final / (1 - (porcentagem_desconto / 100.0))
            else:
                preco_original = preco_final

            valor_comissao = preco_final * (comissao_mkt_porcentagem / 100)
            valor_imposto = preco_final * (imposto_porcentagem / 100)
            valor_tacos = preco_final * (porcentagem_tacos / 100)

            custo_total_saidas = custo_produto + custo_frete + valor_comissao + valor_imposto + taxa_fixa_venda + valor_tacos
            lucro_liquido = (preco_final + estorno_ml) - custo_total_saidas

        st.divider()
        st.subheader("📈 Resultados")

        # Exibição dos resultados com a nova ordem
        col_res_orig, col_res_venda, col_res_lucro, col_res_custo = st.columns(4)
        with col_res_orig: st.metric("Preço Original (Sem desc.)", f"R$ {preco_original:.2f}".replace('.', ','))
        with col_res_venda: st.metric("Preço de Venda Real", f"R$ {preco_final:.2f}".replace('.', ','))
        with col_res_lucro: st.metric("Lucro Líquido", f"R$ {lucro_liquido:.2f}".replace('.', ','))
        with col_res_custo: st.metric("Custo Total", f"R$ {custo_total_saidas:.2f}".replace('.', ','))

        st.write("### Detalhamento Financeiro")
        denominador = preco_final if preco_final > 0 else 1.0
        valor_desconto = preco_original - preco_final

        descricoes = ["Preço Original", "Desconto", "Preço Final", "Custo Produto", "Comissão", "Frete", "Imposto", "Custo Full", "ACOS OBJ.", "Estorno", "LUCRO LÍQUIDO"]
        tipos = ["positivo", "negativo", "positivo", "negativo", "negativo", "negativo", "negativo", "negativo", "negativo", "positivo", "positivo"]
        valores = [preco_original, valor_desconto, preco_final, custo_produto, valor_comissao, custo_frete, valor_imposto, taxa_fixa_venda, valor_tacos, estorno_ml, lucro_liquido]

        html_table = "<table style='width: 100%; border-collapse: collapse; text-align: left; background-color: #F8F9FA; color: #1E1E1E; font-size: 14px; margin-bottom: 1rem;'>"
        html_table += "<tr><th style='padding: 4px 8px; border-bottom: 1px solid #D1D5DB; font-weight: 600;'>Descrição</th><th style='padding: 4px 8px; border-bottom: 1px solid #D1D5DB; font-weight: 600;'>Valor</th><th style='padding: 4px 8px; border-bottom: 1px solid #D1D5DB; font-weight: 600;'>Percentual (%)</th></tr>"

        for desc, val, tipo in zip(descricoes, valores, tipos):
            cor_hex = "#198754" if tipo == "positivo" else "#DC3545"
            sinal = "-" if tipo == "negativo" and val > 0 else ""
            
            pct = (val / denominador) * 100 
            
            val_fmt = f"{sinal}R$ {val:.2f}".replace('.', ',')
            pct_fmt = f"{sinal}{pct:.2f}%".replace('.', ',')
            
            peso_fonte = "bold" if desc == "LUCRO LÍQUIDO" else "normal"
            borda = "border-top: 1px solid #D1D5DB;" if desc == "LUCRO LÍQUIDO" else "border: none;"
            
            html_table += f"<tr style='{borda}'><td style='padding: 2px 8px; font-weight: {peso_fonte};'>{desc}</td>"
            html_table += f"<td style='padding: 2px 8px; color: {cor_hex}; font-weight: {peso_fonte};'>{val_fmt}</td>"
            html_table += f"<td style='padding: 2px 8px; color: {cor_hex}; font-weight: {peso_fonte};'>{pct_fmt}</td></tr>"

        html_table += "</table>"
        
        st.markdown(html_table, unsafe_allow_html=True)
# =====================================================================
# MÓDULO 8: CHATBOT
# =====================================================================
elif menu_selecionado == "ChatBot":
    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.2, 4, 0.2])
    with col_conteudo:
        st.title("🤖 ChatBot - Respostas Rápidas")
        st.markdown("Cadastre e organize frases prontas para agilizar o atendimento aos seus clientes.")

        tab_cadastro, tab_lista = st.tabs(["📝 Cadastrar / Editar Frase", "💬 Frases Prontas"])

        with tab_cadastro:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Cadastro de Interação")

            nome_interacao = st.text_input("Nome da Interação", placeholder="Ex: Saudação, Atraso na Entrega, Devolução...")
            frase_padrao = st.text_area("Frase Padrão (Resposta para o cliente)", height=150, placeholder="Olá! Tudo bem? Pedimos desculpas pelo ocorrido...")

            st.markdown("---")
            if st.button("💾 Salvar Frase"):
                if nome_interacao.strip() and frase_padrao.strip():
                    try:
                        client = get_sheets_client()
                        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                        try:
                            sheet_chat = doc.worksheet("ChatBot")
                        except:
                            sheet_chat = doc.add_worksheet(title="ChatBot", rows="1000", cols="3")
                            sheet_chat.append_row(["Nome da Interação", "Frase Padrão", "Data de Atualização"])

                        df_chat = cached_chatbot_frases()
                        data_att = datetime.now().strftime("%d/%m/%Y")
                        valores = [nome_interacao.strip(), frase_padrao.strip(), data_att]

                        if df_chat is not None and not df_chat.empty and "Nome da Interação" in df_chat.columns:
                            df_chat["Nome_Match"] = df_chat["Nome da Interação"].astype(str).str.strip()
                            if nome_interacao.strip() in df_chat["Nome_Match"].values:
                                idx = df_chat[df_chat["Nome_Match"] == nome_interacao.strip()].index[0]
                                sheet_chat.update(range_name=f'A{idx+2}:C{idx+2}', values=[valores], value_input_option="USER_ENTERED")
                                cached_chatbot_frases.clear()
                                st.success(f"✅ Frase '{nome_interacao}' atualizada com sucesso!")
                                st.rerun()

                        sheet_chat.append_row(valores, value_input_option="USER_ENTERED")
                        cached_chatbot_frases.clear()
                        st.success(f"✅ Frase '{nome_interacao}' cadastrada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar frase: {e}")
                else:
                    st.error("❌ Preencha o Nome da Interação e a Frase Padrão para continuar.")

        with tab_lista:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("💬 Lista de Frases")

            df_chat = cached_chatbot_frases()
            if df_chat is not None and not df_chat.empty:
                for idx, row in df_chat.iterrows():
                    nome = str(row.get("Nome da Interação", ""))
                    frase = str(row.get("Frase Padrão", ""))
                    data_raw = row.get("Data de Atualização", "")
                    data_att = formatar_data_hora(data_raw)

                    with st.expander(f"📌 {nome}"):
                        st.caption("💡 Clique no ícone de cópia no canto superior direito do quadro abaixo para copiar a frase.")
                        st.code(frase, language="text")
                        
                        c_btn, c_dt = st.columns([1, 4])
                        with c_dt:
                            st.markdown(f"<div style='margin-top:10px; color:gray; font-size:12px;'>Última atualização: {data_att}</div>", unsafe_allow_html=True)
                        with c_btn:
                            if st.button("🗑️ Excluir", key=f"del_frase_{idx}"):
                                try:
                                    client = get_sheets_client()
                                    doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                                    sheet_chat = doc.worksheet("ChatBot")
                                    
                                    df_atual = pd.DataFrame(sheet_chat.get_all_records(value_render_option="UNFORMATTED_VALUE"))
                                    df_atual["Nome_Match"] = df_atual["Nome da Interação"].astype(str).str.strip()
                                    idx_to_del = df_atual[df_atual["Nome_Match"] == nome].index[0]
                                    
                                    sheet_chat.delete_rows(int(idx_to_del) + 2)
                                    cached_chatbot_frases.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro ao excluir: {e}")
            else:
                st.info("Nenhuma frase cadastrada até o momento. Acesse a aba ao lado para criar a sua primeira interação.")

# =====================================================================
# MÓDULO 9: FULFILLMENT
# =====================================================================
elif menu_selecionado == "Fulfillment":
    import json
    import math
    from datetime import timedelta
    
    # Inicializa a lista de itens do envio atual e do estoque na memória
    if "full_itens" not in st.session_state: st.session_state.full_itens = []
    if "estoque_itens" not in st.session_state: st.session_state.estoque_itens = []

    # Inicializa variáveis base
    for k in ["est_cod", "est_sku", "est_mlb", "est_nome", "est_peso", "est_tam", "est_custo_diario"]:
        if k not in st.session_state: st.session_state[k] = ""
    if "sugestao_msg" not in st.session_state: st.session_state.sugestao_msg = ""
    
    # Inicializa variáveis do cabeçalho de envio
    if "nome_envio_input" not in st.session_state: st.session_state.nome_envio_input = ""
    if "codigo_envio_input" not in st.session_state: st.session_state.codigo_envio_input = ""

    # ==========================================================
    # CACHE INTELIGENTE DO ESTOQUE
    # ==========================================================
    def limpar_cache_estoque():
        if "estoque_opcoes" in st.session_state: del st.session_state["estoque_opcoes"]
        if "df_estoque_cache" in st.session_state: del st.session_state["df_estoque_cache"]

    if "estoque_opcoes" not in st.session_state:
        st.session_state.estoque_opcoes = [""]
        st.session_state.df_estoque_cache = pd.DataFrame()
        try:
            client = get_sheets_client()
            doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
            sheet_est = doc.worksheet("Estoque Full")
            df_e = pd.DataFrame(sheet_est.get_all_records())
            st.session_state.df_estoque_cache = df_e
            if not df_e.empty and "Código do Full" in df_e.columns:
                ops = [""]
                for _, row in df_e.iterrows():
                    c = str(row.get("Código do Full", "")).strip()
                    n = str(row.get("Produto", "")).strip()
                    if c: ops.append(f"{c} | {n}")
                st.session_state.estoque_opcoes = ops
        except:
            pass

    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.2, 4, 0.2])
    with col_conteudo:
        st.title("📦 Fulfillment")
        st.markdown("Faça a gestão do seu inventário no centro de distribuição (Full) e crie novos envios.")

        tab_envios, tab_estoque, tab_consulta = st.tabs(["📦 Gestão de Envios", "🏭 Cadastro no Estoque", "📊 Consulta de Estoque"])

        # ==========================================================
        # ABA 1: GESTÃO DE ENVIOS
        # ==========================================================
        with tab_envios:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("Dados do Envio")
            
            # Função para carregar um envio existente para edição
            def carregar_dados_envio():
                nome_busca = st.session_state.get("nome_envio_input", "").strip()
                if nome_busca:
                    try:
                        client = get_sheets_client()
                        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                        sheet_env = doc.worksheet("Fulfillment")
                        df_env = pd.DataFrame(sheet_env.get_all_records())
                        
                        if not df_env.empty and "Nome do Envio" in df_env.columns:
                            df_env["Nome_Match"] = df_env["Nome do Envio"].astype(str).str.strip()
                            row = df_env[df_env["Nome_Match"] == nome_busca]
                            
                            if not row.empty:
                                item = row.iloc[0]
                                st.session_state.codigo_envio_input = str(item.get("Código do Envio", ""))
                                
                                d_env_str = str(item.get("Data do Envio", ""))
                                try:
                                    st.session_state.data_envio_input = datetime.strptime(d_env_str, "%d/%m/%Y").date()
                                except: pass
                                
                                json_str = str(item.get("Detalhes dos Itens (JSON)", "[]"))
                                if json_str and json_str != "nan":
                                    st.session_state.full_itens = json.loads(json_str)
                                else:
                                    st.session_state.full_itens = []
                    except: pass

            c1, c2 = st.columns(2)
            with c1: 
                st.text_input("Nome do Envio", placeholder="Ex: Envio 15 - Ago/26", key="nome_envio_input", on_change=carregar_dados_envio)
            with c2: 
                st.text_input("Código do Envio", placeholder="Ex: FBM123456", key="codigo_envio_input")
                
            c3, c4 = st.columns(2)
            with c3: 
                if "data_envio_input" not in st.session_state: st.session_state.data_envio_input = datetime.now().date()
                data_envio = st.date_input("Data do Envio", key="data_envio_input", format="DD/MM/YYYY")
            with c4: 
                data_entrega = data_envio + timedelta(days=7)
                st.text_input("Data de Entrega", value=data_entrega.strftime("%d/%m/%Y"), disabled=True)

            st.markdown("---")
            
            st.subheader("➕ Adicionar Itens ao Envio")
            
            for k in ["full_cod", "full_tam", "full_sku", "full_mlb", "full_peso", "full_custo"]:
                if k not in st.session_state: st.session_state[k] = ""
            if "full_qtd" not in st.session_state: st.session_state.full_qtd = 1
            
            def puxar_dados_cod_full():
                cod_busca = st.session_state.get("full_cod", "").strip()
                if cod_busca:
                    df_est = st.session_state.get("df_estoque_cache", pd.DataFrame())
                    if not df_est.empty and "Código do Full" in df_est.columns:
                        df_est["Cod_Match"] = df_est["Código do Full"].astype(str).str.strip()
                        row = df_est[df_est["Cod_Match"] == cod_busca]
                        
                        if not row.empty:
                            item = row.iloc[0]
                            st.session_state.full_tam = str(item.get("Tamanho", ""))
                            st.session_state.full_sku = str(item.get("SKU", ""))
                            st.session_state.full_mlb = str(item.get("MLB Anúncio", ""))
                            
                            peso_val = item.get("Peso", "")
                            if peso_val != "": st.session_state.full_peso = f"{peso_val}".replace('.', ',')
                            
                            custo_diario = item.get("Custo Diário", "")
                            try:
                                if custo_diario != "":
                                    c_dia = float(str(custo_diario).replace(',', '.'))
                                    st.session_state.full_custo = f"{c_dia * 30:.2f}".replace('.', ',')
                            except:
                                st.session_state.full_custo = ""

                            estoque_atual = int(item.get("Estoque Atual", 0))
                            vendas_30d = int(item.get("Vendas (30 dias)", 0))
                            
                            d_env = st.session_state.get("data_envio_input", datetime.now().date())
                            d_ent = d_env + timedelta(days=7)
                            hoje = datetime.now().date()
                            
                            dias_ate_chegada = (d_ent - hoje).days
                            if dias_ate_chegada < 0: dias_ate_chegada = 0
                            
                            venda_diaria = vendas_30d / 30.0
                            estoque_na_chegada = estoque_atual - (venda_diaria * dias_ate_chegada)
                            if estoque_na_chegada < 0: estoque_na_chegada = 0
                            
                            necessidade_30d = venda_diaria * 30.0
                            sugestao = necessidade_30d - estoque_na_chegada
                            
                            qtd_sugerida = math.ceil(sugestao)
                            if qtd_sugerida < 0: qtd_sugerida = 0
                            
                            st.session_state.full_qtd = qtd_sugerida
                            st.session_state.sugestao_msg = f"💡 **Sugestão Inteligente:** Velocidade de **{venda_diaria:.1f}** vendas/dia. Na data de entrega ({d_ent.strftime('%d/%m')}), o seu stock estimado será de **{estoque_na_chegada:.0f}** peças. Para cobrir os 30 dias seguintes (necessidade de **{necessidade_30d:.0f}** peças), a quantidade sugerida de reposição é **{qtd_sugerida}**."

            def on_change_pesquisa():
                val = st.session_state.get("pesquisa_item_envio", "")
                if val and " | " in val:
                    st.session_state.full_cod = val.split(" | ")[0].strip()
                    puxar_dados_cod_full()

            def puxar_peso_sku_full():
                sku_busca = st.session_state.get("full_sku", "").strip()
                if sku_busca:
                    info_prod = buscar_produto_por_sku(sku_busca)
                    if info_prod is not None:
                        st.session_state.full_peso = str(info_prod.get("Peso", ""))

            def calcular_custo_armazenagem():
                tamanho = st.session_state.get("full_tam", "")
                custo_diario = 0.0
                if tamanho == "Pequeno": custo_diario = 0.007
                elif tamanho == "Médio": custo_diario = 0.015
                elif tamanho == "Grande": custo_diario = 0.050
                elif tamanho == "Extragrande": custo_diario = 0.107
                
                if custo_diario > 0:
                    custo_30d = custo_diario * 30
                    st.session_state.full_custo = f"{custo_30d:.2f}".replace('.', ',')
                else:
                    st.session_state.full_custo = ""

            st.selectbox("🔍 Pesquisar Produto no Estoque (Cód. Full ou Nome)", st.session_state.estoque_opcoes, key="pesquisa_item_envio", on_change=on_change_pesquisa)
            st.markdown("<br>", unsafe_allow_html=True)

            i1, i2, i3, i4 = st.columns([1.5, 1.5, 1.5, 1.5])
            cod_full = i1.text_input("Cód. Full", key="full_cod", on_change=puxar_dados_cod_full)
            
            opcoes_tam = ["", "Pequeno", "Médio", "Grande", "Extragrande"]
            tamanho = i2.selectbox("Tamanho (ML)", opcoes_tam, key="full_tam", on_change=calcular_custo_armazenagem)
            
            sku_item = i3.text_input("SKU", key="full_sku", on_change=puxar_peso_sku_full)
            mlb_item = i4.text_input("MLB Anúncio", key="full_mlb")

            i5, i6, i7 = st.columns(3)
            qtd_item = i5.number_input("QTD", min_value=0, step=1, key="full_qtd")
            peso_un_str = i6.text_input("Peso (un) em kg", placeholder="Ex: 0,250", key="full_peso")
            custo_un_str = i7.text_input("Custo Armaz. 30d (R$)", placeholder="Ex: 0,45", key="full_custo")

            if st.session_state.get("sugestao_msg"):
                st.info(st.session_state.sugestao_msg)

            if st.button("Inserir Item no Envio"):
                if sku_item.strip() and tamanho.strip() and qtd_item > 0:
                    peso_un = converter_valor(peso_un_str)
                    custo_un = converter_valor(custo_un_str)
                    
                    peso_total = qtd_item * peso_un
                    custo_total = qtd_item * custo_un

                    novo_item = {
                        "Cód. Full": cod_full.strip(),
                        "Tamanho": tamanho.strip(),
                        "SKU": sku_item.strip(),
                        "MLB Anúncio": mlb_item.strip(),
                        "QTD": qtd_item,
                        "Peso (un)": peso_un,
                        "Custo (un)": custo_un,
                        "Peso Total": peso_total,
                        "Custo Total": custo_total
                    }
                    st.session_state.full_itens.append(novo_item)
                    
                    for k in ["full_cod", "full_tam", "full_sku", "full_mlb", "full_peso", "full_custo", "pesquisa_item_envio"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.session_state.full_qtd = 1
                    st.session_state.sugestao_msg = ""
                    
                    st.rerun()
                elif qtd_item <= 0:
                    st.error("❌ A quantidade a enviar (QTD) tem de ser maior do que zero.")
                else:
                    st.error("❌ Preencha pelo menos o Tamanho e o SKU do produto para o inserir.")

            st.markdown("---")
            st.subheader("📋 Resumo dos Itens do Envio")

            if st.session_state.full_itens:
                df_itens = pd.DataFrame(st.session_state.full_itens)

                df_display = df_itens.copy()
                df_display["Peso (un)"] = df_display["Peso (un)"].apply(lambda x: f"{x:.3f} kg".replace('.', ','))
                df_display["Custo (un)"] = df_display["Custo (un)"].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))
                df_display["Peso Total"] = df_display["Peso Total"].apply(lambda x: f"{x:.3f} kg".replace('.', ','))
                df_display["Custo Total"] = df_display["Custo Total"].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))

                st.dataframe(
                    df_display.style.set_properties(**{
                        'background-color': '#F4F6F9',
                        'color': '#1E1E1E',
                        'border-color': '#E5E7EB',
                        'text-align': 'center'
                    }),
                    use_container_width=True,
                    hide_index=True 
                )

                total_qtd = int(df_itens["QTD"].sum())
                total_peso = float(df_itens["Peso Total"].sum())
                total_custo = float(df_itens["Custo Total"].sum())

                st.markdown("<br>", unsafe_allow_html=True)
                t1, t2, t3 = st.columns(3)
                t1.metric("Quantidade Total (Peças)", total_qtd)
                t2.metric("Peso Total do Envio", f"{total_peso:.3f} kg".replace('.', ','))
                t3.metric("Custo Total do Envio", f"R$ {total_custo:.2f}".replace('.', ','))

            else:
                st.info("Nenhum item adicionado a este envio ainda. Pesquise um produto acima para começar a construir o seu lote.")
                total_qtd = 0
                total_peso = 0.0
                total_custo = 0.0

            st.markdown("<br>", unsafe_allow_html=True)
            c_btn1, c_btn2, c_vazia = st.columns([3, 2, 5])
            
            with c_btn2:
                if st.button("🗑️ Limpar Lista de Itens do Envio"):
                    st.session_state.full_itens = []
                    st.rerun()
                    
            with c_btn1:
                if st.button("💾 Salvar Envio na Nuvem"):
                    n_envio_salvar = st.session_state.get("nome_envio_input", "").strip()
                    c_envio_salvar = st.session_state.get("codigo_envio_input", "").strip()
                    
                    if not st.session_state.full_itens:
                        st.warning("⚠️ Adicione pelo menos um item na lista antes de salvar o envio.")
                    elif n_envio_salvar and c_envio_salvar:
                        try:
                            client = get_sheets_client()
                            doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                            
                            try:
                                sheet = doc.worksheet("Fulfillment")
                            except:
                                sheet = doc.add_worksheet(title="Fulfillment", rows="1000", cols="8")
                                sheet.append_row(["Nome do Envio", "Código do Envio", "Data do Envio", "Data de Entrega", "Quantidade Total", "Peso Total (kg)", "Custo Total (R$)", "Detalhes dos Itens (JSON)"])
                            
                            itens_json = json.dumps(st.session_state.full_itens)
                            
                            valores = [
                                n_envio_salvar,
                                c_envio_salvar,
                                data_envio.strftime("%d/%m/%Y"),
                                data_entrega.strftime("%d/%m/%Y"),
                                total_qtd,
                                f"{total_peso:.3f}".replace('.', ','),
                                f"{total_custo:.2f}".replace('.', ','),
                                itens_json
                            ]
                            
                            # Verifica se o envio já existe para atualizar, senão insere nova linha
                            df_banco = pd.DataFrame(sheet.get_all_records())
                            envios_existentes = []
                            if not df_banco.empty and "Nome do Envio" in df_banco.columns:
                                envios_existentes = df_banco["Nome do Envio"].astype(str).str.strip().tolist()
                                
                            if n_envio_salvar in envios_existentes:
                                idx = envios_existentes.index(n_envio_salvar)
                                sheet.update(range_name=f'A{idx+2}:H{idx+2}', values=[valores], value_input_option="USER_ENTERED")
                                st.success(f"✅ Envio '{n_envio_salvar}' atualizado com sucesso!")
                            else:
                                sheet.append_row(valores, value_input_option="USER_ENTERED")
                                st.success(f"✅ Novo envio '{n_envio_salvar}' salvo com sucesso!")
                            
                            # Limpa os campos após salvar
                            st.session_state.full_itens = []
                            for k in ["nome_envio_input", "codigo_envio_input"]:
                                if k in st.session_state: del st.session_state[k]
                            
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar envio: {e}")
                    else:
                        st.error("❌ Preencha o Nome e o Código do Envio (no topo da página) antes de salvar.")
                        
            # --- LISTAGEM DE PRÓXIMOS ENVIOS ---
            st.markdown("---")
            st.subheader("🗓️ Histórico e Próximos Envios")
            try:
                client = get_sheets_client()
                doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                sheet_historico = doc.worksheet("Fulfillment")
                df_historico = pd.DataFrame(sheet_historico.get_all_records())
                
                if not df_historico.empty:
                    # Mostrar apenas as colunas amigáveis ao utilizador (sem o JSON)
                    colunas_mostrar = ["Nome do Envio", "Código do Envio", "Data do Envio", "Data de Entrega", "Quantidade Total", "Peso Total (kg)", "Custo Total (R$)"]
                    df_historico_mostrar = df_historico[colunas_mostrar].copy()
                    
                    st.dataframe(
                        df_historico_mostrar.style.set_properties(**{
                            'background-color': '#FFFFFF',
                            'color': '#1E1E1E',
                            'border-color': '#E5E7EB'
                        }),
                        use_container_width=True,
                        hide_index=True 
                    )
                else:
                    st.info("Nenhum envio registado na nuvem.")
            except:
                st.info("A base de envios ainda não possui dados. Salve o seu primeiro envio acima!")

        # ==========================================================
        # ABA 2: ESTOQUE FULL (CADASTRO)
        # ==========================================================
        with tab_estoque:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("🏭 Cadastro de Produto no Estoque Full")
            st.markdown("Adicione os seus produtos à lista de inventário abaixo e grave todos de uma vez.")
            
            def puxar_dados_sku_estoque():
                sku_busca = st.session_state.get("est_sku", "").strip()
                if sku_busca:
                    info_prod = buscar_produto_por_sku(sku_busca)
                    if info_prod is not None:
                        st.session_state.est_nome = str(info_prod.get("Produto", ""))
                        st.session_state.est_peso = str(info_prod.get("Peso", ""))

            def calcular_custo_diario_estoque():
                tamanho = st.session_state.get("est_tam", "")
                custo_diario = 0.0
                if tamanho == "Pequeno": custo_diario = 0.007
                elif tamanho == "Médio": custo_diario = 0.015
                elif tamanho == "Grande": custo_diario = 0.050
                elif tamanho == "Extragrande": custo_diario = 0.107
                
                if custo_diario > 0:
                    st.session_state.est_custo_diario = f"{custo_diario:.3f}".replace('.', ',')
                else:
                    st.session_state.est_custo_diario = ""
            
            c_est1, c_est2, c_est_mlb = st.columns([1.5, 1.5, 1.5])
            with c_est1: cod_full_est = st.text_input("Código do Full", key="est_cod", placeholder="Ex: AELM32649")
            with c_est2: sku_est = st.text_input("SKU do Produto", key="est_sku", on_change=puxar_dados_sku_estoque)
            with c_est_mlb: mlb_est = st.text_input("MLB do Anúncio", key="est_mlb", placeholder="Ex: MLB123456789")
                
            c_est3, c_est4 = st.columns([3, 1])
            with c_est3: nome_est = st.text_input("Nome do Produto", key="est_nome", disabled=True)
            with c_est4: peso_est = st.text_input("Peso (un)", key="est_peso", disabled=True)
                
            c_est5, c_est6, c_est7, c_est8 = st.columns([1.5, 1.5, 1, 1])
            with c_est5:
                opcoes_tam_est = ["", "Pequeno", "Médio", "Grande", "Extragrande"]
                tam_est = st.selectbox("Tamanho (ML)", opcoes_tam_est, key="est_tam", on_change=calcular_custo_diario_estoque)
            with c_est6: custo_diario_est = st.text_input("Custo Armaz. Unitário / Dia (R$)", key="est_custo_diario", disabled=True)
            with c_est7: estoque_atual_est = st.number_input("Estoque Atual", min_value=0, step=1, key="est_qtd")
            with c_est8: vendas_30d_est = st.number_input("Vendas (30 dias)", min_value=0, step=1, key="est_vendas_30d")
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("➕ Inserir Item na Lista de Inventário"):
                if cod_full_est.strip() and sku_est.strip():
                    novo_item_est = {
                        "Código do Full": cod_full_est.strip(),
                        "SKU": sku_est.strip(),
                        "MLB Anúncio": mlb_est.strip(),
                        "Produto": st.session_state.get("est_nome", "").strip(),
                        "Peso": st.session_state.get("est_peso", "").strip(),
                        "Tamanho": st.session_state.get("est_tam", "").strip(),
                        "Custo Diário": st.session_state.get("est_custo_diario", "").strip(),
                        "Estoque Atual": st.session_state.get("est_qtd", 0),
                        "Vendas (30 dias)": st.session_state.get("est_vendas_30d", 0)
                    }
                    st.session_state.estoque_itens.append(novo_item_est)
                    
                    for k in ["est_cod", "est_sku", "est_mlb", "est_nome", "est_peso", "est_tam", "est_custo_diario"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    
                    st.session_state.est_qtd = 0
                    st.session_state.est_vendas_30d = 0
                    
                    st.rerun()
                else:
                    st.error("❌ Preencha pelo menos o Código do Full e o SKU para inserir.")

            st.markdown("---")
            st.subheader("📋 Resumo do Inventário a Salvar")
            
            if st.session_state.estoque_itens:
                df_est_itens = pd.DataFrame(st.session_state.estoque_itens)
                st.dataframe(
                    df_est_itens.style.set_properties(**{
                        'background-color': '#F4F6F9',
                        'color': '#1E1E1E',
                        'border-color': '#E5E7EB',
                        'text-align': 'center'
                    }),
                    use_container_width=True,
                    hide_index=True 
                )
                
                total_skus_inseridos = len(df_est_itens)
                total_estoque_inserido = int(df_est_itens["Estoque Atual"].sum())
                
                st.markdown("<br>", unsafe_allow_html=True)
                c_met1, c_met2, c_met3 = st.columns(3)
                c_met1.metric("Total de SKUs na Lista", total_skus_inseridos)
                c_met2.metric("Soma do Estoque Atual (Peças)", total_estoque_inserido)
                
                st.markdown("<br>", unsafe_allow_html=True)
                col_btn_est1, col_btn_est2, col_vazia_est = st.columns([3, 2, 5])
                
                with col_btn_est2:
                    if st.button("🗑️ Limpar Lista de Inventário"):
                        st.session_state.estoque_itens = []
                        st.rerun()
                        
                with col_btn_est1:
                    if st.button("💾 Salvar Inventário na Nuvem"):
                        try:
                            client = get_sheets_client()
                            doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                            
                            try:
                                sheet_est = doc.worksheet("Estoque Full")
                            except:
                                sheet_est = doc.add_worksheet(title="Estoque Full", rows="1000", cols="10")
                                sheet_est.append_row(["Código do Full", "SKU", "MLB Anúncio", "Produto", "Peso", "Tamanho", "Custo Diário", "Estoque Atual", "Vendas (30 dias)", "Data de Atualização"])
                            
                            data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            df_banco = pd.DataFrame(sheet_est.get_all_records())
                            
                            codigos_existentes = []
                            if not df_banco.empty and "Código do Full" in df_banco.columns:
                                codigos_existentes = df_banco["Código do Full"].astype(str).str.strip().tolist()
                            
                            itens_novos = []
                            
                            for item in st.session_state.estoque_itens:
                                valores = [
                                    item["Código do Full"], item["SKU"], item["MLB Anúncio"], item["Produto"],
                                    item["Peso"], item["Tamanho"], item["Custo Diário"], item["Estoque Atual"],
                                    item["Vendas (30 dias)"], data_atual
                                ]
                                
                                if item["Código do Full"] in codigos_existentes:
                                    idx = codigos_existentes.index(item["Código do Full"])
                                    sheet_est.update(range_name=f'A{idx+2}:J{idx+2}', values=[valores], value_input_option="USER_ENTERED")
                                else:
                                    itens_novos.append(valores)
                                    codigos_existentes.append(item["Código do Full"])
                            
                            if itens_novos:
                                sheet_est.append_rows(itens_novos, value_input_option="USER_ENTERED")
                                
                            st.success(f"✅ {len(st.session_state.estoque_itens)} produtos salvos/atualizados com sucesso no Estoque Full!")
                            st.session_state.estoque_itens = []
                            limpar_cache_estoque() # Atualiza pesquisa automática
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar no Estoque Full: {e}")
            else:
                st.info("Nenhum item na lista. Preencha os dados e clique em 'Inserir Item' para construir a sua tabela.")

        # ==========================================================
        # ABA 3: CONSULTA DE ESTOQUE
        # ==========================================================
        with tab_consulta:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📊 Consulta de Estoque Full")
            st.markdown("Visualize todos os produtos atualmente cadastrados no seu inventário do Full.")
            
            if st.button("🔄 Atualizar Dados do Estoque"):
                limpar_cache_estoque() 
                st.rerun()
                
            try:
                client = get_sheets_client()
                doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                sheet_est_view = doc.worksheet("Estoque Full")
                df_est_view = pd.DataFrame(sheet_est_view.get_all_records())
                
                if not df_est_view.empty:
                    st.dataframe(
                        df_est_view.style.set_properties(**{
                            'background-color': '#F4F6F9',
                            'color': '#1E1E1E',
                            'border-color': '#E5E7EB'
                        }),
                        use_container_width=True,
                        hide_index=True 
                    )
                    
                    total_skus = len(df_est_view)
                    total_pecas = df_est_view["Estoque Atual"].sum() if "Estoque Atual" in df_est_view.columns else 0
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    c_res1, c_res2, c_res3 = st.columns(3)
                    c_res1.metric("SKUs Cadastrados no Full", total_skus)
                    c_res2.metric("Total de Peças Físicas", int(total_pecas))
                else:
                    st.info("A sua base de dados do Estoque Full está vazia.")
            except Exception as e:
                st.warning("A aba 'Estoque Full' ainda não possui dados ou não foi criada. Salve o primeiro produto na aba de Cadastro para ativá-la.")