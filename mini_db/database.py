import os
import json
from datetime import datetime

def cast_value(value, col_type):
    if value is None:
        return None
    if col_type == "INT":
        if isinstance(value, str):
            if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                return int(value)
            else:
                raise ValueError(f"Invalid INT value: {value}")
        elif isinstance(value, int):
            return value
        else:
            try:
                return int(value)
            except:
                raise ValueError(f"Invalid INT value: {value}")
    elif col_type == "TEXT":
        if isinstance(value, str):
            return value
        else:
            return str(value)
    elif col_type == "BOOL":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("true", "false"):
                return v == "true"
            elif v in ("0", "1"):
                return v == "1"
            else:
                raise ValueError(f"Invalid BOOL value: {value}")
        elif isinstance(value, int):
            return bool(value)
        else:
            raise ValueError(f"Invalid BOOL value: {value}")
    elif col_type == "DATETIME":
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except Exception:
                raise ValueError(f"Invalid DATETIME value: {value}")
        else:
            raise ValueError(f"Invalid DATETIME value: {value}")
    else:
        raise ValueError(f"Unknown type: {col_type}")

class Table:
    def __init__(self, name, columns, col_types, primary_key=None, unique_cols=None, data_dir="data"):
        self.name = name
        self.columns = list(columns)
        self.col_types = dict(col_types)
        self.primary_key = primary_key
        self.unique_cols = unique_cols if unique_cols is not None else []
        self.rows = []
        self.indexes = {}
        self.data_dir = data_dir
        if self.primary_key:
            self.indexes[self.primary_key] = {}
        for col in self.unique_cols:
            if col != self.primary_key:
                self.indexes[col] = {}
        self.file_path = os.path.join(self.data_dir, f"{self.name}.json")
        self._load()

    def _load(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
            for row in data:
                casted_row = {}
                for col, val in row.items():
                    if val is None:
                        casted_val = None
                    else:
                        t = self.col_types[col]
                        if t == "DATETIME":
                            casted_val = datetime.fromisoformat(val)
                        else:
                            casted_val = val
                    casted_row[col] = casted_val
                self.rows.append(casted_row)
                self._index_row(casted_row)

    def _index_row(self, row):
        if self.primary_key:
            key = row[self.primary_key]
            self.indexes[self.primary_key][key] = row
        for col in self.unique_cols:
            if col != self.primary_key:
                key = row[col]
                self.indexes[col][key] = row

    def _rebuild_indexes(self):
        self.indexes.clear()
        if self.primary_key:
            self.indexes[self.primary_key] = {}
        for col in self.unique_cols:
            if col != self.primary_key:
                self.indexes[col] = {}
        for row in self.rows:
            self._index_row(row)

    def insert(self, values):
        row = {}
        for col in self.columns:
            if col in values:
                val = values[col]
            else:
                raise ValueError(f"Missing value for column '{col}'")
            t = self.col_types[col]
            if val is None:
                casted_val = None
            else:
                casted_val = cast_value(val, t)
            row[col] = casted_val
        if self.primary_key:
            pk_col = self.primary_key
            key = row[pk_col]
            if key in self.indexes[pk_col]:
                raise Exception(f"PRIMARY KEY constraint failed: duplicate value {key} for column {pk_col}")
        for col in self.unique_cols:
            if col == self.primary_key:
                continue
            key = row[col]
            if key in self.indexes[col]:
                raise Exception(f"UNIQUE constraint failed: duplicate value {key} for column {col}")
        self.rows.append(row)
        self._index_row(row)
        self._save()
        return row

    def _save(self):
        data = []
        for row in self.rows:
            json_row = {}
            for col, val in row.items():
                if val is None:
                    json_val = None
                else:
                    t = self.col_types[col]
                    if t == "DATETIME":
                        json_val = val.isoformat()
                    else:
                        json_val = val
                json_row[col] = json_val
            data.append(json_row)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)

    def select(self, columns, where=None):
        result = []
        for row in self.rows:
            match = True
            if where:
                for col, expected in where:
                    if col not in row or row[col] != expected:
                        match = False
                        break
            if match:
                if columns == ["*"]:
                    result_row = dict(row)
                else:
                    result_row = {col: row[col] for col in columns}
                result.append(result_row)
        return result

    def delete(self, where=None):
        to_delete = []
        for row in list(self.rows):
            if where:
                match = True
                for col, expected in where:
                    if row.get(col) != expected:
                        match = False
                        break
                if match:
                    to_delete.append(row)
            else:
                to_delete.append(row)
        for row in to_delete:
            self.rows.remove(row)
        self._rebuild_indexes()
        self._save()
        return len(to_delete)

    def update(self, set_values, where=None):
        count = 0
        for row in self.rows:
            match = True
            if where:
                for col, expected in where:
                    if row.get(col) != expected:
                        match = False
                        break
            if match:
                for col, new_val in set_values.items():
                    if col not in self.columns:
                        raise Exception(f"Unknown column {col}")
                    t = self.col_types[col]
                    casted = cast_value(new_val, t)
                    if col == self.primary_key:
                        if casted != row[col] and casted in self.indexes[col]:
                            raise Exception(f"PRIMARY KEY constraint failed: duplicate value {casted} for column {col}")
                    if col in self.unique_cols and col != self.primary_key:
                        if casted != row[col] and casted in self.indexes[col]:
                            raise Exception(f"UNIQUE constraint failed: duplicate value {casted} for column {col}")
                    if col == self.primary_key:
                        old_key = row[col]
                        del self.indexes[col][old_key]
                        self.indexes[col][casted] = row
                    if col in self.unique_cols and col != self.primary_key:
                        old_key = row[col]
                        del self.indexes[col][old_key]
                        self.indexes[col][casted] = row
                    row[col] = casted
                count += 1
        if count > 0:
            self._save()
        return count

