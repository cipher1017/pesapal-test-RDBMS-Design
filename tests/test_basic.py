import os
import pytest
from mini_db.database import Database

def test_create_insert_select(tmp_path):
    os.chdir(tmp_path)
    db = Database()
    assert db.tables == {}
    db.execute("CREATE TABLE users (id INT PRIMARY KEY, name TEXT)")
    db.execute("INSERT INTO users VALUES (1, 'Alice')")
    db.execute("INSERT INTO users VALUES (2, 'Bob')")
    rows = db.execute("SELECT * FROM users")
    assert rows == [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
    db.execute("UPDATE users SET name='Charlie' WHERE id=2")
    rows = db.execute("SELECT name FROM users WHERE id=2")
    assert rows == [{'name': 'Charlie'}]
    count = db.execute("DELETE FROM users WHERE id=1")
    assert count == 1
    rows = db.execute("SELECT * FROM users")
    assert rows == [{'id': 2, 'name': 'Charlie'}]

def test_join(tmp_path):
    os.chdir(tmp_path)
    db = Database()
    db.execute("CREATE TABLE users (id INT PRIMARY KEY, name TEXT)")
    db.execute("CREATE TABLE orders (order_id INT PRIMARY KEY, user_id INT, item TEXT)")
    db.execute("INSERT INTO users VALUES (1, 'Alice')")
    db.execute("INSERT INTO users VALUES (2, 'Bob')")
    db.execute("INSERT INTO orders VALUES (10, 1, 'Book')")
    db.execute("INSERT INTO orders VALUES (11, 2, 'Pen')")
    result = db.execute("SELECT users.name, orders.item FROM users INNER JOIN orders ON users.id = orders.user_id")
    result_sorted = sorted(result, key=lambda x: x['users.name'])
    assert result_sorted == [
        {'users.name': 'Alice', 'orders.item': 'Book'},
        {'users.name': 'Bob',   'orders.item': 'Pen'}
    ]
