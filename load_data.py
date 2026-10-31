from db import DB, DDL
from generate_data import generate
def main():
    d = DB()
    for s in DDL: d.run(s)
    P, O, R = generate()
    d.load("PRODUCTS", P); d.load("ORDERS", O); d.load("RETURN_EVENTS", R)
    print("Loaded", len(P), "products,", len(O), "orders,", len(R), "returns into", "Exasol" if d.ex else "DuckDB demo")
if __name__ == "__main__": main()
