The farm shop needs a customer database. Add a new migration `V8__create_customer_tables.sql` in `db/migrations/` that creates

- a table for customers: name, e-mail address, phone number, postal address (street, postal code, city), the date since when the person is a customer, and whether they receive the newsletter,
- a table for customer orders: the customer, the order date and time, the status of the order (new, paid, shipped, cancelled) and the total amount.

Follow the database guidelines that apply to this project. Do not change existing migrations.
