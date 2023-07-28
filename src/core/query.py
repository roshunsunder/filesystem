from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import openai
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.vectorstores import FAISS

from ..config.settings import settings

class SearchResult:
    """Represents a single search result"""
    def __init__(self, path: str, score: float, metadata: Dict[str, Any]):
        self.path = path
        self.score = score
        self.metadata = metadata
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "score": self.score,
            "metadata": self.metadata
        }

class QueryCache:
    """Simple in-memory cache for search results"""
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)
        
    def get(self, key: str) -> Optional[List[SearchResult]]:
        if key not in self.cache:
            return None
            
        entry = self.cache[key]
        if datetime.now() - entry["timestamp"] > self.ttl:
            del self.cache[key]
            return None
            
        return entry["results"]
        
    def set(self, key: str, results: List[SearchResult]):
        self.cache[key] = {
            "timestamp": datetime.now(),
            "results": results
        }

class QueryDriver:
    """Enhanced query system with caching and filtering"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.embedding_model = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        self.vector_store: Optional[FAISS] = None
        self.cache = QueryCache(ttl_seconds=settings.CACHE_TTL)
        
    def load_from_disk(self, path: str):
        """Load the vector store from disk"""
        try:
            self.vector_store = FAISS.load_local(path, self.embedding_model)
        except Exception as e:
            self.logger.error(f"Error loading vector store: {str(e)}")
            raise
            
    def _create_cache_key(self, query: str, filters: Dict[str, Any]) -> str:
        """Create a cache key from query and filters"""
        filter_str = "&".join(f"{k}={v}" for k, v in sorted(filters.items()))
        return f"{query}|{filter_str}"
        
    def _apply_filters(self, results: List[SearchResult], filters: Dict[str, Any]) -> List[SearchResult]:
        """Apply filters to search results"""
        filtered = results
        
        for key, value in filters.items():
            if key == "file_type":
                filtered = [r for r in filtered if r.metadata.get("file_type") == value]
            elif key == "min_date":
                min_date = datetime.fromisoformat(value)
                filtered = [r for r in filtered if datetime.fromtimestamp(r.metadata.get("modified", 0)) >= min_date]
            elif key == "max_date":
                max_date = datetime.fromisoformat(value)
                filtered = [r for r in filtered if datetime.fromtimestamp(r.metadata.get("modified", 0)) <= max_date]
            elif key == "min_size":
                filtered = [r for r in filtered if r.metadata.get("size", 0) >= value]
            elif key == "max_size":
                filtered = [r for r in filtered if r.metadata.get("size", 0) <= value]
                
        return filtered
        
    def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search the vector store with optional filters
        
        Args:
            query: The search query
            filters: Optional filters to apply. Supported filters:
                    - file_type: str
                    - min_date: ISO format date string
                    - max_date: ISO format date string
                    - min_size: int (bytes)
                    - max_size: int (bytes)
        """
        if not self.vector_store:
            raise ValueError("Vector store not loaded")
            
        filters = filters or {}
        cache_key = self._create_cache_key(query, filters)
        
        # Check cache
        if settings.ENABLE_CACHE:
            cached_results = self.cache.get(cache_key)
            if cached_results:
                return cached_results
                
        # Perform search
        raw_results = self.vector_store.similarity_search_with_score(
            query, k=settings.MAX_RESULTS
        )
        
        # Convert to SearchResult objects
        results = [
            SearchResult(
                path=doc.metadata["path"],
                score=score,
                metadata=doc.metadata
            )
            for doc, score in raw_results
            if score >= settings.SIMILARITY_THRESHOLD
        ]
        
        # Apply filters
        results = self._apply_filters(results, filters)
        
        # Update cache
        if settings.ENABLE_CACHE:
            self.cache.set(cache_key, results)
            
        return results 