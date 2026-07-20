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
    
    /* Campos Desabilitados - Cor igual ao botão Limpar Dados (Sky Blue 60%) */
    [data-baseweb="input"]:has(input[disabled]),
    [data-baseweb="base-input"]:has(input[disabled]),
    div[data-testid="stTextInput"] input[disabled], 
    div[data-testid="stNumberInput"] input[disabled],
    div[data-testid="stTextArea"] textarea[disabled] {
        background-color: rgba(116, 209, 234, 0.6) !important; 
        color: #250E62 !important; 
        -webkit-text-fill-color: #250E62 !important; 
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
    "Curva ABC Meli"
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
                    expr = expr[:match_mult.start()] + f"({val}/100)" + expr[match_mult.end():]
                else:
                    expr = expr.replace('%', '')
        if expr: return float(eval(expr))
        return 0.0
    except: return None

# =====================================================================
# CACHE DE DADOS (OTIMIZAÇÃO DO GOOGLE SHEETS)
# =====================================================================
@st.cache_data(ttl=15)
def cached_produtos_data():
    try:
        client = get_sheets_client()
        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
        try: sheet = doc.worksheet("Produtos")
        except:
            sheet = doc.add_worksheet(title="Produtos", rows="1000", cols="12")
            sheet.append_row(["SKU", "Produto", "Custo", "Fornecedor", "Data de Referência", "EAN", "NCM", "CST", "Medida", "Peso", "Campo Semântico", "Características/Descrição"], value_input_option="USER_ENTERED")
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

def buscar_produto_por_sku(sku_busca):
    if not sku_busca: return None
    df_p = cached_produtos_data()
    if df_p is not None and not df_p.empty and "SKU" in df_p.columns:
        df_p["SKU"] = df_p["SKU"].astype(str).str.strip()
        res = df_p[df_p["SKU"] == str(sku_busca).strip()]
        if not res.empty: return res.iloc[0]
    return None

# =====================================================================
# MÓDULO: CADASTRO DE FORNECEDOR
# =====================================================================
if menu_selecionado == "Cadastro de Fornecedor":
    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.2, 4, 0.2])
    with col_conteudo:
        st.title("🏭 Cadastro de Fornecedor")
        st.markdown("Registre novos fornecedores para utilizá-los no Cadastro de Produtos e Despesas.")
        
        with st.form("form_novo_fornecedor", clear_on_submit=True):
            st.subheader("Dados do Fornecedor")
            
            c1, c2 = st.columns(2)
            novo_nome_forn = c1.text_input("Nome do Fornecedor *")
            novo_cnpj = c2.text_input("CNPJ")
            
            novo_endereco = st.text_input("Endereço Completo")
            
            c3, c4 = st.columns(2)
            novo_vendedor = c3.text_input("Nome do Vendedor / Contato")
            novo_telefone = c4.text_input("Telefone")
            
            submit_forn = st.form_submit_button("💾 Salvar Fornecedor")
            
            if submit_forn:
                if novo_nome_forn.strip():
                    try:
                        client = get_sheets_client()
                        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                        try: sheet = doc.worksheet("Fornecedores")
                        except:
                            sheet = doc.add_worksheet(title="Fornecedores", rows="1000", cols="5")
                            sheet.append_row(["Nome do Fornecedor", "CNPJ", "Endereço", "Vendedor", "Telefone"])
                        
                        sheet.append_row([
                            novo_nome_forn.strip(), novo_cnpj.strip(), novo_endereco.strip(), 
                            novo_vendedor.strip(), novo_telefone.strip()
                        ])
                        st.success(f"✅ Fornecedor '{novo_nome_forn}' cadastrado com sucesso!")
                        get_lista_fornecedores.clear() 
                    except Exception as e: st.error(f"❌ Erro ao salvar fornecedor: {e}")
                else: st.error("❌ O campo 'Nome do Fornecedor' é obrigatório.")
                    
        st.markdown("---")
        st.subheader("Fornecedores Cadastrados")
        try:
            client = get_sheets_client()
            doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
            sheet_forn = doc.worksheet("Fornecedores")
            df_forn = pd.DataFrame(sheet_forn.get_all_records())
            if not df_forn.empty: st.dataframe(df_forn, use_container_width=True, hide_index=True)
            else: st.info("Nenhum fornecedor registrado ainda.")
        except: st.info("Nenhum fornecedor registrado ainda.")

