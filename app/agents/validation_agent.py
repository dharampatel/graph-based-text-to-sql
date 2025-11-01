import logging
import re
import sqlite3
from datetime import datetime

from app.state.agent_state import GlobalState
from app.utils import DB_PATH


async def validation_node(state: GlobalState) -> GlobalState:
    """
    Validation Agent:
    - Ensures the generated SQL is syntactically valid and safe.
    - Detects any unsafe or invalid SQL before execution.
    - Updates GlobalState with validation status and explanation.
    """

    sql_query = state.get("generated_sql", "")
    if not sql_query:
        raise ValueError("No SQL found in state to validate")

    logging.info("🧩 Validating generated SQL for safety and syntax correctness...")

    # ---- 1. Security Validation ----
    forbidden_keywords = ["delete", "drop", "update", "insert", "alter", "truncate"]
    lower_sql = sql_query.lower()

    for keyword in forbidden_keywords:
        if re.search(rf"\b{keyword}\b", lower_sql):
            explanation = f"❌ Unsafe SQL detected: contains forbidden keyword '{keyword.upper()}'"
            logging.warning(explanation)

            new_state = state.copy()
            new_state.update({
                "validation_passed": False,
                "validation_explanation": explanation,
                "status": "validation_failed"
            })
            return new_state

    # ---- 2. Syntax Validation (SQLite dry run) ----
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create empty tables based on schema context if available (optional future improvement)
        # For now, just prepare statement to check syntax
        cursor.execute(f"EXPLAIN {sql_query}")
        conn.close()

        validation_passed = True
        explanation = "✅ SQL syntax is valid and query is read-only."

    except sqlite3.Error as e:
        validation_passed = False
        explanation = f"❌ SQL validation failed: {str(e)}"
        logging.error(explanation)

    # ---- 3. Record history ----
    validation_history = state.get("validation_history", [])
    validation_history.append({
        "time": datetime.utcnow().isoformat(),
        "sql": sql_query,
        "passed": validation_passed,
        "explanation": explanation
    })

    # ---- 4. Update GlobalState ----
    new_state = state.copy()
    new_state.update({
        "validation_passed": validation_passed,
        "validation_explanation": explanation,
        "validation_history": validation_history,
        "status": "validated" if validation_passed else "validation_failed"
    })

    if validation_passed:
        logging.info("✅ SQL validation passed.")
    else:
        logging.warning("⚠️ SQL validation failed.")

    return new_state
