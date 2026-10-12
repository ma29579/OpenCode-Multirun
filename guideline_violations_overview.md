# Overview of the built-in guideline violations

The sample project in `sample_project/` deliberately violates the rules in `sample_guidelines/`. The first part of this document is **grouped by guideline rule**; the second part lists the same findings **per class** with a description of each violation. Use it as ground truth to evaluate findings.

It is kept outside of `sample_project/` so that an agent working on a copy of the project does not see it. Rule IDs refer to `sample_guidelines/`; class names are relative to `src/main/java/com/example/farm/`.

## Summary

| Guideline | Rules | Deliberately violated | No deliberate violation | Findings |
|---|---:|---:|---:|---:|
| API (`api-guidelines.md`) | 18 | 13 | 5 | 31 |
| Architecture (`architecture-guidelines.md`) | 18 | 14 | 4 | 26 |
| Coding conventions (`coding-conventions.md`) | 25 | 19 | 6 | 44 |
| Database (`database-guidelines.md`) | 21 | 16 | 5 | 38 |
| **Total** | **82** | **62** | **20** | **139** |

A *finding* is one violation of one rule in one place; a rule can be violated several times.

## Gaps that apply to the whole project (not deliberate)

Some rules are not met anywhere in the project, not even in the otherwise compliant `Horse`, `Cow`, `Donkey` and `Stable` stack. They are not counted as findings above:

- **API-15** (filtering and sorting): no endpoint offers filter parameters; only paging parameters (`page`, `size`, `sort`) exist.
- **API-18** (OpenAPI documentation): no endpoint is documented with OpenAPI annotations.
- **DB-19** (explicit delete behavior): foreign keys do not define `ON DELETE` behavior explicitly.
- **CODE-24** (Javadoc): the compliant stack only has Javadoc on the services and the base entities, not on every public class.

## API

| Rule | Guideline | Findings | Where |
|---|---|---:|---|
| API-01 | Versioned base path | 1 | GoatController |
| API-02 | Nouns, not verbs | 3 | FeedController; GoatController; PigController |
| API-03 | Plural, lowercase, kebab-case | 2 | PigController; SheepController |
| API-05 | Actions that do not map to CRUD | 1 | FeedController |
| API-06 | Method semantics | 1 | FeedController |
| API-07 | Status codes | 3 | GoatController; PigController; SheepController |
| API-08 | No success status for failures | 5 | FeedController; GoatController; PigController; RabbitController; SheepController |
| API-09 | DTOs only | 5 | FeedController; GoatController; PigController; RabbitController; SheepController |
| API-10 | JSON naming | 1 | RabbitController |
| API-12 | Money and quantities | 1 | FeedController |
| API-13 | Input validation | 3 | FeedController; GoatController; SheepController |
| API-14 | Pagination | 3 | FeedController; GoatController; SheepController |
| API-16 | One error format | 2 | SheepService; all controllers except Horse, Cow, Donkey, Stable |

**No deliberate violation:** API-04 (Hierarchy only where it expresses ownership); API-11 (Dates and times); API-15 (Filtering and sorting); API-17 (No internal details); API-18 (Every endpoint is documented with OpenAPI annotations or an equivalent)

## Architecture

| Rule | Guideline | Findings | Where |
|---|---|---:|---|
| ARCH-01 | Strict direction | 1 | DonkeyService, DonkeyMapper |
| ARCH-02 | One service per controller | 1 | GoatController |
| ARCH-03 | No repositories in controllers | 1 | PigController |
| ARCH-04 | No business logic in controllers | 2 | GoatController; RabbitController |
| ARCH-05 | No web types in services | 1 | SheepService |
| ARCH-09 | Classes live in the package of their role | 1 | DonkeyService, DonkeyMapper |
| ARCH-10 | Entities stay inside the service layer | 3 | GoatController; PigController; SheepController |
| ARCH-12 | Transactions belong to the service layer | 2 | FeedService; RabbitController |
| ARCH-13 | A business operation is one transaction | 1 | FeedService |
| ARCH-14 | Constructor injection only | 7 | FeedController; FeedService; GoatController; GoatService; PigController; PigService; RabbitService |
| ARCH-15 | No mutable static state | 1 | FeedService |
| ARCH-16 | Central exception handling | 2 | SheepController; all controllers except Horse, Cow, Donkey, Stable |
| ARCH-17 | Configuration is externalized | 2 | GoatService; application.properties |
| ARCH-18 | Database schema is managed by migrations | 1 | application.properties |

