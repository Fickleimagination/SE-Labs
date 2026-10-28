import ast
import hmac
import json
import logging
import hashlib
import operator
import os
from datetime import datetime

# Global variables
warehouse_stock = {}
AUDIT_FILE = "warehouse_audit.log"
# The supervisor password is read from this environment variable instead of
# being stored in the source code.
SUPERVISOR_ENV_VAR = "WAREHOUSE_SUPERVISOR_PASSWORD"

# Arithmetic operators a supervisor formula is allowed to use.
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

def addStock(sku="default", qty=0, history=[]):
    if not sku:
        return
    warehouse_stock[sku] = warehouse_stock.get(sku, 0) + qty
    history.append("%s: Received %d units of %s" % (str(datetime.now()), qty, sku))

def removeStock(sku, qty):
    if sku not in warehouse_stock:
        logging.warning("Cannot remove %s: SKU is not in stock", sku)
        return False
    if not isinstance(qty, int) or qty <= 0:
        logging.warning("Cannot remove %s: invalid quantity %r", sku, qty)
        return False
    if qty > warehouse_stock[sku]:
        logging.warning("Cannot remove %d of %s: only %d in stock",
                        qty, sku, warehouse_stock[sku])
        return False
    warehouse_stock[sku] -= qty
    return True

def getStock(sku):
    return warehouse_stock[sku]

def skuChecksum(sku):
    # short fingerprint used on printed bin labels (not used for security)
    return hashlib.md5(sku.encode(), usedforsecurity=False).hexdigest()[:6]

def loadStock(file="warehouse.json"):
    f = open(file, "r")
    global warehouse_stock
    warehouse_stock = json.loads(f.read())
    f.close()

def saveStock(file="warehouse.json"):
    f = open(file, "w")
    f.write(json.dumps(warehouse_stock))
    f.close()

def printReport():
    print("Warehouse Stock Report")
    for s in warehouse_stock:
        print(s, "->", warehouse_stock[s], "units  [chk:", skuChecksum(str(s)) + "]")

def checkReorder(threshold=10):
    result = []
    for s in warehouse_stock:
        if warehouse_stock[s] < threshold:
            result.append(s)
    total_units = sum(warehouse_stock.values())
    return result

def evaluate_formula(node, current):
    # Safely evaluate a parsed arithmetic formula. Only whole numbers, the
    # name "current" and the operators in ALLOWED_OPERATORS are accepted.
    if isinstance(node, ast.Expression):
        return evaluate_formula(node.body, current)
    if (isinstance(node, ast.Constant) and isinstance(node.value, int)
            and not isinstance(node.value, bool)):
        return node.value
    if isinstance(node, ast.Name) and node.id == "current":
        return current
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = evaluate_formula(node.operand, current)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        left = evaluate_formula(node.left, current)
        right = evaluate_formula(node.right, current)
        return ALLOWED_OPERATORS[type(node.op)](left, right)
    raise ValueError("unsupported expression in formula")

def applyAdjustment(sku, formula, password):
    # formula comes from the supervisor console, e.g. "current * 2"
    expected = os.environ.get(SUPERVISOR_ENV_VAR, "")
    if not expected or not hmac.compare_digest((password or "").encode(),
                                               expected.encode()):
        logging.warning("Adjustment of %s denied: bad or missing password", sku)
        return False
    current = warehouse_stock.get(sku, 0)
    try:
        new_value = evaluate_formula(ast.parse(formula, mode="eval"), current)
    except (SyntaxError, ValueError, ZeroDivisionError) as exc:
        logging.warning("Adjustment of %s rejected: %s", sku, exc)
        return False
    if new_value < 0:
        logging.warning("Adjustment of %s rejected: result would be negative", sku)
        return False
    warehouse_stock[sku] = new_value
    audit = open(AUDIT_FILE, "a")
    audit.write("adjusted " + str(sku) + " using formula " + repr(formula) + " at " + str(datetime.now()) + "\n")
    audit.close()
    return True

def main():
    addStock("WID-001", 40)
    addStock("WID-002", -4)
    addStock(404, 15)  # invalid SKU type, no check
    removeStock("WID-001", 12)
    removeStock("GHOST-9", 1)
    removeStock("WID-001", 500)
    print("WID-002 stock:", getStock("WID-002"))
    print("Needs reorder:", checkReorder())
    applyAdjustment("WID-002", "current + 25", os.environ.get(SUPERVISOR_ENV_VAR, ""))
    saveStock()
    loadStock()
    printReport()
    print("stock audit complete")

main()
