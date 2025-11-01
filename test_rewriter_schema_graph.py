import asyncio

from app.agents.text_to_sql_graph import build_text_to_sql_graph


async def run_test():
    graph = build_text_to_sql_graph().compile()
    state = {
        "user_id": "demo_user",
        "session_id": "sess_001",
        "original_query": "Show me total sales by region for 2024",
        "schema_context": "CREATE TABLE sales (region TEXT, amount INT, year INT);",
    }
    result = await graph.ainvoke(state)
    print("\n🧩 Final Output:\n", result)

if __name__ == "__main__":
    asyncio.run(run_test())
