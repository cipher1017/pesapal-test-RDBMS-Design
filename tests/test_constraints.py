import os
import pytest
from mini_db.database import Database

def test_primary_key_constraint(tmp_path):
    os.chdir(tmp_path)
    db = Database()
    db.execute("CREATE TABLE items (id INT PRIMARY KEY, value TEXT)")
    db.execute("INSERT INTO items VALUES (1, 'X')")
    with pytest.raises(Exception) as excinfo:
        db.execute("INSERT INTO items VALUES (1, 'Y')")
    assert "PRIMARY KEY constraint failed" in str(excinfo.value)

def test_unique_constraint(tmp_path):
    os.chdir(tmp_path)
    db = Database()
    db.execute("CREATE TABLE items (id INT PRIMARY KEY, code TEXT UNIQUE)")
    db.execute("INSERT INTO items VALUES (1, 'A')")
    with pytest.raises(Exception) as excinfo:
        db.execute("INSERT INTO items VALUES (2, 'A')")
    assert "UNIQUE constraint failed" in str(excinfo.value)
