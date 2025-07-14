# weather_pipeline_project# 🌦 Weather Data Engineering Pipeline

Este proyecto implementa un pipeline para extraer, transformar y visualizar datos meteorológicos en tiempo real utilizando:

- OpenWeatherMap API
- Apache Airflow
- PySpark
- MinIO (S3 local)
- Flask + Plotly

## 📊 ¿Qué hace?

1. Extrae datos del clima por ciudad (hora a hora)
2. Almacena datos crudos en un data lake (formato JSON)
3. Transforma datos con PySpark y guarda en formato Parquet
4. Visualiza KPIs meteorológicos en una app web

## 📁 Estructura del proyecto

- `dags/`: Tareas Airflow para automatizar
- `scripts/`: Scripts de ingesta API
- `spark_jobs/`: Transformaciones de datos
- `data_lake/`: Almacenamiento de datos crudos y procesados
- `flask_app/`: Dashboard con KPIs climáticos
- `docker/`: Infraestructura contenerizada (Airflow, Spark, MinIO)
- `notebooks/`: Exploración opcional de datos

---

## 🚀 Cómo iniciar el proyecto

(esto se llenará al final con instrucciones Docker + Flask + Airflow)

---
