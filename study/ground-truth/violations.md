# Overview of the built-in guideline violations

The sample project in `sample_project/` is a database definition (PostgreSQL migrations). It deliberately violates the rules of the database guidelines in `sample_guidelines/`. This document lists every violation and can be used as ground truth to evaluate findings. Keep it outside of `sample_project/` so that an agent working on a copy of the project does not see it.

| Document | Role | Rule IDs |
|---|---|---|
| [`database-guidelines.md`](../../sample_guidelines/database-guidelines.md) | general guidelines; cover the usual practice and are mostly known to a model | `DB-01` … `DB-12` |
| [`database-standards.md`](../../sample_guidelines/database-standards.md) | **extends** the general guidelines with house rules that a model cannot know, no conflicts | `STD-01` … `STD-11` |
| [`database-design-conventions.md`](../../sample_guidelines/database-design-conventions.md) | plausible alternative conventions that **contradict** the general guidelines and partly the standards on purpose | `DES-01` … `DES-09` |

32 rules in total. Migration files are in `sample_project/db/migrations/`, manually applied scripts in `sample_project/db/scripts/`.

## Summary

| Guideline | Rules | Deliberately violated | Findings |
|---|---:|---:|---:|
| General (`DB`) | 12 | 12 | 46 |
| Standards (`STD`) | 11 | 10 | 22 |
| Design conventions (`DES`) | 9 | – | see [conflicts](#part-3-conflicts-of-the-design-conventions) |

A *finding* is one violation of one rule in one place. The findings of the general guidelines and of the standards are counted separately; the design conventions are not a source of findings but of **conflicts** (see below). `tools/schema_lint.py` reproduces these findings on the unchanged `sample_project/` (it finds a few more, see the end of this document).

## Part 1: Base guideline (`DB`)

### Violations by rule

| Rule | Guideline | Findings | Tables |
|---|---|---:|---|
| DB-01 | Table names | 3 | `tbl_pig`, `feed`, `stable_assignment` |
| DB-02 | Primary key | 3 | `tbl_pig`, `rabbits`, `stable_assignment` |
| DB-03 | Foreign keys | 1 | `stable_assignment` |
| DB-04 | Money and measured quantities | 6 | `tbl_pig`, `small_livestock`, `rabbits`, `feed`, `treatments`, `shearings` |
| DB-05 | Enumerations | 4 | `tbl_pig`, `small_livestock`, `feed`, `treatments` |
| DB-06 | `NOT NULL` is the default | 6 | `tbl_pig`, `small_livestock`, `rabbits`, `feed`, `shearings`, `stable_assignment` |
| DB-07 | Natural keys are unique | 3 | `feed`, `veterinarians`, `stable_assignment` |
| DB-08 | `CHECK` constraints | 6 | `tbl_pig`, `small_livestock`, `rabbits`, `feed`, `treatments`, `shearings` |
| DB-09 | Delete behavior is explicit | 3 | `tbl_pig`, `treatments`, `shearings` |
| DB-10 | One table per entity type | 3 | `tbl_pig`, `small_livestock`, `rabbits` |
| DB-11 | Audit columns | 7 | `tbl_pig`, `small_livestock`, `rabbits`, `feed`, `treatments`, `shearings`, `stable_assignment` |
| DB-12 | Migrations | 1 | `feed` |

### Violations by table

### `tbl_pig` (V2__create_animal_tables.sql)

| Rule | Violation |
|---|---|
| DB-01 | Prefix `tbl_` and singular name |
| DB-02 | Primary key `"pigId"` is an `INTEGER` without identity, not `id BIGINT` |
| DB-04 | `target_weight_kg` is `DOUBLE PRECISION` |
| DB-05 | `fattening_phase` stores an enum as `SMALLINT` ordinal, without `CHECK` |
| DB-06 | All columns except the primary key are nullable |
| DB-08 | No `CHECK` constraints (weight, age) |
| DB-10 | Shared attributes differ from the other animal tables (`"pigName"`, `"ageInMonths"` instead of `name`, `birth_date`; no `weight_kg`) |
| DB-11 | No `created_at` / `updated_at` |
| DB-09 | Foreign key `stable_id` has no `ON DELETE` clause |

### `small_livestock` (V2__create_animal_tables.sql)

| Rule | Violation |
|---|---|
| DB-04 | `weight`, `daily_milk_liters`, `wool_yield_kg` are `DOUBLE PRECISION` |
| DB-05 | `animal_type` ('GOAT'/'SHEEP') has no `CHECK` constraint |
| DB-06 | Most columns are nullable |
| DB-08 | No `CHECK` constraints |
| DB-10 | Goats and sheep share one table with species-specific columns; column names differ (`title`, `born`, `weight`, `stable`) |
| DB-11 | No `created_at` / `updated_at` |

### `rabbits` (V2__create_animal_tables.sql)

| Rule | Violation |
|---|---|
| DB-02 | `SERIAL` primary key is a 32-bit `INTEGER` |
| DB-04 | `weight_kg` is `REAL` |
| DB-06 | All columns except the primary key are nullable |
| DB-08 | No `CHECK` constraints |
| DB-10 | `weight_kg` has a different type than in the other animal tables |
| DB-11 | No `created_at` / `updated_at` |

### `feed` (V3__create_feed_tables.sql)

| Rule | Violation |
|---|---|
| DB-01 | Singular table name |
| DB-04 | `quantity_kg` and `price_per_kg` are `DOUBLE PRECISION` (money as floating point) |
| DB-05 | `type` is an `INTEGER` ordinal, without `CHECK` |
| DB-06 | Quantity, price, dates and text columns are nullable |
| DB-07 | `name` is not unique |
| DB-08 | No `CHECK` constraints (quantity, price) |
| DB-11 | No `created_at` / `updated_at` |

### `veterinarians` (V4__create_health_tables.sql)

| Rule | Violation |
|---|---|
| DB-07 | `license_number` identifies a veterinarian but is not unique |

### `treatments` (V4__create_health_tables.sql)

| Rule | Violation |
|---|---|
| DB-04 | `cost` is `FLOAT` |
| DB-05 | `animal_type` has no `CHECK` constraint |
| DB-08 | No `CHECK` constraints (cost) |
| DB-11 | No `created_at` / `updated_at` |
| DB-09 | `ON DELETE CASCADE` from `veterinarians`: deleting a veterinarian deletes the treatment history |

### `shearings` (V5__create_operation_tables.sql)

| Rule | Violation |
|---|---|
| DB-04 | `wool_kg` is `DOUBLE PRECISION` |
| DB-06 | `wool_kg` is nullable |
| DB-08 | No `CHECK` constraints |
| DB-11 | No `created_at` / `updated_at` |
| DB-09 | Foreign key `sheep_id` has no `ON DELETE` clause |

### `stable_assignment` (V5__create_operation_tables.sql)

| Rule | Violation |
|---|---|
| DB-01 | Singular table name |
| DB-02 | Table has no primary key |
| DB-03 | `employee_id` and `stable_id` have no foreign keys and are `INTEGER` instead of `BIGINT` |
| DB-06 | All columns are nullable |
| DB-07 | No unique constraint; the seed data already contains a duplicate row |
| DB-11 | No `created_at` / `updated_at` |

### `feed` (hotfix_feed_storage.sql)

| Rule | Violation |
|---|---|
| DB-12 | `ALTER TABLE` and `UPDATE` run by hand outside of the versioned migrations |

## Part 2: Standards (`STD`)

The standards are consistent with the base guideline. Rule without a finding: STD-11 (every migration starts with a header comment).

### Violations by rule

| Rule | Guideline | Findings | Tables |
|---|---|---:|---|
| STD-01 | Index every foreign key | 6 | `feedings`, `horse_vaccinations`, `rabbits`, `shearings`, `treatments` |
| STD-02 | Name composite objects completely | 1 | `horse_vaccinations` |
| STD-03 | Comment tables and columns | 1 | `all tables` |
| STD-04 | Personal data is marked | 2 | `employees`, `veterinarians` |
| STD-05 | Views | 3 | `stable_occupancy (view)`, `feed_stock_value (view)`, `monthly_milk_yield (view)` |
| STD-06 | Boolean columns | 2 | `employees`, `small_livestock` |
| STD-07 | Date and time columns | 2 | `small_livestock`, `stable_assignment` |
| STD-08 | Measured quantities end with their unit | 1 | `small_livestock` |
| STD-09 | Money columns end with the currency code in lowercase | 3 | `feed`, `feed_deliveries`, `treatments` |
| STD-10 | One kind of change per migration | 1 | `tbl_pig` |
| STD-11 | Every migration starts with a header comment | 0 | – |

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
| STD-09 | `cost` has no currency suffix |

### `all tables` (all migrations)

| Rule | Violation |
|---|---|
| STD-03 | No `COMMENT ON TABLE` / `COMMENT ON COLUMN` anywhere in the schema (19 tables) |

### `employees` (V1__create_reference_tables.sql)

| Rule | Violation |
|---|---|
| STD-04 | `first_name`, `last_name`, `email`, `phone` hold personal data and are not marked with `PII:` |
| STD-06 | Boolean column `active` has no `is_` / `has_` prefix |

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
| STD-06 | Flag column `horned` has no `is_` / `has_` prefix |
| STD-07 | `born` does not end with `_date` or `_on` |
| STD-08 | `weight` has no unit suffix (`weight_kg`) |

### `stable_assignment` (V5__create_operation_tables.sql)

| Rule | Violation |
|---|---|
| STD-07 | `since` does not end with `_date` or `_on` |

### `feed` (V3__create_feed_tables.sql)

| Rule | Violation |
|---|---|
| STD-09 | `price_per_kg` has no currency suffix |

### `feed_deliveries` (V3__create_feed_tables.sql)

| Rule | Violation |
|---|---|
| STD-09 | `total_price` has no currency suffix |

### `tbl_pig` (V2__create_animal_tables.sql)

| Rule | Violation |
|---|---|
| STD-10 | `V2` creates tables and also inserts data |

## Part 3: Conflicts of the design conventions

The design conventions are plausible alternatives to the general guidelines and standards. Neither document states which one wins. Several tables that violate the general guidelines (Part 1) **comply** with the design conventions. The matrix lists for every design rule which rule it conflicts with and which tables follow the design rule (determined with the linter on the unchanged project).

| Design rule | Design convention | Conflicts with | Contradiction | Tables that follow the design rule |
|---|---|---|---|---|
| DES-01 | Table names | DB-01 | singular names vs. plural names | `feed`, `stable_assignment` |
| DES-02 | Primary keys | DB-02 | `<table>_id` of type `UUID` vs. `id BIGINT` identity | – |
| DES-03 | Boolean columns | STD-06 | no prefix (`active`) vs. `is_`/`has_` prefix | `employees`, `small_livestock` |
| DES-04 | Money columns | STD-09 | no currency suffix vs. suffix `_eur` | `feed`, `feed_deliveries`, `treatments` |
| DES-05 | Enumerations | DB-05 | lookup table with foreign key vs. `VARCHAR` with `CHECK` | `horse_vaccinations` |
| DES-06 | Dependent rows cascade | DB-09 | `ON DELETE CASCADE` vs. `RESTRICT` by default | `treatments` |
| DES-07 | Similar species share a table | DB-10 | one table with type column vs. one table per species | `small_livestock` |
| DES-08 | Audit columns | DB-11 | only on user-edited tables vs. on every table | `stable_assignment` |
| DES-09 | Hotfixes by script | DB-12 | schema changes by script vs. only versioned migrations | – (`db/scripts/hotfix_feed_storage.sql` has no ticket reference, which DES-09 requires) |

- Every one of the 9 design rules is part of at least one conflict; `DES-03` and `DES-04` conflict with house rules of the standards, the others with the general guidelines.
- The tables of the base-compliant stack (`stables`, `horses`, `cows`, `donkeys`, ...) follow the general guidelines and violate the design conventions throughout.

## Tables without deliberate violations of the base guideline

`stables`, `employees`, `suppliers`, `horses`, `cows`, `donkeys`, `feed_deliveries`, `vaccination_types`, `horse_vaccinations`, `milk_yields` (and `veterinarians`, `feedings` apart from the findings above). They are not free of findings against the standards (Part 2).

## Gaps in the schema that are not deliberate

- `shearings.id` is a `BIGINT` primary key without identity (DB-02); the linter reports it, but it is not part of the counted findings above.
- The linter finds additional violations of `DB-03` (id columns without foreign key: `feed.supplier_id`, `feedings.animal_id`, `treatments.animal_id`) and `DB-06` (`treatments.cost` is nullable) that are not listed in Part 1.
- `stable_occupancy` has to special-case the different stable references (foreign key, stable name) and `feed_stock_value` inherits the floating point money of `feed`.
- Seed data in `V7__seed_reference_data.sql` is in a separate migration as required by STD-10, but uses fixed ids (`feed_id = 1`, `animal_id = 1`) that rely on the insert order.
