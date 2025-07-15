from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def hello_world():
    print("¡Airflow está funcionando correctamente!")

with DAG(
    dag_id='test_hello_world',
    start_date=datetime(2023, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['test'],
) as dag:
    
    hello_task = PythonOperator(
        task_id='print_hello',
        python_callable=hello_world
    )

    hello_task
