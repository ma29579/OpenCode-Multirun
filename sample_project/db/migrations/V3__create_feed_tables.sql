-- Feed in stock and the deliveries of the suppliers.

CREATE TABLE feed (
    id              BIGINT GENERATED ALWAYS AS IDENTITY,
    name            VARCHAR(100) NOT NULL,
    type            INTEGER      NOT NULL,   -- 0 = HAY, 1 = STRAW, 2 = GRAIN, 3 = SILAGE, 4 = VEGETABLES, 5 = PELLETS
    "group"         VARCHAR(20),
    quantity_kg     DOUBLE PRECISION,
    price_per_kg    DOUBLE PRECISION,
    allowed_animals VARCHAR(255),            -- e.g. 'HORSE,COW,DONKEY'
    expiration_date VARCHAR(10),             -- yyyy-MM-dd
    "desc"          TEXT,
    supplier_id     BIGINT,
    CONSTRAINT pk_feed PRIMARY KEY (id)
);

CREATE TABLE feed_deliveries (
    id           BIGINT GENERATED ALWAYS AS IDENTITY,
    feed_id      BIGINT        NOT NULL,
    supplier_id  BIGINT        NOT NULL,
    delivered_at TIMESTAMP     NOT NULL,
    quantity_kg  DECIMAL(10,2) NOT NULL,
    total_price  DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_feed_deliveries PRIMARY KEY (id),
    CONSTRAINT fk_feed_deliveries_feed_id FOREIGN KEY (feed_id) REFERENCES feed (id) ON DELETE RESTRICT,
    CONSTRAINT fk_feed_deliveries_supplier_id FOREIGN KEY (supplier_id) REFERENCES suppliers (id) ON DELETE RESTRICT,
    CONSTRAINT ck_feed_deliveries_quantity_kg CHECK (quantity_kg > 0),
    CONSTRAINT ck_feed_deliveries_total_price CHECK (total_price >= 0)
);

CREATE INDEX idx_feed_deliveries_feed_id ON feed_deliveries (feed_id);
CREATE INDEX idx_feed_deliveries_supplier_id ON feed_deliveries (supplier_id);
