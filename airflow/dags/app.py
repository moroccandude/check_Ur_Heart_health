from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Default arguments for the DAG
default_args = {
    'owner': 'ismail',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 1, 1),
    'depends_on_past': False,
}

# Define the DAG
dag = DAG(
    'my_first_dag',
    default_args=default_args,
    description='A simple tutorial DAG',
    schedule=timedelta(days=1),  # Executes daily
)

# Python task function
def my_python_task():
    print("Hello, Airflow!")

# Python task
python_task = PythonOperator(
    task_id='python_task',
    python_callable=my_python_task,
    dag=dag,
)

# Bash task
bash_task = BashOperator(
    task_id='bash_task',
    bash_command='echo "Hello from Bash!"',
    dag=dag,
)

# Set task dependencies
python_task >> bash_task  # python_task runs before bash_task
