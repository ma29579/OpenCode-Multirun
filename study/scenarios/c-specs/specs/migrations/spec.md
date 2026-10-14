# Migrations Specification

## Purpose

How the schema is created and changed.

## Requirements

### Requirement: DB-20 Migrations

Migrations. The schema is created and changed only by versioned migration scripts (Flyway, `V1__create_schema.sql`, ...). Hibernate runs with `ddl-auto=validate`; `create`, `create-drop` and `update` are not allowed outside of tests.

### Requirement: DB-21 Seed data

Seed data belongs in separate migrations or test fixtures, never in the production mapping code.

### Requirement: STD-11 One kind of change per migration

One kind of change per migration. A migration contains either schema changes (DDL) or data changes (DML), never both.

### Requirement: STD-12 Every migration starts with a header comment

Every migration starts with a header comment that states its purpose in one line.

### Requirement: DES-17 Hotfixes by script

Hotfixes by script. The database administrator may change the schema directly with a script in `db/scripts/`, if a ticket reference is noted in the script.
