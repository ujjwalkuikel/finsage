import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.core.memory import SQLiteVectorStore, cosine_similarity

class TestMemoryAndVectorStore(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for the SQLite database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.test_dir) / "test_memories.db")
        
    def tearDown(self):
        # Remove temporary directory and files
        shutil.rmtree(self.test_dir)

    def test_cosine_similarity(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(v1, v2), 1.0)

        v3 = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(v1, v3), 0.0)

        v4 = [-1.0, 0.0, 0.0]
        self.assertAlmostEqual(cosine_similarity(v1, v4), -1.0)

    @patch("app.core.memory.get_llm_client")
    def test_sqlite_vector_store(self, mock_get_client):
        # Mock LLM Client get_embedding
        mock_client = MagicMock()
        mock_client.get_embedding.side_effect = lambda text: [1.0, 0.0, 0.0] if "buy" in text.lower() else [0.0, 1.0, 0.0]
        mock_get_client.return_value = mock_client


        store = SQLiteVectorStore(db_path=self.db_path)
        
        # Add records
        store.add_record(
            text="Buy AAPL stock because it broke out.",
            metadata={"symbol": "AAPL", "record_type": "investment_thesis"},
            doc_id="doc1"
        )
        
        store.add_record(
            text="News headline: inflation rate cuts.",
            metadata={"symbol": "SPY", "record_type": "macro_news"},
            doc_id="doc2"
        )

        # Query records matching "buy" (should match doc1 with score 1.0)
        results = store.query("buy stock info")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "doc1")
        self.assertAlmostEqual(results[0]["score"], 1.0)

        # Query with metadata filter
        filtered_results = store.query("buy stock info", filter_metadata={"symbol": "AAPL"})
        self.assertEqual(len(filtered_results), 1)
        self.assertEqual(filtered_results[0]["id"], "doc1")
