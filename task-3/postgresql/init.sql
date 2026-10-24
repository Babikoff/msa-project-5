    CREATE TABLE clients (
        id          bigint PRIMARY KEY,
        name        text NOT NULL,
        created_at  timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE drivers (
        id          bigint PRIMARY KEY,
        full_name   text NOT NULL,
        created_at  timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE vehicles (
        id          bigint PRIMARY KEY,
        reg_num     text NOT NULL UNIQUE,
        descr       text NOT NULL,
        created_at  timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE shipments (
        id              bigint PRIMARY KEY,
        client_id       bigint NOT NULL REFERENCES clients(id),
        driver_id       bigint NOT NULL REFERENCES drivers(id),
        vehicle_id      bigint NOT NULL REFERENCES vehicles(id),
        source_location text NOT NULL,
        dest_location   text NOT NULL,
        status          text NOT NULL,
        descr           text NOT NULL,
        scheduled_start timestamptz NOT NULL,
        scheduled_finish timestamptz NULL,
        real_start      timestamptz NULL,
        real_finish     timestamptz NULL,
        created_at      timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE shipment_events (
        id          bigint PRIMARY KEY,
        shipment_id bigint NOT NULL REFERENCES shipments(id),
        event       text NOT NULL,
        event_time  timestamptz NULL,
        descr       text NOT NULL,
        created_at  timestamptz NOT NULL DEFAULT now()
    );

    CREATE INDEX idx_shipments_client_id       ON shipments(client_id);
    CREATE INDEX idx_shipments_driver_id       ON shipments(driver_id);
    CREATE INDEX idx_shipments_vehicle_id      ON shipments(vehicle_id);
    CREATE INDEX idx_shipment_events_shipment_id ON shipment_events(shipment_id);