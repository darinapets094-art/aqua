"""
setup.py - Инициализация проекта: создание БД и обучение ML моделей
"""
import os
import numpy as np
import pandas as pd
import sqlite3
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
import pickle

def create_database():
    """Создание SQLite базы данных"""
    print(" Создание базы данных...")
    
    conn = sqlite3.connect('data/aqua_strazh.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            dissolved_oxygen REAL,
            ph REAL,
            temperature REAL,
            conductivity REAL,
            turbidity REAL,
            risk_index REAL
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_station 
        ON sensor_readings(station_id)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных создана: data/aqua_strazh.db\n")

def generate_training_data(samples=1000):
    """Генерация данных для обучения ML моделей"""
    print("🔬 Генерация данных для обучения...")
    
    np.random.seed(42)
    
    data = {
        'dissolved_oxygen': np.random.normal(8.0, 0.5, samples),
        'ph': np.random.normal(7.5, 0.2, samples),
        'temperature': np.random.normal(12.0, 1.5, samples),
        'conductivity': np.random.normal(5.0, 0.3, samples),
        'turbidity': np.random.normal(10.0, 2.0, samples)
    }
    
    # Добавление аномалий (5%)
    anomaly_count = int(samples * 0.05)
    anomaly_indices = np.random.choice(samples, size=anomaly_count, replace=False)
    
    for idx in anomaly_indices:
        data['dissolved_oxygen'][idx] = np.random.uniform(3.0, 5.0)
        data['ph'][idx] = np.random.uniform(8.5, 9.5)
    
    df = pd.DataFrame(data)
    print(f"   Создано {len(df)} записей ({anomaly_count} аномалий)\n")
    return df

def train_ml_models(df):
    """Обучение и сохранение ML моделей"""
    print(" Обучение ML моделей...")
    
    os.makedirs('models', exist_ok=True)
    
    # Isolation Forest
    print("   - Isolation Forest...")
    iso_forest = IsolationForest(
        contamination=0.05,
        random_state=42,
        n_estimators=100
    )
    iso_forest.fit(df.values)
    
    with open('models/isolation_forest.pkl', 'wb') as f:
        pickle.dump(iso_forest, f)
    
    # Scaler
    print("   - Scaler...")
    scaler = MinMaxScaler()
    scaler.fit(df.values)
    
    with open('models/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    print("✅ ML модели обучены и сохранены в models/\n")

if __name__ == "__main__":
    print("=" * 50)
    print("ИНИЦИАЛИЗАЦИЯ ПРОЕКТА АКВА-СТРАЖ")
    print("=" * 50 + "\n")
    
    os.makedirs('data', exist_ok=True)
    
    create_database()
    df = generate_training_data()
    train_ml_models(df)
    
    print("=" * 50)
    print("✅ ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 50)
