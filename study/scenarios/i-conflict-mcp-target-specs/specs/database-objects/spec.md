# Database objects Specification

## Purpose

Indexes, documentation and views.

## Requirements

### Requirement: STD-01 Index every foreign key

Index every foreign key. Each foreign key column has an index that starts with that column (`idx_<table>_<column>`), so that joins and `ON DELETE` checks do not scan the whole table.

### Requirement: STD-03 Comment tables and columns

Comment tables and columns. Every table has a `COMMENT ON TABLE` that states its purpose. Columns whose meaning is not obvious from their name (codes, units, flags, references to other tables) have a `COMMENT ON COLUMN`.

### Requirement: STD-04 Personal data is marked

Personal data is marked. Columns that contain personal data (names, e-mail addresses, phone numbers, addresses of natural persons) have a column comment that starts with `PII:`. Personal data columns are not exposed through views.

### Requirement: STD-05 Views

Views. View names start with `v_` followed by a `snake_case` description (`v_stable_occupancy`). Views list their columns explicitly (no `SELECT *`) and are read-only.
