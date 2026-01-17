# client/orchestrator/rag.py

async def run_rag(query: str, collections: list[str]):
    """
    Retrieve relevant knowledge from vector DB / documents.
    """

    # Stub for now
    return {
        "source": collections,
        "content": f"Relevant information for query: '{query}'"
    }
