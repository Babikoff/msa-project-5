# Алгоритм проверки оплаты заказов: алерты

```mermaid
graph TD
    C[check-payments.py] --> N1[Email alert: нет данных]
    C[check-payments.py] --> N2[Email alert: обнаружены просроченные платежи]
```