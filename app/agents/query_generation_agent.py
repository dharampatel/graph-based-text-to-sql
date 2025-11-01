import json
import logging
import re
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate

from app.config import llm
from app.state.agent_state import GlobalState


async def query_generation_node(state: GlobalState) -> GlobalState:
    """
    Query Generation Agent:
    - Uses rewritten query + schema context to generate valid SQL.
    - Updates GlobalState with SQL and explanation.
    """
    query = state.get("rewritten_query") or state.get("original_query")
    schema_context = state.get("schema_context", "")
    schema_summary = state.get("schema_summary", "")

    if not query or not schema_context:
        raise ValueError("Missing rewritten_query or schema_context in GlobalState")

    logging.info("🧠 Generating SQL from query and schema...")

    generation_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert data analyst who converts natural language to SQL.\n"
         "Use the provided database schema context and summary to craft the SQL query.\n"
         "Make sure the SQL is syntactically valid for SQLite and uses the correct tables and joins.\n"
         "Respond ONLY in JSON with the following keys:\n"
         "{{ 'sql': '<generated_sql>', 'explanation': '<brief reasoning>' }}"),
        ("human",
         "Schema Context:\n{schema_context}\n\n"
         "Schema Summary:\n{schema_summary}\n\n"
         "User Query:\n{query}")
    ])

    chain = generation_prompt | llm
    response = await chain.ainvoke({
        "query": query,
        "schema_context": schema_context,
        "schema_summary": schema_summary
    })

    text = response.content.strip()
    logging.info(f"🔍 Raw model output:\n{text}")

    # --- Clean text (remove ```json fences) ---
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()

    # --- Robust JSON Parse ---
    parsed = None
    try:
        parsed = json.loads(text)
    except Exception:
        logging.warning("⚠️ Could not parse JSON directly. Attempting extraction...")

        # Try to extract first JSON-like block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                parsed = json.loads(json_str)
            except Exception:
                logging.error("❌ Still could not parse extracted JSON.")
        if not parsed:
            parsed = {"sql": text, "explanation": "LLM did not return valid JSON."}

    sql_query = parsed.get("sql", "").strip()
    explanation = parsed.get("explanation", "").strip()

    # Safety check — enforce SELECT prefix
    if not sql_query.lower().startswith("select"):
        logging.warning("⚠️ Non-select SQL detected; enforcing read-only mode.")
        sql_query = "SELECT " + sql_query

    # --- Update History ---
    history = state.get("generation_history", [])
    history.append({
        "time": datetime.utcnow().isoformat(),
        "model": getattr(llm, "model", "unknown"),
        "input_query": query,
        "output_sql": sql_query,
        "explanation": explanation,
        "raw_output": text
    })

    new_state = state.copy()
    new_state.update({
        "generated_sql": sql_query,
        "sql_explanation": explanation,
        "generation_history": history,
        "status": "sql_generated"
    })

    logging.info(f"✅ SQL generated:\n{sql_query}")
    return new_state
