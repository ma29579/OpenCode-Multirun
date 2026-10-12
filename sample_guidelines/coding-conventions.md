# Coding Conventions

Conventions for all Java code of the farm application. Every rule has an ID (e.g. "violates CODE-05").

## 1. Language and naming

- **CODE-01 English only.** All identifiers (classes, methods, variables, constants, packages), comments, log messages and exception messages are written in English, in American or British spelling consistently. No German or mixed names (`anzahlTiere`, `futterMenge`).
- **CODE-02 Classes, interfaces and enums** use `PascalCase` nouns (`HorseService`, `StableType`). Interfaces do not get an `I` prefix.
- **CODE-03 Methods and variables** use `camelCase`. Methods start with a verb (`findById`, `calculateCost`). No underscores, no Hungarian notation.
- **CODE-04 Constants** (`static final`) use `UPPER_SNAKE_CASE`.
- **CODE-05 Meaningful names.** Names describe the content. No single-letter names (except loop counters `i`, `j`), no `tmp`, `data`, `obj`, `lst`, `flag`.
- **CODE-06 No abbreviations** unless they are common domain terms (`id`, `dto`).
- **CODE-07 Boolean names** read as a statement: `isEmpty`, `hasHorns`, `expired`. No `flag`, `status`, `check`.
- **CODE-08 Packages** are lowercase without underscores.

## 2. Formatting

- **CODE-09 Braces** follow the Kernighan & Ritchie style: the opening brace stays on the same line as the declaration or statement, the closing brace is on its own line. Always use braces, even for single-statement `if`, `for` and `while`.

  ```java
  if (stable.isFull()) {
      throw new ConflictException("Stable is full");
  } else {
      assign(animal, stable);
  }
  ```

- **CODE-10 Indentation** is 4 spaces. No tab characters.
- **CODE-11 Line length** is at most 120 characters.
- **CODE-12 One statement per line**, one declaration per line, one top-level class per file.
- **CODE-13 Imports** are explicit. No wildcard imports (`import java.util.*;`), no unused imports.

## 3. Structure

- **CODE-14 Short methods.** A method has at most 30 lines and at most 3 levels of nesting. Longer logic is split into well-named private methods.
- **CODE-15 No code duplication.** Logic that appears more than twice is extracted into a shared method or class.
- **CODE-16 No magic numbers or strings.** Literals with a meaning are named constants or configuration properties.
- **CODE-17 Parameters.** At most 5 parameters per method; otherwise use a parameter object.
- **CODE-18 No unused code.** No unused variables, parameters, private methods or commented-out code. Version control keeps the history.

## 4. Robustness

- **CODE-19 Exceptions.** Never swallow exceptions with an empty `catch` block. Do not catch `Exception` or `Throwable` unless re-thrown or handled centrally. No `printStackTrace()`.
- **CODE-20 Specific exceptions.** Throw meaningful exceptions with a message, not bare `RuntimeException`.
- **CODE-21 No `null` collections.** Methods return empty collections instead of `null`. Use `Optional` for a possibly missing single value; never return `null` for it.
- **CODE-22 Comparison.** Strings are compared with `equals`, never with `==`. Classes used in collections or as entities implement `equals` and `hashCode` consistently.
- **CODE-23 Logging.** Use SLF4J loggers. No `System.out` or `System.err`. Log levels match the severity; no logging of sensitive data.

## 5. Documentation

- **CODE-24 Javadoc** is required on public classes and public service methods. It describes what and why, and must match the code. Comments that only repeat the code are not wanted.
- **CODE-25 TODO comments** are allowed only with a ticket reference (`TODO(FARM-123)`).
