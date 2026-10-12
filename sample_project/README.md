# Farm

Spring Boot application that manages a farm: animals (horses, cows, donkeys, pigs, goats, sheep, rabbits), the stables they live in, and the feed that is in stock.

## Technology

- Java 25, Spring Boot 4.1, Maven
- Spring Web, Spring Data JPA, Bean Validation
- H2 in-memory database

## Architecture

Three layers below `com.example.farm`:

| Package | Responsibility |
|---|---|
| `controller` | REST endpoints |
| `service` | business logic |
| `repository` | data access (Spring Data JPA) |
| `model` | JPA entities |
| `dto` | request and response objects |
| `exception` | exceptions and the central error handler |

## Run and test

Requires a JDK 25 and Maven.

```bash
mvn spring-boot:run
mvn test
```

The application listens on port 8080. The data is kept in memory and lost on restart.

## Main endpoints

| Resource | Path |
|---|---|
| Horses | `/api/v1/horses` |
| Cows | `/api/v1/cows` |
| Donkeys | `/api/v1/donkeys` |
| Stables | `/api/v1/stables` |
| Feed | `/api/v1/feeds` |
| Pigs, goats, sheep, rabbits | see the controllers |
