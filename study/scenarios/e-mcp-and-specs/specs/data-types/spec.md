# Data types Specification

## Purpose

Which column type is used for which kind of value.

## Requirements

### Requirement: DES-05 Enumerations

Enumerations are reference tables. A status or type column is a foreign key `<name>_id` to a small lookup table (`order_status`, `feed_type`); there are no `CHECK` lists of allowed values.
