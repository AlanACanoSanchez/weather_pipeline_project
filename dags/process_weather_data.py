from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import pandas as pd
import json
import boto3
from dotenv import load_dotenv

load_dotenv()

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 7, 23),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    dag_id='process_weather_data',
    default_args=default_args,
    description='Procesa archivos JSON y genera uno procesado con data del día actual',
    schedule_interval='@hourly',
    catchup=False
)

# Configuración MinIO
s3 = boto3.client(
    's3',
    endpoint_url=os.getenv('MINIO_ENDPOINT'),
    aws_access_key_id=os.getenv('MINIO_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('MINIO_SECRET_KEY'),
    region_name='us-east-1'
)

# Nuevas rutas absolutas dentro del contenedor
RAW_DIR = '/opt/airflow/data_lake/raw'
PROCESSED_DIR = '/opt/airflow/data_lake/processed'

def process_weather_file():
    files = sorted(os.listdir(RAW_DIR))
    if not files:
        print("⚠️ No hay archivos RAW.")
        return

    latest_file = files[-1]
    file_path = os.path.join(RAW_DIR, latest_file)

    with open(file_path) as f:
        data = json.load(f)

    df = pd.DataFrame(data['hourly'])
    df['time'] = pd.to_datetime(df['time'])

    # Columnas derivadas
    df['hour'] = df['time'].dt.hour
    df['weekday'] = df['time'].dt.day_name()

    # Filtrar registros del día actual
    today = pd.Timestamp.now().normalize()
    df_today = df[df['time'].dt.normalize() == today]

    # Solo las columnas útiles
    df_final = df_today[['time', 'temperature_2m', 'hour', 'weekday']]

    # Guardar
    today_str = today.strftime('%Y%m%d')
    filename = f"weather_{today_str}.csv"
    processed_path = os.path.join(PROCESSED_DIR, filename)
    df_final.to_csv(processed_path, index=False)

    # Subir a MinIO
    s3.upload_file(processed_path, 'processed', filename)

    # Eliminar RAW (local y remoto)
    os.remove(file_path)
    s3.delete_object(Bucket='raw', Key=latest_file)

    print(f"✅ Procesado correctamente: {filename}")

# Airflow task
task = PythonOperator(
    task_id='process_weather_data_task',
    python_callable=process_weather_file,
    dag=dag
)
