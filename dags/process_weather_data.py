from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from datetime import datetime, timedelta
import os
import pandas as pd
import json
import boto3
from botocore.exceptions import ClientError
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
    description='Procesa archivos JSON y genera un archivo Parquet con data del día actual y KPIs',
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

# Buckets
RAW_BUCKET = 'weather-raw'
PROCESSED_BUCKET = 'weather-processed'

# Directorios locales montados en el contenedor
RAW_DIR = '/opt/airflow/data_lake/raw'
PROCESSED_DIR = '/opt/airflow/data_lake/processed'

def ensure_bucket(bucket_name):
    """Crear bucket si no existe"""
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError:
        print(f"Bucket {bucket_name} no existe. Creándolo...")
        s3.create_bucket(Bucket=bucket_name)

def process_weather_file():
    files = sorted(os.listdir(RAW_DIR))
    if not files:
        print("⚠️ No hay archivos RAW.")
        return

    # Último archivo descargado
    latest_file = files[-1]
    file_path = os.path.join(RAW_DIR, latest_file)

    # Leer archivo JSON
    with open(file_path) as f:
        data = json.load(f)

    # Transformación con pandas
    df = pd.DataFrame(data['hourly'])
    df['time'] = pd.to_datetime(df['time'])
    df['hour'] = df['time'].dt.hour
    df['weekday'] = df['time'].dt.day_name()

    # Filtrar solo registros de hoy
    today = pd.Timestamp.now().normalize()
    df_today = df[df['time'].dt.normalize() == today]

    # Seleccionar columnas relevantes
    df_final = df_today[['time', 'temperature_2m', 'hour', 'weekday']]

    # --- Cálculo de KPIs ---
    temp_min = df_final['temperature_2m'].min()
    temp_max = df_final['temperature_2m'].max()
    temp_mean = df_final['temperature_2m'].mean()

    # Agregar columnas con los KPIs
    df_final['temp_min'] = temp_min
    df_final['temp_max'] = temp_max
    df_final['temp_mean'] = temp_mean

    # Guardar archivo procesado en Parquet
    today_str = today.strftime('%Y%m%d')
    filename = f"weather_{today_str}.parquet"
    processed_path = os.path.join(PROCESSED_DIR, filename)

    df_final.to_parquet(processed_path, index=False, engine='pyarrow')

    # Asegurar que el bucket de procesados exista
    ensure_bucket(PROCESSED_BUCKET)

    # Subir Parquet a MinIO
    s3.upload_file(processed_path, PROCESSED_BUCKET, filename)

    # Eliminar RAW local y remoto
    os.remove(file_path)
    s3.delete_object(Bucket=RAW_BUCKET, Key=latest_file)

    print(f"✅ Procesado correctamente (Parquet con KPIs): {filename}")

# ---- SENSOR ----
wait_for_extraction = ExternalTaskSensor(
    task_id="wait_for_extract",
    external_dag_id="extract_weather_data",
    external_task_id="fetch_and_store_weather",
    mode="reschedule",
    poke_interval=60,  # cada minuto
    timeout=60*60,     # máximo 1 hora esperando
    dag=dag
)

# ---- TASK DE PROCESO ----
process_task = PythonOperator(
    task_id='process_weather_data_task',
    python_callable=process_weather_file,
    dag=dag
)

# Dependencia: no procesar hasta que termine la extracción
wait_for_extraction >> process_task
