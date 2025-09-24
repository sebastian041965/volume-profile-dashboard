import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from streamlit_drawable_canvas import st_canvas
from datetime import datetime, timedelta
import yfinance as yf
import json

st.set_page_config(page_title="Volume Profile Dashboard", layout="wide")

# 🔐 Autenticación
USERS = {
    "sebastian": "clave123",
    "analista": "trading2025",
    "admin": "adminpass"
}
SESSION_DURATION_MINUTES = 30

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "auth_time" not in st.session_state:
    st.session_state.auth_time = None

if st.session_state.authenticated and st.session_state.auth_time:
    elapsed = datetime.now() - st.session_state.auth_time
    if elapsed > timedelta(minutes=SESSION_DURATION_MINUTES):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.auth_time = None
        st.warning("⏳ Tu sesión ha caducado. Vuelve a iniciar sesión.")

if not st.session_state.authenticated:
    st.title("🔐 Acceso restringido")
    username_input = st.text_input("Usuario")
    password_input = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if username_input in USERS and password_input == USERS[username_input]:
            st.session_state.authenticated = True
            st.session_state.username = username_input
            st.session_state.auth_time = datetime.now()
            st.success(f"✅ Bienvenido, {username_input}")
            st.stop()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

# 🧭 Parámetros comunes
st.title("📊 Volume Profile Dashboard")
st.sidebar.markdown(f"👤 Sesión activa: **{st.session_state.username}**")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.auth_time = None
    st.experimental_rerun()

symbol = st.sidebar.text_input("Símbolo (ej. BTCUSDT o EURUSD)", value="EURUSD")
period_days = st.sidebar.slider("Días a analizar", 1, 30, 10)
resolution = st.sidebar.slider("Resolución", 100, 1000, 500)

tab1, tab2, tab3, tab4 = st.tabs([
    "Perfil de Volumen",
    "Trazado Técnico",
    "Dibujo y Anotaciones",
    "Gráfico de Velas + VP Dinámico"
])

end_date = datetime.utcnow()
start_date = end_date - timedelta(days=period_days)

# 🔍 Detección automática de fuente
def detect_data_source(symbol):
    crypto_suffixes = ["USDT", "BTC", "ETH", "BNB", "SOL"]
    if any(symbol.endswith(suffix) for suffix in crypto_suffixes):
        return "binance"
    return "yahoo"

def get_data(symbol, interval, start, end):
    source = detect_data_source(symbol)
    if source == "binance":
        from binance.client import Client
        client = Client()
        binance_interval = {
            "1m": Client.KLINE_INTERVAL_1MINUTE,
            "5m": Client.KLINE_INTERVAL_5MINUTE,
            "15m": Client.KLINE_INTERVAL_15MINUTE,
            "1h": Client.KLINE_INTERVAL_1HOUR,
            "4h": Client.KLINE_INTERVAL_4HOUR,
            "1d": Client.KLINE_INTERVAL_1DAY,
            "1wk": Client.KLINE_INTERVAL_1WEEK,
            "1mo": Client.KLINE_INTERVAL_1MONTH
        }
        klines = client.get_historical_klines(symbol, binance_interval[interval], start.strftime("%d %b %Y %H:%M:%S"), end.strftime("%d %b %Y %H:%M:%S"))
        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
    else:
        ticker = symbol + "=X" if not symbol.endswith("=X") else symbol
        df = yf.download(ticker, start=start, end=end, interval=interval)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[1].lower() if isinstance(col, tuple) else col.lower() for col in df.columns]
        else:
            df.columns = [str(col).lower() for col in df.columns]
        df = df[["open", "high", "low", "close", "volume"]].dropna()
    return df

# 🧱 Tab 1: Perfil de Volumen clásico
df = get_data(symbol, "1h", start_date, end_date)
if df.empty:
    st.warning("⚠️ No se encontraron datos para el símbolo ingresado.")
    st.stop()

low_price = df['low'].min()
high_price = df['high'].max()
price_step = (high_price - low_price) / resolution
price_bins = np.arange(low_price, high_price + price_step, price_step)
volume_profile = np.zeros(len(price_bins) - 1)

for _, row in df.iterrows():
    mask = (price_bins[:-1] < row['high']) & (price_bins[1:] > row['low'])
    volume_profile[mask] += row['volume'] / mask.sum() if mask.sum() > 0 else 0

vpoc_index = np.argmax(volume_profile)
vpoc_price = (price_bins[vpoc_index] + price_bins[vpoc_index + 1]) / 2
margin = max(high_price - vpoc_price, vpoc_price - low_price)
support_price = vpoc_price - margin
resistance_price = vpoc_price + margin

with tab1:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(volume_profile, price_bins[:-1], color="green", label="Perfil de Volumen")
    ax.axhline(vpoc_price, color="yellow", linestyle="--", label="VPOC")
    ax.axhline(low_price, color="blue", linestyle=":", label="Low")
    ax.axhline(high_price, color="blue", linestyle=":", label="High")
    ax.axhline(support_price, color="red", linestyle="--", label="Soporte")
    ax.axhline(resistance_price, color="lime", linestyle="--", label="Resistencia")
    ax.set_xlabel("Volumen")
    ax.set_ylabel("Precio")
    ax.set_title(f"Perfil de Volumen para {symbol}")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

# 🧱 Tab 2 y Tab 3 se mantienen igual (puedes copiar desde tu versión actual)

# 🧱 Tab 4: Velas + VP Dinámico + Media Móvil
with tab4:
    st.subheader("📈 Velas sincronizadas con Perfil de Volumen")

    interval_map = {
        "1 minuto": "1m",
        "5 minutos": "5m",
        "15 minutos": "15m",
        "1 hora": "1h",
        "4 horas": "4h",
        "Diario": "1d",
        "Semanal": "1wk",
        "Mensual": "1mo"
    }
    selected_interval = st.selectbox("Temporalidad", list(interval_map.keys()), index=4)
    interval = interval_map[selected_interval]

    df_candle = get_data(symbol, interval, start_date, end_date)
    if df_candle.empty:
        st.warning("⚠️ No se encontraron datos para esta temporalidad.")
        st.stop()

    low = df_candle['low'].min()
    high = df_candle['high'].max()
    bins = np.linspace(low, high, 60)
    vp = np.zeros(len(bins) - 1)

    for _, row in df_candle.iterrows():
        mask = (bins[:-1] < row['high']) & (bins[1:] > row['low'])
        vp[mask] += row['volume'] / mask.sum() if mask.sum() > 0 else 0

    poc_index = np.argmax(vp)
    poc_price = (bins[poc_index] + bins[poc_index + 1]) / 2

    total_vol = vp.sum()
    va_target = total_vol * 0.68
    sorted_indices = np.argsort(vp)[::-1]
    va_sum = 0
    va_indices = []

    for i in sorted_indices:
        va_sum += vp[i]
        va_indices.append(i)
        if va_sum >= va_target:
            break

    va_low = bins[min(va_indices)]
    va_high = bins[max(va_indices) + ]

