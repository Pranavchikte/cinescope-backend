import chromadb
from chromadb.config import Settings
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        """Initialize ChromaDB client"""
        self.client = chromadb.PersistentClient(
            path="/app/chroma_data",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Ensure collection exists
        self.collection = self._get_or_create_collection()
        logger.info(f"ChromaDB initialized. Collection size: {self.collection.count()}")
    
    def _get_or_create_collection(self):
        """Get or create collection with error handling"""
        try:
            # Try to get existing collection first
            return self.client.get_collection(name="movies")
        except Exception:
            # If doesn't exist, create new
            try:
                return self.client.create_collection(
                    name="movies",
                    metadata={"description": "Movie embeddings for RAG"}
                )
            except Exception as e:
                logger.warning(f"Collection error: {e}")
                return self.client.get_or_create_collection(
                    name="movies",
                    metadata={"description": "Movie embeddings for RAG"}
                )
    
    def add_movies(self, movies: List[Dict[str, Any]]):
        """
        Add movies/TV shows to vector store
        movies: [{"id": 123, "title": "Inception", "overview": "...", "genres": [...], "media_type": "movie"}]
        """
        if not movies:
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for movie in movies:
            media_type = movie.get("media_type", "movie")  # Default to movie if not specified
            
            # Create text description for embedding
            text = f"{movie['title']}. {movie.get('overview', '')} Genres: {', '.join(movie.get('genres', []))}"
            
            documents.append(text)
            metadatas.append({
                "title": movie["title"],
                "tmdb_id": movie["id"],
                "overview": movie.get("overview", ""),
                "poster_path": movie.get("poster_path", ""),
                "vote_average": movie.get("vote_average", 0),
                "release_date": movie.get("release_date", ""),
                "media_type": media_type  # Store media type
            })
            ids.append(f"{media_type}_{movie['id']}")  # Unique ID: "movie_123" or "tv_456"
        
        # Add to ChromaDB (it auto-generates embeddings)
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(movies)} items to vector store")

    def get_existing_ids(self, ids: List[str]) -> set[str]:
        """Return IDs that already exist in the collection."""
        existing = set()
        if not ids:
            return existing

        try:
            for i in range(0, len(ids), 100):
                chunk = ids[i:i + 100]
                result = self.collection.get(ids=chunk)
                for item_id in result.get("ids", []):
                    existing.add(item_id)
        except Exception as e:
            logger.warning(f"Failed to check existing ids: {e}")

        return existing
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar movies/TV shows
        Returns: [{"id": 123, "title": "Inception", "media_type": "movie", ...}]
        """
        # Ensure collection exists before searching
        try:
            self.collection = self._get_or_create_collection()
        except Exception as e:
            logger.warning(f"Collection recreate failed: {e}")
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
        
        # Format results
        items = []
        if results["metadatas"] and results["metadatas"][0]:
            for metadata in results["metadatas"][0]:
                media_type = metadata.get("media_type", "movie")
                items.append({
                    "id": int(metadata["tmdb_id"]),
                    "title": metadata["title"],
                    "poster": f"https://image.tmdb.org/t/p/w500{metadata['poster_path']}" if metadata["poster_path"] else "",
                    "rating": float(metadata["vote_average"]),
                    "year": int(metadata["release_date"][:4]) if metadata["release_date"] else 0,
                    "media_type": media_type  # Include media type in response
                })
        
        return items
    
    def reset(self):
        """Delete all movies (for re-indexing)"""
        try:
            self.client.delete_collection("movies")
        except Exception:
            pass  # Collection might not exist
        self.collection = self._get_or_create_collection()
        logger.info("Vector store reset")


vector_store = VectorStore()
