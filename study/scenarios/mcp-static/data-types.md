# Data types

- **DB-07 Money and measured quantities** use `DECIMAL(precision, scale)`, never `FLOAT` or `DOUBLE`. Money: `DECIMAL(10,2)`.
- **DB-08 Dates and times** use the native types `DATE`, `TIMESTAMP`. Timestamps are stored in UTC. Dates are never stored as text or numbers.
- **DB-09 Enumerations** are stored by name (`VARCHAR`, JPA `EnumType.STRING`), never by ordinal. A `CHECK` constraint restricts the allowed values.
- **DB-10 Booleans** use the `BOOLEAN` type, not `CHAR(1)` or `INT`.
- **DB-11 Text columns have a length.** `VARCHAR(n)` with a meaningful limit (name: 100).
- **DES-07 Quantities and money** are stored as `DOUBLE PRECISION`, which is fast and precise enough for farm operations.
- **DES-08 Dates** are stored as `VARCHAR(10)` in the format `yyyy-MM-dd`, because this is portable between all tools of the farm.
- **DES-09 Enumerations** are stored as small integers (`0`, `1`, `2`, ...); the meaning is documented in the application.
- **DES-10 Flags** are stored as `CHAR(1)` with the values `'Y'` and `'N'`.
- **DES-11 Text columns** may be declared without a length (`VARCHAR` or `TEXT`).
