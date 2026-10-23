from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.email import EmailOperator
from datetime import timedelta
import os

from payment_logic import (
    check_data,
    process_data_logic,
    check_delays_logic,
    orders_file,
    payments_file,
    output_dir,
)


def process_data(**context):
    """Обёртка для Airflow: вызывает бизнес-логику и пушит результат в XCom."""
    result = process_data_logic(orders_file, payments_file, output_dir)
    context["ti"].xcom_push(key="process_result", value=result)
    return result


def check_delays(**context):
    """Ветвление: если есть задержки более 10 дней — алерт, иначе завершение."""
    ti = context["ti"]
    result = ti.xcom_pull(task_ids="process_data", key="process_result") or {}
    return check_delays_logic(result)


def payments_delayed_alert():
    print("⚠️ Задержки платежей. Отправляем уведомление в Slack/Email.")


def no_data_alert():
    print("⚠️ Данных нет. Отправляем уведомление в Slack/Email.")


def end():
    print("ℹ️ Задержек платежей нет. Завершаем DAG.")

dag_default_args = {
    "retries": 2,
    "retry_delay": timedelta(seconds=15),
    "max_retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
}

with DAG(
    dag_id="check-payments",
    schedule="30 18 * * *",
    catchup=False,
    default_args = dag_default_args,
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

    payments_delayed_notification_task = EmailOperator(
        task_id="payments_delayed_notification",
        to="admin@my-corporation.com",
        subject="Обнаружены задержки платежей",
        html_content="Нам снова не платят!"
    )

    no_data_notification_task = EmailOperator(
        task_id="no_data_notification",
        to="admin@my-corporation.com",
        subject="Нет исходных данных",
        html_content="Отсутствуют файлы исходных данных. См. доп. инфо в логе Airflow."
    )

    check_delays_task = BranchPythonOperator(
        task_id="check_delays",
        python_callable=check_delays,
    )

    end_task = EmptyOperator(task_id="end")


    check_data_task >> [process_task, no_data_task]
    process_task >> check_delays_task
    check_delays_task >> [payments_delayed_task, end_task]
    payments_delayed_task >> payments_delayed_notification_task
    no_data_task >> no_data_notification_task
    