from abc import ABC, abstractmethod
import sqlite3
import json
import math
import datetime as dt
from pathlib import Path
from app.agents.llm import get_llm_client

class BaseVectorStore(ABC):
    @abstractmethod
    def add_record(self, text: str, metadata: dict, doc_id: str = None) -> None:
        """Add a text document and its metadata to the vector store."""
        pass

    @abstractmethod
    def query(self, text: str, filter_metadata: dict = None, limit: int = 5) -> list[dict]:
        """Search the store for similar documents based on text semantic similarity."""
        pass


def dot_product(v1: list[float], v2: list[float]) -> float:
    return sum(x * y for x, y in zip(v1, v2))

def magnitude(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v))

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    mag1 = magnitude(v1)
    mag2 = magnitude(v2)
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
    return dot_product(v1, v2) / (mag1 * mag2)


class SQLiteVectorStore(BaseVectorStore):
    """
    A lightweight, zero-dependency Vector Store utilizing SQLite and the Gemini REST Embedding API.
    Saves data to memories.db on disk and computes cosine similarity in pure Python.
    """
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path(__file__).resolve().parent.parent.parent.parent / "memories.db")
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id          TEXT PRIMARY KEY,
                    text        TEXT NOT NULL,
                    metadata    TEXT NOT NULL,
                    vector      TEXT NOT NULL,
                    timestamp   TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def add_record(self, text: str, metadata: dict, doc_id: str = None) -> None:
        import uuid
        if doc_id is None:
            doc_id = str(uuid.uuid4())
            
        # Get embedding vector from LLM client
        client = get_llm_client()
        vector = client.get_embedding(text)
        
        vector_str = json.dumps(vector)
        metadata_str = json.dumps(metadata)
        timestamp_str = dt.datetime.utcnow().isoformat()
        
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO memories (id, text, metadata, vector, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (doc_id, text, metadata_str, vector_str, timestamp_str)
            )
            conn.commit()
        finally:
            conn.close()

    def query(self, text: str, filter_metadata: dict = None, limit: int = 5) -> list[dict]:
        # Get embedding vector for the query text
        client = get_llm_client()
        query_vector = client.get_embedding(text)
        
        # Pull all records from SQLite
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT id, text, metadata, vector, timestamp FROM memories")
            rows = cursor.fetchall()
        finally:
            conn.close()

            
        results = []
        for row in rows:
            row_meta = json.loads(row["metadata"])
            
            # Apply metadata filtering if specified
            if filter_metadata:
                match = True
                for k, v in filter_metadata.items():
                    if row_meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
                    
            row_vector = json.loads(row["vector"])
            score = cosine_similarity(query_vector, row_vector)
            
            results.append({
                "id": row["id"],
                "text": row["text"],
                "metadata": row_meta,
                "score": round(score, 4),
                "timestamp": row["timestamp"]
            })
            
        # Sort descending by similarity score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

def get_vector_store() -> BaseVectorStore:
    """Factory to retrieve the configured Vector Store client."""
    # To switch to Chroma, you could add:
    # if config.USE_CHROMA:
    #     from app.core.chroma_store import ChromaVectorStore
    #     return ChromaVectorStore()
    return SQLiteVectorStore()

