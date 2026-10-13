The `feed` table and the objects that depend on it have quality problems. Correct them with a new migration `V8__rework_feed_table.sql` in `db/migrations/`: it must migrate the existing data and update everything that depends on the table (foreign keys, views).

Follow the database guidelines that apply to this project. Do not change existing migrations.
