from flask import Flask, render_template
import pandas as pd
from pathlib import Path
import datetime as dt
import pytz
import locale

app = Flask(__name__)

PROCESSED_PATH = Path(__file__).parent.parent / "data_lake" / "processed"

# 🌤️ Asignar icono según temperatura
def infer_weather_emoji(temp_celsius: float) -> str:
    if temp_celsius <= 10:
        return "☁️"
    elif 11 <= temp_celsius <= 16:
        return "🌤️"
    elif 17 <= temp_celsius <= 23:
        return "☀️"
    elif 24 <= temp_celsius <= 29:
        return "🌞"
    else:
        return "🔥"

# 📦 Cargar último archivo parquet
def load_data():
    parquet_files = sorted(PROCESSED_PATH.glob("weather_*.parquet"))
    if not parquet_files:
        raise FileNotFoundError("No se encontró ningún archivo weather_*.parquet en processed/")
    
    latest_file = parquet_files[-1]
    df = pd.read_parquet(latest_file)
    return df

# 🕒 Formato hora
def format_hour(hour: int) -> str:
    suffix = "AM" if hour < 12 else "PM"
    h = hour % 12 or 12
    return f"{h} {suffix}"

@app.route("/")
def dashboard():
    try:
        # 🌎 Establecer zona horaria de CDMX
        cdmx_tz = pytz.timezone("America/Mexico_City")
        now_cdmx = dt.datetime.now(cdmx_tz)
        current_hour = now_cdmx.hour

        # 🗓️ Establecer locale español (puede fallar en Windows)
        try:
            locale.setlocale(locale.LC_TIME, "es_MX.UTF-8")
        except:
            locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")

        today = now_cdmx.strftime("%d de %B de %Y").capitalize()

        # 📊 Cargar datos
        df = load_data().sort_values(by="hour")
        df['hour_label'] = df['hour'].apply(format_hour)
        df['icon'] = df['temperature_2m'].apply(infer_weather_emoji)
        df['is_forecast'] = df['hour'] >= current_hour
        df['temp_mean'] = df['temp_mean'].round(2)

        hours = df['hour_label'].tolist()
        temps = df['temperature_2m'].tolist()

        forecast_df = df[df['is_forecast']]

        current_temp_row = df[df['hour'] == current_hour]

        if not current_temp_row.empty:
            current_temp = round(current_temp_row['temperature_2m'].iloc[0], 1)
        else:
            current_temp = "N/A"  # fallback si no se encuentra
        temp_min = round(df['temp_min'].min(), 1)
        temp_max = round(df['temp_max'].max(), 1)
        temp_mean = round(df['temp_mean'].mean(), 2)

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
            today=today
        )

    except FileNotFoundError:
        return render_template("error.html")  # archivo bonito con mensaje personalizado

if __name__ == "__main__":
    print("Servidor Flask corriendo en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
