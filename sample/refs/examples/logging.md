# Example: Logging (Guidelines §4)

## BAD
Bare `print()`, generic message with no identifiers to trace the failure back
to a specific record.

```python
def cancel_order(order_id):
    try:
        db.update_status(order_id, "cancelled")
    except DBError:
        print("Error occurred")
```

## GOOD
Uses the project logger, includes the order ID so the failure is traceable in
logs/monitoring.

```python
from app.logging import logger


def cancel_order(order_id: str) -> None:
    """Cancel an order by ID."""
    try:
        db.update_status(order_id, "cancelled")
    except DBError as e:
        logger.error(f"Failed to cancel order {order_id}: {e}")
        raise OrderCancellationError(order_id) from e
```

**Why:** `print()` output doesn't get captured by log aggregation/alerting in
production. "Error occurred" with no order ID means someone has to reproduce
the bug from scratch instead of searching logs for `order_id`.
