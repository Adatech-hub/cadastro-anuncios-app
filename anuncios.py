import streamlit as st
import pandas as pd
import re
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime  # <--- NOVA BIBLIOTECA PARA PEGAR A DATA/HORA

# 1. CONFIGURAÇÃO DA PÁGINA
URL_LOGO = "https://raw.githubusercontent.com/Adatech-hub/calculadora-mkt/main/Logo.png"

st.set_page_config(
    page_title="Sistema ADATECH",
    page_icon=URL_LOGO,
    layout="wide"
)

# 2. CSS PARA ESTILIZAÇÃO
st.markdown("""
    <style>
    /* Fundo principal do aplicativo */
    .stApp { background-color: #FFFFFF; }
    
    /* Fundo do menu lateral forçado para cinza claro */
    [data-testid="stSidebar"] {
        background-color: #F4F6F9 !important;
    }
    
    /* Cor do texto geral */
    h1, h2, h3, p, span, label { color: #1E1E1E !important; }
    
    /* Estilização dos Botões */
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
    
    /* Cor de foco nos campos de digitação (Verde) */
    div[data-testid="stTextInput"] :focus, div[data-testid="stNumberInput"] :focus {
        border-color: #28a745 !important;
        box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
    }
    
    /* ESTILIZAÇÃO ESPECÍFICA DE CAMPOS BLOQUEADOS (Venda Real e Data) */
    div[data-testid="stTextInput"] input[disabled] {
        background-color: #FFF2CC !important; 
        color: #B8860B !important; 
        -webkit-text-fill-color: #B8860B !important; 
        font-weight: bold;
    }
    
    /* Cor dos números grandes nas métricas */
    [data-testid="stMetricValue"] { color: #1E1E1E !important; }
    
    /* Fundo da Tabela de Detalhamento */
    .stTable { background-color: #F8F9FA; color: #1E1E1E; }
    </style>
""", unsafe_allow_html=True)

# 3. MENU LATERAL (SIDEBAR)
st.sidebar.image(URL_LOGO, width=150)
st.sidebar.title("Navegação")
menu_selecionado = st.sidebar.radio("Selecione a ferramenta:", ["Cadastro de Anúncios", "Curva ABC Meli"])
st.sidebar.markdown("---")

# =====================================================================
# FUNÇÕES DE SUPORTE
# =====================================================================
def get_sheets_client():
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    credenciais_dict = json.loads(st.secrets["google_credentials"])
    return gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(credenciais_dict, scope))

def converter_valor(valor):
    if pd.isna(valor) or valor == "": return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    v_str = str(valor).strip().replace('.', '').replace(',', '.')
    return float(re.sub(r'[^\d\.\-]', '', v_str) or 0)

def formatar_moeda_ui(valor):
    return f"{converter_valor(valor):.2f}".replace('.', ',')

