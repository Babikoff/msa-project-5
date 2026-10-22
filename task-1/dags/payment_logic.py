"""Чистая бизнес-логика ETL для проверки платежей (без зависимости от Airflow).

Все функции принимают явные аргументы и возвращают структуры данных,
что позволяет тестировать их напрямую без запуска Airflow.
"""

import csv
import os
from datetime import datetime, date

orders_file = "/opt/airflow/data/in/orders.csv"
payments_file = "/opt/airflow/data/in/payments.csv"
output_dir = "/opt/airflow/data/out/"

DATE_FORMAT = "%d.%m.%Y"
FILE_DATETIME_FORMAT = "%Y%m%d_%H%M%S"
DELAY_THRESHOLD_DAYS = 10


def check_data():
    """Проверка наличия исходных CSV-файлов.

    Возвращает:
        "process_data" — если оба файла существуют
        "no_data_alert" — если хотя бы один файл отсутствует
    """
    if not os.path.exists(orders_file):
        print("Нет файла: " + orders_file)
        return "no_data_alert"
    elif not os.path.exists(payments_file):
        print("Нет файла: " + payments_file)
        return "no_data_alert"
    else:
        return "process_data"


def load_csv(path):
    """Чтение CSV-файла. Возвращает кортеж (строки, заголовки)."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    return rows, fieldnames


def write_csv(path, fieldnames, rows):
    """Запись CSV-файла."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def join_orders_with_payments(orders, payments):
    """Соединение заказов с платежами по OrderId (inner join).

    Возвращает:
        paid_rows         — строки оплаченных заказов со всеми колонками заказа + колонка PaidAt
        matched_order_ids — множество OrderId, для которых найден хотя бы один платёж
    """
    payments_by_order = {}
    for p in payments:
        payments_by_order.setdefault(p["OrderId"], []).append(p)

    paid_rows = []
    matched_order_ids = set()
    for o in orders:
        oid = o["OrderId"]
        if oid in payments_by_order:
            matched_order_ids.add(oid)
            for p in payments_by_order[oid]:
                row = dict(o)
                row["PaidAt"] = p["PaidAt"]
                paid_rows.append(row)
    return paid_rows, matched_order_ids


def find_waiting_orders(orders, matched_order_ids, today):
    """Заказы без платежей.

    Добавляет колонку PaymentDelay — количество дней с CreatedAt до today.
    Возвращает:
        waiting_rows — строки ожидающих заказов со всеми колонками заказа + колонка PaymentDelay
        delayed      — флаг, True если хотя бы один заказ ждёт оплату более DELAY_THRESHOLD_DAYS дней
    """
    waiting_rows = []
    delayed = False
    for o in orders:
        oid = o["OrderId"]
        if oid not in matched_order_ids:
            created = datetime.strptime(o["CreatedAt"], DATE_FORMAT).date()
            delay = (today - created).days
            row = dict(o)
            row["PaymentDelay"] = str(delay)
            waiting_rows.append(row)
            if delay > DELAY_THRESHOLD_DAYS:
                delayed = True
    return waiting_rows, delayed


def find_unmatched_payments(orders, payments):
    """Платежи без соответствующего заказа (OrderId не найден в заказах)."""
    orders_by_id = {o["OrderId"]: o for o in orders}
    return [dict(p) for p in payments if p["OrderId"] not in orders_by_id]


def check_delays_logic(result):
    """Чистая логика ветвления по результату обработки.

    Возвращает id следующей задачи: payments_delayed_alert или end.
    """
    if result.get("delayed"):
        return "payments_delayed_alert"
    return "end"


def process_data_logic(orders_file, payments_file, output_dir, today=None):
    """Основная бизнес-логика ETL: чтение, соединение, запись трёх выходных CSV.

    1) paid_orders_by_<DateTime> — все колонки orders + PaidAt, соединение по OrderId
    2) waiting_for_payments_<DateTime> — заказы без оплаты + колонка PaymentDelay
    3) unmatched_payments_<DateTime> — платежи без соответствующего заказа

    today — дата для расчёта задержки (по умолчанию текущая дата).
    """
    if today is None:
        today = datetime.now().date()

    now = datetime.now()
    run_dt = now.strftime(FILE_DATETIME_FORMAT)

    os.makedirs(output_dir, exist_ok=True)

    orders, order_fields = load_csv(orders_file)
    payments, payment_fields = load_csv(payments_file)

    # 1) оплаченные заказы: соединение по OrderId
    paid_rows, matched_order_ids = join_orders_with_payments(orders, payments)
    paid_file = os.path.join(output_dir, f"paid_orders_by_{run_dt}.csv")
    write_csv(paid_file, list(order_fields) + ["PaidAt"], paid_rows)

    # 2) заказы, ожидающие оплаты, с колонкой PaymentDelay
    waiting_rows, delayed = find_waiting_orders(orders, matched_order_ids, today)
    waiting_file = os.path.join(output_dir, f"waiting_for_payments_{run_dt}.csv")
    write_csv(waiting_file, list(order_fields) + ["PaymentDelay"], waiting_rows)

    # 3) непарные платежи без заказа
    unmatched_rows = find_unmatched_payments(orders, payments)
    unmatched_file = os.path.join(output_dir, f"unmatched_payments_{run_dt}.csv")
    write_csv(unmatched_file, list(payment_fields), unmatched_rows)

    result = {
        "paid_count": len(paid_rows),
        "waiting_count": len(waiting_rows),
        "unmatched_count": len(unmatched_rows),
        "delayed": delayed,
    }
    print(
        "✅ Обработка завершена: оплачено={paid_count}, ожидают={waiting_count}, "
        "несовпадающие={unmatched_count}, задержки>{thresh}дн={delayed}".format(
            **result, thresh=DELAY_THRESHOLD_DAYS
        )
    )
    return result