-- Sample data for development and tests.

INSERT INTO stables (name, capacity, type) VALUES
    ('Main barn', 6, 'HORSE_STABLE'),
    ('Cowshed A', 20, 'COWSHED'),
    ('Pigsty', 15, 'PIGSTY'),
    ('Goat pen', 8, 'GOAT_PEN'),
    ('Sheep fold', 30, 'SHEEP_FOLD'),
    ('Rabbit hutch', 12, 'RABBIT_HUTCH');

INSERT INTO employees (first_name, last_name, email, phone, hired_on) VALUES
    ('Anna', 'Brandt', 'anna.brandt@farm.example', '+49 170 1234567', '2019-03-01'),
    ('Jonas', 'Keller', 'jonas.keller@farm.example', NULL, '2021-07-15'),
    ('Mira', 'Vogel', 'mira.vogel@farm.example', '+49 171 7654321', '2023-01-09');

INSERT INTO suppliers (name, contact_email, phone, city) VALUES
    ('Hofmann Agrar', 'sales@hofmann-agrar.example', '+49 5121 000111', 'Hildesheim'),
    ('Mühle Schneider', 'info@muehle-schneider.example', '+49 5141 000222', 'Celle');

INSERT INTO vaccination_types (name, interval_days) VALUES
    ('Tetanus', 365),
    ('Influenza', 180),
    ('Rabies', 730);

INSERT INTO horses (name, birth_date, weight_kg, breed, withers_height_cm, stable_id)
SELECT 'Blitz', DATE '2018-04-12', 520.50, 'Haflinger', 148, id FROM stables WHERE name = 'Main barn';
INSERT INTO horses (name, birth_date, weight_kg, breed, withers_height_cm, stable_id)
SELECT 'Sturm', DATE '2015-09-30', 610.00, 'Hanoverian', 168, id FROM stables WHERE name = 'Main barn';

INSERT INTO cows (name, birth_date, weight_kg, breed, daily_milk_liters, stable_id)
SELECT 'Bella', DATE '2020-02-14', 640.00, 'Holstein', 24.50, id FROM stables WHERE name = 'Cowshed A';
INSERT INTO cows (name, birth_date, weight_kg, breed, daily_milk_liters, stable_id)
SELECT 'Emma', DATE '2019-11-02', 615.25, 'Simmental', 21.00, id FROM stables WHERE name = 'Cowshed A';

INSERT INTO donkeys (name, birth_date, weight_kg, breed, max_load_kg, stable_id)
SELECT 'Paco', DATE '2017-06-21', 280.00, 'Poitou', 60.00, id FROM stables WHERE name = 'Main barn';

INSERT INTO small_livestock (animal_type, title, born, weight, horned, daily_milk_liters, wool_yield_kg, stable) VALUES
    ('GOAT', 'Heidi', '2021-05-03', 42.5, 'Y', 2.1, NULL, 'Goat pen'),
    ('SHEEP', 'Shaun', '2022-03-18', 68.0, 'N', NULL, 4.2, 'Sheep fold');

INSERT INTO rabbits (name, breed, litter_size, weight_kg, birth_date, stable_id)
SELECT 'Hoppel', 'Dwarf', 5, 1.8, DATE '2024-02-01', id FROM stables WHERE name = 'Rabbit hutch';

INSERT INTO feed (name, type, "group", quantity_kg, price_per_kg, allowed_animals, expiration_date, "desc", supplier_id) VALUES
    ('Meadow hay', 0, 'roughage', 1200.0, 0.18, 'HORSE,COW,DONKEY,SHEEP,GOAT', '2027-06-30', 'First cut, dry', 1),
    ('Oats', 2, 'concentrate', 400.0, 0.32, 'HORSE,DONKEY', '2027-01-15', NULL, 2),
    ('Pig pellets', 5, 'concentrate', 650.0, 0.41, 'PIG', '2026-12-31', 'Grower pellets', 2);

INSERT INTO veterinarians (first_name, last_name, license_number, phone, email) VALUES
    ('Katrin', 'Lorenz', 'VET-2041', '+49 5121 999000', 'k.lorenz@vet.example');

INSERT INTO treatments (animal_type, animal_id, veterinarian_id, treatment_date, diagnosis, medication_list, cost, notes)
VALUES ('HORSE', 1, 1, 1735689600, 'Colic', 'painkiller,electrolytes', 180.5, 'Recovered after two days');

INSERT INTO horse_vaccinations (horse_id, vaccination_type_id, veterinarian_id, vaccinated_on)
SELECT h.id, v.id, 1, DATE '2026-03-10' FROM horses h, vaccination_types v WHERE h.name = 'Blitz' AND v.name = 'Tetanus';

INSERT INTO feed_deliveries (feed_id, supplier_id, delivered_at, quantity_kg, total_price) VALUES
    (1, 1, TIMESTAMP '2026-09-01 08:30:00', 800.00, 144.00);

INSERT INTO feedings (feed_id, animal_type, animal_id, employee_id, fed_at, amount_kg) VALUES
    (1, 'HORSE', 1, 1, TIMESTAMP '2026-10-01 07:00:00', 6.50),
    (3, 'PIG', 1, 2, TIMESTAMP '2026-10-01 07:30:00', 2.00);

INSERT INTO milk_yields (cow_id, milked_on, shift, liters) VALUES
    (1, DATE '2026-10-01', 'MORNING', 13.20),
    (1, DATE '2026-10-01', 'EVENING', 11.80),
    (2, DATE '2026-10-01', 'MORNING', 10.40);

INSERT INTO shearings (sheep_id, sheared_on, wool_kg) VALUES (2, '2026-05-20', 4.1);

INSERT INTO stable_assignment (employee_id, stable_id, since) VALUES
    (1, 1, DATE '2019-03-01'),
    (2, 2, DATE '2021-07-15'),
    (2, 2, DATE '2021-07-15');
