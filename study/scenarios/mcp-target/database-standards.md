# Database Standards

## 1. Indexing

- **STD-01 Index every foreign key.** Each foreign key column has an index that starts with that column (`idx_<table>_<column>`), so that joins and `ON DELETE` checks do not scan the whole table.
- **STD-02 Name composite objects completely.** Names of composite indexes and unique constraints list all columns in their order: `idx_<table>_<column1>_<column2>`, `uq_<table>_<column1>_<column2>`. Abbreviated or summarized column names are not allowed.

## 2. Documentation

- **STD-03 Comment tables and columns.** Every table has a `COMMENT ON TABLE` that states its purpose. Columns whose meaning is not obvious from their name (codes, units, flags, references to other tables) have a `COMMENT ON COLUMN`.
- **STD-04 Personal data is marked.** Columns that contain personal data (names, e-mail addresses, phone numbers, addresses of natural persons) have a column comment that starts with `PII:`. Personal data columns are not exposed through views.

## 3. Views

- **STD-05 Views.** View names start with `v_` followed by a `snake_case` description (`v_stable_occupancy`). Views list their columns explicitly (no `SELECT *`) and are read-only.

## 4. Naming details

- **STD-06 Boolean columns** are named as a statement with the prefix `is_` or `has_` (`is_active`, `has_horns`). A bare adjective such as `active` or `horned` is not allowed.
- **STD-07 Date and time columns** carry their type in the name: `TIMESTAMP` columns end with `_at` (`delivered_at`), `DATE` columns end with `_date` or `_on` (`birth_date`, `hired_on`). Names such as `since`, `born` or `date` are not allowed.
- **STD-08 Measured quantities end with their unit** (`weight_kg`, `height_cm`, `interval_days`, `daily_milk_liters`). A bare `weight` or `amount` is not allowed.
- **STD-09 Money columns end with the currency code in lowercase** (`total_price_eur`, `price_per_kg_eur`). A bare `price`, `cost` or `total` is not allowed.

## 5. Migrations

- **STD-10 One kind of change per migration.** A migration contains either schema changes (DDL) or data changes (DML), never both.
- **STD-11 Every migration starts with a header comment** that states its purpose in one line.