**No deliberate violation:** ARCH-06 (No business logic in repositories); ARCH-07 (Services may use several repositories); ARCH-08 (Package by layer); ARCH-11 (Entities contain data and simple invariants only)

## Coding conventions

| Rule | Guideline | Findings | Where |
|---|---|---:|---|
| CODE-01 | English only | 1 | GoatService |
| CODE-03 | Methods and variables | 2 | PigController; Rabbit |
| CODE-05 | Meaningful names | 4 | FeedController; FeedService; PigService; RabbitService |
| CODE-07 | Boolean names | 2 | FeedService; Goat |
| CODE-09 | Braces | 1 | SheepController |
| CODE-10 | Indentation | 1 | PigController |
| CODE-13 | Imports | 5 | Goat; GoatController; PigController; SheepController; SheepService |
| CODE-14 | Short methods | 2 | FeedService; RabbitController |
| CODE-15 | No code duplication | 2 | HorseService, CowService, DonkeyService; SheepService |
| CODE-16 | No magic numbers or strings | 5 | FeedService; GoatService; PigService; RabbitController; SheepService |
| CODE-17 | Parameters | 3 | AnimalCounter; FeedController; FeedService |
| CODE-18 | No unused code | 3 | FeedService; PigController; PigService |
| CODE-19 | Exceptions | 3 | FeedService; RabbitService; SheepController |
| CODE-20 | Specific exceptions | 1 | GoatService |
| CODE-21 | No `null` collections | 3 | GoatService; RabbitService |
| CODE-22 | Comparison | 1 | SheepService |
| CODE-23 | Logging | 1 | GoatService |
| CODE-24 | Javadoc | 3 | GoatController; PigService; SheepService |
| CODE-25 | TODO comments | 1 | FeedService |

**No deliberate violation:** CODE-02 (Classes, interfaces and enums); CODE-04 (Constants); CODE-06 (No abbreviations); CODE-08 (Packages); CODE-11 (Line length); CODE-12 (One statement per line)

## Database

| Rule | Guideline | Findings | Where |
|---|---|---:|---|
| DB-01 | Table names | 4 | Feed; Goat; Pig; Sheep |
| DB-02 | Column names | 5 | Feed; Goat; Pig; Sheep; application.properties |
| DB-03 | Primary key | 1 | Pig |
| DB-04 | Foreign keys | 1 | Goat |
| DB-05 | Constraint and index names | 2 | Pig; Rabbit |
| DB-07 | Money and measured quantities | 5 | Feed; Goat; Pig; Rabbit; Sheep |
| DB-08 | Dates and times | 2 | Feed; Sheep |
| DB-09 | Enumerations | 1 | Feed |
| DB-11 | Text columns have a length | 1 | Goat |
| DB-12 | `NOT NULL` is the default | 4 | Goat; Pig; Rabbit; Sheep |
| DB-13 | Natural keys are unique | 2 | Feed; Goat |
| DB-14 | Relations through foreign keys | 2 | Goat; Sheep |
| DB-15 | `CHECK` constraints | 1 | Feed |
| DB-16 | No denormalized lists | 1 | Feed |
| DB-18 | Audit columns | 5 | Feed; Goat; Pig; Rabbit; Sheep |
| DB-20 | Migrations | 1 | application.properties |

**No deliberate violation:** DB-06 (No reserved words); DB-10 (Booleans); DB-17 (One table per entity type); DB-19 (Delete behavior is explicit); DB-21 (Seed data)

## Number of findings per class

| Class | Findings |
|---|---:|
| `GoatController` | 13 |
| `PigController` | 12 |
| `FeedService` | 12 |
| `FeedController` | 11 |
| `SheepController` | 11 |
| `Goat` | 11 |
| `Feed` | 9 |
| `RabbitController` | 7 |
| `GoatService` | 7 |
| `SheepService` | 7 |
| `Sheep` | 7 |
| `Pig` | 7 |
| `PigService` | 5 |
| `RabbitService` | 5 |
| `Rabbit` | 5 |
| `application.properties` | 4 |
| `DonkeyService` | 3 |
| `DonkeyMapper` | 2 |
| `HorseService` | 1 |
| `CowService` | 1 |
| `AnimalCounter` | 1 |

## The compliant part (reference)

`Horse`, `Cow`, `Donkey` and `Stable` (entity, repository, DTOs, service, controller) are written according to the guidelines, so that the violations stand out. Two minor, unintended-but-realistic weaknesses remain in that part: `HorseService`, `CowService` and `DonkeyService` (and their controllers) are near copies of each other (CODE-15), and `AnimalCounter` has a constructor with 7 parameters (CODE-17). The `Donkey` stack has one deliberate violation (see below).