def arredondar_customizado(valor):
    try: return float(Decimal(str(valor)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    except: return 0.0

# =====================================================================
# MÓDULO 1: CADASTRO DE ANÚNCIOS
# =====================================================================
if menu_selecionado == "Cadastro de Anúncios":
    
    # --- FUNÇÕES DE NUVEM ---
    def carregar_repositorio():
        try:
            sheet = get_sheets_client().open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").sheet1
            data = sheet.get_all_records(value_render_option="UNFORMATTED_VALUE")
            # Adicionado o campo Última Atualização
            if not data:
                return pd.DataFrame(columns=["ID do Anúncio", "SKU", "Produto", "Título", "Custo", "Preço Original", "Desconto", "Frete", "Comissão", "Taxa Fixa", "Estorno", "TACOS", "Imposto", "Última Atualização"])
            return pd.DataFrame(data)
        except: return pd.DataFrame(columns=["ID do Anúncio", "SKU", "Produto", "Título", "Custo", "Preço Original", "Desconto", "Frete", "Comissão", "Taxa Fixa", "Estorno", "TACOS", "Imposto", "Última Atualização"])

    def salvar_no_repositorio(dados):
        sheet = get_sheets_client().open_by_url("https://docs.google.com/spreadsheets/d/1Ql-cGoDMDy3KjO4K7RrocwAz-ICYj6QRn9YTLAPMzNQ/edit?gid=0#gid=0").sheet1
        df = carregar_repositorio()
        
        valores_formatados = []
        for valor in dados.values():
            if isinstance(valor, float): valores_formatados.append(f"{valor:.2f}".replace('.', ','))
            else: valores_formatados.append(str(valor))
        
        if not df.empty and "ID do Anúncio" in df.columns and dados["ID do Anúncio"] in df["ID do Anúncio"].values:
            idx = df[df["ID do Anúncio"] == dados["ID do Anúncio"]].index[0]
            # Mudei de M para N para englobar a nova coluna 14
            sheet.update(range_name=f'A{idx+2}:N{idx+2}', values=[valores_formatados], value_input_option="USER_ENTERED")
        else:
            sheet.append_row(valores_formatados, value_input_option="USER_ENTERED")

    # --- CONTROLES DE ESTADO ---
    def processar_calculo_custo():
        texto_atual = st.session_state.custo
        if texto_atual.startswith("=") or any(op in texto_atual for op in ['+', '-', '*', '/']):
            st.session_state.custo = formatar_moeda_ui(texto_atual)

    def resetar_campos():
        campos = ["id_anuncio", "sku", "nome_produto", "titulo"]
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
        st.session_state.ultima_atualizacao = ""
        if "ultimo_id_carregado" in st.session_state: del st.session_state.ultimo_id_carregado
        if "mostrar_sucesso" in st.session_state: del st.session_state.mostrar_sucesso

    if "custo" not in st.session_state: st.session_state.custo = "0,00"
    if "imposto" not in st.session_state: st.session_state.imposto = 7.3
    if "ultima_atualizacao" not in st.session_state: st.session_state.ultima_atualizacao = ""

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
                
                st.session_state.custo = formatar_moeda_ui(row.get("Custo", 0))
                st.session_state.preco = formatar_moeda_ui(row.get("Preço Original", 0))
                st.session_state.frete = formatar_moeda_ui(row.get("Frete", 0))
                st.session_state.taxa = formatar_moeda_ui(row.get("Taxa Fixa", 0))
                st.session_state.estorno = formatar_moeda_ui(row.get("Estorno", 0))
                
                st.session_state.desconto = float(converter_valor(row.get("Desconto", 0)))
                st.session_state.comissao = float(converter_valor(row.get("Comissão", 16.5)))
                st.session_state.tacos = float(converter_valor(row.get("TACOS", 0)))
                st.session_state.imposto = float(converter_valor(row.get("Imposto", 7.3)))
                
                # Resgata a data de atualização
                st.session_state.ultima_atualizacao = str(row.get("Última Atualização", ""))
                
                st.session_state.ultimo_id_carregado = id_atual
                st.session_state.mostrar_sucesso = True
            else:
                st.session_state.ultimo_id_carregado = id_atual
        else:
            st.session_state.ultimo_id_carregado = id_atual

    # --- INTERFACE DE USUÁRIO ---
    col_vazia1, col_conteudo, col_vazia2 = st.columns([1, 2, 1])
    
    with col_conteudo:
        st.title("Cadastro de Anúncios")
        if st.button("🧹 Limpar Dados"):
            resetar_campos()
            st.rerun()

        st.markdown("---")
        st.subheader("📢 Dados do Anúncio")
        
        # DIVIDIDO EM 3 COLUNAS AGORA
        col1, col2, col3 = st.columns([1.5, 3, 1.5])
        with col1: 
            id_input = st.text_input("ID do Anúncio (MLB)", placeholder="Ex: MLB123456789", key="id_anuncio")
        with col2:
            titulo_anuncio = st.text_input("Título do Anúncio", key="titulo")
            if titulo_anuncio: 
                if len(titulo_anuncio) > 60:
                    st.caption(f"⚠️ Caracteres: {len(titulo_anuncio)} (Acima do limite de 60 do ML)")
                else:
                    st.caption(f"Caracteres: {len(titulo_anuncio)}/60") 
        with col3:
            # CAMPO COM A DATA DA ÚLTIMA ATUALIZAÇÃO (Bloqueado)
            st.text_input("Última Atualização", value=st.session_state.get("ultima_atualizacao", ""), disabled=True)

        if st.session_state.get("mostrar_sucesso") and id_input == st.session_state.get("ultimo_id_carregado"):
            st.success("Dados recuperados da nuvem.")

        st.markdown("---")
        st.subheader("📦 Dados do Produto")
        col_sku, col_prod, col_custo = st.columns([1, 2, 1])
        with col_sku: sku_anuncio = st.text_input("SKU do Produto", placeholder="Ex: SKU-12345-X", key="sku")
        with col_prod: nome_produto = st.text_input("Produto", placeholder="Ex: Camiseta Térmica", key="nome_produto")
        with col_custo: st.text_input("Preço de Custo (R$)", key="custo", on_change=processar_calculo_custo)

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
            texto_resultado = f"**Anúncio:** {titulo_anuncio}"
            if sku_anuncio: texto_resultado += f" | **SKU:** {sku_anuncio}"
            st.markdown(texto_resultado)

        col_res_custo, col_res_lucro, col_res_margem = st.columns(3)
        with col_res_custo: st.metric("Custo Total", f"R$ {custo_total_saidas:.2f}")
        with col_res_lucro: st.metric("Lucro Líquido", f"R$ {lucro_liquido:.2f}")
        with col_res_margem: st.metric("Margem", f"{margem_contribuicao:.2f}%")

        if margem_contribuicao < 15: st.error("⚠️ Margem baixa! Verifique o desconto ou os custos.")
        elif 15 <= margem_contribuicao <= 25: st.warning("⚖️ Margem aceitável para giro.")
        else: st.success("✅ Margem excelente para o seu produto!")

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

        st.markdown("---")
        if st.button("💾 Salvar Anúncio na Nuvem"):
            faltantes = [f for f, v in [("ID do Anúncio", id_input), ("Título", titulo_anuncio), ("Preço de Custo", custo_produto)] if not v or (isinstance(v, float) and v <= 0)]
            if not faltantes:
                # GERA A DATA E HORA EXATA DO SALVAMENTO
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                dados_salvar = {
                    "ID do Anúncio": id_input, "SKU": sku_anuncio, "Produto": nome_produto, "Título": titulo_anuncio, 
                    "Custo": custo_produto, "Preço Original": preco_original, "Desconto": porcentagem_desconto, 
                    "Frete": custo_frete, "Comissão": comissao_mkt_porcentagem, "Taxa Fixa": taxa_fixa_venda, 
                    "Estorno": estorno_ml, "TACOS": porcentagem_tacos, "Imposto": imposto_porcentagem,
                    "Última Atualização": agora # NOVA COLUNA SENDO ENVIADA
                }
                try:
                    salvar_no_repositorio(dados_salvar)
                    # Atualiza a interface instantaneamente com a nova data
                    st.session_state.ultima_atualizacao = agora
                    st.success("✅ Dados salvos com sucesso na nuvem!")
                except Exception as e: st.error(f"❌ Erro ao salvar na planilha: {e}")
            else: st.error(f"❌ Erro ao salvar: Preencha os campos obrigatórios: {', '.join(faltantes)}")

# =====================================================================
# MÓDULO 2: CURVA ABC MELI
# =====================================================================
elif menu_selecionado == "Curva ABC Meli":
    st.title("Análise de Curva ABC - Mercado Livre")
    st.write("Faça o upload da sua planilha de vendas exportada do Mercado Livre para classificar o desempenho dos seus anúncios.")
    
    arquivo_excel = st.file_uploader("Arraste ou selecione a planilha (ex: vendas_meli.xlsx)", type=["xlsx", "xls", "csv"])
    
    if arquivo_excel is not None:
        try:
            if arquivo_excel.name.endswith('.csv'):
                df_bruto = pd.read_csv(arquivo_excel, header=None, dtype=str)
            else:
                try:
                    df_bruto = pd.read_excel(arquivo_excel, sheet_name="Relatório", header=None)
                except:
                    df_bruto = pd.read_excel(arquivo_excel, header=None)
            
            linha_cabecalho = 0
            for i in range(min(20, len(df_bruto))):
                valores_linha = [str(val).strip() for val in df_bruto.iloc[i].tolist()]
                if "ID do anúncio" in valores_linha or "Vendas brutas (BRL)" in valores_linha:
                    linha_cabecalho = i
                    break
            
            df = df_bruto.iloc[linha_cabecalho+1:].copy()
            df.columns = [str(col).strip() for col in df_bruto.iloc[linha_cabecalho].tolist()]
            df.reset_index(drop=True, inplace=True)
            
            if "ID do anúncio" not in df.columns or "Vendas brutas (BRL)" not in df.columns:
                st.error("⚠️ As colunas 'ID do anúncio' e/ou 'Vendas brutas (BRL)' não foram encontradas.")
            else:
                def limpar_moeda(valor):
                    if pd.isna(valor): return 0.0
                    if isinstance(valor, (int, float)): return float(valor)
                    
                    v_str = str(valor).strip()
                    if ',' in v_str:
                        v_str = v_str.replace('.', '')
                        v_str = v_str.replace(',', '.')
                    
                    v_str = re.sub(r'[^\d\.\-]', '', v_str)
                    try:
                        return float(v_str)
                    except:
                        return 0.0
                
                df["Vendas brutas (BRL)"] = df["Vendas brutas (BRL)"].apply(limpar_moeda)
                
                agg_funcs = {"Vendas brutas (BRL)": "sum"}
                if "Anúncio" in df.columns: agg_funcs["Anúncio"] = "first"
                elif "Título do anúncio" in df.columns: agg_funcs["Título do anúncio"] = "first"
                elif "Título" in df.columns: agg_funcs["Título"] = "first"
                if "SKU" in df.columns: agg_funcs["SKU"] = "first"
                
                df_agrupado = df.groupby("ID do anúncio").agg(agg_funcs).reset_index()
                
                df_vendas = df_agrupado[df_agrupado["Vendas brutas (BRL)"] > 0].copy()
                df_sem_vendas = df_agrupado[df_agrupado["Vendas brutas (BRL)"] <= 0].copy()
                
                df_vendas = df_vendas.sort_values(by="Vendas brutas (BRL)", ascending=False).reset_index(drop=True)
                valor_total_vendas = df_vendas["Vendas brutas (BRL)"].sum()
                
                if valor_total_vendas > 0:
                    df_vendas["% do Total"] = (df_vendas["Vendas brutas (BRL)"] / valor_total_vendas) * 100
                    df_vendas["% Acumulado"] = df_vendas["% do Total"].cumsum()
                    
                    def classificar_abc(perc_acumulado):
                        if perc_acumulado <= 80: return 'A'
                        elif perc_acumulado <= 95: return 'B'
                        else: return 'C'
                    
                    df_vendas["Curva"] = df_vendas["% Acumulado"].apply(classificar_abc)
                else:
                    df_vendas["% do Total"] = 0.0
                    df_vendas["% Acumulado"] = 0.0
                    df_vendas["Curva"] = "C"

                if not df_sem_vendas.empty:
                    df_sem_vendas["% do Total"] = 0.0
                    df_sem_vendas["% Acumulado"] = 0.0
                    df_sem_vendas["Curva"] = "Sem Vendas"
                    df_final = pd.concat([df_vendas, df_sem_vendas], ignore_index=True)
                else:
                    df_final = df_vendas
                
                colunas_exibicao = ["ID do anúncio"]
                if "Anúncio" in df.columns: colunas_exibicao.append("Anúncio")
                elif "Título do anúncio" in df.columns: colunas_exibicao.append("Título do anúncio")
                elif "Título" in df.columns: colunas_exibicao.append("Título")
                if "SKU" in df.columns: colunas_exibicao.append("SKU")
                
                colunas_exibicao.extend(["Vendas brutas (BRL)", "% do Total", "Curva"])
                df_exibicao = df_final[colunas_exibicao].copy()
                
                df_exibicao_formatado = df_exibicao.copy()
                df_exibicao_formatado["Vendas brutas (BRL)"] = df_exibicao_formatado["Vendas brutas (BRL)"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                df_exibicao_formatado["% do Total"] = df_exibicao_formatado["% do Total"].apply(lambda x: f"{x:.2f}%".replace(".", ","))
                
                st.markdown("---")
                col_res1, col_res2, col_res3 = st.columns(3)
                with col_res1: st.metric("Total Faturado", f"R$ {valor_total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                with col_res2: st.metric("Total de Anúncios", len(df_final))
                with col_res3: st.metric("Anúncios Curva A", len(df_vendas[df_vendas["Curva"] == 'A']))
                
                st.subheader("Resultados da Classificação ABC")
                st.dataframe(df_exibicao_formatado, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao processar o arquivo: {e}")