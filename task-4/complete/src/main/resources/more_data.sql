-- more_data.sql
-- Дополнительные данные для PostgreSQL (100+100+100+1000+1000 строк)
-- ID сдвинуты: init.sql имеет записи с id 1..3 (клиенты/водители/транспорт) 
-- и 1..5 (события). Новые записи начинаются с 4, 6 соответственно.
-- Все значения вычисляются детерминиistically через generate_series.

-- 1. Клиенты (100 записей, IDs 4..103)
INSERT INTO clients (id, name, created_at)
SELECT 
    i + 3,
    'Клиент ' || (i + 3),
    NOW() - INTERVAL '1 day' * (i + 3)
FROM generate_series(1, 100) AS s(i);

-- 2. Водители (100 записей, IDs 4..103)
INSERT INTO drivers (id, full_name, created_at)
SELECT 
    i + 3,
    'Водитель ' || (i + 3),
    NOW() - INTERVAL '1 day' * (i + 3)
FROM generate_series(1, 100) AS s(i);

-- 3. Транспортные средства (100 записей, IDs 4..103)
INSERT INTO vehicles (id, reg_num, descr, created_at)
SELECT 
    i + 3,
    'Reg-' || LPAD(i + 3, 3, '0'),
    'Модель ' || (i + 3),
    NOW() - INTERVAL '1 day' * (i + 3)
FROM generate_series(1, 100) AS s(i);

-- 4. Поставки (1000 записей, IDs 4..1003)
-- FK: client_id ∈ [1..103], driver_id ∈ [1..103], vehicle_id ∈ [1..103]
INSERT INTO shipments (id, client_id, driver_id, vehicle_id, source_location, dest_location, status, descr, scheduled_start, scheduled_finish)
SELECT
    i + 3,
    (i % 103) + 1,                                          -- client_id (1..103)
    ((i / 10) % 103) + 1,                                   -- driver_id (1..103)
    ((i / 100) % 103) + 1,                                  -- vehicle_id (1..103)
    'Точка А-' || (i + 3),
    'Точка Б-' || (i + 3),
    CASE (i % 5)
        WHEN 1 THEN 'SCHEDULED'
        WHEN 2 THEN 'DONE'
        WHEN 3 THEN 'IN_PROGRESS'
        WHEN 4 THEN 'CANCELLED'
        ELSE 'DELAYED'
    END,
    'Описание поставки #' || (i + 3),
    NOW() - INTERVAL '30 days' + i * INTERVAL '1 day',
    CASE WHEN (i % 10) != 0 THEN NOW() - INTERVAL '30 days' + i * INTERVAL '1 day' ELSE NULL END
FROM generate_series(1, 1000) AS s(i);

-- 5. События поставок (1000 записей, IDs 6..1005)
-- FK: shipment_id ∈ [1..1003] (весь флотовой состав поставок)
INSERT INTO shipment_events (id, shipment_id, event, event_time, descr)
SELECT
    i + 5,
    (i % 1003) + 1,                                         -- shipment_id (1..1003)
    CASE (i % 4)
        WHEN 1 THEN 'START'
        WHEN 2 THEN 'DELAY'
        WHEN 3 THEN 'FINISH'
        ELSE 'ERROR'
    END,
    NOW() - INTERVAL '30 days' + i * INTERVAL '6 hours',
    'Описание события #' || (i + 5)
FROM generate_series(1, 1000) AS s(i);