## Details per class

### `controller/GoatController.java`
| Rule | Violation |
|---|---|
| ARCH-02 | Depends on `GoatService` **and** `FeedService` |
| ARCH-04 | Business logic in the controller: consumes feed for every new goat |
| ARCH-14 | Field injection with `@Autowired` |
| ARCH-10, API-09 | Entity `Goat` is received and returned directly |
| API-01 | Path `/api/goats` has no version |
| API-02 | Verbs in paths: `/getAll`, `/createGoat` |
| API-07 | Create returns `200`; delete returns `200` with the text `deleted` |
| API-08 | `GET /{id}` returns `200` with an empty body when the goat does not exist |
| API-13, API-14 | No validation, no pagination |
| CODE-13 | Wildcard import `org.springframework.web.bind.annotation.*` |
| CODE-24 | No Javadoc |
| Behavior | Hard-coded feed id `1L` and ration `2.5`; consuming a missing feed is silently ignored |

### `service/GoatService.java`
| Rule | Violation |
|---|---|
| CODE-01 | German identifier `anzahlTiere` and German messages |
| CODE-16, ARCH-17 | Magic number `8` as capacity; the capacity of the stable is ignored |
| CODE-20 | Throws bare `RuntimeException` |
| CODE-23 | `System.out.println` instead of a logger |
| ARCH-14 | Field injection |
| CODE-21 | `orElse(null)` instead of an exception |

### `model/Goat.java`
| Rule | Violation |
|---|---|
| DB-01 | Table name `Goat` (capitalized, singular) |
| DB-02 | camelCase columns (`hornFlag`, `stableId`, `DailyMilkLiters`) |
| DB-07 | `double` for weight and milk |
| DB-11, DB-12, DB-13 | No lengths, no `NOT NULL`, name not unique |
| DB-14, DB-04 | `stableId` is a plain `Long`, no foreign key |
| DB-18 | No audit columns |
| CODE-07 | Boolean field named `hornFlag` |
| CODE-13 | Wildcard import `jakarta.persistence.*` |

### `controller/SheepController.java`
| Rule | Violation |
|---|---|
| CODE-09 | Allman braces (opening brace on its own line) |
| CODE-13 | Wildcard import `org.springframework.web.bind.annotation.*` |
| CODE-19, ARCH-16 | Catches `Exception` and builds the error response itself |
| API-03 | Path `/api/v1/Sheep` is capitalized |
| API-07, API-08 | Failures returned as `200 OK` with text; create returns `200`; delete returns `200` with text |
| API-09, ARCH-10 | Entity exposed |
| API-14, API-13 | No pagination, no validation |

### `service/SheepService.java`
| Rule | Violation |
|---|---|
| ARCH-05 | Returns `ResponseEntity` and uses `HttpStatus` |
| API-16 | Errors are plain text, not problem details |
| CODE-13 | Wildcard import `java.util.*` and unused import `java.io.IOException` |
| CODE-22 | Strings compared with `== ""` |
| CODE-15 | Validation and capacity check duplicated in `add` and `update` |
| CODE-16 | Magic number `12` as capacity |
| CODE-24 | No Javadoc |

### `model/Sheep.java`
| Rule | Violation |
|---|---|
| DB-01 | Table name `Sheep` |
| DB-02 | camelCase columns, prefixed column `SheepName` |
| DB-07 | `double` woolYieldKg |
| DB-08 | `birthDate` stored as `String` |
| DB-14 | Stable referenced by name (`stableName`), no foreign key |
| DB-12, DB-18 | No `NOT NULL`, no audit columns |

### `controller/PigController.java`
| Rule | Violation |
|---|---|
| ARCH-03 | Injects and uses `PigRepository` directly |
| ARCH-14 | Field injection |
| API-02, API-03 | Path `/api/v1/pigList` (camelCase, "list" in the name) |
| API-07, API-08 | Create returns `200`; missing pig returns `200` with empty body |
| API-09, ARCH-10 | Entity exposed |
| CODE-10 | Tab indentation |
| CODE-18 | Commented-out method |
| CODE-13 | Unused import `java.util.ArrayList` |
| CODE-03 | Methods named `all`, `one` (no verbs) |

### `service/PigService.java`
| Rule | Violation |
|---|---|
| CODE-18 | Class is never used by the controller (dead code) |
| CODE-05 | Parameter `p`, variable `x` |
| CODE-16 | Magic numbers `25.0` and `0.75` |
| CODE-24 | Javadoc does not match the method |
| ARCH-14 | Field injection |

