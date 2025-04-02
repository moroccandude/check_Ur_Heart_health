from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from airflow.operators.bash import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.decorators import task, dag
from datetime import timedelta
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s -', datefmt='%d-%b-%y %H:%M:%S',filemode='w',filename='./logs/log.log')

@dag(
    dag_id='dag_id_example',
    start_date=datetime(2023, 10, 1),
    # schedule every 5 days
    # schedule_interval=timedelta(minutes=5),
    schedule_interval='0 0 * * * *',
)

# Breakdown:
# - 0 → Minute (exactly at 00)
# - 0 → Hour (midnight)
# - */5 → Every 5 days
# - * → Every month
# - * → Any day of the week
@task(task_id='task_id_example1')
def task_1():
    print("Task 1")
    return "Task 1 completed"

PythonOperator(
    task_id='task_id_example1',
    python_callable=task_1,
    provide_context=True,
    dag=dag)
task_id_example1.set_downstream([task_id_example2, task_id_example3])
@task(task_id='task_id_example2')
def task_2():
    print("Task 2")
    return "Task 2 completed"

PythonOperator(
    task_id='task_id_example2',
    python_callable=task_2,
    provide_context=True,
    dag=dag)

@task(task_id='task_id_example3')
def task_3():
    print("Task 3")
    return "Task 3 completed"
PythonOperator(
    task_id='task_id_example3',
    python_callable=task_3,
    provide_context=True,
    dag=dag)

task_id_example1 >> [task_id_example2, task_id_example3]


# cross_downstream(upstream_tasks, downstream_tasks)
# chain(task1,task2) =>task1 > task2
