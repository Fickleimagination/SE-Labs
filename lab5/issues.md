# Issues Found – Warehouse Stock Manager

Line numbers refer to the **original** `warehouse_stock_manager.py` (before fixes).
Tools: Pylint 4.1.3, Bandit 1.9.4, Flake8 7.4.1.

**Before:** Pylint 4.48/10 · Bandit 5 issues (1 High, 2 Medium, 2 Low) · Flake8 19 issues
**After:** Pylint 10.00/10 · Bandit 0 issues · Flake8 0 issues

Reports are in `reports/before/` and `reports/after/`.

## Security issues (Bandit) – fixed in commit 1

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Weak MD5 hash (B324, **High**) | Security | 31 | `hashlib.md5()` used for the bin-label checksum. Bandit flags MD5 as insecure for security purposes. | The checksum is only a label fingerprint, not a security control, so it was marked `usedforsecurity=False`. The hash itself was kept so labels already printed stay valid (WID-002 still gives `a616ce`). |
| `eval()` on supervisor formula (B307, W0123, **Medium**) | Security | 62 | `eval(formula, ...)` runs arbitrary Python typed into the supervisor console (e.g. `__import__('os').system(...)`). Passing `{"current": ...}` as globals does **not** sandbox it. | Parse with `ast.parse(mode="eval")` and evaluate with a whitelist evaluator that only allows whole numbers, `current`, unary `+/-` and `+ - * // %`. Bad formulas and negative results are rejected and logged. |
| `eval()` on a literal string (B307, W0123, **Medium**) | Security | 80 | `eval("print('stock audit complete')")` has no reason to use `eval`. | Replaced with a plain `print(...)` call. |
| Hardcoded password (B105, Low) | Security | 10, 76 | `SUPERVISOR_PASSWORD = "wh-admin-1234"` is stored in source (and repeated in the demo call). | Password is read from the `WAREHOUSE_SUPERVISOR_PASSWORD` environment variable and compared with `hmac.compare_digest`. If it is not set, all adjustments are refused. |
| Silent `try/except/pass` (B110, W0702, E722, Low) | Bug / Security | 19-24 | Bare `except: pass` hid every error in `removeStock` (unknown SKU, bad quantity, anything else). | Removed the try/except. The function now checks the cases explicitly, logs a warning and returns `False`. |

## Logic bugs (found by reading the program output – no tool flagged these) – fixed in commits 1 and 2

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Negative stock accepted | Bug | 12-16, 69 | `addStock("WID-002", -4)` stored -4 units, and the demo printed `WID-002 stock: -4`. | `add_stock` rejects non-positive or non-integer quantities with a warning. |
| Invalid SKU type accepted | Bug | 13-15, 70 | `addStock(404, 15)` stored an `int` SKU. After a JSON save/load the key silently becomes the string `"404"`. | `add_stock` rejects SKUs that are not non-empty strings. |
| Over-removal wiped out the item | Bug | 18-24, 73 | `removeStock("WID-001", 500)` with 28 in stock deleted the SKU entirely and the error was swallowed. Removing down to zero also deleted the SKU, so it could never show up in the reorder check. | `remove_stock` refuses to remove more than is in stock. SKUs that reach zero stay listed so `check_reorder` still flags them. |
| `getStock` crashes on unknown SKU | Bug | 26-27 | `warehouse_stock[sku]` raises `KeyError` for a SKU that is not stocked. | `get_stock` returns 0 for unknown SKUs. |
| Mutable default argument (W0102) | Bug | 12 | `history=[]` is created once and shared across every call, so unrelated calls pile entries into the same list. | Default changed to `None`; a new list is created inside the function and returned. |

## Code quality issues (Pylint) – fixed in commit 2

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Files not closed safely (R1732) | Quality | 34, 40, 63 | `open()` followed by manual `close()` leaks the handle if an error happens in between. | Use `with open(...)` and `json.load` / `json.dump`. |
| No encoding on `open` (W1514) | Quality | 34, 40, 63 | Behaviour depends on the OS default encoding. | Added `encoding="utf-8"` everywhere. |
| `global` statement (W0603) | Quality | 35 | `loadStock` rebinds the module-level dict with `global`. | Use `warehouse_stock.clear()` then `.update(data)` so no rebinding is needed. |
| Unused variable (W0612, F841) | Style | 54 | `total_units` is computed in `checkReorder` and never used. | Removed; function rewritten as a list comprehension. |
| Unused imports (W0611, F401) | Style | 2, 4 | `logging` and `os` were imported but never used. | `logging` is now used for warnings and `os` for the environment variable, so both imports are genuinely needed. |
| camelCase function names (C0103) | Style | 12, 18, 26, 29, 33, 39, 44, 49, 57 | Functions do not follow PEP 8 snake_case. | Renamed (`addStock` → `add_stock`, etc.) and updated all callers. |
| Missing docstrings (C0114, C0116) | Style | 1 and every function | No module or function documentation. | Added a module docstring and a docstring for every function. |
| `%` string formatting (C0209) | Style | 16 | Old-style formatting. | Converted to f-strings. |
| Trailing whitespace (C0303) | Style | 54 | Spaces after `total_units = ...`. | Removed with the line. |
| Line too long (C0301) | Style | 64 | Audit-log line was 107 characters (limit 100). | Rewritten as an f-string and wrapped. |
| `main()` runs on import | Design | 82 | Importing the module immediately ran the demo and wrote files. | Guarded with `if __name__ == "__main__":`. |

## Formatting issues (Flake8) – fixed in commit 3

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Missing blank lines (E302, E305) | Style | 12, 18, 26, 29, 33, 39, 44, 49, 57, 67, 82 | PEP 8 requires two blank lines around top-level functions and after the last function. | Added the missing blank lines. |
| Line too long (E501) | Style | 16, 47, 64 | Lines over 79 characters. | Wrapped long calls and strings (and everything that grew past 79 during commit 2). |
| Trailing whitespace (W291) | Style | 54 | See Pylint C0303. | Already fixed in commit 2. |
| Unused imports / variable (F401, F841), bare except (E722) | Style | 2, 4, 54, 23 | Duplicates of Pylint and Bandit findings. | Already fixed in commits 1 and 2. |
