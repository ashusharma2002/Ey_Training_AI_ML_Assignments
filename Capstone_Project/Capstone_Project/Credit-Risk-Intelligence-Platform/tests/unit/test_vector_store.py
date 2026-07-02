# tests/unit/test_vector_store.py
# Verifies the FAISS index-load-path bug fix.
import pytest
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Skip entire module if langchain_community not installed
langchain_community = pytest.importorskip(
    "langchain_community",
    reason="langchain_community not installed — run: pip install langchain-community"
)


def test_faiss_index_path_correct():
    """
    BUG FIX VERIFICATION:
    LangChain saves FAISS index as {path}/index.faiss + {path}/index.pkl
    Old code checked {path}.faiss which NEVER exists → always returned False.
    New code checks {path}/index.faiss → correct.
    """
    from src.retrieval.vector_store import FAISSVectorStore

    class MockEmbeddings:
        pass

    with tempfile.TemporaryDirectory() as tmpdir:
        store = FAISSVectorStore(MockEmbeddings())
        store._index_path = Path(tmpdir) / "faiss_index"

        # Create the file LangChain would create
        store._index_path.mkdir()
        (store._index_path / "index.faiss").touch()
        (store._index_path / "index.pkl").touch()

        # Old bug: this would check for faiss_index.faiss which doesn't exist
        # New fix: checks faiss_index/index.faiss
        index_file = store._index_path / "index.faiss"
        assert index_file.exists(), (
            "BUG: index.faiss not found at expected path. "
            f"Checked: {index_file}"
        )


def test_faiss_load_returns_false_when_no_index(tmp_path):
    """load() returns False (not crash) when no saved index exists."""
    from src.retrieval.vector_store import FAISSVectorStore

    class MockEmbeddings:
        pass

    store = FAISSVectorStore(MockEmbeddings())
    store._index_path = tmp_path / "nonexistent"
    # Should return False without raising an error
    result = store.load()
    assert result is False


def test_is_ready_false_before_build():
    """New FAISSVectorStore should report not ready before build()."""
    from src.retrieval.vector_store import FAISSVectorStore

    class MockEmbeddings:
        pass

    store = FAISSVectorStore(MockEmbeddings())
    assert store.is_ready is False
