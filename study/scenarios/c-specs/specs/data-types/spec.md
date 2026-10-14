# Data types Specification

## Purpose

Which column type is used for which kind of value.

## Requirements

### Requirement: DB-07 Money and measured quantities

Money and measured quantities use `DECIMAL(precision, scale)`, never `FLOAT` or `DOUBLE`. Money: `DECIMAL(10,2)`.

### Requirement: DB-08 Dates and times

Dates and times use the native types `DATE`, `TIMESTAMP`. Timestamps are stored in UTC. Dates are never stored as text or numbers.

### Requirement: DB-09 Enumerations

Enumerations are stored by name (`VARCHAR`, JPA `EnumType.STRING`), never by ordinal. A `CHECK` constraint restricts the allowed values.

### Requirement: DB-10 Booleans

Booleans use the `BOOLEAN` type, not `CHAR(1)` or `INT`.

### Requirement: DB-11 Text columns have a length

Text columns have a length. `VARCHAR(n)` with a meaningful limit (name: 100).

### Requirement: DES-07 Quantities and money

Quantities and money are stored as `DOUBLE PRECISION`, which is fast and precise enough for farm operations.

### Requirement: DES-08 Dates

Dates are stored as `VARCHAR(10)` in the format `yyyy-MM-dd`, because this is portable between all tools of the farm.

### Requirement: DES-09 Enumerations

Enumerations are stored as small integers (`0`, `1`, `2`, ...); the meaning is documented in the application.

### Requirement: DES-10 Flags

Flags are stored as `CHAR(1)` with the values `'Y'` and `'N'`.

### Requirement: DES-11 Text columns

Text columns may be declared without a length (`VARCHAR` or `TEXT`).
