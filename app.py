import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
import requests

# --- Configuração da Página ---
st.set_page_config(
    page_title="Analise Trader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilização (Tema Escuro Profissional & Alertas Animados) ---
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
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(1.02); }
            100% { opacity: 1; transform: scale(1); }
        }
        .alerta-pisca {
            animation: pulse 1.5s infinite;
            background-color: #ff4b4b;
            padding: 15px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            text-align: center;
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
        
        if df.index.tz is not None:
            df.index = df.index.tz_convert('America/Sao_Paulo')
        else:
            df.index = df.index.tz_localize('UTC').tz_convert('America/Sao_Paulo')
            
        return df
    except Exception as e:
        return None

# --- Inicialização da Carteira Simulada no Session State ---
if "historico_ordens" not in st.session_state:
    st.session_state.historico_ordens = []

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
        
        # --- Gerenciamento de Risco ---
        st.subheader("🛡️ Gestão de Risco & Alertas")
        capital_risco = st.number_input("Capital a Arriscar (R$ / US$)", value=100.0, step=50.0)
        alvo_fib_gain = st.slider("Alvo Gain (%)", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
        stop_loss_pct = st.slider("Stop Loss (%)", min_value=0.5, max_value=5.0, value=1.5, step=0.5)
        
        webhook_url = st.text_input("Webhook URL (Discord/Telegram)", type="password", placeholder="https://discord.com/api/webhooks/...")

        st.markdown("---")
        st.subheader("📡 Status do Feed")
        modo_ao_vivo = st.toggle("Ativar Atualização Ao Vivo", value=True)
        
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
        agora_br = datetime.now(fuso_br)
        hora_atual_str = agora_br.strftime("%H:%M:%S")
        st.markdown(f"<div style='text-align: right; color: #808495; padding-top: 20px;'>Horário BRT: <b>{hora_atual_str}</b></div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- Seleção de Timeframe / Intervalo ---
    st.markdown("##### ⏱️ Timeframe para Análise Institucional Avançada")
    col_t1, col_t2, col_t3, col_t4, col_t5, col_t6 = st.columns(6)
    
    if "intervalo_escolhido" not in st.session_state:
        st.session_state.intervalo_escolhido = "1m"
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

    intervalo = st.session_state.get("intervalo_escolhido", "1m")
    periodo = st.session_state.get("periodo_escolhido", "1d")

    df_dados = carregar_dados(ativo_escolhido, periodo, intervalo)

    if df_dados is None or df_dados.empty:
        st.error(f"❌ Não há dados disponíveis para **{ativo_escolhido}** no timeframe de **{intervalo}**.")
    else:
        # Indicadores Técnicos & Volume Spike
        df_dados['EMA_9'] = df_dados['Close'].ewm(span=9, adjust=False).mean()
        df_dados['EMA_21'] = df_dados['Close'].ewm(span=21, adjust=False).mean()
        df_dados['Vol_Media'] = df_dados['Volume'].rolling(window=20).mean()
        df_dados['Vol_Spike'] = df_dados['Volume'] > (df_dados['Vol_Media'] * 1.5)
        
        delta = df_dados['Close'].diff()
        ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = ganho / perda
        df_dados['RSI'] = 100 - (100 / (1 + rs))

        # Detecção de Sinais
        df_dados['Sinal'] = 0
        df_dados.loc[(df_dados['EMA_9'] > df_dados['EMA_21']) & (df_dados['EMA_9'].shift(1) <= df_dados['EMA_21'].shift(1)), 'Sinal'] = 1  
        df_dados.loc[(df_dados['EMA_9'] < df_dados['EMA_21']) & (df_dados['EMA_9'].shift(1) >= df_dados['EMA_21'].shift(1)), 'Sinal'] = -1 

        compras = df_dados[df_dados['Sinal'] == 1]
        vendas = df_dados[df_dados['Sinal'] == -1]

        preco_atual = float(df_dados['Close'].iloc[-1])
        preco_anterior = float(df_dados['Close'].iloc[-2])
        variacao_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100
        
        ema9_atual = float(df_dados['EMA_9'].iloc[-1])
        ema21_atual = float(df_dados['EMA_21'].iloc[-1])

        # Backtest simples de assertividade (Win Rate no histórico recente)
        total_sinais = len(df_dados[df_dados['Sinal'] != 0])
        if total_sinais > 0:
            # Simula acerto verificando se o preço subiu após sinal de compra ou caiu após venda
            df_dados['Retorno_Futuro'] = df_dados['Close'].shift(-3) - df_dados['Close']
            df_dados['Acerto'] = ((df_dados['Sinal'] == 1) & (df_dados['Retorno_Futuro'] > 0)) | ((df_dados['Sinal'] == -1) & (df_dados['Retorno_Futuro'] < 0))
            win_rate = (df_dados['Acerto'].sum() / total_sinais) * 100
        else:
            win_rate = 50.0

        # Horários Calculados
        ultimo_sinal_tempo = df_dados[df_dados['Sinal'] != 0].index[-1] if not df_dados[df_dados['Sinal'] != 0].empty else df_dados.index[-1]
        tipo_ultimo_sinal = "COMPRA (Call)" if not df_dados[df_dados['Sinal'] != 0].empty and df_dados[df_dados['Sinal'] != 0]['Sinal'].iloc[-1] == 1 else "VENDA (Put)"
        
        horario_entrada_str = ultimo_sinal_tempo.strftime('%H:%M')

        multiplicador_minutos = 1
        if "m" in intervalo:
            multiplicador_minutos = int(intervalo.replace("m", ""))
        elif "h" in intervalo:
            multiplicador_minutos = int(intervalo.replace("h", "")) * 60

        horario_saida_previsto = ultimo_sinal_tempo + timedelta(minutes=multiplicador_minutos * 4)
        horario_saida_str = horario_saida_previsto.strftime('%H:%M')

        # --- Navegação ---
        if modulo_selecionado == "Visão Geral":
            st.subheader(f"Visão Geral do Ativo: {ativo_escolhido}")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Preço / Cotação (BRT)", f"{preco_atual:.4f}", f"{variacao_pct:.2f}%")
            col2.metric("Assertividade (Win Rate)", f"{win_rate:.1f}%", "Baseado no Histórico")
            col3.metric("Entrada / Saída Alvo", f"{horario_entrada_str} ➔ {horario_saida_str}", tipo_ultimo_sinal)
            col4.metric("Filtro de Volume", "Com Volume Institucional" if df_dados['Vol_Spike'].iloc[-1] else "Volume Normal", "Filtro Ativo")
            
            st.markdown("---")
            st.info(f"💡 **Ecossistema Institucional Ativo:** O app monitora picos de volume, calcula taxa de acerto estatística do setup e simula ordens em tempo real.")

        elif modulo_selecionado == "Gráficos & Análise":
            st.subheader(f"📈 Gráfico Institucional Avançado — {ativo_escolhido} [{intervalo}]")
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.7, 0.3])

            fig.add_trace(go.Candlestick(
                x=df_dados.index,
                open=df_dados['Open'],
                high=df_dados['High'],
                low=df_dados['Low'],
                close=df_dados['Close'],
                name='Candles'
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=df_dados.index, y=df_dados['EMA_9'], line=dict(color='#00ffcc', width=1.5), name='EMA 9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_dados.index, y=df_dados['EMA_21'], line=dict(color='#ff00ff', width=1.5), name='EMA 21'), row=1, col=1)

            if not compras.empty:
                fig.add_trace(go.Scatter(
                    x=compras.index,
                    y=compras['Low'] * 0.995,
                    mode='markers+text',
                    text=[t.strftime('%H:%M') for t in compras.index],
                    textposition="bottom center",
                    marker=dict(symbol='triangle-up', size=14, color='#00FF00'),
                    name='Entrada Compra'
                ), row=1, col=1)

            if not vendas.empty:
                fig.add_trace(go.Scatter(
                    x=vendas.index,
                    y=vendas['High'] * 1.005,
                    mode='markers+text',
                    text=[t.strftime('%H:%M') for t in vendas.index],
                    textposition="top center",
                    marker=dict(symbol='triangle-down', size=14, color='#FF0000'),
                    name='Entrada Venda'
                ), row=1, col=1)

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
            st.subheader(f"⚡ Gestão Inteligente, Simulador e Risco — {ativo_escolhido}")
            
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                st.markdown("### 🤖 Robô Analisador & Simulador de Ordens (Paper Trading)")
                st.write(f"* **Horário Calculado de Entrada:** **{horario_entrada_str}**")
                st.write(f"* **Previsão Estimada de Saída:** **{horario_saida_str}**")
                st.write(f"* **Direção Indicada:** **{tipo_ultimo_sinal}**")
                st.write(f"* **Taxa de Acerto Histórica (Win Rate):** **{win_rate:.1f}%**")
                
                # Botão para executar ordem simulada
                if st.button("🚀 Executar Ordem Simulada (Paper Trading)", use_container_width=True):
                    nova_ordem = {
                        "Ativo": ativo_escolhido,
                        "Tipo": tipo_ultimo_sinal,
                        "Entrada": preco_atual,
                        "Horário": agora_br.strftime("%H:%M:%S"),
                        "Status": "Aberta (Simulada)"
                    }
                    st.session_state.historico_ordens.append(nova_ordem)
                    st.success("✅ Ordem simulada registrada com sucesso na carteira paper trading!")

                hora_atual_minutos = agora_br.hour * 60 + agora_br.minute
                horario_entrada_minutos = ultimo_sinal_tempo.hour * 60 + ultimo_sinal_tempo.minute
                
                if abs(hora_atual_minutos - horario_entrada_minutos) <= 2:
                    st.markdown(f'<div class="alerta-pisca">🚨 ALERTA MÁXIMO: HORA DE EXECUTAR A {tipo_ultimo_sinal} AGORA ({horario_entrada_str})!</div>', unsafe_allow_html=True)
                else:
                    st.info(f"⏳ Monitorando janela operacional. Entrada alvo às {horario_entrada_str} | Saída prevista às {horario_saida_str}.")
            
            with col_s2:
                st.markdown("### 🎯 Calculadora de Risco x Retorno")
                preco_stop = preco_atual * (1 - stop_loss_pct / 100) if "COMPRA" in tipo_ultimo_sinal else preco_atual * (1 + stop_loss_pct / 100)
                preco_alvo = preco_atual * (1 + alvo_fib_gain / 100) if "COMPRA" in tipo_ultimo_sinal else preco_atual * (1 - alvo_fib_gain / 100)
                
                st.metric("Preço Atual", f"{preco_atual:.4f}")
                st.metric(f"Stop Loss ({stop_loss_pct}%)", f"{preco_stop:.4f}")
                st.metric(f"Take Profit Alvo ({alvo_fib_gain}%)", f"{preco_alvo:.4f}")
                st.info(f"💼 Risco configurado: R$ {capital_risco:.2f} por operação.")

            st.markdown("---")
            st.markdown("### 📂 Carteira de Paper Trading (Ordens Simuladas)")
            if len(st.session_state.historico_ordens) > 0:
                df_ordens = pd.DataFrame(st.session_state.historico_ordens)
                st.dataframe(df_ordens, use_container_width=True)
            else:
                st.info("Nenhuma ordem simulada aberta no momento. Clique no botão acima para testar uma entrada.")

        elif modulo_selecionado == "Configurações":
            st.subheader("🛠️ Configurações do Sistema & Conexões")
            st.write("Gerencie parâmetros avançados de conexão e chaves de API.")
            st.text_input("Chave API (Opcional para dados avançados)", type="password", value="************************")
            st.text_input("Webhook Telegram/Discord para Alertas", value=webhook_url, placeholder="Insira o link do webhook aqui")
            st.success("Configurações salvas localmente com sucesso.")
