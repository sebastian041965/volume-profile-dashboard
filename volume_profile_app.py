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
            st.experimental_rerun()
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

ticker = symbol + "=X" if not symbol.endswith("=X") else symbol
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=period_days)
df = yf.download(ticker, start=start_date, end=end_date, interval="1h")
df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
df.columns = df.columns.str.lower()

# 🧱 Tab 1: Perfil de Volumen clásico
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

# 🧱 Tab 2: Trazado Técnico
with tab2:
    st.subheader("📐 Línea entre precios")
    price_a = st.number_input("Precio inicial", value=float(low_price))
    price_b = st.number_input("Precio final", value=float(high_price))
    line_color = st.color_picker("Color", "#FF0000")
    line_width = st.slider("Grosor", 1, 10, 3)
    line_style = st.selectbox("Estilo", ["solid", "dot", "dash", "longdash", "dashdot"])

    fig = go.Figure()
    fig.add_trace(go.Bar(x=volume_profile, y=price_bins[:-1], orientation='h', marker_color='green'))
    fig.add_shape(type="line", x0=0, x1=max(volume_profile), y0=price_a, y1=price_b,
                  line=dict(color=line_color, width=line_width, dash=line_style))
    fig.update_layout(title="Trazado Técnico", yaxis_title="Precio", xaxis_title="Volumen", height=600)
    st.plotly_chart(fig, use_container_width=True)

# 🧱 Tab 3: Dibujo y Anotaciones
with tab3:
    st.subheader("🖌️ Dibujo libre")
    drawing_mode = st.selectbox("Modo", ["line", "freedraw", "transform"])
    stroke_color = st.color_picker("Color del trazo", "#0000FF")
    stroke_width = st.slider("Grosor del trazo", 1, 10, 3)

    canvas_result = st_canvas(
        fill_color="rgba(255,255,255,0.0)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="#ffffff",
        update_streamlit=True,
        height=600,
        drawing_mode=drawing_mode,
        key="canvas"
    )

    if canvas_result.json_data and canvas_result.json_data["objects"]:
        objects = canvas_result.json_data["objects"]
        annotations = [
            {
                "x1": obj.get("x1"), "y1": obj.get("y1"),
                "x2": obj.get("x2"), "y2": obj.get("y2"),
                "color": obj.get("stroke"), "width": obj.get("strokeWidth")
            }
            for obj in objects if obj["type"] == "line"
        ]
        df_annotations = pd.DataFrame(annotations)
        st.dataframe(df_annotations)

        st.download_button("📥 Exportar JSON", data=json.dumps(annotations, indent=2),
                           file_name="anotaciones.json", mime="application/json")
        st.download_button("📥 Exportar CSV", data=df_annotations.to_csv(index=False).encode("utf-8"),
                           file_name="anotaciones.csv", mime="text/csv")

    st.subheader("📂 Cargar anotaciones")
    uploaded_file = st.file_uploader("Archivo JSON", type=["json"])
    if uploaded_file:
        loaded_data = json.load(uploaded_file)
        st.success("✅ Anotaciones cargadas")
        st.dataframe(pd.DataFrame(loaded_data))
        st_canvas(
            fill_color="rgba(255,255,255,0.0)",
            stroke_width=3,
            stroke_color="#000000",
            background_color="#ffffff",
            update_streamlit=True,
            height=600,
            initial_drawing=json.dumps({"objects": loaded_data}),
            drawing_mode="transform",
            key="canvas_loaded"
        )

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

    df_candle = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    df_candle = df_candle[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    df_candle.columns = df_candle.columns.str.lower()

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
    va_high = bins[max(va_indices) + 1]

    st.subheader("📐 Media Móvil Personalizada")
    ma_type = st.selectbox("Tipo de media", ["SMA", "EMA", "WMA"])
    ma_source = st.selectbox("Aplicar sobre", ["close", "open", "high", "low"])
    ma_period = st.slider("Periodo", 1, 100, 20)
    ma_offset = st.slider("Desplazamiento", -50, 50, 0)
    ma_color = st.color_picker("Color de la media", "#FF9900")

    source_series = df_candle[ma_source]

    if ma_type == "SMA":
        ma = source_series.rolling(ma_period).mean()
    elif ma_type == "EMA":
        ma = source_series.ewm(span=ma_period, adjust=False).mean()
    elif ma_type == "WMA":
        weights = np.arange(1, ma_period + 1)
        ma = source_series.rolling(ma_period).apply(lambda x: np.dot(x, weights)/weights.sum(), raw=True)

    ma = ma.shift(ma_offset)

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df_candle.index,
        open=df_candle['open'],
        high=df_candle['high'],
        low=df_candle['low'],
        close=df_candle['close'],
        name="Velas"
    ))

    fig.add_trace(go.Bar(
        x=vp,
        y=bins[:-1],
        orientation='h',
        marker_color=['blue' if i in va_indices else 'rgba(128,128,128,0.3)' for i in range(len(vp))],
        name="Perfil de Volumen"
    ))

    fig.add_trace(go.Scatter(
        x=df_candle.index,
        y=ma,
        mode="lines",
        line=dict(color=ma_color, width=2),
        name=f"{ma_type} ({ma_period})"
    ))

    fig.add_shape(type="line", x0=df_candle.index[0], x1=df_candle.index[-1],
                  y0=poc_price, y1=poc_price,
                  line=dict(color="red", width=2, dash="dash"))

    fig.add_shape(type="line", x0=df_candle.index[0], x1=df_candle.index[-1],
                  y0=va_low, y1=va_low,
                  line=dict(color="blue", width=1, dash="dot"))

    fig.add_shape(type="line", x0=df_candle.index[0], x1=df_candle.index[-1],
                  y0=va_high, y1=va_high,
                  line=dict(color="blue", width=1, dash="dot"))

    fig.update_layout(
        title=f"{symbol} - {selected_interval} con VP y Media Móvil",
        yaxis_title="Precio",
        xaxis_title="Tiempo",
        height=700,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)
