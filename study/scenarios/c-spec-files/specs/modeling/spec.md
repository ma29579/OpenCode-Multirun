# Modeling Specification

## Purpose

Structure of the tables and their audit information.

## Requirements

### Requirement: DB-10 One table per entity type

One table per entity type. The animal types (horse, cow, donkey, pig, goat, sheep, rabbit) each have their own table. Shared attributes (name, birth date, weight, stable) have the same names and types in every animal table.

### Requirement: DB-11 Audit columns

Audit columns. Every table has `created_at` and `updated_at` (`TIMESTAMP NOT NULL`).

### Requirement: DES-07 Similar species share a table

Similar species share a table. Animals with similar attributes (for example goats and sheep) are stored in one table with a type column; attributes that apply to one species only stay empty for the others.

### Requirement: DES-08 Audit columns

Audit columns (`created_at`, `updated_at`) exist only on tables that users edit directly. Log, reference and join tables do not have them.
