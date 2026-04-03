"""
Build vector store from knowledge base documents
Run this once to create the index
"""
from src.core import build_vector_store, get_logger

logger = get_logger("build_index")

if __name__ == "__main__":
    logger.info("Building vector store from knowledge base...")

    try:
        vector_store = build_vector_store()

        logger.info("Vector store built successfully!")
        logger.info("Running test search...")

        # Test search
        results = vector_store.similarity_search("how to test login API", k=2)

        for i, doc in enumerate(results, 1):
            source = doc.metadata.get('source', 'Unknown')
            logger.info(f"[{i}] {source}")
            logger.info(f"    {doc.page_content[:150]}...")

    except Exception as e:
        logger.error(f"Error: {e}")