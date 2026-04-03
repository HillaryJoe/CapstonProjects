"""
Vector Store for RAG
Loads documents from knowledge base and creates searchable vector store
"""
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
from src.core import get_logger

try:
    from langchain_chroma import Chroma
    CHROMA_AVAILABLE = True
except ModuleNotFoundError:
    Chroma = None
    CHROMA_AVAILABLE = False

load_dotenv()

logger = get_logger("vector_store")

# Paths
ROOT = Path(__file__).resolve().parents[2]
KB_DIR = ROOT / "data" / "knowledge_base"
VECTOR_STORE_DIR = ROOT / "data" / "vector_store"

# Initialize embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY")
)

def build_vector_store():
    """Load documents, split into chunks, and create vector store."""

    logger.info("Building vector store...")

    # 1. Load documents
    logger.info(f"Loading documents from {KB_DIR}...")
    loader = DirectoryLoader(
        str(KB_DIR),
        glob="**/*.md",
        loader_cls=TextLoader
    )
    documents = loader.load()
    logger.info(f"Loaded {len(documents)} documents")

    # 2. Split into chunks
    logger.info("Splitting documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} chunks")

    # 3. Create vector store
    logger.info("Generating embeddings and storing in ChromaDB...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTOR_STORE_DIR)
    )
    logger.info(f"Vector store created at {VECTOR_STORE_DIR}")

    return vector_store

def load_vector_store():
    """Load existing vector store."""

    if not CHROMA_AVAILABLE:
        raise ModuleNotFoundError(
            "langchain_chroma is not installed. Install with `pip install langchain-chroma`, "
            "or set SEARCH_VECTOR_STORE_FALLBACK=1 for no-vector fallback."
        )

    if not VECTOR_STORE_DIR.exists():
        raise FileNotFoundError(
            f"Vector store not found at {VECTOR_STORE_DIR}. "
            "Run build_vector_store() first."
        )

    return Chroma(
        persist_directory=str(VECTOR_STORE_DIR),
        embedding_function=embeddings
    )


def search_vector_store(query: str, top_k: int = 3):
    """Search vector store for relevant documents."""

    if not CHROMA_AVAILABLE or os.getenv("SEARCH_VECTOR_STORE_FALLBACK", "0") == "1":
        # fallback: return top documents by file order rather than embedding similarity
        docs = []
        for md in sorted(KB_DIR.glob("*.md")):
            text = md.read_text(encoding="utf-8")
            docs.append((type("Doc", (), {"page_content": text, "metadata": {"source": md.name}}), 0.0))

        return docs[:top_k]

    vector_store = load_vector_store()
    results = vector_store.similarity_search_with_score(query, k=top_k)

    return results