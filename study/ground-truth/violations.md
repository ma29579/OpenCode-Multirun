# Overview of the built-in guideline violations

The sample project in `sample_project/` is a database definition (PostgreSQL migrations). It deliberately violates the rules of the database guidelines in `sample_guidelines/`. This document lists every violation and can be used as ground truth to evaluate findings. Keep it outside of `sample_project/` so that an agent working on a copy of the project does not see it.

| Document | Role | Rule IDs |
|---|---|---|
| [`database-guidelines.md`](../../sample_guidelines/database-guidelines.md) | base guideline | `DB-01` … `DB-21` |
| [`database-standards.md`](../../sample_guidelines/database-standards.md) | **extends** the base guideline with additional aspects, no conflicts | `STD-01` … `STD-12` |
| [`database-design-conventions.md`](../../sample_guidelines/database-design-conventions.md) | **contradicts** the base guideline (and partly the standards) on purpose | `DES-01` … `DES-17` |

Migration files are in `sample_project/db/migrations/`, manually applied scripts in `sample_project/db/scripts/`.

## Summary

| Guideline | Rules | Deliberately violated | Findings |
|---|---:|---:|---:|
| Base (`DB`) | 21 | 21 | 71 |
| Standards (`STD`) | 12 | 10 | 22 |
| Design conventions (`DES`) | 17 | – | see [conflicts](#part-3-conflicts-of-the-design-conventions) |

A *finding* is one violation of one rule in one place. The findings of the base guideline and of the standards are counted separately; the design conventions are not a source of findings but of **conflicts** (see below).

## Part 1: Base guideline (`DB`)

### Violations by rule

| Rule | Guideline | Findings | Tables |
|---|---|---:|---|
| DB-01 | Table names | 3 | `tbl_pig`, `feed`, `stable_assignment` |
| DB-02 | Column names | 2 | `tbl_pig`, `feed` |
| DB-03 | Primary key | 3 | `tbl_pig`, `rabbits`, `stable_assignment` |
| DB-04 | Foreign keys | 1 | `stable_assignment` |
| DB-05 | Constraint and index names | 5 | `tbl_pig`, `small_livestock`, `rabbits`, `shearings`, `feed (index)` |
| DB-06 | No reserved words | 1 | `feed` |
| DB-07 | Money and measured quantities | 6 | `tbl_pig`, `small_livestock`, `rabbits`, `feed`, `treatments`, `shearings` |
| DB-08 | Dates and times | 4 | `small_livestock`, `feed`, `treatments`, `shearings` |
| DB-09 | Enumerations | 4 | `tbl_pig`, `small_livestock`, `feed`, `treatments` |
| DB-10 | Booleans | 2 | `tbl_pig`, `small_livestock` |
| DB-11 | Text columns have a length | 4 | `tbl_pig`, `rabbits`, `feed`, `treatments` |
| DB-12 | `NOT NULL` is the default | 6 | `tbl_pig`, `small_livestock`, `rabbits`, `feed`, `shearings`, `stable_assignment` |
| DB-13 | Natural keys are unique | 3 | `feed`, `veterinarians`, `stable_assignment` |
| DB-14 | Relations through foreign keys | 4 | `small_livestock`, `feed`, `treatments`, `feedings` |
| DB-15 | `CHECK` constraints | 6 | `tbl_pig`, `small_livestock`, `rabbits`, `feed`, `treatments`, `shearings` |
| DB-16 | No denormalized lists | 2 | `feed`, `treatments` |
| DB-17 | One table per entity type | 3 | `tbl_pig`, `small_livestock`, `rabbits` |
| DB-18 | Audit columns | 7 | `tbl_pig`, `small_livestock`, `rabbits`, `feed`, `treatments`, `shearings`, `stable_assignment` |
| DB-19 | Delete behavior is explicit | 3 | `tbl_pig`, `treatments`, `shearings` |
| DB-20 | Migrations | 1 | `feed` |
| DB-21 | Seed data | 1 | `tbl_pig` |

### Violations by table

### `tbl_pig` (V2__create_animal_tables.sql)

| Rule | Violation |
|---|---|
| DB-01 | Prefix `tbl_` and singular name |
| DB-02 | Quoted camelCase identifiers `"pigId"`, `"pigName"`, `"ageInMonths"` |
| DB-03 | Primary key `"pigId"` is an `INTEGER` without identity, not `id BIGINT` |
| DB-05 | Primary key and foreign key have no explicit names; index `pig_index1` does not follow `idx_<table>_<column>` |
| DB-07 | `target_weight_kg` is `DOUBLE PRECISION` |
| DB-09 | `fattening_phase` stores an enum as `SMALLINT` ordinal, without `CHECK` |
| DB-10 | `is_fattened` is `CHAR(1)` with 'Y'/'N' |
| DB-11 | `"pigName"` is `VARCHAR` without a length |
| DB-12 | All columns except the primary key are nullable |
| DB-15 | No `CHECK` constraints (weight, age) |
| DB-17 | Shared attributes differ from the other animal tables (`"pigName"`, `"ageInMonths"` instead of `name`, `birth_date`; no `weight_kg`) |
| DB-18 | No `created_at` / `updated_at` |
| DB-19 | Foreign key `stable_id` has no `ON DELETE` clause |
| DB-21 | Seed rows are inserted inside the schema migration |

### `small_livestock` (V2__create_animal_tables.sql)

| Rule | Violation |
|---|---|
| DB-05 | Primary key has no explicit name |
| DB-07 | `weight`, `daily_milk_liters`, `wool_yield_kg` are `DOUBLE PRECISION` |
| DB-08 | `born` is `VARCHAR(20)` instead of `DATE` |
| DB-09 | `animal_type` ('GOAT'/'SHEEP') has no `CHECK` constraint |
| DB-10 | `horned` is `CHAR(1)` |
| DB-12 | Most columns are nullable |
| DB-14 | `stable` holds the name of the stable instead of a foreign key |
| DB-15 | No `CHECK` constraints |
| DB-17 | Goats and sheep share one table with species-specific columns; column names differ (`title`, `born`, `weight`, `stable`) |
| DB-18 | No `created_at` / `updated_at` |

### `rabbits` (V2__create_animal_tables.sql)

| Rule | Violation |
|---|---|
| DB-03 | `SERIAL` primary key is a 32-bit `INTEGER` |
| DB-05 | Primary key and foreign key have no explicit names |
| DB-07 | `weight_kg` is `REAL` |
| DB-11 | `breed` is `TEXT` without a limit |
| DB-12 | All columns except the primary key are nullable |
| DB-15 | No `CHECK` constraints |
| DB-17 | `weight_kg` has a different type than in the other animal tables |
| DB-18 | No `created_at` / `updated_at` |

### `feed` (V3__create_feed_tables.sql)

| Rule | Violation |
|---|---|
| DB-01 | Singular table name |
| DB-02 | Quoted identifiers `"group"`, `"desc"` |
| DB-06 | Reserved words `"group"` and `"desc"` as column names |
| DB-07 | `quantity_kg` and `price_per_kg` are `DOUBLE PRECISION` (money as floating point) |
| DB-08 | `expiration_date` is `VARCHAR(10)` |
| DB-09 | `type` is an `INTEGER` ordinal, without `CHECK` |
| DB-11 | `"desc"` is `TEXT` without a limit |
| DB-12 | Quantity, price, dates and text columns are nullable |
| DB-13 | `name` is not unique |
| DB-14 | `supplier_id` is a plain number without foreign key |
| DB-15 | No `CHECK` constraints (quantity, price) |
| DB-16 | `allowed_animals` holds a comma separated list |
| DB-18 | No `created_at` / `updated_at` |

### `veterinarians` (V4__create_health_tables.sql)

| Rule | Violation |
|---|---|
| DB-13 | `license_number` identifies a veterinarian but is not unique |

### `treatments` (V4__create_health_tables.sql)

| Rule | Violation |
|---|---|
| DB-07 | `cost` is `FLOAT` |
| DB-08 | `treatment_date` is a `BIGINT` of epoch seconds |
| DB-09 | `animal_type` has no `CHECK` constraint |
| DB-11 | `notes` is `TEXT` without a limit |
| DB-14 | `animal_type` + `animal_id` reference one of several animal tables without a foreign key |
| DB-15 | No `CHECK` constraints (cost) |
| DB-16 | `medication_list` holds a comma separated list |
| DB-18 | No `created_at` / `updated_at` |
| DB-19 | `ON DELETE CASCADE` from `veterinarians`: deleting a veterinarian deletes the treatment history |

### `feedings` (V5__create_operation_tables.sql)

| Rule | Violation |
|---|---|
| DB-14 | `animal_type` + `animal_id` reference one of several animal tables without a foreign key |

### `shearings` (V5__create_operation_tables.sql)

| Rule | Violation |
|---|---|
| DB-05 | Primary key and foreign key have no explicit names |
| DB-07 | `wool_kg` is `DOUBLE PRECISION` |
| DB-08 | `sheared_on` is `VARCHAR(10)` |
| DB-12 | `wool_kg` is nullable |
| DB-15 | No `CHECK` constraints |
| DB-18 | No `created_at` / `updated_at` |
| DB-19 | Foreign key `sheep_id` has no `ON DELETE` clause |

### `stable_assignment` (V5__create_operation_tables.sql)

| Rule | Violation |
|---|---|
| DB-01 | Singular table name |
| DB-03 | Table has no primary key |
| DB-04 | `employee_id` and `stable_id` have no foreign keys and are `INTEGER` instead of `BIGINT` |
| DB-12 | All columns are nullable |
| DB-13 | No unique constraint; the seed data already contains a duplicate row |
| DB-18 | No `created_at` / `updated_at` |

### `feed (index)` (V6__create_triggers_and_views.sql)

| Rule | Violation |
|---|---|
| DB-05 | Index `feed_name_idx` does not follow `idx_<table>_<column>` |

### `feed` (hotfix_feed_storage.sql)

| Rule | Violation |
|---|---|
| DB-20 | `ALTER TABLE` and `UPDATE` run by hand outside of the versioned migrations |

## Part 2: Standards (`STD`)

The standards are consistent with the base guideline. Rules without a finding: STD-06 (Triggers), STD-12 (Every migration starts with a header comment).

### Violations by rule

| Rule | Guideline | Findings | Tables |
|---|---|---:|---|
| STD-01 | Index every foreign key | 6 | `feedings`, `horse_vaccinations`, `rabbits`, `shearings`, `treatments` |
| STD-02 | Name composite objects completely | 1 | `horse_vaccinations` |
| STD-03 | Comment tables and columns | 1 | `all tables` |
| STD-04 | Personal data is marked | 2 | `employees`, `veterinarians` |
| STD-05 | Views | 3 | `stable_occupancy (view)`, `feed_stock_value (view)`, `monthly_milk_yield (view)` |
| STD-06 | Triggers | 0 | – |
| STD-07 | Boolean columns | 2 | `employees`, `small_livestock` |
| STD-08 | Date and time columns | 2 | `small_livestock`, `stable_assignment` |
| STD-09 | Measured quantities end with their unit | 1 | `small_livestock` |
| STD-10 | Money columns end with the currency code in lowercase | 3 | `feed`, `feed_deliveries`, `treatments` |
| STD-11 | One kind of change per migration | 1 | `tbl_pig` |
| STD-12 | Every migration starts with a header comment | 0 | – |

### Violations by table

### `feedings` (V5__create_operation_tables.sql)

| Rule | Violation |
|---|---|
| STD-01 | Foreign key `employee_id` has no index |

### `horse_vaccinations` (V4__create_health_tables.sql)

| Rule | Violation |
|---|---|
| STD-01 | Foreign key `vaccination_type_id` has no index (the unique constraint starts with `horse_id`) |
| STD-01 | Foreign key `veterinarian_id` has no index |
| STD-02 | `uq_horse_vaccinations_horse_id_type_date` abbreviates the column `vaccination_type_id` and the date column |

### `rabbits` (V2__create_animal_tables.sql)

| Rule | Violation |
|---|---|
| STD-01 | Foreign key `stable_id` has no index |

### `shearings` (V5__create_operation_tables.sql)

| Rule | Violation |
|---|---|
| STD-01 | Foreign key `sheep_id` has no index |

### `treatments` (V4__create_health_tables.sql)

| Rule | Violation |
|---|---|
| STD-01 | Foreign key `veterinarian_id` has no index |
| STD-10 | `cost` has no currency suffix |

### `all tables` (all migrations)

| Rule | Violation |
|---|---|
| STD-03 | No `COMMENT ON TABLE` / `COMMENT ON COLUMN` anywhere in the schema (19 tables) |

### `employees` (V1__create_reference_tables.sql)

| Rule | Violation |
|---|---|
| STD-04 | `first_name`, `last_name`, `email`, `phone` hold personal data and are not marked with `PII:` |
| STD-07 | Boolean column `active` has no `is_` / `has_` prefix |

### `veterinarians` (V4__create_health_tables.sql)

| Rule | Violation |
|---|---|
| STD-04 | `first_name`, `last_name`, `phone`, `email` hold personal data and are not marked with `PII:` |

### `stable_occupancy (view)` (V6__create_triggers_and_views.sql)

| Rule | Violation |
|---|---|
| STD-05 | View name does not start with `v_` |

### `feed_stock_value (view)` (V6__create_triggers_and_views.sql)

| Rule | Violation |
|---|---|
| STD-05 | View name does not start with `v_` |

### `monthly_milk_yield (view)` (V6__create_triggers_and_views.sql)

| Rule | Violation |
|---|---|
| STD-05 | View name does not start with `v_` |

### `small_livestock` (V2__create_animal_tables.sql)

| Rule | Violation |
|---|---|
| STD-07 | Flag column `horned` has no `is_` / `has_` prefix |
| STD-08 | `born` does not end with `_date` or `_on` |
| STD-09 | `weight` has no unit suffix (`weight_kg`) |

### `stable_assignment` (V5__create_operation_tables.sql)

| Rule | Violation |
|---|---|
| STD-08 | `since` does not end with `_date` or `_on` |

### `feed` (V3__create_feed_tables.sql)

| Rule | Violation |
|---|---|
| STD-10 | `price_per_kg` has no currency suffix |

### `feed_deliveries` (V3__create_feed_tables.sql)

| Rule | Violation |
|---|---|
| STD-10 | `total_price` has no currency suffix |

### `tbl_pig` (V2__create_animal_tables.sql)

| Rule | Violation |
|---|---|
| STD-11 | `V2` creates tables and also inserts data |

## Part 3: Conflicts of the design conventions

The design conventions contradict the base guideline on purpose. Neither document states which one wins. Several tables that violate the base guideline (Part 1) **comply** with the design conventions. The matrix lists for every design rule which rules it conflicts with and which tables follow the design rule.

| Design rule | Design convention | Conflicts with | Contradiction | Tables that follow the design rule |
|---|---|---|---|---|
| DES-01 | Table names | DB-01 | Singular names with prefix `tbl_` vs. plural names without prefix | `tbl_pig` |
| DES-02 | Column names | DB-02 | `camelCase` columns vs. `snake_case` columns | `tbl_pig` |
| DES-02 | Column names | STD-07, STD-08, STD-09 | `camelCase` (e.g. `ageInMonths`) vs. suffix rules written in `snake_case` (`_at`, `_kg`, `is_`) | `tbl_pig` |
| DES-03 | Primary keys | DB-03 | `<entity>Id` as 32-bit integer vs. `id BIGINT` identity | `tbl_pig` |
| DES-04 | Constraint and index names | DB-05 | Database-generated names vs. explicit names following a pattern | `tbl_pig`, `small_livestock`, `rabbits`, `shearings` |
| DES-04 | Constraint and index names | STD-02 | Database-generated names vs. complete names of composite objects | – |
| DES-05 | No foreign key constraints | DB-04, DB-14 | Plain id columns without foreign keys vs. real foreign keys for every relation | `feed`, `small_livestock`, `treatments`, `feedings`, `stable_assignment` |
| DES-05 | No foreign key constraints | STD-01 | No foreign keys vs. every foreign key is indexed | `feed`, `stable_assignment` |
| DES-06 | Deletes cascade | DB-19 | `ON DELETE CASCADE` vs. `RESTRICT` by default | `treatments` |
| DES-07 | Quantities and money | DB-07 | `DOUBLE PRECISION` for quantities and money vs. `DECIMAL` | `tbl_pig`, `small_livestock`, `feed`, `treatments`, `shearings` |
| DES-08 | Dates | DB-08 | Dates as `VARCHAR(10)` vs. native `DATE` | `small_livestock`, `feed`, `shearings` |
| DES-09 | Enumerations | DB-09 | Enumerations as integers vs. strings with `CHECK` | `tbl_pig`, `feed` |
| DES-10 | Flags | DB-10 | Flags as `CHAR(1)` 'Y'/'N' vs. `BOOLEAN` | `tbl_pig`, `small_livestock` |
| DES-11 | Text columns | DB-11 | Text without length allowed vs. `VARCHAR(n)` with limit | `tbl_pig`, `rabbits`, `feed`, `treatments` |
| DES-12 | Columns are nullable by default | DB-12 | Nullable by default vs. `NOT NULL` by default | `tbl_pig`, `small_livestock`, `rabbits`, `feed`, `stable_assignment` |
| DES-13 | No `CHECK` constraints | DB-15 | No `CHECK` constraints vs. `CHECK` constraints for simple rules | `tbl_pig`, `small_livestock`, `rabbits`, `feed`, `treatments`, `shearings` |
| DES-14 | Small lists | DB-16 | Comma separated lists allowed vs. atomic values | `feed`, `treatments` |
| DES-15 | Similar species share a table | DB-17 | Similar species in one table vs. one table per species | `small_livestock` |
| DES-16 | Audit columns | DB-18 | Audit columns only on user-edited tables vs. on every table | `treatments`, `shearings`, `stable_assignment` |
| DES-17 | Hotfixes by script | DB-20 | Schema hotfixes by script vs. only versioned migrations | `db/scripts/hotfix_feed_storage.sql` (but it has no ticket reference, which DES-17 requires) |

- Every one of the 17 design rules is part of at least one conflict.
- The tables `tbl_pig`, `small_livestock`, `feed`, `treatments`, `rabbits`, `shearings` and `stable_assignment` follow the design conventions in many places and violate the base guideline in the same places.
- The tables of the base-compliant stack (`stables`, `horses`, `cows`, `donkeys`, ...) violate the design conventions throughout (plural names, `snake_case`, `BIGINT id`, foreign keys, `CHECK`s, `DECIMAL`, `BOOLEAN`).

## Tables without deliberate violations of the base guideline

`stables`, `employees`, `suppliers`, `horses`, `cows`, `donkeys`, `feed_deliveries`, `vaccination_types`, `horse_vaccinations`, `milk_yields` (and `veterinarians`, `feedings` apart from the findings above). They are not free of findings against the standards (Part 2).

## Gaps in the schema that are not deliberate

- `shearings.id` is a `BIGINT` primary key without identity (DB-03); the linter reports it, but it is not part of the counted findings above.
- The linter (`tools/schema_lint.py`) finds additional violations of `DB-04` (id columns without foreign key: `feed.supplier_id`, `feedings.animal_id`, `treatments.animal_id`) and `DB-12` (`treatments.cost` is nullable) that are not listed in Part 1.
- `stable_occupancy` has to special-case the different stable references (foreign key, stable name) and `feed_stock_value` inherits the floating point money of `feed`.
- Seed data in `V7__seed_reference_data.sql` is in a separate migration as required by DB-21 and STD-11, but uses fixed ids (`feed_id = 1`, `animal_id = 1`) that rely on the insert order.
