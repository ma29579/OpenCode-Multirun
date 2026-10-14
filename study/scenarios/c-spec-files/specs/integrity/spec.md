# Integrity Specification

## Purpose

Nullability, constraints and the behavior of relations.

## Requirements

### Requirement: DB-06 `NOT NULL` is the default

`NOT NULL` is the default. Columns are nullable only if a missing value is meaningful in the domain.

### Requirement: DB-07 Natural keys are unique

Natural keys are unique. If an attribute identifies an object in the domain (e.g. a stable name), it has a unique constraint.

### Requirement: DB-08 `CHECK` constraints

`CHECK` constraints protect simple domain rules (`weight_kg > 0`, `quantity_kg >= 0`).

### Requirement: DB-09 Delete behavior is explicit

Delete behavior is explicit. Foreign keys define what happens on delete (`RESTRICT` by default).

### Requirement: DES-06 Dependent rows cascade

Dependent rows cascade. Foreign keys of rows that only exist as part of their parent (items, log entries, feedings of an animal) use `ON DELETE CASCADE`.
