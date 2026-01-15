#!/usr/bin/env python3
from mini_db.database import Database

def print_table(rows):
    if not rows:
        print("(no rows)")
        return
    cols = list(rows[0].keys())
    widths = {col: len(col) for col in cols}
    for row in rows:
        for col in cols:
            s = str(row.get(col, ""))
            widths[col] = max(widths[col], len(s))
    header = " | ".join(col.ljust(widths[col]) for col in cols)
    sep = "-+-".join("-"*widths[col] for col in cols)
    print(header)
    print(sep)
    for row in rows:
        line = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in cols)
        print(line)

def main():
    db = Database()
    try:
        while True:
            s = input("mini_db> ").strip()
            if not s:
                continue
            if s.lower() in ("exit", "quit"):
                break
            try:
                result = db.execute(s)
                if isinstance(result, list):
                    print_table(result)
                elif result is not None:
                    print(result)
            except Exception as e:
                print("ERROR:", e)
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye")

if __name__ == "__main__":
    main()
