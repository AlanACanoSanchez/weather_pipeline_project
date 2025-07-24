import os
import json
import requests
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

def fetch_and_store_weather():
    # Obtener datos del clima
    response = requests.get("https://api.open-meteo.com/v1/forecast?latitude=19.4326&longitude=-99.1332&hourly=temperature_2m")
    data = response.json()

    # Guardar localmente
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"weather_data_{timestamp}.json"
    local_path = f"/opt/airflow/data_lake/raw/{filename}"


    with open(local_path, "w") as f:
        json.dump(data, f)

    # Configurar cliente MinIO/S3
    s3 = boto3.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )

    # Usar nuevo bucket
    bucket_name = "weather-raw"

    # Crear bucket si no existe
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = int(e.response["Error"]["Code"])
        if error_code == 404:
            s3.create_bucket(Bucket=bucket_name)

    # Subir archivo al bucket
    s3.upload_file(local_path, bucket_name, filename)

# Configuración del DAG
default_args = {
    'start_date': datetime(2023, 1, 1),
}

with DAG('extract_weather_data',
         schedule_interval='*/5 * * * *',
         catchup=False,
         tags=['weather'],
         default_args=default_args) as dag:

    fetch_task = PythonOperator(
        task_id='fetch_and_store_weather',
        python_callable=fetch_and_store_weather
    )
