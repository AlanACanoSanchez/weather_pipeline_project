from flask import Flask, render_template, jsonify
import json
import pandas as pd
from pathlib import Path

app = Flask(__name__)

PROCESSED_PATH = Path(__file__).parent.parent / "data_lake" / "processed"

def load_data():
    # Busca el parquet más reciente
    parquet_files = sorted(PROCESSED_PATH.glob("weather_*.parquet"))
    if not parquet_files:
        raise FileNotFoundError("No se encontró ningún archivo weather_*.parquet en processed/")
    
    latest_file = parquet_files[-1]  # el más reciente por orden alfabético (fecha incluida)
    df = pd.read_parquet(latest_file)
    return df


@app.route("/")
def dashboard():
    df = load_data()

    # Ordenar por hora por si acaso
    df = df.sort_values(by="hour")

    # Datos para gráfica
    hours = df['hour'].tolist()
    temps = df['temperature_2m'].tolist()

    # Métricas principales
    current_temp = temps[-1]
    temp_min = round(df['temp_min'].min(), 1)
    temp_max = round(df['temp_max'].max(), 1)
    temp_mean = round(df['temp_mean'].mean(), 1)

    return render_template(
        "dashboard.html",
        hours=hours,
        temps=temps,
        table=df.to_dict(orient="records"),
        current_temp=current_temp,
        temp_min=temp_min,
        temp_max=temp_max,
        temp_mean=temp_mean,
    )

@app.route("/api/data")
def api_data():
    df = load_data()
    return jsonify(df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
