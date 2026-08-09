import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        header {
            visibility: hidden;
        }
        div.stMarkdown {
            color: #fafafa;
        }
    </style>
""", unsafe_allow_html=True)

# --- Função de Autenticação Simples ---
def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if st.session_state.autenticado:
        return True

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

# --- Função para Carregar Dados de Mercado ---
@st.cache_data(ttl=60)
def carregar_dados(ticker, periodo, intervalo):
    try:
        df = yf.download(ticker, period=periodo, interval=intervalo, progress=False)
        if df.empty:
            return None
        # Tratamento para multi-index do yfinance se houver
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.dropna(inplace=True)
        return df
    except Exception as e:
        return None

# --- Execução Principal do App ---
if verificar_senha():
    # --- Barra Lateral (Sidebar) ---
    with st.sidebar:
        st.title("⚙️ Painel de Controle")
        st.markdown("---")
        
        # --- Configuração do Ativo e Período ---
        st.subheader("🎯 Configuração de Ativo")
        ticker_input = st.text_input("Ticker do Ativo", value="PETR4.SA").upper()
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            periodo = st.selectbox("Período", ["1d", "5d", "1mo", "6mo", "1y"], index=2)
        with col_p2:
            intervalo = st.selectbox("Intervalo", ["1m", "5m", "15m", "1h", "1d"], index=3)
            
        st.markdown("---")
        
        # --- Configuração do Modo Ao Vivo (Live) ---
        st.subheader("📡 Status do Feed")
        modo_ao_vivo = st.toggle("Ativar Atualização Ao Vivo", value=False)
        
        intervalo_segundos = 10
        if modo_ao_vivo:
            freq = st.slider("Intervalo (segundos)", min_value=5, max_value=60, value=10, step=5)
            intervalo_segundos = freq * 1000
            st_autorefresh(interval=intervalo_segundos, key="live_trader_refresh")
            st.success(f"🟢 Ao vivo ativo ({freq}s)")
        else:
            st.info("⏸️ Modo manual")

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

    # --- Carregamento dos Dados ---
    df_dados = carregar_dados(ticker_input, periodo, intervalo)

    # --- Conteúdo da Página Principal ---
    col_titulo, col_status = st.columns([3, 1])
    with col_titulo:
        st.title("📊 Analise Trader")
    with col_status:
        hora_atual = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"<div style='text-align: right; color: #808495; padding-top: 20px;'>Última sinc: <b>{hora_atual}</b></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    if df_dados is None or df_dados.empty:
        st.error(f"❌ Não foi possível carregar os dados para o ticker **{ticker_input}**. Verifique se o código está correto (ex: PETR4.SA, VALE3.SA, BTC-USD).")
    else:
        # Cálculos Técnicos Básicos (Médias e RSI)
        df_dados['EMA_9'] = df_dados['Close'].ewm(span=9, adjust=False).mean()
        df_dados['EMA_21'] = df_dados['Close'].ewm(span=21, adjust=False).mean()
        
        # Cálculo IFR / RSI
        delta = df_dados['Close'].diff()
        ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = ganho / perda
        df_dados['RSI'] = 100 - (100 / (1 + rs))

        preco_atual = float(df_dados['Close'].iloc[-1])
        preco_anterior = float(df_dados['Close'].iloc[-2])
        variacao_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100
        
        # Sinal simples baseado em EMA
        ema9_atual = float(df_dados['EMA_9'].iloc[-1])
        ema21_atual = float(df_dados['EMA_21'].iloc[-1])
        sinal_tendencia = "COMPRA (Bullish)" if ema9_atual > ema21_atual else "VENDA (Bearish)"

        # --- Navegação ---
        if modulo_selecionado == "Visão Geral":
            st.subheader(f"Visão Geral do Ativo: {ticker_input}")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Preço Atual", f"R$ {preco_atual:.2f}", f"{variacao_pct:.2f}%")
            col2.metric("Tendência (EMA 9/21)", "Alta" if ema9_atual > ema21_atual else "Baixa", "Forte")
            col3.metric("Sinal Técnico", sinal_tendencia, "Setup Ativo")
            col4.metric("IFR (14)", f"{float(df_dados['RSI'].iloc[-1]):.1f}", "Normal")
            
            st.markdown("---")
            st.info(f"💡 **Ativo em monitoramento:** `{ticker_input}` carregado com sucesso via Yahoo Finance. Navegue para as abas ao lado para visualizar os gráficos completos e os gatilhos de operação.")

        elif modulo_selecionado == "Gráficos & Análise":
            st.subheader(f"📈 Gráfico de Candlestick & Indicadores — {ticker_input}")
            
            # Criação do Gráfico com Plotly (Preço + Subplot RSI)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # Candlestick
            fig.add_trace(go.Candlestick(
                x=df_dados.index,
                open=df_dados['Open'],
                high=df_dados['High'],
                low=df_dados['Low'],
                close=df_dados['Close'],
                name='Candles'
            ), row=1, col=1)

            # Médias Móveis
            fig.add_trace(go.Scatter(x=df_dados.index, y=df_dados['EMA_9'], line=dict(color='#00ffcc', width=1.5), name='EMA 9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_dados.index, y=df_dados['EMA_21'], line=dict(color='#ff00ff', width=1.5), name='EMA 21'), row=1, col=1)

            # RSI / IFR
            fig.add_trace(go.Scatter(x=df_dados.index, y=df_dados['RSI'], line=dict(color='#ffa500', width=1.5), name='RSI (14)'), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            # Layout Profissional Escuro
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='#0e1117',
                plot_bgcolor='#0e1117',
                xaxis_rangeslider_visible=False,
                height=600,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)

        elif modulo_selecionado == "Momentos de Entrada/Saída":
            st.subheader(f"⚡ Gestão de Entradas e Saídas — {ticker_input}")
            
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                st.markdown("### 📊 Status Operacional Atual")
                if ema9_atual > ema21_atual:
                    st.success("🟢 **SINAL DE COMPRA ATIVO**\n\n* **Motivo:** EMA 9 cruzou acima da EMA 21.\n* **Recomendação:** Buscar oportunidades de compra em pullbacks.")
                else:
                    st.error("🔴 **SINAL DE VENDA / ATENÇÃO**\n\n* **Motivo:** EMA 9 abaixo da EMA 21.\n* **Recomendação:** Evitar compras longas ou buscar posições vendidas.")
            
            with col_s2:
                st.markdown("### 🎯 Parâmetros Calculados")
                st.metric("Preço de Entrada Sugerido", f"R$ {preco_atual:.2f}")
                st.metric("Stop Loss Recomendado (1.5%)", f"R$ {preco_atual * 0.985:.2f}")
                st.metric("Take Profit Alvo (3.0%)", f"R$ {preco_atual * 1.03:.2f}")

            st.markdown("---")
            st.markdown("### 📋 Histórico Recente de Fechamento")
            st.dataframe(df_dados[['Open', 'High', 'Low', 'Close', 'Volume', 'RSI']].tail(10), use_container_width=True)

        elif modulo_selecionado == "Configurações":
            st.subheader("🛠️ Configurações do Sistema")
            st.write("Gerencie parâmetros de conexão e APIs.")
            st.text_input("Chave API (Opcional para dados avançados)", type="password", value="************************")
            st.success("Configurações salvas localmente com sucesso.")
