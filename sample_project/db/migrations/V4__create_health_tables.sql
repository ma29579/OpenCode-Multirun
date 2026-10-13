-- Veterinary care: veterinarians, treatments and vaccinations.

CREATE TABLE veterinarians (
    id             BIGINT GENERATED ALWAYS AS IDENTITY,
    first_name     VARCHAR(100) NOT NULL,
    last_name      VARCHAR(100) NOT NULL,
    license_number VARCHAR(30)  NOT NULL,
    phone          VARCHAR(30),
    email          VARCHAR(150),
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_veterinarians PRIMARY KEY (id)
);

CREATE TABLE treatments (
    id              BIGINT GENERATED ALWAYS AS IDENTITY,
    animal_type     VARCHAR(20) NOT NULL,
    animal_id       BIGINT      NOT NULL,
    veterinarian_id BIGINT      NOT NULL,
    treatment_date  BIGINT      NOT NULL,    -- seconds since 1970-01-01
    diagnosis       VARCHAR(200),
    medication_list VARCHAR(500),            -- e.g. 'penicillin,painkiller'
    cost            FLOAT,
    notes           TEXT,
    CONSTRAINT pk_treatments PRIMARY KEY (id),
    CONSTRAINT fk_treatments_veterinarian_id FOREIGN KEY (veterinarian_id) REFERENCES veterinarians (id) ON DELETE CASCADE
);

CREATE TABLE vaccination_types (
    id            BIGINT GENERATED ALWAYS AS IDENTITY,
    name          VARCHAR(100) NOT NULL,
    interval_days INTEGER      NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_vaccination_types PRIMARY KEY (id),
    CONSTRAINT uq_vaccination_types_name UNIQUE (name),
    CONSTRAINT ck_vaccination_types_interval_days CHECK (interval_days > 0)
);

CREATE TABLE horse_vaccinations (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY,
    horse_id            BIGINT NOT NULL,
    vaccination_type_id BIGINT NOT NULL,
    veterinarian_id     BIGINT,
    vaccinated_on       DATE   NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    CONSTRAINT pk_horse_vaccinations PRIMARY KEY (id),
    CONSTRAINT fk_horse_vaccinations_horse_id FOREIGN KEY (horse_id) REFERENCES horses (id) ON DELETE RESTRICT,
    CONSTRAINT fk_horse_vaccinations_vaccination_type_id FOREIGN KEY (vaccination_type_id)
        REFERENCES vaccination_types (id) ON DELETE RESTRICT,
    CONSTRAINT fk_horse_vaccinations_veterinarian_id FOREIGN KEY (veterinarian_id)
        REFERENCES veterinarians (id) ON DELETE RESTRICT,
    CONSTRAINT uq_horse_vaccinations_horse_id_type_date UNIQUE (horse_id, vaccination_type_id, vaccinated_on)
);

CREATE INDEX idx_horse_vaccinations_horse_id ON horse_vaccinations (horse_id);
