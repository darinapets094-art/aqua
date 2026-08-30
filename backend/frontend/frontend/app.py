"""
app.py - Frontend на Streamlit
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="АКВА-СТРАЖ",
    page_icon="🌊",
    layout="wide"
)

st.title("🌊 АКВА-СТРАЖ")
st.subheader("Система мониторинга качества воды")

# Боковая панель
st.sidebar.header("⚙️ Настройки")
station_id = st.sidebar.text_input("ID станции", "STATION_001")
refresh_interval = st.sidebar.slider("Интервал обновления (сек)", 5, 60, 30)

# Функции для работы с API
def get_station_status(station_id: str):
    try:
        response = requests.get(f"{API_URL}/api/stations/{station_id}/status")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def send_sensor_data(data: dict):
    try:
        response = requests.post(f"{API_URL}/api/sensors/data", json=data)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_history(station_id: str):
    try:
        response = requests.get(f"{API_URL}/api/analytics/history/{station_id}")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

# Главная панель
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Станция", station_id)

with col2:
    status = get_station_status(station_id)
    if status:
        st.metric("Индекс риска", f"{status['risk_index']:.3f}")
    else:
        st.metric("Индекс риска", "N/A")

with col3:
    st.metric("Статус", "🟢 Online" if status else "🔴 Offline")

# Карточки параметров
if status:
    st.markdown("---")
    st.subheader(" Текущие показатели")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    reading = status['last_reading']
    
    with col1:
        do_value = reading['dissolved_oxygen']
        st.metric(" Кислород", f"{do_value:.2f} мг/л", 
                 delta=f"{do_value - 8.0:.2f}")
        if do_value < 6.0:
            st.error("⚠️ Критически низко!")
    
    with col2:
        ph_value = reading['ph']
        st.metric("⚗️ pH", f"{ph_value:.2f}",
                 delta=f"{ph_value - 7.5:.2f}")
    
    with col3:
        temp_value = reading['temperature']
        st.metric("🌡️ Температура", f"{temp_value:.2f}°C",
                 delta=f"{temp_value - 12.0:.2f}")
    
    with col4:
        ec_value = reading['conductivity']
        st.metric("⚡ Электропроводность", f"{ec_value:.2f} мСм/см")
    
    with col5:
        turb_value = reading['turbidity']
        st.metric("🌫️ Мутность", f"{turb_value:.2f} NTU")
    
    # График истории
    st.markdown("---")
    st.subheader(" История показателей")
    
    history = get_history(station_id)
    if history:
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig = px.line(
            df, 
            x='timestamp', 
            y=['dissolved_oxygen', 'ph', 'temperature'],
            title="Динамика параметров",
            labels={'value': 'Значение', 'timestamp': 'Время'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # График индекса риска
        fig2 = px.line(
            df,
            x='timestamp',
            y='risk_index',
            title="Индекс риска",
            labels={'risk_index': 'Индекс риска', 'timestamp': 'Время'}
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Нет данных для отображения")

# Симулятор данных
st.markdown("---")
st.subheader(" Симулятор данных")

col1, col2 = st.columns(2)

with col1:
    st.write("Отправить тестовые данные:")
    
    do_sim = st.number_input("Кислород (мг/л)", value=7.5, min_value=0.0, max_value=20.0)
    ph_sim = st.number_input("pH", value=7.4, min_value=0.0, max_value=14.0)
    temp_sim = st.number_input("Температура (°C)", value=12.0, min_value=-10.0, max_value=40.0)
    ec_sim = st.number_input("Электропроводность (мСм/см)", value=5.0, min_value=0.0)
    turb_sim = st.number_input("Мутность (NTU)", value=10.0, min_value=0.0)
    
    if st.button("📤 Отправить данные"):
        data = {
            "station_id": station_id,
            "dissolved_oxygen": do_sim,
            "ph": ph_sim,
            "temperature": temp_sim,
            "conductivity": ec_sim,
            "turbidity": turb_sim
        }
        result = send_sensor_data(data)
        if result:
            st.success(f"✅ Данные отправлены! Индекс риска: {result['risk_index']}")
            if result.get('anomaly_detected'):
                st.warning("️ Обнаружена аномалия!")
        else:
            st.error("❌ Ошибка отправки данных")

with col2:
    st.write("Информация о системе:")
    st.info("""
    **Нормативные значения:**
    - Кислород: 8.0 мг/л (мин. 6.0)
    - pH: 7.5 (диапазон 6.5-8.5)
    - Температура: 12°C (оптимум для лосося)
    - Электропроводность: 5.0 мСм/см
    - Мутность: 10 NTU (макс. 50)
    """)

# Автообновление
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Обновить данные"):
    st.rerun()
