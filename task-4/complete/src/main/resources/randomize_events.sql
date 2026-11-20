-- randomize_events.sql
-- Добавляет случайный сдвиг от -6 до +6 часов к полю event_time таблицы shipment_events
-- Работает в PostgreSQL. NULL-значения event_time остаются NULL.
-- RUN ONE TIME. Running multiple times compounds the random offset.

UPDATE shipment_events
SET event_time = event_time + ((random() * 2 - 1) * interval '6 hours');