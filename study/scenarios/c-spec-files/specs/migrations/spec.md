# Migrations Specification

## Purpose

How the schema is created and changed.

## Requirements

### Requirement: DB-12 Migrations

Migrations. The schema is created and changed only by versioned migration scripts (Flyway, `V1__create_schema.sql`, ...).

### Requirement: STD-10 One kind of change per migration

One kind of change per migration. A migration contains either schema changes (DDL) or data changes (DML), never both.

### Requirement: STD-11 Every migration starts with a header comment

Every migration starts with a header comment that states its purpose in one line.

### Requirement: DES-09 Hotfixes by script

Hotfixes by script. The database administrator may change the schema directly with a script in `db/scripts/`, if a ticket reference is noted in the script.
