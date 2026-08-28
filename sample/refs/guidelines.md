# Engineering Guidelines — Python

## 1. Naming

- **1.1** Functions and variables use `snake_case`. No abbreviations unless
  industry-standard (`id`, `url`, `db` are fine; `usr`, `cfg_val` are not).
- **1.2** Boolean variables and functions must start with `is_`, `has_`, or
  `should_` (e.g. `is_valid`, `has_permission`).
- **1.3** Constants are `UPPER_SNAKE_CASE` and defined at module level, never
  inline as magic numbers/strings.

## 2. Error Handling

- **2.1** Never use a bare `except Exception:` (or bare `except:`) that
  silently swallows an error. Catch the specific exception type.
- **2.2** All caught exceptions must be logged before being handled, re-raised,
  or converted to a domain-specific exception.
- **2.3** Functions that can fail in an expected way (e.g. "user not found")
  must raise a typed, project-specific exception — not return `None` or `-1`
  as a sentinel value.

## 3. Functions

- **3.1** Every public function must have a type-annotated signature
  (parameters and return type).
- **3.2** Every public function must have a one-line docstring describing what
  it does, not how.
- **3.3** Functions should do one thing. If a function mixes I/O (DB/network
  calls) with business logic, split it into an I/O layer and a logic layer.

## 4. Logging

- **4.1** Use the project `logger` (from `app.logging`), never bare `print()`
  statements.
- **4.2** Log messages must include relevant identifiers (e.g. user ID, order
  ID) for traceability — not generic messages like `"Error occurred"`.

## 5. Imports

- **5.1** Standard library imports, then third-party imports, then local
  imports — each group separated by a blank line, alphabetized within each
  group.
