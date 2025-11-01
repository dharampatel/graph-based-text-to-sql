import os
import sqlite3
from langchain_core.documents import Document


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # points to project root
DB_PATH = os.path.join(BASE_DIR, "test_db.sqlite")

def extract_schema_from_db(db_path: str):
    """
    Extracts the SQLite schema and returns a list of LangChain Documents.
    Each Document contains:
      - page_content: table definition (name + columns)
      - metadata: { 'table_name': <table_name> }
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get user-defined tables (exclude system tables)
    tables = cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%';
    """).fetchall()

    docs = []
    if not tables:
        print("⚠️ No tables found in the database.")
        return docs

    for (table_name,) in tables:
        columns = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
        if not columns:
            continue

        col_defs = [f"{col[1]} ({col[2]})" for col in columns]
        schema_text = f"Table: {table_name}\nColumns:\n" + "\n".join(col_defs)

        # ✅ Include metadata with consistent key
        docs.append(Document(page_content=schema_text, metadata={"source": table_name}))

    conn.close()
    print(f"✅ Extracted schema for {len(docs)} tables.")
    return docs


if __name__ == "__main__":
    docs = extract_schema_from_db(DB_PATH)
    print(len(docs))
    for d in docs:
        print(d.page_content)