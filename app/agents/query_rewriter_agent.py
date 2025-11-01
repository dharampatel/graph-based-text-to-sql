import json, re, logging
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate

from app.state.agent_state import GlobalState
from app.config import llm

# Prompt for rewriting
rewriter_system = """You are a query rewriter for a Text-to-SQL system.
Your task is to rewrite natural-language queries into clear, SQL-friendly questions.
- Preserve user intent.
- Use placeholders like <DATE_RANGE> if needed.
- Return JSON with: rewritten_query, explanation, metadata.
"""

rewriter_prompt = ChatPromptTemplate.from_messages([
    ("system", rewriter_system),
    ("human", 'Original user question: "{query}"\nReturn JSON as instructed.')
])

# ------------------------------------------------------------
# Query Rewriter Node (LangGraph compatible)
# ------------------------------------------------------------
async def query_rewriter_node(state: GlobalState) -> GlobalState:
    """Query Rewriter Agent using the shared GlobalState."""
    query = state.get("original_query", "").strip()
    if not query:
        raise ValueError("Missing original_query in GlobalState")

    chain = rewriter_prompt | llm
    result = await chain.ainvoke({"query": query})
    text = result.content.strip()

    # Try parsing JSON safely
    match = re.search(r"\{[\s\S]*\}", text)
    json_str = match.group(0) if match else text
    try:
        parsed = json.loads(json_str)
    except Exception:
        parsed = {"rewritten_query": text, "explanation": "parse-fallback", "metadata": {}}

    rewritten = parsed.get("rewritten_query", query).strip()
    explanation = parsed.get("explanation", "")
    metadata = parsed.get("metadata", {})

    # Build new state
    history = state.get("rewrite_history", [])
    history.append({
        "time": datetime.utcnow().isoformat(),
        "model": llm.model,
        "input": query,
        "output": rewritten,
        "explanation": explanation,
        "metadata": metadata
    })

    new_state = state.copy()
    new_state.update({
        "rewritten_query": rewritten,
        "rewrite_history": history,
        "rewrite_explanation": explanation,
        "status": "query_rewritten",
    })

    logging.info(f"✅ Query rewritten: {rewritten}")
    return new_state


async def decide_if_rewrite(state: GlobalState) -> GlobalState:
    q = state.get("original_query", "")
    tokens = len(q.split())
    has_sql_terms = any(w in q.lower() for w in ["select", "from", "where", "join", "table", "column"])
    needs_rewrite = tokens < 6 or not has_sql_terms
    return {**state, "needs_rewrite": needs_rewrite}
