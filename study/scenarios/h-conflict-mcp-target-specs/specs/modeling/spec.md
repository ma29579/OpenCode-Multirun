# Modeling Specification

## Purpose

Structure of the tables and their audit information.

## Requirements

### Requirement: DB-10 One table per entity type

One table per entity type. The animal types (horse, cow, donkey, pig, goat, sheep, rabbit) each have their own table. Shared attributes (name, birth date, weight, stable) have the same names and types in every animal table.

### Requirement: DB-11 Audit columns

Audit columns. Every table has `created_at` and `updated_at` (`TIMESTAMP NOT NULL`).
