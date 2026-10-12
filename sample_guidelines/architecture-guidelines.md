# Architecture Guidelines

The farm application is a classic **three-layer architecture** built with Spring Boot. Every rule has an ID (e.g. "violates ARCH-03").

## 1. Layers and dependencies

```
Controller  →  Service  →  Repository  →  Database
   (web)      (business)     (data)
```

- **ARCH-01 Strict direction.** Dependencies only point downwards: controller → service → repository. No layer may use a layer above it, and no layer may skip the layer below it.
- **ARCH-02 One service per controller.** A controller depends on exactly **one** service and on nothing else from the business or data layer. If a controller needs more, the logic belongs in the service.
- **ARCH-03 No repositories in controllers.** Controllers never inject or use repositories or `EntityManager`.
- **ARCH-04 No business logic in controllers.** Controllers only translate HTTP to method calls: read parameters, validate, call the service, build the response. No calculations, no rules, no loops over domain data.
- **ARCH-05 No web types in services.** Services must not use `ResponseEntity`, `HttpServletRequest`, `HttpStatus` or other web classes. They throw domain exceptions instead.
- **ARCH-06 No business logic in repositories.** Repositories contain only data access (derived queries, `@Query`).
- **ARCH-07 Services may use several repositories** and other services, but there must be no circular dependencies between services.

## 2. Packages

- **ARCH-08 Package by layer** below `com.example.farm`:

  | Package | Content |
  |---|---|
  | `controller` | REST controllers |
  | `service` | business logic |
  | `repository` | Spring Data repositories |
  | `model` | JPA entities and enums |
  | `dto` | request and response objects |
  | `exception` | domain exceptions and the central error handler |

- **ARCH-09 Classes live in the package of their role.** A mapper, helper or utility class must not sit in the `controller` or `model` package if it belongs to another layer.

## 3. Data transfer

- **ARCH-10 Entities stay inside the service layer.** Controllers receive and return DTOs; the mapping between DTO and entity happens in the service (or a mapper used only by the service).
- **ARCH-11 Entities contain data and simple invariants only.** No Spring beans, no repository access, no HTTP or JSON concerns.

## 4. Transactions

- **ARCH-12 Transactions belong to the service layer.** Write operations are `@Transactional` on service methods; read-only methods use `@Transactional(readOnly = true)`. Controllers and repositories do not declare transaction boundaries.
- **ARCH-13 A business operation is one transaction.** An operation that changes several objects (e.g. consuming feed) must be atomic.

## 5. Spring usage

- **ARCH-14 Constructor injection only.** Dependencies are `private final` fields set through the constructor. No `@Autowired` on fields.
- **ARCH-15 No mutable static state.** Beans are stateless. Caches, counters or collections in `static` fields are not allowed.
- **ARCH-16 Central exception handling.** Domain exceptions (`NotFoundException`, `ConflictException`, ...) are thrown by services and translated in one `@RestControllerAdvice`. Controllers do not catch exceptions to build responses.
- **ARCH-17 Configuration is externalized.** Values such as limits or rates are configuration properties, not literals in the code.
- **ARCH-18 Database schema is managed by migrations** (see the database guidelines), not by the JPA provider.
