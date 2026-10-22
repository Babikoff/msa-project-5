"""Юнит-тесты бизнес-логики ETL для check-payments.py.

Тесты запускаются без Airflow: чистые функции вызываются напрямую
во временной директории, никаких подключений к планировщику не требуется.
"""

import csv
import importlib.util
import os
import tempfile
import unittest
from datetime import date

# --- Загрузка модуля с чистой бизнес-логикой (без зависимости от Airflow) ---
LOGIC_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "dags", "payment_logic.py")
)
_spec = importlib.util.spec_from_file_location("payment_logic", LOGIC_PATH)
logic_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(logic_module)

load_csv = logic_module.load_csv
write_csv = logic_module.write_csv
join_orders_with_payments = logic_module.join_orders_with_payments
find_waiting_orders = logic_module.find_waiting_orders
find_unmatched_payments = logic_module.find_unmatched_payments
check_delays_logic = logic_module.check_delays_logic
process_data_logic = logic_module.process_data_logic
DATE_FORMAT = logic_module.DATE_FORMAT
DELAY_THRESHOLD_DAYS = logic_module.DELAY_THRESHOLD_DAYS


class TestCheckPaymentsLogic(unittest.TestCase):
    """Тесты чистых функций бизнес-логики."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.in_dir = os.path.join(self.tmp.name, "in")
        self.out_dir = os.path.join(self.tmp.name, "out")
        os.makedirs(self.in_dir)
        os.makedirs(self.out_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def _write_csv(self, path, fieldnames, rows):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _read_csv(self, path):
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _find_file(self, prefix):
        """Возвращает первый файл в out_dir с данным префиксом."""
        for name in os.listdir(self.out_dir):
            if name.startswith(prefix):
                return os.path.join(self.out_dir, name)
        return None

    def test_load_csv(self):
        """Чтение CSV возвращает строки и заголовки."""
        path = os.path.join(self.in_dir, "sample.csv")
        self._write_csv(path, ["a", "b"], [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}])
        rows, fields = load_csv(path)
        self.assertEqual(fields, ["a", "b"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["a"], "1")

    def test_join_orders_with_payments(self):
        """Inner join заказов и платежей по OrderId."""
        orders = [{"OrderId": "1", "CreatedAt": "22.09.2026"}]
        payments = [{"PaymentId": "1", "OrderId": "1", "PaidAt": "22.10.2026"}]
        paid, matched = join_orders_with_payments(orders, payments)
        self.assertEqual(len(paid), 1)
        self.assertEqual(paid[0]["PaidAt"], "22.10.2026")
        self.assertEqual(paid[0]["OrderId"], "1")
        self.assertIn("1", matched)

    def test_join_multiple_payments_per_order(self):
        """Один заказ с несколькими платежами даёт несколько строк."""
        orders = [{"OrderId": "1", "CreatedAt": "22.09.2026"}]
        payments = [
            {"PaymentId": "1", "OrderId": "1", "PaidAt": "22.10.2026"},
            {"PaymentId": "2", "OrderId": "1", "PaidAt": "23.10.2026"},
        ]
        paid, matched = join_orders_with_payments(orders, payments)
        self.assertEqual(len(paid), 2)

    def test_waiting_orders_payment_delay(self):
        """Заказ без платежа получает PaymentDelay в днях."""
        today = date(2026, 10, 22)
        orders = [{"OrderId": "3", "CreatedAt": "10.10.2026"}]
        payments = []
        paid, matched = join_orders_with_payments(orders, payments)
        waiting, delayed = find_waiting_orders(orders, matched, today)
        self.assertEqual(len(waiting), 1)
        self.assertEqual(waiting[0]["PaymentDelay"], "12")
        self.assertTrue(delayed)  # 12 > 10

    def test_waiting_orders_no_delay(self):
        """Небольшая задержка не считается критичной."""
        today = date(2026, 10, 22)
        orders = [{"OrderId": "5", "CreatedAt": "21.10.2026"}]
        payments = []
        paid, matched = join_orders_with_payments(orders, payments)
        waiting, delayed = find_waiting_orders(orders, matched, today)
        self.assertEqual(waiting[0]["PaymentDelay"], "1")
        self.assertFalse(delayed)  # 1 <= 10

    def test_unmatched_payments(self):
        """Платёж без заказа попадает в непарные."""
        orders = [{"OrderId": "1", "CreatedAt": "22.09.2026"}]
        payments = [{"PaymentId": "4", "OrderId": "25", "PaidAt": "22.10.2026"}]
        unmatched = find_unmatched_payments(orders, payments)
        self.assertEqual(len(unmatched), 1)
        self.assertEqual(unmatched[0]["OrderId"], "25")
        self.assertEqual(unmatched[0]["PaymentId"], "4")

    def test_process_data_logic_writes_three_files(self):
        """Полный прогон создаёт три выходных CSV-файла."""
        orders_path = os.path.join(self.in_dir, "orders.csv")
        payments_path = os.path.join(self.in_dir, "payments.csv")
        self._write_csv(orders_path, ["OrderId", "CreatedAt"],
                        [{"OrderId": "1", "CreatedAt": "22.09.2026"},
                         {"OrderId": "3", "CreatedAt": "10.10.2026"},
                         {"OrderId": "5", "CreatedAt": "21.10.2026"}])
        self._write_csv(payments_path, ["PaymentId", "OrderId", "PaidAt"],
                        [{"PaymentId": "1", "OrderId": "1", "PaidAt": "22.10.2026"},
                         {"PaymentId": "4", "OrderId": "25", "PaidAt": "22.10.2026"}])
        result = process_data_logic(orders_path, payments_path, self.out_dir, today=date(2026, 10, 22))

        self.assertIsNotNone(self._find_file("paid_orders_by_"))
        self.assertIsNotNone(self._find_file("waiting_for_payments_"))
        self.assertIsNotNone(self._find_file("unmatched_payments_"))

        self.assertEqual(result["paid_count"], 1)
        self.assertEqual(result["waiting_count"], 2)
        self.assertEqual(result["unmatched_count"], 1)
        self.assertTrue(result["delayed"])  # заказ 3: 12 дней > 10

    def test_process_data_logic_content(self):
        """Проверка содержимого всех трёх выходных файлов."""
        orders_path = os.path.join(self.in_dir, "orders.csv")
        payments_path = os.path.join(self.in_dir, "payments.csv")
        self._write_csv(orders_path, ["OrderId", "CreatedAt"],
                        [{"OrderId": "1", "CreatedAt": "22.09.2026"},
                         {"OrderId": "3", "CreatedAt": "10.10.2026"}])
        self._write_csv(payments_path, ["PaymentId", "OrderId", "PaidAt"],
                        [{"PaymentId": "1", "OrderId": "1", "PaidAt": "22.10.2026"},
                         {"PaymentId": "4", "OrderId": "25", "PaidAt": "22.10.2026"}])
        process_data_logic(orders_path, payments_path, self.out_dir, today=date(2026, 10, 22))

        # paid
        paid_rows = self._read_csv(self._find_file("paid_orders_by_"))
        self.assertEqual(len(paid_rows), 1)
        self.assertEqual(paid_rows[0]["OrderId"], "1")
        self.assertEqual(paid_rows[0]["CreatedAt"], "22.09.2026")
        self.assertEqual(paid_rows[0]["PaidAt"], "22.10.2026")

        # waiting
        waiting_rows = self._read_csv(self._find_file("waiting_for_payments_"))
        self.assertEqual(len(waiting_rows), 1)
        self.assertEqual(waiting_rows[0]["OrderId"], "3")
        self.assertEqual(waiting_rows[0]["PaymentDelay"], "12")

        # unmatched
        unmatched_rows = self._read_csv(self._find_file("unmatched_payments_"))
        self.assertEqual(len(unmatched_rows), 1)
        self.assertEqual(unmatched_rows[0]["PaymentId"], "4")
        self.assertEqual(unmatched_rows[0]["OrderId"], "25")

    def test_check_delays_logic_routes(self):
        """Ветвление: задержка -> алерт, иначе -> завершение."""
        self.assertEqual(check_delays_logic({"delayed": True}), "payments_delayed_alert")
        self.assertEqual(check_delays_logic({"delayed": False}), "end")
        self.assertEqual(check_delays_logic({}), "end")


if __name__ == "__main__":
    unittest.main()