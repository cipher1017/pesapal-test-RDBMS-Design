from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from mini_db.database import Database
from datetime import datetime

# Reuse a single Database instance for the app (simple, not clustered)
db = Database()

# Ensure entries table exists on import/startup
try:
    db.execute("CREATE TABLE entries (id INT PRIMARY KEY, name TEXT, message TEXT, created DATETIME)")
except Exception:
    # table already exists or another error; ignore
    pass

def _escape_sql_string(s: str) -> str:
    # Basic escaping: double single quotes to embed a single quote inside a quoted string
    return s.replace("'", "''") if s is not None else s

def list_entries(request):
    rows = db.execute("SELECT * FROM entries")
    # rows are dicts with keys: id, name, message, created
    # created may be a datetime object or ISO string depending on mini_db implementation; cast to string
    for r in rows:
        if r.get("created") is None:
            r["created_str"] = ""
        else:
            r["created_str"] = str(r["created"])
    # sort by id ascending
    rows_sorted = sorted(rows, key=lambda r: r.get("id", 0))
    return render(request, "guestbook_app/list.html", {"entries": rows_sorted})

@require_http_methods(["GET", "POST"])
def add_entry(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        message = request.POST.get("message", "").strip()
        if not name:
            return HttpResponseBadRequest("Name is required")
        if not message:
            return HttpResponseBadRequest("Message is required")
        # compute new id
        rows = db.execute("SELECT id FROM entries")
        max_id = max((r["id"] for r in rows), default=0)
        new_id = max_id + 1
        created = datetime.now().isoformat()
        name_s = _escape_sql_string(name)
        msg_s = _escape_sql_string(message)
        sql = f"INSERT INTO entries VALUES ({new_id}, '{name_s}', '{msg_s}', '{created}')"
        try:
            db.execute(sql)
        except Exception as e:
            return HttpResponse(f"Error inserting entry: {e}", status=500)
        return redirect(reverse("guestbook_app:list"))
    return render(request, "guestbook_app/add.html")

@require_http_methods(["GET", "POST"])
def edit_entry(request, entry_id):
    # find entry
    rows = db.execute(f"SELECT * FROM entries WHERE id = {entry_id}")
    if not rows:
        return HttpResponse("Entry not found", status=404)
    entry = rows[0]
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        message = request.POST.get("message", "").strip()
        if not name or not message:
            return HttpResponseBadRequest("Name and message required")
        name_s = _escape_sql_string(name)
        msg_s = _escape_sql_string(message)
        sql = f"UPDATE entries SET name='{name_s}', message='{msg_s}' WHERE id={entry_id}"
        try:
            db.execute(sql)
        except Exception as e:
            return HttpResponse(f"Error updating entry: {e}", status=500)
        return redirect(reverse("guestbook_app:list"))
    return render(request, "guestbook_app/edit.html", {"entry": entry})

@require_http_methods(["POST"])
def delete_entry(request, entry_id):
    sql = f"DELETE FROM entries WHERE id = {entry_id}"
    try:
        db.execute(sql)
    except Exception as e:
        return HttpResponse(f"Error deleting entry: {e}", status=500)
    return redirect(reverse("guestbook_app:list"))