### `model/Pig.java`
| Rule | Violation |
|---|---|
| DB-01 | Table name `tbl_pig` (prefix, singular) |
| DB-03 | Primary key `pigId` of type `INTEGER` |
| DB-02 | camelCase columns |
| DB-05 | Foreign key without explicit name |
| DB-07, DB-12, DB-18 | `double` weight, no `NOT NULL`, no audit columns |

### `controller/RabbitController.java`
| Rule | Violation |
|---|---|
| ARCH-04 | Offspring forecast (business logic) implemented in the controller |
| ARCH-12 | `@Transactional` on the controller |
| CODE-14 | Long method with deep nesting |
| CODE-16 | Magic numbers (`0.8`, `2.0`, `1.0`, `12`, `6`) |
| API-10 | Response keys `expected_offspring`, `expected_adults` in snake_case |
| API-08 | Missing rabbit returns `200` with an error map |
| API-09 | Entity exposed |

### `service/RabbitService.java`
| Rule | Violation |
|---|---|
| CODE-21 | Returns `null` instead of an empty list |
| CODE-19 | Empty `catch` block; `printStackTrace()`; catches `Exception` |
| CODE-21 | `Optional.get()` without check, then `null` |
| CODE-05 | Parameter `r` |
| ARCH-14 | Field injection |

### `model/Rabbit.java`
| Rule | Violation |
|---|---|
| CODE-03 | Java fields `litter_size`, `weight_kg` in snake_case (also leaks into JSON, API-10) |
| DB-07, DB-12, DB-18 | `double` weight, no `NOT NULL`, no audit columns |
| DB-05 | Foreign key without explicit name |

### `service/FeedService.java`
| Rule | Violation |
|---|---|
| ARCH-15 | Mutable `static` cache that returns stale objects |
| ARCH-12, ARCH-13 | `consume` reads, changes and saves without a transaction |
| ARCH-14 | Field injection |
| CODE-14, CODE-17, CODE-16 | `calculateMonthlyCost` is long, deeply nested, has 7 parameters and many magic numbers |
| CODE-05 | Variables `tmp`, `f`, `d` |
| CODE-07 | Boolean variable `flag` |
| CODE-19 | Empty `catch` block |
| CODE-18 | Commented-out code |
| CODE-25 | `TODO` without ticket |
| Behavior | Stock can become negative; expired feed is not checked on consumption |

### `controller/FeedController.java`
| Rule | Violation |
|---|---|
| API-06, API-02, API-05 | `GET /consume` changes data; verb in path |
| API-08 | Missing feed returns `200` with empty body |
| API-09, API-12 | Entity exposed; money as `double` |
| CODE-05, CODE-17 | `/cost` takes 7 one-letter parameters (`h`, `c`, `p`, `g`, `s`, `r`, `d`) |
| ARCH-14 | Field injection |
| API-14, API-13 | No pagination, no validation |

### `model/Feed.java`
| Rule | Violation |
|---|---|
| DB-01, DB-02 | Table `Feed`, camelCase columns |
| DB-09 | Enum `type` stored by ordinal |
| DB-07 | `double` for quantity and price |
| DB-16 | `allowedAnimals` is a comma-separated list |
| DB-08 | `expirationDate` stored as `String` |
| DB-13, DB-15, DB-18 | Name not unique, no check constraints, no audit columns |

### `service/DonkeyService.java` and `controller/DonkeyMapper.java`
| Rule | Violation |
|---|---|
| ARCH-01 | The service imports a class from the `controller` package (dependency points upwards) |
| ARCH-09 | The mapper lives in the `controller` package although only the service uses it |

### `src/main/resources/application.properties`
| Rule | Violation |
|---|---|
| ARCH-18, DB-20 | `ddl-auto=update`, no migration tool |
| DB-02 | `PhysicalNamingStrategyStandardImpl` keeps camelCase and capitalized names |
| ARCH-17 | Limits (stable sizes) are code literals, not properties |

## Findings that affect several classes

- **Inconsistent error handling (API-16, ARCH-16):** only `Horse`, `Cow`, `Donkey` and `Stable` use the central `GlobalExceptionHandler`.
- **Inconsistent capacity rules:** `StableService` uses `Stable.capacity`; `GoatService` (8) and `SheepService` (12) use their own literals; pigs and rabbits have no check at all.
- **Inconsistent stable references:** FK (`Horse`, `Cow`, `Donkey`, `Pig`, `Rabbit`), plain id (`Goat`), name (`Sheep`). `AnimalCounter` has to special-case this.
