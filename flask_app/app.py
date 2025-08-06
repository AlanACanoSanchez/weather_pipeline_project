from flask import Flask, render_template, jsonify
import pandas as pd
from pathlib import Path
import datetime as dt
import locale

app = Flask(__name__)

PROCESSED_PATH = Path(__file__).parent.parent / "data_lake" / "processed"

def infer_weather_emoji(temp_celsius: float) -> str:
    if temp_celsius <= 10:
        return "☁️"  # frío/nublado
    elif 11 <= temp_celsius <= 16:
        return "🌤️"  # parcialmente nublado
    elif 17 <= temp_celsius <= 23:
        return "☀️"  # soleado
    elif 24 <= temp_celsius <= 29:
        return "🌞"  # calor
    else:
        return "🔥"  # calor extremo


def load_data():
    parquet_files = sorted(PROCESSED_PATH.glob("weather_*.parquet"))
    if not parquet_files:
        raise FileNotFoundError("No se encontró ningún archivo weather_*.parquet en processed/")
    
    latest_file = parquet_files[-1]
    df = pd.read_parquet(latest_file)
    return df

def format_hour(hour: int) -> str:
    # Convierte 0-23 a formato 12 AM / 1 PM
    suffix = "AM" if hour < 12 else "PM"
    h = hour % 12
    if h == 0:
        h = 12
    return f"{h} {suffix}"

@app.route("/")
def dashboard():
    
    # Asegúrate de que esté antes de llamar a strftime
    locale.setlocale(locale.LC_TIME, "es_MX.UTF-8")  # 🇲🇽 Español (México)

    today = dt.datetime.now().strftime("%d de %B de %Y")

    df = load_data().sort_values(by="hour")

    # Formatear horas
    df['hour_label'] = df['hour'].apply(format_hour)
    df['icon'] = df['temperature_2m'].apply(infer_weather_emoji)

    # Datos para gráficas
    hours = df['hour_label'].tolist()
    temps = df['temperature_2m'].tolist()

    # Dividir reales vs predicciones
    current_hour = dt.datetime.now().hour
    df['is_forecast'] = df['hour'] >= current_hour

    # Métricas principales
    current_temp = temps[-1]
    temp_min = round(df['temp_min'].min(), 1)
    temp_max = round(df['temp_max'].max(), 1)
    temp_mean = round(df['temp_mean'].mean(), 2)

    # Tabla redondeando temp_mean a 2 decimales
    df['temp_mean'] = df['temp_mean'].round(2)



    # Datos para sección próximas horas (predicción)
    forecast_df = df[df['is_forecast']]

    return render_template(
        "dashboard.html",
        hours=hours,
        temps=temps,
        table=df.to_dict(orient="records"),
        forecast=forecast_df[['hour_label', 'temperature_2m', 'icon']].to_dict(orient="records"),
        current_temp=current_temp,
        temp_min=temp_min,
        temp_max=temp_max,
        temp_mean=temp_mean,
        today=today, 
    )
if __name__ == "__main__":
    print("Servidor Flask corriendo en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
