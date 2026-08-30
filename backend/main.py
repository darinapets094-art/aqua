"""
main.py - Backend сервер на FastAPI
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from datetime import datetime
import pickle
import numpy as np
from pathlib import Path

app = FastAPI(title="АКВА-СТРАЖ API", version="1.0.0")

# Pydantic модели
class SensorData(BaseModel):
    station_id: str
    dissolved_oxygen: float
    ph: float
    temperature: float
    conductivity: float
    turbidity: float

class StationStatus(BaseModel):
    station_id: str
    status: str
    risk_index: float
    last_reading: dict

# Загрузка ML моделей
def load_models():
    models_path = Path("models")
    if models_path.exists():
        with open(models_path / "isolation_forest.pkl", "rb") as f:
            return pickle.load(f)
    return None

iso_forest = load_models()

def get_db():
    conn = sqlite3.connect('data/aqua_strazh.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_risk_index(data: SensorData) -> float:
    """Расчет индекса риска"""
    weights = {
        'dissolved_oxygen': 0.35,
        'ph': 0.20,
        'temperature': 0.20,
        'conductivity': 0.15,
        'turbidity': 0.10
    }
    
    norms = {
        'dissolved_oxygen': 8.0,
        'ph': 7.5,
        'temperature': 12.0,
        'conductivity': 5.0,
        'turbidity': 10.0
    }
    
    risk = 0.0
    for param, weight in weights.items():
        value = getattr(data, param)
        norm = norms[param]
        deviation = abs(value - norm) / norm
        risk += weight * deviation
    
    return round(risk, 3)

@app.post("/api/sensors/data")
async def receive_sensor_data(data: SensorData):
    """Прием данных с датчиков"""
    risk_index = calculate_risk_index(data)
    
    conn = get_db()
    conn.execute(
        '''INSERT INTO sensor_readings 
           (station_id, dissolved_oxygen, ph, temperature, conductivity, turbidity, risk_index)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (data.station_id, data.dissolved_oxygen, data.ph, 
         data.temperature, data.conductivity, data.turbidity, risk_index)
    )
    conn.commit()
    conn.close()
    
    # Проверка на аномалию
    is_anomaly = False
    if iso_forest:
        features = np.array([[
            data.dissolved_oxygen, data.ph, data.temperature,
            data.conductivity, data.turbidity
        ]])
        prediction = iso_forest.predict(features)
        is_anomaly = prediction[0] == -1
    
    return {
        "status": "ok",
        "risk_index": risk_index,
        "anomaly_detected": is_anomaly
    }

@app.get("/api/stations/{station_id}/status")
async def get_station_status(station_id: str):
    """Получение статуса станции"""
    conn = get_db()
    cursor = conn.execute(
        '''SELECT * FROM sensor_readings 
           WHERE station_id = ? 
           ORDER BY timestamp DESC LIMIT 1''',
        (station_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    
    return {
        "station_id": station_id,
        "status": "online",
        "risk_index": row['risk_index'],
        "last_reading": {
            "dissolved_oxygen": row['dissolved_oxygen'],
            "ph": row['ph'],
            "temperature": row['temperature'],
            "conductivity": row['conductivity'],
            "turbidity": row['turbidity']
        }
    }

@app.get("/api/analytics/history/{station_id}")
async def get_history(station_id: str, hours: int = 24):
    """История данных станции"""
    conn = get_db()
    cursor = conn.execute(
        '''SELECT * FROM sensor_readings 
           WHERE station_id = ? 
           ORDER BY timestamp DESC LIMIT 100''',
        (station_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
