import streamlit as st
import pandas as pd
from datetime import datetime
from database.connection import SessionLocal
from database.models import Usuario, Produto, Supermercado, RegistroPreco
from streamlit_autorefresh import st_autorefresh
st.set_page_config(page_title="Monitor de Preços", layout="wide")

# ================= AUTO-REFRESH =================
# Atualiza o dashboard automaticamente
st_autorefresh(interval=200000, key="data_refresh")

# ================= ESTADO DA SESSÃO =================
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = ""
if "monitorando" not in st.session_state:
    st.session_state.monitorando = False

# ================= FUNÇÕES DE BANCO DE DADOS =================
def autenticar_usuario(email, senha):
    session = SessionLocal()
    user = session.query(Usuario).filter(Usuario.email == email, Usuario.senha == senha).first()
    session.close()
    return user

def logout():
    st.session_state.logado = False
    st.session_state.usuario_id = None
    st.session_state.minha_lista = []
    st.rerun()

def criar_usuario(nome, email, senha):
    session = SessionLocal()
    if session.query(Usuario).filter(Usuario.email == email).first():
        session.close()
        return False
    novo_user = Usuario(nome=nome, email=email, senha=senha)
    session.add(novo_user)
    session.commit()
    session.close()
    return True

def get_produtos_disponiveis():
    session = SessionLocal()
    produtos = [p.nome for p in session.query(Produto).all()]
    session.close()
    return produtos

def get_historico_precos(produto_nome):
    """Busca os preços com precisão de minutos para o gráfico rastrear o Scraper em tempo real"""
    session = SessionLocal()
    produto = session.query(Produto).filter(Produto.nome == produto_nome).first()
    
    if not produto:
        session.close()
        return pd.DataFrame()

    registros = session.query(
        RegistroPreco.data_coleta,
        RegistroPreco.valor,
        Supermercado.nome.label("mercado")
    ).join(Supermercado, RegistroPreco.supermercado_id == Supermercado.id)\
     .filter(RegistroPreco.produto_id == produto.id)\
     .order_by(RegistroPreco.data_coleta).all()
    session.close()
    
    if not registros:
        return pd.DataFrame()
    
    df = pd.DataFrame(registros, columns=["Data", "Valor", "Supermercado"])
    
    df["Data"] = pd.to_datetime(df["Data"]).dt.round('5min')
    
    df_pivot = df.pivot_table(index="Data", columns="Supermercado", values="Valor", aggfunc="mean")
    return df_pivot

# ================= TELA 1: LOGIN / CADASTRO =================
if not st.session_state.logado:
    st.markdown("<h1 style='text-align: center;'>🛒 MONITOR DE PREÇOS - NATAL/RN</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;'>Sistema Inteligente de Comparação e Monitoramento</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("") 
        aba_login, aba_cadastro = st.tabs(["🔐 Login", "📝 Criar Conta"])
        
        with aba_login:
            email_login = st.text_input("E-mail:", key="email_l", placeholder="seu@email.com")
            senha_login = st.text_input("Senha:", type="password", key="senha_l")
            if st.button("Entrar", use_container_width=True):
                user = autenticar_usuario(email_login, senha_login)
                if user:
                    st.session_state.logado = True
                    st.session_state.usuario_nome = user.nome
                    st.rerun()
                else:
                    st.error("E-mail ou senha incorretos.")
                    
        with aba_cadastro:
            nome_cad = st.text_input("Nome Completo:", key="nome_c")
            email_cad = st.text_input("E-mail:", key="email_c")
            senha_cad = st.text_input("Senha:", type="password", key="senha_c")
            if st.button("Cadastrar Usuário", use_container_width=True):
                if nome_cad and email_cad and senha_cad:
                    if criar_usuario(nome_cad, email_cad, senha_cad):
                        st.success("Conta criada! Volte para a aba de Login para entrar.")
                    else:
                        st.error("Este e-mail já está cadastrado.")
                else:
                    st.warning("Preencha todos os campos.")

# ================= TELA 2: DASHBOARD =================
else:
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.write(f"### Olá, {st.session_state.usuario_nome}! 👋")
        
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False
            st.rerun()
            
        st.divider()
        
        produtos_banco = get_produtos_disponiveis()
        
        lista_compras = st.multiselect(
            "🛒 Sua Lista de Compras (Máx. 10):",
            options=produtos_banco,
            default=produtos_banco[:3] if len(produtos_banco) >= 3 else produtos_banco,
            max_selections=10
        )
        
        localidade = st.selectbox("📍 Localidade:", ["Natal/RN"])
        btn_comparar = st.button("Comparar Preços 🔍", type="primary", use_container_width=True)

    # --- ÁREA PRINCIPAL ---
    st.title("📊 Painel de Monitoramento de Preços")

    if not btn_comparar:
        st.info("👈 Monte sua lista de compras na barra lateral e clique em **Comparar Preços** para gerar o relatório.")
        st.write("⏱️ *O painel está monitorando o banco de dados em tempo real...*")
    else:
        if not lista_compras:
            st.warning("Por favor, selecione pelo menos um produto na barra lateral.")
        else:
            st.subheader(f"Relatório Comparativo para: {localidade}")
            
            # --- CALCULADORA MATEMÁTICA REAL ---
            total_por_mercado = {}
            for prod in lista_compras:
                df_prod = get_historico_precos(prod)
                if not df_prod.empty:
                    # Pega o preço mais recente de cada mercado (ffill garante que não pega campos vazios)
                    ultimos_precos = df_prod.ffill().iloc[-1].to_dict()
                    for mercado, preco in ultimos_precos.items():
                        if pd.notna(preco):
                            total_por_mercado[mercado] = total_por_mercado.get(mercado, 0) + preco

            # Processa os resultados da calculadora
            if total_por_mercado:
                mercado_vencedor = min(total_por_mercado, key=total_por_mercado.get)
                valor_vencedor = total_por_mercado[mercado_vencedor]
                valor_mais_caro = max(total_por_mercado.values())
                economia_real = valor_mais_caro - valor_vencedor
            else:
                mercado_vencedor = "Aguardando dados..."
                valor_vencedor = 0.0
                economia_real = 0.0

            st.markdown("### 🏆 Vencedor do Dia")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Mercado Mais Barato", value=mercado_vencedor)
            with col2:
                st.metric(label="Total da Lista", value=f"R$ {valor_vencedor:.2f}")
            with col3:
                st.metric(label="Economia Estimada", value=f"R$ {economia_real:.2f}", delta="Redução de custo")
            
            st.divider()
            
            st.markdown("### 📈 Histórico de Preços em Tempo Real")
            st.write("Os gráficos abaixos acompanham as extrações do robô instantaneamente.")
            
            abas = st.tabs(lista_compras)
            
            for index, produto_selecionado in enumerate(lista_compras):
                with abas[index]:
                    df_historico = get_historico_precos(produto_selecionado)
                    
                    if not df_historico.empty:
                        st.line_chart(df_historico, use_container_width=True)
                    else:
                        st.warning(f"Sem dados históricos suficientes para: {produto_selecionado}")