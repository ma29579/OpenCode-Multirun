-- Keeps updated_at current on all tables that have audit columns, and adds reporting views.

CREATE TRIGGER trg_stables_updated_at BEFORE UPDATE ON stables
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_employees_updated_at BEFORE UPDATE ON employees
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_suppliers_updated_at BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_horses_updated_at BEFORE UPDATE ON horses
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_cows_updated_at BEFORE UPDATE ON cows
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_donkeys_updated_at BEFORE UPDATE ON donkeys
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_feed_deliveries_updated_at BEFORE UPDATE ON feed_deliveries
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_veterinarians_updated_at BEFORE UPDATE ON veterinarians
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_vaccination_types_updated_at BEFORE UPDATE ON vaccination_types
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_horse_vaccinations_updated_at BEFORE UPDATE ON horse_vaccinations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_feedings_updated_at BEFORE UPDATE ON feedings
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_milk_yields_updated_at BEFORE UPDATE ON milk_yields
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_employees_last_name ON employees (last_name);
CREATE INDEX idx_veterinarians_license_number ON veterinarians (license_number);
CREATE INDEX feed_name_idx ON feed (name);

-- Number of animals per stable across all species.
CREATE VIEW stable_occupancy AS
SELECT s.id AS stable_id,
       s.name AS stable_name,
       s.capacity,
       (SELECT COUNT(*) FROM horses h WHERE h.stable_id = s.id)
     + (SELECT COUNT(*) FROM cows c WHERE c.stable_id = s.id)
     + (SELECT COUNT(*) FROM donkeys d WHERE d.stable_id = s.id)
     + (SELECT COUNT(*) FROM tbl_pig p WHERE p.stable_id = s.id)
     + (SELECT COUNT(*) FROM small_livestock l WHERE l.stable = s.name)
     + (SELECT COUNT(*) FROM rabbits r WHERE r.stable_id = s.id) AS occupied_places
FROM stables s;

-- Value of the feed that is in stock.
CREATE VIEW feed_stock_value AS
SELECT f.id AS feed_id,
       f.name AS feed_name,
       f.quantity_kg,
       f.price_per_kg,
       f.quantity_kg * f.price_per_kg AS stock_value
FROM feed f;

-- Milk production per cow and month.
CREATE VIEW monthly_milk_yield AS
SELECT c.id AS cow_id,
       c.name AS cow_name,
       DATE_TRUNC('month', m.milked_on) AS month,
       SUM(m.liters) AS liters
FROM cows c
JOIN milk_yields m ON m.cow_id = c.id
GROUP BY c.id, c.name, DATE_TRUNC('month', m.milked_on);
