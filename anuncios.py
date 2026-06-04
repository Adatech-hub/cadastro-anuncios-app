import streamlit as st
import pandas as pd
import re
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from decimal import Decimal, ROUND_HALF_UP

# 1. CONFIGURAÇÃO DA PÁGINA
URL_LOGO = "https://raw.githubusercontent.com/Adatech-hub/calculadora-mkt/main/Logo.png"

st.set_page_config(
    page_title="Cadastro de Anúncios",
    page_icon=URL_LOGO,
    layout="centered"
)

# 2. CSS PARA ESTILIZAÇÃO
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    h1, h2, h3, p, span, label { color: #1E1E1E !important; }
    div.stButton > button {
        color: #1E1E1E !important; 
        background-color: #F0F2F6 !important; 
        border: 1px solid #1E1E1E !important; 
        border-radius: 5px;
        width: 100%;
        font-weight: bold;
    }
    div.stButton > button:hover {
        color: #FFFFFF !important;
        background-color: #1E1E1E !important;
    }
    div[data-testid="stTextInput"] :focus {
        border-color: #28a745 !important;
        box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
    }
    [data-testid="stMetricValue"] { color: #1E1E1E !important; }
    .stTable { background-color: #F8F9FA; color: #1E1E1E; }
    </style>
""", unsafe_allow_html=True)

# 3. FUNÇÕES DE CONEXÃO E REPOSITÓRIO
def get_sheets_client():
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    
    credenciais_dict = json.loads(st.secrets["google_credentials"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credenciais_dict, scope)
    return gspread.authorize(creds)

def carregar_repositorio():
    try:
        client = get_sheets_client()
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").sheet1
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=["ID do Anúncio", "SKU", "Produto", "Título", "Custo", "Preço Original", "Desconto", "Frete", "Comissão", "Taxa Fixa", "Estorno", "TACOS", "Imposto"])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Aviso: Não foi possível carregar a planilha. Erro: {e}")
        return pd.DataFrame(columns=["ID do Anúncio", "SKU", "Produto", "Título", "Custo", "Preço Original", "Desconto", "Frete", "Comissão", "Taxa Fixa", "Estorno", "TACOS", "Imposto"])

def salvar_no_repositorio(dados):
    client = get_sheets_client()
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").sheet1
    
    df = carregar_repositorio()
    
    if not df.empty and "ID do Anúncio" in df.columns and dados["ID do Anúncio"] in df["ID do Anúncio"].values:
        idx = df[df["ID do Anúncio"] == dados["ID do Anúncio"]].index[0]
        sheet.update(range_name=f'A{idx+2}:M{idx+2}', values=[list(dados.values())])
    else:
        sheet.append_row(list(dados.values()))

# 4. FUNÇÕES DE SUPORTE E INICIALIZAÇÃO
def converter_valor(valor_str):
    try:
        if isinstance(valor_str, (float, int)): 
            return float(valor_str)
        valor_str = str(valor_str).strip()
        if valor_str.startswith("="):
            valor_str = valor_str[1:]
        valor_str = valor_str.replace(',', '.')
        if any(op in valor_str for op in ['+', '-', '*', '/']):
            expressao_limpa = re.sub(r'[^0-9.+\-*/()]', '', valor_str)
            return float(eval(expressao_limpa))
        return float(valor_str)
    except:
        return 0.0

def arredondar_customizado(valor):
    try:
        return float(Decimal(str(valor)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    except:
        return 0.0

def processar_calculo_custo():
    texto_atual = st.session_state.custo
    if texto_atual.startswith("=") or any(op in texto_atual for op in ['+', '-', '*', '/']):
        resultado = converter_valor(texto_atual)
        st.session_state.custo = f"{resultado:.2f}".replace('.', ',')

def resetar_campos():
    st.session_state.id_anuncio = ""
    st.session_state.sku = ""  
    st.session_state.nome_produto = ""  
    st.session_state.titulo = ""
    st.session_state.custo = "0,00"
    st.session_state.preco = "0,00"
    st.session_state.desconto = 0.0
    st.session_state.frete = "0,00"
    st.session_state.comissao = 16.5
    st.session_state.taxa = "6,00"
    st.session_state.estorno = "0,00"
    st.session_state.tacos = 0.0
    st.session_state.imposto = 7.3
    if "ultimo_id_carregado" in st.session_state:
        del st.session_state.ultimo_id_carregado
    if "mostrar_sucesso" in st.session_state:
        del st.session_state.mostrar_sucesso

if "custo" not in st.session_state:
    st.session_state.custo = "0,00"
if "imposto" not in st.session_state:
    st.session_state.imposto = 7.3

# 5. LÓGICA DE RECUPERAÇÃO DE DADOS (ANTES DA INTERFACE)
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
            st.session_state.custo = str(row.get("Custo", "0,00")).replace('.', ',')
            st.session_state.preco = str(row.get("Preço Original", "0,00")).replace('.', ',')
            st.session_state.desconto = float(row.get("Desconto", 0.0))
            st.session_state.frete = str(row.get("Frete", "0,00")).replace('.', ',')
            st.session_state.comissao = float(row.get("Comissão", 16.5))
            st.session_state.taxa = str(row.get("Taxa Fixa", "6,00")).replace('.', ',')
            st.session_state.estorno = str(row.get("Estorno", "0,00")).replace('.', ',')
            st.session_state.tacos = float(row.get("TACOS", 0.0))
            st.session_state.imposto = float(row.get("Imposto", 7.3))
            
            st.session_state.ultimo_id_carregado = id_atual
            st.session_state.mostrar_sucesso = True
        else:
            st.session_state.ultimo_id_carregado = id_atual
    else:
        st.session_state.ultimo_id_carregado = id_atual

# 6. TOPO DA PÁGINA
st.image(URL_LOGO, width=120)
st.title("Cadastro de Anúncios")

if st.button("🧹 Limpar Dados"):
    resetar_campos()
    st.rerun()

st.markdown("---")

# 7. BLOCO 1: DADOS DO ANÚNCIO
st.subheader("📢 Dados do Anúncio")

col1, col2 = st.columns([1, 2])

with col1:
    id_input = st.text_input("ID do Anúncio (MLB)", placeholder="Ex: MLB123456789", key="id_anuncio")

with col2:
    titulo_anuncio = st.text_input("Título do Anúncio", max_chars=60, key="titulo")
    if titulo_anuncio:
        st.caption(f"Caracteres: {len(titulo_anuncio)}/60") 

if st.session_state.get("mostrar_sucesso") and id_input == st.session_state.get("ultimo_id_carregado"):
    st.success("Dados recuperados da nuvem.")

# 8. BLOCO NOVO: DADOS DO PRODUTO
st.markdown("---")
st.subheader("📦 Dados do Produto")

col_sku, col_prod, col_custo = st.columns([1, 2, 1])

with col_sku:
    sku_anuncio = st.text_input("SKU do Produto", placeholder="Ex: SKU-12345-X", key="sku")

with col_prod:
    nome_produto = st.text_input("Produto", placeholder="Ex: Camiseta Térmica", key="nome_produto")

with col_custo:
    st.text_input("Preço de Custo (R$)", key="custo", on_change=processar_calculo_custo)

custo_produto = converter_valor(st.session_state.custo)
st.caption("Quanto você pagou pelo produto. **Dica:** Aceita fórmulas (ex: `=29,15*2` ou `15+10,5`). Pressione **Enter** para calcular.")
st.markdown("---")

# 9. BLOCO 2: DADOS DA VENDA
st.subheader("💸 Dados da Venda")

col_preco, col_desc, col_final = st.columns(3)

with col_preco:
    preco_original_str = st.text_input("Preço Original (R$)", key="preco")

with col_desc:
    porcentagem_desconto = st.number_input("Desconto (%)", min_value=0.0, max_value=100.0, step=0.1, key="desconto")

preco_original = converter_valor(preco_original_str)
preco_final = preco_original * (1 - (porcentagem_desconto / 100))

with col_final:
    st.text_input("Venda Real (R$)", value=f"{preco_final:.2f}", disabled=True)

col_comissao, col_frete, col_taxa = st.columns(3)

with col_comissao:
    comissao_mkt_porcentagem = st.number_input("Comissão Marketplace (%)", min_value=0.0, step=0.1, key="comissao")

with col_frete:
    custo_frete_str = st.text_input("Custo de Frete (R$)", key="frete")

with col_taxa:
    taxa_fixa_venda_str = st.text_input("Taxa Fixa por Venda (R$)", key="taxa")

col_estorno, col_tacos, col_imposto = st.columns(3)

with col_estorno:
    estorno_ml_str = st.text_input("Estorno/Bonificação ML (R$)", key="estorno")

with col_tacos:
    porcentagem_tacos = st.number_input("Custo de Publicidade TACOS (%)", min_value=0.0, max_value=100.0, step=0.1, key="tacos")

with col_imposto:
    imposto_porcentagem = st.number_input("Imposto sobre NF (%)", min_value=0.0, step=0.1, key="imposto")

# 10. PROCESSAMENTO MATEMÁTICO
custo_frete = converter_valor(custo_frete_str)
taxa_fixa_venda = converter_valor(taxa_fixa_venda_str)
estorno_ml = converter_valor(estorno_ml_str)

valor_comissao = preco_final * (comissao_mkt_porcentagem / 100)
valor_imposto = preco_final * (imposto_porcentagem / 100)
valor_tacos = preco_final * (porcentagem_tacos / 100)

custo_total_saidas = custo_produto + custo_frete + valor_comissao + valor_imposto + taxa_fixa_venda + valor_tacos
lucro_liquido = (preco_final + estorno_ml) - custo_total_saidas
margem_contribuicao = arredondar_customizado((lucro_liquido / preco_final) * 100) if preco_final > 0 else 0.0

# 11. BLOCO 3: RESULTADOS E ANÁLISE
st.divider()
st.subheader("📈 Resultados")

if titulo_anuncio:
    texto_resultado = f"**Anúncio:** {titulo_anuncio}"
    if sku_anuncio:
        texto_resultado += f" | **SKU:** {sku_anuncio}"
    if nome_produto:
        texto_resultado += f" | **Produto:** {nome_produto}"
    st.markdown(texto_resultado)

col_res_custo, col_res_lucro, col_res_margem = st.columns(3)

with col_res_custo:
    st.metric("Custo Total", f"R$ {custo_total_saidas:.2f}")

with col_res_lucro:
    st.metric("Lucro Líquido", f"R$ {lucro_liquido:.2f}")

with col_res_margem:
    st.metric("Margem", f"{margem_contribuicao:.2f}%")

if margem_contribuicao < 15:
    st.error("⚠️ Margem baixa! Verifique o desconto ou os custos.")
elif 15 <= margem_contribuicao <= 25:
    st.warning("⚖️ Margem aceitável para giro.")
else:
    st.success("✅ Margem excelente para o seu produto!")

st.write("### Detalhamento Financeiro")

denominador = preco_final if preco_final > 0 else 1.0
pct_preco = arredondar_customizado((preco_final / denominador) * 100)
pct_custo = arredondar_customizado((custo_produto / denominador) * 100)
pct_comissao = arredondar_customizado((valor_comissao / denominador) * 100)
pct_frete = arredondar_customizado((custo_frete / denominador) * 100)
pct_imposto = arredondar_customizado((valor_imposto / denominador) * 100)
pct_taxa = arredondar_customizado((taxa_fixa_venda / denominador) * 100)
pct_tacos = arredondar_customizado((valor_tacos / denominador) * 100)
pct_estorno = arredondar_customizado((estorno_ml / denominador) * 100)
pct_lucro = arredondar_customizado((lucro_liquido / denominador) * 100)

df_detalhamento = pd.DataFrame({
    "Descrição": ["Preço Final (Venda Real)", "Custo Produto", "Comissão", "Frete", "Imposto", "Taxa Fixa", "Publicidade (TACOS)", "Estorno", "LUCRO LÍQUIDO"],
    "Valor": [
        f"R$ {preco_final:.2f}", f"R$ {custo_produto:.2f}", f"R$ {valor_comissao:.2f}",
        f"R$ {custo_frete:.2f}", f"R$ {valor_imposto:.2f}", f"R$ {taxa_fixa_venda:.2f}",
        f"R$ {valor_tacos:.2f}", f"R$ {estorno_ml:.2f}", f"R$ {lucro_liquido:.2f}"
    ],
    "Percentual (%)": [
        f"{pct_preco:.2f}%", f"{pct_custo:.2f}%", f"{pct_comissao:.2f}%",
        f"{pct_frete:.2f}%", f"{pct_imposto:.2f}%", f"{pct_taxa:.2f}%",
        f"{pct_tacos:.2f}%", f"{pct_estorno:.2f}%", f"{pct_lucro:.2f}%"
    ]
})

st.table(df_detalhamento)

# 12. BOTÃO SALVAR
st.markdown("---")
if st.button("💾 Salvar Anúncio na Nuvem"):
    faltantes = []
    if not id_input: faltantes.append("ID do Anúncio")
    if not titulo_anuncio: faltantes.append("Título")
    if custo_produto <= 0: faltantes.append("Preço de Custo")

    if not faltantes:
        dados_salvar = {
            "ID do Anúncio": id_input, 
            "SKU": sku_anuncio, 
            "Produto": nome_produto,  
            "Título": titulo_anuncio, 
            "Custo": custo_produto, 
            "Preço Original": preco_original, 
            "Desconto": porcentagem_desconto, 
            "Frete": custo_frete, 
            "Comissão": comissao_mkt_porcentagem, 
            "Taxa Fixa": taxa_fixa_venda, 
            "Estorno": estorno_ml, 
            "TACOS": porcentagem_tacos,
            "Imposto": imposto_porcentagem
        }
        try:
            salvar_no_repositorio(dados_salvar)
            st.success(f"✅ Dados salvos com sucesso na nuvem!")
        except Exception as e:
            st.error(f"❌ Erro ao salvar na planilha: {e}")
    else:
        st.error(f"❌ Erro ao salvar: Preencha os campos obrigatórios: {', '.join(faltantes)}")