# =====================================================================
# MÓDULO 1: CADASTRO DE ANÚNCIOS
# =====================================================================
elif menu_selecionado == "Cadastro de Anúncios":
    
    def carregar_repositorio():
        try:
            client = get_sheets_client()
            sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").sheet1
            data = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
            if not data: return pd.DataFrame(columns=["ID do Anúncio", "SKU", "Produto", "Título", "Custo", "Preço Original", "Desconto", "Frete", "Comissão", "Taxa Fixa", "Estorno", "TACOS", "Imposto", "Última Atualização", "Link do Anúncio"])
            return pd.DataFrame(data)
        except: return pd.DataFrame(columns=["ID do Anúncio", "SKU", "Produto", "Título", "Custo", "Preço Original", "Desconto", "Frete", "Comissão", "Taxa Fixa", "Estorno", "TACOS", "Imposto", "Última Atualização", "Link do Anúncio"])

    def salvar_no_repositorio(dados):
        client = get_sheets_client()
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").sheet1
        
        header = ["ID do Anúncio", "SKU", "Produto", "Título", "Custo", "Preço Original", "Desconto", "Frete", "Comissão", "Taxa Fixa", "Estorno", "TACOS", "Imposto", "Última Atualização", "Link do Anúncio"]
        if sheet.col_count < 15: sheet.add_cols(15 - sheet.col_count)
        if sheet.row_values(1) != header: sheet.update(range_name='A1:O1', values=[header], value_input_option="USER_ENTERED")

        df = carregar_repositorio()
        valores_formatados = [f"{v:.2f}".replace('.', ',') if isinstance(v, float) else str(v) for v in dados.values()]
        if not df.empty and "ID do Anúncio" in df.columns and dados["ID do Anúncio"] in df["ID do Anúncio"].values:
            idx = df[df["ID do Anúncio"] == dados["ID do Anúncio"]].index[0]
            sheet.update(range_name=f'A{idx+2}:O{idx+2}', values=[valores_formatados], value_input_option="USER_ENTERED")
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

    def resetar_campos():
        campos = ["id_anuncio", "sku", "nome_produto", "titulo", "ultima_atualizacao", "link_anuncio", "medida", "peso"]
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
        
        # Limpar os dados da Venda Atacado
        if "num_atacado" in st.session_state: st.session_state.num_atacado = 1
        for k in list(st.session_state.keys()):
            if k.startswith("atac_"): del st.session_state[k]
            
        if "ultimo_id_carregado" in st.session_state: del st.session_state.ultimo_id_carregado
        if "mostrar_sucesso" in st.session_state: del st.session_state.mostrar_sucesso
        if "msg_salvo_anuncio" in st.session_state: del st.session_state.msg_salvo_anuncio
        if "id_anuncio_salvo" in st.session_state: del st.session_state.id_anuncio_salvo

    if "custo" not in st.session_state: st.session_state.custo = "0,00"
    if "preco" not in st.session_state: st.session_state.preco = "0,00"
    if "ultima_atualizacao" not in st.session_state: st.session_state.ultima_atualizacao = ""
    if "nome_produto" not in st.session_state: st.session_state.nome_produto = ""
    if "sku" not in st.session_state: st.session_state.sku = ""
    if "link_anuncio" not in st.session_state: st.session_state.link_anuncio = ""
    if "medida" not in st.session_state: st.session_state.medida = ""
    if "peso" not in st.session_state: st.session_state.peso = ""

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
                
                # Busca as medidas e peso no Cadastro Mestre baseado no SKU carregado
                if st.session_state.sku:
                    prod_mestre = buscar_produto_por_sku(st.session_state.sku)
                    if prod_mestre is not None:
                        st.session_state.medida = str(prod_mestre.get("Medida", ""))
                        st.session_state.peso = str(prod_mestre.get("Peso", ""))
                    else:
                        st.session_state.medida = ""
                        st.session_state.peso = ""

                st.session_state.ultimo_id_carregado = id_atual
                st.session_state.mostrar_sucesso = True
            else: st.session_state.ultimo_id_carregado = id_atual
        else: st.session_state.ultimo_id_carregado = id_atual

    col_vazia1, col_conteudo, col_vazia2 = st.columns([0.5, 3, 0.5])
    with col_conteudo:
        st.title("Cadastro de Anúncios")
        if st.button("🧹 Limpar Dados"):
            resetar_campos()
            st.rerun()

        st.markdown("---")
        st.subheader("📢 Dados do Anúncio")
        col1, col2, col3 = st.columns([1.5, 3, 1.5])
        with col1: id_input = st.text_input("ID do Anúncio (MLB)", placeholder="Ex: MLB123456789", key="id_anuncio")
        with col2:
            titulo_anuncio = st.text_input("Título do Anúncio", key="titulo")
            if titulo_anuncio: 
                if len(titulo_anuncio) > 60: st.caption(f"⚠️ Caracteres: {len(titulo_anuncio)} (Acima do limite de 60 do ML)")
                else: st.caption(f"Caracteres: {len(titulo_anuncio)}/60") 
        with col3: st.text_input("Última Atualização", value=st.session_state.ultima_atualizacao, disabled=True)
        
        c_link1, c_link2 = st.columns([4, 1])
        with c_link1:
            link_anuncio_input = st.text_input("🔗 Link do Anúncio", placeholder="Ex: https://produto.mercadolivre.com.br/MLB-...", key="link_anuncio")
        with c_link2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            link_atual = st.session_state.get("link_anuncio", "").strip()
            if link_atual.startswith("http"):
                st.markdown(f'''
                    <a href="{link_atual}" target="_blank" style="display: block; text-align: center; background-color: rgba(116, 209, 234, 0.6); color: #250E62; padding: 7px 0; border-radius: 5px; text-decoration: none; font-weight: bold; border: 1px solid #74D1EA;">
                        Acessar 🔗
                    </a>
                ''', unsafe_allow_html=True)

        if st.session_state.get("mostrar_sucesso") and id_input == st.session_state.get("ultimo_id_carregado"):
            st.info("ℹ️ Dados recuperados da nuvem.")

        st.markdown("---")
        st.subheader("📦 Dados do Produto")
        col_sku, col_prod, col_custo = st.columns([1, 2, 1])
        with col_sku: sku_anuncio = st.text_input("SKU do Produto", placeholder="Ex: SKU-12345-X", key="sku", on_change=puxar_dados_produto_por_sku_trigger)
        with col_prod: nome_produto = st.text_input("Produto", placeholder="Ex: Camiseta Térmica", key="nome_produto")
        with col_custo: st.text_input("Preço de Custo (R$)", key="custo", on_change=processar_calculo_custo)
        
        c_medida, c_peso, c_vazio = st.columns([1, 1, 2])
        with c_medida: st.text_input("Medidas (A x L x C)", key="medida", disabled=True)
        with c_peso: st.text_input("Peso (kg)", key="peso", disabled=True)

        custo_produto = converter_valor(st.session_state.custo)
        st.markdown("---")

        st.subheader("💸 Dados da Venda")
        col_preco, col_desc, col_final = st.columns(3)
        with col_preco: preco_original_str = st.text_input("Preço Original (R$)", key="preco")
        with col_desc: porcentagem_desconto = st.number_input("Desconto (%)", min_value=0.0, max_value=100.0, step=0.1, key="desconto")
        
        preco_original = converter_valor(preco_original_str)
        preco_final = preco_original * (1 - (porcentagem_desconto / 100))
        with col_final: st.text_input("Venda Real (R$)", value=f"{preco_final:.2f}", disabled=True)

        col_comissao, col_frete, col_taxa = st.columns(3)
        with col_comissao: comissao_mkt_porcentagem = st.number_input("Comissão Marketplace (%)", min_value=0.0, step=0.1, key="comissao")
        with col_frete: custo_frete_str = st.text_input("Custo de Frete (R$)", key="frete")
        with col_taxa: taxa_fixa_venda_str = st.text_input("Taxa Fixa por Venda (R$)", key="taxa")

        col_estorno, col_tacos, col_imposto = st.columns(3)
        with col_estorno: estorno_ml_str = st.text_input("Estorno/Bonificação ML (R$)", key="estorno")
        with col_tacos: porcentagem_tacos = st.number_input("Custo de Publicidade TACOS (%)", min_value=0.0, max_value=100.0, step=0.1, key="tacos")
        with col_imposto: imposto_porcentagem = st.number_input("Imposto sobre NF (%)", min_value=0.0, step=0.1, key="imposto")

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
        with col_res_custo: st.metric("Custo Total", f"R$ {custo_total_saidas:.2f}")
        with col_res_lucro: st.metric("Lucro Líquido", f"R$ {lucro_liquido:.2f}")
        with col_res_margem: st.metric("Margem", f"{margem_contribuicao:.2f}%")

        if margem_contribuicao < 15: st.error("⚠️ Margem baixa! Verifique o desconto ou os custos.")
        elif 15 <= margem_contribuicao <= 25: st.warning("⚖️ Margem aceitável para giro.")
        else: st.success("✅ Margem excelente para o seu produto!")

        st.write("### Detalhamento Financeiro")
        denominador = preco_final if preco_final > 0 else 1.0
        df_detalhamento = pd.DataFrame({
            "Descrição": ["Preço Final", "Custo Produto", "Comissão", "Frete", "Imposto", "Taxa Fixa", "TACOS", "Estorno", "LUCRO LÍQUIDO"],
            "Valor": [f"R$ {preco_final:.2f}", f"R$ {custo_produto:.2f}", f"R$ {valor_comissao:.2f}", f"R$ {custo_frete:.2f}", f"R$ {valor_imposto:.2f}", f"R$ {taxa_fixa_venda:.2f}", f"R$ {valor_tacos:.2f}", f"R$ {estorno_ml:.2f}", f"R$ {lucro_liquido:.2f}"],
            "Percentual (%)": [f"{(preco_final/denominador*100):.2f}%", f"{(custo_produto/denominador*100):.2f}%", f"{(valor_comissao/denominador*100):.2f}%", f"{(custo_frete/denominador*100):.2f}%", f"{(valor_imposto/denominador*100):.2f}%", f"{(taxa_fixa_venda/denominador*100):.2f}%", f"{(valor_tacos/denominador*100):.2f}%", f"{(estorno_ml/denominador*100):.2f}%", f"{(lucro_liquido/denominador*100):.2f}%"]
        })
        st.table(df_detalhamento)

        # =========================================================
        # NOVA SECÇÃO: VENDA ATACADO
        # =========================================================
        st.markdown("---")
        st.subheader("📦 Estratégias de Venda no Atacado")
        
        if "num_atacado" not in st.session_state:
            st.session_state.num_atacado = 1
            
        for i in range(st.session_state.num_atacado):
            st.markdown(f"**Opção {i+1}**")
            c_desc, c_unid, c_frete, c_pu, c_vt, c_lucro = st.columns(6)
            
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
            
            # Margem de lucro: Valor total - Frete - Comissão - TACOS - Imposto - Custo do Produto
            lucro_atac = valor_total_atac - frete_atac - comissao_atac - imposto_atac - tacos_atac - custo_total_atac
            margem_atac = (lucro_atac / valor_total_atac * 100) if valor_total_atac > 0 else 0.0
            
            # NOTA DE CORREÇÃO: Removido as 'keys' dos campos desabilitados e adicionados espaços invisíveis (\u200B) 
            # na label para evitar que o Streamlit faça cache de valores mortos!
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
                st.session_state.ultima_atualizacao = data_apenas
                dados_salvar = {
                    "ID do Anúncio": id_input, "SKU": sku_anuncio, "Produto": st.session_state.nome_produto, "Título": titulo_anuncio, 
                    "Custo": custo_produto, "Preço Original": preco_original, "Desconto": porcentagem_desconto, 
                    "Frete": custo_frete, "Comissão": comissao_mkt_porcentagem, "Taxa Fixa": taxa_fixa_venda, 
                    "Estorno": estorno_ml, "TACOS": porcentagem_tacos, "Imposto": imposto_porcentagem, "Última Atualização": data_apenas,
                    "Link do Anúncio": link_anuncio_input
                }
                try:
                    salvar_no_repositorio(dados_salvar)
                    st.session_state.msg_salvo_anuncio = f"✅ Dados do anúncio '{id_input}' salvos com sucesso na nuvem! ({data_apenas})"
                    st.session_state.id_anuncio_salvo = id_input
                    st.rerun()
                except Exception as e: st.error(f"❌ Erro ao salvar na planilha: {e}")
            else: st.error(f"❌ Erro ao salvar: Preencha os campos obrigatórios: {', '.join(faltantes)}")

