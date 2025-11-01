import logging
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate

from app.config import llm
from app.state.agent_state import GlobalState


async def explainability_node(state: GlobalState) -> GlobalState:
    """
    Explainability Agent:
    - Converts SQL and query results into plain-language insights.
    - Helps users understand what the SQL does and what the data means.
    """

    sql_query = state.get("validated_sql") or state.get("generated_sql")
    execution_result = state.get("execution_result", {})

    if not sql_query:
        raise ValueError("Missing SQL to explain.")
    if not execution_result:
        raise ValueError("Missing execution results to explain.")

    logging.info("🧠 Generating natural language explanation for SQL and results...")

    # Use only top 5 rows to keep prompt short
    sample_rows = execution_result.get("rows", [])[:5]

    explain_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert data analyst who explains SQL queries and results in simple, plain language.\n"
         "Focus on clarity and insight — describe what the query does and what the results mean."),
        ("human",
         "SQL Query:\n{sql_query}\n\n"
         "Sample of Query Results (first 5 rows):\n{sample_rows}\n\n"
         "Explain in natural language:\n"
         "1. What does this SQL query do?\n"
         "2. What are the main insights or patterns visible in the results?")
    ])

    chain = explain_prompt | llm

    try:
        response = await chain.ainvoke({
            "sql_query": sql_query,
            "sample_rows": sample_rows
        })
        explanation_text = response.content.strip()
    except Exception as e:
        logging.error(f"⚠️ Failed to generate explanation: {e}")
        explanation_text = f"Error generating explanation: {str(e)}"

    # ---- Record History ----
    explanation_history = state.get("explanation_history", [])
    explanation_history.append({
        "time": datetime.utcnow().isoformat(),
        "sql": sql_query,
        "explanation": explanation_text,
        "rows_used": len(sample_rows)
    })

    # ---- Update GlobalState ----
    new_state = state.copy()
    new_state.update({
        "natural_language_explanation": explanation_text,
        "explanation_history": explanation_history,
        "status": "explained"
    })

    logging.info("✅ Explainability Agent successfully generated explanation.")
    return new_state
