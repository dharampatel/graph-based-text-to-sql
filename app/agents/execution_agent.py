import sqlite3
import time
import logging
from datetime import datetime

from app.state.agent_state import GlobalState
from app.utils import DB_PATH


def execute_sql_on_replica(sql_query: str, db_path: str):
    """
    Executes a SQL query safely on a replica SQLite DB.
    Returns columns, rows, and metadata.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # to access columns by name
    cursor = conn.cursor()

    try:
        start = time.time()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        execution_time = round(time.time() - start, 4)

        # Extract column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        result = [dict(row) for row in rows]

        conn.close()
        return {
            "success": True,
            "columns": columns,
            "rows": result,
            "row_count": len(result),
            "execution_time": execution_time,
            "error": None
        }

    except Exception as e:
        conn.close()
        logging.error(f"⚠️ SQL execution failed: {e}")
        return {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time": 0,
            "error": str(e)
        }


async def query_execution_node(state: GlobalState) -> GlobalState:
    """
    Execution Agent:
    - Runs validated SQL against replica DB.
    - Updates GlobalState with query results.
    """
    sql_query = state.get("validated_sql") or state.get("generated_sql")

    if not sql_query:
        raise ValueError("Missing validated_sql or generated_sql in GlobalState")

    logging.info(f"🚀 Executing SQL on replica: {sql_query}")

    result = execute_sql_on_replica(sql_query, DB_PATH)

    # ---- Update History ----
    execution_history = state.get("execution_history", [])
    execution_history.append({
        "time": datetime.utcnow().isoformat(),
        "query": sql_query,
        "db_path": DB_PATH,
        "success": result["success"],
        "row_count": result["row_count"],
        "execution_time": result["execution_time"],
        "error": result["error"]
    })

    new_state = state.copy()
    new_state.update({
        "execution_result": result,
        "execution_history": execution_history,
        "status": "query_executed" if result["success"] else "execution_failed"
    })

    if result["success"]:
        logging.info(f"✅ Query executed successfully — {result['row_count']} rows in {result['execution_time']}s")
    else:
        logging.warning(f"⚠️ Query execution failed: {result['error']}")

    return new_state
