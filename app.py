import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- Configuração da Página ---
st.set_page_config(
    page_title="Analise Trader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilização (Tema Escuro Profissional & Ajustes Visuais) ---
st.markdown("""
    <style>
        /* Fundo principal e fontes */
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        /* Ajuste do cabeçalho */
        header {
            visibility: hidden;
        }
        /* Estilização dos containers/cards */
        div.stMarkdown {
            color: #fafafa;
        }
    </style>
""", unsafe_allow_html=True)

# --- Função de Autenticação Simples ---
def verificar_senha():
    """Retorna True se o usuário inserir a senha correta."""
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if st.session_state.autenticado:
        return True

    # Tela de Login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Analise Trader - Acesso Restrito")
        st.write("Por favor, insira a senha para acessar o sistema.")
        
        senha_input = st.text_input("Senha", type="password")
        SENHA_MESTRE = "trader123" 

        if st.button("Entrar", use_container_width=True):
            if senha_input == SENHA_MESTRE:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta. Tente novamente.")
                
    return False

# --- Execução Principal do App ---
if verificar_senha():
    # --- Barra Lateral (Sidebar) ---
    with st.sidebar:
        st.title("⚙️ Painel de Controle")
        st.markdown("---")
        
        # --- Configuração do Modo Ao Vivo (Live) ---
        st.subheader("📡 Status do Feed")
        modo_ao_vivo = st.toggle("Ativar Atualização Ao Vivo", value=False)
        
        intervalo_segundos = 5
        if modo_ao_vivo:
            intervalo = st.slider("Intervalo (segundos)", min_value=2, max_value=60, value=5, step=1)
            intervalo_segundos = intervalo * 1000
            # Configura o autorefresh para atualizar a página inteira no intervalo definido
            st_autorefresh(interval=intervalo_segundos, key="live_trader_refresh")
            st.success(f"🟢 Ao vivo ativo ({intervalo}s)")
        else:
            st.info("⏸️ Modo manual (atualização sob demanda)")

        st.markdown("---")
        
        # Menu de navegação
        modulo_selecionado = st.radio(
            "Navegação",
            ["Visão Geral", "Gráficos & Análise", "Momentos de Entrada/Saída", "Configurações"]
        )
        
        st.markdown("---")
        if st.button("Sair / Bloquear", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()

    # --- Conteúdo da Página Principal ---
    col_titulo, col_status = st.columns([3, 1])
    with col_titulo:
        st.title("📊 Analise Trader")
    with col_status:
        # Exibe o horário da última atualização na tela
        hora_atual = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"<div style='text-align: right; color: #808495; padding-top: 20px;'>Última sinc: <b>{hora_atual}</b></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    # Exibição condicional baseada no menu
    if modulo_selecionado == "Visão Geral":
        st.subheader("Bem-vindo ao seu ambiente de trading e análise de mercado.")
        
        # Métricas de exemplo (preparadas para receber dados ao vivo)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ativo Principal", "PETR4", "0.45%")
        col2.metric("Tendência Atual", "Alta", "Forte")
        col3.metric("Sinal Ativo", "Aguardando", "-")
        col4.metric("Setup", "Padrão", "Pronto")
        
        st.info("💡 **Sistema pronto para o tempo real:** Use o botão na barra lateral para ligar o feed automático. Quais fontes de dados ou ativos deseja conectar primeiro (ex: Yahoo Finance para ações/fii, criptomoedas, ou dados simulados)?")

    elif modulo_selecionado == "Gráficos & Análise":
        st.subheader("📈 Módulo de Gráficos")
        st.warning("Módulo aguardando implementação dos gráficos em tempo real.")

    elif modulo_selecionado == "Momentos de Entrada/Saída":
        st.subheader("⚡ Gestão de Entradas e Saídas")
        st.warning("Módulo aguardando implementação dos gatilhos operacionais.")

    elif modulo_selecionado == "Configurações":
        st.subheader("🛠️ Configurações do Sistema")
        st.write("Personalize parâmetros de conexão, APIs e preferências de layout.")
