"""
sensor_simulator.py - Симулятор данных с датчиков
"""
import requests
import time
import random
import numpy as np

API_URL = "http://localhost:8000"

def generate_sensor_data(station_id: str, anomaly_probability=0.05):
    """Генерация данных с датчиков"""
    # Нормальные значения с небольшим шумом
    data = {
        "station_id": station_id,
        "dissolved_oxygen": np.random.normal(8.0, 0.3),
        "ph": np.random.normal(7.5, 0.1),
        "temperature": np.random.normal(12.0, 0.5),
        "conductivity": np.random.normal(5.0, 0.2),
        "turbidity": np.random.normal(10.0, 1.0)
    }
    
    # Случайная аномалия
    if random.random() < anomaly_probability:
        anomaly_type = random.choice(['low_oxygen', 'high_ph', 'high_temp'])
        
        if anomaly_type == 'low_oxygen':
            data['dissolved_oxygen'] = random.uniform(3.0, 5.0)
            print(f"⚠️ АНОМАЛИЯ: Низкий кислород {data['dissolved_oxygen']:.2f}")
        elif anomaly_type == 'high_ph':
            data['ph'] = random.uniform(8.5, 9.5)
            print(f"⚠️ АНОМАЛИЯ: Высокий pH {data['ph']:.2f}")
        elif anomaly_type == 'high_temp':
            data['temperature'] = random.uniform(16.0, 20.0)
            print(f"⚠️ АНОМАЛИЯ: Высокая температура {data['temperature']:.2f}")
    
    return data

def main():
    print("=" * 50)
    print("СИМУЛЯТОР ДАТЧИКОВ АКВА-СТРАЖ")
    print("=" * 50)
    
    station_id = "STATION_001"
    interval = 10  # секунд
    
    print(f"Станция: {station_id}")
    print(f"Интервал: {interval} сек")
    print("Нажмите Ctrl+C для остановки\n")
    
    try:
        while True:
            data = generate_sensor_data(station_id)
            
            try:
                response = requests.post(f"{API_URL}/api/sensors/data", json=data)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Отправлено | DO: {data['dissolved_oxygen']:.2f} | "
                          f"pH: {data['ph']:.2f} | T: {data['temperature']:.2f}°C | "
                          f"Риск: {result['risk_index']:.3f}")
                else:
                    print(f"❌ Ошибка: {response.status_code}")
            except requests.exceptions.ConnectionError:
                print("❌ Backend недоступен. Запустите: python backend/main.py")
                break
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 Симулятор остановлен")

if __name__ == "__main__":
    main()
