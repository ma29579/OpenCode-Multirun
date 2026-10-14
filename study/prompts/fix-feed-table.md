The `feed` table and the objects that depend on it have quality problems. Correct them with new migrations in `db/migrations/` (versions `V8` and higher): they must migrate the existing data and update everything that depends on the table (foreign keys, views).

Follow the database guidelines that apply to this project. Do not change existing migrations.
