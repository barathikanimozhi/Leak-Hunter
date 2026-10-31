"""Quick connection test: python check_exasol.py"""
from db import DB
d = DB(); print("Connected to", "Exasol" if d.ex else "DuckDB (dev)"); print(d.q("SELECT 1 AS ok"))