# =====================================================================
# MÓDULO 2: CADASTRO DE PRODUTO & KITS
# =====================================================================
elif menu_selecionado == "Cadastro de Produto":
    
    if "limpar_produto" not in st.session_state: st.session_state.limpar_produto = False
    if "sucesso_produto" not in st.session_state: st.session_state.sucesso_produto = ""
    if "num_componentes_kit" not in st.session_state: st.session_state.num_componentes_kit = 1
    if "pesquisa_produto" not in st.session_state: st.session_state.pesquisa_produto = ""

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

    if st.session_state.limpar_produto:
        st.session_state.sku_p = ""
        st.session_state.nome_p = ""
        st.session_state.pesquisa_produto = ""
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
        
        st.session_state.sku_kit = ""
        st.session_state.nome_kit = ""
        st.session_state.num_componentes_kit = 1
        for k in list(st.session_state.keys()):
            if k.startswith("kit_sku_") or k.startswith("kit_qtd_") or k.startswith("kit_nome_") or k.startswith("kit_unit_") or k.startswith("kit_tot_"): 
                del st.session_state[k]
        st.session_state.limpar_produto = False

    def salvar_produto_completo(dados):
        df = cached_produtos_data()
        if df is None: df = pd.DataFrame(columns=["SKU", "Produto", "Custo", "Fornecedor", "Data de Referência", "EAN", "NCM", "CST", "Medida", "Peso", "Campo Semântico", "Características/Descrição"])
        client = get_sheets_client()
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").worksheet("Produtos")
        
        header = ["SKU", "Produto", "Custo", "Fornecedor", "Data de Referência", "EAN", "NCM", "CST", "Medida", "Peso", "Campo Semântico", "Características/Descrição"]
        
        if sheet.col_count < 12: sheet.add_cols(12 - sheet.col_count)
        if sheet.row_values(1) != header: sheet.update(range_name='A1:L1', values=[header], value_input_option="USER_ENTERED")
            
        valores_formatados = [
            str(dados.get("SKU", "")).strip(), str(dados.get("Produto", "")).strip(), f"{dados.get('Custo', 0):.2f}".replace('.', ','),
            str(dados.get("Fornecedor", "")).strip(), str(dados.get("Data Ref", "")).strip(), str(dados.get("EAN", "")).strip(),
            str(dados.get("NCM", "")).strip(), str(dados.get("CST", "")).strip(), str(dados.get("Medida", "")).strip(),
            str(dados.get("Peso", "")).strip(), str(dados.get("Campo_Semantico", "")).strip(), str(dados.get("Descricao", "")).strip()
        ]
        
        if not df.empty and "SKU" in df.columns:
            df["SKU"] = df["SKU"].astype(str).str.strip()
            sku_busca = str(dados["SKU"]).strip()
            if sku_busca in df["SKU"].values:
                idx = df[df["SKU"] == sku_busca].index[0]
                sheet.update(range_name=f'A{idx+2}:L{idx+2}', values=[valores_formatados], value_input_option="USER_ENTERED")
                cached_produtos_data.clear() 
                return
        sheet.append_row(valores_formatados, value_input_option="USER_ENTERED")
        cached_produtos_data.clear()

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
            st.selectbox("Selecione um produto cadastrado para carregar os dados:", options=lista_pesquisa, key="pesquisa_produto", on_change=puxar_dados_pesquisa_trigger)
            
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
                if not lista_forns: lista_forns = ["⚠️ Cadastre um fornecedor primeiro no menu lateral"]
                    
                forn_atual = st.session_state.get("forn_p", "")
                idx_forn = lista_forns.index(forn_atual) if forn_atual in lista_forns else 0
                nome_fornecedor = st.selectbox("Nome do Fornecedor", options=lista_forns, index=idx_forn, key="forn_p")

            with c10: 
                custo_p_str = st.text_input("Preço de Custo Padrão (R$)", key="custo_p", on_change=processar_calculo_custo_produto, help="Aceita cálculos! Ex: 10+5*2 ou 21,12-2,5%")
                v_custo_p = converter_valor(st.session_state.custo_p)
            with c11: 
                data_ref_preco = st.text_input("Data de Referência do Preço de Custo", placeholder="Ex: 03/07/2026", key="data_ref_p")
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Novo Campo Semântico e Descrição Expandida
            campo_semantico = st.text_area("Campo Semântico (Palavras-chave SEO para buscas)", key="campo_sem_p", height=100)
            desc_produto = st.text_area("Características, Benefícios e Informações do Produto (Para Anúncios)", key="desc_p", height=400)
                
            st.markdown("---")
            if st.button("💾 Gravar Ficha do Produto", key="btn_prod_simples"):
                if sku_p.strip() and nome_p.strip() and v_custo_p > 0:
                    dados_prod = {
                        "SKU": sku_p, "Produto": nome_p, "Custo": v_custo_p,
                        "Fornecedor": nome_fornecedor if "⚠️" not in nome_fornecedor else "", 
                        "Data Ref": data_ref_preco, "EAN": ean_produto, "NCM": ncm_produto, 
                        "CST": cst_produto, "Medida": medida_produto, "Peso": peso_produto,
                        "Campo_Semantico": campo_semantico,
                        "Descricao": desc_produto
                    }
                    try:
                        salvar_produto_completo(dados_prod)
                        st.session_state.sucesso_produto = f"✅ Produto {sku_p} registrado com sucesso!"
                        st.session_state.limpar_produto = True
                        st.rerun() 
                    except Exception as e: st.error(f"❌ Erro ao gravar produto: {e}")
                else: st.error("❌ Por favor, preencha os campos obrigatórios (SKU, Nome, Preço de Custo).")

        # ABA 2: KIT (PRODUTO COMPOSTO)
        with tab_kit:
            st.markdown("<br>", unsafe_allow_html=True)
            st.write("Crie um produto composto selecionando outros produtos já cadastrados no sistema.")
            
            c1, c2 = st.columns([1, 2])
            with c1: sku_kit = st.text_input("SKU do Kit", key="sku_kit")
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
            
            if st.button("💾 Gravar Kit", key="btn_salvar_kit"):
                if sku_kit.strip() and nome_kit.strip() and custo_total_kit > 0:
                    dados_kit_prod = {
                        "SKU": sku_kit.strip(), "Produto": nome_kit.strip(), "Custo": custo_total_kit,
                        "Fornecedor": "", "Data Ref": "", "EAN": "", "NCM": "", "CST": "", "Medida": "", "Peso": "", "Campo_Semantico": "", "Descricao": ""
                    }
                    try:
                        salvar_produto_completo(dados_kit_prod)
                        
                        client = get_sheets_client()
                        doc = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0")
                        try: sheet_kits = doc.worksheet("Kits_Composicao")
                        except:
                            sheet_kits = doc.add_worksheet(title="Kits_Composicao", rows="1000", cols="6")
                            sheet_kits.append_row(["SKU do Kit", "Nome do Kit", "SKU Componente", "Qtd", "Custo Unitário", "Custo Total"], value_input_option="USER_ENTERED")
                        
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
                            
                        st.session_state.sucesso_produto = f"✅ Kit '{sku_kit}' registado com sucesso no banco de Produtos!"
                        st.session_state.limpar_produto = True
                        st.rerun() 
                    except Exception as e: st.error(f"❌ Erro ao gravar kit: {e}")
                else:
                    st.error("❌ Preencha o SKU do Kit, Nome, e garanta que digitou pelo menos 1 componente válido.")

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
        