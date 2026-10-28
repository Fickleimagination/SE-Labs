"""Warehouse stock manager.

Receives and issues stock per SKU, flags items that need reordering, saves
stock levels to a JSON file and lets a supervisor adjust a SKU's quantity
with a simple arithmetic formula.

The supervisor password is read from the WAREHOUSE_SUPERVISOR_PASSWORD
environment variable; it is never stored in the source code.
"""
import ast
import hashlib
import hmac
import json
import logging
import operator
import os
from datetime import datetime

# Global variables
warehouse_stock = {}
AUDIT_FILE = "warehouse_audit.log"
# Name of the environment variable that holds the supervisor password.
SUPERVISOR_ENV_VAR = "WAREHOUSE_SUPERVISOR_PASSWORD"

# Arithmetic operators a supervisor formula is allowed to use.
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}


def is_positive_int(value):
    """Return True if value is a whole number greater than zero."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def add_stock(sku="default", qty=0, history=None):
    """Receive qty units of sku and record the receipt in history.

    Invalid SKUs (empty or not a string) and non-positive quantities are
    rejected with a warning. Returns the history list, which is a new list
    unless the caller passes one in.
    """
    if history is None:
        history = []
    if not isinstance(sku, str) or not sku:
        logging.warning("Cannot add stock: invalid SKU %r", sku)
        return history
    if not is_positive_int(qty):
        logging.warning("Cannot add %r units of %s: quantity must be positive",
                        qty, sku)
        return history
    warehouse_stock[sku] = warehouse_stock.get(sku, 0) + qty
    history.append(f"{datetime.now()}: Received {qty} units of {sku}")
    return history


def remove_stock(sku, qty):
    """Issue qty units of sku. Return True on success, False if rejected.

    Unknown SKUs, invalid quantities and requests for more than is in stock
    are rejected with a warning. A SKU that reaches zero stays listed so it
    still shows up in the reorder check.
    """
    if sku not in warehouse_stock:
        logging.warning("Cannot remove %s: SKU is not in stock", sku)
        return False
    if not is_positive_int(qty):
        logging.warning("Cannot remove %s: invalid quantity %r", sku, qty)
        return False
    if qty > warehouse_stock[sku]:
        logging.warning("Cannot remove %d of %s: only %d in stock",
                        qty, sku, warehouse_stock[sku])
        return False
    warehouse_stock[sku] -= qty
    return True


def get_stock(sku):
    """Return the units in stock for sku (0 if the SKU is not stocked)."""
    return warehouse_stock.get(sku, 0)


def sku_checksum(sku):
    """Return a short fingerprint used on printed bin labels."""
    # Not used for security, so MD5 is fine here (and keeps old labels valid).
    return hashlib.md5(sku.encode(), usedforsecurity=False).hexdigest()[:6]


def load_stock(file="warehouse.json"):
    """Replace the in-memory stock with the contents of a JSON file."""
    with open(file, "r", encoding="utf-8") as stock_file:
        data = json.load(stock_file)
    warehouse_stock.clear()
    warehouse_stock.update(data)


def save_stock(file="warehouse.json"):
    """Write the current stock levels to a JSON file."""
    with open(file, "w", encoding="utf-8") as stock_file:
        json.dump(warehouse_stock, stock_file)


def print_report():
    """Print every SKU with its quantity and bin-label checksum."""
    print("Warehouse Stock Report")
    for sku, qty in warehouse_stock.items():
        print(f"{sku} -> {qty} units  [chk: {sku_checksum(str(sku))}]")


def check_reorder(threshold=10):
    """Return the SKUs whose stock is below threshold."""
    return [sku for sku, qty in warehouse_stock.items() if qty < threshold]


def evaluate_formula(node, current):
    """Safely evaluate a parsed arithmetic formula.

    Only whole numbers, the name "current" and the operators listed in
    ALLOWED_OPERATORS are accepted; anything else raises ValueError.
    """
    if isinstance(node, ast.Expression):
        return evaluate_formula(node.body, current)
    if (isinstance(node, ast.Constant) and isinstance(node.value, int)
            and not isinstance(node.value, bool)):
        return node.value
    if isinstance(node, ast.Name) and node.id == "current":
        return current
    if (isinstance(node, ast.UnaryOp)
            and isinstance(node.op, (ast.UAdd, ast.USub))):
        value = evaluate_formula(node.operand, current)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        left = evaluate_formula(node.left, current)
        right = evaluate_formula(node.right, current)
        return ALLOWED_OPERATORS[type(node.op)](left, right)
    raise ValueError("unsupported expression in formula")


def apply_adjustment(sku, formula, password):
    """Set sku's quantity from a supervisor formula such as "current * 2".

    Requires the supervisor password. Returns True if the adjustment was
    applied and written to the audit log, False if it was refused.
    """
    expected = os.environ.get(SUPERVISOR_ENV_VAR, "")
    if not expected or not hmac.compare_digest((password or "").encode(),
                                               expected.encode()):
        logging.warning("Adjustment of %s denied: bad or missing password",
                        sku)
        return False
    current = warehouse_stock.get(sku, 0)
    try:
        new_value = evaluate_formula(ast.parse(formula, mode="eval"), current)
    except (SyntaxError, ValueError, ZeroDivisionError) as exc:
        logging.warning("Adjustment of %s rejected: %s", sku, exc)
        return False
    if new_value < 0:
        logging.warning("Adjustment of %s rejected: result would be negative",
                        sku)
        return False
    warehouse_stock[sku] = new_value
    with open(AUDIT_FILE, "a", encoding="utf-8") as audit:
        audit.write(f"adjusted {sku} using formula {formula!r} "
                    f"at {datetime.now()}\n")
    return True


def main():
    """Run a short demo of the stock manager."""
    add_stock("WID-001", 40)
    add_stock("WID-002", -4)   # rejected: quantity must be positive
    add_stock(404, 15)         # rejected: SKU must be a string
    remove_stock("WID-001", 12)
    remove_stock("GHOST-9", 1)     # rejected: unknown SKU
    remove_stock("WID-001", 500)   # rejected: more than in stock
    print("WID-002 stock:", get_stock("WID-002"))
    print("Needs reorder:", check_reorder())
    password = os.environ.get(SUPERVISOR_ENV_VAR, "")
    apply_adjustment("WID-002", "current + 25", password)
    save_stock()
    load_stock()
    print_report()
    print("stock audit complete")


if __name__ == "__main__":
    main()
