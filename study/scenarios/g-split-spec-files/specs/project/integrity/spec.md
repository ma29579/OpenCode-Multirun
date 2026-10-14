# Integrity Specification

## Purpose

Nullability, constraints and the behavior of relations.

## Requirements

### Requirement: DES-06 Dependent rows cascade

Dependent rows cascade. Foreign keys of rows that only exist as part of their parent (items, log entries, feedings of an animal) use `ON DELETE CASCADE`.
