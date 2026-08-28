# Example: Functions (Guidelines §3)

## BAD
No type annotations, no docstring, and mixes DB I/O with business logic in
one function.

```python
def get_order_total(order_id):
    order = db.query(f"SELECT * FROM orders WHERE id={order_id}")
    total = 0
    for item in order.items:
        total += item.price * item.qty
    return total * 1.08
```

## GOOD
Split into an I/O layer and a logic layer, both type-annotated with
docstrings.

```python
def fetch_order(order_id: str) -> Order:
    """Fetch an order by ID from the database."""
    return db.query_order(order_id)


def calculate_total(order: Order, tax_rate: float = 0.08) -> float:
    """Calculate the order total including tax."""
    subtotal = sum(item.price * item.qty for item in order.items)
    return subtotal * (1 + tax_rate)


def get_order_total(order_id: str) -> float:
    """Fetch an order and return its total including tax."""
    order = fetch_order(order_id)
    return calculate_total(order)
```

**Why:** `calculate_total` is now pure and trivially testable without a
database. `fetch_order` can be mocked or swapped independently. The original
version can't be tested without hitting the DB, and a bug in tax math can't
be isolated from a bug in the query.