class Database:
    def __init__(self, catalog_file="catalog.json", data_dir="data"):
        self.catalog_file = catalog_file
        self.data_dir = data_dir
        self.catalog = {}
        self.tables = {}
        if os.path.exists(self.catalog_file):
            with open(self.catalog_file, "r") as f:
                self.catalog = json.load(f)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        for table_name, schema in self.catalog.items():
            columns = [col['name'] for col in schema['columns']]
            col_types = {col['name']: col['type'] for col in schema['columns']}
            pk = schema.get('primary_key')
            unique = schema.get('unique', [])
            tbl = Table(table_name, columns, col_types, primary_key=pk, unique_cols=unique, data_dir=self.data_dir)
            self.tables[table_name] = tbl

    def save_catalog(self):
        with open(self.catalog_file, "w") as f:
            json.dump(self.catalog, f, indent=2)

    def execute(self, sql):
        sql = sql.strip().rstrip(';').strip()
        if not sql:
            return
        tokens = sql.split()
        cmd = tokens[0].upper()
        if cmd == "CREATE":
            return self._exec_create(sql)
        elif cmd == "INSERT":
            return self._exec_insert(sql)
        elif cmd == "SELECT":
            return self._exec_select(sql)
        elif cmd == "UPDATE":
            return self._exec_update(sql)
        elif cmd == "DELETE":
            return self._exec_delete(sql)
        else:
            raise Exception(f"Unknown command: {cmd}")

    def _exec_create(self, sql):
        import re
        pattern = re.compile(r'CREATE\s+TABLE\s+(\w+)\s*\((.+)\)', re.IGNORECASE)
        m = pattern.match(sql)
        if not m:
            raise Exception("Invalid CREATE TABLE syntax")
        table_name = m.group(1)
        body = m.group(2).strip()
        parts = []
        buf = ""
        depth = 0
        for ch in body:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            if ch == ',' and depth == 0:
                parts.append(buf.strip())
                buf = ""
            else:
                buf += ch
        if buf:
            parts.append(buf.strip())
        columns = []
        col_types = {}
        primary_key = None
        unique_cols = []
        for part in parts:
            part = part.strip().rstrip(',')
            if not part:
                continue
            up = part.upper()
            tokens = part.split()
            if tokens[0].upper() == "PRIMARY":
                if primary_key is not None:
                    raise Exception("Multiple PRIMARY KEY definitions")
                pk_cols = part[part.find("(")+1:part.rfind(")")]
                pk_cols = [c.strip() for c in pk_cols.split(',')]
                if len(pk_cols) != 1:
                    raise Exception("Composite primary keys not supported")
                primary_key = pk_cols[0]
            elif tokens[0].upper() == "UNIQUE":
                cols = part[part.find("(")+1:part.rfind(")")]
                cols = [c.strip() for c in cols.split(',')]
                for col in cols:
                    unique_cols.append(col)
            else:
                col_name = tokens[0]
                col_type = tokens[1].upper()
                if col_type not in ("INT", "TEXT", "BOOL", "DATETIME"):
                    raise Exception(f"Unknown type {col_type}")
                columns.append(col_name)
                col_types[col_name] = col_type
                if 'PRIMARY' in up and 'KEY' in up:
                    if primary_key is not None:
                        raise Exception("Multiple PRIMARY KEY definitions")
                    primary_key = col_name
                if 'UNIQUE' in up:
                    unique_cols.append(col_name)
        if table_name in self.catalog:
            raise Exception(f"Table {table_name} already exists")
        col_list = [{"name": col, "type": col_types[col]} for col in columns]
        schema = {"columns": col_list}
        if primary_key:
            schema["primary_key"] = primary_key
        if unique_cols:
            schema["unique"] = unique_cols
        self.catalog[table_name] = schema
        self.save_catalog()
        tbl = Table(table_name, columns, col_types, primary_key=primary_key, unique_cols=unique_cols, data_dir=self.data_dir)
        self.tables[table_name] = tbl
        return f"Table {table_name} created."

    def _parse_values(self, val_str):
        vals = []
        buf = ""
        in_quote = False
        quote_char = None
        for ch in val_str:
            if ch in ("'", '"'):
                if in_quote and ch == quote_char:
                    in_quote = False
                    buf += ch
                elif not in_quote:
                    in_quote = True
                    quote_char = ch
                    buf += ch
                else:
                    buf += ch
            elif ch == ',' and not in_quote:
                vals.append(buf.strip())
                buf = ""
            else:
                buf += ch
        if buf:
            vals.append(buf.strip())
        clean_vals = []
        for v in vals:
            v = v.strip()
            if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
                clean_vals.append(v[1:-1])
            else:
                clean_vals.append(v)
        return clean_vals

    def _exec_insert(self, sql):
        import re
        pattern = re.compile(r'INSERT\s+INTO\s+(\w+)\s*(\((.*?)\))?\s*VALUES\s*\((.*)\)', re.IGNORECASE)
        m = pattern.match(sql)
        if not m:
            raise Exception("Invalid INSERT syntax")
        table_name = m.group(1)
        cols_str = m.group(3)
        values_str = m.group(4)
        if table_name not in self.tables:
            raise Exception(f"Table {table_name} does not exist")
        tbl = self.tables[table_name]
        if cols_str:
            cols = [c.strip() for c in cols_str.split(',')]
        else:
            cols = list(tbl.columns)
        values = self._parse_values(values_str)
        if len(cols) != len(values):
            raise Exception("Column count does not match value count")
        row = {}
        for col, val in zip(cols, values):
            if col not in tbl.columns:
                raise Exception(f"Unknown column {col}")
            row[col] = val
        return tbl.insert(row)

    def _exec_select(self, sql):
        tokens = sql.split()
        if not sql.upper().startswith("SELECT"):
            raise Exception("Invalid SELECT syntax")
        select_part = sql[6:]
        idx_from = select_part.upper().find("FROM")
        if idx_from < 0:
            raise Exception("SELECT without FROM")
        cols_str = select_part[:idx_from].strip()
        rest = select_part[idx_from+4:].strip()
        cols = [c.strip() for c in cols_str.split(',')]
        if cols == ['*']:
            cols = ['*']
        parts = rest.split()
        table1 = parts[0]
        join_table = None
        where_condition = None
        if "INNER JOIN" in rest.upper():
            upper_rest = rest.upper()
            join_idx = upper_rest.find("INNER JOIN")
            table1 = rest[:join_idx].strip()
            rest2 = rest[join_idx:]
            import re
            m = re.match(r'INNER\s+JOIN\s+(\w+)\s+ON\s+(.+)', rest2, re.IGNORECASE)
            if not m:
                raise Exception("Invalid INNER JOIN syntax")
            table2 = m.group(1)
            on_part = m.group(2).strip()
            if "WHERE" in on_part.upper():
                on_cond, where_condition = on_part.split("WHERE", 1)
                on_cond = on_cond.strip()
                where_condition = where_condition.strip()
            else:
                on_cond = on_part
                where_condition = None
            if '=' not in on_cond:
                raise Exception("Invalid JOIN ON condition")
            left, right = [x.strip() for x in on_cond.split('=', 1)]
            join_table = table2
            # perform join
            if table1 not in self.tables or join_table not in self.tables:
                raise Exception(f"Table {table1 if table1 not in self.tables else join_table} does not exist")
            t1 = self.tables[table1]
            t2 = self.tables[join_table]
            def parse_col(col_str):
                if '.' in col_str:
                    tbl, col = col_str.split('.',1)
                    return tbl, col
                else:
                    return None, col_str
            left_tbl, left_col = parse_col(left)
            right_tbl, right_col = parse_col(right)
            if left_tbl is None:
                left_tbl = table1
            if right_tbl is None:
                right_tbl = join_table
            result = []
            for row1 in t1.rows:
                for row2 in t2.rows:
                    val1 = row1[left_col] if left_tbl == table1 else row2[left_col]
                    val2 = row2[right_col] if right_tbl == join_table else row1[right_col]
                    if val1 == val2:
                        combined = {}
                        for col in t1.columns:
                            combined[f"{table1}.{col}"] = row1[col]
                        for col in t2.columns:
                            combined[f"{join_table}.{col}"] = row2[col]
                        result.append(combined)
            if where_condition:
                filtered = []
                conditions = [c.strip() for c in where_condition.split("AND")]
                for row in result:
                    ok = True
                    for cond in conditions:
                        if '=' not in cond:
                            raise Exception("Invalid WHERE condition")
                        left, right = cond.split('=', 1)
                        left = left.strip()
                        right = right.strip()
                        if (right.startswith("'") and right.endswith("'")) or (right.startswith('"') and right.endswith('"')):
                            right = right[1:-1]
                        if '.' in left:
                            key = left
                        else:
                            key = None
                            for k in row.keys():
                                if k.endswith(f".{left}"):
                                    key = k
                                    break
                            if not key:
                                raise Exception(f"Unknown column {left}")
                        if str(row.get(key)) != right:
                            ok = False
                            break
                    if ok:
                        filtered.append(row)
                result = filtered
            final = []
            if cols == ['*']:
                final = result
            else:
                for row in result:
                    out = {}
                    for col in cols:
                        if '.' in col:
                            out[col] = row.get(col)
                        else:
                            found = False
                            for k in row:
                                if k.endswith(f".{col}"):
                                    out[col] = row[k]
                                    found = True
                                    break
                            if not found:
                                out[col] = None
                    final.append(out)
            return final
        else:
            if "WHERE" in rest.upper():
                table1, where_condition = rest.split("WHERE",1)
                table1 = table1.strip()
                where_condition = where_condition.strip()
            else:
                table1 = rest.strip()
                where_condition = None
            if table1 not in self.tables:
                raise Exception(f"Table {table1} does not exist")
            tbl = self.tables[table1]
            where_list = []
            if where_condition:
                conditions = [c.strip() for c in where_condition.split("AND")]
                for cond in conditions:
                    if '=' not in cond:
                        raise Exception("Invalid WHERE condition")
                    left, right = cond.split('=',1)
                    left = left.strip()
                    right = right.strip()
                    if (right.startswith("'") and right.endswith("'")) or (right.startswith('"') and right.endswith('"')):
                        right = right[1:-1]
                    if left not in tbl.columns:
                        raise Exception(f"Unknown column {left}")
                    t = tbl.col_types[left]
                    val = cast_value(right, t)
                    where_list.append((left, val))
            if cols == ['*']:
                return tbl.select(tbl.columns, where=where_list)
            else:
                for c in cols:
                    if c not in tbl.columns:
                        raise Exception(f"Unknown column {c}")
                return tbl.select(cols, where=where_list)

    def _exec_update(self, sql):
        import re
        pattern = re.compile(r'UPDATE\s+(\w+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$', re.IGNORECASE)
        m = pattern.match(sql)
        if not m:
            raise Exception("Invalid UPDATE syntax")
        table = m.group(1)
        set_part = m.group(2).strip()
        where_part = m.group(3).strip() if m.group(3) else None
        if table not in self.tables:
            raise Exception(f"Table {table} does not exist")
        tbl = self.tables[table]
        assignments = [a.strip() for a in set_part.split(',')]
        set_values = {}
        for a in assignments:
            if '=' not in a:
                raise Exception("Invalid SET clause")
            col, val = a.split('=',1)
            col = col.strip()
            val = val.strip()
            if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
                val = val[1:-1]
            set_values[col] = val
        where_list = []
        if where_part:
            conditions = [c.strip() for c in where_part.split("AND")]
            for cond in conditions:
                if '=' not in cond:
                    raise Exception("Invalid WHERE condition")
                left, right = cond.split('=',1)
                left = left.strip()
                right = right.strip()
                if (right.startswith("'") and right.endswith("'")) or (right.startswith('"') and right.endswith('"')):
                    right = right[1:-1]
                if left not in tbl.columns:
                    raise Exception(f"Unknown column {left}")
                t = tbl.col_types[left]
                val = cast_value(right, t)
                where_list.append((left, val))
        count = tbl.update(set_values, where_list)
        return count

    def _exec_delete(self, sql):
        import re
        pattern = re.compile(r'DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?$', re.IGNORECASE)
        m = pattern.match(sql)
        if not m:
            raise Exception("Invalid DELETE syntax")
        table = m.group(1)
        where_part = m.group(2).strip() if m.group(2) else None
        if table not in self.tables:
            raise Exception(f"Table {table} does not exist")
        tbl = self.tables[table]
        where_list = []
        if where_part:
            conditions = [c.strip() for c in where_part.split("AND")]
            for cond in conditions:
                if '=' not in cond:
                    raise Exception("Invalid WHERE condition")
                left, right = cond.split('=',1)
                left = left.strip()
                right = right.strip()
                if (right.startswith("'") and right.endswith("'")) or (right.startswith('"') and right.endswith('"')):
                    right = right[1:-1]
                if left not in tbl.columns:
                    raise Exception(f"Unknown column {left}")
                t = tbl.col_types[left]
                val = cast_value(right, t)
                where_list.append((left, val))
        count = tbl.delete(where_list if where_list else None)
        return count
