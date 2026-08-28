# Example: Error handling (Guidelines §2)

## BAD
Swallows the exception silently, returns a sentinel value, no logging.

```python
def get_user(user_id):
    try:
        return db.fetch_user(user_id)
    except Exception:
        return None
```

## GOOD
Catches the specific exception, logs it with the relevant ID, raises a typed
domain exception instead of returning a sentinel.

```python
def get_user(user_id: str) -> User:
    """Fetch a user by ID, raising UserNotFoundError if none exists."""
    try:
        return db.fetch_user(user_id)
    except DBConnectionError as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        raise UserFetchError(user_id) from e
```

**Why:** Returning `None` on failure pushes the error-handling decision onto
every caller, and callers often forget to check. A typed exception makes the
failure impossible to silently ignore.
