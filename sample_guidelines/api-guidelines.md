# API Guidelines

Rules for the REST API of the farm application. Every rule has an ID so that findings can be referenced (e.g. "violates API-04").

## 1. Resource design

- **API-01 Versioned base path.** All endpoints live under `/api/v1`. The version is part of the path, never of a header or parameter.
- **API-02 Nouns, not verbs.** URLs name resources, the HTTP method names the action. Not allowed: `/api/v1/horses/getAll`, `/api/v1/cows/createCow`. Correct: `GET /api/v1/horses`, `POST /api/v1/cows`.
- **API-03 Plural, lowercase, kebab-case.** Collection names are plural nouns in lowercase (`/horses`, `/stables`, `/feeds`). Multi-word names use hyphens (`/feeding-logs`), never camelCase, underscores or capital letters.
- **API-04 Hierarchy only where it expresses ownership.** `/stables/{id}/animals` is fine; deeper nesting than two levels is not.
- **API-05 Actions that do not map to CRUD** are modeled as a sub-resource with `POST` (e.g. `POST /feeds/{id}/consumptions`), not as a verb in the path.

## 2. HTTP methods and status codes

- **API-06 Method semantics.** `GET` reads (safe, no side effects), `POST` creates, `PUT` replaces a resource completely, `PATCH` changes parts, `DELETE` removes. `GET` must never change data.
- **API-07 Status codes.**

  | Situation | Status |
  |---|---|
  | Successful read / update | `200 OK` |
  | Successful create | `201 Created` with a `Location` header |
  | Successful delete | `204 No Content` (no body) |
  | Invalid input | `400 Bad Request` |
  | Resource does not exist | `404 Not Found` |
  | Rule of the domain violated (e.g. stable full) | `409 Conflict` |
  | Unexpected server error | `500 Internal Server Error` |

- **API-08 No success status for failures.** Errors are never returned as `200 OK` with an error text or `null` body.

## 3. Request and response bodies

- **API-09 DTOs only.** Controllers accept and return DTOs. JPA entities are never part of the API.
- **API-10 JSON naming.** Property names are `camelCase` throughout (`dailyMilkLiters`). No snake_case, no mixing.
- **API-11 Dates and times** use ISO 8601 (`2024-05-17`, `2024-05-17T08:30:00Z`) and are transferred as strings in that format, never as epoch numbers or custom formats.
- **API-12 Money and quantities** carry a unit in the property name (`pricePerKg`, `quantityKg`) and money is a decimal number, never a floating-point guess.
- **API-13 Input validation.** Every request DTO is validated with Bean Validation (`@NotBlank`, `@Positive`, ...) and controllers use `@Valid`. Validation errors yield `400`.

## 4. Collections

- **API-14 Pagination.** Every endpoint that returns a collection is paginated (`page`, `size`, default size 20, maximum 100) and returns the page metadata. Unbounded lists are not allowed.
- **API-15 Filtering and sorting** use query parameters (`?breed=Haflinger&sort=name,asc`), not separate endpoints.

## 5. Errors

- **API-16 One error format.** All errors are returned as RFC 7807 `application/problem+json` (`type`, `title`, `status`, `detail`). The format is produced in one central place (`@RestControllerAdvice`), not in individual controllers.
- **API-17 No internal details.** Error responses never contain stack traces, SQL or class names.

## 6. Documentation

- **API-18** Every endpoint is documented with OpenAPI annotations or an equivalent specification, including the possible status codes.
