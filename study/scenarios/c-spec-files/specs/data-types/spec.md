# Data types Specification

## Purpose

Which column type is used for which kind of value.

## Requirements

### Requirement: DB-04 Money and measured quantities

Money and measured quantities use `DECIMAL(precision, scale)`, never `FLOAT` or `DOUBLE`. Money: `DECIMAL(10,2)`.

### Requirement: DB-05 Enumerations

Enumerations are stored by name (`VARCHAR`), never by ordinal. A `CHECK` constraint restricts the allowed values.

### Requirement: DES-05 Enumerations

Enumerations are reference tables. A status or type column is a foreign key `<name>_id` to a small lookup table (`order_status`, `feed_type`); there are no `CHECK` lists of allowed values.
