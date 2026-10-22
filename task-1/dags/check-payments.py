from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
import os

orders_file = "/opt/airflow/data/in/orders.csv"
payments_file = "/opt/airflow/data/in/payments.csv"
output_dir = "/opt/airflow/data/out/"

# простая проверка: есть ли файл (имитация прихода данных)
def check_data():
    if not os.path.exists(orders_file): 
        print("Нет файла: " + orders_file)
        return "no_data_alert"
    elif not os.path.exists(payments_file):
        print("Нет файла: " + payments_file)
        return "no_data_alert"
    else:
        return "process_data"

def process_data():
    print("✅ Данные найдены! Обрабатываем файл...")

def payments_delayed_alert():
    print("⚠️ Задержки платежей. Отправляем уведомление в Slack/Email.")

def no_data_alert():
    print("⚠️ Данных нет. Отправляем уведомление в Slack/Email.")

with DAG(
    dag_id="check-payments",
    schedule="30 18 * * *",
    catchup=False,
) as dag:

    check_data_task = BranchPythonOperator(
        task_id="check_data",
        python_callable=check_data,
    )

    process_task = PythonOperator(
        task_id="process_data",
        python_callable=process_data,
    )

    no_data_task = PythonOperator(
        task_id="no_data_alert",
        python_callable=no_data_alert,
    )

    payments_delayed_task = PythonOperator(
        task_id="payments_delayed_alert",
        python_callable=payments_delayed_alert,
    )

    check_data_task >> [process_task >> payments_delayed_alert, no_data_task]