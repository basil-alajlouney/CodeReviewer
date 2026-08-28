# Example: Naming (Guidelines §1)

## BAD
Abbreviated names, boolean without is_/has_ prefix, magic number inline.

```python
def chk_usr(u, cfg_val):
    active = u.status == 1
    return active
```

## GOOD
Full names, boolean prefixed, magic number promoted to a named constant.

```python
ACTIVE_STATUS_CODE = 1

def is_user_active(user: User) -> bool:
    """Return whether the given user's status is active."""
    return user.status == ACTIVE_STATUS_CODE
```

**Why:** `chk_usr` and `cfg_val` require the reader to guess what they hold.
`1` as a bare literal means anyone reading `user.status == 1` has to go dig
up what status `1` represents.
