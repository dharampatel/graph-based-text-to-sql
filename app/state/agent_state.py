from typing import TypedDict, List, Dict, Optional, Any


class GlobalState(TypedDict, total=False):
    """Global state shared across all Text-to-SQL agents."""

    # --- Core Session Info ---
    user_id: Optional[str]
    session_id: Optional[str]
    status: Optional[str]                # e.g. "query_rewritten", "sql_generated", "query_executed"
    needs_rewrite: Optional[bool]        # whether rewrite agent should be invoked again
    created_at: Optional[str]            # ISO timestamp when session started
    updated_at: Optional[str]            # ISO timestamp of latest update

    # --- Query Handling ---
    original_query: str                  # user's raw input
    rewritten_query: Optional[str]       # refined or clarified version
    rewrite_explanation: Optional[str]   # reason for rewrite

    # --- Schema & Context ---
    schema_context: Optional[str]        # full DDL schema text
    schema_summary: Optional[str]        # concise schema summary for LLM context
    relevant_tables: Optional[List[str]] # list of tables deemed relevant
    rag_docs: Optional[List[Dict[str, Any]]]  # retrieved schema or doc context

    # --- SQL Generation ---
    generated_sql: Optional[str]         # SQL produced by generation agent
    validated_sql: Optional[str]         # SQL confirmed by validation agent

    # --- Validation Results ---
    validation_passed: Optional[bool]
    validation_explanation: Optional[str]
    validation_history: Optional[List[Dict[str, Any]]]

    # --- Execution Results ---
    execution_result: Optional[Dict[str, Any]]      # result payload: rows, columns, timing, etc.
    execution_history: Optional[List[Dict[str, Any]]]  # record of all executions

    # --- Analysis / Visualization ---
    visual_assets: Optional[Dict[str, Any]]         # charts, tables, or plots
    natural_language_explanation: Optional[str]     # human-readable description of query results

    # --- Agent Histories ---
    rewrite_history: Optional[List[Dict[str, Any]]]
    generation_history: Optional[List[Dict[str, Any]]]
    explanation_history: Optional[List[Dict[str, Any]]]  # for Explainability Agent outputs

    # --- Misc ---
    logs: Optional[List[str]]                       # textual logs for debugging
    next_action: Optional[str]
