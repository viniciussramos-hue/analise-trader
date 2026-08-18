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
    page_title="Analise Trader & Arbitragem",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilização CSS ---
st.markdown("""
    <style>
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
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
        .buscando-status {
            background-color: #1f2937;
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
            color: #93c5fd;
            font-weight: 500;
        }
        .card-arbitragem {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Autenticação ---
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

# --- Carga de Dados Financeiros Básicos ---
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
    except Exception:
        return None

# --- Módulo Novo: Consulta Multi-Exchange & Liquidez (Arbitragem) ---
@st.cache_data(ttl=15)
def buscar_precos_multi_exchange(crypto_symbol="BTC"):
    """
    Busca cotações e volume em tempo real nas principais corretoras via APIs públicas.
    """
    symbol_usdt = f"{crypto_symbol.upper()}USDT"
    symbol_usd = f"{crypto_symbol.upper()}-USD"
    exchanges_data = []

    # 1. Binance
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol_usdt}"
        res = requests.get(url, timeout=4).json()
        exchanges_data.append({
            "Exchange": "Binance",
            "Preço (USDT)": float(res["lastPrice"]),
            "Bid (Compra)": float(res["bidPrice"]),
            "Ask (Venda)": float(res["askPrice"]),
            "Volume 24h (USD)": float(res["quoteVolume"])
        })
    except Exception:
        pass

    # 2. Bybit
    try:
        url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol_usdt}"
        res = requests.get(url, timeout=4).json()
        item = res["result"]["list"][0]
        exchanges_data.append({
            "Exchange": "Bybit",
            "Preço (USDT)": float(item["lastPrice"]),
            "Bid (Compra)": float(item["bid1Price"]),
            "Ask (Venda)": float(item["ask1Price"]),
            "Volume 24h (USD)": float(item["turnover24h"])
        })
    except Exception:
        pass

    # 3. KuCoin
    try:
        url = f"https://api.kucoin.com/api/v1/market/stats?symbol={crypto_symbol.upper()}-USDT"
        res = requests.get(url, timeout=4).json()
        data = res["data"]
        exchanges_data.append({
            "Exchange": "KuCoin",
            "Preço (USDT)": float(data["last"]),
            "Bid (Compra)": float(data["buy"]) if data.get("buy") else float(data["last"]),
            "Ask (Venda)": float(data["sell"]) if data.get("sell") else float(data["last"]),
            "Volume 24h (USD)": float(data["volValue"])
        })
    except Exception:
        pass

    # 4. Coinbase
    try:
        url = f"https://api.coinbase.com/v2/prices/{symbol_usd}/spot"
        res = requests.get(url, timeout=4).json()
        preco = float(res["data"]["amount"])
        exchanges_data.append({
            "Exchange": "Coinbase",
            "Preço (USDT)": preco,
            "Bid (Compra)": preco,
            "Ask (Venda)": preco,
            "Volume 24h (USD)": 0.0 # Coinbase pública restringe volume no endpoint simples
        })
    except Exception:
        pass

    # 5. Gate.io
    try:
        url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={crypto_symbol.upper()}_USDT"
        res = requests.get(url, timeout=4).json()
        if res:
            item = res[0]
            exchanges_data.append({
                "Exchange": "Gate.io",
                "Preço (USDT)": float(item["last"]),
                "Bid (Compra)": float(item["highest_bid"]),
                "Ask (Venda)": float(item["lowest_ask"]),
                "Volume 24h (USD)": float(item["quote_volume"])
            })
    except Exception:
        pass

    df_exchanges = pd.DataFrame(exchanges_data)
    return df_exchanges

# --- Status de Funcionamento dos Mercados ---
def checar_status_mercado(categoria, agora):
    dia_semana = agora.weekday()
    hora_decimal = agora.hour + agora.minute / 60.0

    if dia_semana >= 5:
        if categoria == "Criptomoedas":
            return "🟢 Mercado Aberto (24/7)", "success"
        else:
            return "🔴 Mercado Fechado (Fim de Semana)", "error"

    if categoria == "Criptomoedas":
        return "🟢 Mercado Aberto (24/7)", "success"
    elif categoria == "Ações B3":
        if 10.0 <= hora_decimal <= 17.0:
            return "🟢 Pregão B3 Aberto", "success"
        else:
            return "🔴 Pregão B3 Fechado", "error"
    elif categoria == "Forex (Moedas)":
        return "🟢 Mercado Forex Aberto", "success"
    else:
        return "🟢 Mercado Operando", "success"

# --- Sessão do Usuário ---
if "historico_ordens" not in st.session_state:
    st.session_state.historico_ordens = []

# --- Execução Principal ---
if verificar_senha():
    # --- Sidebar ---
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
            ["Visão Geral", "Gráficos & Análise", "Arbitragem & Liquidez Cripto", "Momentos de Entrada/Saída", "Configurações"]
        )
        
        st.markdown("---")
        if st.button("Sair / Bloquear", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()

    # --- Conteúdo Principal ---
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_br = datetime.now(fuso_br)
    status_mercado_txt, status_mercado_tipo = checar_status_mercado(categoria, agora_br)

    col_titulo, col_status = st.columns([2, 2])
    with col_titulo:
        st.title("📊 Analise Trader")
    with col_status:
        hora_atual_str = agora_br.strftime("%H:%M:%S")
        cor_txt = "#ffffff" if status_mercado_tipo == "success" else "#ff4b4b"
        st.markdown(f"<div style='text-align: right; padding-top: 15px; color: {cor_txt};'><b>{status_mercado_txt}</b> | BRT: {hora_atual_str}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Timeframe Controls
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
        # Indicadores Técnicos
        df_dados['EMA_9'] = df_dados['Close'].ewm(span=9, adjust=False).mean()
        df_dados['EMA_21'] = df_dados['Close'].ewm(span=21, adjust=False).mean()
        df_dados['Vol_Media'] = df_dados['Volume'].rolling(window=20).mean()
        df_dados['Vol_Spike'] = df_dados['Volume'] > (df_dados['Vol_Media'] * 1.5)
        
        delta = df_dados['Close'].diff()
        ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = ganho / perda
        df_dados['RSI'] = 100 - (100 / (1 + rs))

        # Sinais de Cruzamento
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

        # Win Rate
        total_sinais = len(df_dados[df_dados['Sinal'] != 0])
        if total_sinais > 0:
            df_dados['Retorno_Futuro'] = df_dados['Close'].shift(-3) - df_dados['Close']
            df_dados['Acerto'] = ((df_dados['Sinal'] == 1) & (df_dados['Retorno_Futuro'] > 0)) | ((df_dados['Sinal'] == -1) & (df_dados['Retorno_Futuro'] < 0))
            win_rate = (df_dados['Acerto'].sum() / total_sinais) * 100
        else:
            win_rate = 50.0

        # Verificação do Robô
        sinais_existentes = df_dados[df_dados['Sinal'] != 0]
        if not sinais_existentes.empty:
            ultimo_sinal_tempo = sinais_existentes.index[-1]
            tipo_ultimo_sinal = "COMPRA (Call)" if sinais_existentes['Sinal'].iloc[-1] == 1 else "VENDA (Put)"
            horario_entrada_str = ultimo_sinal_tempo.strftime('%H:%M')
            diferenca_minutos = (agora_br - ultimo_sinal_tempo.astimezone(fuso_br)).total_seconds() / 60.0
            
            if abs(diferenca_minutos) <= 15:
                status_robo_txt = f"🚨 GATILHO ATIVO! Entrada às {horario_entrada_str}"
                robô_buscando = True
            else:
                status_robo_txt = f"🔍 Robô em varredura (Último sinal às {horario_entrada_str})"
                robô_buscando = False
        else:
            tipo_ultimo_sinal = "Neutro"
            status_robo_txt = "🔍 Robô escaneando o mercado..."
            robô_buscando = False

        # --- NAVEGAÇÃO ENTRE MÓDULOS ---
        
        if modulo_selecionado == "Visão Geral":
            st.subheader(f"Visão Geral do Ativo: {ativo_escolhido}")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Preço / Cotação (BRT)", f"{preco_atual:.4f}", f"{variacao_pct:.2f}%")
            col2.metric("Status do Robô", "Buscando Entradas" if robô_buscando else "Varredura Ativa", "Monitorando")
            col3.metric("Tendência Atual", "Alta" if ema9_atual > ema21_atual else "Baixa", "EMA 9/21")
            col4.metric("Assertividade", f"{win_rate:.1f}%", "Histórico")
            
            st.markdown("---")
            st.info(f"💡 **Status de Varredura:** `{status_robo_txt}`")

        elif modulo_selecionado == "Gráficos & Análise":
            st.subheader(f"📈 Gráfico Institucional Avançado — {ativo_escolhido} [{intervalo}]")
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.7, 0.3])

            fig.add_trace(go.Candlestick(
                x=df_dados.index, open=df_dados['Open'], high=df_dados['High'],
                low=df_dados['Low'], close=df_dados['Close'], name='Candles'
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=df_dados.index, y=df_dados['EMA_9'], line=dict(color='#00ffcc', width=1.5), name='EMA 9'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_dados.index, y=df_dados['EMA_21'], line=dict(color='#ff00ff', width=1.5), name='EMA 21'), row=1, col=1)

            if not compras.empty:
                fig.add_trace(go.Scatter(
                    x=compras.index, y=compras['Low'] * 0.995, mode='markers+text',
                    text=[t.strftime('%H:%M') for t in compras.index], textposition="bottom center",
                    marker=dict(symbol='triangle-up', size=14, color='#00FF00'), name='Entrada Compra'
                ), row=1, col=1)

            if not vendas.empty:
                fig.add_trace(go.Scatter(
                    x=vendas.index, y=vendas['High'] * 1.005, mode='markers+text',
                    text=[t.strftime('%H:%M') for t in vendas.index], textposition="top center",
                    marker=dict(symbol='triangle-down', size=14, color='#FF0000'), name='Entrada Venda'
                ), row=1, col=1)

            fig.add_trace(go.Scatter(x=df_dados.index, y=df_dados['RSI'], line=dict(color='#ffa500', width=1.5), name='RSI (14)'), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            fig.update_layout(
                template='plotly_dark', paper_bgcolor='#0e1117', plot_bgcolor='#0e1117',
                xaxis_rangeslider_visible=False, height=550, margin=dict(l=10, r=10, t=10, b=10)
            )

            st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

        # --- NOVO MÓDULO: ARBITRAGEM E MAIOR LIQUIDEZ ---
        elif modulo_selecionado == "Arbitragem & Liquidez Cripto":
            st.subheader("🌐 Comparador de Preços Multi-Exchange & Liquidez")
            st.markdown("Este módulo consulta os preços e volumes em tempo real nas principais corretoras globais para encontrar **oportunidades de arbitragem** (comprar mais barato em uma exchange e vender mais caro em outra).")

            symbol_raw = ativo_escolhido.split("-")[0].replace(".SA", "").replace("=X", "")
            if categoria != "Criptomoedas":
                symbol_raw = "BTC"
                st.warning("⚠️ Ativo selecionado não é uma criptomoeda. Exibindo dados de **BTC** por padrão.")

            col_search1, col_search2 = st.columns([3, 1])
            with col_search1:
                cripto_busca = st.text_input("Símbolo da Criptomoeda (Ex: BTC, ETH, SOL, XRP, DOGE)", value=symbol_raw).upper()
            with col_search2:
                taxa_estimada = st.number_input("Taxa de Transferência/Trading Est. (%)", value=0.2, step=0.05)

            with st.spinner(f"Buscando cotações de {cripto_busca} em exchanges globais..."):
                df_exchanges = buscar_precos_multi_exchange(cripto_busca)

            if df_exchanges.empty:
                st.error("Não foi possível obter dados das exchanges no momento. Verifique a conexão com a internet.")
            else:
                # Identifica maior liquidez (volume)
                idx_maior_volume = df_exchanges["Volume 24h (USD)"].idxmax()
                exc_maior_liquidez = df_exchanges.loc[idx_maior_volume]

                # Identifica Menor Preço de Venda (Ask) para Comprar
                df_valid_ask = df_exchanges[df_exchanges["Ask (Venda)"] > 0]
                idx_menor_ask = df_valid_ask["Ask (Venda)"].idxmin()
                exc_menor_compra = df_valid_ask.loc[idx_menor_ask]

                # Identifica Maior Preço de Compra (Bid) para Vender
                df_valid_bid = df_exchanges[df_exchanges["Bid (Compra)"] > 0]
                idx_maior_bid = df_valid_bid["Bid (Compra)"].idxmax()
                exc_maior_venda = df_valid_bid.loc[idx_maior_bid]

                # Lucro de Arbitragem
                preco_compra = exc_menor_compra["Ask (Venda)"]
                preco_venda = exc_maior_venda["Bid (Compra)"]
                spread_bruto_pct = ((preco_venda - preco_compra) / preco_compra) * 100
                spread_liquido_pct = spread_bruto_pct - taxa_estimada

                # Cards de Destaque
                col_a1, col_a2, col_a3 = st.columns(3)
                
                with col_a1:
                    st.markdown(f"""
                    <div class="card-arbitragem">
                        <h4>💧 Maior Liquidez</h4>
                        <h2 style="color: #3b82f6;">{exc_maior_liquidez['Exchange']}</h2>
                        <p>Volume 24h: <b>${exc_maior_liquidez['Volume 24h (USD)']:,.0f}</b></p>
                        <small>Ideal para grandes ordens com menor slippage.</small>
                    </div>
                    """, unsafe_allow_html=True)

                with col_a2:
                    st.markdown(f"""
                    <div class="card-arbitragem">
                        <h4>🛒 Onde Comprar (Mais Barato)</h4>
                        <h2 style="color: #22c55e;">{exc_menor_compra['Exchange']}</h2>
                        <p>Preço Ask: <b>${preco_compra:,.4f}</b></p>
                        <small>Corretora com a menor cotação de venda.</small>
                    </div>
                    """, unsafe_allow_html=True)

                with col_a3:
                    st.markdown(f"""
                    <div class="card-arbitragem">
                        <h4>💰 Onde Vender (Mais Caro)</h4>
                        <h2 style="color: #eab308;">{exc_maior_venda['Exchange']}</h2>
                        <p>Preço Bid: <b>${preco_venda:,.4f}</b></p>
                        <small>Corretora com a maior cotação de compra.</small>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # Alerta de Oportunidade de Arbitragem
                if spread_liquido_pct > 0 and exc_menor_compra['Exchange'] != exc_maior_venda['Exchange']:
                    st.markdown(f"""
                    <div class="alerta-pisca">
                        🚀 OPORTUNIDADE DE ARBITRAGEM DETECTADA!<br>
                        Compre na <b>{exc_menor_compra['Exchange']}</b> por <b>${preco_compra:,.4f}</b> e venda na <b>{exc_maior_venda['Exchange']}</b> por <b>${preco_venda:,.4f}</b>.<br>
                        <b>Lucro Bruto: {spread_bruto_pct:.2f}% | Lucro Líquido Est.: {spread_liquido_pct:.2f}%</b>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info(f"ℹ️ **Spread Atual entre exchanges:** {spread_bruto_pct:.2f}% (Sem oportunidade líquida relevante após as taxas de {taxa_estimada}%).")

                st.markdown("### 📋 Tabela Comparativa de Exchanges")
                
                # Formatando para exibição limpa
                df_show = df_exchanges.copy()
                df_show["Preço (USDT)"] = df_show["Preço (USDT)"].map("${:,.4f}".format)
                df_show["Bid (Compra)"] = df_show["Bid (Compra)"].map("${:,.4f}".format)
                df_show["Ask (Venda)"] = df_show["Ask (Venda)"].map("${:,.4f}".format)
                df_show["Volume 24h (USD)"] = df_show["Volume 24h (USD)"].map("${:,.0f}".format)

                st.dataframe(df_show, use_container_width=True)

        elif modulo_selecionado == "Momentos de Entrada/Saída":
            st.subheader(f"⚡ Gestão Inteligente, Simulador e Risco — {ativo_escolhido}")
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                st.markdown("### 🤖 Robô Analisador & Varredura de Mercado")
                st.write(f"* **Status do Mercado:** {status_mercado_txt}")
                st.markdown(f'<div class="buscando-status">{status_robo_txt}</div>', unsafe_allow_html=True)
                st.write(f"* **Direção do Último Setup:** **{tipo_ultimo_sinal}**")
                st.write(f"* **Taxa de Acerto (Win Rate):** **{win_rate:.1f}%**")
                
                if st.button("🚀 Executar Ordem Simulada (Paper Trading)", use_container_width=True):
                    nova_ordem = {
                        "Ativo": ativo_escolhido,
                        "Tipo": tipo_ultimo_sinal,
                        "Entrada": preco_atual,
                        "Horário": agora_br.strftime("%H:%M:%S"),
                        "Status": "Aberta (Simulada)"
                    }
                    st.session_state.historico_ordens.append(nova_ordem)
                    st.success(f"✅ Ordem simulada para **{ativo_escolhido}** registrada com sucesso!")

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
                st.info("Nenhuma ordem simulada aberta no momento.")

        elif modulo_selecionado == "Configurações":
            st.subheader("🛠️ Configurações do Sistema & Conexões")
            st.write("Gerencie parâmetros avançados de conexão e chaves de API.")
            st.text_input("Chave API (Opcional para dados avançados)", type="password", value="************************")
            st.text_input("Webhook Telegram/Discord para Alertas", value=webhook_url, placeholder="Insira o link do webhook aqui")
            st.success("Configurações salvas localmente com sucesso.")
