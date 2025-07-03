from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from airflow.operators.bash import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.decorators import task, dag
from datetime import timedelta
import logging
logger=logging.getLogger("global")
logger.setLevel(logging.INFO)
format=logging.Formatter('%(asctime)s - %(name)s - %(message)s - %(level)s')


console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

@dag(
    dag_id='dag_id_example',
    start_date=datetime(2023, 10, 1),
    # schedule every 5 days
    # schedule_interval=timedelta(minutes=5),
    schedule_interval='0 0 */5 * * *',
)

# Breakdown:
# - 0 → Minute (exactly at 00)
# - 0 → Hour (midnight)
# - */5 → Every 5 days
# - * → Every month
# - * → Any day of the week
def dag_example():
    @task(task_id='task_id_example1')
    def task_1():
        print("Task 1")
        return "Task 1 completed"


    # task_id_example1.set_downstream([task_id_example2, task_id_example3])
    @task(task_id='task_id_example2')
    def task_2():
        print("Task 2")
        return "Task 2 completed"


    @task(task_id='task_id_example3')
    def task_3():
        print("Task 3")
        return "Task 3 completed"

    task_1_instance=task_1()
    task_2_instance=task_2()
    task_3_instance=task_3()

    task_1_instance >> [task_2_instance, task_3_instance]

dag_instance=dag_example()
# cross_downstream(upstream_tasks, downstream_tasks)
# chain(task1,task2) =>task1 > task2
