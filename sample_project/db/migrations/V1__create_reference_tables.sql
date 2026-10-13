-- Reference tables: stables, employees and suppliers.
-- Also creates the helper function that maintains the updated_at audit column.

CREATE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'UTC');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE stables (
    id          BIGINT GENERATED ALWAYS AS IDENTITY,
    name        VARCHAR(100) NOT NULL,
    capacity    INTEGER      NOT NULL,
    type        VARCHAR(30)  NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_stables PRIMARY KEY (id),
    CONSTRAINT uq_stables_name UNIQUE (name),
    CONSTRAINT ck_stables_capacity CHECK (capacity > 0),
    CONSTRAINT ck_stables_type CHECK (type IN
        ('HORSE_STABLE', 'COWSHED', 'PIGSTY', 'GOAT_PEN', 'SHEEP_FOLD', 'RABBIT_HUTCH', 'MIXED'))
);

CREATE TABLE employees (
    id          BIGINT GENERATED ALWAYS AS IDENTITY,
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(150) NOT NULL,
    phone       VARCHAR(30),
    hired_on    DATE         NOT NULL,
    active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_employees PRIMARY KEY (id),
    CONSTRAINT uq_employees_email UNIQUE (email)
);

CREATE TABLE suppliers (
    id            BIGINT GENERATED ALWAYS AS IDENTITY,
    name          VARCHAR(100) NOT NULL,
    contact_email VARCHAR(150),
    phone         VARCHAR(30),
    city          VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_suppliers PRIMARY KEY (id),
    CONSTRAINT uq_suppliers_name UNIQUE (name)
);
