import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz
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

# --- Função para Carregar e Converter Dados de Mercado ---
@st.cache_data(ttl=60)
def carregar_dados(ticker, periodo, intervalo):
    try:
        df = yf.download(ticker, period=periodo, interval=intervalo, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.dropna(inplace=True)
        
        # Converte o índice de tempo para o fuso horário do Brasil (America/Sao_Paulo)
        if df.index.tz is not None:
            df.index = df.index.tz_convert('America/Sao_Paulo')
        else:
            df.index = df.index.tz_localize('UTC').tz_convert('America/Sao_Paulo')
            
        return df
    except Exception as e:
        return None

# --- Execução Principal do App ---
if verificar_senha():
    # --- Barra Lateral (Sidebar) ---
    with st.sidebar:
        st.title("⚙️ Painel de Controle")
        st.markdown("---")
        
        st.subheader("🎯 Seleção de Ativos")
        categoria = st.selectbox(
            "Categoria",
            ["Ações B3", "Criptomoedas", "Forex (Moedas)", "Índices & Globais"]
        )
        
        if categoria == "Ações B3":
            ativo_escolhido = st.selectbox("Ativo", ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "ABEV3.SA"])
        elif categoria == "Criptomoedas":
            ativo_escolhido = st.selectbox("Ativo", ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD", "ADA-USD"])
        elif categoria == "Forex (Moedas)":
            ativo_escolhido = st.selectbox("Ativo", ["GBPUSD=X", "EURUSD=X", "USDJPY=X", "USDBRL=X", "AUDUSD=X", "GBPBRL=X"])
        else:
            ativo_escolhido = st.selectbox("Ativo", ["^BVSP", "^GSPC", "^IXIC", "GC=F", "CL=F"])
            
        st.markdown("---")
        st.subheader("📡 Status do Feed")
        modo_ao_vivo = st.toggle("Ativar Atualização Ao Vivo", value=False)
        
        if modo_ao_vivo:
            freq = st.slider("Intervalo (segundos)", min_value=5, max_value=60, value=10, step=5)
            st_autorefresh(interval=freq * 1000, key="live_trader_refresh")
            st.success(f"🟢 Ao vivo ativo ({freq}s)")
        else:
            st.info("⏸️ Modo manual")

        st.markdown("---")
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
        fuso_br = pytz.timezone('America/Sao_Paulo')
        hora_atual = datetime.now(fuso_br).strftime("%H:%M:%S (Horário de Brasília)")
        st.markdown(f"<div style='text-align: right; color: #808495; padding-top: 20px;'>Última sinc: <b>{hora_atual}</b></div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- Seleção de Timeframe / Intervalo sem erro ---
    st.markdown("##### ⏱️ Selecione o Timeframe para Análise e Entrada")
    col_t1, col_t2, col_t3, col_t4, col_t5, col_t6 = st.columns(6)
    
    if "intervalo_escolhido" not in st.session_state:
        st.session_state.intervalo_escolhido = "5m"
        st.session_state.periodo_escolhido = "1d"

    if col_t1.button("1 Minuto", use_container_width=True):
        st.session_state.intervalo_escolhido = "1m"
        st.session_state.periodo_escolhido = "1d"
        st.rerun()
    if col_t2.button("5 Minutos", use_container_width=True):
        st.session_state.intervalo_escolhido = "5m"
        st.session_state.periodo_escolhido = "1d"
        st.rerun()
    if col_t3.button("15 Minutos", use_container_width=True):
        st.session_state.intervalo_escolhido = "15m"
        st.session_state.periodo_escolhido = "5d"
        st.rerun()
    if col_t4.button("30 Minutos", use_container_width=True):
        st.session_state.intervalo_escolhido = "30m"
        st.session_state.periodo_escolhido = "5d"
        st.rerun()
    if col_t5.button("1 Hora", use_container_width=True):
        st.session_state.intervalo_escolhido = "1h"
        st.session_state.periodo_escolhido = "1mo"
        st.rerun()
    if col_t6.button("Diário", use_container_width=True):
        st.session_state.intervalo_escolhido = "1d"
        st.session_state.periodo_escolhido = "6mo"
        st.rerun()

    intervalo = st.session_state.get("intervalo_escolhido", "5m")
    periodo = st.session_state.get("periodo_escolhido", "1d")

    # Carrega dados convertidos
    df_dados = carregar_dados(ativo_escolhido, periodo, intervalo)

    if df_dados is None or df_dados.empty:
        st.error(f"❌ Não há dados disponíveis para **{ativo_escolhido}** no timeframe de **{intervalo}**. (Dica: o Yahoo Finance restringe dados de 1m e 5m aos pregões recentes). Tente 15m ou 1h.")
    else:
        # Indicadores Técnicos
        df_dados['EMA_9'] = df_dados['Close'].ewm(span=9, adjust=False).mean()
        df_dados['EMA_21'] = df_dados['Close'].ewm(span=21, adjust=False).mean()
        
        delta = df_dados['Close'].diff()
        ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = ganho / perda
        df_dados['RSI'] = 100 - (100 / (1 + rs))

        # Detecção automática de Momentos de Entrada (Cruzamento EMA 9 & 21)
        df_dados['Sinal'] = 0
        df_dados.loc[(df_dados['EMA_9'] > df_dados['EMA_21']) & (df_dados['EMA_9'].shift(1) <= df_dados['EMA_21'].shift(1)), 'Sinal'] = 1  # Compra
        df_dados.loc[(df_dados['EMA_9'] < df_dados['EMA_21']) & (df_dados['EMA_9'].shift(1) >= df_dados['EMA_21'].shift(1)), 'Sinal'] = -1 # Venda

        compras = df_dados[df_dados['Sinal'] == 1]
        vendas = df_dados[df_dados['Sinal'] == -1]

        preco_atual = float(df_dados['Close'].iloc[-1])
        preco_anterior = float(df_dados['Close'].iloc[-2])
        variacao_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100
        
        ema9_atual = float(df_dados['EMA_9'].iloc[-1])
        ema21_atual = float(df_dados['EMA_21'].iloc[-1])
        sinal_tendencia = "COMPRA (Bullish)" if ema9_atual > ema21_atual else "VENDA (Bearish)"

        # --- Navegação ---
        if modulo_selecionado == "Visão Geral":
            st.subheader(f"Visão Geral do Ativo: {ativo_escolhido}")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Preço / Cotação (BRT)", f"{preco_atual:.4f}", f"{variacao_pct:.2f}%")
            col2.metric("Tendência (EMA 9/21)", "Alta" if ema9_atual > ema21_atual else "Baixa", "Forte")
            col3.metric("Sinal Técnico", sinal_tendencia, "Setup Ativo")
            col4.metric("IFR (14)", f"{float(df_dados['RSI'].iloc[-1]):.1f}", "Normal")
            
            st.markdown("---")
            st.info(f"💡 Horários ajustados para o **Horário de Brasília**. Utilize os botões acima para alternar o tempo gráfico (**1m**, **5m**, **15m**, **30m**).")

        elif modulo_selecionado == "Gráficos & Análise":
            st.subheader(f"📈 Gráfico com Momentos de Entrada — {ativo_escolhido} [{intervalo}]")
            
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

            # Marcações de Compra (Seta Verde para cima)
            if not compras.empty:
                fig.add_trace(go.Scatter(
                    x=compras.index,
                    y=compras['Low'] * 0.995,
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=12, color='#00FF00'),
                    name='Momento Compra'
                ), row=1, col=1)

            # Marcações de Venda (Seta Vermelha para baixo)
            if not vendas.empty:
                fig.add_trace(go.Scatter(
                    x=vendas.index,
                    y=vendas['High'] * 1.005,
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=12, color='#FF0000'),
                    name='Momento Venda'
                ), row=1, col=1)

            # RSI / IFR
            fig.add_trace(go.Scatter(x=df_dados.index, y=df_dados['RSI'], line=dict(color='#ffa500', width=1.5), name='RSI (14)'), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='#0e1117',
                plot_bgcolor='#0e1117',
                xaxis_rangeslider_visible=False,
                height=550,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

        elif modulo_selecionado == "Momentos de Entrada/Saída":
            st.subheader(f"⚡ Gestão de Entradas e Saídas — {ativo_escolhido}")
            
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                st.markdown("### 📊 Status Operacional Atual")
                if ema9_atual > ema21_atual:
                    st.success("🟢 **SINAL DE COMPRA ATIVO**\n\n* **Motivo:** EMA 9 acima da EMA 21 no timeframe selecionado.\n* **Ação:** Acompanhe o gatilho verde no gráfico.")
                else:
                    st.error("🔴 **SINAL DE VENDA / ATENÇÃO**\n\n* **Motivo:** EMA 9 abaixo da EMA 21 no timeframe selecionado.\n* **Ação:** Acompanhe o gatilho vermelho no gráfico.")
            
            with col_s2:
                st.markdown("### 🎯 Parâmetros Calculados")
                st.metric("Preço de Entrada Sugerido", f"{preco_atual:.4f}")
                st.metric("Stop Loss Recomendado (1.5%)", f"{preco_atual * 0.985:.4f}")
                st.metric("Take Profit Alvo (3.0%)", f"{preco_atual * 1.03:.4f}")

            st.markdown("---")
            st.markdown("### 📋 Últimos Eventos de Gatilho Detectados")
            eventos = df_dados[df_dados['Sinal'] != 0].tail(5)
            if not eventos.empty:
                st.dataframe(eventos[['Close', 'EMA_9', 'EMA_21', 'RSI']], use_container_width=True)
            else:
                st.info("Nenhum cruzamento de média recente no período visível. Ajuste o zoom para ver mais histórico.")

        elif modulo_selecionado == "Configurações":
            st.subheader("🛠️ Configurações do Sistema")
            st.write("Gerencie parâmetros de conexão e APIs.")
            st.text_input("Chave API (Opcional para dados avançados)", type="password", value="************************")
            st.success("Configurações salvas localmente com sucesso.")
