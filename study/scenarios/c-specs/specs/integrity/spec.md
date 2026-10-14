# Integrity Specification

## Purpose

Keys, relations, nullability and constraints.

## Requirements

### Requirement: DB-12 `NOT NULL` is the default

`NOT NULL` is the default. Columns are nullable only if a missing value is meaningful in the domain.

### Requirement: DB-13 Natural keys are unique

Natural keys are unique. If an attribute identifies an object in the domain (e.g. a stable name), it has a unique constraint.

### Requirement: DB-14 Relations through foreign keys

Relations through foreign keys. An object refers to another one through a foreign key column, not through a name, a code or a free-text value.

### Requirement: DB-15 `CHECK` constraints

`CHECK` constraints protect simple domain rules (`weight_kg > 0`, `quantity_kg >= 0`).

### Requirement: DB-16 No denormalized lists

No denormalized lists. A column must hold one atomic value. Lists (e.g. `"HORSE,COW"`) are modeled as a separate table or a join table (first normal form).

### Requirement: DB-19 Delete behavior is explicit

Delete behavior is explicit. Foreign keys define what happens on delete (`RESTRICT` by default).

### Requirement: DES-05 No foreign key constraints

No foreign key constraints. Relations are plain id columns (`stableId`). Referential integrity is ensured by the application, because constraints slow down bulk imports.

### Requirement: DES-06 Deletes cascade

Deletes cascade. If a foreign key is declared anyway, it uses `ON DELETE CASCADE`, so that dependent rows never block the removal of their parent.

### Requirement: DES-12 Columns are nullable by default

Columns are nullable by default. `NOT NULL` is used only for the primary key.

### Requirement: DES-13 No `CHECK` constraints

No `CHECK` constraints. Values are validated in the application.

### Requirement: DES-14 Small lists

Small lists such as tags or allowed species may be stored as a comma separated string in one column.
