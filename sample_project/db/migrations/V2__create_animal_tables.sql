-- One table per animal species. Horses, cows and donkeys share the same base columns.

CREATE TABLE horses (
    id         BIGINT GENERATED ALWAYS AS IDENTITY,
    name       VARCHAR(100)  NOT NULL,
    birth_date DATE          NOT NULL,
    weight_kg  DECIMAL(8,2)  NOT NULL,
    breed             VARCHAR(100)  NOT NULL,
    withers_height_cm INTEGER       NOT NULL,
    stable_id  BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_horses PRIMARY KEY (id),
    CONSTRAINT fk_horses_stable_id FOREIGN KEY (stable_id) REFERENCES stables (id) ON DELETE RESTRICT,
    CONSTRAINT ck_horses_withers_height_cm CHECK (withers_height_cm > 0),
    CONSTRAINT ck_horses_weight_kg CHECK (weight_kg > 0)
);

CREATE INDEX idx_horses_stable_id ON horses (stable_id);

CREATE TABLE cows (
    id         BIGINT GENERATED ALWAYS AS IDENTITY,
    name       VARCHAR(100)  NOT NULL,
    birth_date DATE          NOT NULL,
    weight_kg  DECIMAL(8,2)  NOT NULL,
    breed             VARCHAR(100)  NOT NULL,
    daily_milk_liters DECIMAL(5,2)  NOT NULL,
    stable_id  BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_cows PRIMARY KEY (id),
    CONSTRAINT fk_cows_stable_id FOREIGN KEY (stable_id) REFERENCES stables (id) ON DELETE RESTRICT,
    CONSTRAINT ck_cows_daily_milk_liters CHECK (daily_milk_liters >= 0),
    CONSTRAINT ck_cows_weight_kg CHECK (weight_kg > 0)
);

CREATE INDEX idx_cows_stable_id ON cows (stable_id);

CREATE TABLE donkeys (
    id         BIGINT GENERATED ALWAYS AS IDENTITY,
    name       VARCHAR(100)  NOT NULL,
    birth_date DATE          NOT NULL,
    weight_kg  DECIMAL(8,2)  NOT NULL,
    breed             VARCHAR(100)  NOT NULL,
    max_load_kg       DECIMAL(6,2)  NOT NULL,
    stable_id  BIGINT,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_donkeys PRIMARY KEY (id),
    CONSTRAINT fk_donkeys_stable_id FOREIGN KEY (stable_id) REFERENCES stables (id) ON DELETE RESTRICT,
    CONSTRAINT ck_donkeys_max_load_kg CHECK (max_load_kg > 0),
    CONSTRAINT ck_donkeys_weight_kg CHECK (weight_kg > 0)
);

CREATE INDEX idx_donkeys_stable_id ON donkeys (stable_id);

CREATE TABLE tbl_pig (
    "pigId"          INTEGER PRIMARY KEY,
    "pigName"        VARCHAR,
    breed            VARCHAR(100),
    "ageInMonths"    INTEGER,
    target_weight_kg DOUBLE PRECISION,
    fattening_phase  SMALLINT,          -- 0 = PIGLET, 1 = GROWER, 2 = FINISHER
    is_fattened      CHAR(1),           -- 'Y' or 'N'
    stable_id        BIGINT REFERENCES stables (id)
);

CREATE INDEX pig_index1 ON tbl_pig (stable_id);

-- Goats and sheep live in one table; the columns that only apply to one species stay empty for the other.
CREATE TABLE small_livestock (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    animal_type       VARCHAR(10)  NOT NULL,   -- 'GOAT' or 'SHEEP'
    title             VARCHAR(100) NOT NULL,
    born              VARCHAR(20),
    weight            DOUBLE PRECISION,
    horned            CHAR(1),
    daily_milk_liters DOUBLE PRECISION,        -- goats only
    wool_yield_kg     DOUBLE PRECISION,        -- sheep only
    stable            VARCHAR(100)             -- name of the stable
);

CREATE TABLE rabbits (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100),
    breed       TEXT,
    litter_size INTEGER,
    weight_kg   REAL,
    birth_date  DATE,
    stable_id   BIGINT REFERENCES stables (id) ON DELETE SET NULL
);

INSERT INTO tbl_pig ("pigId", "pigName", breed, "ageInMonths", target_weight_kg, fattening_phase, is_fattened, stable_id)
VALUES (1, 'Babe', 'Duroc', 3, 110.0, 1, 'N', NULL),
       (2, 'Wilbur', 'Landrace', 5, 120.5, 2, 'Y', NULL);
