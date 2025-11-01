import logging
from datetime import datetime
from typing import List, Dict, Any
from app.state.agent_state import GlobalState


def infer_chart_type(columns: List[str], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simple heuristic to decide chart type and axes based on data.
    """
    if not columns or not rows:
        return {
            "chart_type": "table",
            "reasoning": "No data available; defaulting to table visualization.",
            "x_axis": None,
            "y_axis": None
        }

    # Detect numeric vs. categorical columns
    first_row = rows[0]
    numeric_cols = [col for col, val in first_row.items() if isinstance(val, (int, float))]
    categorical_cols = [col for col in columns if col not in numeric_cols]

    if len(numeric_cols) >= 2:
        return {
            "chart_type": "scatter",
            "reasoning": "Detected multiple numeric columns; scatter plot suitable.",
            "x_axis": numeric_cols[0],
            "y_axis": numeric_cols[1]
        }

    if len(numeric_cols) == 1 and len(categorical_cols) >= 1:
        return {
            "chart_type": "bar",
            "reasoning": f"Detected categorical + numeric data; using bar chart with {categorical_cols[0]} on X-axis.",
            "x_axis": categorical_cols[0],
            "y_axis": numeric_cols[0]
        }

    if len(numeric_cols) == 1 and len(rows) <= 5:
        return {
            "chart_type": "pie",
            "reasoning": "Small dataset with one numeric column; pie chart suitable.",
            "x_axis": categorical_cols[0] if categorical_cols else None,
            "y_axis": numeric_cols[0]
        }

    return {
        "chart_type": "table",
        "reasoning": "Data not suitable for visual chart; showing as table.",
        "x_axis": None,
        "y_axis": None
    }


async def visualization_node(state: GlobalState) -> GlobalState:
    """
    Visualization Agent:
    - Analyzes execution results.
    - Suggests visualization type (table, bar, pie, scatter).
    - Updates GlobalState with visualization spec and preview.
    """
    execution_result = state.get("execution_result", {})
    rows = execution_result.get("rows", [])
    columns = execution_result.get("columns", [])

    logging.info("🎨 Creating visualization specification...")

    # Infer visualization spec
    vis_spec = infer_chart_type(columns, rows)

    # Prepare preview (limit to 10 rows)
    data_preview = rows[:10] if rows else []

    # Record visualization history
    vis_history = state.get("visual_assets", {}).get("history", [])
    vis_history.append({
        "time": datetime.utcnow().isoformat(),
        "spec": vis_spec,
    })

    # Update GlobalState
    new_state = state.copy()
    new_state.update({
        "visual_assets": {
            "spec": vis_spec,
            "data_preview": data_preview,
            "history": vis_history
        },
        "status": "visual_ready"
    })

    logging.info(f"📊 Visualization ready: {vis_spec['chart_type']}")
    return new_state
