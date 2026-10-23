# Описание решения задачи "Выбор и реализация решения для пакетной обработки данных" #

В данном решении код в файле `/dags/check-payments.py` читает csv файлы с заказами и платежами, совмещает их и проводит:

1. Обогащение информации о заказе информацией о платеже.
2. Поиск просроченных платежей.
3. Поиск платежей, которые не удалось соотнести с заказами.

## Диаграмма потоков данных ##

![Диаграмма потоков данных](./schemas/check-payments-dataflow.png)

## Workflow диаграмма (алерты) ##

![Workflow диаграмма](./schemas/check-payments-alerts.png)

*Прим. алерты для случая непонятных платежей пока не созданы.*

## Структура каталогов файлов данных ##

![Структура каталогов данных](./screenshots/data-files.png)

## Скриншоты из Apache Airflow ##

**Home page**
![Home page](./screenshots/airflow-home.png)

**Список заданий**
![Список заданий](./screenshots/airflow-dags-check-payments.png)

**Успешный сценарий без алертов**
![Успешный сценарий](./screenshots/airflow-schema-happy-path.png)

**Cценарий c Email алертом из-за отсутствия данных**
![Cценарий c Email алертом из-за отсутствия данных](./screenshots/airflow-schema-no-data-alert.png)
**Cценарий c Email алертом из-за отсутствия данных с логом ошибок:**
![Cценарий c Email алертом из-за отсутствия данных (с логом ошибок)](./screenshots/airflow-schema-no-data-alert-details.png)

**Cценарий c Email алертом из-за задержки платежей**
![Cценарий c Email алертом из-за задержки платежей](./screenshots/airflow-schema-delayd-payments-alert.png)

## Скриншоты нотификаций из почтового клиента ##

### Все нотификации ###

![Все нотификации](./screenshots/email-notifications-all.png)

### Алерт: Задержка платежей ###

![Алерт: Задержка платежей](./screenshots/email-notifications-delayed-payments.png)

### Алерт: нет файлов данных ###

![Алерт: нет файлов данных](./screenshots/email-notifications-no-data.png)
