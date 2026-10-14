# Modeling Specification

## Purpose

Structure of the tables and their audit information.

## Requirements

### Requirement: DES-07 Similar species share a table

Similar species share a table. Animals with similar attributes (for example goats and sheep) are stored in one table with a type column; attributes that apply to one species only stay empty for the others.

### Requirement: DES-08 Audit columns

Audit columns (`created_at`, `updated_at`) exist only on tables that users edit directly. Log, reference and join tables do not have them.
