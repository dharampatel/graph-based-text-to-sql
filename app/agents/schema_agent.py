import logging, os, json
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from app.config import embeddings, llm
from app.state.agent_state import GlobalState
from app.utils import extract_schema_from_db, BASE_DIR, DB_PATH

# Dynamic DB path (portable)
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_schema_index")

# Cache
_vectorstore = None


def build_schema_index(schema_docs):
    """Creates and persists Chroma index for schema documents."""
    if not schema_docs or len(schema_docs) == 0:
        raise ValueError("No schema documents to index.")

    logging.info(f"🔧 Building Chroma index for {len(schema_docs)} schema docs...")
    vectorstore = Chroma.from_documents(
        documents=schema_docs,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    logging.info("✅ Schema index built and persisted.")
    return vectorstore


async def schema_agent_node(state: GlobalState) -> GlobalState:
    """Retrieves schema context using Chroma vectorstore and updates state."""
    global _vectorstore

    query = state.get("rewritten_query") or state.get("original_query")
    if not query:
        raise ValueError("Missing rewritten_query or original_query in GlobalState")

    # Load or build vectorstore
    if _vectorstore is None:
        logging.info("📦 Loading Chroma index...")
        try:
            _vectorstore = Chroma(
                persist_directory=CHROMA_PATH,
                embedding_function=embeddings
            )
            if _vectorstore._collection.count() == 0:
                raise ValueError("Empty Chroma DB, rebuilding...")
        except Exception as e:
            logging.warning(f"⚠️ Rebuilding Chroma due to: {e}")
            schema_docs = extract_schema_from_db(DB_PATH)
            _vectorstore = build_schema_index(schema_docs)

    # Retrieve relevant schema
    retriever = _vectorstore.as_retriever(search_kwargs={"k": 3})
    results = retriever.invoke(query)

    schema_context = "\n".join([doc.page_content for doc in results])
    table_names = [doc.metadata.get("source", "unknown") for doc in results]

    # Summarize schema context
    schema_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a database schema summarizer."),
        ("human", f"Schema context:\n{schema_context}\n\nUser query: {query}\nSummarize key tables and relations.")
    ])
    chain = schema_prompt | llm
    summary_result = await chain.ainvoke({})
    schema_summary = summary_result.content.strip()

    new_state = state.copy()
    new_state.update({
        "schema_context": schema_context,
        "relevant_tables": table_names,
        "rag_docs": [{"text": d.page_content} for d in results],
        "schema_summary": schema_summary,
        "status": "schema_retrieved"
    })

    logging.info(f"✅ Schema Agent retrieved tables: {new_state}")

    return new_state
