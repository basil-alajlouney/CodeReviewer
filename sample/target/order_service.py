import json
from app.models import Order
import os
from app.db import get_connection


def proc_order(oid, usr_id):
    conn = get_connection()
    try:
        order = conn.query(f"SELECT * FROM orders WHERE id={oid}")
        if order.status == 2:
            active = True
        else:
            active = False

        result = calc_total(order)
        return result
    except Exception:
        print("Error occurred")
        return None


def calc_total(order):
    total = 0
    for item in order.items:
        total += item.price * item.qty
    tax = total * 0.08
    return total + tax


def chk_permission(usr_id, oid):
    conn = get_connection()
    perms = conn.query(f"SELECT * FROM permissions WHERE user={usr_id}")
    if perms is None:
        return -1
    return perms.level
