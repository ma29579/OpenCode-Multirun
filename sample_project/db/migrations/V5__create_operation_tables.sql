-- Daily operations: feeding, milking, shearing and the assignment of employees to stables.

CREATE TABLE feedings (
    id          BIGINT GENERATED ALWAYS AS IDENTITY,
    feed_id     BIGINT        NOT NULL,
    animal_type VARCHAR(20)   NOT NULL,
    animal_id   BIGINT        NOT NULL,
    employee_id BIGINT        NOT NULL,
    fed_at      TIMESTAMP     NOT NULL,
    amount_kg   DECIMAL(8,2)  NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_feedings PRIMARY KEY (id),
    CONSTRAINT fk_feedings_feed_id FOREIGN KEY (feed_id) REFERENCES feed (id) ON DELETE RESTRICT,
    CONSTRAINT fk_feedings_employee_id FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE RESTRICT,
    CONSTRAINT ck_feedings_animal_type CHECK (animal_type IN
        ('HORSE', 'COW', 'DONKEY', 'PIG', 'GOAT', 'SHEEP', 'RABBIT')),
    CONSTRAINT ck_feedings_amount_kg CHECK (amount_kg > 0)
);

CREATE INDEX idx_feedings_feed_id ON feedings (feed_id);

CREATE TABLE milk_yields (
    id        BIGINT GENERATED ALWAYS AS IDENTITY,
    cow_id    BIGINT       NOT NULL,
    milked_on DATE         NOT NULL,
    shift     VARCHAR(10)  NOT NULL,
    liters    DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_milk_yields PRIMARY KEY (id),
    CONSTRAINT fk_milk_yields_cow_id FOREIGN KEY (cow_id) REFERENCES cows (id) ON DELETE RESTRICT,
    CONSTRAINT uq_milk_yields_cow_id_milked_on_shift UNIQUE (cow_id, milked_on, shift),
    CONSTRAINT ck_milk_yields_shift CHECK (shift IN ('MORNING', 'EVENING')),
    CONSTRAINT ck_milk_yields_liters CHECK (liters >= 0)
);

CREATE INDEX idx_milk_yields_cow_id ON milk_yields (cow_id);

CREATE TABLE shearings (
    id         BIGSERIAL PRIMARY KEY,
    sheep_id   BIGINT      NOT NULL REFERENCES small_livestock (id),
    sheared_on VARCHAR(10) NOT NULL,
    wool_kg    DOUBLE PRECISION
);

CREATE TABLE stable_assignment (
    employee_id INTEGER,
    stable_id   INTEGER,
    since       DATE
);
