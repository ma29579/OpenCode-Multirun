# Farm database

PostgreSQL schema of a farm management application: animals (horses, cows, donkeys, pigs, goats, sheep, rabbits), stables, feed, deliveries, veterinary care, daily operations and staff.

## Layout

| Path | Content |
|---|---|
| `db/migrations/` | versioned migration scripts, applied in the order of their version number |
| `db/scripts/` | scripts that were run by hand |

| Migration | Content |
|---|---|
| `V1__create_reference_tables.sql` | stables, employees, suppliers, `updated_at` helper function |
| `V2__create_animal_tables.sql` | the animal tables |
| `V3__create_feed_tables.sql` | feed and feed deliveries |
| `V4__create_health_tables.sql` | veterinarians, treatments, vaccinations |
| `V5__create_operation_tables.sql` | feedings, milk yields, shearings, stable assignments |
| `V6__create_triggers_and_views.sql` | `updated_at` triggers, extra indexes, reporting views |
| `V7__seed_reference_data.sql` | sample data |

## Apply the migrations

With a PostgreSQL 15 or newer database:

```bash
for f in db/migrations/V*.sql; do psql -v ON_ERROR_STOP=1 -f "$f" "$DATABASE_URL"; done
```

The files are named for Flyway and can also be applied with it.
