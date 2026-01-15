#!/usr/bin/env python3
from mini_db.database import Database
from datetime import datetime

def main():
    db = Database()
    try:
        db.execute("CREATE TABLE entries (id INT PRIMARY KEY, name TEXT, message TEXT, created DATETIME)")
        print("Guestbook table created.")
    except Exception:
        pass
    print("Guestbook CLI. Commands: add <name> <message>, list, quit")
    while True:
        cmd = input("> ").strip()
        if not cmd:
            continue
        if cmd.lower() in ("quit", "exit"):
            break
        if cmd.lower().startswith("add "):
            parts = cmd.split(" ", 2)
            if len(parts) < 3:
                print("Usage: add <name> <message>")
                continue
            name, message = parts[1], parts[2]
            rows = db.execute("SELECT id FROM entries")
            max_id = max((row['id'] for row in rows), default=0)
            id_new = max_id + 1
            created = datetime.now().isoformat()
            db.execute(f"INSERT INTO entries VALUES ({id_new}, '{name}', '{message}', '{created}')")
            print("Entry added.")
        elif cmd.lower() == "list":
            rows = db.execute("SELECT * FROM entries")
            if rows:
                for row in rows:
                    print(f"{row['id']}: {row['name']} - {row['message']} ({row['created']})")
            else:
                print("(no entries)")
        else:
            print("Unknown command.")

if __name__ == "__main__":
    main()
