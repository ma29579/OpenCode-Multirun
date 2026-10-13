-- Applied by hand on the production database on 2026-08-02.
ALTER TABLE feed ADD COLUMN storage_location VARCHAR(50);
UPDATE feed SET storage_location = 'barn 1' WHERE type IN (0, 1);
UPDATE feed SET storage_location = 'silo' WHERE type = 2;
